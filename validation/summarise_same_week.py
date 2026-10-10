"""The analysis of SAME_WEEK_PLAN.md on results/same_week_2026-10-10.json.

    python3 validation/summarise_same_week.py validation/results/same_week_2026-10-10.json
"""
import json
import random
import statistics as st
import sys

d = json.load(open(sys.argv[1]))
subs = [s for s in d["subjects"] if s["replay_exact"]]
print(f"subjects {len(d['subjects'])}, replay exact {len(subs)}, {d['seconds']:.0f} s")


def ranks(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    mx, my = st.mean(rx), st.mean(ry)
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / den if den else float("nan")


def slope(x, y):
    mx, my = st.mean(x), st.mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx if sxx else float("nan")


def pairs(metric, change=None):
    return [(r["estimated"][metric], r["same_fortnight"][metric], s["name"])
            for s in subs for r in s["rows"] if change in (None, r["change"])]


def boot(metric, fn, n=5000, seed=0):
    """Bootstrap over subjects (their ten changes travel together)."""
    rng = random.Random(seed)
    names = [s["name"] for s in subs]
    by = {nm: [(e, t) for e, t, n2 in pairs(metric) if n2 == nm] for nm in names}
    vals = []
    for _ in range(n):
        pick = [p for _ in names for p in by[rng.choice(names)]]
        x, y = [p[0] for p in pick], [p[1] for p in pick]
        vals.append(fn(x, y))
    vals.sort()
    return vals[int(0.025 * n)], vals[int(0.975 * n)]


print("\nPooled over subjects and changes")
for m, lab in (("tbr70", "below 70"), ("tir", "in range"), ("tbr54", "below 54")):
    p = pairs(m)
    x, y = [a for a, _, _ in p], [b for _, b, _ in p]
    rho, sl = spearman(x, y), slope(x, y)
    print(f"  {lab}: n {len(p)}, Spearman {rho:+.3f} [{boot(m, spearman)[0]:+.3f}, {boot(m, spearman)[1]:+.3f}], "
          f"slope of same-fortnight on estimated {sl:+.3f} [{boot(m, slope)[0]:+.3f}, {boot(m, slope)[1]:+.3f}]")

thr = {"tbr70": 0.5, "tir": 2.0}
print("\nSign agreement where the same-fortnight change is large")
for m, t in thr.items():
    p = [(a, b) for a, b, _ in pairs(m) if abs(b) >= t]
    print(f"  {m}: {sum((a > 0) == (b > 0) for a, b in p)} of {len(p)}")

print("\nPer change: median estimated and same-fortnight change, median ratio estimated/same (where |same| > 0.2)")
for ch in d["changes"]:
    for m in ("tbr70", "tir"):
        p = pairs(m, ch)
        est = [a for a, _, _ in p]
        tru = [b for _, b, _ in p]
        rat = [a / b for a, b, _ in p if abs(b) > 0.2]
        print(f"  {ch} {m}: estimated {st.median(est):+.2f}, same fortnight {st.median(tru):+.2f}, "
              f"ratio {st.median(rat) if rat else float('nan'):.2f} (n {len(rat)})")
