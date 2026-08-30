#!/usr/bin/env python3
"""Model bake-off for the nowcast (author-run; logged in the changelog). A reviewer asked: can a
better forecasting model beat naive persistence at nowcasting each material's export shares? Test a
suite of standard methods out-of-sample (predict each year 2019-2024 from prior years only) and score
them against persistence. Candidate list contributed by Codex; the ones fit for short, persistent,
compositional, low-N series: moving averages, simple exponential smoothing, shrink-to-mean
(James-Stein flavour), linear trend.

Result: NONE beats persistence at identifying the top exporter (84.4% is the ceiling). Shrink-to-mean
marginally improves the share error (4.83 -> 4.66pp). This confirms Meese-Rogoff on our own data: a
highly persistent series leaves little for a cleverer extrapolation to add — the real lever is the
reconciliation engine using CURRENT-year data (pre-registered forward test), not model sophistication.
Untested and plausibly better in low-N (Codex): hierarchical/panel shrinkage across all 32 materials.

Run: python build_nowcast_models.py
"""
import os, json, statistics

ROOT = os.path.dirname(os.path.abspath(__file__))
LAB = [m['label'] for m in json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))['materials']]
cache = {}
def load(y):
    if y not in cache:
        p = os.path.join(ROOT, 'out', f'flows_{y}.json')
        cache[y] = json.load(open(p, encoding='utf8')).get('materials', {}) if os.path.exists(p) else None
    return cache[y]
def sh(mats, lab):
    o, t = {}, 0.0
    for f in (mats.get(lab) or []):
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; t += f['value']
    return {c: v / t for c, v in o.items()} if t else None
def norm(d):
    t = sum(max(0, v) for v in d.values())
    return {c: max(0, v) / t for c, v in d.items()} if t > 0 else d
def top(d): return max(d, key=d.get) if d else None
def allc(hist):
    s = set()
    for d in hist.values():
        s |= set(d)
    return s

series = {lab: {y: sh(load(y), lab) for y in range(2002, 2025) if load(y) and sh(load(y), lab)} for lab in LAB}

def m_persist(h, ys): return h[ys[-1]]
def m_ma(k):
    def f(h, ys):
        use = ys[-k:]
        return norm({c: statistics.mean(h[y].get(c, 0) for y in use) for c in allc({y: h[y] for y in use})})
    return f
def m_ses(a):
    def f(h, ys):
        cs = allc(h); est = {c: h[ys[0]].get(c, 0) for c in cs}
        for y in ys[1:]:
            for c in cs:
                est[c] = a * h[y].get(c, 0) + (1 - a) * est[c]
        return norm(est)
    return f
def m_shrink(a, k):
    ma = m_ma(k)
    def f(h, ys):
        p, mm = h[ys[-1]], ma(h, ys)
        return norm({c: a * p.get(c, 0) + (1 - a) * mm.get(c, 0) for c in allc(h)})
    return f
def m_lintrend(k):
    def f(h, ys):
        use = ys[-k:]; n = len(use); xs = list(range(n)); xb = sum(xs) / n; out = {}
        for c in allc({y: h[y] for y in use}):
            yv = [h[y].get(c, 0) for y in use]; yb = sum(yv) / n
            den = sum((x - xb) ** 2 for x in xs) or 1
            b = sum((xs[i] - xb) * (yv[i] - yb) for i in range(n)) / den
            out[c] = yb + b * (n - xb)
        return norm(out)
    return f

MODELS = {'persistence (naive)': m_persist, '3-yr moving avg': m_ma(3), '5-yr moving avg': m_ma(5),
          'exp. smoothing (a=.4)': m_ses(0.4), 'shrink 70% -> 5-yr mean': m_shrink(0.7, 5), 'linear trend': m_lintrend(4)}
res = {k: {'hit': 0, 'n': 0, 'smae': []} for k in MODELS}
for lab in LAB:
    h = series[lab]; ys_all = sorted(h)
    for T in range(2019, 2025):
        if T not in h:
            continue
        hist = [y for y in ys_all if y < T]
        if len(hist) < 3:
            continue
        hpast = {y: h[y] for y in hist}; actual = h[T]; at = top(actual)
        for name, fn in MODELS.items():
            try:
                pred = fn(hpast, hist)
            except Exception:
                continue
            r = res[name]; r['n'] += 1
            r['hit'] += (top(pred) == at)
            r['smae'].append(abs(pred.get(at, 0) - actual[at]) * 100)

print(f"{'model':24} {'top-hit':>8} {'shareMAE':>9}")
for name, r in res.items():
    print(f"{name:24} {100*r['hit']/r['n']:7.1f}% {statistics.mean(r['smae']):8.2f}pp")
print("\nNo model beats naive persistence at identifying the top exporter; shrink-to-mean marginally "
      "improves the share error. Persistence is near-optimal among simple models — the real lever is "
      "current-year reconciliation, not a cleverer extrapolation.")
