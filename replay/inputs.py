"""Reconstruct oref determine-basal requests from normalised data.

The loop logs its decision, not every input, so reconstruction is best-effort and each request
carries fidelity warnings.

Insulin on board is rebuilt from the Nightscout treatments by oref0's own lib/iob, run inside
the oracle (see oracle/request.js). determine-basal needs the 48-step forward projection that
library returns: it walks it to build every predicted-glucose curve, and given a single IOB
object instead it throws inside a try block, leaves minPredBG and minGuardBG at 999 and so
disables its own low-glucose guard. Until 30 September 2026 this module passed the single
object logged in devicestatus, which made absolute replayed decisions wrong in the unsafe
direction. A cycle without treatments to rebuild from is now refused.

Still approximated: `currenttemp`, the temp basal running at decision time, is assumed none.
The profile comes from the Nightscout profile and the user's settings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

from typing import Any

from ingestion.models import DeviceStatusCycle, GlucoseReading, ProfileSnapshot, Treatment

# oref profile fields that must come from settings (not the Nightscout profile)
REQUIRED_SETTINGS = ("max_iob",)

# insulin curves oref0's lib/iob knows, with its default peak for each
INSULIN_CURVES = {"rapid-acting": 75, "ultra-rapid": 55, "bilinear": None}


def _seconds_of_day(ts_ms: int, tz: str | None) -> int:
    tzinfo = timezone.utc
    if tz:
        try:
            from zoneinfo import ZoneInfo

            tzinfo = ZoneInfo(tz)
        except Exception:
            tzinfo = timezone.utc
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=tzinfo)
    return dt.hour * 3600 + dt.minute * 60 + dt.second


def _block_value_at(blocks, sod: int, default: float | None) -> float | None:
    if not blocks:
        return default
    ordered = sorted(blocks, key=lambda b: b.seconds_from_midnight)
    chosen = ordered[0].value
    for b in ordered:
        if b.seconds_from_midnight <= sod:
            chosen = b.value
        else:
            break
    return chosen


_sorted_cgm: dict = {}


def _cgm_points(entries: list[GlucoseReading]) -> list[tuple]:
    """(ts_ms, mg/dL) for every reading, sorted, built once per entries list.

    Sorting the whole stream again for every cycle was the largest cost of building a week of
    replay requests (4.0 s of 6.6 in CPython, several times that in the browser).
    """
    key = (id(entries), len(entries))
    if _sorted_cgm.get("key") != key:
        _sorted_cgm.clear()
        _sorted_cgm.update(key=key, pts=sorted((r.ts_ms, r.sgv_mgdl) for r in entries
                                               if r.sgv_mgdl is not None))
    return _sorted_cgm["pts"]


def build_glucose_status(entries: list[GlucoseReading], at_ms: int) -> dict | None:
    """oref glucose_status from the CGM stream around `at_ms` (oref field names)."""
    import bisect

    pts = _cgm_points(entries)
    end = bisect.bisect_right(pts, (at_ms, float("inf")))     # readings at or before at_ms
    if not end:
        return None
    cur_ts, cur = pts[end - 1]

    def at_offset(minutes: int) -> float | None:
        target = cur_ts - minutes * 60_000
        best, best_d = None, 4 * 60_000  # within 4 min
        for i in range(end - 1, -1, -1):
            ts, v = pts[i]
            d = abs(ts - target)
            if d <= best_d:
                best, best_d = v, d
            if ts < target - best_d:
                break
        return best

    g5, g15, g45 = at_offset(5), at_offset(15), at_offset(45)
    delta = round(cur - g5, 1) if g5 is not None else 0.0
    short_avg = round((cur - g15) / 3.0, 1) if g15 is not None else delta
    long_avg = round((cur - g45) / 9.0, 1) if g45 is not None else short_avg
    return {
        "glucose": cur,
        "delta": delta,
        "short_avgdelta": short_avg,
        "long_avgdelta": long_avg,
        "date": cur_ts,
    }


def build_profile(snapshot: ProfileSnapshot, settings: dict, at_ms: int) -> tuple[dict, list[str]]:
    """Assemble an oref profile from the Nightscout profile + the user's settings.

    Returns (profile, warnings). Missing required settings are reported, not guessed.
    """
    warnings: list[str] = []
    tz = snapshot.timezone
    sod = _seconds_of_day(at_ms, tz)

    basal = _block_value_at(snapshot.basal, sod, None)
    sens = _block_value_at(snapshot.isf_mgdl, sod, None)
    cr = _block_value_at(snapshot.carb_ratio, sod, None)
    low = _block_value_at(snapshot.target_low_mgdl, sod, None)
    high = _block_value_at(snapshot.target_high_mgdl, sod, None)
    target = None
    if low is not None and high is not None:
        target = round((low + high) / 2.0, 1)

    for name, val in (("basal", basal), ("sens", sens), ("carb_ratio", cr), ("target", target)):
        if val is None:
            warnings.append(f"profile is missing {name} — replay for this cycle is unreliable.")

    for key in REQUIRED_SETTINGS:
        if settings.get(key) is None:
            warnings.append(f"settings missing '{key}' — required for faithful replay.")

    max_basal = settings.get("max_basal", (basal or 0.0) * 4)
    # Clamp exactly as replay.settings_delta does. Otherwise a negative baseline is compared
    # against a clamped altered run and the counterfactual diff is meaningless while still
    # rendering as a real delivery delta.
    max_iob = settings.get("max_iob")
    if max_iob is not None and float(max_iob) < 0:
        warnings.append(f"max_iob {max_iob} is negative — clamped to 0 for replay.")
        max_iob = 0.0
    if max_basal is not None and float(max_basal) < 0:
        warnings.append(f"max_basal {max_basal} is negative — clamped to 0 for replay.")
        max_basal = 0.0
    profile = {
        "dia": snapshot.dia_h or 6.0,
        "current_basal": basal or 0.0,
        "max_basal": max_basal,
        "max_daily_basal": basal or 0.0,
        "max_daily_safety_multiplier": settings.get("max_daily_safety_multiplier", 3),
        "current_basal_safety_multiplier": settings.get("current_basal_safety_multiplier", 4),
        "max_iob": max_iob,
        "sens": sens,
        "carb_ratio": cr,
        "min_bg": low if low is not None else target,
        "max_bg": high if high is not None else target,
        "target_bg": target,
        "min_5m_carbimpact": settings.get("min_5m_carbimpact", 8),
        "type": "current",
        "enableSMB_always": bool(settings.get("enable_smb", False)),
        "enableSMB_with_COB": bool(settings.get("enable_smb", False)),
        "enableSMB_after_carbs": bool(settings.get("enable_smb", False)),
        "enableSMB_uam": bool(settings.get("enable_smb_uam", settings.get("enable_smb", False))),
        "maxSMBBasalMinutes": settings.get("max_smb_minutes", 30),
        "maxUAMSMBBasalMinutes": settings.get("max_uam_minutes", 30),
    }

    # These defaults are permissive: absent an SMB cap we assume 30 minutes, and absent a
    # max basal we assume 4x the scheduled rate. If SMB is on and the real caps are unknown,
    # the replay may allow more insulin than the user's own configuration would. Say so —
    # a substituted dosing bound must never pass silently.
    if profile["enableSMB_always"] or profile["enableSMB_uam"]:
        for friendly, oref_field in (("max_smb_minutes", "maxSMBBasalMinutes"),
                                     ("max_uam_minutes", "maxUAMSMBBasalMinutes")):
            if settings.get(friendly) is None:
                warnings.append(f"{friendly} unknown — assumed {profile[oref_field]} min; "
                                f"replay may permit more SMB than your settings allow.")
    if settings.get("max_basal") is None:
        warnings.append(f"max_basal unknown — assumed {max_basal} U/h (4x scheduled basal).")

    return profile, warnings


def _num0(v: Any) -> float:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0


def _iob_data_from_cycle(cycle: DeviceStatusCycle) -> tuple[dict, bool]:
    """Real iob_data (iob, activity, basaliob, bolusiob) from openaps.iob when present.

    Returns (iob_data, activity_known). Using the logged iob_data — activity included —
    makes bgi/eventualBG faithful instead of assuming activity 0.
    """
    raw = cycle.raw_openaps or {}
    ib = raw.get("iob")
    if isinstance(ib, list) and ib:
        ib = ib[0]
    if isinstance(ib, dict) and ib.get("iob") is not None:
        return ({
            "iob": _num0(ib.get("iob")),
            "activity": _num0(ib.get("activity")),
            "basaliob": _num0(ib.get("basaliob")),
            "bolusiob": _num0(ib.get("bolusiob")),
            "time": cycle.ts_ms,
        }, True)
    return ({"iob": cycle.iob or 0.0, "activity": 0.0, "basaliob": 0.0, "bolusiob": 0.0,
             "time": cycle.ts_ms}, False)


@lru_cache(maxsize=65536)
def _iso(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# A temp basal that started this long before the window can still run into it. AndroidAPS
# and Trio cap a temp at 12 hours.
_LONGEST_TEMP_MS = 12 * 3_600_000
_index: dict = {}


def _window(treatments: list[Treatment], lo: int, hi: int) -> list[Treatment]:
    """The treatments with lo <= ts_ms <= hi, in their original order.

    Every cycle of a replay asks for its own window of the same list, and scanning the whole
    list each time made building the requests for a week the slowest step of the settings
    tests in the browser (about 20 s of 120). The list is sorted once and bisected; the cache
    holds the last list only, keyed by identity and length.
    """
    import bisect

    key = (id(treatments), len(treatments))
    if _index.get("key") != key:
        order = sorted(range(len(treatments)), key=lambda i: treatments[i].ts_ms)
        _index.clear()
        _index.update(key=key, order=order, ts=[treatments[i].ts_ms for i in order])
    a = bisect.bisect_left(_index["ts"], lo)
    b = bisect.bisect_right(_index["ts"], hi)
    return [treatments[i] for i in sorted(_index["order"][a:b])]


def pump_history(treatments: list[Treatment], at_ms: int, dia_h: float) -> list[dict]:
    """Nightscout boluses and temp basals as oref0 pump-history records, up to `at_ms`.

    Everything that can still be acting is included: boluses and SMBs from the last DIA plus
    an hour, and any temp basal that ran into that window. Temp basals use the absolute rate;
    AndroidAPS uploads it as `absolute` and Trio as `rate`. oref0 pairs a TempBasal with the
    TempBasalDuration carrying the same timestamp.

    The list is returned newest first, as a pump reports it. oref0's history reader skips any
    record newer than the one before it, treating it as a duplicate from an overlapping
    download, so an oldest-first list silently loses every record after the first.
    """
    lo = at_ms - int((dia_h + 1.0) * 3_600_000)
    out: list[dict] = []
    for t in _window(treatments, lo - _LONGEST_TEMP_MS, at_ms):
        if t.ts_ms > at_ms:
            continue
        if t.insulin_u is not None and t.insulin_u > 0:
            if t.ts_ms >= lo:
                out.append({"_type": "Bolus", "amount": round(float(t.insulin_u), 3),
                            "timestamp": _iso(t.ts_ms)})
        elif (t.event_type or "").lower() == "temp basal":
            rate = t.absolute if t.absolute is not None else t.rate
            if rate is None or t.duration_min is None:
                continue
            if t.ts_ms + t.duration_min * 60_000 < lo:
                continue
            ts = _iso(t.ts_ms)
            out.append({"_type": "TempBasal", "temp": "absolute", "rate": float(rate),
                        "timestamp": ts})
            out.append({"_type": "TempBasalDuration", "duration (min)": float(t.duration_min),
                        "timestamp": ts})
    out.reverse()
    return out


def basal_schedule(snapshot: ProfileSnapshot) -> list[dict]:
    """The Nightscout basal profile in oref0's basalprofile shape."""
    out = []
    for i, b in enumerate(sorted(snapshot.basal, key=lambda b: b.seconds_from_midnight)):
        m = b.seconds_from_midnight // 60
        out.append({"i": i, "start": f"{m // 60:02d}:{m % 60:02d}:00", "minutes": m,
                    "rate": float(b.value)})
    return out


