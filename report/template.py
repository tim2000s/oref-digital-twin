"""Deterministic template report.

Generated purely from the structured findings — no LLM, no network. This is the report
the user always gets: it is the safety net behind the optional LLM narration, and it runs
client-side in Pyodide. Markdown out.

Inputs are plain dicts (the `.to_dict()` outputs), because that is what crosses the
JS/Python (Pyodide) boundary.
"""

from __future__ import annotations

from typing import Any

DISCLAIMER = (
    "_This is decision-support, not medical advice, and it is advisory-only — it never "
    "changes your loop or pump. Discuss any change with your clinician and trial it "
    "deliberately._"
)


def _fmt(v: Any, suffix: str = "") -> str:
    return "—" if v is None else f"{v}{suffix}"


def _glycemia_block(g: dict) -> list[str]:
    if not g or g.get("n_readings", 0) == 0:
        return ["## Glucose", "", "No CGM data in this window."]
    return [
        "## Glucose",
        "",
        f"- Readings: {g['n_readings']} over ~{_fmt(g.get('days'))} days",
        f"- Mean: {_fmt(g.get('mean_mgdl'))} mg/dL ({_fmt(g.get('mean_mmol'))} mmol/L), "
        f"GMI {_fmt(g.get('gmi_pct'), '%')}",
        f"- Time in range (70–180): {_fmt(g.get('tir_70_180'), '%')}",
        f"- Time below 70: {_fmt(g.get('tbr_lt70'), '%')}; below 54: {_fmt(g.get('tbr_lt54'), '%')}",
        f"- Time above 180: {_fmt(g.get('tar_gt180'), '%')}; above 250: {_fmt(g.get('tar_gt250'), '%')}",
        f"- Variability (CV): {_fmt(g.get('cv_pct'), '%')}",
    ]


_SEV_HEADING = {"critical": "### Critical", "warning": "### Worth attention", "info": "### Notes"}


def _findings_block(findings: list[dict]) -> list[str]:
    if not findings:
        return ["## Findings", "", "No findings."]
    lines = ["## Findings", ""]
    for sev in ("critical", "warning", "info"):
        group = [f for f in findings if f.get("severity") == sev]
        if not group:
            continue
        lines.append(_SEV_HEADING[sev])
        lines.append("")
        for f in group:
            lines.append(f"- **{f.get('title')}** — {f.get('detail')}")
        lines.append("")
    return lines


def _variant_block(variant: dict | None) -> list[str]:
    if not variant:
        return []
    advis = variant.get("advisability")
    note = {
        "full": "A modelled controller: the settings tests replay it directly.",
        "diagnosis_only": "Middleware or a fork is in play: the settings tests run stock oref0 "
                          "and do not model what it adds.",
        "out_of_scope": "The controller could not be classified — findings only.",
    }.get(advis, "")
    lines = [
        "## Your setup",
        "",
        f"- Detected: **{variant.get('variant')}** (confidence {_fmt(variant.get('confidence'))})",
        f"- {note}",
    ]
    for n in variant.get("notes", []):
        lines.append(f"- {n}")
    return lines


def render_report(diagnostics: dict, variant: dict | None = None,
                  jurisdiction: str | None = "UK") -> str:
    """Render a full deterministic Markdown report from structured findings."""
    counts = diagnostics.get("counts", {})
    parts: list[str] = [
        "# oref digital twin — report",
        "",
        f"Findings: {counts.get('critical', 0)} critical, {counts.get('warning', 0)} to watch, "
        f"{counts.get('info', 0)} notes.",
        "",
    ]
    parts += _variant_block(variant)
    parts.append("")
    parts += _glycemia_block(diagnostics.get("glycemia", {}))
    parts.append("")
    parts += _findings_block(diagnostics.get("findings", []))
    from .guidance import render as render_guidance

    guidance = render_guidance(diagnostics.get("findings", []), jurisdiction)
    if guidance:
        parts += [""] + guidance
    parts += ["", "---", "", DISCLAIMER]
    return "\n".join(parts)


