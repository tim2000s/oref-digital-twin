# oref-digital-twin

Advisory decision support for AndroidAPS and Trio dosing settings. It is a single web page that
runs entirely in your browser, and you host your own copy on GitHub Pages under your own
GitHub account, at no cost and with no server.

> Read-only and advisory only. Nothing here writes to Nightscout, a pump or a loop, and it
> is not medical advice. Any settings change it suggests is a trial to discuss with your
> clinician and test deliberately, one setting at a time.

## Setting up your own copy

It takes about ten minutes and needs a free GitHub account.

1. Sign in to GitHub, open this repository and choose Fork (top right). Keep the name
   `oref-digital-twin` and create the fork. Your copy holds no one's data, so a public fork is
   safe.
2. In your fork, open the Actions tab and choose "I understand my workflows, go ahead and
   enable them". GitHub turns workflows off in every new fork until you do.
3. Open Settings, then Pages. Under Build and deployment, set Source to GitHub Actions.
4. Back in the Actions tab, choose "Deploy web to GitHub Pages" on the left, then Run workflow
   on the `main` branch. It takes about a minute.

Your copy is then at

    https://{your-github-id}.github.io/oref-digital-twin/

where `{your-github-id}` is your GitHub username in lower case. A user called `JaneDoe` would
open `https://janedoe.github.io/oref-digital-twin/`. The summary of the workflow run shows the
same address, and every later push to `main` republishes it.

Open the address and wait for the status line to read "Ready.", which takes a few seconds.
INSTALL.md has the same steps in more detail, how to keep your copy up to date and how to run
it on your own computer instead.

## Using it

Open your copy and enter your Nightscout address (it must start with `https://`) and a
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

Your token and data stay in the browser. Nothing is sent anywhere except the requests to your
own Nightscout.

The main report appears once the data has arrived, which on a slow Nightscout can take a
couple of minutes for a week. The settings tests then run for about two more minutes, with
a status line saying so. Keep the page open meanwhile; on a phone, switching away can stop it.

### The plain-language summary

Ticking "Also write a plain-language summary" adds a few paragraphs of prose above the report,
written by a language model (Llama 3.1 8B) that runs on your own device through WebGPU. Only the
anonymous findings (percentages and finding names, no readings, token or address) are given to
it, and it sends nothing anywhere. Its text is checked against those findings before it is
shown, and a summary that adds a number, gives a dosing instruction or leaves out a critical
finding is withheld in favour of the report alone.

The first time, the model downloads about 5 GB, which the browser keeps for later visits. It
needs a computer with a reasonably capable graphics chip and a browser with WebGPU (current
Chrome or Edge on desktop; Safari 26 or later). When the page loads it checks for WebGPU, a
graphics chip that allows the 1 GB buffers the model needs, 8 GB of memory where the browser
reports it, and room for the download, and greys the option out with the reason when any check
fails. If the model still will not load, the option is switched off for that visit. Phones
will mostly not manage it. The summary is written after the settings tests
finish, so it never delays the report. Everything else on the page works without it.

On the findings used in the grounding tests, the 8B model's summaries passed the check 19 times
in 20 over two runs; a smaller 3B model passed 4 in 10 and described SMBs as glucose readings
(`validation/narrator/`). That is one set of findings, not a measure across real reports.

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

The page offers two aims: time in range above 80% with time below range under 2% (tighter, the
default since 10 October 2026), or time in range above 70% with the same limit on lows
(standard). Tested on simulated people (validation/BAD_PROFILES_3.md), the tighter aim reached
its goal slightly more often with no measured harm. At each stage the page
picks the smallest change that meets both. When no value does, it keeps time below range
under 2% with the most time in range, and failing that it picks the value with the least
time below range, because a low is the more immediate harm. A value that gives more insulin than the current
setting is only considered when the whole period's estimate keeps time below 70 under 2% and
time below 54 under 0.6%. The tests can also take a history of the settings, which refuses a
further step towards more insulin after one the readings since did not bear out, and any step
more than 20% from a reference profile (validation/GUARD_PLAN.md); only the validation runs
give one, and the page does not yet. A stage is reported but not
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
sensitivity. A low that only the changed setting causes is treated as people are taught to treat
one: 10 g of fast carbohydrate every 15 minutes until glucose is back above 70 mg/dL, each raising
it by 10 × your ISF ÷ your carb ratio. Otherwise it assumes your meals, activity and own
treatments would have been the same under the new setting.

