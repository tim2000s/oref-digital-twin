"""Raw Nightscout JSON -> normalised dataclasses.

Pure functions, no network. Each `normalise_*` takes a single raw document (a dict as
returned by the Nightscout REST API) and returns a model, or ``None`` if the document
lacks a usable timestamp (in which case the caller drops it and it is counted).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import (
    DeviceStatusCycle,
    GlucoseReading,
    ProfileBlock,
    ProfileSnapshot,
    Treatment,
    to_mgdl,
)


def parse_iso_ms(s: str | None) -> int | None:
    """Parse a Nightscout ISO-8601 ``created_at`` into epoch milliseconds (UTC)."""
    if not s or not isinstance(s, str):
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _doc_ts_ms(doc: dict[str, Any]) -> int | None:
    """Best-effort timestamp for any NS doc: numeric ``date``/``mills`` or ISO fields."""
    for key in ("date", "mills"):
        v = doc.get(key)
        if isinstance(v, (int, float)) and v > 0:
            return int(v)
    for key in ("created_at", "dateString", "timestamp", "sysTime"):
        ms = parse_iso_ms(doc.get(key))
        if ms is not None:
            return ms
    return None


def _num(v: Any) -> float | None:
    if isinstance(v, bool):  # guard: bools are ints in Python
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def normalise_entry(doc: dict[str, Any]) -> GlucoseReading | None:
    ts = _doc_ts_ms(doc)
    if ts is None:
        return None
    sgv = _num(doc.get("sgv"))
    if sgv is None:
        sgv = _num(doc.get("mbg"))  # manual BG fallback
    return GlucoseReading(
        ts_ms=ts,
        sgv_mgdl=sgv,
        direction=doc.get("direction"),
        device=doc.get("device"),
        raw_type=doc.get("type"),
    )


_SMB_HINTS = ("smb",)


def normalise_treatment(doc: dict[str, Any]) -> Treatment | None:
    ts = _doc_ts_ms(doc)
    if ts is None:
        return None
    entered_by = doc.get("enteredBy") or ""
    event_type = doc.get("eventType")
    is_smb = bool(doc.get("isSMB")) or any(
        h in f"{entered_by} {event_type}".lower() for h in _SMB_HINTS
    )
    return Treatment(
        ts_ms=ts,
        event_type=event_type,
        insulin_u=_num(doc.get("insulin")),
        carbs_g=_num(doc.get("carbs")),
        duration_min=_num(doc.get("duration")),
        rate=_num(doc.get("rate")),
        absolute=_num(doc.get("absolute")),
        target_low_mgdl=_num(doc.get("targetBottom")),
        target_high_mgdl=_num(doc.get("targetTop")),
        is_smb=is_smb,
        entered_by=entered_by or None,
        notes=doc.get("notes"),
    )


def _pred(preds: Any, key: str) -> list[float] | None:
    if isinstance(preds, dict):
        arr = preds.get(key)
        if isinstance(arr, list):
            return [float(x) for x in arr if isinstance(x, (int, float))]
    return None


def normalise_devicestatus(doc: dict[str, Any]) -> DeviceStatusCycle | None:
    ts = _doc_ts_ms(doc)
    if ts is None:
        return None
    openaps = doc.get("openaps")
    if not isinstance(openaps, dict):
        # No oref payload (e.g. a pure uploader/pump status) — not a loop cycle.
        return None
    # Prefer `enacted`, fall back to `suggested`; oref writes both, enacted wins.
    enacted = openaps.get("enacted") if isinstance(openaps.get("enacted"), dict) else {}
    suggested = openaps.get("suggested") if isinstance(openaps.get("suggested"), dict) else {}
    src = {**suggested, **enacted}  # enacted overrides suggested
    iob_block = openaps.get("iob")
    if isinstance(iob_block, list) and iob_block:
        iob_block = iob_block[0]
    iob_val = _num(iob_block.get("iob")) if isinstance(iob_block, dict) else _num(src.get("IOB"))
    # NOTE: in oref `units` is the SMB bolus amount (a number), not a display unit. Only
    # keep it as a reported-unit string when it genuinely is one (e.g. "mg/dl").
    units_val = src.get("units")
    units = units_val if isinstance(units_val, str) else None

    return DeviceStatusCycle(
        ts_ms=ts,
        device=doc.get("device"),
        bg_mgdl=_num(src.get("bg")),
        iob=iob_val if iob_val is not None else _num(src.get("IOB")),
        cob=_num(src.get("COB")),
        eventual_bg_mgdl=_num(src.get("eventualBG")),
        insulin_req=_num(src.get("insulinReq")),
        sensitivity_ratio=_num(src.get("sensitivityRatio")),
        reason=src.get("reason"),
        enacted_smb_u=_num(enacted.get("units")),  # SMB bolus, U
        enacted_rate=_num(enacted.get("rate")),
        enacted_duration_min=_num(enacted.get("duration")),
        pred_iob=_pred(src.get("predBGs"), "IOB"),
        pred_zt=_pred(src.get("predBGs"), "ZT"),
        pred_cob=_pred(src.get("predBGs"), "COB"),
        pred_uam=_pred(src.get("predBGs"), "UAM"),
        device_reported_units=units,
        raw_openaps=openaps,
    )


def _blocks(arr: Any, units: str | None, is_glucose: bool) -> list[ProfileBlock]:
    out: list[ProfileBlock] = []
    if not isinstance(arr, list):
        return out
    for item in arr:
        if not isinstance(item, dict):
            continue
        val = _num(item.get("value"))
        if val is None:
            continue
        if is_glucose:
            val = to_mgdl(val, units)
        secs = item.get("timeAsSeconds")
        if secs is None:
            secs = 0
        out.append(ProfileBlock(seconds_from_midnight=int(secs), value=val))
    return out


def normalise_profile(doc: dict[str, Any]) -> ProfileSnapshot | None:
    """Normalise the *default* store block of a Nightscout profile document."""
    store = doc.get("store")
    if not isinstance(store, dict) or not store:
        return None
    default_name = doc.get("defaultProfile")
    block = store.get(default_name) if default_name in store else next(iter(store.values()))
    if not isinstance(block, dict):
        return None
    units = block.get("units")
    return ProfileSnapshot(
        valid_from_ms=parse_iso_ms(doc.get("startDate")) or _doc_ts_ms(doc),
        units=units,
        dia_h=_num(block.get("dia")),
        timezone=block.get("timezone"),
        basal=_blocks(block.get("basal"), units, is_glucose=False),
        isf_mgdl=_blocks(block.get("sens"), units, is_glucose=True),
        carb_ratio=_blocks(block.get("carbratio"), units, is_glucose=False),
        target_low_mgdl=_blocks(block.get("target_low"), units, is_glucose=True),
        target_high_mgdl=_blocks(block.get("target_high"), units, is_glucose=True),
    )
