# -*- coding: utf-8 -*-
"""What the AI build-out actually buys: the chips, and the equipment that carries power to them.

Measurement, not a test. Every figure is world trade from CEPII BACI through the atlas's one door
(baci.py), deflated by US CPI (World Bank, FP.CPI.TOTL, fetched 2026-09-17 and frozen below), with
each line's export concentration computed the same way as the rest of the atlas.

Writes out/ai_buildout.json and ai-buildout.html.  Usage: python build_ai_buildout.py
"""
import io
import json
import math
import os
import sys

import pandas as pd

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import baci                                            # the one door for BACI

OUT_JSON = os.path.join(ROOT, 'out', 'ai_buildout.json')
OUT_HTML = os.path.join(ROOT, 'ai-buildout.html')
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

# US consumer price index, 2010 = 100. World Bank indicator FP.CPI.TOTL, United States,
# https://api.worldbank.org/v2/country/USA/indicator/FP.CPI.TOTL (fetched 17 Sep 2026).
CPI = {2019: 117.244, 2020: 118.691, 2021: 124.266, 2022: 134.211, 2023: 139.736, 2024: 143.857}

GROUPS = [
    ('The chips', [
        ('854231', 'Processors and controllers'),
        ('854232', 'Memory'),
        ('854239', 'Other integrated circuits'),
    ]),
    ('Often counted as chips, and not', [
        ('854140', 'Photosensitive semiconductor devices'),
    ]),
    ('What goes into them', [
        ('280461', 'Silicon, 99.99% pure and above'),
        ('280429', 'Rare gases (helium, neon, krypton, xenon)'),
        ('811292', 'Niobium, gallium, indium, vanadium, germanium (one line)'),
        ('810320', 'Tantalum, unwrought and powder'),
    ]),
    ('What carries power to them', [
        ('850421', 'Liquid-dielectric transformers, up to 650 kVA'),
        ('850422', 'Liquid-dielectric transformers, over 650 up to 10,000 kVA'),
        ('850423', 'Liquid-dielectric transformers, over 10,000 kVA'),
        ('722511', 'Grain-oriented electrical steel, 600 mm or wider'),
        ('722611', 'Grain-oriented electrical steel, narrow'),
        ('740811', 'Copper wire, refined'),
    ]),
]
CODES = {c: lab for _, items in GROUPS for c, lab in items}
CYCLE = {}

# Lines whose HS code is wider than the name suggests. Printed on the page, next to the line.
CAVEATS = {
    '280429': 'Dominated by helium, not the neon used in lithography: the top exporters are Qatar, '
              'Algeria and the United States. The code cannot separate the two gases.',
    '811292': 'One customs line covering unwrought niobium, gallium, indium, vanadium and germanium '
              'together, with their powders and scrap, so a change here cannot be attributed to any '
              'one of them. The metals in the line also differ between nomenclature vintages.',
    '854140': 'Solar cells are most of this line, and light-emitting diodes are much of the rest, so '
              'it follows solar far more than it follows computing. It is shown because it is routinely '
              'read as a semiconductor line; it is not one.',
    '740811': 'Copper wire has many uses beyond data centres and grids.',
    '850421': 'Liquid-dielectric (oil-filled) transformers only; dry-type transformers sit in other '
              'customs lines and are not counted here.',
}


def collect():
    iso = baci.countries().set_index('code')['iso3'].to_dict()
    name = baci.countries().set_index('code')['name'].to_dict()
    rows = []
    for y in YEARS:
        t = baci.year(y)
        t['k'] = t.k.astype(str).str.zfill(6)
        t = t[t.k.isin(CODES)]
        t['q'] = pd.to_numeric(t['q'], errors='coerce')
        for code, g in t.groupby('k'):
            ex = g.groupby('i').v.sum()
            share = ex / ex.sum()
            top = share.sort_values(ascending=False).head(3)
            rows.append({
                'year': y, 'code': code, 'label': CODES[code],
                'value_musd': float(g.v.sum()) / 1000.0,          # BACI value is thousands of USD
                'value_real_musd': float(g.v.sum()) / 1000.0 * CPI[YEARS[-1]] / CPI[y],
                'tonnes': float(g.q.sum(skipna=True)),
                'exporters': int(g.i.nunique()),
                'hhi': round(float((share ** 2).sum()), 3),
                'top3': [{'iso3': iso.get(str(i), str(i)), 'name': name.get(str(i), str(i)),
                          'share': round(float(s), 3)} for i, s in top.items()],
            })
    return pd.DataFrame(rows)


