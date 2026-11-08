from ingestion.models import DeviceStatusCycle, GlucoseReading, ProfileBlock, ProfileSnapshot
from replay.inputs import build_glucose_status, build_profile, from_cycle


def _entries(base_ms, series):
    # series: list of (minutes_before_base, sgv)
    return [GlucoseReading(ts_ms=base_ms - m * 60_000, sgv_mgdl=v) for m, v in series]


def test_build_glucose_status_delta():
    base = 1_700_000_000_000
    entries = _entries(base, [(0, 150), (5, 145), (15, 135), (45, 120)])
    gs = build_glucose_status(entries, base)
    assert gs["glucose"] == 150
    assert gs["delta"] == 5.0                     # 150 - 145
    assert gs["short_avgdelta"] == round((150 - 135) / 3.0, 1)
    assert gs["long_avgdelta"] == round((150 - 120) / 9.0, 1)
    assert "short_avgdelta" in gs and "long_avgdelta" in gs  # oref field names


def test_build_glucose_status_empty():
    assert build_glucose_status([], 1) is None


def _snapshot(tz="UTC"):
    b = lambda v: [ProfileBlock(0, v)]
    return ProfileSnapshot(valid_from_ms=1, units="mg/dl", dia_h=6.0, timezone=tz,
                           basal=b(1.0), isf_mgdl=b(50.0), carb_ratio=b(10.0),
                           target_low_mgdl=b(100.0), target_high_mgdl=b(110.0))


def test_build_profile_uses_settings_and_flags_missing():
    prof, warn = build_profile(_snapshot(), {"max_iob": 6.0, "enable_smb": True}, at_ms=1_700_000_000_000)
    assert prof["current_basal"] == 1.0 and prof["sens"] == 50.0
    assert prof["target_bg"] == 105.0 and prof["max_iob"] == 6.0
    assert prof["enableSMB_always"] is True
    # nothing missing from the *profile* — the SMB caps are separately reported as
    # substituted, which is expected here since the settings dict does not carry them.
    assert not [w for w in warn if "profile is missing" in w or "settings missing" in w]


def test_build_profile_warns_when_max_iob_missing():
    _, warn = build_profile(_snapshot(), {}, at_ms=1_700_000_000_000)
    assert any("max_iob" in w for w in warn)


def test_build_profile_picks_time_of_day_block():
    b0, b12 = ProfileBlock(0, 0.8), ProfileBlock(43200, 1.6)  # 00:00 and 12:00 UTC
    snap = ProfileSnapshot(valid_from_ms=1, units="mg/dl", dia_h=6.0, timezone="UTC",
                           basal=[b0, b12], isf_mgdl=[ProfileBlock(0, 50.0)],
                           carb_ratio=[ProfileBlock(0, 10.0)],
                           target_low_mgdl=[ProfileBlock(0, 100.0)],
                           target_high_mgdl=[ProfileBlock(0, 110.0)])
    # a 14:00 UTC timestamp should select the 12:00 basal block (1.6)
    from datetime import datetime, timezone
    at = int(datetime(2023, 11, 15, 14, 0, tzinfo=timezone.utc).timestamp() * 1000)
    prof, _ = build_profile(snap, {"max_iob": 6.0}, at)
    assert prof["current_basal"] == 1.6


def test_from_cycle_returns_none_without_max_iob():
    cyc = DeviceStatusCycle(ts_ms=1_700_000_000_000, bg_mgdl=150, iob=1.0)
    entries = _entries(1_700_000_000_000, [(0, 150), (5, 148)])
    req, warn = from_cycle(cyc, _snapshot(), entries, settings={}, treatments=[])
    assert req is None
    assert any("max_iob" in w for w in warn)


