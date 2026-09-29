# replay

The oref `determine-basal` replay oracle. Runs the **real** oref0 controller (pinned in
`oracle/package.json`) over reconstructed inputs to price how a settings change flips a
decision. Decision-level counterfactual only — never a BG counterfactual. We do not
reimplement determine-basal. See [../DESIGN.md](../DESIGN.md) §2.

## Pieces

| File | Role |
|---|---|
| `oracle/determine.js` | Node wrapper calling real `oref0/lib/determine-basal`. Reads `{requests:[...]}` on stdin, returns `{results:[...]}`. |
| `oracle_bridge.py` | Spawns the Node oracle (runner injectable for offline tests). |
| `settings_delta.py` | Applies a friendly settings change to a request's oref profile (max_iob, targets, ISF, SMB flags, SMB minutes…). Unknown keys raise. |
| `counterfactual.py` | Runs baseline vs altered through the oracle and diffs the enacted decision per cycle. |
| `inputs.py` | Reconstructs a determine-basal request from a devicestatus cycle + Nightscout profile + settings, with explicit fidelity flags. |

## Setup

```bash
cd replay/oracle && npm install     # installs pinned oref0 (node_modules is gitignored)
```

## Usage

```python
from replay import OrefOracle, from_cycle, run_counterfactual

req, warnings = from_cycle(cycle, profile_snapshot, entries, settings={"max_iob": 6.0, "enable_smb": True})
cf = run_counterfactual(OrefOracle(), [req], {"max_iob": 3.0})
print(cf.n_changed, cf.mean_delta_u, cf.caveat)
```

## Fidelity (read this)

Insulin on board is rebuilt for each cycle by oref0's own `lib/iob` from the Nightscout
boluses, SMBs and temp basals, inside the oracle (`oracle/request.js`), and determine-basal
receives the 48-step projection that library produces. Before 30 September 2026 the replay
passed the single IOB object logged in devicestatus. determine-basal walks the projection to
build its predicted-glucose curves; given one object it threw inside a try block, left
minPredBG and minGuardBG at 999 and switched off its low-glucose guard. Across 225 scenarios
checked, that changed the decision in 28, and gave more insulin in every one of them. A cycle
with no treatments to rebuild from is now refused, and the oracle refuses a request that
carries only a single `iob_data` object.

Each result reports oref's rebuilt IOB (`iob_rebuilt`) beside the logged figure, and the report
states how often the two agree within 0.5 U. A wide gap means treatments are missing from
Nightscout, and the replayed decisions then rest on too little insulin.

The insulin curve matters as much as the history. When the settings do not name it, the report
tries the three curves AndroidAPS and Trio ship (rapid-acting peak 75 min, ultra-rapid 55, the
Lyumjev preset at 45) on a sample of cycles and keeps the one whose rebuilt IOB is closest to
the logged figure. On two days of one AndroidAPS user on Lyumjev the median gap was 0.71 U,
0.40 U and 0.26 U respectively on that sample; over all 400 replayed cycles on the chosen curve
it was 0.14 U, with 88% of cycles within 0.5 U (correlation 0.984).

Still approximated: the temp basal running at decision time (`currenttemp`, assumed none).
`lib/iob` splits temp basals on the basal schedule by local clock hour: the Node oracle sets the
profile's time zone, and the browser runs in the viewer's own.

## Tests

`pytest replay/tests` — unit tests use a fake oracle (no Node needed); the integration
tests run real oref0 and skip automatically if it is not installed.
