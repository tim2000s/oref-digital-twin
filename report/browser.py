"""Pyodide entrypoint: raw Nightscout JSON -> report, all client-side.

The browser does the Nightscout `fetch` (token + CORS stay on the device) and hands the
raw arrays here. This runs the whole read-only pipeline — normalise, classify variant,
diagnose and render the deterministic report, then run the settings tests through real
oref0 (in the browser) as a second step — in Pyodide.

`abstracted_findings` is the ONLY thing that may be sent to the narration Worker.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from diagnostics import run_diagnostics
from ingestion.models import ProfileSnapshot
from ingestion.pull import pull_from_raw
from replay import OrefOracle, from_cycle
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
        notes.append("Could not infer max_iob from devicestatus — settings tests skipped.")
    enable_smb = any(t.is_smb for t in pull.treatments)
    return {"max_iob": max_iob, "enable_smb": enable_smb, "max_smb_minutes": 30}, notes


# The insulin curves AndroidAPS and Trio ship: rapid-acting (peak 75 min), ultra-rapid (55)
# and the Lyumjev preset (ultra-rapid, peak 45).
CURVE_CANDIDATES = (("rapid-acting", None), ("ultra-rapid", None), ("ultra-rapid", 45))
CURVE_SAMPLE = 60


def _choose_insulin_curve(pull, settings, profile, entries, runner) -> tuple[dict, dict]:
    """Pick the insulin curve whose rebuilt IOB best matches what the loop logged.

    The settings rarely name the insulin, and the curve moves oref's rebuilt IOB a long way: on
    one AndroidAPS user on Lyumjev the median gap to the logged figure was 0.66 U on the
    rapid-acting default and 0.14 U on the Lyumjev preset. A curve named in the settings is
    used as given.
    """
    if settings.get("insulin_curve"):
        return settings, {"insulin_curve": settings["insulin_curve"], "insulin_curve_source": "settings"}
    cycles = [c for c in pull.devicestatus if c.iob is not None and c.bg_mgdl is not None]
    step = max(len(cycles) // CURVE_SAMPLE, 1)
    sample = cycles[::step][-CURVE_SAMPLE:]
    fit = {}
    oracle = OrefOracle(runner=runner)
    for curve, peak in CURVE_CANDIDATES:
        trial = {**settings, "insulin_curve": curve}
        if peak:
            trial["insulin_peak_min"] = peak
        reqs = [r for r in (from_cycle(c, profile, entries, trial, pull.treatments)[0]
                            for c in sample) if r is not None]
        gaps = sorted(abs(r["iob_rebuilt"] - q["iob_logged"])
                      for r, q in zip(oracle.evaluate(reqs), reqs)
                      if r.get("ok") and r.get("iob_rebuilt") is not None
                      and q.get("iob_logged") is not None)
        if gaps:
            fit[f"{curve}{'' if peak is None else f' peak {peak}'}"] = (gaps[len(gaps) // 2], trial)
    if not fit:
        return settings, {"insulin_curve_source": "default"}
    label, (gap, trial) = min(fit.items(), key=lambda kv: kv[1][0])
    return trial, {"insulin_curve": label, "insulin_curve_source": "matched to logged IOB",
                   "insulin_curve_fit_u": {k: round(v[0], 2) for k, v in fit.items()}}


def _openaps_shape(pull) -> str:
    """Compact description of the most-recent cycle's openaps fields, for diagnosing parse gaps."""
    if not pull.devicestatus:
        return "no devicestatus"
    c = pull.devicestatus[-1]
    raw = c.raw_openaps or {}
    sug = list((raw.get("suggested") or {}).keys())
    ena = list((raw.get("enacted") or {}).keys())
    top = list(raw.keys())
    return (f"parsed bg={c.bg_mgdl} iob={c.iob}; openaps={top}; "
            f"suggested={sug[:20]}; enacted={ena[:20]}")


# What the settings tests need from the last build_report: they run as a second step so the
# main report is on screen while they work.
_LAST: dict[str, Any] = {}


def build_report(
    raw: dict[str, Any],
    *,
    oref_runner: Callable | None = None,
    settings: dict[str, Any] | None = None,
    max_iob_override: float | None = None,
) -> dict[str, Any]:
    """raw: {base_url, start_ms, end_ms, entries, treatments, devicestatus, profiles}.

    Produces the diagnostic report. With `oref_runner` (the browser injects one backed by
    oref0-in-WASM) it also resolves the settings the settings tests will replay with, from the
    uploaded file, the Max IOB box or the devicestatus, and keeps them for `settings_tests`.
    """
    pull = pull_from_raw(
        raw.get("base_url", ""), int(raw["start_ms"]), int(raw["end_ms"]),
        raw.get("entries", []), raw.get("treatments", []),
        raw.get("devicestatus", []), raw.get("profiles", []),
    )
    verdict = detect_variant(pull.devicestatus, dropped_no_oref=pull.dropped.get("devicestatus", 0))
    diagnostics = run_diagnostics(pull, variant=verdict.to_dict())

    _LAST.clear()
    _LAST.update({"pull": pull, "variant": verdict.to_dict(), "runner": oref_runner})
    if oref_runner is not None:
        if settings is None:
            settings, _notes = infer_settings(pull)
        if max_iob_override is not None:
            settings = {**settings, "max_iob": float(max_iob_override)}
        _LAST.update({"profile": _active_profile(pull.profiles), "settings": settings})

    diag_d = diagnostics.to_dict()
    variant_d = verdict.to_dict()
    return {
        "report_md": render_report(diag_d, variant_d),
        "diagnostics": diag_d,
        "variant": variant_d,
        "coverage": {"cgm": pull.cgm.to_dict(), "loop": pull.loop.to_dict(), "warnings": pull.warnings()},
    }


