"""Validate and coerce extracted settings against the schema.

Whatever the source (vision on a screenshot, or the client-side decrypt), the raw
key/values land here. This maps source names to friendly keys, coerces types, range-checks,
and flags anything that must be confirmed by the user before it is trusted — never a silent
accept of an out-of-range or low-confidence insulin-relevant value (DESIGN §5.2).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .schema import SETTINGS, _to_bool, alias_rank, resolve_alias

LOW_CONFIDENCE = 0.8


@dataclass
class SettingIssue:
    key: str                        # friendly key, or the raw name for unknown_key
    kind: str                       # unknown_key | wrong_type | out_of_range | needs_confirm
                                    # | duplicate | conflict (a duplicate with another value)
    message: str
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedSettings:
    values: dict[str, Any] = field(default_factory=dict)
    issues: list[SettingIssue] = field(default_factory=list)
    needs_confirm: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)   # parsed, but not safe to act on

    def replay_settings(self) -> dict[str, Any]:
        """The subset the replay oracle can vary (replay_lever specs only).

        Anything out of range, zero-valued or read with low confidence is withheld: an
        unconfirmed insulin-relevant number must never silently drive a counterfactual
        (DESIGN §5.2). It stays in `values` so the caller can display it and ask.
        """
        blocked = set(self.blocked)
        return {k: v for k, v in self.values.items()
                if SETTINGS[k].replay_lever and k not in blocked}

    def is_clean(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "values": self.values,
            "needs_confirm": self.needs_confirm,
            "blocked": self.blocked,
            "issues": [i.to_dict() for i in self.issues],
        }


# AndroidAPS names its insulin by which plugin is on; these are the oref curves (and peaks) they run.
_AAPS_INSULIN = {
    "InsulinOrefRapidActingPlugin": ("rapid-acting", None),
    "InsulinOrefUltraRapidActingPlugin": ("ultra-rapid", None),
    "InsulinLyumjevPlugin": ("ultra-rapid", 45),
    "InsulinOrefFreePeakPlugin": (None, "insulin_oref_peak"),
}


def _insulin(raw: dict[str, Any]) -> dict[str, Any]:
    """Insulin curve and peak from an AAPS plugin choice or Trio's custom-peak switch."""
    out: dict[str, Any] = {}
    for plugin, (curve, peak) in _AAPS_INSULIN.items():
        if _to_bool(raw.get(f"ConfigBuilder_Enabled_INSULIN_{plugin}", False)):
            if isinstance(peak, str):       # free peak: oref0 takes 50-120 min on rapid-acting,
                peak = raw.get(peak)        # 35-100 on ultra-rapid, so below 50 needs ultra-rapid
                try:
                    curve = "ultra-rapid" if float(peak) < 50 else "rapid-acting"
                except (TypeError, ValueError):
                    curve = None            # left to the peak's own check, and the curve to the fit
            if curve:
                out["curve"] = curve
            if peak is not None:
                out["insulin_peak_min"] = peak
    if _to_bool(raw.get("useCustomPeakTime", False)) and raw.get("insulinPeakTime") is not None:
        out["insulin_peak_min"] = raw["insulinPeakTime"]
    return out


def validate(raw: dict[str, Any], confidences: dict[str, float] | None = None) -> ValidatedSettings:
    confidences = confidences or {}
    raw = {**_insulin(raw), **raw}      # a name the file gives itself wins over one derived
    out = ValidatedSettings()
    needs: set[str] = set()
    blocked: set[str] = set()

    used: dict[str, str] = {}
    # Several source names can fill one setting (an AAPS export holds both max IOB keys);
    # the alias order decides, not the order of keys in the file.
    for raw_name, raw_val in sorted(raw.items(), key=lambda kv: alias_rank(kv[0])):
        key = resolve_alias(raw_name)
        if key is None:
            out.issues.append(SettingIssue(raw_name, "unknown_key",
                                           f"'{raw_name}' is not a recognised setting.", raw_val))
            continue
        spec = SETTINGS[key]
        coerced, ok = spec.coerce(raw_val)
        if key in used:
            differs = ok and key in out.values and coerced != out.values[key]
            out.issues.append(SettingIssue(
                key, "conflict" if differs else "duplicate",
                f"'{raw_name}' ({raw_val}) ignored: {key} was read from '{used[key]}'.", raw_val))
            continue
        used[key] = raw_name
        if not ok:
            # The preferred name is unreadable: withhold the setting rather than fall back to a
            # lower-ranked name, which may belong to a plugin the person does not run.
            out.issues.append(SettingIssue(key, "wrong_type",
                                           f"'{raw_val}' is not a valid {spec.kind} for {key}.", raw_val))
            needs.add(key)
            blocked.add(key)
            continue

        out.values[key] = coerced

        if not spec.in_range(coerced):
            unit = f" {spec.unit}" if spec.unit else ""
            out.issues.append(SettingIssue(
                key, "out_of_range",
                f"{key}={coerced}{unit} is outside the plausible range "
                f"[{spec.min}, {spec.max}] — confirm before use.", coerced))
            needs.add(key)
            blocked.add(key)

        # A zero is only suspect where the schema says so (see SettingSpec.zero_suspect).
        # It must NOT be a blanket rule over the replay levers: `max_smb_minutes: 0`,
        # `max_uam_minutes: 0` and `max_basal: 0` are deliberate "off" settings, and
        # withholding them makes build_profile fall back to 30 / 30 / 4x basal — simulating
        # insulin the real configuration forbids. Blocking must never be more permissive
        # than accepting.
        elif spec.zero_suspect and coerced == 0:
            unit = f" {spec.unit}" if spec.unit else ""
            out.issues.append(SettingIssue(
                key, "needs_confirm",
                f"{key}=0{unit} would disable this lever — confirm it was read correctly.",
                coerced))
            needs.add(key)
            blocked.add(key)

        conf = confidences.get(raw_name)
        if conf is not None and conf < LOW_CONFIDENCE:
            out.issues.append(SettingIssue(
                key, "needs_confirm",
                f"{key} was read with low confidence ({conf}); please confirm.", coerced))
            needs.add(key)
            blocked.add(key)

    out.needs_confirm = sorted(needs)
    out.blocked = sorted(blocked)
    return out
