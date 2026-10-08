"""Integration test against the REAL oref0 via Node.

Skips automatically when Node or the installed oref0 package is unavailable (e.g. CI
without `npm install` in replay/oracle), so the suite stays green everywhere while still
exercising the genuine controller where it exists.
"""

import shutil

import pytest

from ingestion.models import DeviceStatusCycle, GlucoseReading, ProfileBlock, ProfileSnapshot
from replay import OrefOracle, from_cycle, run_counterfactual
from replay.oracle_bridge import ORACLE_DIR

_node = shutil.which("node")
_oref0 = (ORACLE_DIR / "node_modules" / "oref0").exists()
pytestmark = pytest.mark.skipif(
    not (_node and _oref0),
    reason="node and/or oref0 not installed in replay/oracle (run npm install there)",
)


def _snapshot():
    b = lambda v: [ProfileBlock(0, v)]
    return ProfileSnapshot(valid_from_ms=1, units="mg/dl", dia_h=6.0, timezone="UTC",
                           basal=b(1.0), isf_mgdl=b(50.0), carb_ratio=b(10.0),
                           target_low_mgdl=b(100.0), target_high_mgdl=b(100.0))


def _high_rising_cycle(base=1_700_000_000_000):
    cyc = DeviceStatusCycle(ts_ms=base, bg_mgdl=180, iob=0.3, sensitivity_ratio=1.0)
    entries = [GlucoseReading(ts_ms=base - m * 60_000, sgv_mgdl=v)
               for m, v in [(0, 180), (5, 174), (15, 165), (45, 150)]]
    return cyc, entries


def test_real_oref_produces_a_decision():
    cyc, entries = _high_rising_cycle()
    req, _ = from_cycle(cyc, _snapshot(), entries, settings={"max_iob": 6.0, "enable_smb": True},
                        treatments=[])
    assert req is not None
    rt = OrefOracle().enacted([req])[0]
    assert rt is not None
    assert "eventualBG" in rt and rt.get("error") is None


def test_max_iob_zero_reduces_delivery_vs_baseline():
    cyc, entries = _high_rising_cycle()
    settings = {"max_iob": 6.0, "enable_smb": True, "max_smb_minutes": 60}
    req, _ = from_cycle(cyc, _snapshot(), entries, settings=settings, treatments=[])
    assert req is not None

    cf = run_counterfactual(OrefOracle(), [req], {"max_iob": 0.0}, ts_of=[cyc.ts_ms])
    # capping IOB at 0 cannot deliver MORE insulin into a high than the baseline
    assert cf.n_evaluated == 1
    assert cf.total_delta_u is not None and cf.total_delta_u <= 0.0


def _rising_after_bolus(base=1_758_376_800_000):
    """180 mg/dL rising 8 per 5 min, 3 U given an hour ago."""
    from ingestion.models import Treatment

    cyc = DeviceStatusCycle(ts_ms=base, bg_mgdl=180, iob=2.4, sensitivity_ratio=1.0)
    entries = [GlucoseReading(ts_ms=base - m * 60_000, sgv_mgdl=180 - 8 * m / 5)
               for m in (0, 5, 10, 15, 30, 45)]
    tr = [Treatment(ts_ms=base - 60 * 60_000, event_type="Correction Bolus", insulin_u=3.0)]
    return cyc, entries, tr


SETTINGS = {"max_iob": 6.0, "enable_smb": True, "max_smb_minutes": 30, "max_uam_minutes": 30,
            "max_basal": 3.0}


def test_rebuilt_projection_keeps_the_low_guard():
    """Regression for the single-IOB-object defect.

    With oref's own 48-step projection this case runs 0.13 U/h after a 0.3 U SMB, because the
    insulin still acting from the earlier 3 U is projected forward. Handed the single logged
    IOB object, determine-basal lost its predictions (minPredBG 999) and ran 2.45 U/h. Across
    225 scenarios checked on 30 September 2026 the single object changed the decision in 28,
    and gave more insulin in every one of them.
    """
    cyc, entries, tr = _rising_after_bolus()
    req, _ = from_cycle(cyc, _snapshot(), entries, settings=SETTINGS, treatments=tr)
    res = OrefOracle().evaluate([req])[0]
    assert res["ok"] and res["iob_steps"] == 48
    assert "minPredBG 999" not in res["rt"]["reason"]
    assert res["rt"]["rate"] < 0.5


