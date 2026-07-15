from report.grounding import check_narrative

SOURCE = {
    "glycemia": {"mean_mgdl": 120.0, "tir_70_180": 55.0, "tbr_lt54": 3.0},
    "counts": {"critical": 1, "warning": 1, "info": 0},
    "findings": [
        {"key": "tbr_lt54_over_limit", "severity": "critical",
         "title": "Severe hypoglycaemia exposure above the 1% limit",
         "detail": "3.0% of readings are below 54 mg/dL, above the 1% limit."},
        {"key": "smb_high_iob_overnight", "severity": "warning",
         "title": "Overnight SMBs at high IOB", "detail": "4 of 10 overnight SMBs at high IOB."},
    ],
}


def test_grounded_narrative_passes():
    txt = ("Your mean glucose was 120 mg/dL with time in range of 55%. Critically, severe "
           "hypoglycaemia below 54 was 3.0%, above the 1% limit. Overnight SMBs at high IOB "
           "showed 4 of 10 followed by lows — an association, this does not prove causation.")
    res = check_narrative(txt, SOURCE)
    assert res.passed, res.to_dict()


def test_fabricated_number_is_caught():
    txt = ("Severe hypoglycaemia below 54 was 3.0%, above the 1% limit. Your time in range "
           "was 85%.")  # 85 is not in the source (real TIR is 55)
    res = check_narrative(txt, SOURCE)
    assert not res.passed
    assert any(v.kind == "ungrounded_number" and "85" in v.detail for v in res.violations)


def test_prescription_is_blocked():
    txt = ("Severe hypoglycaemia below 54 was 3.0%, above the 1% limit. You should increase "
           "your max IOB to 8 to fix this.")
    res = check_narrative(txt, SOURCE)
    assert not res.passed
    assert any(v.kind == "prescription" for v in res.violations)


def test_omitted_critical_is_caught():
    txt = "Things look broadly fine and your time in range was 55%."  # no mention of hypo
    res = check_narrative(txt, SOURCE)
    assert not res.passed
    assert any(v.kind == "omitted_critical" for v in res.violations)


def test_missing_association_caveat_for_smb_pattern():
    txt = ("Severe hypoglycaemia below 54 was 3.0%, above the 1% limit. Overnight SMBs at "
           "high IOB were seen 4 of 10 times and caused the lows.")  # asserts causation, no caveat
    res = check_narrative(txt, SOURCE)
    assert not res.passed
    assert any(v.kind == "missing_assoc_caveat" for v in res.violations)


def test_counterfactual_requires_caveat():
    src = dict(SOURCE)
    src["counterfactuals"] = [{"label": "max_iob=3", "n_changed": 5}]
    txt = ("Severe hypoglycaemia below 54 was 3.0%, above the 1% limit. Lowering max IOB to 3 "
           "changed the decision on 5 cycles.")  # mentions counterfactual, no BG caveat
    res = check_narrative(txt, src)
    assert not res.passed
    assert any(v.kind == "missing_caveat" for v in res.violations)

    txt_ok = txt + " This is decision-level only and does not predict the resulting blood glucose."
    assert check_narrative(txt_ok, src).passed


def test_structural_small_integers_allowed():
    txt = ("Severe hypoglycaemia below 54 was 3.0%, above the 1% limit; this is the 1 thing to "
           "fix. Overnight SMBs — association only, does not prove causation — over 2 nights.")
    res = check_narrative(txt, SOURCE)
    assert res.passed, res.to_dict()