def settings_tests(sim_runner: Callable | None = None,
                   progress: Callable | None = None) -> dict[str, Any]:
    """Basal, ISF, carb-ratio, target and SMB tests on the last report's data.

    Returns {"report_md": section, "result": tables} or {"report_md": note, "skipped": why}.
    In the browser `sim_runner` is omitted and oref0-in-WASM is used.
    """
    from ingestion.models import GlucoseReading
    from replay.scenarios import run_settings_tests, sample_cycles

    from .template import render_settings_tests

    def skipped(why: str) -> dict[str, Any]:
        return {"report_md": render_settings_tests(None, note=why), "skipped": why}

    pull, profile, settings = _LAST.get("pull"), _LAST.get("profile"), _LAST.get("settings")
    runner = _LAST.get("runner")
    if pull is None or runner is None:
        return skipped("Settings tests skipped: the in-browser oref engine did not load.")
    if profile is None:
        return skipped("Settings tests skipped: no Nightscout profile found.")
    if not settings or settings.get("max_iob") is None:
        recent = next((c.reason for c in reversed(pull.devicestatus) if c.reason), None)
        snippet = (recent[:120] + "…") if recent else "(no reason text present)"
        return skipped(f"Settings tests skipped: max IOB isn't in your Nightscout data "
                       f"({len(pull.devicestatus)} cycles). Enter Max IOB above to run them. "
                       f"Sample reason: {snippet}")
    if sim_runner is None:
        sim_runner = make_js_oref_simulator()

    merged = list(pull.entries) + [GlucoseReading(ts_ms=c.ts_ms, sgv_mgdl=c.bg_mgdl)
                                   for c in pull.devicestatus if c.bg_mgdl is not None]
    settings, curve = _choose_insulin_curve(pull, settings, profile, merged, runner)
    cycles = [c for c in sample_cycles(pull.devicestatus) if c.bg_mgdl is not None]
    requests = [r for r in (from_cycle(c, profile, merged, settings, pull.treatments)[0]
                            for c in cycles) if r is not None]
    if len(requests) < 288:
        return skipped(f"Settings tests skipped: only {len(requests)} usable loop cycles, under "
                       f"one day's worth. Diagnostic: {_openaps_shape(pull)}")
    result = run_settings_tests(sim_runner, requests, pull.entries, pull.treatments, settings,
                                progress=progress)
    result["insulin_curve"] = curve
    variant = _LAST.get("variant") or {}
    if variant.get("advisability") != "full":
        result["variant_note"] = (
            f"Your loop was detected as {variant.get('variant')}. These tests run stock oref0, "
            "so anything your variant adds on top of it is not modelled.")
    return {"report_md": render_settings_tests(result), "result": result}


def settings_from_raw(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate uploaded raw key/values (AAPS prefs / Trio JSON) into replay settings.

    Returns the replay-lever settings plus any validation issues / values needing
    confirmation, so the caller can feed `settings` into build_report and warn the user.
    """
    from settings import resolve_alias, validate

    v = validate(raw)
    # keys that mention IOB but map to nothing — helps diagnose an unknown build's naming
    unmapped_iob = [k for k in raw if "iob" in str(k).lower() and resolve_alias(k) is None]
    return {
        "settings": v.replay_settings(),
        "all_values": v.values,
        "needs_confirm": v.needs_confirm,
        "blocked": v.blocked,          # parsed but withheld from replay until confirmed
        "issues": [i.to_dict() for i in v.issues],
        "unmapped_iob_keys": unmapped_iob,
    }


def make_js_oref_runner():
    """A runner backed by globalThis.orefDetermine (oref0-in-WASM). Pyodide-only."""
    import js
    from pyodide.ffi import to_js

    def runner(requests: list[dict]) -> list[dict]:
        if hasattr(js, "orefDetermineJSON"):
            return json.loads(js.orefDetermineJSON(json.dumps(requests)))
        js_req = to_js(requests, dict_converter=js.Object.fromEntries)
        return js.orefDetermine(js_req).to_py()

    return runner


def make_js_oref_simulator():
    """The closed-loop simulator in oref0-in-WASM (globalThis.orefSimulate). Pyodide-only."""
    import js
    from pyodide.ffi import to_js

    def simulate(payload: dict) -> dict:
        # one JSON string each way: field-by-field conversion of a week of requests was the
        # largest single cost of the settings tests in the browser
        return json.loads(js.orefSimulateJSON(json.dumps(payload)))

    return simulate


def abstracted_findings(result: dict[str, Any]) -> dict[str, Any]:
    """The only payload allowed to leave the browser for narration — no raw data/token."""
    diag = result.get("diagnostics", {})
    return {
        "counts": diag.get("counts", {}),
        "glycemia": diag.get("glycemia", {}),
        "findings": diag.get("findings", []),
        "variant": result.get("variant", {}),
    }


def gate_narrative(narrative: str, source: dict[str, Any]) -> dict[str, Any]:
    """Run the grounding gate; the browser shows the narrative only if passed is True."""
    return check_narrative(narrative, source).to_dict()
