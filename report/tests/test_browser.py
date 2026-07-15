"""End-to-end of the Pyodide entrypoint: raw NS JSON -> report, all in Python."""

from ingestion.tests import fixtures as fx
from report.browser import abstracted_findings, build_report, gate_narrative

RAW = {
    "base_url": "https://example.test",
    "start_ms": 1_699_990_000_000,
    "end_ms": 1_700_010_000_000,
    "entries": [fx.ENTRY, fx.ENTRY_MBG],
    "treatments": [fx.TREATMENT_SMB, fx.TREATMENT_CARB, fx.TREATMENT_TT],
    "devicestatus": [fx.DEVICESTATUS, fx.DEVICESTATUS_NO_OREF],
    "profiles": [fx.PROFILE_MMOL],
}


def test_build_report_end_to_end():
    result = build_report(RAW)
    assert result["report_md"].startswith("# oref digital twin")
    assert "diagnostics" in result and "variant" in result
    assert "cgm" in result["coverage"]
    # the no-oref devicestatus doc was dropped upstream
    assert isinstance(result["diagnostics"]["findings"], list)


def test_abstracted_findings_excludes_raw_data_and_token():
    result = build_report(RAW)
    payload = abstracted_findings(result)
    # only findings/stats leave the browser
    assert set(payload).issubset({"counts", "glycemia", "findings", "variant", "counterfactuals"})
    # no raw NS data or connection info anywhere in the payload
    flat = str(payload)
    assert "example.test" not in flat
    assert "entries" not in payload and "base_url" not in payload


def test_gate_narrative_wires_through():
    result = build_report(RAW)
    source = abstracted_findings(result)
    # a narrative that invents a number must be rejected
    bad = gate_narrative("Your time in range was 999%.", source)
    assert bad["passed"] is False
    assert any(v["kind"] == "ungrounded_number" for v in bad["violations"])
