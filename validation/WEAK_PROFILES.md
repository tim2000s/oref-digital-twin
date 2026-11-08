# Why the twin rarely strengthens a too-weak ISF or basal

A diagnostic, not a pre-registered test. The fourth mis-set run and its rerun on the settings fixes
(`BAD_PROFILES_4.md`, `SETTINGS_FIX.md`) showed the twin rarely moving a too-weak ISF or basal back
towards its titrated value, while often strengthening the carb ratio. `weak_profile_stages.py`
reran the learning fortnight and the twin, with the tighter aim, for the 48 subject-conditions with
too little insulin and kept every stage's table; `summarise_weak_profile_stages.py` counts them.
Results in `results/weak_profile_stages_2026-11-08.json`, 8 November 2026, the twin at 3ad9550.

Three explanations were written down before the run: the choice rule stops at the smallest change
that meets the aim; the strengthening limit removes every stronger value when the learning
fortnight already has lows; and the twin takes the mis-set ISF as the body's sensitivity. The run
tests the first two only.

| Condition, stage | Chosen: stronger, unchanged, weaker | Rule that decided | Every stronger value excluded by the limit | A stronger value estimated over 1 point more in range |
|---|---|---|---|---|
| ISF too weak, ISF | 1, 9, 2 | already meets the aim 9, most in range with lows under 2% 2, smallest change 1 | 2 | 12 |
| Basal too low, basal | 0, 7, 5 | already meets the aim 7, smallest change 3, fewest lows 2 | 4 | 4 |
| Carb ratio too weak, carb ratio | 7, 4, 1 | most in range with lows under 2% 7, already meets the aim 3, smallest change 2 | 1 | 6 |
| All too weak, basal | 1, 10, 1 | already meets the aim 10 | 1 | 2 |
| All too weak, ISF | 6, 6, 0 | already meets the aim 5, smallest change 5 | 1 | 12 |
| All too weak, carb ratio | 10, 2, 0 | most in range with lows under 2% 9 | 0 | 8 |

The first explanation accounts for most of it. `choose` takes the smallest change that meets the
aim (time in range above 80%, below 70 under 2%) on the stretches each stage is judged on. With ISF
too weak, the whole period already met the aim in 9 of 12, so ISF was left as it was, although in
all 12 a stronger ISF was estimated to give more than a point more time in range. Basal, judged on
fasting stretches, already met it in 7 of 12. The loop's own corrections make up most of the
missing insulin outside meals, so those stretches look acceptable.

The carb ratio is judged on meal stretches, which rarely meet the aim; there the rule takes the
value with most time in range and lows under 2%, which is usually a stronger carb ratio. The twin
therefore puts the correction on the one setting whose stretches show the shortfall, whichever
setting was wrong.

The strengthening limit is the second cause and the smaller one: it removed every stronger value
in 2 of 12 ISF stages and 4 of 12 basal stages, all in people whose learning fortnight had time
below 70 above 2%. Where it did, the fallback rule chose the value with the fewest estimated lows,
which for basal was a further cut (adult#011: basal to 0.49 of titrated, time in range on
evaluation 76.6% to 70.4%).

The third explanation is untested.
