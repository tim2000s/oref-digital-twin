"""Official guidance, quoted, shown in the report beside the findings it bears on.

`report/guidance/references.json` holds each passage word for word with its source, jurisdiction
and the date it was retrieved; `report/guidance/sources.json` names the sources. Nothing here paraphrases:
a driving rule restated from memory is exactly the error this must not make, so every quote is
checked against a snapshot of its source by `report/tests/test_guidance.py`, and
`guidance/fetch_sources.py` at the repository root refetches the snapshots.

Which passages appear: every driving rule for the jurisdiction the person chose, always, since a
loop user is on insulin and the licensing rules on severe hypoglycaemia apply whether or not this
fortnight had lows; the clinical passages on hypoglycaemia under their own heading only when the
findings show lows; and the glucose targets, always, with NICE's only for the UK.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guidance")

JURISDICTIONS = {"UK": "UK", "EU": "EU", "US": "US", "none": None}

# Findings that make the passages on hypoglycaemia relevant.
LOW_FINDINGS = {"tbr_lt70_over_limit", "tbr_lt54_over_limit", "nocturnal_hypos"}


@lru_cache(maxsize=1)
def _load() -> tuple[dict[str, dict], list[dict]]:
    with open(os.path.join(HERE, "sources.json"), encoding="utf-8") as fh:
        sources = {s["id"]: s for s in json.load(fh)}
    with open(os.path.join(HERE, "references.json"), encoding="utf-8") as fh:
        refs = json.load(fh)
    return sources, refs


def _matches(ref: dict, jurisdiction: str | None) -> bool:
    j = ref["jurisdiction"]
    if j == "International":
        return True
    if jurisdiction is None:
        return False
    return j == jurisdiction or j.startswith(jurisdiction + " ")


def select(findings: list[dict], jurisdiction: str | None) -> dict[str, list[dict]]:
    """The passages to show, grouped as driving, hypoglycaemia and targets."""
    sources, refs = _load()
    lows = any(f.get("key") in LOW_FINDINGS for f in findings)
    keep: dict[str, list[dict]] = {"driving": [], "hypoglycaemia": [], "targets": []}
    for r in refs:
        if not _matches(r, jurisdiction):
            continue
        item = {**r, "source_info": sources[r["source"]]}
        if "driving" in r["topics"]:
            # licensing rules apply to anyone driving on insulin, lows found or not
            keep["driving"].append(item)
        elif "hypoglycaemia" in r["topics"] and lows:
            keep["hypoglycaemia"].append(item)
        elif "targets" in r["topics"]:
            keep["targets"].append(item)
    return keep


def _cite(source: dict, retrieved: str) -> str:
    return f"{source['body']}: {source['title']}. {source['url']} (retrieved {retrieved})"


def render(findings: list[dict], jurisdiction: str | None) -> list[str]:
    """Markdown lines for the report's official guidance section, quotes grouped by source."""
    chosen = select(findings, jurisdiction)
    if not any(chosen.values()):
        return []
    lines = ["## Official guidance", "",
             "_Quoted word for word from the bodies named, with the date each was retrieved. "
             "Guidance changes; check the source before relying on it._"]
    heads = {"driving": f"Driving ({jurisdiction})", "hypoglycaemia": "Hypoglycaemia",
             "targets": "Glucose targets"}
    if jurisdiction is None:
        lines += ["", "No driving rules shown: no country was chosen."]
    for group in ("driving", "hypoglycaemia", "targets"):
        if not chosen[group]:
            continue
        lines += ["", f"### {heads[group]}"]
        by_source: dict[str, list[dict]] = {}
        for item in chosen[group]:
            by_source.setdefault(item["source"], []).append(item)
        for items in by_source.values():
            lines += ["", _cite(items[0]["source_info"], items[0]["retrieved"]), ""]
            lines += [f"- “{i['quote']}”" for i in items]
    if jurisdiction == "UK" and chosen["driving"]:
        lines += ["", "The DVLA passages above apply to car and motorcycle (Group 1) licences "
                      "unless they name Group 2; for bus and lorry licences see the DVLA guidance "
                      "for medical professionals cited above."]
    return lines


__all__ = ["JURISDICTIONS", "LOW_FINDINGS", "select", "render"]
