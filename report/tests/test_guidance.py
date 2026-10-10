"""The quoted guidance: every passage traceable, and shown only where it applies."""
import json
import os
import re
import sys

import pytest

from report.guidance import HERE, render, select

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SNAPSHOTS = os.path.join(ROOT, "guidance", "sources")
sources = {s["id"]: s for s in json.load(open(os.path.join(HERE, "sources.json")))}
refs = json.load(open(os.path.join(HERE, "references.json")))
norm = lambda s: re.sub(r"\s+", " ", s).strip()


def test_every_reference_names_a_source_a_date_and_a_quote():
    assert len({r["id"] for r in refs}) == len(refs)
    for r in refs:
        assert r["source"] in sources, r["id"]
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["retrieved"]), r["id"]
        assert len(r["quote"]) > 20 and r["topics"], r["id"]
        assert sources[r["source"]]["url"].startswith("https://"), r["source"]


@pytest.mark.parametrize("ref", refs, ids=[r["id"] for r in refs])
def test_quote_appears_word_for_word_in_its_source(ref):
    """Skipped where the snapshot has not been fetched (it is not committed: several sources
    are copyright). Run guidance/fetch_sources.py to fetch them. A changed source fails here
    rather than quietly leaving a quote that no longer stands."""
    path = os.path.join(SNAPSHOTS, ref["source"] + ".txt")
    if not os.path.exists(path):
        pytest.skip("snapshot not fetched")
    sys.path.insert(0, os.path.join(ROOT, "guidance"))
    from fetch_sources import digest, snapshot_text
    body = snapshot_text(path)
    assert norm(ref["quote"]) in norm(body), "quote not found in its source"
    assert digest(body) == ref["source_sha256"], (
        "the source has changed since this quote was taken; re-read it and update the entry")


def test_driving_rules_follow_the_chosen_country():
    uk = select([], "UK")["driving"]
    eu = select([], "EU")["driving"]
    assert uk and all(i["jurisdiction"].startswith("UK") for i in uk)
    assert eu and all(i["jurisdiction"] == "EU" for i in eu)
    assert select([], None)["driving"] == []


def test_the_hypoglycaemia_heading_only_appears_with_lows():
    calm = select([{"key": "meets_consensus"}], "UK")
    lows = select([{"key": "nocturnal_hypos"}], "UK")
    assert calm["hypoglycaemia"] == [] and lows["hypoglycaemia"]
    # the licensing rules on severe hypoglycaemia are driving rules and show either way
    assert any(i["id"] == "dvla-severe-definition" for i in calm["driving"])


def test_report_section_quotes_and_cites():
    md = "\n".join(render([{"key": "tbr_lt70_over_limit"}], "UK"))
    assert md.startswith("## Official guidance")
    assert "“Don’t drive if your glucose (sugar) level is 4.0mmol/L or below." in md
    assert "retrieved 20" in md and "https://" in md
