#!/usr/bin/env python3
"""Controlled experiment (author-run; NOT wired into the live build): does the two-sided reconciliation's
GEOMETRIC mean (inverse-variance averaging on logs, reconcile.py step 4) systematically understate
concentration, and does switching to a level-space ARITHMETIC inverse-variance mean cure it?

A geometric mean sits below the arithmetic mean by a gap that grows with the mirror disagreement, which
is largest for big dominant flows -> the leader is pulled down hardest -> HHI understated. This rebuilds
the reconciliation from raw Comtrade for 2024 with BOTH operators (identical CIF/FOB deflation and
reliability weights), computes export-HHI per commodity, and compares each to official BACI and to the
raw [exporter-only, importer-only] bracket.

Run: python reconcile/operator_test.py
"""
import os, csv, math, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YEAR = 2024

M49 = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'), encoding='utf-8')):
    try:
        M49[int(r['country_code'])] = r['country_iso3']
    except (ValueError, KeyError):
        pass

def fold(c): return '811292' if c == '811231' else c

# ---- build two-sided flows from raw Comtrade ----
exp, imp = defaultdict(float), defaultdict(float)   # (i,j,cmd) FOB export ; (i,j,cmd) CIF import
for r in csv.DictReader(open(os.path.join(ROOT, 'raw', 'comtrade', f'comtrade_{YEAR}.csv'), encoding='utf-8')):
    try:
        v = float(r['value'])
        if v <= 0: continue
        rep, par = int(r['reporter']), int(r['partner'])
    except (ValueError, KeyError):
        continue
    if rep == par or rep not in M49 or par not in M49: continue
    c = fold(str(r['cmd']).zfill(6))
    if r['flow'] == 'X':   exp[(M49[rep], M49[par], c)] += v      # reporter exports to partner
    elif r['flow'] == 'M': imp[(M49[par], M49[rep], c)] += v      # reporter imports from partner -> exporter=partner

keys = set(exp) | set(imp)

# ---- CIF/FOB per-commodity median markup (same recipe as reconcile.py) ----
ratios = defaultdict(list)
for k in set(exp) & set(imp):
    x, m = exp[k], imp[k]
    if x > 0 and m > 0:
        ratios[k[2]].append(min(max(m / x, 0.3), 3.0))
cif = {c: min(max(statistics.median(v), 1.02), 1.30) for c, v in ratios.items()}
gmed = min(max(statistics.median([x for v in ratios.values() for x in v]), 1.02), 1.30)

# ---- reliability weights: variance of log mirror discrepancy per country (i- and j-role pooled) ----
disc = defaultdict(list)
for k in set(exp) & set(imp):
    x = exp[k]; mf = imp[k] / cif.get(k[2], gmed)
    if x > 0 and mf > 0:
        d2 = (math.log(x) - math.log(mf)) ** 2
        disc[k[0]].append(d2); disc[k[1]].append(d2)
var = {iso: max(statistics.mean(v), 1e-3) for iso, v in disc.items()}
medvar = statistics.median(list(var.values()))
def vget(iso): return var.get(iso, medvar)

# ---- reconcile with each operator ----
def reconcile(op, drop_imp_only=False):
    agg = defaultdict(lambda: defaultdict(float))    # cmd -> exporter -> value
    for k in keys:
        i, j, c = k
        x = exp.get(k, 0.0)
        mf = imp.get(k, 0.0) / cif.get(c, gmed)
        if x > 0 and mf > 0:
            wi, wj = 1.0 / vget(i), 1.0 / vget(j)
            if op == 'geometric':
                val = math.exp((wi * math.log(x) + wj * math.log(mf)) / (wi + wj))
            else:  # arithmetic inverse-variance on levels
                val = (wi * x + wj * mf) / (wi + wj)
        elif x > 0:
            val = x                              # exporter-only
        elif mf > 0:
            if drop_imp_only:                    # importer-only (no exporter mirror) — likely re-export/entrepot
                continue
            val = mf
        else:
            continue
        agg[c][i] += val
    return agg

def hhi(d):
    t = sum(d.values()); return sum((v / t) ** 2 for v in d.values()) if t else None

def raw_hhi(src):
    agg = defaultdict(lambda: defaultdict(float))
    for k, v in src.items():
        agg[k[2]][k[0]] += v
    return {c: hhi(d) for c, d in agg.items()}

geo = reconcile('geometric'); ari = reconcile('arithmetic')
geo_nx = reconcile('geometric', drop_imp_only=True)   # diagnostic: drop importer-only flows
h_geo = {c: hhi(d) for c, d in geo.items()}
h_ari = {c: hhi(d) for c, d in ari.items()}
h_nx = {c: hhi(d) for c, d in geo_nx.items()}
h_exp = raw_hhi(exp); h_imp = raw_hhi(imp)

# ---- BACI benchmark (itself a reconciliation, not ground truth) ----
bexp = defaultdict(lambda: defaultdict(float))
for r in csv.DictReader(open(os.path.join(ROOT, 'reconcile', f'baci_{YEAR}.csv'), encoding='utf-8')):
    try: bexp[r['cmd']][r['i']] += float(r['value'])
    except (ValueError, KeyError): pass
h_baci = {c: hhi(d) for c, d in bexp.items()}

codes = sorted(set(h_geo) & set(h_baci) & set(h_exp) & set(h_imp))
dg = [h_baci[c] - h_geo[c] for c in codes]     # BACI - geometric (positive = geo understates)
da = [h_baci[c] - h_ari[c] for c in codes]     # BACI - arithmetic
def inside(c, h):
    lo, hi = sorted((h_exp[c], h_imp[c])); return lo - 1e-9 <= h[c] <= hi + 1e-9
print(f"2024, {len(codes)} commodities. Gap to BACI (positive = engine understates concentration):")
print(f"  GEOMETRIC (current):  mean {statistics.mean(dg):+.3f}  median {statistics.median(dg):+.3f}  "
      f"| understates (gap>0.02) in {sum(1 for x in dg if x>0.02)}/{len(codes)}  "
      f"| inside raw bracket {sum(inside(c,h_geo) for c in codes)}/{len(codes)}")
print(f"  ARITHMETIC (proposed):mean {statistics.mean(da):+.3f}  median {statistics.median(da):+.3f}  "
      f"| understates (gap>0.02) in {sum(1 for x in da if x>0.02)}/{len(codes)}  "
      f"| inside raw bracket {sum(inside(c,h_ari) for c in codes)}/{len(codes)}")
dn = [h_baci[c] - h_nx[c] for c in codes if c in h_nx]
print(f"  DROP importer-only:   mean {statistics.mean(dn):+.3f}  median {statistics.median(dn):+.3f}  "
      f"| understates (gap>0.02) in {sum(1 for x in dn if x>0.02)}/{len(dn)}  "
      f"| inside raw bracket {sum(inside(c,h_nx) for c in codes if c in h_nx)}/{len(dn)}")
print(f"\n  abs gap to BACI: geometric {statistics.mean(abs(x) for x in dg):.3f}  arithmetic {statistics.mean(abs(x) for x in da):.3f}  drop-imp-only {statistics.mean(abs(x) for x in dn):.3f}")
print("\nworst geometric understatements, and what arithmetic gives (exp/imp/geo/ari/BACI):")
for c in sorted(codes, key=lambda c: -(h_baci[c] - h_geo[c]))[:10]:
    print(f"  {c}: {h_exp[c]:.2f}/{h_imp[c]:.2f}/{h_geo[c]:.2f}/{h_ari[c]:.2f}/{h_baci[c]:.2f}")
