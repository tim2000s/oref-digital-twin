# oref digital twin — report

Findings: 0 critical, 2 to watch, 3 notes.

## Your setup

- Detected: **unknown** (confidence 0.0)
- The controller could not be classified — findings only.

## Glucose

- Readings: 4032 over ~14.0 days
- Mean: 130.7 mg/dL (7.3 mmol/L), GMI 6.4%
- Time in range (70–180): 85.4%
- Time below 70: 3.1%; below 54: 0.4%
- Time above 180: 11.5%; above 250: 1.6%
- Variability (CV): 33.0%

## Findings

### Worth attention

- **Overnight SMBs at high IOB, with lows following** — 216 of 397 overnight SMBs fired at high IOB (>= p75 6.51 U); 4 (1.9%) were followed by BG < 70 mg/dL within 2h. Association only — this names the pattern, it does not prove the SMB caused the low.
- **Nocturnal hypoglycaemia episodes** — 9 overnight (00:00-06:00) low episode(s) below 70 mg/dL across 7 night(s). Overnight lows are the domain's repeated risk; cross-check against overnight SMBs and IOB.

### Notes

- **Meets consensus glycaemic targets** — TIR 85.4%, TBR<70 3.1%, TBR<54 0.4% — within consensus targets over this window.
- **Estimated daily insulin** — ~80.5 U/day estimated (profile basal ~24.91 U + bolus/SMB ~55.6 U/day). Rough: basal is the scheduled profile, not delivered basal, and temp basals are not integrated.
- **30-min IOB prediction bias -7.2 mg/dL** — Over 4027 cycles the IOB-only prediction ran 7.2 mg/dL lower than realised on average (MAE 16.8). A large systematic bias points at model calibration; it is descriptive, not a dosing instruction.


---

_This is decision-support, not medical advice, and it is advisory-only — it never changes your loop or pump. Discuss any change with your clinician and trial it deliberately._

## Settings tests (estimated)

Goal: time in range above 70% and time below range under 2%. Observed over 14.0 days: 85.4% in range, 3.1% below, 14 low episodes.

Each setting is stepped from −30% to +30% and the loop is re-run through every 5-minute cycle (4032) under each value. Basal is tested first, on fasting stretches; ISF next, on correction stretches; then carb ratio on meals; then target, the SMB limit and max IOB over the whole period. Each stage keeps the choices before it.

_Estimated, not measured: each value's glucose is your CGM shifted by the change in insulin the loop would have given, times your profile ISF, with the loop reacting to the shifted glucose at every step. It assumes your meals, activity and own treatments would have been the same, and that your profile ISF is your real sensitivity. Treat any change as a trial to test, one setting at a time._

_Your loop was detected as unknown. These tests run stock oref0, so anything your variant adds on top of it is not modelled._

Insulin curve: rapid-acting (settings).

### 1. Basal

Judged on fasting stretches (no carbs or meal-sized rise in the last 4 h, nothing above 180 mg/dL in the last 3 h): 94.7 h of readings, observed 93.6% in range and 6.4% below.

| Basal rates | Average glucose change | In range (fasting) | Below range (fasting) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% ← | +10 mg/dL (+0.5 mmol/L) | 96.7% | 3.3% | 4 | 80.0% | 1.4% |
| -20% | +6 mg/dL (+0.3 mmol/L) | 95.8% | 4.2% | 5 | 81.7% | 1.9% |
| -10% | +3 mg/dL (+0.2 mmol/L) | 94.2% | 5.8% | 6 | 83.0% | 2.6% |
| current | +0 mg/dL (+0.0 mmol/L) | 93.6% | 6.4% | 7 | 85.4% | 3.1% |
| +10% | -2 mg/dL (-0.1 mmol/L) | 92.2% | 7.8% | 9 | 85.5% | 4.4% |
| +20% | -5 mg/dL (-0.3 mmol/L) | 90.8% | 9.2% | 11 | 85.5% | 5.6% |
| +30% | -8 mg/dL (-0.4 mmol/L) | 89.9% | 10.1% | 12 | 85.0% | 6.5% |

Trial to consider: basal rates -30%, because no value gets lows under 2%; this has the fewest.

### 2. ISF

Judged on correction stretches (above 180 mg/dL in the last 3 h, outside meals): 27.8 h of readings, observed 69.5% in range and 8.4% below.
Run with basal rates -30%.

| ISF | Average glucose change | In range (correction) | Below range (correction) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +2 mg/dL (+0.1 mmol/L) | 44.9% | 8.4% | 3 | 81.1% | 3.4% |
| -20% | +4 mg/dL (+0.2 mmol/L) | 46.1% | 6.3% | 3 | 80.9% | 2.6% |
| -10% | +7 mg/dL (+0.4 mmol/L) | 47.3% | 4.8% | 1 | 80.7% | 1.9% |
| current | +10 mg/dL (+0.5 mmol/L) | 47.9% | 3.9% | 1 | 80.0% | 1.4% |
| +10% | +12 mg/dL (+0.7 mmol/L) | 49.7% | 1.5% | 0 | 79.9% | 0.7% |
| +20% | +14 mg/dL (+0.8 mmol/L) | 50.3% | 0.9% | 0 | 79.3% | 0.5% |
| +30% ← | +17 mg/dL (+0.9 mmol/L) | 50.6% | 0.3% | 0 | 78.5% | 0.2% |

