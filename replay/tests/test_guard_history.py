"""The guard's history as the page derives it from Nightscout (replay.inputs.guard_history)."""
from dataclasses import replace

from ingestion.models import GlucoseReading, ProfileBlock, ProfileSnapshot, Treatment
from replay.inputs import (EVIDENCE_DAYS, REFERENCE_DAYS, evidence_range, guard_history,
                           settings_timeline)
from replay.scenarios import guard_refuses

DAY = 86_400_000
NOW = 400 * DAY


def _snap(basal=1.0, isf=50.0, cr=10.0, at=1):
    b = lambda v: [ProfileBlock(0, v)]
    return ProfileSnapshot(valid_from_ms=at, units="mg/dl", dia_h=6.0, timezone="UTC",
                           basal=b(basal), isf_mgdl=b(isf), carb_ratio=b(cr),
                           target_low_mgdl=b(100.0), target_high_mgdl=b(110.0))


def _switch(at, pct, duration=None):
    return Treatment(ts_ms=at, event_type="Profile Switch", percentage=pct, duration_min=duration)


def _readings(lo, hi, low_every=None, high_every=None):
    out = []
    for i, t in enumerate(range(lo, hi, 300_000)):
        g = 120
        if low_every and i % low_every == 0:
            g = 60
        elif high_every and i % high_every == 0:
            g = 220
        out.append(GlucoseReading(ts_ms=t, sgv_mgdl=g))
    return out


def test_aaps_percentage_switch_is_the_last_change_and_counts_towards_the_cap():
    change = NOW - 20 * DAY
    tl = settings_timeline(_snap(), [_snap()], [_switch(NOW - 200 * DAY, 100), _switch(change, 106),
                                                 _switch(NOW - 2 * DAY, 130, duration=60)])  # temporary: ignored
    h = guard_history(tl, _readings(change - EVIDENCE_DAYS * DAY, NOW, high_every=3), NOW)
    assert abs(h["cumulative"]["basal"] - 1.06) < 1e-9 and abs(h["cumulative"]["isf"] - 1 / 1.06) < 1e-9
    assert abs(h["last"]["basal"] - 1.06) < 1e-9
    # same readings either side: no gain, so basal may not be strengthened again
    assert guard_refuses("basal", 1.1, h).startswith("the last change already gave more insulin")
    # the cap: ISF already ×0.94 of the reference, so a further ×0.8 passes 20% and ×0.9 does not
    assert "than the reference profile" in guard_refuses("isf", 0.8, {"cumulative": h["cumulative"]})
    assert guard_refuses("isf", 0.9, {"cumulative": h["cumulative"]}) is None


def test_gain_since_the_change_lets_the_setting_strengthen_again():
    change = NOW - 20 * DAY
    tl = settings_timeline(_snap(), [], [_switch(NOW - 200 * DAY, 100), _switch(change, 110)])
    entries = (_readings(change - EVIDENCE_DAYS * DAY, change, high_every=3) + _readings(change, NOW))
    h = guard_history(tl, entries, NOW)
    assert h["after"]["tir"] >= h["before"]["tir"] + 2 and h["after"]["tbr"] <= h["before"]["tbr"]
    assert guard_refuses("basal", 1.05, h) is None


def test_missing_readings_before_the_change_refuse_only_further_strengthening():
    change = NOW - 10 * DAY
    tl = settings_timeline(_snap(), [], [_switch(NOW - 200 * DAY, 100), _switch(change, 110)])
    h = guard_history(tl, _readings(change, NOW), NOW)
    assert h["before"] is None and h["after"] is not None
    assert guard_refuses("basal", 1.1, h) is not None
    # a percentage switch scales ISF and carb ratio too, so both count as strengthened; the
    # target did not move, so a lower target is judged by the cap alone
    assert guard_refuses("cr", 0.9, h) is not None
    assert guard_refuses("target", -9, h) is None
    assert evidence_range(tl, NOW) == (change - EVIDENCE_DAYS * DAY, change)


def test_reference_is_the_profile_in_force_reference_days_ago():
    tl = settings_timeline(_snap(), [], [_switch(NOW - (REFERENCE_DAYS + 30) * DAY, 100),
                                         _switch(NOW - (REFERENCE_DAYS + 5) * DAY, 110),
                                         _switch(NOW - 30 * DAY, 120)])
    h = guard_history(tl, [], NOW)
    assert abs(h["cumulative"]["basal"] - 120 / 110) < 1e-9


def test_trio_profile_documents_make_the_timeline_without_switches():
    docs = [_snap(isf=50.0, at=NOW - 100 * DAY), _snap(isf=40.0, at=NOW - 7 * DAY)]
    tl = settings_timeline(docs[-1], docs, [])
    h = guard_history(tl, [], NOW)
    assert abs(h["cumulative"]["isf"] - 0.8) < 1e-9 and abs(h["last"]["isf"] - 0.8) < 1e-9
    assert h["before"] is None
    assert guard_refuses("isf", 0.9, h) is not None


def test_no_history_still_caps_one_visit_at_twenty_percent():
    tl = settings_timeline(_snap(), [_snap()], [])
    h = guard_history(tl, [], NOW)
    assert "last" not in h
    assert guard_refuses("basal", 1.2, h) is None
    assert guard_refuses("basal", 1.3, h) is not None
    assert guard_refuses("cr", 1.3, h) is None          # less insulin is never refused here


def test_last_change_is_the_latest_of_several():
    tl = settings_timeline(_snap(), [], [_switch(NOW - 200 * DAY, 100), _switch(NOW - 60 * DAY, 120),
                                         _switch(NOW - 10 * DAY, 90)])
    h = guard_history(tl, [], NOW)
    assert abs(h["last"]["basal"] - 0.75) < 1e-9
    assert guard_refuses("basal", 1.1, h) is None       # the latest change gave less insulin


def test_more_lows_since_the_change_refuse_despite_more_time_in_range():
    change = NOW - 20 * DAY
    tl = settings_timeline(_snap(), [], [_switch(NOW - 200 * DAY, 100), _switch(change, 110)])
    entries = (_readings(change - EVIDENCE_DAYS * DAY, change, high_every=3)
               + _readings(change, NOW, low_every=20))
    h = guard_history(tl, entries, NOW)
    assert h["after"]["tir"] >= h["before"]["tir"] + 2 and h["after"]["tbr"] > h["before"]["tbr"]
    assert guard_refuses("basal", 1.05, h) is not None