def test_from_cycle_builds_request_with_fidelity_warnings():
    cyc = DeviceStatusCycle(ts_ms=1_700_000_000_000, bg_mgdl=150, iob=1.0, sensitivity_ratio=0.9)
    entries = _entries(1_700_000_000_000, [(0, 150), (5, 148), (15, 140)])
    req, warn = from_cycle(cyc, _snapshot(), entries, settings={"max_iob": 6.0}, treatments=[])
    assert req is not None
    assert req["glucose_status"]["glucose"] == 150
    assert req["autosens_data"]["ratio"] == 0.9
    assert req["profile"]["max_iob"] == 6.0
    # inherent fidelity limits are always disclosed
    assert any("currenttemp" in w for w in warn)
    assert any("insulin curve unknown" in w for w in warn)
    # determine-basal is never handed the single logged object
    assert "iob_data" not in req and req["iob_logged"] == 1.0


def test_negative_max_iob_is_clamped_like_apply_delta():
    """build_profile must clamp exactly as settings_delta does.

    Otherwise an unclamped negative baseline is diffed against a clamped altered run and
    the counterfactual reports a delivery delta that means nothing.
    """
    from replay.settings_delta import apply_delta

    prof, warn = build_profile(_snapshot(), {"max_iob": -3.0}, at_ms=1_700_000_000_000)
    assert prof["max_iob"] == 0.0
    assert any("negative" in w for w in warn)

    req = {"profile": dict(prof)}
    assert apply_delta(req, {"max_iob": -3.0})["profile"]["max_iob"] == prof["max_iob"]


def test_zero_smb_cap_survives_into_the_oref_profile():
    """A deliberate 'SMB off' must reach oref as 0, not be replaced by the 30-min default."""
    prof, _ = build_profile(_snapshot(),
                            {"max_iob": 6.0, "enable_smb": True, "max_smb_minutes": 0,
                             "max_uam_minutes": 0},
                            at_ms=1_700_000_000_000)
    assert prof["maxSMBBasalMinutes"] == 0
    assert prof["maxUAMSMBBasalMinutes"] == 0


def test_substituted_smb_caps_are_warned_about():
    """Permissive defaults are allowed, but never silently."""
    _, warn = build_profile(_snapshot(), {"max_iob": 6.0, "enable_smb": True},
                            at_ms=1_700_000_000_000)
    assert any("max_smb_minutes unknown" in w for w in warn)
    assert any("more SMB than your settings allow" in w for w in warn)


def test_from_cycle_refuses_without_treatments():
    """Without treatments the IOB projection cannot be rebuilt, and a single logged IOB object
    switches off oref's low-glucose guard, so the cycle is refused rather than replayed."""
    cyc = DeviceStatusCycle(ts_ms=1_700_000_000_000, bg_mgdl=150, iob=1.0)
    entries = _entries(1_700_000_000_000, [(0, 150), (5, 148)])
    req, warn = from_cycle(cyc, _snapshot(), entries, settings={"max_iob": 6.0})
    assert req is None
    assert any("no treatments" in w for w in warn)


def test_pump_history_from_nightscout_treatments():
    from ingestion.models import Treatment
    from replay.inputs import pump_history

    at = 1_700_000_000_000
    h = 3_600_000
    tr = [Treatment(ts_ms=at - 8 * h, event_type="Correction Bolus", insulin_u=2.0),   # too old
          Treatment(ts_ms=at - 2 * h, event_type="Correction Bolus", insulin_u=1.5),
          Treatment(ts_ms=at - 30 * 60_000, event_type="SMB", insulin_u=0.4, is_smb=True),
          Treatment(ts_ms=at - 20 * 60_000, event_type="Temp Basal", absolute=2.1, rate=2.1,
                    duration_min=30),
          Treatment(ts_ms=at - 10 * 60_000, event_type="Temp Basal", rate=0.0, duration_min=60),
          Treatment(ts_ms=at + 60_000, event_type="SMB", insulin_u=0.5),                     # future
          Treatment(ts_ms=at - h, event_type="Meal Bolus", insulin_u=0.0, carbs_g=30)]
    hist = pump_history(tr, at, dia_h=6.0)
    boluses = [e["amount"] for e in hist if e["_type"] == "Bolus"]
    assert boluses == [0.4, 1.5]                  # newest first, as oref0 requires
    stamps = [e["timestamp"] for e in hist]
    assert stamps == sorted(stamps, reverse=True)
    temps = [e for e in hist if e["_type"] == "TempBasal"]
    durs = [e for e in hist if e["_type"] == "TempBasalDuration"]
    assert [t["rate"] for t in temps] == [0.0, 2.1] and [d["duration (min)"] for d in durs] == [60, 30]
    assert all(t["timestamp"] == d["timestamp"] for t, d in zip(temps, durs))
    assert all(e["timestamp"].endswith("Z") for e in hist)


