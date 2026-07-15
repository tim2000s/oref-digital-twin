"""Validate and coerce extracted settings against the schema.

Whatever the source (vision on a screenshot, or the client-side decrypt), the raw
key/values land here. This maps source names to friendly keys, coerces types, range-checks,
and flags anything that must be confirmed by the user before it is trusted — never a silent
accept of an out-of-range or low-confidence insulin-relevant value (DESIGN §5.2).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .schema import SETTINGS, resolve_alias

LOW_CONFIDENCE = 0.8


@dataclass
class SettingIssue:
    key: str                        # friendly key, or the raw name for unknown_key
    kind: str                       # unknown_key | wrong_type | out_of_range | needs_confirm
    message: str
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedSettings:
    values: dict[str, Any] = field(default_factory=dict)
    issues: list[SettingIssue] = field(default_factory=list)
    needs_confirm: list[str] = field(default_factory=list)

    def replay_settings(self) -> dict[str, Any]:
        """The subset the replay oracle can vary (replay_lever specs only)."""
        return {k: v for k, v in self.values.items() if SETTINGS[k].replay_lever}

    def is_clean(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "values": self.values,
            "needs_confirm": self.needs_confirm,
            "issues": [i.to_dict() for i in self.issues],
        }


def validate(raw: dict[str, Any], confidences: dict[str, float] | None = None) -> ValidatedSettings:
    confidences = confidences or {}
    out = ValidatedSettings()
    needs: set[str] = set()

    for raw_name, raw_val in raw.items():
        key = resolve_alias(raw_name)
        if key is None:
            out.issues.append(SettingIssue(raw_name, "unknown_key",
                                           f"'{raw_name}' is not a recognised setting.", raw_val))
            continue
        spec = SETTINGS[key]
        coerced, ok = spec.coerce(raw_val)
        if not ok:
            out.issues.append(SettingIssue(key, "wrong_type",
                                           f"'{raw_val}' is not a valid {spec.kind} for {key}.", raw_val))
            continue

        out.values[key] = coerced

        if not spec.in_range(coerced):
            unit = f" {spec.unit}" if spec.unit else ""
            out.issues.append(SettingIssue(
                key, "out_of_range",
                f"{key}={coerced}{unit} is outside the plausible range "
                f"[{spec.min}, {spec.max}] — confirm before use.", coerced))
            needs.add(key)

        conf = confidences.get(raw_name)
        if conf is not None and conf < LOW_CONFIDENCE:
            out.issues.append(SettingIssue(
                key, "needs_confirm",
                f"{key} was read with low confidence ({conf}); please confirm.", coerced))
            needs.add(key)

    out.needs_confirm = sorted(needs)
    return out
