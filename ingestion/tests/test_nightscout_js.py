"""web/nightscout.js, run under node with a stand-in for fetch."""
import json
import os
import shutil
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "web", "nightscout.js")

SCRIPT = r"""
const fs = require('fs');
const seen = [];
globalThis.fetch = async (u) => {
  u = new URL(u);
  seen.push(Object.fromEntries(u.searchParams));
  const p = u.pathname;
  const ev = u.searchParams.get('find[eventType]');
  let body = [];
  if (p.endsWith('treatments.json') && ev) body = [{ _id: 'prior-' + ev, eventType: ev, created_at: '2020-01-01T00:00:00Z' }];
  else if (p.endsWith('treatments.json')) body = [{ _id: 'w', eventType: 'Correction Bolus' }];
  return { status: 200, ok: true, json: async () => body };
};
const fetchNightscout = new Function(fs.readFileSync(process.argv[1], 'utf8') + '; return fetchNightscout;')();
fetchNightscout('https://ns.example', '', 1, () => {}).then((r) => {
  console.log(JSON.stringify({ treatments: r.treatments.map((t) => t._id), seen }));
});
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_fetch_adds_switches_and_temp_targets_from_before_the_window():
    out = json.loads(subprocess.run(["node", "-e", SCRIPT, SRC], capture_output=True, text=True,
                                    check=True).stdout)
    assert sorted(out["treatments"]) == ["prior-Profile Switch", "prior-Temporary Target", "w"]
    prior = [q for q in out["seen"] if "find[eventType]" in q]
    assert {q["find[eventType]"] for q in prior} == {"Profile Switch", "Temporary Target"}
    assert all("find[created_at][$lt]" in q for q in prior)


FAILING = SCRIPT.replace("if (p.endsWith('treatments.json') && ev) body =",
                         "if (p.endsWith('treatments.json') && ev) return { status: 500, ok: false, json: async () => ({}) }; if (0) body =")
FAILING = FAILING.replace("const fetchNightscout", "globalThis.setTimeout = (f) => { f(); return 0; };\nconst fetchNightscout")


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_a_failing_before_window_fetch_does_not_cost_the_pull():
    out = json.loads(subprocess.run(["node", "-e", FAILING, SRC], capture_output=True, text=True,
                                    check=True).stdout)
    assert out["treatments"] == ["w"]
