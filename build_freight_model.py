#!/usr/bin/env python3
"""Freight-model identification test (author-run experiment). reconcile.py rejects a gravity CIF/FOB
model because regressing the freight RATIO (CIF/FOB, a % of value) on distance is unidentified on the
31-code slice (measured R^2 ~ 0.01). The hypothesis a reviewer raised: the failure is the VARIABLE, not
the code count -- freight scales with WEIGHT and distance, so freight-as-%-of-value drowns in the value
denominator, while freight PER TONNE against distance should be a clean physical relationship we can
identify with data already in the repo (Comtrade netwgt + centroid distance).

This tests it, falsifiably, on matched two-sided flows (2024, the tracked codes):
  value_ratio basis (reconcile.py's):  (M_cif / X_fob)          ~ distance      -> expect R^2 ~ 0.01
  weight basis (proposed):             (M_cif - X_fob)/tonne     ~ distance      -> does R^2 jump?
The CIF-FOB wedge per flow is freight + residual noise; the question is whether the distance-proportional
freight component emerges across many flows on the weight basis. Reports slope, R^2, n for each -- and a
verdict on whether the gravity approach is recoverable here or whether the robust median stays.

Run: python build_freight_model.py
"""
import os, csv, math, json, statistics
from collections import defaultdict
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
xw = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))
CODES = {e['title_code'] for e in xw.values() if e.get('title_code')}
CENT = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf-8'))['centroids']  # iso2 -> [lat,lon]
M2 = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'), encoding='utf-8')):
    try: M2[int(r['country_code'])] = r['country_iso2']
    except (ValueError, KeyError): pass

def hav(a, b):
    if a not in CENT or b not in CENT: return None
    (la1, lo1), (la2, lo2) = CENT[a], CENT[b]
    r = math.radians
    h = math.sin(r(la2-la1)/2)**2 + math.cos(r(la1))*math.cos(r(la2))*math.sin(r(lo2-lo1)/2)**2
    return 2*6371*math.asin(math.sqrt(min(1, h)))

fold = lambda c: '811292' if c == '811231' else c
# per (i,j,cmd): exporter FOB value + weight; importer CIF value + weight
X = defaultdict(lambda: [0.0, 0.0]); M = defaultdict(lambda: [0.0, 0.0])
for r in csv.DictReader(open(os.path.join(ROOT, 'raw', 'comtrade', 'comtrade_2024.csv'), encoding='utf-8')):
    try:
        v = float(r['value']); w = float(r['netwgt'] or 0)
        if v <= 0: continue
        rep, par = int(r['reporter']), int(r['partner'])
    except (ValueError, KeyError): continue
    if rep == par or rep not in M2 or par not in M2: continue
    c = fold(str(r['cmd']).zfill(6))
    if c not in CODES: continue
    if r['flow'] == 'X':   d = X[(M2[rep], M2[par], c)]; d[0] += v; d[1] += w
    elif r['flow'] == 'M': d = M[(M2[par], M2[rep], c)]; d[0] += v; d[1] += w

vr, fpk, dist = [], [], []   # value-ratio, freight $/tonne, distance(km)
for k in set(X) & set(M):
    (i, j, c) = k
    xv, xw = X[k]; mv, mw = M[k]
    d = hav(i, j)
    w = xw or mw                          # tonnes of the shipment (prefer exporter weight)
    if not (xv > 0 and mv > 0 and w > 0 and d and d > 0): continue
    vr.append((mv / xv, d))
    fpk.append(((mv - xv) / (w / 1000.0), d))   # $ per tonne (weight in kg -> /1000)

def winsor(vals, lo=2, hi=98):
    a = np.array([v[0] for v in vals]); d = np.array([v[1] for v in vals])
    ql, qh = np.percentile(a, [lo, hi]); m = (a >= ql) & (a <= qh)
    return a[m], d[m]

def fit(vals, name):
    y, x = winsor(vals)
    if len(x) < 20: return
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = A @ coef
    ss_res = float(np.sum((y - yhat)**2)); ss_tot = float(np.sum((y - y.mean())**2))
    r2 = 1 - ss_res/ss_tot if ss_tot else 0
    print(f"  {name:34} n={len(x):>5}  slope/1000km={coef[0]*1000:+.4g}  intercept={coef[1]:.4g}  R^2={r2:.3f}")
    return r2

print("Freight-model identification test (2024, matched two-sided flows on tracked codes)\n")
r2_vr = fit(vr, 'value ratio (CIF/FOB) ~ distance')
r2_fpk = fit(fpk, 'freight $/tonne ~ distance  [WEIGHT]')
print()
if r2_fpk and r2_vr is not None:
    if r2_fpk > max(0.10, 3*r2_vr):
        print(f"VERDICT: the weight basis IDENTIFIES (R^2 {r2_vr:.3f} -> {r2_fpk:.3f}). The gravity approach is")
        print("recoverable on our data by switching to freight-per-tonne. Worth building.")
    else:
        print(f"VERDICT: even the weight basis does NOT identify (R^2 {r2_vr:.3f} -> {r2_fpk:.3f}). The CIF-FOB")
        print("wedge per flow is dominated by residual noise (re-exports/misreporting), not distance. The robust")
        print("per-product median stays -- now with evidence that gravity is not recoverable here, not just asserted.")
