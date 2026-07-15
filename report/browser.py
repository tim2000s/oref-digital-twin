"""Pyodide entrypoint: raw Nightscout JSON -> report, all client-side.

The browser does the Nightscout `fetch` (token + CORS stay on the device) and hands the
raw arrays here. This runs the whole read-only pipeline — normalise, classify variant,
diagnose, optionally run decision-level counterfactuals via real oref0 (in the browser),
and render the deterministic report — in Pyodide.

`abstracted_findings` is the ONLY thing that may be sent to the narration Worker.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from diagnostics import run_diagnostics
from ingestion.models import ProfileSnapshot
from ingestion.pull import pull_from_raw
from replay import OrefOracle, from_cycle, run_counterfactual
from variant import detect_variant

from .grounding import check_narrative
from .template import render_report

MAX_CYCLES = 400                       # cap oref calls for browser responsiveness

# maxIOB parsing modelled on the Boost analyser (`maxIOB: ?([0-9.,]+)`), generalised:
#   - case-insensitive; "maxIOB" | "max_iob" | "max iob"
#   - separator ":" | "=" | JSON quote+colon | bare space
#   - decimal "." OR "," (European locale / some AAPS builds) -> normalised to "."
# Covers AAPS console/reason ("maxIOB: 8.0", "maxIOB 1,0") and Trio/oref JSON ("max_iob":8).
_MAXIOB_RE = re.compile(r"max[\s_]?iob[\"']?\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?)", re.IGNORECASE)


def _parse_max_iob(text: str | None) -> float | None:
    if not text:
        return None
    m = _MAXIOB_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _active_profile(profiles: list[ProfileSnapshot]) -> ProfileSnapshot | None:
    return max(profiles, key=lambda p: (p.valid_from_ms or 0)) if profiles else None


def infer_settings(pull) -> tuple[dict[str, Any], list[str]]:
    """Best-effort replay settings from devicestatus + treatments (not in the NS profile).

    max_iob is read from the most recent reason string ("maxIOB 6.0"); SMB is inferred from
    whether SMBs were actually delivered. Both are flagged as inferred.
    """
    notes: list[str] = []
    max_iob = None
    for c in reversed(pull.devicestatus):          # most recent first
        # search the reason AND the whole openaps blob (the value may live in a nested
        # field, a console line, or the reason text depending on AAPS/Trio build).
        haystack = c.reason or ""
        if c.raw_openaps:
            haystack += " " + json.dumps(c.raw_openaps)
        max_iob = _parse_max_iob(haystack)
        if max_iob is not None:
            break
    if max_iob is None:
        notes.append("Could not infer max_iob from devicestatus — counterfactuals skipped.")
    enable_smb = any(t.is_smb for t in pull.treatments)
    return {"max_iob": max_iob, "enable_smb": enable_smb, "max_smb_minutes": 30}, notes


def _default_deltas(settings: dict[str, Any], profile: ProfileSnapshot | None) -> list[tuple[str, dict]]:
    """Illustrative, conservative 'what if' levers computed from the user's baseline."""
    out: list[tuple[str, dict]] = []
    max_iob = settings.get("max_iob")
    if max_iob and max_iob > 1.5:
        lowered = round(max_iob - 1.0, 1)
        out.append((f"max_iob {max_iob} → {lowered}", {"max_iob": lowered}))
    if profile and profile.target_low_mgdl and profile.target_high_mgdl:
        base = (profile.target_low_mgdl[0].value + profile.target_high_mgdl[0].value) / 2.0
        raised = round(base + 18.0, 0)             # ~ +1 mmol/L
        out.append((f"target {round(base)} → {round(raised)} mg/dL", {"target_bg": raised}))
    return out


def _run_counterfactuals(pull, settings, profile, runner, deltas) -> tuple[list[dict], int]:
    cycles = pull.devicestatus[-MAX_CYCLES:]
    requests, ts = [], []
    for c in cycles:
        if c.iob is None or c.bg_mgdl is None:
            continue
        req, _w = from_cycle(c, profile, pull.entries, settings)
        if req is not None:
            requests.append(req)
            ts.append(c.ts_ms)
    if not requests:
        return [], 0
    oracle = OrefOracle(runner=runner)
    results = []
    for label, delta in deltas:
        cf = run_counterfactual(oracle, requests, delta, label=label, ts_of=ts)
        results.append(cf.to_dict())
    return results, len(requests)


