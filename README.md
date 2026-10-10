# oref-digital-twin

Advisory decision support for AndroidAPS and Trio dosing settings. It runs in the browser:

https://tim2000s.github.io/oref-digital-twin/

> Read-only and advisory only. Nothing here writes to Nightscout, a pump or a loop, and it
> is not medical advice. Any settings change it suggests is a trial to discuss with your
> clinician and test deliberately, one setting at a time.

## Using it

Open the page and enter your Nightscout address (it must start with `https://`) and a
read-only token, which is one with the `readable` role made in Nightscout's Admin Tools.
Choose how many days to analyse; the default is 7. Your Nightscout must have `cors` in its
`ENABLE` setting, because the page fetches from it directly.

Two optional inputs make the settings tests more faithful. Max IOB can be typed in, and a
settings file can be loaded: an AndroidAPS preferences export, decrypted in the page with
your master password, or a Trio settings JSON. Without them the page reads max IOB from the
loop's own reason text and assumes 30 minutes for the SMB limit.

Pick which country's driving rules the report quotes: the UK (DVLA), the EU (Directive
2006/126/EC), the US (the American Diabetes Association's position; rules vary by state) or none.
The report quotes them word for word with their source and date, beside the international and,
for the UK, NICE glucose targets, and adds the guidance on hypoglycaemia when it finds lows. How
the quotes are kept honest is in `guidance/README.md`.

Your token and data stay in the browser. If you tick the written-summary box, only the
anonymous findings (percentages and finding names, no readings, token or address) go to a
narration service, and its text is checked against those findings before it is shown.

The main report appears once the data has arrived, which on a slow Nightscout can take a
couple of minutes for a week. The settings tests then run for about two more minutes, with
a status line saying so. Keep the page open meanwhile; on a phone, switching away can stop it.

## What it does

A worked case shows it best. Take one week from an AndroidAPS user whose loop decided every
minute. The page fetches the week and first reports what happened: about 87% of readings in
range (70 to 180 mg/dL), 6.5% below 70, nine low episodes, five of them overnight.

It then asks what a lower basal would have done. It takes one loop decision every five
minutes, about 2,000 across the week, and re-runs each through the real oref0 dosing code
with every basal rate 30% lower. At each of those moments the loop may now give a different
amount of insulin. Glucose from then on is moved by that difference times the profile ISF,
spread over the time the insulin takes to act, and the loop sees the moved glucose at its
next decision, so it responds as it would have done. For this person the lower basal left
daily insulin almost unchanged, because the loop made up the difference with temp basals
and SMBs. What changed was where glucose settled: about 15 mg/dL (0.8 mmol/L) higher on
average, which took the estimated time below 70 from 6.5% to 1.7% while time in range
stayed at 87%.

That is one step of six. The settings are tested in the order a manual basal test, ISF
test and carb-ratio test would follow, each on the part of the day it governs, and each
keeping the values chosen before it:

| Order | Setting | Stepped across | Judged on |
|---|---|---|---|
| 1 | Basal rates | −30% to +30% | Fasting stretches: no carbs or meal-sized rise in 4 h, nothing above 180 mg/dL in 3 h |
| 2 | ISF | −30% to +30% | The whole period, once there are at least 6 h of correction stretches (above 180 mg/dL in the last 3 h, outside meals) |
| 3 | Carb ratio | −30% to +30%, with logged meal boluses scaled to match | The 4 h after logged carbs or a meal-sized rise |
| 4 | Target | −1 to +1 mmol/L in 0.5 steps | The whole period |
| 5 | SMB limit (maximum SMB basal minutes) | 15 to 90 minutes | The whole period |
| 6 | Max IOB | −30% to +30% | The whole period |

The page offers two aims: time in range above 70% and time below range under 2% (standard), or
time in range above 80% with the same limit on lows (tighter). At each stage the page
picks the smallest change that meets both. When no value does, it keeps time below range
under 2% with the most time in range, and failing that it picks the value with the least
time below range, because a low is the more immediate harm. A value that gives more insulin than the current
setting is only considered when the whole period's estimate keeps time below 70 under 2% and
time below 54 under 0.6%. A stage is reported but not
judged when its stretches add up to less than 6 hours, which is common for ISF in someone
who rarely runs high, and the carb-ratio stage is skipped when no carbs were logged.

Each stage ends with a table of every value tried and either "no change suggested" or a
trial to consider, and the last section shows the chosen values together.

Before the settings tests, the report also covers glucose summary figures, findings such as
overnight lows and SMBs given at high insulin on board, how far the loop's 30-minute
predictions ran from what followed, and which algorithm variant appears to be running.

## What the estimates assume

The glucose figures in the settings tests are estimates from a deliberately simple model,
and the page labels them that way. The model takes your profile ISF as your real
sensitivity, and assumes your meals, activity and own treatments, hypo treatments included,
would have been the same under the new setting. It has not yet been checked against periods
where someone actually changed a setting, so it is better at ranking settings than at
predicting what a change will do. The tests run stock oref0; if the page detects a variant
such as Boost or AutoISF, it says that what the variant adds is not modelled.

DESIGN.md §2.1 sets out the model, and `replay/README.md` covers the simulator, its checks
and its timings.

## Layout

| Path | Purpose |
|---|---|
| `DESIGN.md` | Architecture and rationale. Start here. |
| `ingestion/` | Nightscout pulls (`devicestatus`, `entries`, `treatments`, `profile`) to a common schema. |
| `variant/` | Algorithm-variant detection (AAPS stock, DynISF, AutoISF, Trio, middleware). |
| `diagnostics/` | Deterministic sanity checks and out-of-sample pattern detection. |
| `replay/` | The oref0 `determine-basal` oracle, the closed-loop simulator and the staged settings tests. |
| `settings/` | Settings ingestion, including client-side decryption of AAPS preference exports. |
| `report/` | The report: Pyodide entry point, Markdown template, quoted official guidance and the grounding check on narration. |
| `guidance/` | Fetching and checking the official sources the report quotes. |
| `web/` | The browser page (GitHub Pages, Pyodide and an oref0 bundle). |
| `worker/` | The optional narration service (Cloudflare Worker). |
| `docs/` | Supporting notes and references. |

## Privacy

Public repository. No names, tokens, site URLs or locations in code, docs, fixtures or
commit messages. Test data is synthetic or anonymised. Nightscout tokens are read-only,
scoped, never stored and revocable.

## Licence

Intended: AGPL-3.0, to stay consistent with the AAPS and oref ecosystem this builds on and
replays. See `LICENSE`; confirm before the first substantive release.
