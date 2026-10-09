"""Judge a bad_profiles_<tag>.json against BAD_PROFILES_PLAN.md and print the tables.

    python3 validation/summarise_bad_profiles.py validation/results/bad_profiles_2026-10-09.json \
        validation/results/timsim_roundtrip_2026-10-09.json

The second file is the titrated round trip, reported beside the conditions as the reference.
"""
import json
import statistics as st
import sys

TIR_MIN, TBR70_MAX, TBR54_MAX = 80.0, 1.5, 0.4     # the pass rule, from the plan
HARM_RISE = 0.2                                    # points of time below 54, from the plan


def passes(o):
    return o["tir"] > TIR_MIN and o["tbr70"] < TBR70_MAX and o["tbr54"] < TBR54_MAX


def more_insulin(r):
    c = r["chosen"]
    return (c["basal_scale"] > 1 or c["isf_scale"] < 1 or c["cr_scale"] < 1
            or c.get("target_offset", 0) < 0 or (c.get("smb_minutes") or 75) > 75
            # the max IOB stage rounds its values to 0.1 U, so "unchanged" can come back up to
            # 0.05 U above the current value; that is not more insulin
            or (c.get("max_iob") or 0) > r["profile0"]["max_iob"] + 0.051)


def spread(v):
    return f"{st.median(v):.2f}, {st.mean(v):.2f} ({min(v):.2f}–{max(v):.2f})"


d = json.load(open(sys.argv[1]))
rows = d["rows"]
ref = json.load(open(sys.argv[2]))["subjects"] if len(sys.argv) > 2 else []
conds = list(d["design"]["conditions"])
print(f"rows {len(rows)}, failed {len(d['failed'])}, seconds {d['seconds']}")

print("\nPass rule (TIR > 80, below 70 < 1.5, below 54 < 0.4), subjects passing of 12")
print("condition | mis-set: cgm, bg | twin: cgm, bg | given more insulin")
if ref:
    print(f"titrated (reference) | {sum(passes(s['eval_start']['cgm']) for s in ref)}, "
          f"{sum(passes(s['eval_start']['bg']) for s in ref)} | "
          f"{sum(passes(s['eval_twin']['cgm']) for s in ref)}, "
          f"{sum(passes(s['eval_twin']['bg']) for s in ref)} | "
          f"{sum(more_insulin({'chosen': s['chosen'], 'profile0': s['profile0']}) for s in ref)}")
for c in conds:
    rs = [r for r in rows if r["condition"] == c]
    print(f"{c} | {sum(passes(r['eval_start']['cgm']) for r in rs)}, "
          f"{sum(passes(r['eval_start']['bg']) for r in rs)} | "
          f"{sum(passes(r['eval_twin']['cgm']) for r in rs)}, "
          f"{sum(passes(r['eval_twin']['bg']) for r in rs)} | {sum(more_insulin(r) for r in rs)}")

print("\nOutcomes on sensor glucose, median, mean (range), mis-set -> twin")
for c in conds:
    rs = [r for r in rows if r["condition"] == c]
    for k, lab in (("tir", "TIR"), ("tbr70", "<70"), ("tbr54", "<54")):
        a = [r["eval_start"]["cgm"][k] for r in rs]
        b = [r["eval_twin"]["cgm"][k] for r in rs]
        print(f"{c} {lab}: {spread(a)} -> {spread(b)}")

print(f"\nHarm check: time below 54 (cgm) higher with the twin's profile; harm is a rise > {HARM_RISE}")
harm = []
for r in rows:
    a, b = r["eval_start"]["cgm"]["tbr54"], r["eval_twin"]["cgm"]["tbr54"]
    if b > a:
        tag = "HARM" if b - a > HARM_RISE else "rise"
        harm.append((tag, r))
        bga, bgb = r["eval_start"]["bg"]["tbr54"], r["eval_twin"]["bg"]["tbr54"]
        print(f"{tag} {r['condition']} {r['name']}: {a:.2f} -> {b:.2f} (+{b - a:.2f}); bg {bga:.2f} -> "
              f"{bgb:.2f}; more insulin {more_insulin(r)}; chosen basal x{r['chosen']['basal_scale']} "
              f"ISF x{r['chosen']['isf_scale']} CR x{r['chosen']['cr_scale']} target "
              f"{r['chosen'].get('target_offset', 0):+} SMB {r['chosen'].get('smb_minutes')} "
              f"maxIOB {r['chosen'].get('max_iob')}")
n_more = sum(more_insulin(r) for r in rows)
print(f"rises {len(harm)}, harm {sum(t == 'HARM' for t, _ in harm)} of {len(rows)}; "
      f"among {n_more} given more insulin: rises {sum(more_insulin(r) for _, r in harm)}, "
      f"harm {sum(more_insulin(r) for t, r in harm if t == 'HARM')}")

print("\nDid the twin move each mis-set setting back towards its titrated value?")
for c in conds:
    rs = [r for r in rows if r["condition"] == c]
    for lever in d["design"]["conditions"][c]:
        start = rs[0]["titrated_vs_start"][lever]
        towards = sum(abs(r["titrated_vs_twin"][lever] - 1) < abs(r["titrated_vs_start"][lever] - 1) - 1e-9
                      for r in rs)
        away = sum(abs(r["titrated_vs_twin"][lever] - 1) > abs(r["titrated_vs_start"][lever] - 1) + 1e-9
                   for r in rs)
        ends = [round(r["titrated_vs_twin"][lever], 2) for r in rs]
        print(f"{c} {lever} (start x{start:.2f} of titrated): towards {towards}, away {away}, "
              f"unchanged {len(rs) - towards - away}; twin's value as a multiple of titrated {sorted(ends)}")

print("\nEstimated against realised change in time below 70 (cgm), median per condition")
for c in conds:
    rs = [r for r in rows if r["condition"] == c]
    est = [r["twin_estimate"]["est_all"]["tbr"] - r["twin_observed"]["tbr"] for r in rs]
    real = [r["eval_twin"]["cgm"]["tbr70"] - r["eval_start"]["cgm"]["tbr70"] for r in rs]
    print(f"{c}: estimated {st.median(est):+.2f}, realised {st.median(real):+.2f}")