def iob_inputs(snapshot: ProfileSnapshot, settings: dict, treatments: list[Treatment],
               at_ms: int) -> tuple[dict, list[str]]:
    """What oref0's lib/iob needs to produce the 48-step projection for one cycle."""
    warnings: list[str] = []
    dia = snapshot.dia_h or 6.0
    curve = settings.get("insulin_curve")
    if curve not in INSULIN_CURVES:
        if curve is not None:
            warnings.append(f"insulin curve '{curve}' not known to oref0 — assumed rapid-acting.")
        else:
            warnings.append("insulin curve unknown — assumed rapid-acting (peak 75 min).")
        curve = "rapid-acting"
    peak = settings.get("insulin_peak_min")
    profile = {"dia": dia, "curve": curve, "basalprofile": basal_schedule(snapshot),
               "current_basal": _block_value_at(snapshot.basal, _seconds_of_day(at_ms, snapshot.timezone), 0.0)}
    if peak is not None:
        profile.update({"useCustomPeakTime": True, "insulinPeakTime": float(peak)})
    return ({"history": pump_history(treatments, at_ms, dia), "profile": profile,
             "clock": _iso(at_ms), "tz": snapshot.timezone}, warnings)


# fidelity warning inherent to devicestatus-based reconstruction
_INHERENT_FIDELITY = [
    "currenttemp unknown from devicestatus — assumed none.",
]