def build_report(
    raw: dict[str, Any],
    *,
    oref_runner: Callable | None = None,
    settings: dict[str, Any] | None = None,
    deltas: list[tuple[str, dict]] | None = None,
) -> dict[str, Any]:
    """raw: {base_url, start_ms, end_ms, entries, treatments, devicestatus, profiles}.

    If `oref_runner` is provided (the browser injects one backed by oref0-in-WASM), run
    decision-level counterfactuals; otherwise produce the diagnostic report alone.
    """
    pull = pull_from_raw(
        raw.get("base_url", ""), int(raw["start_ms"]), int(raw["end_ms"]),
        raw.get("entries", []), raw.get("treatments", []),
        raw.get("devicestatus", []), raw.get("profiles", []),
    )
    verdict = detect_variant(pull.devicestatus, dropped_no_oref=pull.dropped.get("devicestatus", 0))
    diagnostics = run_diagnostics(pull, variant=verdict.to_dict())

    counterfactuals: list[dict] = []
    cf_note: str | None = None
    n_loop = len(pull.devicestatus)
    if oref_runner is None:
        cf_note = "Settings experiments skipped: the in-browser oref engine did not load."
    else:
        profile = _active_profile(pull.profiles)
        if settings is None:
            settings, _notes = infer_settings(pull)
        if profile is None:
            cf_note = "Settings experiments skipped: no Nightscout profile found."
        elif settings.get("max_iob") is None:
            cf_note = (f"Settings experiments skipped: could not read max_iob from the "
                       f"devicestatus reason ({n_loop} loop cycles seen).")
        else:
            deltas = deltas or _default_deltas(settings, profile)
            if not deltas:
                cf_note = "Settings experiments skipped: no applicable levers for this profile."
            else:
                try:
                    counterfactuals, n_built = _run_counterfactuals(
                        pull, settings, profile, oref_runner, deltas)
                    if not counterfactuals or n_built == 0:
                        cf_note = (f"Settings experiments: could not build oref inputs from any of "
                                   f"the last {min(n_loop, MAX_CYCLES)} cycles (max_iob "
                                   f"{settings.get('max_iob')}).")
                    elif all(c.get("n_evaluated", 0) == 0 for c in counterfactuals):
                        cf_note = (f"Settings experiments: oref evaluated 0 of {n_built} cycles — "
                                   "the in-browser engine returned no decisions.")
                        counterfactuals = []
                except Exception as exc:  # surface, never break the report
                    counterfactuals = []
                    cf_note = f"Settings experiments errored: {type(exc).__name__}: {exc}"

    diag_d = diagnostics.to_dict()
    variant_d = verdict.to_dict()
    report_md = render_report(diag_d, variant_d, counterfactuals, counterfactual_note=cf_note)

    return {
        "report_md": report_md,
        "diagnostics": diag_d,
        "variant": variant_d,
        "counterfactuals": counterfactuals,
        "counterfactual_note": cf_note,
        "coverage": {"cgm": pull.cgm.to_dict(), "loop": pull.loop.to_dict(), "warnings": pull.warnings()},
    }


def make_js_oref_runner():
    """A runner backed by globalThis.orefDetermine (oref0-in-WASM). Pyodide-only."""
    import js
    from pyodide.ffi import to_js

    def runner(requests: list[dict]) -> list[dict]:
        js_req = to_js(requests, dict_converter=js.Object.fromEntries)
        return js.orefDetermine(js_req).to_py()

    return runner


def abstracted_findings(result: dict[str, Any]) -> dict[str, Any]:
    """The only payload allowed to leave the browser for narration — no raw data/token."""
    diag = result.get("diagnostics", {})
    return {
        "counts": diag.get("counts", {}),
        "glycemia": diag.get("glycemia", {}),
        "findings": diag.get("findings", []),
        "variant": result.get("variant", {}),
        "counterfactuals": result.get("counterfactuals", []),
    }


def gate_narrative(narrative: str, source: dict[str, Any]) -> dict[str, Any]:
    """Run the grounding gate; the browser shows the narrative only if passed is True."""
    return check_narrative(narrative, source).to_dict()
