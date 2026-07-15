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


def test_infer_settings_reads_max_iob_from_reason():
    from ingestion.pull import pull_from_raw
    from report.browser import infer_settings
    pull = pull_from_raw("x", RAW["start_ms"], RAW["end_ms"], RAW["entries"],
                         RAW["treatments"], RAW["devicestatus"], RAW["profiles"])
    settings, _notes = infer_settings(pull)
    assert settings["max_iob"] == 11.2          # from "maxIOB 11.2" in the reason
    assert settings["enable_smb"] is True        # an SMB was delivered


def _fake_oref_runner(requests):
    # SMB scales with max_iob so a max_iob delta produces a decision change
    return [{"ok": True, "rt": {"rate": 0.0, "duration": 30,
                                "units": round(r["profile"].get("max_iob", 0) * 0.1, 3)}}
            for r in requests]


def test_counterfactuals_run_when_oref_runner_supplied():
    result = build_report(RAW, oref_runner=_fake_oref_runner)
    cfs = result["counterfactuals"]
    assert cfs, "expected counterfactuals with a runner supplied"
    # the max_iob lever should change the decision on the evaluated cycle(s)
    maxiob_cf = next(c for c in cfs if "max_iob" in c["label"])
    assert maxiob_cf["n_evaluated"] >= 1
    assert maxiob_cf["n_changed"] >= 1
    assert "not the resulting blood glucose" in maxiob_cf["caveat"]
    # and it renders into the report
    assert "Settings experiments" in result["report_md"]


def test_no_counterfactuals_without_runner():
    assert build_report(RAW)["counterfactuals"] == []