def test_basal_schedule_shape():
    from replay.inputs import basal_schedule

    snap = _snapshot()
    snap.basal = [ProfileBlock(0, 0.8), ProfileBlock(6 * 3600 + 1800, 1.1)]
    sched = basal_schedule(snap)
    assert sched == [{"i": 0, "start": "00:00:00", "minutes": 0, "rate": 0.8},
                     {"i": 1, "start": "06:30:00", "minutes": 390, "rate": 1.1}]


# --- profile switches and temp targets in force at a cycle (in_force) ---

H = 3_600_000
T0 = 1_700_000_000_000 - (1_700_000_000_000 % 86_400_000)      # a UTC midnight


def _switch(ts, pct=100, shift=0, dur=0, pj=None):
    from ingestion.models import Treatment
    return Treatment(ts_ms=ts, event_type="Profile Switch", duration_min=dur, percentage=pct,
                     timeshift_h=shift, profile_json=pj)


def _tt(ts, low, high, dur):
    from ingestion.models import Treatment
    return Treatment(ts_ms=ts, event_type="Temporary Target", duration_min=dur,
                     target_low_mgdl=low, target_high_mgdl=high)


def test_percentage_switch_scales_and_a_temporary_one_reverts():
    from replay.inputs import in_force
    tr = [_switch(T0, pct=120), _switch(T0 + 2 * H, pct=150, dur=60)]
    snap, _ = in_force(_snapshot(), tr, T0 + H)
    assert snap.basal[0].value == 1.2 and abs(snap.isf_mgdl[0].value - 50 / 1.2) < 1e-9
    snap, _ = in_force(_snapshot(), tr, T0 + 2 * H + 30 * 60_000)
    assert snap.basal[0].value == 1.5 and abs(snap.carb_ratio[0].value - 10 / 1.5) < 1e-9
    snap, _ = in_force(_snapshot(), tr, T0 + 4 * H)          # the 150% has run out
    assert snap.basal[0].value == 1.2
    assert in_force(_snapshot(), tr, T0 - 1)[0].basal[0].value == 1.0


def test_switch_with_its_own_profile_and_timeshift():
    import json
    from replay.inputs import build_profile, in_force
    pj = json.dumps({"units": "mmol", "dia": 5, "timezone": "UTC",
                     "basal": [{"timeAsSeconds": 0, "value": 0.5}, {"timeAsSeconds": 6 * 3600, "value": 1.0}],
                     "sens": [{"timeAsSeconds": 0, "value": 2.0}], "carbratio": [{"timeAsSeconds": 0, "value": 8}],
                     "target_low": [{"timeAsSeconds": 0, "value": 5.5}],
                     "target_high": [{"timeAsSeconds": 0, "value": 5.5}]})
    snap, _ = in_force(_snapshot(), [_switch(T0 - 24 * H, shift=1, pj=pj)], T0 + 6 * H + 30 * 60_000)
    prof, _ = build_profile(snap, {"max_iob": 6.0}, T0 + 6 * H + 30 * 60_000)
    assert prof["current_basal"] == 0.5          # the 06:00 block starts at 07:00 with +1 h
    assert abs(prof["sens"] - 2.0 * 18.018) < 0.1 and prof["carb_ratio"] == 8
    prof, _ = build_profile(snap, {"max_iob": 6.0}, T0 + 7 * H + 30 * 60_000)
    assert prof["current_basal"] == 1.0