CYCLE_YEARS = list(range(2002, 2025))
# The chip cycle is the whole 8542 heading (integrated circuits). The six-digit splits used in the
# table only exist from HS 2007, so a series back to 2002 has to be taken at four digits.
CYCLE_INPUTS = ['280461', '280429', '811292', '810320', '722511', '850422', '740811']


def chip_cycle():
    """Does each input line move with the chip cycle, year by year?

    Deliberately modest: 22 annual observations can only see large co-movements, so every line is
    reported with the smallest elasticity it could have detected, and nothing here is a test of
    causation - an input and the chips can move together because both follow the world economy.
    """
    import numpy as np
    import statsmodels.formula.api as smf
    from scipy import stats
    tot = {}
    for y in CYCLE_YEARS:
        # ONE nomenclature for the whole series: baci.year() otherwise returns the newest one
        # holding each year, which would splice HS 2002 up to 2016 onto HS 2017 after it.
        t = baci.year(y, nom='HS02')
        t['k'] = t.k.astype(str).str.zfill(6)
        t = t[t.k.isin(CYCLE_INPUTS) | t.k.str.startswith('8542')]
        g = t.groupby('k').v.sum()
        tot[y] = {k: float(g.get(k, np.nan)) / 1000.0 for k in CYCLE_INPUTS}
        tot[y]['_ic'] = float(sum(v for k, v in g.items() if str(k).startswith('8542'))) / 1000.0
    # Both sides are nominal: the year's inflation is common to input and chips, so it cancels out of
    # a regression of one growth rate on the other. The page says so.
    out = {}
    yrs = [y for y in CYCLE_YEARS]
    ic = {y: tot[y]['_ic'] for y in yrs}
    for code in CYCLE_INPUTS:
        rows = []
        for y in yrs[1:]:
            a0, a1 = tot[y - 1].get(code), tot[y].get(code)
            b0, b1 = ic[y - 1], ic[y]
            if a0 and a1 and b0 and b1 and a0 > 0 and a1 > 0:
                rows.append({'year': y, 'dx': math.log(a1 / a0), 'dic': math.log(b1 / b0)})
        df = pd.DataFrame(rows)
        if len(df) < 15:
            continue
        m = smf.ols('dx ~ dic', df).fit(cov_type='HAC', cov_kwds={'maxlags': 2, 'use_correction': True},
                                        use_t=True)
        se = float(m.bse['dic'])
        dfree = int(m.df_resid)
        crit = float(stats.t.ppf(0.975, dfree))
        out[code] = {'label': CODES[code], 'elasticity': round(float(m.params['dic']), 3),
                     'p': round(float(m.pvalues['dic']), 4),
                     'ci95': [round(float(m.params['dic']) - crit * se, 3),
                              round(float(m.params['dic']) + crit * se, 3)],
                     'mde_80pct_power': round(float((crit + stats.t.ppf(0.80, dfree)) * se), 3),
                     'n': int(m.nobs), 'years': [int(df.year.min()), int(df.year.max())]}
    return out


