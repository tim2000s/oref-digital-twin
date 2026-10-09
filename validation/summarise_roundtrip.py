"""Print the tables in TIMSIM_ROUNDTRIP.md from a timsim_roundtrip_<tag>.json.

    python3 validation/summarise_roundtrip.py validation/results/timsim_roundtrip_2026-10-09.json
"""
import json
import statistics as st
import sys

import numpy as np

d = json.load(open(sys.argv[1]))
subs = d["subjects"]
print(f"subjects {len(subs)}, failed {len(d['design']['subjects_failed'])}")
for sig in ("cgm", "bg"):
    print(f"\n{sig}: metric | start median, mean, range | twin median, mean, range | "
          "paired difference median [95% CI], mean [95% CI], subjects better")
    for k in ("tir", "tbr70", "tbr54", "tar180", "mean"):
        a, b = d["outcomes"]["eval_start"][sig][k], d["outcomes"]["eval_twin"][sig][k]
        p = d["paired_twin_minus_start"][sig][k]
        print(f"{k} | {a['median']:.1f}, {a['mean']:.1f}, {a['min']:.1f}-{a['max']:.1f} | "
              f"{b['median']:.1f}, {b['mean']:.1f}, {b['min']:.1f}-{b['max']:.1f} | "
              f"{p['median']:+.2f} [{p['median_ci'][0]:+.2f}, {p['median_ci'][1]:+.2f}], "
              f"{p['mean']:+.2f} [{p['mean_ci'][0]:+.2f}, {p['mean_ci'][1]:+.2f}], {p['improved']}/{p['n']}")
print("\nper subject: choices | eval start TIR/TBR -> twin TIR/TBR (cgm) | rescues | "
      "estimated vs realised change in TBR and TIR")
est_tbr, real_tbr, est_tir, real_tir = [], [], [], []
for s in subs:
    c, o, e = s["chosen"], s["twin_observed"], s["twin_estimate"]["est_all"]
    e0, e1 = s["eval_start"]["cgm"], s["eval_twin"]["cgm"]
    est_tbr.append(e["tbr"] - o["tbr"]); real_tbr.append(e1["tbr70"] - e0["tbr70"])
    est_tir.append(e["tir"] - o["tir"]); real_tir.append(e1["tir"] - e0["tir"])
    print(f"{s['name']} | basal x{c['basal_scale']} ISF x{c['isf_scale']} CR x{c['cr_scale']} "
          f"target {c['target_offset']:+} SMB {c.get('smb_minutes')} maxIOB {c.get('max_iob')} | "
          f"{e0['tir']:.1f}/{e0['tbr70']:.1f} -> {e1['tir']:.1f}/{e1['tbr70']:.1f} | "
          f"{s['eval_start']['rescue_events']} -> {s['eval_twin']['rescue_events']} | "
          f"TBR {est_tbr[-1]:+.1f} vs {real_tbr[-1]:+.1f}, TIR {est_tir[-1]:+.1f} vs {real_tir[-1]:+.1f}")
for lab, v in (("estimated TBR change", est_tbr), ("realised TBR change", real_tbr),
               ("estimated TIR change", est_tir), ("realised TIR change", real_tir)):
    print(f"{lab}: median {st.median(v):+.2f}, mean {st.mean(v):+.2f}")
print(f"correlation estimated vs realised: TBR {np.corrcoef(est_tbr, real_tbr)[0, 1]:.2f}, "
      f"TIR {np.corrcoef(est_tir, real_tir)[0, 1]:.2f}")
goal = lambda r: r["tir"] > 70 and r["tbr70"] < 2
print(f"meeting TIR > 70% and TBR < 2% (cgm): start {sum(goal(s['eval_start']['cgm']) for s in subs)}, "
      f"twin {sum(goal(s['eval_twin']['cgm']) for s in subs)} of {len(subs)}")
print(f"rescue carbohydrate events: start {sum(s['eval_start']['rescue_events'] for s in subs)}, "
      f"twin {sum(s['eval_twin']['rescue_events'] for s in subs)}")
print(f"insulin U/day mean: start {st.mean(s['eval_start']['insulin_u_per_day'] for s in subs):.1f}, "
      f"twin {st.mean(s['eval_twin']['insulin_u_per_day'] for s in subs):.1f}")
