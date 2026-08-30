#!/usr/bin/env python3
"""Concentration correction (author-run adversarial audit; logged in the changelog). Audits #3 and #5
turned out to be ONE phenomenon. The reconciliation engine averages the exporter- and importer-reported
value of every flow (a mirror average). That average is not a uniform multiplicative offset: it shrinks
the DOMINANT exporter's reported value more than the tail's, so it (a) preserves the leader's identity
and rank most of the time, but (b) systematically DILUTES the leader's share and UNDERSTATES
concentration (HHI). The 'uniform offset cancels in shares' defence was therefore too strong.

This script measures the full scope across every commodity and both audited snapshot years (2022, 2024)
against official BACI, and emits the corrected concentration (the un-diluted BACI HHI / leader share) as
the authoritative value. Downstream pages that quote a trade-flow HHI should read the engine value as a
LOWER BOUND and the BACI value here as the corrected concentration; ranks and trends are unaffected
(the dilution is roughly constant year to year, so it shifts the level, not the direction).

Run: python build_hhi_correction.py   ->  writes out/hhi_correction.json
"""
import os, csv, json, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
XW = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))
CODE2NAME = {}
for name, e in XW.items():
    tc = e.get('title_code')
    if tc:
        CODE2NAME.setdefault(tc, name)

def load(fn):
    exp = defaultdict(lambda: defaultdict(float))
    for r in csv.DictReader(open(os.path.join(ROOT, 'reconcile', fn), encoding='utf-8')):
        try:
            exp[r['cmd']][r['i']] += float(r['value'])
        except (ValueError, KeyError):
            continue
    return exp

def hhi(d):
    t = sum(d.values())
    return sum((v / t) ** 2 for v in d.values()) if t else None

def lead(d):
    t = sum(d.values())
    if not t:
        return None, None
    k = max(d, key=d.get)
    return k, 100 * d[k] / t

YEARS = ['2022', '2024']
rows, summary = {}, {}
for yr in YEARS:
    R, B = load(f'recon_{yr}.csv'), load(f'baci_{yr}.csv')
    hd, ld, rank_ok, n = [], [], 0, 0
    for code in sorted(set(R) & set(B)):
        if sum(R[code].values()) <= 0 or sum(B[code].values()) <= 0:
            continue
        n += 1
        he, hb = hhi(R[code]), hhi(B[code])
        le_iso, le_sh = lead(R[code]); lb_iso, lb_sh = lead(B[code])
        same = (le_iso == lb_iso)
        rank_ok += same
        hd.append(hb - he); ld.append(lb_sh - le_sh)
        rows.setdefault(code, {'code': code, 'name': CODE2NAME.get(code, code)})[yr] = {
            'hhi_engine': round(he, 3), 'hhi_baci_corrected': round(hb, 3),
            'leader_engine': le_iso, 'leader_share_engine': round(le_sh, 1),
            'leader_baci': lb_iso, 'leader_share_baci': round(lb_sh, 1),
            'leader_preserved': same,
            'hhi_understated_by': round(hb - he, 3),
            'material_miss': abs(hb - he) >= 0.05,
        }
    summary[yr] = {
        'n_commodities': n,
        'leader_identity_preserved': rank_ok,
        'leader_identity_preserved_pct': round(100 * rank_ok / n, 1),
        'median_hhi_understatement': round(statistics.median(hd), 3),
        'mean_hhi_understatement': round(statistics.mean(hd), 3),
        'median_leader_share_dilution_pp': round(statistics.median(ld), 1),
        'n_material_hhi_miss_ge_0p05': sum(1 for x in hd if x >= 0.05),
    }

out = {
    'note': ('The engine mirror-average dilutes dominant exporters, so its trade HHI is a LOWER BOUND. '
             'hhi_baci_corrected is the un-diluted official value; leader identity and trend are preserved.'),
    'summary': summary,
    'materials': sorted(rows.values(), key=lambda r: r['name']),
}
json.dump(out, open(os.path.join(ROOT, 'out', 'hhi_correction.json'), 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False)

# console report
for yr in YEARS:
    s = summary[yr]
    print(f"{yr}: {s['n_commodities']} commodities | leader identity kept "
          f"{s['leader_identity_preserved']}/{s['n_commodities']} ({s['leader_identity_preserved_pct']}%) | "
          f"median HHI understated {s['median_hhi_understatement']:+.3f}, leader diluted "
          f"{s['median_leader_share_dilution_pp']:+.1f}pp | miss>=0.05: {s['n_material_hhi_miss_ge_0p05']}")
print("\nWorst 2024 concentration understatements (engine -> corrected BACI):")
worst = sorted((r for r in rows.values() if '2024' in r), key=lambda r: -r['2024']['hhi_understated_by'])[:8]
for r in worst:
    d = r['2024']
    print(f"  {r['name']:14} ({r['code']}): {d['hhi_engine']:.2f} -> {d['hhi_baci_corrected']:.2f} "
          f"(+{d['hhi_understated_by']:.2f}), leader {d['leader_baci']} "
          f"{d['leader_share_engine']:.0f}%->{d['leader_share_baci']:.0f}%")
print("\nwrote out/hhi_correction.json")
