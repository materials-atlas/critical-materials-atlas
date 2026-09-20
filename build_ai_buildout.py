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
# The research note's figures for grain-oriented electrical steel, both customs lines together.
# Read, not recomputed, so the two pages cannot disagree.
STUDY_JSON = os.path.join(ROOT, 'out', 'buildout_study.json')
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
    ('Other electrical machinery, for comparison', [
        ('850152', 'AC motors, multi-phase, 750 W to 75 kW'),
        ('850153', 'AC motors, multi-phase, over 75 kW'),
        ('841370', 'Centrifugal pumps for liquids'),
        ('841480', 'Other air and gas pumps and compressors'),
    ]),
    ('What a new chip factory buys', [
        ('848620', 'Machines for making semiconductor devices and integrated circuits'),
        ('848610', 'Machines for making boules and wafers'),
        ('848690', 'Parts of chip- and wafer-making machines'),
        ('381800', 'Wafers: chemical elements doped for electronics'),
        ('370790', 'Photographic chemical preparations, including photoresists'),
        ('903082', 'Instruments for testing semiconductor wafers and devices'),
    ]),
]
CODES = {c: lab for _, items in GROUPS for c, lab in items}
CYCLE = {}
NAMES = {'NLD': 'the Netherlands', 'JPN': 'Japan', 'SGP': 'Singapore', 'USA': 'the United States',
         'KOR': 'South Korea', 'TWN': 'Taiwan', 'CHN': 'China', 'DEU': 'Germany', 'MYS': 'Malaysia'}