Trial to consider: ISF +30%, because no value reaches 70% in range; this keeps lows under 2% with the most time in range.

### 3. Carb ratio

Judged on meal stretches (the 4 h after logged carbs or a meal-sized rise): 213.5 h of readings, observed 83.8% in range and 1.0% below.
Run with basal rates -30%, ISF +30%.
Logged meal boluses are scaled with the ratio, as the bolus wizard would.

| Carb ratio | Average glucose change | In range (meal) | Below range (meal) | Low episodes | In range (all) | Below range (all) |
|---|---|---|---|---|---|---|
| -30% | +16 mg/dL (+0.9 mmol/L) | 73.1% | 0.0% | 0 | 78.6% | 0.3% |
| -20% | +16 mg/dL (+0.9 mmol/L) | 73.0% | 0.0% | 0 | 78.5% | 0.3% |
| -10% | +16 mg/dL (+0.9 mmol/L) | 73.1% | 0.0% | 0 | 78.5% | 0.3% |
| current ← | +17 mg/dL (+0.9 mmol/L) | 73.0% | 0.0% | 0 | 78.5% | 0.2% |
| +10% | +17 mg/dL (+0.9 mmol/L) | 72.9% | 0.0% | 0 | 78.4% | 0.3% |
| +20% | +17 mg/dL (+1.0 mmol/L) | 72.6% | 0.0% | 0 | 78.2% | 0.2% |
| +30% | +18 mg/dL (+1.0 mmol/L) | 72.3% | 0.0% | 0 | 78.1% | 0.2% |

No change suggested: already meets both goals.

### 4. Target

Judged on the whole period: 336.0 h of readings, observed 85.4% in range and 3.1% below.
Run with basal rates -30%, ISF +30%.

| Target | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| -1.0 mmol/L (-18 mg/dL) on every target: 92 mg/dL (5.1 mmol/L) | -1 mg/dL (-0.1 mmol/L) | 81.6% | 3.6% | 14 |
| -0.5 mmol/L (-9 mg/dL) on every target: 101 mg/dL (5.6 mmol/L) | +8 mg/dL (+0.4 mmol/L) | 81.0% | 1.4% | 8 |
| 110 mg/dL (6.1 mmol/L) (current) ← | +17 mg/dL (+0.9 mmol/L) | 78.5% | 0.2% | 2 |
| +0.5 mmol/L (+9 mg/dL) on every target: 119 mg/dL (6.6 mmol/L) | +26 mg/dL (+1.4 mmol/L) | 75.2% | 0.0% | 0 |
| +1.0 mmol/L (+18 mg/dL) on every target: 128 mg/dL (7.1 mmol/L) | +34 mg/dL (+1.9 mmol/L) | 70.1% | 0.0% | 0 |

No change suggested: already meets both goals.

### 5. SMB limit

Judged on the whole period: 336.0 h of readings, observed 85.4% in range and 3.1% below.
Run with basal rates -30%, ISF +30%.

| Maximum SMB basal minutes | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 15 min | +21 mg/dL (+1.1 mmol/L) | 77.1% | 0.2% | 1 |
| 30 min | +17 mg/dL (+1.0 mmol/L) | 78.2% | 0.2% | 1 |
| 45 min | +17 mg/dL (+0.9 mmol/L) | 78.5% | 0.2% | 2 |
| 60 min | +16 mg/dL (+0.9 mmol/L) | 78.8% | 0.3% | 2 |
| 75 min (current) ← | +16 mg/dL (+0.9 mmol/L) | 78.8% | 0.3% | 2 |
| 90 min | +16 mg/dL (+0.9 mmol/L) | 78.8% | 0.3% | 2 |

No change suggested: already meets both goals.

### 6. Max IOB

Judged on the whole period: 336.0 h of readings, observed 85.4% in range and 3.1% below.
Run with basal rates -30%, ISF +30%.

| Max IOB | Average glucose change | In range | Below range | Low episodes |
|---|---|---|---|---|
| 5.2 U | +34 mg/dL (+1.9 mmol/L) | 71.2% | 0.1% | 0 |
| 6 U | +26 mg/dL (+1.5 mmol/L) | 74.7% | 0.2% | 1 |
| 6.7 U | +21 mg/dL (+1.2 mmol/L) | 77.7% | 0.2% | 1 |
| 7.5 U ← | +16 mg/dL (+0.9 mmol/L) | 78.9% | 0.3% | 2 |
| 8.2 U | +14 mg/dL (+0.8 mmol/L) | 80.1% | 0.4% | 2 |
| 9 U | +13 mg/dL (+0.7 mmol/L) | 80.8% | 0.4% | 2 |
| 9.7 U | +13 mg/dL (+0.7 mmol/L) | 80.9% | 0.4% | 2 |

Trial to consider: max IOB 7.5 U, because the smallest change that meets both goals.

### Together

With basal rates -30%, ISF +30%, max IOB 7.5 U: estimated 78.9% in range and 0.3% below (observed 85.4% and 3.1%), average glucose +16 mg/dL (+0.9 mmol/L). That meets both goals.

Change one setting at a time and give each a few days before the next, so its effect can be seen on its own.