def test_temp_target_runs_its_length_and_a_zero_length_one_cancels():
    from replay.inputs import in_force
    tr = [_tt(T0, 140, 140, 60), _tt(T0 + 2 * H, 80, 80, 120), _tt(T0 + 3 * H, 80, 80, 0)]
    assert in_force(_snapshot(), tr, T0 + 30 * 60_000)[1] == (140, 140)
    assert in_force(_snapshot(), tr, T0 + 90 * 60_000)[1] is None
    assert in_force(_snapshot(), tr, T0 + 2.5 * H)[1] == (80, 80)
    assert in_force(_snapshot(), tr, T0 + 3.5 * H)[1] is None


def test_from_cycle_applies_the_temp_target():
    cyc = DeviceStatusCycle(ts_ms=T0 + 30 * 60_000, bg_mgdl=150, iob=1.0)
    entries = _entries(cyc.ts_ms, [(0, 150), (5, 148), (15, 140)])
    req, _ = from_cycle(cyc, _snapshot(), entries, settings={"max_iob": 6.0},
                        treatments=[_tt(T0, 140, 150, 60)])
    p = req["profile"]
    assert (p["min_bg"], p["max_bg"], p["target_bg"], p["temptargetSet"]) == (140, 150, 145.0, True)
    req, _ = from_cycle(cyc, _snapshot(), entries, settings={"max_iob": 6.0}, treatments=[])
    assert req["profile"]["target_bg"] == 105.0 and "temptargetSet" not in req["profile"]


def test_aaps3_millisecond_timeshift_and_the_persons_own_zone():
    import json
    from ingestion.normalise import normalise_treatment
    from replay.inputs import build_profile, in_force
    pj = json.dumps({"units": "mg/dl", "timezone": "UTC",
                     "basal": [{"timeAsSeconds": 0, "value": 0.5}, {"timeAsSeconds": 6 * 3600, "value": 1.0}],
                     "sens": [{"timeAsSeconds": 0, "value": 50}], "carbratio": [{"timeAsSeconds": 0, "value": 8}],
                     "target_low": [{"timeAsSeconds": 0, "value": 100}], "target_high": [{"timeAsSeconds": 0, "value": 100}]})
    sw = normalise_treatment({"eventType": "Profile Switch", "date": T0 - 24 * H, "duration": 0,
                              "percentage": 100, "timeshift": 3_600_000, "profileJson": pj})
    assert sw.timeshift_h == 1
    at = T0 + 6 * H + 30 * 60_000
    snap, _ = in_force(_snapshot(), [sw], at)
    assert build_profile(snap, {"max_iob": 6.0}, at)[0]["current_basal"] == 0.5
    # the switch says UTC; the person's profile says Europe/London, which is UTC+1 in summer
    summer = 1_752_000_000_000 - (1_752_000_000_000 % 86_400_000)      # a July midnight UTC
    snap, _ = in_force(_snapshot(tz="Europe/London"), [sw], summer + 5 * H + 30 * 60_000)
    assert snap.timezone == "Europe/London"
    # 05:30 UTC is 06:30 in London, inside the shifted 07:00 block's predecessor
    assert build_profile(snap, {"max_iob": 6.0}, summer + 5 * H + 30 * 60_000)[0]["current_basal"] == 0.5
    assert build_profile(snap, {"max_iob": 6.0}, summer + 6 * H + 30 * 60_000)[0]["current_basal"] == 1.0


def test_deleted_switch_and_temp_target_are_dropped():
    from ingestion.normalise import normalise_treatment
    for ev in ("Profile Switch", "Temporary Target"):
        assert normalise_treatment({"eventType": ev, "date": T0, "isValid": False, "duration": 60}) is None
        assert normalise_treatment({"eventType": ev, "date": T0, "isValid": True, "duration": 60}) is not None


