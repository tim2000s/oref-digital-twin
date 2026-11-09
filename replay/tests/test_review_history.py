"""The settings' history the TimSim round trip gives each review (validation/GUARD_PLAN.md)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "validation"))
from timsim_roundtrip import review_history  # noqa: E402


def _out(tir, tbr):
    return {"cgm": {"tir": tir, "tbr70": tbr}}


def test_first_review_gets_only_the_reference():
    one = {"basal_scale": 1.0, "isf_scale": 1.0, "cr_scale": 1.0, "target_offset": 0}
    assert review_history(one, [], _out(60, 1)) == {
        "cumulative": {"basal": 1.0, "isf": 1.0, "cr": 1.0, "target": 0}}


def test_later_reviews_get_the_accumulated_change_the_last_one_and_both_fortnights():
    r1 = {"basal_scale": 1.0, "isf_scale": 0.9, "cr_scale": 0.8, "target_offset": -9}
    r2 = {"basal_scale": 1.1, "isf_scale": 1.0, "cr_scale": 0.9, "target_offset": 0}
    so_far = {"basal_scale": 1.1, "isf_scale": 0.9, "cr_scale": 0.72, "target_offset": -9}
    reviews = [{"chosen": r1, "learn": _out(60, 1)}, {"chosen": r2, "learn": _out(65, 2)}]
    h = review_history(so_far, reviews, _out(66, 3))
    assert h["cumulative"] == {"basal": 1.1, "isf": 0.9, "cr": 0.72, "target": -9}
    assert h["last"] == {"basal": 1.1, "isf": 1.0, "cr": 0.9, "target": 0}      # review 2, not 1
    assert h["before"] == {"tir": 65, "tbr": 2} and h["after"] == {"tir": 66, "tbr": 3}
