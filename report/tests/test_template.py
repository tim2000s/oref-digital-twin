from report.template import render_report

DIAG = {
    "counts": {"critical": 1, "warning": 1, "info": 0},
    "glycemia": {"n_readings": 288, "days": 1.0, "mean_mgdl": 120.0, "mean_mmol": 6.7,
                 "gmi_pct": 6.2, "cv_pct": 30.0, "tir_70_180": 55.0, "tbr_lt70": 5.0,
                 "tbr_lt54": 3.0, "tar_gt180": 40.0, "tar_gt250": 6.0, "ting_63_140": 40.0},
    "findings": [
        {"key": "tbr_lt54_over_limit", "severity": "critical",
         "title": "Severe hypoglycaemia exposure above the 1% limit", "detail": "3.0% below 54."},
        {"key": "cv_high", "severity": "warning", "title": "Variability above 36%", "detail": "CV 30%."},
    ],
}
VARIANT = {"variant": "aaps_smb", "confidence": 0.9, "advisability": "full", "notes": []}


def test_render_contains_key_sections_and_numbers():
    md = render_report(DIAG, VARIANT)
    assert "# oref digital twin — report" in md
    assert "Severe hypoglycaemia exposure above the 1% limit" in md
    assert "55.0%" in md and "120" in md         # metrics rendered
    assert "aaps_smb" in md
    assert "not medical advice" in md            # disclaimer present


def test_critical_before_warning():
    md = render_report(DIAG, VARIANT)
    assert md.index("### Critical") < md.index("### Worth attention")


def test_report_has_no_decision_level_section():
    # removed in October 2026: it summed each cycle's 30-minute forecast across every cycle
    assert "Settings experiments" not in render_report(DIAG, VARIANT)


def test_render_is_deterministic():
    assert render_report(DIAG, VARIANT) == render_report(DIAG, VARIANT)


def test_handles_no_cgm():
    md = render_report({"counts": {}, "glycemia": {"n_readings": 0}, "findings": []})
    assert "No CGM data" in md


def test_settings_tests_section_lists_only_real_changes():
    from replay.tests.test_scenarios import _readings
    from replay.scenarios import run_settings_tests
    from report.template import render_settings_tests

    entries = _readings(([110] * 30 + [62] * 6) * 8)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    kept = {}

    def fake_sim(payload):
        if "cycles" in payload:
            kept[payload["cache_key"]] = payload["cycles"]
        t = [r["currentTime"] for r in kept[payload["cache_key"]]]
        return {"t": t, "scenarios": [
            {"du": [0.0] * len(t), "failed": 0,
             "dbg": [(1 - sc["basal_scale"]) * 50 + sc["target_offset"] * 0.5] * len(t)}
            for sc in payload["scenarios"]]}

    md = render_settings_tests(run_settings_tests(fake_sim, requests, entries, [], {}))
    assert "Trial to consider: basal rates -20%" in md
    assert "Run with basal rates -20%." in md          # later stages say what they carry
    assert "target 100 mg/dL" not in md.split("### Together")[1]   # unchanged target not listed
    assert "No change suggested" in md
    assert "That meets both goals." in md


def test_settings_tests_section_when_skipped():
    from report.template import render_settings_tests

    md = render_settings_tests(None, note="Settings tests skipped: no profile.")
    assert md.startswith("## Settings tests") and "no profile" in md


def test_settings_tests_section_says_how_far_to_trust_the_estimates():
    from replay.tests.test_scenarios import _readings, _shift_sim
    from replay.scenarios import run_settings_tests
    from report.template import render_settings_tests

    entries = _readings([120] * 300)
    requests = [{"currentTime": r.ts_ms, "profile": {"target_bg": 100}} for r in entries]
    md = render_settings_tests(run_settings_tests(_shift_sim(lambda sc: 0.0), requests, entries, [], {}))
    assert "overstated the fall in lows by 1.5 to 3 times" in md
