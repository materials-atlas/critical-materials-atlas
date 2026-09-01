#!/usr/bin/env python3
"""Feasibility scan: can we compute apparent consumption per country x material, and for how many is it
sensible? Measure-first, before committing to the production anchor's consumption input.

apparent_consumption(country c, material m) = production(c) + imports(c) - exports(c), in TONNES.
  production : per-country mine output from production.json top-5 (others -> 0)
  imports/exports : per-country net trade in tonnes (Comtrade netwgt, each country's own reports)

We report, per material: whether a physical mass balance is even meaningful (does world consumption
roughly equal world production?), and the top producer's apparent consumption (should be ~0 for a pure
exporter like DRC cobalt, large for a processor like Indonesia nickel). The KNOWN catch we want to
surface: production is mine tonnes (contained metal / ore) while trade tonnes are the gross weight of the
traded FORM (oxide, hydroxide, concentrate) -- so the balance is clean only where traded form ~ production
form (refined metals), and muddied for compounds/ores. The scan tells us which materials are which.

Run: python build_consumption_scan.py
"""
import csv, json, os, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
xw = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))
name2code = {n: e['title_code'] for n, e in xw.items() if e.get('title_code')}
prod = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'production.json'), encoding='utf8'))['rows']}
M2 = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'), encoding='utf-8')):
    try: M2[int(r['country_code'])] = r['country_iso2']
    except (ValueError, KeyError): pass
fold = lambda c: '811292' if c == '811231' else c

# per code, PARTNER-reported so a country's own (mis)reporting can't distort its own numbers, in TONNES:
#   Xto[code][c]   = imports OF c   = exporters' X reports with partner=c  (what others shipped to c)
#   Mfrom[code][c] = exports OF c   = importers' M reports with partner=c  (what others bought from c)
Xto = defaultdict(lambda: defaultdict(float)); Mfrom = defaultdict(lambda: defaultdict(float))
for r in csv.DictReader(open(os.path.join(ROOT, 'raw', 'comtrade', 'comtrade_2024.csv'), encoding='utf-8')):
    try:
        w = float(r['netwgt'] or 0) / 1000.0        # kg -> tonnes
        if w <= 0: continue
        par = int(r['partner'])
    except (ValueError, KeyError): continue
    if par not in M2: continue
    c = fold(str(r['cmd']).zfill(6))
    if r['flow'] == 'X':   Xto[c][M2[par]] += w      # exporter shipped to partner => import of partner
    elif r['flow'] == 'M': Mfrom[c][M2[par]] += w    # importer bought from partner => export of partner
X, M = Xto, Mfrom   # reuse names below: X = imports-of-c, M = exports-of-c

cells_total = cells_prod = pos = neg = 0
mat_ok = mat_muddy = 0
print(f"{'material':13}{'worldprod_t':>12}{'sum_cons_t':>12}{'balance':>9}{'topprod cons%':>14}  verdict")
for lab, code in name2code.items():
    p = prod.get(lab)
    if not p or code not in X and code not in M: continue
    wt = p.get('world_tonnes') or 0
    top5 = {t['iso']: t['tonnes'] for t in (p.get('top5') or [])}
    countries = set(X[code]) | set(M[code]) | set(top5)
    cons = {}
    for c in countries:
        cells_total += 1
        pr = top5.get(c, 0.0)
        if c in top5: cells_prod += 1
        cc = pr + X[code].get(c, 0) - M[code].get(c, 0)   # production + imports - exports
        cons[c] = cc
        pos += (cc > 0); neg += (cc < 0)
    sum_signed = sum(cons.values())          # ~ world production if the balance is meaningful
    sum_pos = sum(v for v in cons.values() if v > 0)
    bal = sum_signed / wt if wt else 0
    muddy = not (0.3 <= bal <= 3.0)          # signed world consumption far from world production => form/stage mismatch
    mat_ok += (not muddy); mat_muddy += muddy
    topc = p.get('wmd_top_iso')
    topcons = 100 * cons.get(topc, 0) / (top5.get(topc, 1) or 1) if topc in top5 else None
    verdict = 'form-muddied (compound/ore)' if muddy else 'clean-ish (traded~produced form)'
    tc = f"{topcons:+.0f}%" if topcons is not None else '   -  '
    print(f"{lab[:12]:13}{wt:>12,.0f}{sum_signed:>14,.0f}{bal:>8.1f}x{tc:>14}  {verdict}")

print(f"\nCOVERAGE: {cells_total} country x material cells attempted; {cells_prod} have production data "
      f"(top-5 producers); the rest assume prod=0.")
print(f"SANITY: {pos} cells give positive (usable) consumption, {neg} negative (stage/form mismatch or trade noise).")
print(f"MATERIALS: {mat_ok} balance within 0.3-3x of world production (feasible); {mat_muddy} are form-muddied "
      f"(traded compound/ore != mine tonnes -> need stage-aware handling before the anchor can use them).")