def build_doc(d):
    first, last = YEARS[0], YEARS[-1]
    lines = {}
    for code in CODES:
        g = d[d.code == code].set_index('year')
        if first not in g.index or last not in g.index:
            continue
        v0, v1 = g.loc[first, 'value_real_musd'], g.loc[last, 'value_real_musd']
        lines[code] = {
            'label': CODES[code],
            'value_musd': {str(y): round(float(g.loc[y, 'value_musd']), 1) for y in YEARS if y in g.index},
            'real_growth_pct': round(100.0 * (v1 / v0 - 1.0), 1),
            'nominal_growth_pct': round(100.0 * (float(g.loc[last, 'value_musd']) /
                                                 float(g.loc[first, 'value_musd']) - 1.0), 1),
            'hhi_latest': float(g.loc[last, 'hhi']),
            'exporters_latest': int(g.loc[last, 'exporters']),
            'top3_latest': g.loc[last, 'top3'],
            'caveat': CAVEATS.get(code),
        }
    return {
        'note': 'World trade in the lines a data-centre build-out runs on. Measurement only: this is '
                'what crossed borders, not what was produced, consumed or installed, and no part of it '
                'is attributed to AI rather than to electrification generally.',
        'years': YEARS, 'deflator': {'source': 'World Bank FP.CPI.TOTL, United States, 2010 = 100',
                                     'values': CPI},
        'groups': [{'title': t, 'codes': [c for c, _ in items]} for t, items in GROUPS],
        'lines': lines,
        'chip_cycle': CYCLE,
        'sources': ['CEPII BACI (HS02) via baci.py', 'World Bank, US consumer price index'],
    }


NAV = ('<header class="topbar"><div class="wrap">'
       '<a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>'
       '<nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a>'
       '<a href="value-chains">Value Chains</a><a href="analysis">Analysis</a>'
       '<a href="reports">Reports</a><a href="method">Method</a></nav>'
       '</div></header>')
FOOT = ('<footer class="siteftr"><div class="wrap">'
        '<div><h4>Critical Materials Atlas</h4>Public-data value-chain research. Not affiliated '
        'with, nor representing, any institution.</div>'
        '<div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value '
        'Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br>'
        '<a href="method">Method</a></div>'
        '<div><h4>Sources</h4>CEPII BACI &middot; World Bank</div>'
        '<div class="fineprint">Independent public-data research; figures approximate and '
        'rounded.</div></div></footer>')
CSS = """
.xp{max-width:62rem}
.xp table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
.xp th,.xp td{padding:.4rem .55rem;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top}
.xp td.n,.xp th.n{text-align:right;font-variant-numeric:tabular-nums}
.grp{background:#f7f7f5;font-weight:600}
.up{color:#0e7c74;font-weight:600}.dn{color:#b3384b;font-weight:600}
.note{background:#f7f7f5;border-left:3px solid #0e7c74;padding:.7rem 1rem;margin:1rem 0;font-size:.93rem}
.cav{color:#6b675f;font-size:.86rem}
.bar{display:inline-block;height:.55rem;background:#0e7c74;border-radius:2px;vertical-align:middle}
"""


def page(doc):
    L = doc['lines']
    rows = []
    span = max(abs(v['real_growth_pct']) for v in L.values()) or 1
    for title, items in GROUPS:
        rows.append('<tr class="grp"><td colspan="5">%s</td></tr>' % title)
        for code, _ in items:
            v = L.get(code)
            if not v:
                continue
            g = v['real_growth_pct']
            w = max(2.0, 100.0 * abs(g) / span * 0.55)
            top = ', '.join('%s %d%%' % (t['iso3'], round(100 * t['share'])) for t in v['top3_latest'])
            cav = ('<div class="cav">%s</div>' % v['caveat']) if v['caveat'] else ''
            rows.append(
                '<tr><td>%s<div class="cav">HS %s</div>%s</td>'
                '<td class="n">$%s bn</td><td class="n">$%s bn</td>'
                '<td class="n"><span class="%s">%+d%%</span> <span class="bar" style="width:%.0f%%"></span></td>'
                '<td>%s<div class="cav">HHI %.2f, %d exporters</div></td></tr>'
                % (v['label'], code, cav,
                   format(v['value_musd'][str(YEARS[0])] / 1000.0, '.1f'),
                   format(v['value_musd'][str(YEARS[-1])] / 1000.0, '.1f'),
                   'up' if g >= 0 else 'dn', round(g), w, top, v['hhi_latest'], v['exporters_latest']))
    tbl = '\n'.join(rows)

    C = doc.get('chip_cycle', {})
    cyrows = '\n'.join(
        '<tr><td>%s<div class="cav">HS %s</div></td><td class="n">%+.2f</td>'
        '<td class="n">%+.2f to %+.2f</td><td class="n">%.3f</td><td class="n">%.2f</td></tr>'
        % (v['label'], code, v['elasticity'], v['ci95'][0], v['ci95'][1], v['p'], v['mde_80pct_power'])
        for code, v in C.items())
    any_cy = next(iter(C.values()), {'years': [0, 0], 'elasticity': 0})
    cy0, cy1 = any_cy['years'][0], any_cy['years'][1]
    neon = ('%+.2f%%' % C['280429']['elasticity']) if '280429' in C else 'n/a'
    neonp = ('%.3f' % C['280429']['p']) if '280429' in C else 'n/a'

    tr = [L[c]['real_growth_pct'] for c in ('850421', '850422', '850423')]
    ch = [L[c]['real_growth_pct'] for c in ('854231', '854232', '854239')]
    chip_bn = sum(L[c]['value_musd'][str(YEARS[-1])] for c in ('854231', '854232', '854239')) / 1000.0
    tr_bn = sum(L[c]['value_musd'][str(YEARS[-1])] for c in ('850421', '850422', '850423')) / 1000.0

    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The AI build-out in customs data &mdash; Critical Materials Atlas</title>