def _signed_mgdl(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{v:+.0f} mg/dL ({v / 18.0:+.1f} mmol/L)"


_SEGMENT_TEXT = {
    "fasting": "fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above "
               "180 mg/dL in the last 3 h)",
    "correction": "correction stretches (above 180 mg/dL in the last 3 h, outside meals)",
    "meal": "meal stretches (the 4 h after logged carbs or a meal-sized rise)",
    "all": "the whole period",
}


def render_settings_tests(result: dict | None, note: str | None = None) -> str:
    """The staged basal, ISF, carb-ratio, target and SMB tests (replay.scenarios)."""
    lines = ["## Settings tests (estimated)", ""]
    if result is None:
        lines.append(f"_{note}_")
        return "\n".join(lines)
    goals = result["goals"]
    obs = result["observed"]["all"]
    lines += [
        f"Aim ({result.get('aim', 'standard')}): time in range above {goals['tir_gt_pct']:.0f}% "
        f"and time below range under {goals['tbr_lt_pct']:.0f}%. Observed over {result['days']} days: "
        f"{_fmt(obs['tir'], '%')} in range, {_fmt(obs['tbr'], '%')} below, "
        f"{obs['lows']} low episodes.",
        "",
        "Each setting is stepped from −30% to +30% and the loop is re-run through every "
        f"5-minute cycle ({result['cycles']}) under each value. Basal is tested first, on "
        "fasting stretches; ISF next, on the whole period once there are enough correction "
        "stretches to judge it; then carb ratio on meals; then target, the SMB limit and max IOB "
        "over the whole period. Each stage keeps the choices before it.",
        "",
        f"_{result['caveat']}_",
        "",
        f"A value that gives more insulin than your current setting is only considered when the "
        f"estimate for the whole period keeps time below 70 under "
        f"{goals.get('strengthen_tbr70_lt_pct', 2):g}% and time below 54 under "
        f"{goals.get('strengthen_tbr54_lt_pct', 0.6):g}%; rows that fail it are marked.",
    ]
    if result.get("variant_note"):
        lines += ["", f"_{result['variant_note']}_"]
    curve = result.get("insulin_curve") or {}
    fit = curve.get("insulin_curve_fit_u") or {}
    if curve.get("insulin_curve"):
        gap = fit.get(curve["insulin_curve"])
        lines += ["", f"Insulin curve: {curve['insulin_curve']} ({curve.get('insulin_curve_source')}"
                  + (f"; insulin on board rebuilt from your treatments sits a median {gap} U from "
                     "what your loop logged" if gap is not None else "") + ")."]
    applied: list[str] = []
    for i, st in enumerate(result["stages"], 1):
        lines += ["", f"### {i}. {st['name']}", ""]
        where = _SEGMENT_TEXT.get(st["measured_on"], st["measured_on"])
        if not st.get("rows"):
            lines.append(f"Not run: {st['why']}.")
            continue
        seg = st["observed"]
        lines.append(f"Judged on {where}: {st['segment_hours']} h of readings, observed "
                     f"{_fmt(seg['tir'], '%')} in range and {_fmt(seg['tbr'], '%')} below.")
        if st.get("enough_on"):
            lines.append(f"Judged only with at least 6 h of "
                         f"{_SEGMENT_TEXT.get(st['enough_on'], st['enough_on'])}: there were "
                         f"{st['enough_hours']} h.")
        if applied:
            lines.append(f"Run with {', '.join(applied)}.")
        if st.get("note"):
            lines.append(st["note"])
        whole = st["measured_on"] == "all"
        scope = "" if whole else f" ({st['measured_on']})"
        lever = st["lever"][0].upper() + st["lever"][1:]
        head = (f"| {lever} | Average glucose change | In range{scope} | Below range{scope} "
                "| Low episodes |")
        rule = "|---|---|---|---|---|"
        if not whole:
            head += " In range (all) | Below range (all) |"
            rule += "---|---|"
        head += " Below 54 (all) |"
        rule += "---|"
        lines += ["", head, rule]
        for r in st["rows"]:
            mark = " ←" if r["value"] == st["chosen"] else ""
            if r.get("excluded"):
                mark += " (excluded: more insulin with too many lows)"
            row = (f"| {r['label']}{mark} | {_signed_mgdl(r['mean_shift'])} "
                   f"| {_fmt(r['est']['tir'], '%')} | {_fmt(r['est']['tbr'], '%')} "
                   f"| {r['est']['lows']} |")
            if not whole:
                row += f" {_fmt(r['est_all']['tir'], '%')} | {_fmt(r['est_all']['tbr'], '%')} |"
            row += f" {_fmt(r['est_all'].get('tbr54'), '%')} |"
            lines.append(row)
        if st["chosen"] == st.get("neutral"):
            lines += ["", f"No change suggested: {st['why']}."]
        else:
            lines += ["", f"Trial to consider: {st['lever']} {st['chosen_label']}, because "
                          f"{st['why']}."]
            applied.append(f"{st['lever']} {st['chosen_label']}")
    fin = result["final"]["est_all"]
    meets = (fin["tir"] is not None and fin["tir"] > goals["tir_gt_pct"]
             and fin["tbr"] < goals["tbr_lt_pct"])
    lines += [
        "",
        "### Together",
        "",
        (f"With {', '.join(applied)}: " if applied else "With no change: ")
        + f"estimated {_fmt(fin['tir'], '%')} in range and {_fmt(fin['tbr'], '%')} below "
        f"(observed {_fmt(obs['tir'], '%')} and {_fmt(obs['tbr'], '%')}), average glucose "
        f"{_signed_mgdl(result['final']['mean_shift'])}. "
        + ("That meets both goals." if meets else "That does not meet both goals."),
        "",
        "Change one setting at a time and give each a few days before the next, so its effect "
        "can be seen on its own.",
    ]
    return "\n".join(lines)