def test_single_iob_object_is_refused_by_the_oracle():
    cyc, entries, tr = _rising_after_bolus()
    req, _ = from_cycle(cyc, _snapshot(), entries, settings=SETTINGS, treatments=tr)
    legacy = {k: v for k, v in req.items() if k != "iob_inputs"}
    legacy["iob_data"] = {"iob": 2.4, "activity": 0.02, "basaliob": 0.0, "bolusiob": 2.4,
                          "time": cyc.ts_ms}
    res = OrefOracle().evaluate([legacy])[0]
    assert not res["ok"] and "low-glucose guard" in res["error"]


def test_every_dose_in_the_history_is_counted():
    """oref0 skips records that arrive out of newest-first order, so a history in the wrong
    order loses every dose after the first. Three boluses must all count."""
    from ingestion.models import Treatment

    base = 1_758_376_800_000
    cyc = DeviceStatusCycle(ts_ms=base, bg_mgdl=150, iob=0.0, sensitivity_ratio=1.0)
    entries = [GlucoseReading(ts_ms=base - m * 60_000, sgv_mgdl=150) for m in (0, 5, 15, 45)]
    doses = [(170, 2.0), (90, 1.0), (20, 1.5)]
    one = []
    for ago, u in doses:
        tr = [Treatment(ts_ms=base - ago * 60_000, event_type="Correction Bolus", insulin_u=u)]
        req, _ = from_cycle(cyc, _snapshot(), entries, settings=SETTINGS, treatments=tr)
        one.append(OrefOracle().evaluate([req])[0]["iob_rebuilt"])
    tr = [Treatment(ts_ms=base - ago * 60_000, event_type="Correction Bolus", insulin_u=u)
          for ago, u in doses]
    req, _ = from_cycle(cyc, _snapshot(), entries, settings=SETTINGS, treatments=tr)
    together = OrefOracle().evaluate([req])[0]["iob_rebuilt"]
    assert all(v > 0.1 for v in one)
    assert abs(together - sum(one)) < 0.01


def _flat_day(hours=8, base=1_758_376_800_000):
    """Cycles every 5 minutes, glucose waving gently around 130, scheduled-rate temps.

    Perfectly flat CGM will not do: oref0 reads it as a stuck sensor and does nothing.
    """
    import math

    from ingestion.models import Treatment

    bg = lambda t: round(130 + 12 * math.sin(2 * math.pi * (t - base) / (100 * 60_000)), 1)
    n = hours * 12
    times = [base + i * 5 * 60_000 for i in range(n)]
    entries = [GlucoseReading(ts_ms=t, sgv_mgdl=bg(t)) for t in
               [base - m * 60_000 for m in range(60, 0, -5)] + times]
    temps = [Treatment(ts_ms=base - 6 * 3_600_000 + i * 30 * 60_000, event_type="Temp Basal",
                       absolute=1.0, duration_min=30) for i in range(12 + hours * 2)]
    cycles = [DeviceStatusCycle(ts_ms=t, bg_mgdl=bg(t), iob=0.0, sensitivity_ratio=1.0)
              for t in times]
    reqs = [from_cycle(c, _snapshot(), entries, SETTINGS, temps)[0] for c in cycles]
    assert all(r is not None for r in reqs)
    return reqs


def test_simulation_that_changes_nothing_matches_the_baseline_exactly():
    sim = OrefOracle().simulate({"cycles": _flat_day(), "scenarios": [{"label": "same"}]})
    s = sim["scenarios"][0]
    assert s["failed"] == 0
    assert all(d == 0 for d in s["du"]) and all(g == 0 for g in s["dbg"])


def test_simulated_basal_cut_raises_glucose_and_increase_lowers_it():
    sim = OrefOracle().simulate({"cycles": _flat_day(), "scenarios": [
        {"label": "less", "basal_scale": 0.7}, {"label": "more", "basal_scale": 1.3}]})
    less, more = (sum(s["dbg"]) / len(s["dbg"]) for s in sim["scenarios"])
    assert less > 1.0 and more < -1.0
