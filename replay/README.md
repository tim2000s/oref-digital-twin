# replay

The oref `determine-basal` replay oracle. Runs the **real** oref0 controller (pinned in
`oracle/package.json`) over reconstructed inputs to price how a settings change flips a
decision. We do not reimplement determine-basal. See [../DESIGN.md](../DESIGN.md) §2.

The settings tests (`scenarios.py`, and `simulate` in `oracle/request.js`) go one step
further and estimate glucose under each setting with a stated model; see DESIGN §2.1 and the
section below. Everything else here is decision-level only.

## Pieces

| File | Role |
|---|---|
| `oracle/determine.js` | Node wrapper calling real `oref0/lib/determine-basal`. Reads `{requests:[...]}` on stdin, returns `{results:[...]}`. |
| `oracle_bridge.py` | Spawns the Node oracle (runner injectable for offline tests). |
| `settings_delta.py` | Applies a friendly settings change to a request's oref profile (max_iob, targets, ISF, SMB flags, SMB minutes…). Unknown keys raise. |
| `counterfactual.py` | (Library only since October 2026; the report no longer uses it.) Runs baseline vs altered through the oracle and diffs the enacted decision per cycle. |
| `scenarios.py` | Staged settings tests: basal, ISF, carb ratio, target, SMB limit, max IOB, each stepped ±30% through the closed-loop simulator and judged against time in range > 70% and time below range < 2%. |
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

## Settings tests: the simulator

`simulate` in `oracle/request.js` walks the cycles in time order under each scenario. At
each cycle it shifts the glucose determine-basal sees by the effect of every earlier
insulin difference (units × ISF × the fraction of that insulin's action completed, from
oref0's own `lib/iob/calculate`), adds those differences to the insulin-on-board projection,
runs determine-basal, and records the new difference. A scenario that changes nothing
reproduces the baseline exactly (tested).

Rebuilding insulin on board costs about 5.6 ms a cycle against 0.03 ms for determine-basal,
so it is done twice per cycle per report and reused: once on the logged history and once
with every bolus removed and every temp rate set to zero. A basal schedule scaled by k is
then X(1) + (k − 1) × X0. This is an approximation, because `lib/iob/history.js` turns each
temp into 0.05 U pulses and rounds the pulse count. On 300 cycles of one user, scaling basal
±30% moved insulin on board by a median of 0.54 to 0.58 U, and the linear form missed the
direct rebuild by a median of 0.04 to 0.08 U (95th percentile 0.16 U). `oracle/check_linearity.js`
reproduces the comparison on any requests file.

On one week of 1-minute AndroidAPS data (about 2,000 cycles at 5 minutes) the stages took
40 s in Node with the cache and 176 s without. In headless Chrome on an M-series Mac, timed
from inside the page, the main report was on screen 14 s after Analyse (Nightscout served
locally) and the six stages took a further 118 s; the browser runs them after the main
report is shown, with a status line saying so.

The glucose arithmetic assumes the profile ISF is real and that meals and the person's own
treatments are unchanged; see DESIGN §2.1.

## Tests

`pytest replay/tests` — unit tests use a fake oracle (no Node needed); the integration
tests run real oref0 and skip automatically if it is not installed.
