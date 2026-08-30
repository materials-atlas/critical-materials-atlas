#!/usr/bin/env python3
"""Reconciliation envelope (author-run; answers an adversarial-council demand). A hostile review
objected that the atlas was calling CEPII BACI the 'un-diluted official ground truth' and correcting
its own reconciliation 'toward' it — circular, because BACI is itself a reliability-weighted
reconciliation of the same UN Comtrade mirror reports. Correct. So instead of one benchmark, report
the ENVELOPE: for each commodity, export-concentration (HHI) and the leading exporter computed four
ways —

  1. exporter-only  : trust only the exporter's own X (FOB) report      -- one raw end of the mirror
  2. importer-only  : trust only the importer's M (CIF) report          -- the other raw end
  3. engine         : the atlas reconciliation (reconcile.py: CIF/FOB deflation + inverse-variance
                      reliability weights on logs)                       -- one reconciliation
  4. BACI           : CEPII's reconciliation (Gaulier & Zignago)         -- another reconciliation

The two raw reports BRACKET the concentration; the two reconciliations sit inside. No column is
'truth'. This makes the uncertainty explicit instead of ontologising one blend as real.

Run: python build_recon_envelope.py   ->  writes out/recon_envelope.json
"""
import os, csv, json, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))

# code -> material name (from crosswalk title_code)
XW = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))
CODE2NAME = {}
for name, e in XW.items():
    if e.get('title_code'):
        CODE2NAME.setdefault(e['title_code'], name)

# Comtrade M49 -> ISO3 (same table reconcile.py uses)
M49 = {}
with open(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        try:
            M49[int(r['country_code'])] = r['country_iso3']
        except (ValueError, KeyError):
            continue

def fold(c):
    return '811292' if c == '811231' else c

def raw_views(year):
    """exporter-only and importer-only exporter-value-by-commodity from raw Comtrade."""
    exp = defaultdict(lambda: defaultdict(float))  # X: value by (cmd, exporter=reporter)
    imp = defaultdict(lambda: defaultdict(float))  # M: value by (cmd, exporter=partner)
    p = os.path.join(ROOT, 'raw', 'comtrade', f'comtrade_{year}.csv')
    with open(p, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try:
                v = float(r['value'])
                if v <= 0:
                    continue
                rep, par = int(r['reporter']), int(r['partner'])
            except (ValueError, KeyError):
                continue
            if rep == par or rep not in M49 or par not in M49:
                continue
            c = fold(str(r['cmd']).zfill(6))
            if r['flow'] == 'X':
                exp[c][M49[rep]] += v          # reporter is the exporter
            elif r['flow'] == 'M':
                imp[c][M49[par]] += v          # partner is the exporter
    return exp, imp

def load_csv(fn):
    e = defaultdict(lambda: defaultdict(float))
    with open(os.path.join(ROOT, 'reconcile', fn), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try:
                e[r['cmd']][r['i']] += float(r['value'])
            except (ValueError, KeyError):
                continue
    return e

def hhi(d):
    t = sum(d.values())
    return sum((v / t) ** 2 for v in d.values()) if t else None

def lead(d):
    t = sum(d.values())
    return (max(d, key=d.get) if t else None)

YEARS = ['2022', '2024']
materials = {}
summary = {}
for yr in YEARS:
    exp, imp = raw_views(yr)
    eng = load_csv(f'recon_{yr}.csv')
    bac = load_csv(f'baci_{yr}.csv')
    codes = set(eng) & set(bac)          # commodities the atlas tracks and BACI has
    widths, eng_in, bac_in = [], 0, 0
    for c in sorted(codes):
        views = {'exporter_only': exp.get(c, {}), 'importer_only': imp.get(c, {}),
                 'engine': eng.get(c, {}), 'baci': bac.get(c, {})}
        hh = {k: (round(hhi(v), 3) if v else None) for k, v in views.items()}
        ld = {k: lead(v) for k, v in views.items()}
        raw_vals = [hh['exporter_only'], hh['importer_only']]
        raw_vals = [x for x in raw_vals if x is not None]
        rec_vals = [x for x in (hh['engine'], hh['baci']) if x is not None]
        env = None
        if raw_vals and rec_vals:
            lo, hi = min(raw_vals), max(raw_vals)
            env = round(hi - lo, 3)
            widths.append(env)
            eng_in += (lo - 1e-9 <= hh['engine'] <= hi + 1e-9)
            bac_in += (lo - 1e-9 <= hh['baci'] <= hi + 1e-9)
        m = materials.setdefault(c, {'code': c, 'name': CODE2NAME.get(c, c)})
        m[yr] = {'hhi': hh, 'leader': ld, 'raw_envelope_width': env,
                 'leader_agree_all4': len(set(v for v in ld.values() if v)) == 1}
    summary[yr] = {
        'n_commodities': len(widths),
        'median_raw_envelope_width': round(statistics.median(widths), 3) if widths else None,
        'max_raw_envelope_width': round(max(widths), 3) if widths else None,
        'engine_inside_raw_bracket': eng_in,
        'baci_inside_raw_bracket': bac_in,
    }

out = {
    'note': ('Four views of export concentration per commodity. exporter_only (X/FOB) and importer_only '
             '(M/CIF) are the two RAW mirror reports and bracket the truth; engine and baci are two '
             'reconciliations that sit inside. No column is ground truth.'),
    'summary': summary,
    'materials': sorted(materials.values(), key=lambda m: m['name']),
}
json.dump(out, open(os.path.join(ROOT, 'out', 'recon_envelope.json'), 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False)

for yr in YEARS:
    s = summary[yr]
    print(f"{yr}: {s['n_commodities']} commodities | raw envelope width median "
          f"{s['median_raw_envelope_width']}, max {s['max_raw_envelope_width']} | "
          f"engine inside raw bracket {s['engine_inside_raw_bracket']}/{s['n_commodities']}, "
          f"BACI inside {s['baci_inside_raw_bracket']}/{s['n_commodities']}")
print("\n2024 — HHI four ways (exp-only / imp-only / engine / BACI), worst-bracketed first:")
rows = [m for m in materials.values() if '2024' in m and m['2024']['raw_envelope_width'] is not None]
for m in sorted(rows, key=lambda m: -m['2024']['raw_envelope_width'])[:8]:
    h = m['2024']['hhi']
    print(f"  {m['name']:12} {h['exporter_only']!s:>6} {h['importer_only']!s:>6} "
          f"{h['engine']!s:>6} {h['baci']!s:>6}   width {m['2024']['raw_envelope_width']}")
print("\nwrote out/recon_envelope.json")
