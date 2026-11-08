#!/usr/bin/env bash
# The four rechecks of SETTINGS_FIX_PLAN.md, in sequence (results in SETTINGS_FIX.md). Run 3 is in
# the private analysis repository at ~/oref-investigations.
set -e
PY=~/.venvs/boost-insilico/bin/python
R='{"grams": 10, "threshold": 70, "refractory_min": 15, "delay": 10, "rise_min": 30, "mode": "new"}'
cd ~/oref-digital-twin
echo "== run 1 $(date)"; $PY validation/same_week.py --workers 7 --out validation/results/same_week_2026-11-08.json
$PY validation/summarise_same_week.py validation/results/same_week_2026-11-08.json
echo "== run 2 $(date)"; $PY validation/same_week.py --workers 7 --rescue "$R" --truth-from validation/results/same_week_2026-11-08.json --out validation/results/same_week_rescue10g_new_2026-11-08.json
$PY validation/summarise_same_week.py validation/results/same_week_rescue10g_new_2026-11-08.json
cd ~/oref-investigations
echo "== run 3 $(date)"; TWIN_TAG=_fix $PY twin_backtest/estimate_aaps.py "240 NS samples" twin_backtest/events_aaps_w7_i0.05.json
$PY twin_backtest/analyse.py twin_backtest/results_aaps_fix.json
TWIN_RESCUE="$R" TWIN_TAG=_fix $PY twin_backtest/estimate_aaps.py "240 NS samples" twin_backtest/events_aaps_w7_i0.05.json
$PY twin_backtest/analyse.py twin_backtest/results_aaps_rescue_fix.json
cd ~/oref-digital-twin
echo "== run 4 $(date)"; $PY validation/timsim_roundtrip.py --conditions isf_strong,isf_weak,basal_high,basal_low,cr_strong,cr_weak,all_strong,all_weak --store validation/results/titrated_2026-10-09.json --eval-seeds 101,102,103 --eval-days 28 --null --aim tighter --reuse-arms validation/results/bad_profiles_2026-10-09b.json --tag 2026-11-08-fix --workers 7 > validation/results/bad_profiles_run_2026-11-08-fix.log 2>&1
$PY validation/summarise_bad_profiles_3.py validation/results/bad_profiles_2026-11-08-fix.json validation/results/bad_profiles_2026-11-07-rescue.json
echo "== done $(date)"
