"""Score generated summaries with the grounding gate.

    PYTHONPATH=. python3 validation/narrator/gate.py validation/narrator/<file>.json
"""
import json
import sys

from report.grounding import check_narrative

d = json.load(open(sys.argv[1]))
passed = 0
for t in d["texts"]:
    r = check_narrative(t, d["source"])
    passed += r.passed
    print(r.passed, [v.kind for v in r.violations])
print(f"{passed} of {len(d['texts'])} passed")
