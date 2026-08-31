#!/usr/bin/env python3
"""Per-commodity status table (author-run; answers the round-three 'over-caveated, findings buried'
critique). Three rounds of review scattered caveats across the site: BACI-not-truth, engine-understates-
thin-codes, the mirror-report spread, cobalt's engine miss, the thinness screen. A reader can no longer
tell which commodities carry a robust concentration/trend number and which don't. This fuses the checks
into ONE classification per commodity, so the headline can state only what is robust.

Concentration status (worst-applicable wins):
  thin-fragile     - flagged by build_thinness_screen (thin market / few exporters / high top-1 leverage)
  engine-understated - the engine's HHI runs far below BACI in some year (max |BACI-engine| >= 0.15 over
                     2002-2024): the reconciliation shrank a dominant, weakly-corroborated exporter (cobalt)
  spread-sensitive - 2024 engine-vs-BACI HHI gap >= 0.05 (real but milder disagreement)
  robust           - none of the above
Trend status (from build_trend_robustness, Hamed-Rao + BH-FDR):
  unreliable (if concentration is thin-fragile or engine-understated), else significant rising/falling
  (engine & BACI agree), no significant trend, or borderline.

Run: python build_commodity_status.py   ->  out/commodity_status.json  (+ prints an HTML <tbody>)
Needs: out/thinness_screen.json, out/trend_robustness.json, out/trend_series.json, out/crosswalk.json
"""
import os, json

ROOT = os.path.dirname(os.path.abspath(__file__))
L = lambda f: json.load(open(os.path.join(ROOT, 'out', f), encoding='utf-8'))
XW = L('crosswalk.json')
NAME2CODE = {n: e['title_code'] for n, e in XW.items() if e.get('title_code')}

thin = {r['name']: r for r in L('thinness_screen.json')['materials']}
trend = {r['name']: r for r in L('trend_robustness.json')['materials']}
series = L('trend_series.json')
# codes shared by more than one tracked material (e.g. gallium/germanium/hafnium share HS 811292):
# their concentration cannot be separated, so they are neither robust nor fragile -- they are shared-code.
from collections import Counter
_codecount = Counter(c for c in NAME2CODE.values())
SHARED = {n for n, c in NAME2CODE.items() if _codecount[c] > 1}

def max_engine_gap(code):
    e = series['engine'].get(code, {}); b = series['baci'].get(code, {})
    gaps = [abs(b[y] - e[y]) for y in set(e) & set(b)]
    return max(gaps) if gaps else None

rows = []
for name in sorted(set(thin) | set(trend)):
    code = NAME2CODE.get(name)
    t = thin.get(name, {})
    gap = max_engine_gap(code) if code else None
    # concentration status
    if name in SHARED or (not t and not code):
        cstat, why = 'shared-code', 'shares its HS6 with another material; not separable in trade'
    elif not t:
        cstat, why = 'shared-code', 'no separable trade series'
    elif t.get('thin_fragile'):
        cstat, why = 'thin-fragile', ', '.join(t.get('reasons', []))
    elif gap is not None and gap >= 0.15:
        cstat, why = 'engine-understated', f'engine HHI up to {gap:.2f} below BACI in some year'
    elif gap is not None and 0.05 <= gap < 0.15:
        cstat, why = 'spread-sensitive', f'max engine-BACI HHI gap {gap:.2f}'
    else:
        cstat, why = 'robust', ''
    if t.get('single_supplier_dominated') and cstat in ('robust', 'spread-sensitive'):
        why = (why + '; ' if why else '') + 'single-country dominated (a finding, not a flag)'
    # trend status
    tr = trend.get(name)
    if cstat in ('thin-fragile', 'engine-understated', 'shared-code'):
        tstat = 'unreliable'
    elif tr:
        es, bs = tr['engine'], tr['baci']
        if es['sig'] and bs['sig'] and es['sign05'] == bs['sign05']:
            tstat = f"significant {es['dir']}"
        elif not es['sig'] and not bs['sig']:
            tstat = 'no significant trend'
        else:
            tstat = 'borderline'
    else:
        tstat = 'n/a'
    rows.append({'name': name, 'code': code,
                 'trade_value_musd': t.get('trade_value_musd'), 'n_exporters': t.get('n_exporters'),
                 'concentration_status': cstat, 'concentration_note': why,
                 'trend_status': tstat})

ORD = {'robust': 0, 'spread-sensitive': 1, 'shared-code': 2, 'thin-fragile': 3, 'engine-understated': 4}
rows.sort(key=lambda r: (ORD.get(r['concentration_status'], 9), -(r['trade_value_musd'] or 0)))
from collections import Counter
tally = Counter(r['concentration_status'] for r in rows)
out = {'note': ('One status per commodity, fusing the thinness screen, the engine-vs-BACI concentration '
                'spread, and the trend-robustness test. Headline findings should be drawn from '
                '"robust" rows; the rest are indicative.'),
       'tally': dict(tally), 'materials': rows}
json.dump(out, open(os.path.join(ROOT, 'out', 'commodity_status.json'), 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False)

print('tally:', dict(tally))
print(f"\n{'name':13}{'$M':>9}{'concentration':>20}  trend")
for r in rows:
    print(f"{r['name'][:12]:13}{(r['trade_value_musd'] or 0):9.0f}{r['concentration_status']:>20}  {r['trend_status']}")

# HTML tbody for pasting into methodology.html
BADGE = {'robust': '#1f7a4d', 'spread-sensitive': '#b8860b', 'shared-code': '#5566aa', 'thin-fragile': '#a0416a', 'engine-understated': '#8a1c1c'}
frag = []
for r in rows:
    c = BADGE.get(r['concentration_status'], '#666')
    val = f"${r['trade_value_musd']:.0f}M" if r['trade_value_musd'] else '&mdash;'
    frag.append(f'<tr><td>{r["name"]}</td><td class="n">{val}</td>'
                f'<td><b style="color:{c}">{r["concentration_status"]}</b>'
                f'{(" &middot; " + r["concentration_note"]) if r["concentration_note"] else ""}</td>'
                f'<td>{r["trend_status"]}</td></tr>')
open(os.path.join(ROOT, 'out', 'commodity_status_tbody.html'), 'w', encoding='utf-8').write('\n'.join(frag))
print('\nwrote out/commodity_status.json and out/commodity_status_tbody.html')
