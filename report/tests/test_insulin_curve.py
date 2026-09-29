"""The insulin curve is chosen as the one whose rebuilt IOB best matches the logged IOB."""
from types import SimpleNamespace

from ingestion.models import DeviceStatusCycle, GlucoseReading, ProfileBlock, ProfileSnapshot
from report.browser import _choose_insulin_curve


def _snapshot():
    b = lambda v: [ProfileBlock(0, v)]
    return ProfileSnapshot(valid_from_ms=1, units="mg/dl", dia_h=6.0, timezone="UTC",
                           basal=b(1.0), isf_mgdl=b(50.0), carb_ratio=b(10.0),
                           target_low_mgdl=b(100.0), target_high_mgdl=b(100.0))


def _pull(n=30):
    base = 1_758_376_800_000
    cycles = [DeviceStatusCycle(ts_ms=base + i * 300_000, bg_mgdl=150, iob=1.0) for i in range(n)]
    entries = [GlucoseReading(ts_ms=c.ts_ms, sgv_mgdl=150) for c in cycles]
    return SimpleNamespace(devicestatus=cycles, treatments=[], entries=entries)


def fake_runner(requests):
    """Rebuilt IOB equals the logged 1.0 only on the Lyumjev preset."""
    out = []
    for r in requests:
        p = r["iob_inputs"]["profile"]
        match = p["curve"] == "ultra-rapid" and p.get("insulinPeakTime") == 45
        out.append({"ok": True, "rt": {}, "iob_rebuilt": 1.0 if match else 1.8})
    return out


def test_curve_matched_to_logged_iob():
    pull = _pull()
    settings, stats = _choose_insulin_curve(pull, {"max_iob": 6.0}, _snapshot(), pull.entries,
                                            fake_runner)
    assert stats["insulin_curve"] == "ultra-rapid peak 45"
    assert settings["insulin_curve"] == "ultra-rapid" and settings["insulin_peak_min"] == 45
    assert stats["insulin_curve_fit_u"]["rapid-acting"] > stats["insulin_curve_fit_u"]["ultra-rapid peak 45"]


def test_curve_named_in_settings_is_kept():
    pull = _pull()
    settings, stats = _choose_insulin_curve(pull, {"max_iob": 6.0, "insulin_curve": "rapid-acting"},
                                            _snapshot(), pull.entries, fake_runner)
    assert settings["insulin_curve"] == "rapid-acting" and stats["insulin_curve_source"] == "settings"
