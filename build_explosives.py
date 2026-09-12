# -*- coding: utf-8 -*-
"""Explosives as a mining indicator: what it measures, and what it does not.

THE CLAIM BEING TESTED
A widely-shared argument runs: mining consumes about 75% of all explosives against the military's
25%, so explosives are the furthest-upstream market in the economy and their price will move before
any expansion in commodity supply. If true, it would be a genuinely early indicator - earlier than
anything else this atlas tracks - and it would be a chokepoint sitting above EVERY mined material at
once rather than above one metal.

WHAT THE ONE AUTHORITATIVE MEASUREMENT SAYS
USGS Minerals Yearbook 2019, Explosives chapter (Lori E. Apodaca, published March 2024; the
underlying survey is collected by the Institute of Makers of Explosives). United States only, and
that limit matters. Industrial explosives and blasting agents sold for consumption in 2019, by use,
in thousand metric tons - table 3, verbatim:

    coal mining                   961      55.6%
    construction work             306      17.7%
    quarrying and nonmetal        254      14.7%
    metal mining                  155       9.0%
    all other purposes             53       3.1%
    total                       1,730

Mining of all kinds is 79%, close enough to the claim. But the line that matters for a
critical-materials atlas is the fourth one. Explosives demand is COAL demand. Metal mining - the
part that moves copper, nickel, lithium - is nine percent of it. "Demand for metals is demand for
explosives" is, in the only country where the split is actually measured, mostly a statement about
coal.

Note also what this table is NOT: it is industrial explosives only. Military explosives are a
different survey and are not in it, so this source cannot settle the 75/25 civil-military split at
all. The market-research reports that can be found for that number disagree with each other by a
factor of nearly two, so the atlas does not repeat it.

WHAT THE TRADE DATA SAYS
Tested on the countries where trade actually approximates consumption. The United States, Australia,
Russia and Canada are excluded outright: they manufacture their own explosives, so their imports say
nothing about what they blast. That leaves the copper economies, which import detonators and mine
little or no coal - the cleanest available separation of the metal signal from the coal one.

Detonators (HS 3603) rather than ammonium nitrate (HS 3102.30) on purpose. 8.5 million tonnes of
ammonium nitrate are traded a year against 444 thousand tonnes of prepared explosives, because
ammonium nitrate is overwhelmingly a fertiliser. Building this on ammonium nitrate would measure
agriculture. Detonators are not dual-use in that way, are made under licence, and are needed roughly
one per blast hole.

Sources: CEPII BACI (Etalab 2.0) for trade 2002-2024; BGS World Mineral Statistics for copper mine
production, one source and one stage only - the cube holds three producers' estimates for the same
quantity and summing them gave Chile 8,441 kt for 2024 against a real 5,506.

Run:  python build_explosives.py
Out:  out/explosives.json, explosives.html
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import duckdb                                                     # noqa: E402
import baci                                                       # noqa: E402

CODES = {'360300': 'detonators and fuses', '360200': 'prepared explosives',
         '310230': 'ammonium nitrate'}
# Copper economies that IMPORT their explosives. Excluded by design: USA, AUS, RUS, CAN - they make
# their own, so imports are not consumption.
TEST = ['CHL', 'PER', 'ZMB', 'COD', 'MNG', 'KAZ', 'BRA', 'PHL', 'MEX', 'IDN']
NAMES = {'CHL': 'Chile', 'PER': 'Peru', 'ZMB': 'Zambia', 'COD': 'DR Congo', 'MNG': 'Mongolia',
         'KAZ': 'Kazakhstan', 'BRA': 'Brazil', 'PHL': 'Philippines', 'MEX': 'Mexico',
         'IDN': 'Indonesia'}

# USGS Minerals Yearbook 2019, table 3. Thousand metric tons, 2019.
USGS_USE = [('Coal mining', 961), ('Construction work', 306),
            ('Quarrying and nonmetal mining', 254), ('Metal mining', 155),
            ('All other purposes', 53)]
# USGS table 2: detonators sold for consumption, units.
USGS_DET = {2015: {'mining': 37900000, 'oilgas': 1700000},
            2019: {'mining': 28900000, 'oilgas': 4850000}}


def corr(a, b):
    n = len(a)
    if n < 6:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a) ** 0.5
    vb = sum((x - mb) ** 2 for x in b) ** 0.5
    if not va or not vb:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (va * vb)


def growth(v):
    return [(v[i] / v[i - 1]) - 1.0 if v[i - 1] > 0 and v[i] > 0 else None
            for i in range(1, len(v))]


def load_trade():
    """Detonator imports by (iso3, year): value in $000 and tonnes, from BACI HS02."""
    con = duckdb.connect()
    cc = baci.countries()
    num2iso = {str(k): v for k, v in cc['iso3'].items() if v}
    out = {}
    for y in range(2002, 2025):
        p = baci.path(y, 'HS02')
        if not os.path.exists(p):
            continue
        q = ("select j, k, sum(v), sum(q) from read_parquet('" + p.replace('\\', '/')
             + "') where k in (" + ','.join("'%s'" % c for c in sorted(CODES))
             + ") group by j, k")
        for j, k, v, qq in con.execute(q).fetchall():
            i3 = num2iso.get(str(j))
            if i3:
                out.setdefault((i3, y), {})[k] = {'usd_000': float(v or 0), 't': float(qq or 0)}
    return out


def load_production():
    """Copper MINE production, one source only. See the module docstring for why that matters."""
    con = duckdb.connect()
    q = ("select country_iso3, year, sum(value_t) from '"
         + os.path.join(ROOT, 'pipeline', 'data', 'cube.parquet').replace('\\', '/')
         + "' where measure='production' and material='copper' and stage='mine' "
           "and source='BGS World Mineral Statistics' and country_iso3 is not null "
           "and year between 2002 and 2024 group by 1,2")
    return {(i3, int(y)): float(t) for i3, y, t in con.execute(q).fetchall() if t}


def main():
    trade, prod = load_trade(), load_production()
    rows = []
    for i3 in TEST:
        P, D, T, yrs = [], [], [], []
        for y in range(2002, 2025):
            p = prod.get((i3, y))
            d = trade.get((i3, y), {}).get('360300')
            if p and d and d['usd_000'] and d['t']:
                yrs.append(y)
                P.append(p)
                D.append(d['usd_000'])
                T.append(d['t'])
        if len(P) < 8:
            continue
        gP, gT = growth(P), growth(T)
        pairs = [(a, b) for a, b in zip(gP, gT) if a is not None and b is not None]
        rows.append({
            'iso': i3, 'name': NAMES.get(i3, i3), 'n_years': len(P),
            'years': [yrs[0], yrs[-1]],
            'r_level_tonnes': round(corr(P, T), 2) if corr(P, T) is not None else None,
            'r_level_usd': round(corr(P, D), 2) if corr(P, D) is not None else None,
            'r_growth_tonnes': (round(corr([a for a, _ in pairs], [b for _, b in pairs]), 2)
                                if len(pairs) > 5 else None),
            'copper_kt_2024': round(prod.get((i3, 2024), 0) / 1000.0),
            'detonators_usd_m_2024': round(
                trade.get((i3, 2024), {}).get('360300', {}).get('usd_000', 0) / 1000.0, 1),
        })
    rows.sort(key=lambda r: (-(r['r_level_tonnes'] if r['r_level_tonnes'] is not None else -9),
                             r['iso']))

    # lead / lag on the strongest case. shift -1 pairs this year's output with LAST year's trade,
    # so a negative shift means trade LEADS - which is what the claim requires.
    lead = {}
    for i3 in ('CHL', 'PER'):
        P, T = [], []
        for y in range(2002, 2025):
            p = prod.get((i3, y))
            d = trade.get((i3, y), {}).get('360300')
            if p and d and d['t']:
                P.append(p)
                T.append(d['t'])
        gP, gT = growth(P), growth(T)
        shifts = {}
        for s in (-2, -1, 0, 1, 2):
            aa, bb = [], []
            for i in range(len(gP)):
                j = i + s
                if 0 <= j < len(gT) and gP[i] is not None and gT[j] is not None:
                    aa.append(gP[i])
                    bb.append(gT[j])
            r = corr(aa, bb) if len(aa) > 5 else None
            shifts[str(s)] = round(r, 2) if r is not None else None
        lead[i3] = shifts

    world = {}
    for code in sorted(CODES):
        v = sum(d.get(code, {}).get('usd_000', 0) for (i3, y), d in trade.items() if y == 2024)
        t = sum(d.get(code, {}).get('t', 0) for (i3, y), d in trade.items() if y == 2024)
        world[code] = {'label': CODES[code], 'usd_m_2024': round(v / 1000.0),
                       'kt_2024': round(t / 1000.0)}

    doc = {
        'note': 'Is explosives trade an indicator of mining activity? Measured, not assumed.',
        'us_end_use_2019_kt': [{'use': u, 'kt': k,
                                'pct': round(100.0 * k / 1730.0, 1)} for u, k in USGS_USE],
        'us_end_use_source': ('USGS Minerals Yearbook 2019, Explosives (Lori E. Apodaca, published '
                              'March 2024), table 3; survey data collected by the Institute of '
                              'Makers of Explosives. United States only. Industrial explosives '
                              'only - military explosives are a different survey and are not in it.'),
        'us_detonators': USGS_DET,
        'world_trade_2024': world,
        'countries': rows,
        'lead_lag': lead,
        'lead_lag_convention': ('shift -1 pairs a year of output with the PREVIOUS year of '
                                'explosives trade, so a negative shift means trade LEADS output; '
                                '+1 means trade follows it.'),
        'excluded': ['USA', 'AUS', 'RUS', 'CAN'],
        'excluded_why': ('they manufacture their own explosives, so imports are not a measure of '
                         'consumption'),
        'code_choice_why': ('detonators (HS 3603), not ammonium nitrate (HS 3102.30): 8.5 Mt of '
                            'ammonium nitrate trades annually against 0.44 Mt of prepared '
                            'explosives, because ammonium nitrate is overwhelmingly a fertiliser'),
    }
    io.open(os.path.join(ROOT, 'out', 'explosives.json'), 'w', encoding='utf-8').write(
        json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True))
    print('out/explosives.json: %d countries tested' % len(rows))
    for r in rows:
        print('   %-12s level(t) %5s  growth(t) %5s   %5d kt Cu   $%5.1f m detonators'
              % (r['name'], r['r_level_tonnes'], r['r_growth_tonnes'],
                 r['copper_kt_2024'], r['detonators_usd_m_2024']))
    io.open(os.path.join(ROOT, 'explosives.html'), 'w', encoding='utf-8',
            newline='\n').write(page(doc))
    print('   Chile lead/lag:', lead.get('CHL'))
    print('wrote explosives.html')
    return doc


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
        '<div><h4>Sources</h4>USGS &middot; BGS &middot; IEA<br>UN Comtrade &middot; CEPII BACI '
        '&middot; Eurostat &middot; World Bank</div>'
        '<div class="fineprint">Independent public-data research; figures approximate and '
        'rounded.</div>'
        '</div></footer>')

CSS = """
.xp{max-width:60rem}
.xp table{border-collapse:collapse;width:100%;font-size:.92rem;margin:.6rem 0}
.xp th,.xp td{padding:.4rem .6rem;border-bottom:1px solid #e5e7eb;text-align:left}
.xp td.n,.xp th.n{text-align:right;font-variant-numeric:tabular-nums}
.xp tbody tr:hover{background:#fafafa}
.bar{display:inline-block;height:.62rem;background:#0e7c74;border-radius:2px;vertical-align:middle}
.bar.w{background:#c9d5d3}
.pos{color:#0e7c74;font-weight:600}.neg{color:#b3384b;font-weight:600}
.lg{display:flex;gap:.5rem;align-items:flex-end;margin:.8rem 0 .2rem}
.lg div{text-align:center;font-size:.72rem;color:#5f5a52}
.lg .b{width:3.4rem;background:#0e7c74;border-radius:3px 3px 0 0}
.lg .b.dim{background:#c9d5d3}
.note{background:#f7f7f5;border-left:3px solid #0e7c74;padding:.7rem 1rem;margin:1rem 0;font-size:.93rem}
"""


def page(doc):
    use = doc['us_end_use_2019_kt']
    mine_pct = round(sum(u['pct'] for u in use if u['use'] in
                         ('Coal mining', 'Quarrying and nonmetal mining', 'Metal mining')), 1)
    metal = next(u for u in use if u['use'] == 'Metal mining')
    rows = doc['countries']
    ll = doc['lead_lag']['CHL']

    def rcell(v):
        if v is None:
            return '<td class="n">&mdash;</td>'
        cls = 'pos' if v > 0 else 'neg'
        w = min(abs(v), 1.0) * 5.4
        bar = '<span class="bar%s" style="width:%.2frem"></span>' % ('' if v > 0 else ' w', w)
        return '<td class="n">%s <span class="%s">%+.2f</span></td>' % (bar, cls, v)

    trs = []
    for r in rows:
        trs.append('<tr><td>%s</td>%s%s<td class="n">%s</td><td class="n">$%s m</td></tr>'
                   % (r['name'], rcell(r['r_level_tonnes']), rcell(r['r_growth_tonnes']),
                      '{:,}'.format(r['copper_kt_2024']), r['detonators_usd_m_2024']))

    userows = ''.join(
        '<tr><td>%s</td><td class="n">%s</td><td class="n">%.1f%%</td>'
        '<td><span class="bar" style="width:%.2frem"></span></td></tr>'
        % (u['use'], '{:,}'.format(u['kt']), u['pct'], u['pct'] / 100.0 * 14)
        for u in use)

    bars = ''.join(
        '<div><div class="b%s" style="height:%.0fpx"></div>%s<br>%+.2f</div>'
        % ('' if k == '0' else ' dim', max(3, abs(ll[k] or 0) * 110),
           {'-2': 'leads 2y', '-1': 'leads 1y', '0': 'same year',
            '1': 'follows 1y', '2': 'follows 2y'}[k], ll[k] or 0)
        for k in ('-2', '-1', '0', '1', '2'))

    det = doc['us_detonators']
TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Explosives are a coal business &mdash; Critical Materials Atlas</title>
<meta name="description" content="Mining consumes about 79% of US industrial explosives, but coal is 56% of it and metal mining only 9%. Detonator imports track copper output in Chile (r=0.78) but do not lead it: the correlation peaks in the same year, not before.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style>@@CSS@@</style></head><body>
@@NAV@@
<section class="hero"><div class="wrap">
  <div class="eyebrow">Upstream &middot; the market above every mine</div>
  <h1>Explosives are a coal business</h1>
  <p class="deck">Blasting sits further upstream than anything else this atlas tracks, and a
  bottleneck there would sit above <i>every</i> mined material at once. That makes it worth
  measuring rather than assuming. In the one country that publishes the split, mining does take
  about <b>@@MINEPCT@@%</b> of industrial explosives &mdash; but <b>coal is 56%</b> of it and metal mining,
  the part that moves copper and nickel and lithium, is <b>@@METALPCT@@%</b>. And where explosives trade does
  track metal output, it moves <i>with</i> the mine, not ahead of it.</p>
</div></section>

<section class="wrap xp">
  <h2>What explosives are actually used for</h2>
  <p>United States, 2019, industrial explosives and blasting agents sold for consumption, thousand
  metric tons. This is the only country that surveys the end-use split.</p>
  <table><thead><tr><th>Use</th><th class="n">kt</th><th class="n">share</th><th></th></tr></thead>
  <tbody>@@USEROWS@@</tbody></table>
  <div class="note"><b>Read the fourth line before the first.</b> "Demand for metals is demand for
  explosives" is, where it is measured, mostly a statement about coal. Metal mining is a ninth of
  the total. Note also what this table is not: industrial explosives only. Military explosives are
  a separate survey and are not in it, so this source cannot settle the civil-military split &mdash;
  and the market-research reports that claim to disagree with each other by nearly a factor of two,
  so no figure for it is quoted here.</div>
</section>

<section class="wrap xp">
  <h2>Does explosives trade track mining?</h2>
  <p>Detonators (HS&nbsp;3603) against copper mine production, 2002&ndash;2024, for copper economies
  that <i>import</i> their explosives. The United States, Australia, Russia and Canada are excluded:
  they manufacture their own, so their imports measure nothing. Correlations are on <b>tonnage</b>,
  not dollars, so price inflation cannot create the result &mdash; in Chile the tonnage correlation
  is the stronger of the two.</p>
  <table><thead><tr><th>Country</th><th class="n">levels</th><th class="n">year-on-year</th>
  <th class="n">copper 2024</th><th class="n">detonator imports 2024</th></tr></thead>
  <tbody>@@TRS@@</tbody></table>
  <p class="howto-src"><b>Why detonators and not ammonium nitrate.</b> 8.5 million tonnes of
  ammonium nitrate trade each year against 0.44 million tonnes of prepared explosives, because
  ammonium nitrate is overwhelmingly a fertiliser. A study built on it would be measuring
  agriculture. Detonators are made under licence, are not a fertiliser, and are needed roughly one
  per blast hole.</p>
</section>

<section class="wrap xp">
  <h2>It does not lead. It coincides.</h2>
  <p>Chile is the strongest case in the table above, so it is the fair place to test the claim that
  explosives move first. Correlation of year-on-year growth in detonator import tonnage against
  copper mine output, at each shift:</p>
  <div class="lg">@@BARS@@</div>
  <div class="note">The signal is <b>@@LL0@@ in the same year</b> and collapses to @@LLM1@@ a year
  earlier. Explosives track the mining that is happening, not the mining that is about to happen.
  As an indicator that makes them a confirmation, not an early warning &mdash; useful for checking
  whether announced expansions are actually moving rock, and not useful for anticipating them.</div>
  <p>One measured counter-signal, from the same USGS survey: detonators sold for mining and
  quarrying in the United States <b>fell from @@DET15M@@ million to @@DET19M@@ million</b> between 2015 and 2019,
  while detonators for oil and gas rose from @@DET15O@@ million to @@DET19O@@ million. Through a period when metal
  prices were not falling, the blasting series was going the other way.</p>
</section>

<section class="wrap xp">
  <h2>What would change the answer</h2>
  <p>Three limits, each of which is a route to a better test rather than a caveat to wave at.</p>
  <ul>
    <li><b>Trade is not consumption.</b> The four largest mining economies make their own explosives
    and are excluded. A consumption series &mdash; production plus imports minus exports, per
    country &mdash; would put them back in.</li>
    <li><b>The end-use split is American.</b> Coal is 56% of US explosives because the United States
    is a coal economy. In Chile the mix must be almost entirely metal, which is exactly why the
    Chilean correlation is the strongest here. No other country publishes the split.</li>
    <li><b>A year is a blunt instrument.</b> If explosives lead output by a quarter, annual data
    cannot see it. The monthly trade layer behind this atlas runs to 2026 and could.</li>
  </ul>
  <p class="howto-src"><b>Sources.</b> End use and detonator counts: USGS Minerals Yearbook 2019,
  <i>Explosives</i>, by Lori E. Apodaca, published March 2024, tables 2 and 3; survey collected by
  the Institute of Makers of Explosives. Trade: CEPII BACI (Etalab Open Licence 2.0). Copper mine
  production: BGS World Mineral Statistics, mine stage only &mdash; the cube holds three
  organisations' estimates of the same quantity and summing them overstates Chile by half.
  Built by <code>build_explosives.py</code>; the figures behind this page are in
  <code>out/explosives.json</code>.</p>
</section>
@@FOOT@@
</body></html>
"""

def page(doc):
    use = doc['us_end_use_2019_kt']
    mine_pct = round(sum(u['pct'] for u in use if u['use'] in
                         ('Coal mining', 'Quarrying and nonmetal mining', 'Metal mining')), 1)
    metal = next(u for u in use if u['use'] == 'Metal mining')
    rows = doc['countries']
    ll = doc['lead_lag']['CHL']

    def rcell(v):
        if v is None:
            return '<td class="n">&mdash;</td>'
        cls = 'pos' if v > 0 else 'neg'
        bar = ('<span class="bar' + ('' if v > 0 else ' w') +
               '" style="width:' + format(min(abs(v), 1.0) * 5.4, '.2f') + 'rem"></span>')
        return ('<td class="n">' + bar + ' <span class="' + cls + '">' +
                format(v, '+.2f') + '</span></td>')

    trs = ''.join(
        '<tr><td>' + r['name'] + '</td>' + rcell(r['r_level_tonnes']) +
        rcell(r['r_growth_tonnes']) + '<td class="n">' + format(r['copper_kt_2024'], ',') +
        '</td><td class="n">$' + str(r['detonators_usd_m_2024']) + ' m</td></tr>' for r in rows)

    userows = ''.join(
        '<tr><td>' + u['use'] + '</td><td class="n">' + format(u['kt'], ',') +
        '</td><td class="n">' + format(u['pct'], '.1f') + '%</td>'
        '<td><span class="bar" style="width:' + format(u['pct'] / 100.0 * 14, '.2f') +
        'rem"></span></td></tr>' for u in use)

    LAB = {'-2': 'leads 2y', '-1': 'leads 1y', '0': 'same year',
           '1': 'follows 1y', '2': 'follows 2y'}
    bars = ''.join(
        '<div><div class="b' + ('' if k == '0' else ' dim') + '" style="height:' +
        format(max(3.0, abs(ll[k] or 0) * 110), '.0f') + 'px"></div>' + LAB[k] + '<br>' +
        format(ll[k] or 0, '+.2f') + '</div>' for k in ('-2', '-1', '0', '1', '2'))

    det = doc['us_detonators']
    html = TEMPLATE
    for token, value in (
            ('CSS', CSS), ('NAV', NAV), ('FOOT', FOOT),
            ('MINEPCT', format(mine_pct, '.1f')), ('METALPCT', format(metal['pct'], '.1f')),
            ('USEROWS', userows), ('TRS', trs), ('BARS', bars),
            ('LL0', format(ll['0'] or 0, '+.2f')), ('LLM1', format(ll['-1'] or 0, '+.2f')),
            ('DET15M', format(det[2015]['mining'] / 1e6, '.1f')),
            ('DET19M', format(det[2019]['mining'] / 1e6, '.1f')),
            ('DET15O', format(det[2015]['oilgas'] / 1e6, '.1f')),
            ('DET19O', format(det[2019]['oilgas'] / 1e6, '.1f'))):
        html = html.replace('@@' + token + '@@', value)
    return html


if __name__ == '__main__':
    main()
