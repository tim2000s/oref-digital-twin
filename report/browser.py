"""Pyodide entrypoint: raw Nightscout JSON -> report, all client-side.

The browser does the Nightscout `fetch` (token + CORS stay on the device) and hands the
raw arrays here. This runs the whole read-only pipeline — normalise, classify variant,
diagnose, render the deterministic report — in Pyodide, so nothing but (optionally) the
abstracted findings ever leaves the browser.

`abstracted_findings` is the ONLY thing that may be sent to the narration Worker: it is
stats and finding-keys, no raw CGM/treatments, no token, no site URL.
"""

from __future__ import annotations

from typing import Any

from diagnostics import run_diagnostics
from ingestion.pull import pull_from_raw
from variant import detect_variant

from .grounding import check_narrative
from .template import render_report


def build_report(raw: dict[str, Any], counterfactuals: list[dict] | None = None) -> dict[str, Any]:
    """raw: {base_url, start_ms, end_ms, entries, treatments, devicestatus, profiles}."""
    pull = pull_from_raw(
        raw.get("base_url", ""),
        int(raw["start_ms"]),
        int(raw["end_ms"]),
        raw.get("entries", []),
        raw.get("treatments", []),
        raw.get("devicestatus", []),
        raw.get("profiles", []),
    )
    verdict = detect_variant(pull.devicestatus, dropped_no_oref=pull.dropped.get("devicestatus", 0))
    diagnostics = run_diagnostics(pull, variant=verdict.to_dict())

    diag_d = diagnostics.to_dict()
    variant_d = verdict.to_dict()
    report_md = render_report(diag_d, variant_d, counterfactuals)

    return {
        "report_md": report_md,
        "diagnostics": diag_d,
        "variant": variant_d,
        "counterfactuals": counterfactuals or [],
        "coverage": {"cgm": pull.cgm.to_dict(), "loop": pull.loop.to_dict(), "warnings": pull.warnings()},
    }


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