def test_lasting_change_is_reported_and_temporary_ones_are_not():
    from replay.inputs import lasting_change
    week = 7 * 24 * H
    assert lasting_change(_snapshot(), [], T0, T0 + week) is None
    assert lasting_change(_snapshot(), [_switch(T0 + 24 * H, pct=150, dur=120)], T0, T0 + week) is None
    assert lasting_change(_snapshot(), [_switch(T0 + 24 * H, pct=105)], T0, T0 + week) is None
    ch = lasting_change(_snapshot(), [_switch(T0 + 3 * 24 * H, pct=120)], T0, T0 + week)
    assert ch["ts_ms"] == T0 + 3 * 24 * H and ch["basal"] == 1.2 and ch["isf"] == round(1 / 1.2, 2)
    # a switch before the window is the starting point, not a change inside it
    assert lasting_change(_snapshot(), [_switch(T0 - H, pct=120)], T0, T0 + week) is None


def test_daily_mean_weights_blocks_by_length():
    from replay.inputs import _daily_mean
    assert _daily_mean([ProfileBlock(0, 1.0), ProfileBlock(18 * 3600, 2.0)]) == 1.25
    assert _daily_mean([ProfileBlock(6 * 3600, 2.0)]) == 2.0


def test_lasting_change_catches_a_switch_that_went_out_and_came_back():
    from replay.inputs import _daily_mean, lasting_change
    week = 7 * 24 * H
    ch = lasting_change(_snapshot(), [_switch(T0 + 24 * H, pct=130), _switch(T0 + 4 * 24 * H, pct=100)],
                        T0, T0 + week)
    assert ch is not None and ch["ts_ms"] == T0 + 4 * 24 * H and ch["basal"] == round(1 / 1.3, 2)
    # a first block after midnight: the last block runs on until it
    assert _daily_mean([ProfileBlock(6 * 3600, 1.0), ProfileBlock(18 * 3600, 2.0)]) == 1.5


def test_build_profile_keeps_each_smb_switch_and_turns_uam_on():
    at = 1_700_000_000_000
    aaps = {"max_iob": 6.0, "enable_smb": True, "enable_smb_always": False, "enable_smb_with_cob": True}
    p, _ = build_profile(_snapshot(), aaps, at)
    assert (p["enableSMB_always"], p["enableSMB_with_COB"], p["enableSMB_after_carbs"],
            p["enableSMB_with_temptarget"]) == (False, True, True, True)
    assert p["enableUAM"] is True                  # oref0 reads enableUAM; UAM follows SMB
    trio = {"max_iob": 6.0, "enable_smb_always": False, "enable_smb_with_cob": True,
            "enable_smb_uam": False}
    p, _ = build_profile(_snapshot(), trio, at)    # no master switch: on because one switch is
    assert (p["enableSMB_always"], p["enableSMB_with_COB"], p["enableUAM"]) == (False, True, False)
    p, _ = build_profile(_snapshot(), {"max_iob": 6.0, "enable_smb": False,
                                       "enable_smb_always": True}, at)
    assert not any(p[k] for k in ("enableSMB_always", "enableSMB_with_COB", "enableUAM"))


def test_build_profile_daily_basal_is_the_largest_scheduled_rate():
    snap = _snapshot()
    snap = ProfileSnapshot(**{**snap.__dict__, "basal": [ProfileBlock(0, 0.8), ProfileBlock(43200, 1.6)]})
    p, _ = build_profile(snap, {"max_iob": 6.0}, at_ms=0)     # 00:00 UTC, on the 0.8 block
    assert (p["current_basal"], p["max_daily_basal"]) == (0.8, 1.6)


def test_build_profile_low_tt_default_and_trio_high_bg_switch():
    p, _ = build_profile(_snapshot(), {"max_iob": 6.0, "enable_smb": True}, 0)
    assert p["enableSMB_with_temptarget"] is True              # AndroidAPS default
    p, _ = build_profile(_snapshot(), {"max_iob": 6.0, "enable_smb_always": True}, 0)
    assert p["enableSMB_with_temptarget"] is False             # Trio default
    trio = {"max_iob": 6.0, "enable_smb_always": False, "enable_smb_high_bg": True,
            "enable_smb_high_bg_target": 160}
    p, _ = build_profile(_snapshot(), trio, 0)
    assert (p["enableSMB_high_bg"], p["enableSMB_high_bg_target"], p["enableSMB_always"]) == (True, 160, False)