def from_cycle(
    cycle: DeviceStatusCycle,
    snapshot: ProfileSnapshot,
    entries: list[GlucoseReading],
    settings: dict,
    treatments: list[Treatment] | None = None,
    *,
    micro_bolus_allowed: bool = True,
) -> tuple[dict | None, list[str]]:
    """Build a determine-basal request for one cycle. Returns (request|None, warnings).

    `treatments` are the Nightscout treatments the insulin-on-board projection is rebuilt
    from. Without them the cycle is refused: the logged IOB alone cannot give oref the
    projection its low-glucose guard depends on.
    """
    warnings: list[str] = []
    if treatments is None:
        return None, ["no treatments to rebuild insulin on board from — cycle not replayed."]
    gs = build_glucose_status(entries, cycle.ts_ms)
    if gs is None:
        gs = ({"glucose": cycle.bg_mgdl, "delta": 0.0, "short_avgdelta": 0.0,
               "long_avgdelta": 0.0, "date": cycle.ts_ms} if cycle.bg_mgdl else None)
        warnings.append("no CGM around this cycle — glucose_status approximated from devicestatus.")
    if gs is None:
        return None, warnings + ["no usable glucose for this cycle."]

    profile, pwarn = build_profile(snapshot, settings, cycle.ts_ms)
    warnings += pwarn
    if profile["max_iob"] is None or profile["target_bg"] is None:
        return None, warnings + ["cannot build a faithful profile (missing max_iob/target)."]

    warnings += _INHERENT_FIDELITY
    iob_in, iwarn = iob_inputs(snapshot, settings, treatments, cycle.ts_ms)
    warnings += iwarn
    # The logged IOB travels with the request only so the oracle can report how far oref's
    # rebuilt figure sits from it; determine-basal is given the rebuilt projection.
    logged, _ = _iob_data_from_cycle(cycle)
    request = {
        "glucose_status": gs,
        "currenttemp": {"duration": 0, "rate": 0, "temp": "absolute"},
        "iob_inputs": iob_in,
        "iob_logged": logged.get("iob"),
        "profile": profile,
        "autosens_data": {"ratio": cycle.sensitivity_ratio or 1.0},
        "meal_data": {"carbs": 0, "mealCOB": cycle.cob or 0},
        "microBolusAllowed": micro_bolus_allowed,
        "currentTime": cycle.ts_ms,
    }
    return request, warnings
