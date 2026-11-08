"""The bounded, typed settings schema.

Settings extraction (screenshots or client-side decrypt) fills a *fixed* set of typed
slots, each with a valid range and the source names it appears under in AAPS/Trio. This is
what makes screenshot extraction tractable and validatable (DESIGN §5.2): we are not
reading arbitrary text, we are filling ~two dozen known slots and rejecting anything that
does not fit.

`replay_lever=True` marks the settings passed to the replay: some can be varied there (the
`replay.settings_delta` keys), the rest set the baseline as configured. The others are
advisory-only inputs to diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    return str(v).strip().lower() in ("true", "1", "yes", "on", "enabled")


@dataclass(frozen=True)
class SettingSpec:
    key: str
    kind: str                       # "float" | "int" | "bool" | "choice"
    unit: str | None
    aliases: tuple[str, ...]        # source names (AAPS pref keys, screen labels, Trio names)
    replay_lever: bool
    description: str
    min: float | None = None
    max: float | None = None
    # Is a zero reading implausible for this setting? Only true where withholding the value
    # is SAFE — i.e. where the replay refuses to run rather than substituting a default.
    # For the caps (max_smb_minutes, max_uam_minutes, max_basal) zero is a real, deliberate
    # configuration meaning "off", and withholding it would make build_profile substitute a
    # *more permissive* default, simulating insulin the real configuration forbids.
    zero_suspect: bool = False
    choices: tuple[str, ...] = ()   # the values a "choice" setting may take

    def coerce(self, v: Any) -> tuple[Any, bool]:
        try:
            if self.kind == "bool":
                return _to_bool(v), True
            if self.kind == "choice":
                c = str(v).strip().lower()
                return (c, True) if c in self.choices else (None, False)
            if self.kind == "int":
                return int(round(float(v))), True
            return float(v), True
        except (TypeError, ValueError):
            return None, False

    def in_range(self, v: Any) -> bool:
        if self.kind in ("bool", "choice"):
            return True
        if self.min is not None and v < self.min:
            return False
        if self.max is not None and v > self.max:
            return False
        return True


SETTINGS: dict[str, SettingSpec] = {
    s.key: s for s in [
        # --- replay levers (map to replay.settings_delta) ---
        SettingSpec("max_iob", "float", "U",
                    # Not boost_max_iob: that is Boost's own cap on its tiers, default 1 U; Boost
                    # takes max IOB from openapsmb_max_iob like stock SMB.
                    # shortcut: the SMB key wins over the AMA one; an AMA-only user who never
                    # stored the SMB key is still read right, one with both is read as SMB.
                    ("max_iob", "Max IOB", "maxIOB", "openapsmb_max_iob", "openapsma_max_iob"),
                    True, "Maximum insulin on board the loop may reach.", 0, 70,
                    # Safe to withhold: from_cycle refuses the cycle when max_iob is absent,
                    # so a suspect zero skips the counterfactual instead of inventing one.
                    zero_suspect=True),
        SettingSpec("max_basal", "float", "U/h", ("max_basal", "Max basal", "maxBasal", "openapsma_max_basal"),
                    True, "Maximum temp basal rate.", 0, 25),
        SettingSpec("max_daily_safety_multiplier", "float", None,
                    ("max_daily_safety_multiplier", "openapsama_max_daily_safety_multiplier"),
                    True, "Temp basal ceiling as a multiple of the largest scheduled basal.", 1, 10),
        SettingSpec("current_basal_safety_multiplier", "float", None,
                    ("current_basal_safety_multiplier", "openapsama_current_basal_safety_multiplier"),
                    True, "Temp basal ceiling as a multiple of the current scheduled basal.", 1, 10),
        SettingSpec("target_bg", "float", "mg/dL", ("target_bg", "Target", "target"),
                    True, "Target glucose (single value).", 70, 180),
        SettingSpec("sens", "float", "mg/dL/U", ("sens", "ISF", "isf", "insulin_sensitivity"),
                    True, "Insulin sensitivity factor.", 5, 500),
        SettingSpec("carb_ratio", "float", "g/U", ("carb_ratio", "CR", "carbratio", "IC"),
                    True, "Carb ratio.", 2, 150),
        SettingSpec("max_smb_minutes", "int", "min",
                    ("maxSMBBasalMinutes", "Max SMB Basal Minutes", "max_smb_minutes", "smbmaxminutes"),
                    True, "SMB size cap as minutes of basal.", 0, 120),
        SettingSpec("max_uam_minutes", "int", "min",
                    ("maxUAMSMBBasalMinutes", "Max UAM SMB Basal Minutes", "max_uam_minutes", "uamsmbmaxminutes"),
                    True, "UAM SMB size cap as minutes of basal.", 0, 120),
        # The SMB switches mirror oref's own. enable_smb is AndroidAPS's master switch; a Trio
        # file has none, and replay.inputs.smb_enabled then reads SMB as on if any switch is.
        SettingSpec("enable_smb", "bool", None, ("use_smb", "enableSMB"),
                    True, "Whether SMBs are enabled at all.", None, None),
        SettingSpec("enable_smb_always", "bool", None, ("enableSMB_always", "Enable SMB Always"),
                    True, "SMBs whatever the carbs on board.", None, None),
        SettingSpec("enable_smb_with_cob", "bool", None, ("enableSMB_with_COB",),
                    True, "SMBs while carbs are on board.", None, None),
        SettingSpec("enable_smb_after_carbs", "bool", None, ("enableSMB_after_carbs",),
                    True, "SMBs for 6 h after carbs.", None, None),
        SettingSpec("enable_smb_with_temptarget", "bool", None, ("enableSMB_with_temptarget",),
                    True, "SMBs with a low temp target.", None, None),
        SettingSpec("allow_smb_with_high_temptarget", "bool", None,
                    ("allowSMB_with_high_temptarget", "enableSMB_with_high_temptarget"),
                    True, "SMBs allowed with a high temp target.", None, None),
        SettingSpec("enable_smb_high_bg", "bool", None, ("enableSMB_high_bg",),
                    True, "SMBs above a glucose level (Trio).", None, None),
        SettingSpec("enable_smb_high_bg_target", "float", "mg/dL", ("enableSMB_high_bg_target",),
                    True, "The glucose level for SMBs above it.", 70, 400),
        SettingSpec("enable_smb_uam", "bool", None,
                    ("enableUAM", "use_uam", "enableSMB_uam", "Enable UAM"),
                    True, "Whether unannounced-meal (UAM) predictions are on.", None, None),
        SettingSpec("insulin_curve", "choice", None, ("curve",),
                    True, "oref insulin curve.", None, None,
                    choices=("rapid-acting", "ultra-rapid", "bilinear")),
        SettingSpec("insulin_peak_min", "int", "min", (),
                    True, "Insulin peak time, when set by hand.", 35, 120),
        # --- advisory-only inputs (not replay levers) ---
        SettingSpec("smb_delivery_ratio", "float", None,
                    ("smb_delivery_ratio", "SMB delivery ratio"),
                    False, "Fraction of the calculated dose delivered as an SMB.", 0.1, 1.0),
        SettingSpec("max_cob", "int", "g", ("maxCOB", "Max COB"),
                    False, "Maximum carbs on board the loop will act on.", 0, 200),
        SettingSpec("autosens_min", "float", None, ("autosens_min", "Autosens min"),
                    False, "Lower bound on the autosens ratio.", 0.3, 1.0),
        SettingSpec("autosens_max", "float", None, ("autosens_max", "Autosens max"),
                    False, "Upper bound on the autosens ratio.", 1.0, 3.0),
        SettingSpec("dynamic_isf_enabled", "bool", None,
                    ("use_dynamic_sensitivity", "useNewFormula", "Dynamic ISF", "dynisf"),
                    False, "Whether dynamic ISF/CR is enabled (informs variant handling).",
                    None, None),
    ]
}

# alias (lowercased) -> friendly key, including each key as its own alias
_ALIAS_TO_KEY: dict[str, str] = {}
for _spec in SETTINGS.values():
    _ALIAS_TO_KEY[_spec.key.lower()] = _spec.key
    for _a in _spec.aliases:
        _ALIAS_TO_KEY[_a.lower()] = _spec.key


def alias_rank(raw_name: str) -> int:
    """Where a source name stands in its setting's alias list; lower wins when a file has several."""
    key = resolve_alias(raw_name)
    names = [key] + [a.lower() for a in SETTINGS[key].aliases] if key else []
    return names.index(str(raw_name).strip().lower()) if key else 0


def resolve_alias(raw_name: str) -> str | None:
    """Map a source name/label to a friendly key, or None if unrecognised."""
    return _ALIAS_TO_KEY.get(str(raw_name).strip().lower())