It is better at ranking settings than at predicting what a change will do. On simulated people
(validation/SAME_WEEK.md and validation/RESCUE.md) the estimated change in time below 70 came out
about the right size and ranked the changes well, while the estimated change in time in range was
about twice too large. Against twelve real setting changes by five AndroidAPS users the estimated
change in time in range ranked the real one (Spearman 0.74) and the estimated change in lows did
not. The report gives the simulated figures beside its tables. The tests run stock oref0; if the
page detects a variant such as Boost or AutoISF, it says that what the variant adds is not
modelled.

DESIGN.md §2.1 sets out the model, and `replay/README.md` covers the simulator, its checks
and its timings.

## How it was tested

The settings tests were checked on simulated people from TimSim, an enhanced version of the
UVA/Padova type 1 diabetes simulator. The UVA/Padova model (the S2008 version, as published in
the open-source simglucose) describes how glucose, insulin and meals interact in the body, and is
widely used to test automated insulin delivery. On its own it produces glucose traces that are noticeably
cleaner than real ones. TimSim adds the parts of real life the model leaves out, each of which can
be switched on or off:

- a defence against lows from the liver, which S2008 lacks, calibrated against published clamp
  studies
- meals eaten without telling the loop
- carbohydrate eaten to treat lows
- a sensor with realistic noise and compression lows
- insulin sensitivity that drifts from week to week
- infusion sets that stop absorbing and are noticed hours later

Its people are driven by an oref0 loop, as real users are. In TimSim's own comparison against 24-hour
windows from a closed-loop trial (DCLP3), a classifier could tell its traces from real ones with
a score of 0.739, against 0.926 for the unmodified model; 0.5 would mean the two could not be
told apart at all. It remains a simulator: its 100 people are resampled from a published cohort of 30, and it
does not reproduce what a specific person's glucose would do after a dosing change.

Twelve TimSim adults were used, each with settings first titrated by TimSim's own procedure.
For each one, the page's settings tests were run on a 14-day stretch under stock oref0. The
suggested profile and the starting profile were then each run for 28 fresh days with the same
meals, sensor noise and drift, so the profile was the only difference.

| Test | What it found | Write-up |
|---|---|---|
| Titrated starting profiles | Time below 70 fell by a mean 0.66 points (95% CI 0.30 to 1.09) and time in range by 2.61 (0.85 to 4.40); 11 of 12 met the standard aim, against 5 of 12 before | `validation/TIMSIM_ROUNDTRIP.md` |
| Eight deliberately mis-set profiles per person, 96 runs, repeated with the tighter aim | The tighter aim was met in 37 of 96, against 35 with the standard aim and 26 with the mis-set profile; no harm criterion fixed before the run was met | `validation/BAD_PROFILES_3.md` |
| The twin's estimates against the same fortnight replayed with each change, 120 comparisons | Estimates ranked changes well (Spearman correlation 0.86 for time below 70) but were about three times too large | `validation/SAME_WEEK.md` |
| The settings fixes of 8 November rechecked: same fortnight, real changes and mis-set profiles | With the 10 g rule, time below 70 estimated at about the right size (slope 0.88, 95% CI 0.74 to 1.09); no harm criterion met | `validation/SETTINGS_FIX.md` |

All of this is evidence about TimSim's people under stock oref0, not about real people.

## Layout

| Path | Purpose |
|---|---|
| `DESIGN.md` | Architecture and rationale. Start here. |
| `ingestion/` | Nightscout pulls (`devicestatus`, `entries`, `treatments`, `profile`) to a common schema. |
| `variant/` | Algorithm-variant detection (AAPS stock, DynISF, AutoISF, Trio, middleware). |
| `diagnostics/` | Deterministic sanity checks and out-of-sample pattern detection. |
| `replay/` | The oref0 `determine-basal` oracle, the closed-loop simulator and the staged settings tests. |
| `settings/` | Settings ingestion, including client-side decryption of AAPS preference exports. |
| `report/` | The report: Pyodide entry point, Markdown template, quoted official guidance and the grounding check on the summary. |
| `guidance/` | Fetching and checking the official sources the report quotes. |
| `web/` | The browser page (GitHub Pages, Pyodide, an oref0 bundle and the in-browser summary model). |
| `docs/` | Supporting notes and references. |

## Privacy

Public repository. No names, tokens, site URLs or locations in code, docs, fixtures or
commit messages. Test data is synthetic or anonymised. Nightscout tokens are read-only,
scoped, never stored and revocable.

## Licence

GNU Affero General Public License v3.0 or later (`LICENSE`), consistent with the AAPS and oref
ecosystem this builds on and replays. If you run a modified copy as a public page, the AGPL asks
you to offer its source to the people using it; a public fork does that. The page's engine bundles
oref0, lodash, moment and moment-timezone under the MIT licence, and the site serves WebLLM
under the Apache License 2.0 (`THIRD_PARTY_NOTICES.txt`).
