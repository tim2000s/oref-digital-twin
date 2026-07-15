"""The grounding gate: verify LLM narration against the source findings.

Deterministic, dependency-free, and runs client-side (Pyodide) — no second LLM. This is
the control that lets us fire findings at an LLM for a nicer report without trusting it:
the narration is only shown if it passes, otherwise the caller falls back to the
deterministic template.

Checks (all blocking):
  * ungrounded_number   — a figure in the narrative that is not present in the source.
  * prescription        — an imperative dosing instruction (the tool is advisory-only).
  * omitted_critical    — a CRITICAL finding missing from the narrative.
  * missing_caveat      — counterfactuals mentioned without the "decision-level, not BG" caveat.
  * missing_assoc_caveat— the SMB/low pattern narrated without its association-not-causation caveat.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

# small integers that appear as ordinary prose ("within 2 hours") and need no grounding
_STRUCTURAL = {0.0, 1.0, 2.0, 3.0, 24.0}
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

# Imperative dosing directives — advisory-only tool must not emit these. Targeted at
# second-person advice and clause-initial imperatives, NOT descriptive counterfactuals
# ("lowering max IOB to 3 changed the decision" is a description, not a prescription).
_DOSE_NOUNS = r"(?:basal|isf|sensitivity|carb\s*ratio|\bcr\b|target|max[\s_]?iob|smb|dose|insulin|correction)"
_IMPERATIVE_VERB = r"(?:set|increase|decrease|raise|lower|reduce|adjust|change|bump|drop)"
_PRESCRIPTION_RES = [
    # second person: "you should/could/need to ... <dose noun>"
    re.compile(rf"\byou\s+(?:should|could|ought to|need to|must|may want to|might want to)\b[^.]*\b{_DOSE_NOUNS}\b",
               re.IGNORECASE),
    # clause-initial imperative verb + (your) <dose noun>: "Set max IOB to 8", "Lower your ISF"
    re.compile(rf"(?:^|[.;:]\s+){_IMPERATIVE_VERB}\s+(?:your\s+)?{_DOSE_NOUNS}\b", re.IGNORECASE),
    # possessive directive with a value: "your max IOB to 8"
    re.compile(rf"\byour\s+{_DOSE_NOUNS}\b[^.]*\bto\s+-?\d", re.IGNORECASE),
]

_CAVEAT_MARKERS = ("decision-level", "not the resulting", "not predict", "cannot predict",
                   "not a blood glucose", "not blood glucose", "resulting blood glucose")
_ASSOC_MARKERS = ("association", "not prove", "does not prove", "not causation", "not caused",
                  "correlation")


@dataclass
class Violation:
    kind: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GateResult:
    passed: bool
    violations: list[Violation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "violations": [v.to_dict() for v in self.violations]}


def _source_numbers(source: dict) -> set[float]:
    """Every number appearing anywhere in the source (numeric leaves AND inside strings)."""
    nums: set[float] = set()
    for tok in _NUM_RE.findall(json.dumps(source)):
        try:
            nums.add(float(tok))
        except ValueError:
            pass
    return nums


def _is_grounded(n: float, allowed: set[float]) -> bool:
    if n in _STRUCTURAL:
        return True
    for a in allowed:
        if abs(a - n) <= max(0.05, 0.01 * abs(a)):
            return True
        if round(a, 1) == round(n, 1) or round(a) == round(n):
            return True
    return False


def _critical_keywords(finding: dict) -> list[str]:
    """Distinctive lowercase tokens from a critical finding's title, for omission checks."""
    title = (finding.get("title") or "").lower()
    words = re.findall(r"[a-z]{5,}", title)
    stop = {"above", "below", "limit", "range", "target", "value"}
    return [w for w in words if w not in stop] or words


def check_narrative(narrative: str, source: dict) -> GateResult:
    """Verify `narrative` is grounded in `source`. Returns a GateResult; passed=no violations."""
    violations: list[Violation] = []
    text = narrative or ""
    low = text.lower()

    # 1. numbers
    allowed = _source_numbers(source)
    for tok in _NUM_RE.findall(text):
        try:
            n = float(tok)
        except ValueError:
            continue
        if not _is_grounded(n, allowed):
            violations.append(Violation("ungrounded_number", f"'{tok}' is not present in the findings."))

    # 2. prescriptions
    for rx in _PRESCRIPTION_RES:
        m = rx.search(text)
        if m:
            violations.append(Violation("prescription", f"dosing directive: '{m.group(0).strip()[:80]}'"))
            break

    findings = source.get("findings", []) if isinstance(source, dict) else []

    # 3. omitted critical findings
    for f in findings:
        if f.get("severity") == "critical":
            kws = _critical_keywords(f)
            if kws and not any(k in low for k in kws):
                violations.append(Violation("omitted_critical",
                                            f"critical finding not mentioned: '{f.get('title')}'"))

    # 4. counterfactual caveat
    if source.get("counterfactuals"):
        if not any(m in low for m in _CAVEAT_MARKERS):
            violations.append(Violation("missing_caveat",
                                        "counterfactual narrated without the decision-level/BG caveat."))

    # 5. association caveat for the SMB/low pattern
    if any(f.get("key") == "smb_high_iob_overnight" for f in findings):
        if "smb" in low and not any(m in low for m in _ASSOC_MARKERS):
            violations.append(Violation("missing_assoc_caveat",
                                        "SMB/low pattern narrated without association-not-causation caveat."))

    return GateResult(passed=not violations, violations=violations)