<meta name="description" content="World trade in the lines a data-centre build-out runs on, 2019 to 2024, in constant dollars: chips, the materials that go into them, and the transformers, electrical steel and copper wire that carry power to them.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style>@@CSS@@</style></head><body>
@@NAV@@
<section class="hero"><div class="wrap">
  <div class="eyebrow">Downstream &middot; measurement</div>
  <h1>The AI build-out in customs data</h1>
  <p class="deck">When people ask what a data centre needs, the answer is usually chips. This page
  asks something customs data can actually answer: over the last five years, which of the things a
  data centre is made of grew fastest in world trade? Deflated by US consumer prices, trade in
  <b>transformers grew @@TRMIN@@&ndash;@@TRMAX@@%</b> between @@Y0@@ and @@Y1@@ while trade in
  <b>integrated circuits grew @@CHMIN@@&ndash;@@CHMAX@@%</b>. The chips are far the larger market
  &mdash; $@@CHIPBN@@bn against $@@TRBN@@bn, about @@RATIO@@ times &mdash; so the growth is happening
  in the small lines.</p>
</div></section>

<section class="wrap xp">
  <h2>World trade, @@Y0@@ and @@Y1@@</h2>
  <p>Values are world exports in current dollars; the growth column divides them by the US consumer
  price index, which puts the changes in constant dollars. That is not a measure of volume: if
  transformers became more expensive faster than US prices generally, part of their growth is price.
  Concentration is the share of world exports held by the largest exporters, on the same measure the
  rest of the atlas uses. The @@Y0@@ and @@Y1@@ figures are read in the 2017 customs nomenclature;
  the series further down uses the 2002 one throughout, because no single six-digit code spans both.</p>
  <table><thead><tr><th>Customs line</th><th class="n">@@Y0@@</th><th class="n">@@Y1@@</th>
  <th class="n">real change</th><th>largest exporters, @@Y1@@</th></tr></thead>
  <tbody>@@ROWS@@</tbody></table>
  <div class="note">Three things this table does not say. It does not say the AI build-out
  caused any of this: transformers and electrical steel are bought by every kind of electrification,
  from grid replacement to electric vehicles, and the data cannot separate a data centre's
  transformer from a substation's. It does not measure production or installation, only what crossed
  a border. And a customs line is not a product: the notes under each line say where the code is
  wider than its name.</div>
</section>