# Lines whose HS code is wider than the name suggests. Printed on the page, next to the line.
CAVEATS = {
    '280429': 'Dominated by helium, not the neon used in lithography: the top exporters are Qatar, '
              'Algeria and the United States. At six digits the code cannot separate the two gases; '
              'the US record can, at ten (below).',
    '811292': 'One customs line covering unwrought niobium, gallium, indium, vanadium and germanium '
              'together, with their powders and scrap, so a change here cannot be attributed to any '
              'one of them. The metals in the line also differ between nomenclature vintages.',
    '854140': 'Solar cells are most of this line, and light-emitting diodes are much of the rest, so '
              'it follows solar far more than it follows computing. It is shown because it is routinely '
              'read as a semiconductor line; it is not one.',
    '740811': 'Copper wire has many uses beyond data centres and grids.',
    '850152': 'Electrical goods bought by the same electrification; the research note uses these '
              'four lines as a robustness comparison for transformers.',
    '850421': 'Liquid-dielectric (oil-filled) transformers only; dry-type transformers sit in other '
              'customs lines and are not counted here.',
    '848620': 'Lithography, etching and deposition tools are all inside this one line; customs data '
              'cannot separate them. Singapore is partly a regional hub, so some of its share is '
              'equipment made elsewhere and shipped on.',
    '370790': 'US Customs classifies photoresists here (ruling HQ 085914), but the line also holds '
              'other chemical preparations for photographic uses, so not all of it is photoresist.',
    '381800': 'Mostly silicon wafers, but any doped element or compound in wafer or disc form counts.',
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
.refs{max-width:46rem;padding-left:1.1rem}.refs li{margin:.45rem 0;font-size:.9rem;line-height:1.55}
.fig .hdot{stroke:#fcfcfb;stroke-width:2}.fig .hdot.pw{fill:#009287}.fig .hdot.ch{fill:#7d5ba6}
.fig .lbl{font-size:11px}.fig .lbl.pw{fill:#00695f}.fig .lbl.ch{fill:#5b4080}
.src{font-size:.78rem;color:#6b675f;margin:.2rem 0 1rem}.src code{font-size:.74rem}
.tbl{overflow-x:auto}.tbl table{min-width:46rem}
.xp th.grph{text-align:center;border-bottom:2px solid #0e7c74}
.fig{margin:1.3rem 0}.fig svg{width:100%;height:auto;display:block}
.fig figcaption{font-size:.86rem;color:#5a6468;margin-top:.45rem;max-width:44rem}
.fig .grid{stroke:#e3e6e5;stroke-width:1}.fig .zero{stroke:#8b9396;stroke-width:1}
.fig .rowline{stroke:#eff1f0;stroke-width:1}
.fig .ax{font:11px Inter,system-ui,sans-serif;fill:#5a6468}
.fig .ax.row{font-size:12px;fill:#15323a}.fig .ax.grp{font-size:11px;font-weight:700;fill:#0e7c74;letter-spacing:.04em}
.fig .dot{stroke:#fcfcfb;stroke-width:2}
.bar{display:inline-block;height:.55rem;background:#0e7c74;border-radius:2px;vertical-align:middle}
"""


EXT_JSON = os.path.join(ROOT, 'out', 'ai_buildout_ext.json')     # ai-buildout/extend.py
EXT_KEY = {'854140': '85414'}          # HS 2022 split 8541.40 into 8541.41-.49; kept together
CT_JSON = os.path.join(ROOT, 'out', 'ai_buildout_comtrade.json')   # ai-buildout/comtrade_extend.py


# Short row labels for the charts: the table carries the full name and the code.
SHORT = {
    '854231': 'Processors and controllers', '854232': 'Memory', '854239': 'Other integrated circuits',
    '854140': 'Photosensitive devices and LEDs', '280461': 'Silicon, 99.99% and purer',
    '280429': 'Rare gases (mostly helium)', '811292': 'Gallium, germanium, niobium line',
    '810320': 'Tantalum', '850421': 'Transformers, up to 650 kVA',
    '850422': 'Transformers, 650 to 10,000 kVA', '850423': 'Transformers, over 10,000 kVA',
    '722511': 'Electrical steel, wide', '722611': 'Electrical steel, narrow',
    '740811': 'Copper wire', '850152': 'AC motors, 0.75 to 75 kW', '850153': 'AC motors, over 75 kW',
    '841370': 'Centrifugal pumps', '841480': 'Other pumps and compressors',
    '848620': 'Chip-making machines', '848610': 'Boule and wafer machines',
    '848690': 'Parts of those machines', '381800': 'Doped wafers',
    '370790': 'Photoresists and photo chemicals', '903082': 'Wafer and chip test instruments',
}
POWER = {'850421', '850422', '850423', '722511', '722611', '740811'}
LABEL_IN_HERO = {'854231', '854232', '848620', '850422', '850423', '722511', '740811', '810320',
                 '280429', '370790'}


def hero_chart(L_lines):
    """Where the money is against where the growth is: one dot per customs line."""
    W, H, L, R, T, B = 720, 360, 58, 20, 30, 46
    xs = [v['value_musd']['2024'] for v in L_lines.values()]
    ys = [v['real_growth_pct'] for v in L_lines.values()]
    x0 = math.floor(math.log10(min(xs)) * 2) / 2
    x1 = math.ceil(math.log10(max(xs)) * 2) / 2
    y0 = math.floor(min(ys) / 20) * 20
    y1 = math.ceil(max(ys) / 20) * 20

    def x(v):
        return L + (math.log10(v) - x0) / (x1 - x0) * (W - L - R)

    def y(v):
        return T + (y1 - v) / (y1 - y0) * (H - T - B)
    g = []
    t = y0
    while t <= y1 + 1e-9:
        g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="%s"/>'
                 % (L, W - R, y(t), y(t), 'zero' if abs(t) < 1e-9 else 'grid'))
        g.append('<text x="%d" y="%.1f" class="ax" text-anchor="end">%s</text>'
                 % (L - 6, y(t) + 4, ('%+d%%' % t) if t else '0%'))
        t += 20
    for dec, lab in ((300.0, '$300m'), (1000.0, '$1bn'), (10000.0, '$10bn'), (100000.0, '$100bn')):
        if x0 <= math.log10(dec) <= x1:
            g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%.1f" class="grid"/>' % (x(dec), x(dec), T, y(y0)))
            g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%s</text>' % (x(dec), H - B + 18, lab))
    g.append('<text x="%d" y="%d" class="ax" text-anchor="middle">world exports in 2024 (log scale)</text>'
             % ((L + W - R) / 2, H - 10))
    placed = []
    for code, v in sorted(L_lines.items(), key=lambda kv: -kv[1]['value_musd']['2024']):
        X, Y = x(v['value_musd']['2024']), y(v['real_growth_pct'])
        cls = 'pw' if code in POWER else 'ch'
        g.append('<circle cx="%.1f" cy="%.1f" r="6" class="hdot %s"><title>%s: $%.1fbn in 2024, %+d%% since 2019</title></circle>'
                 % (X, Y, cls, SHORT[code], v['value_musd']['2024'] / 1000.0, round(v['real_growth_pct'])))
        if code in LABEL_IN_HERO:
            anchor, dx = ('end', -9) if X > W - R - 150 else ('start', 9)
            w = 6.2 * len(SHORT[code])                    # a label's width at 11px, near enough
            x_lo = (X + dx - w) if anchor == 'end' else (X + dx)
            for dy in (4, -12, 16, -24, 28):              # first slot that does not overlap one placed
                box = (x_lo, x_lo + w, Y + dy)
                if all(b[2] != box[2] or b[1] < box[0] or box[1] < b[0]
                       for b in placed if abs(b[2] - box[2]) < 12):
                    break
            placed.append(box)
            g.append('<text x="%.1f" y="%.1f" class="ax lbl %s" text-anchor="%s">%s</text>'
                     % (X + dx, Y + dy, cls, anchor, SHORT[code]))
    leg = ('<circle cx="%d" cy="%d" r="6" class="hdot pw"/><text x="%d" y="%d" class="ax">power equipment</text>'
           '<circle cx="%d" cy="%d" r="6" class="hdot ch"/><text x="%d" y="%d" class="ax">chips, their inputs, and the machines that make them</text>'
           % (L + 6, T - 14, L + 16, T - 10, L + 176, T - 14, L + 186, T - 10))
    return ('<svg viewBox="0 0 %d %d" role="img" aria-label="World exports in 2024 against growth since '
            '2019, one dot per customs line: the chip lines are the largest markets and the transformer '
            'lines the fastest-growing">%s%s</svg>' % (W, H, leg, ''.join(g)))


# Validated for colour-vision separation against the page's surface (dataviz validator, 20 Sep 2026).
SERIES = [('EU imports', 'eu', '#009287'), ('US imports', 'us', '#c2701c'),
          ('world panel', 'wd', '#7d5ba6')]


def dot_strip(rows, lo, hi, step, fmt, title, unit, W=720):
    """One row per customs line, one dot per record. Rows: (label, [(series key, value or None)])."""
    L, R, T, rh = 300, 96, 26, 20
    H = T + rh * len(rows) + 30
    colour = {k: c for _, k, c in SERIES}
    name = {k: n for n, k, _ in SERIES}

    def x(v):
        return L + (min(max(v, lo), hi) - lo) / float(hi - lo) * (W - L - R)
    g = []
    t = lo
    while t <= hi + 1e-9:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%.1f" class="%s"/>'
                 % (x(t), x(t), T - 8, H - 28, 'zero' if abs(t) < 1e-9 else 'grid'))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%s</text>' % (x(t), H - 10, fmt(t)))
        t = round(t + step, 10)
    y = T
    for label, vals in rows:
        if vals is None:                                   # a group heading
            g.append('<text x="0" y="%.1f" class="ax grp">%s</text>' % (y + 12, label))
            y += rh
            continue
        g.append('<line x1="%d" x2="%.1f" y1="%.1f" y2="%.1f" class="rowline"/>' % (L, W - R, y + 8, y + 8))
        g.append('<text x="8" y="%.1f" class="ax row">%s</text>' % (y + 12, label))
        for k, v in vals:
            if v is None:
                continue
            g.append('<circle cx="%.1f" cy="%.1f" r="5" class="dot" fill="%s"><title>%s: %s %s</title></circle>'
                     % (x(v), y + 8, colour[k], name[k], fmt(v), unit))
        y += rh
    leg = ''.join('<circle cx="%d" cy="%d" r="5" fill="%s"/><text x="%d" y="%d" class="ax">%s</text>'
                  % (L + 12 + i * 150, T - 20, c, L + 22 + i * 150, T - 16, n)
                  for i, (n, k, c) in enumerate(SERIES))
    return ('<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s%s</svg>'
            % (W, H, title, leg, ''.join(g)))


def ext_section():
    """After 2024: the page's lines in the EU's and the US's own customs records, to July 2026."""
    with io.open(EXT_JSON, encoding='utf-8') as f:
        E = json.load(f)
    eu, us = E['eu']['lines'], E['us']['lines']
    with io.open(CT_JSON, encoding='utf-8') as f:
        W = json.load(f)
    wy, wh = W['year_2025_vs_2024'], W['h1_2026_vs_h1_2025']

    def money(v, cur):
        sym = '&euro;' if cur == 'EUR' else '$'
        return '%s%.1fbn' % (sym, v / 1000.0) if v >= 1000 else '%s%.0fm' % (sym, v)

    from decimal import Decimal, ROUND_HALF_UP

    def r0(x):                                        # round once, half up: 198.52 -> 199, never 198
        return int(Decimal(str(x)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    def ch(x):
        if x is None:
            return '&ndash;'
        return '0%' if r0(x) == 0 else '%+d%%' % r0(x)

    def cn(x):
        if x is None:
            return '&ndash;'
        return ('%.1f%%' if 100 * x < 1 else '%.0f%%') % (100 * x)

    def mag(x, sign):                                 # the size of a change; its direction is in the words
        assert (x > 0) == (sign > 0), 'direction word no longer matches the data: %s' % x
        return '%d%%' % r0(abs(x))
    rows = []
    for title, items in GROUPS:
        rows.append('<tr class="grp"><td colspan="9">%s</td></tr>' % title)
        for code, lab in items:
            k = EXT_KEY.get(code, code)
            a, b = eu.get(k), us.get(k)
            if not a or not b:
                continue
            rows.append('<tr><td>%s<div class="cav">HS %s</div></td>'
                        '<td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td>'
                        '<td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td></tr>'
                        % (lab, code if k == code else '8541.41&ndash;.49',
                           money(a['value_2025_m'], 'EUR'), ch(a['change_2025_vs_2024_pct']),
                           ch(a['change_2026_vs_2025_same_months_pct']), cn(a['china_share_2025']),
                           money(b['value_2025_m'], 'USD'), ch(b['change_2025_vs_2024_pct']),
                           ch(b['change_2026_vs_2025_same_months_pct']), cn(b['china_share_2025'])))
    wrows = []
    for title, items in GROUPS:
        wrows.append('<tr class="grp"><td colspan="5">%s</td></tr>' % title)
        for code, lab in items:
            k = EXT_KEY.get(code, code)
            y, h = wy.get(k), wh.get(k)
            if not y:
                continue
            wrows.append('<tr><td>%s<div class="cav">HS %s</div></td><td class="n">%s</td>'
                         '<td class="n">%s</td><td class="n">%s</td><td class="n">%s</td></tr>'
                         % (lab, code if k == code else '8541.41&ndash;.49', ch(y['value_change_pct']),
                            ch(h['value_change_pct']) if h else '&ndash;',
                            cn(y['suppliers_b']['china']), cn(y['coverage_of_2024_world_imports'])))
    growth, share = [], []
    for title, items in GROUPS:
        growth.append((title, None))
        share.append((title, None))
        for code, lab in items:
            k = EXT_KEY.get(code, code)
            a, b, w = eu.get(k), us.get(k), wy.get(k)
            if not a or not b or not w:
                continue
            short = SHORT[code]
            growth.append((short, [('eu', a['change_2025_vs_2024_pct']), ('us', b['change_2025_vs_2024_pct']),
                                   ('wd', w['value_change_pct'])]))
            share.append((short, [('eu', 100 * a['china_share_2025'] if a['china_share_2025'] is not None else None),
                                  ('us', 100 * b['china_share_2025'] if b['china_share_2025'] is not None else None),
                                  ('wd', 100 * w['suppliers_b']['china'] if w['suppliers_b']['china'] is not None else None)]))
    gl = [v for _, vals in growth if vals for _, v in vals if v is not None]
    glo = math.floor(min(gl) / 20.0) * 20
    ghi = math.ceil(max(gl) / 20.0) * 20
    growth_svg = dot_strip(growth, glo, ghi, 20, lambda t: '%+d%%' % t if t else '0%',
                           'Change in the value of imports from 2024 to 2025, by customs line, in the '
                           'EU record, the US record and the world panel', '')
    share_svg = dot_strip(share, 0, 90, 15, lambda t: '%d%%' % t,
                          "China's share of the value of imports in 2025, by customs line, in the EU "
                          'record, the US record and the world panel', 'of import value')
    rg = E['us']['rare_gases_2025_split']
    lm = E['eu']['last_month']
    month = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
             'October', 'November', 'December'][int(lm[4:]) - 1]
    ytd = 'January&ndash;%s' % month
    t = {
        'MONTH': month, 'YTD': ytd, 'YTDS': 'Jan&ndash;%s %s' % (month[:3], lm[:4]), 'YR': lm[:4], 'ROWS': '\n'.join(rows),
        'MEMEU': mag(eu['854232']['change_2026_vs_2025_same_months_pct'], +1),
        'MEMUS': mag(us['854232']['change_2026_vs_2025_same_months_pct'], +1),
        'T23EU25': mag(eu['850423']['change_2025_vs_2024_pct'], +1),
        'T23EU26': mag(eu['850423']['change_2026_vs_2025_same_months_pct'], +1),
        'T23EUCN': cn(eu['850423']['china_share_2025']),
        'T22US25': mag(us['850422']['change_2025_vs_2024_pct'], +1), 'T23US25': mag(us['850423']['change_2025_vs_2024_pct'], +1),
        'T22USCN': cn(us['850422']['china_share_2025']), 'T23USCN': cn(us['850423']['china_share_2025']),
        'GOEU': cn(eu['722511']['china_share_2025']), 'GOUS': cn(us['722511']['china_share_2025']),
        'NEON': '%.1f%%' % (100 * rg['neon']), 'HELIUM': '%.0f%%' % (100 * rg['helium']),
        'SOLUS': mag(us['85414']['change_2025_vs_2024_pct'], -1),
        'WROWS': '\n'.join(wrows), 'GROWTHFIG': growth_svg, 'SHAREFIG': share_svg,
        'WN': str(wy['850423']['importers']),
        'WHN': str(wh['850423']['importers']),
        'WLAST': '%s-%s' % (W['last_month'][:4], W['last_month'][4:]),
        'WMEM': mag(wh['854232']['value_change_pct'], +1), 'WMEMCOV': cn(wh['854232']['coverage_of_2024_world_imports']),
    }
    html = """
<section class="wrap xp">
  <h2>After 2024: the EU and US records, to @@MONTH@@ @@YR@@</h2>
  <p>World trade in the table above ends in 2024, the last year of the newest BACI release. The EU and
  the United States publish their own customs records monthly, and those run to @@YTD@@ @@YR@@. They show
  the same lines from one side only: <b>what the EU imports from outside the EU</b>, in euros, and
  <b>what the US imports</b>, in dollars. Neither is world trade, and neither is adjusted for inflation.
  2026 is compared with the same months of 2025; the latest months are first releases and may be
  revised.</p>
  <div class="tbl"><table><thead>
  <tr><th rowspan="2">Customs line</th><th colspan="4" class="grph">EU imports from outside the EU</th>
  <th colspan="4" class="grph">US imports</th></tr>
  <tr><th class="n">2025</th><th class="n">vs 2024</th><th class="n">@@YTDS@@ vs same months 2025</th>
  <th class="n">China, 2025</th><th class="n">2025</th><th class="n">vs 2024</th>
  <th class="n">@@YTDS@@ vs same months 2025</th><th class="n">China, 2025</th></tr></thead>
  <tbody>@@ROWS@@</tbody></table></div>
  <p class="src"><b>Source:</b> <a href="https://ec.europa.eu/eurostat/api/dissemination/files?dir=comext%2FCOMEXT_DATA%2FPRODUCTS">Eurostat
  Comext, monthly bulk files (CN8)</a> &middot; <a href="https://api.census.gov/data/timeseries/intltrade/imports/hs">US
  Census Bureau, international trade API (HS10)</a>. Computed values:
  <a href="https://github.com/materials-atlas/critical-materials-atlas/blob/main/out/ai_buildout_ext.json"><code>out/ai_buildout_ext.json</code></a>.</p>
  <figure class="fig">@@GROWTHFIG@@
  <figcaption><b>What grew in 2025, in three records.</b> Change in the value of imports from 2024 to
  2025. The EU and US records are those countries' own imports; the world panel is the importers that
  filed every month of both years to UN Comtrade (see below). Current euros and dollars, so a change
  mixes price and quantity. Lines are cut off at the ends of the axis where a change runs past
  it.</figcaption></figure>
  <p>What the newer months add, line by line and without attributing any of it to AI:</p>
  <ul>
  <li><b>Memory chips.</b> In @@YTD@@ @@YR@@ the value of memory imports was up @@MEMEU@@ on the same months
  of 2025 in the EU and up @@MEMUS@@ in the US. These are values, so the records alone cannot say how much of
  that is price and how much is quantity.</li>
  <li><b>Large transformers kept rising.</b> EU imports of the largest units (over 10,000 kVA) rose
  @@T23EU25@@ in 2025 and @@T23EU26@@ in @@YTD@@ @@YR@@, and China supplied @@T23EUCN@@ of them in 2025.
  US imports of the two larger classes rose @@T22US25@@ and @@T23US25@@ in 2025, with China at @@T22USCN@@
  and @@T23USCN@@: the two markets buy from different places.</li>
  <li><b>Electrical steel.</b> China supplied @@GOEU@@ of the EU's imports of the wide line in 2025 and
  @@GOUS@@ of the US's, the same split the <a href="grid-trade">research note</a> traces. Imports are not
  supply: counting what EU mills make, China was about a quarter of the EU's electrical steel and a
  tenth of its transformers in 2024 (see the note, section 4.6b).</li>
  <li><b>Neon, in the US record.</b> The US record splits the rare-gas line at ten digits (the EU's
  splits out helium but not neon). In 2025 neon,
  the gas used in chip lithography, was @@NEON@@ of the value of US rare-gas imports, and helium
  @@HELIUM@@. The line&rsquo;s value says almost nothing about neon.</li>
  <li><b>Photosensitive devices and LEDs</b>, mostly solar cells and modules: US imports fell @@SOLUS@@ in
  2025.</li>
  </ul>
  <p class="cav">Lines made of a few large shipments, such as chip-making machines, swing widely from
  one period to the next; a single year's change there is not a trend.</p>

  <h3>And the world, as importers report it</h3>
  <p>Countries also file monthly reports to UN Comtrade, which carry a near-world view past 2024.
  Each line below is the trade of the importers that filed every month of both periods compared
  (@@WN@@ of them for 2024 against 2025, @@WHN@@ for the half-years, because fewer have filed 2026), and
  each row says what share of that line's 2024 world imports those countries held, so a thin panel is
  visible rather than hidden. China, India and Taiwan do not file monthly, so they are missing as
  buyers &mdash; which matters most for the chip lines &mdash; but are counted as suppliers, because the
  panel's members report where their goods came from. Data to @@WLAST@@.</p>
  <div class="tbl"><table><thead><tr><th>Customs line</th><th class="n">2025 vs 2024</th>
  <th class="n">Jan&ndash;Jun 2026 vs 2025</th><th class="n">China, 2025</th>
  <th class="n">panel's share of 2024 world imports</th></tr></thead>
  <tbody>@@WROWS@@</tbody></table></div>
  <p class="src"><b>Source:</b> <a href="https://comtradeplus.un.org/">UN Comtrade, monthly imports as
  reported by importers</a>. Computed values:
  <a href="https://github.com/materials-atlas/critical-materials-atlas/blob/main/out/ai_buildout_comtrade.json"><code>out/ai_buildout_comtrade.json</code></a>.
  The same pull answers two questions filed for the <a href="grid-trade">research note</a>, in
  <code>buildout-study/AMENDMENT_COMTRADE_2026.md</code>.</p>
  <figure class="fig">@@SHAREFIG@@
  <figcaption><b>Who buys from China, and who does not.</b> China's share of the value of each line's
  imports in 2025. The same line can be a Chinese-supplied market in the EU and almost none of the US's
  &mdash; electrical steel is the clearest case.</figcaption></figure>
  <p>The world panel tells the same story as the two national records: memory up @@WMEM@@ in the first
  half of 2026 (on a panel holding @@WMEMCOV@@ of that line's world imports), transformers up in 2025,
  and China's share of the electrical-steel lines higher again. Values are in current dollars, so a
  rise mixes price and quantity.</p>
</section>
"""
    for k, v in t.items():
        html = html.replace('@@%s@@' % k, v)
    return html


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
    mo = [L[c]['real_growth_pct'] for c in ('850152', '850153', '841370', '841480')]
    with io.open(STUDY_JSON, encoding='utf-8') as f:
        st = json.load(f)
    sg = st['checks']['suppliers_goes_combined']
    cc = st['checks']['contaminated_controls']           # the note's 2023-24 gap vs electrical goods
    note_uv, note_q = cc['price']['coefs']['TxP2']['pct'], cc['volume']['coefs']['TxP2']['pct']
    bt = st['designs']['B_transformers']                 # the note's filed comparison, heavy machinery
    note_buv, note_bq = bt['price']['coefs']['TxP2']['pct'], bt['volume']['coefs']['TxP2']['pct']
    g0, g1 = sg[str(YEARS[0])], sg[str(YEARS[-1])]

    hero_svg = hero_chart(L)
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The AI build-out in customs data &mdash; Critical Materials Atlas</title>
<meta name="description" content="World trade in the lines a data-centre build-out runs on, 2019 to 2024 in constant dollars, with EU and US imports to July 2026: chips, the materials that go into them, and the transformers, electrical steel and copper wire that carry power to them.">
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
  <b>integrated circuits grew @@CHMIN@@&ndash;@@CHMAX@@%</b>, and electric motors, pumps and
  compressors, which the same electrification buys, @@MOMIN@@&ndash;@@MOMAX@@%. Growth in trade value
  is not a test. Our <a href="grid-trade">research note</a> tests transformers flow by flow, 2023&ndash;24
  against their 2012&ndash;2020 average: against its filed comparison of heavy machinery, transformer
  unit values stood +@@NOTEBUV@@% and tonnes +@@NOTEBQ@@% higher, but against motors, pumps and
  compressors the gaps (+@@NOTEUV@@% and +@@NOTEQ@@%) cannot be told apart from zero. The rise may
  belong to electrification generally, not to transformers, let alone to data centres. What stands out
  more clearly is one step upstream: China is now the largest exporter of the steel inside
  transformers.</p>
</div></section>

<section class="wrap xp">
  <figure class="fig">@@HERO@@
  <figcaption><b>Where the money is, and where the growth is.</b> Each dot is one customs line: world
  exports in @@Y1@@ against the change since @@Y0@@ in constant dollars. The chip lines are the large
  markets; the transformer lines are small and fast. Nothing here says the build-out caused that &mdash;
  this page and the <a href="grid-trade">research note</a> take it apart below.</figcaption></figure>

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
  transformer from a substation's. The four lines under &ldquo;other electrical machinery&rdquo; are
  the goods the research note uses as a robustness comparison, because they share that demand. It does not measure production or installation, only what crossed
  a border. And a customs line is not a product: the notes under each line say where the code is
  wider than its name.</div>
</section>

@@EXT@@
<section class="wrap xp">
  <h2>What &ldquo;building your own fab&rdquo; buys</h2>
  <p>A company that decides to make its own chips does not escape the supply chain; it moves to the
  part of it that sells the factory. The machines that make integrated circuits were a
  $@@FABBN@@bn line in @@Y1@@, up @@FABG@@% in constant dollars since @@Y0@@, and its three largest
  exporters &mdash; @@FABTOP@@ &mdash; ship @@FAB3@@% of it. The customs line that carries photoresists
  (along with other photographic chemicals) is narrower still: one country, @@PRTOP@@, ships
  @@PRSH@@% of it. None of this says anything about any particular
  company&rsquo;s chip, its cost or its schedule, which customs data cannot see. It says who a new
  fab would be buying from.</p>
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
  <div class="note"><b>No line here is readable, including the one with a small p-value.</b> Seven
  lines were tested with no correction for testing seven, and a common price cycle can move both
  sides together. Rare gases comes in at @@NEON@@ per 1% of chip trade with p = @@NEONP@@, close to
  the smallest effect twenty-two observations could detect; and that line is mostly helium, which
  follows industry at large. Treat this table as a list of things to
  measure properly with monthly data, not as a result.</div>
</section>

<section class="wrap xp">
  <h2>Which lines are worth watching</h2>
  <p>Two things are true at once, and only one of them is about concentration. The transformer lines
  are small and growing fast, but they are <i>less</i> concentrated than the chip lines, not more:
  their largest exporters hold 13&ndash;23% of world exports against 21&ndash;38% for processors and
  memory. What is both small and becoming more concentrated is
  <b>grain-oriented electrical steel</b>, the core of a transformer. Taking its two customs lines
  together (read in the 2002 nomenclature, as in the note), world exports were $@@GOESBN@@bn in
  @@Y1@@; China's share of them rose from @@GOESCN0@@% in @@Y0@@ to @@GOESCN1@@%, and the three largest
  exporters' from @@GOES30@@% to @@GOES31@@%, partly replacing Russian exports. The
  <a href="grid-trade">research note</a> follows this to July 2026: in the EU's imports the shift to
  China continued, while direct US imports of the steel still come mostly from Japan and South Korea.
  That
  makes it a material to watch, which is not the same as a demonstrated constraint &mdash; nothing on this
  page measures whether anyone was actually short of it.</p>
  <p class="howto-src"><b>Sources.</b> Trade: CEPII BACI, release V202601 (Etalab Open Licence 2.0),
  read through the atlas's single BACI reader, which applies the atlas's own quantity repairs. The
  @@Y0@@ and @@Y1@@ table is read in the HS 2017 nomenclature, in which those six-digit codes exist;
  the chip-cycle series is read in HS 2002 for every year, so that no code changes underneath it.
  Deflator: World Bank, US consumer price index (FP.CPI.TOTL). The electrical-steel figures are read
  from the research note's output, <code>out/buildout_study.json</code>. Built by
  <code>build_ai_buildout.py</code> from <code>out/ai_buildout.json</code>, which holds every figure
  on this page.</p>
</section>
<section class="wrap xp">
  <h2>Sources</h2>
  <ol class="refs">
  <li><b>Trade, world.</b> CEPII, <i>BACI: International Trade Database at the Product Level</i>,
  release V202601, used under the Etalab Open Licence 2.0.
  <a href="https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37">cepii.fr</a>. Method:
  Gaulier, G. and Zignago, S. (2010), CEPII Working Paper 2010-23.
  <a href="http://www.cepii.fr/PDF_PUB/wp/2010/wp2010-23.pdf">wp2010-23</a>.</li>
  <li><b>Trade, the EU.</b> Eurostat, Comext monthly bulk files (CN8), imports from outside the EU,
  reused under the Commission&rsquo;s reuse policy.
  <a href="https://ec.europa.eu/eurostat/api/dissemination/files?dir=comext%2FCOMEXT_DATA%2FPRODUCTS">ec.europa.eu</a>.</li>
  <li><b>Trade, the United States.</b> US Census Bureau, international trade API, general imports at
  ten digits (a US government work, public domain).
  <a href="https://api.census.gov/data/timeseries/intltrade/imports/hs">api.census.gov</a>.</li>
  <li><b>Trade, the world panel after 2024.</b> UN Comtrade, monthly imports as reported by importers.
  <a href="https://comtradeplus.un.org/">comtradeplus.un.org</a>. Only derived totals and shares appear
  here; the records themselves are not redistributed.</li>
  <li><b>Deflator.</b> World Bank, consumer price index, United States (FP.CPI.TOTL), fetched
  17 September 2026. <a href="https://data.worldbank.org/indicator/FP.CPI.TOTL">data.worldbank.org</a>.</li>
  <li><b>Photoresists in 3707.90.</b> US Customs and Border Protection, HQ 085914, <i>Photoresists</i>
  (29 January 1990), classified in 3707.90.30, and its reconsideration HQ 087315 (10 September 1991),
  same heading; neither revoked, checked 20 September 2026.
  <a href="https://rulings.cbp.gov/ruling/085914">rulings.cbp.gov</a>.</li>
  <li><b>The transformer study this page draws on.</b> Critical Materials Atlas,
  <a href="grid-trade">Grid transformers rose with all electrical equipment, and their steel moved to
  China</a>, with its pre-registration and amendments in
  <a href="https://github.com/materials-atlas/critical-materials-atlas/tree/main/buildout-study"><code>buildout-study/</code></a>.</li>
  </ol>
  <p class="cav">Every figure on this page is in
  <a href="https://github.com/materials-atlas/critical-materials-atlas/blob/main/out/ai_buildout.json"><code>out/ai_buildout.json</code></a>,
  <a href="https://github.com/materials-atlas/critical-materials-atlas/blob/main/out/ai_buildout_ext.json"><code>out/ai_buildout_ext.json</code></a> and
  <a href="https://github.com/materials-atlas/critical-materials-atlas/blob/main/out/ai_buildout_comtrade.json"><code>out/ai_buildout_comtrade.json</code></a>,
  built by <code>build_ai_buildout.py</code>.</p>
</section>
@@FOOT@@
</body></html>
""".replace('@@EXT@@', ext_section()).replace('@@HERO@@', hero_svg).replace('@@CSS@@', CSS).replace('@@NAV@@', NAV).replace('@@FOOT@@', FOOT) \
   .replace('@@ROWS@@', tbl).replace('@@Y0@@', str(YEARS[0])).replace('@@Y1@@', str(YEARS[-1])) \
   .replace('@@TRMIN@@', str(round(min(tr)))).replace('@@TRMAX@@', str(round(max(tr)))) \
   .replace('@@CHMIN@@', str(round(min(ch)))).replace('@@CHMAX@@', str(round(max(ch)))) \
   .replace('@@CHIPBN@@', format(chip_bn, '.0f')).replace('@@TRBN@@', format(tr_bn, '.0f')) \
   .replace('@@GOESBN@@', format(g1['value_musd'] / 1000.0, '.1f')) \
   .replace('@@GOESCN0@@', str(round(100 * g0['china_share']))).replace('@@GOESCN1@@', str(round(100 * g1['china_share']))) \
   .replace('@@GOES30@@', str(round(100 * g0['top3_share']))).replace('@@GOES31@@', str(round(100 * g1['top3_share']))) \
   .replace('@@MOMIN@@', str(round(min(mo)))).replace('@@MOMAX@@', str(round(max(mo)))) \
   .replace('@@NOTEUV@@', str(round(note_uv))).replace('@@NOTEQ@@', str(round(note_q))) \
   .replace('@@NOTEBUV@@', str(round(note_buv))).replace('@@NOTEBQ@@', str(round(note_bq)))    .replace('@@CYROWS@@', cyrows).replace('@@CY0@@', str(cy0)).replace('@@CY1@@', str(cy1))    .replace('@@NEON@@', neon).replace('@@NEONP@@', neonp).replace('@@RATIO@@', '%.0f' % (chip_bn / tr_bn)) \
   .replace('@@FABBN@@', format(L['848620']['value_musd'][str(YEARS[-1])] / 1000.0, '.0f')) \
   .replace('@@FABG@@', str(round(L['848620']['real_growth_pct']))) \
   .replace('@@FABTOP@@', ', '.join(NAMES.get(t['iso3'], t['iso3']) for t in L['848620']['top3_latest'])) \
   .replace('@@FAB3@@', str(round(100 * sum(t['share'] for t in L['848620']['top3_latest'])))) \
   .replace('@@PRTOP@@', NAMES.get(L['370790']['top3_latest'][0]['iso3'], L['370790']['top3_latest'][0]['iso3'])) \
   .replace('@@PRSH@@', str(round(100 * L['370790']['top3_latest'][0]['share'])))


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