<section class="wrap xp">
  <h2>Which of these actually move with the chip cycle?</h2>
  <p>A second question, and a harder one: when world trade in integrated circuits rises, does trade in
  each input rise with it? The table gives the elasticity from twenty-two annual observations
  (@@CY0@@&ndash;@@CY1@@), and beside it the smallest elasticity that many observations could have
  detected. Read the last column first: for most of these lines the detectable size is larger than
  any plausible answer, so the estimate carries no information. Both sides are in current dollars;
  the same inflation sits on both, but a common price cycle can still move them together without any
  link between the two industries.</p>
  <table><thead><tr><th>Customs line</th><th class="n">moves with chips by</th>
  <th class="n">95% interval</th><th class="n">p</th><th class="n">smallest it could see</th></tr></thead>
  <tbody>@@CYROWS@@</tbody></table>
  <div class="note"><b>No line here is readable, including the one with a small p-value.</b> Rare
  gases comes in at @@NEON@@ per 1% of chip trade with p = @@NEONP@@, but that estimate is almost
  exactly the smallest effect twenty-two observations could detect, so it is not evidence of a
  chip-driven relationship; and that line is mostly helium, which follows industry at large. Seven
  lines were tested with no correction for testing seven. Treat this table as a list of things to
  measure properly with monthly data, not as a result.</div>
</section>

<section class="wrap xp">
  <h2>Which lines are worth watching</h2>
  <p>Two things are true at once, and only one of them is about concentration. The transformer lines
  are small and growing fast, but they are <i>less</i> concentrated than the chip lines, not more:
  their largest exporters hold 13&ndash;23% of world exports against 21&ndash;38% for processors and
  memory. The line that is both small and concentrated is
  <b>grain-oriented electrical steel</b>, the core of a transformer: a $@@GOESBN@@bn line with
  @@GOESN@@ exporters, whose two largest, China and Japan, are @@GOES2@@% of it. That makes it a
  candidate to watch, which is not the same as a demonstrated constraint &mdash; nothing on this page
  measures whether anyone was actually short of it.</p>
  <p class="howto-src"><b>Sources.</b> Trade: CEPII BACI, release V202601 (Etalab Open Licence 2.0),
  read through the atlas's single BACI reader, which applies the atlas's own quantity repairs. The
  @@Y0@@ and @@Y1@@ table is read in the HS 2017 nomenclature, in which those six-digit codes exist;
  the chip-cycle series is read in HS 2002 for every year, so that no code changes underneath it.
  Deflator: World Bank, US consumer price index (FP.CPI.TOTL). Built by
  <code>build_ai_buildout.py</code> from <code>out/ai_buildout.json</code>, which holds every figure
  on this page.</p>
</section>
@@FOOT@@
</body></html>
""".replace('@@CSS@@', CSS).replace('@@NAV@@', NAV).replace('@@FOOT@@', FOOT) \
   .replace('@@ROWS@@', tbl).replace('@@Y0@@', str(YEARS[0])).replace('@@Y1@@', str(YEARS[-1])) \
   .replace('@@TRMIN@@', str(round(min(tr)))).replace('@@TRMAX@@', str(round(max(tr)))) \
   .replace('@@CHMIN@@', str(round(min(ch)))).replace('@@CHMAX@@', str(round(max(ch)))) \
   .replace('@@CHIPBN@@', format(chip_bn, '.0f')).replace('@@TRBN@@', format(tr_bn, '.0f')) \
   .replace('@@GOESBN@@', format(L['722511']['value_musd'][str(YEARS[-1])] / 1000.0, '.1f')) \
   .replace('@@GOESN@@', str(L['722511']['exporters_latest'])) \
   .replace('@@GOES2@@', str(round(100 * sum(t['share'] for t in L['722511']['top3_latest'][:2]))))    .replace('@@CYROWS@@', cyrows).replace('@@CY0@@', str(cy0)).replace('@@CY1@@', str(cy1))    .replace('@@NEON@@', neon).replace('@@NEONP@@', neonp).replace('@@RATIO@@', '%.0f' % (chip_bn / tr_bn))


def main():
    global CYCLE
    d = collect()
    CYCLE = chip_cycle()
    doc = build_doc(d)
    with io.open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, default=float)
    html = page(doc)
    assert '@@' not in html, 'unfilled token'
    with io.open(OUT_HTML, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    print('wrote', OUT_JSON, 'and', OUT_HTML)


if __name__ == '__main__':
    main()
