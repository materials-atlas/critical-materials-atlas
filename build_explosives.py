# -*- coding: utf-8 -*-
"""Explosives as a mining indicator. Tested, mostly failed, and corrected after review.

THE CLAIM BEING TESTED
A widely-shared argument: mining takes about 75% of all explosives against the military's 25%;
explosives are therefore the furthest-upstream market in the economy; and explosives PRICES will
rise before any surge in commodity supply, making them an early indicator.

WHAT THE ONE AUTHORITATIVE MEASUREMENT SAYS
USGS Minerals Yearbook 2019, Explosives (Lori E. Apodaca, published March 2024, table 3; survey
collected by the Institute of Makers of Explosives). UNITED STATES ONLY. Industrial explosives and
blasting agents sold for consumption, 2019, thousand metric tons: coal mining 961, construction 306,
quarrying and nonmetal mining 254, metal mining 155, all other 53; total 1,730.

So mining of all kinds is 79% of the US INDUSTRIAL market, which supports that half of the claim.
Within it, US demand is overwhelmingly coal. What this table cannot do is settle the civil-military
split, because military explosives are a separate survey and are not in it.

THE FIRST VERSION OF THIS PAGE OVERREACHED, AND TWO REVIEWERS SAID SO
It was published on 12 Sep 2026 titled "Explosives are a coal business" and concluded that
explosives coincide with mining rather than lead it, so the post's central claim failed. An
adversarial review by two independent language models, run separately on the same brief, converged
on the same four objections without seeing each other's answers. They are right:

  1. A US table cannot carry a global claim. The United States is an unusually coal-heavy mining
     economy; elsewhere the mix is iron ore, copper, gold. "Explosives are a coal business" is true
     of the United States and was not shown for anywhere else.
  2. The levels correlations are two trending series and carry almost no information. The growth
     column is the result, and in seven of ten countries it is ~0 or negative.
  3. DETONATOR TONNAGE IS A BAD PROXY, and this file's own label said why: HS 3603 is "detonators,
     safety fuses, DETONATING FUSES". Detonating cord is sold by the metre and dominates the traded
     mass, so tonnes track product mix, not blast count. The original page argued that using tonnage
     ruled out price inflation. It does not, and that sentence is withdrawn.
  4. THE LEAD/LAG TEST CANNOT ANSWER THE QUESTION. Fisher 95% intervals on n=22 are [0.41, 0.87] at
     lag 0 and [-0.31, 0.52] at lag -1. They OVERLAP, so the ranking may be noise. Worse, a
     procurement lead of three to nine months would appear at lag 0 in annual data, so annual data
     cannot distinguish "coincides" from "leads by two quarters" at all. Declaring the claim dead
     was a frequency mismatch dressed as a finding.

And the sharpest point, made independently by both: the post is about explosives PRICES leading a
supply surge. This page measures annual import TONNAGE of one HS code against copper output. It was
never a test of the price claim, and the original conclusion was not licensed by it.

WHAT SURVIVES
The US end-use table, bounded to the United States. One real contemporaneous correlation, in Chile,
with a confidence interval attached. A genuine null for any general cross-country relationship. And
a clear statement of what a real test would need.

Sources: USGS as above (PDF archived at raw/_sources/). CEPII BACI (Etalab 2.0) for trade 2002-2024.
BGS World Mineral Statistics for copper mine production, one source and one stage - the cube holds
three organisations' estimates of the same quantity and summing them overstates Chile by half.

Run:  python build_explosives.py
Out:  out/explosives.json, explosives.html
"""
import io
import json
import math
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

CODES = {'360300': 'detonators, safety fuses and detonating fuses',
         '360200': 'prepared explosives', '310230': 'ammonium nitrate'}
TEST = ['CHL', 'PER', 'ZMB', 'COD', 'MNG', 'KAZ', 'BRA', 'PHL', 'MEX', 'IDN']
NAMES = {'CHL': 'Chile', 'PER': 'Peru', 'ZMB': 'Zambia', 'COD': 'DR Congo', 'MNG': 'Mongolia',
         'KAZ': 'Kazakhstan', 'BRA': 'Brazil', 'PHL': 'Philippines', 'MEX': 'Mexico',
         'IDN': 'Indonesia'}
USGS_USE = [('Coal mining', 961), ('Construction work', 306),
            ('Quarrying and nonmetal mining', 254), ('Metal mining', 155),
            ('All other purposes', 53)]
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


def fisher_ci(r, n):
    """95% interval for a correlation. Published beside every r, because an r without one invites
    exactly the reading this page had to withdraw."""
    if r is None or n < 5 or abs(r) >= 1:
        return None
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - 1.96 * se, z + 1.96 * se

    def t(x):
        return (math.exp(2 * x) - 1) / (math.exp(2 * x) + 1)

    return [round(t(lo), 2), round(t(hi), 2)]


def growth(v):
    return [(v[i] / v[i - 1]) - 1.0 if v[i - 1] > 0 and v[i] > 0 else None
            for i in range(1, len(v))]


def load_trade():
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
        P, T, yrs = [], [], []
        for y in range(2002, 2025):
            p = prod.get((i3, y))
            d = trade.get((i3, y), {}).get('360300')
            if p and d and d['usd_000'] and d['t']:
                yrs.append(y)
                P.append(p)
                T.append(d['t'])
        if len(P) < 8:
            continue
        gP, gT = growth(P), growth(T)
        pairs = [(a, b) for a, b in zip(gP, gT) if a is not None and b is not None]
        rg = corr([a for a, _ in pairs], [b for _, b in pairs]) if len(pairs) > 5 else None
        rl = corr(P, T)
        rows.append({
            'iso': i3, 'name': NAMES.get(i3, i3), 'n_years': len(P), 'years': [yrs[0], yrs[-1]],
            'r_growth_tonnes': round(rg, 2) if rg is not None else None,
            'ci_growth': fisher_ci(rg, len(pairs)),
            'r_level_tonnes': round(rl, 2) if rl is not None else None,
            'copper_kt_2024': round(prod.get((i3, 2024), 0) / 1000.0),
            'detonators_usd_m_2024': round(
                trade.get((i3, 2024), {}).get('360300', {}).get('usd_000', 0) / 1000.0, 1),
        })
    rows.sort(key=lambda r: (-(r['r_growth_tonnes'] if r['r_growth_tonnes'] is not None else -9),
                             r['iso']))

    P, T = [], []
    for y in range(2002, 2025):
        p = prod.get(('CHL', y))
        d = trade.get(('CHL', y), {}).get('360300')
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
        shifts[str(s)] = {'r': round(r, 2) if r is not None else None,
                          'n': len(aa), 'ci': fisher_ci(r, len(aa))}

    world = {}
    for code in sorted(CODES):
        v = sum(d.get(code, {}).get('usd_000', 0) for (i3, y), d in trade.items() if y == 2024)
        t = sum(d.get(code, {}).get('t', 0) for (i3, y), d in trade.items() if y == 2024)
        world[code] = {'label': CODES[code], 'usd_m_2024': round(v / 1000.0),
                       'kt_2024': round(t / 1000.0)}

    n_pos = sum(1 for r in rows if (r['ci_growth'] or [0, 0])[0] > 0)
    doc = {
        'note': ('Is explosives trade an indicator of mining activity? Mostly no. Revised 12 Sep '
                 '2026 after adversarial review; see corrections.'),
        'corrections': [
            {'withdrawn': 'Explosives are a coal business (as a general claim)',
             'why': 'the end-use split is measured only in the United States, which is an unusually '
                    'coal-heavy mining economy; nothing was shown for any other country'},
            {'withdrawn': 'correlations are on tonnage, so price inflation cannot create the result',
             'why': 'HS 3603 is "detonators, safety fuses and detonating fuses" - detonating cord is '
                    'sold by the metre and dominates the traded mass, so tonnes track product mix '
                    'rather than blast count'},
            {'withdrawn': 'explosives coincide with mining rather than lead it',
             'why': 'the Fisher intervals at lag 0 and lag -1 overlap, and a lead of three to nine '
                    'months would appear at lag 0 in annual data anyway, so annual resolution '
                    'cannot distinguish the two'},
            {'withdrawn': "the post's central claim is not supported",
             'why': 'the claim is about explosives PRICES; this page measures import tonnage of one '
                    'HS code against copper output, and never tested a price at all'},
        ],
        'reviewed_by': ('two independent language models, run separately on the same brief, 12 Sep '
                        '2026; they converged on the same four objections without seeing each '
                        "other's answers"),
        'us_end_use_2019_kt': [{'use': u, 'kt': k, 'pct': round(100.0 * k / 1730.0, 1)}
                               for u, k in USGS_USE],
        'us_end_use_source': ('USGS Minerals Yearbook 2019, Explosives (Lori E. Apodaca, published '
                              'March 2024), table 3; survey collected by the Institute of Makers of '
                              'Explosives. UNITED STATES ONLY, industrial explosives only.'),
        'us_detonators': USGS_DET,
        'world_trade_2024': world,
        'countries': rows,
        'n_countries_ci_above_zero': n_pos,
        'lead_lag_chile': shifts,
        'lead_lag_caveat': ('annual data cannot separate "coincides" from "leads by one to three '
                            'quarters": both print at lag 0'),
        'excluded': ['USA', 'AUS', 'RUS', 'CAN'],
        'excluded_why': 'they manufacture their own explosives, so imports are not consumption',
    }
    io.open(os.path.join(ROOT, 'out', 'explosives.json'), 'w', encoding='utf-8').write(
        json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True))
    io.open(os.path.join(ROOT, 'explosives.html'), 'w', encoding='utf-8',
            newline='\n').write(page(doc))
    print('out/explosives.json + explosives.html')
    print('  countries whose growth interval excludes zero: %d of %d' % (n_pos, len(rows)))
    for r in rows:
        print('   %-12s growth r %5s  CI %s' % (r['name'], r['r_growth_tonnes'], r['ci_growth']))
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
        'rounded.</div></div></footer>')
CSS = """
.xp{max-width:60rem}
.xp table{border-collapse:collapse;width:100%;font-size:.92rem;margin:.6rem 0}
.xp th,.xp td{padding:.4rem .6rem;border-bottom:1px solid #e5e7eb;text-align:left}
.xp td.n,.xp th.n{text-align:right;font-variant-numeric:tabular-nums}
.bar{display:inline-block;height:.62rem;background:#0e7c74;border-radius:2px;vertical-align:middle}
.pos{color:#0e7c74;font-weight:600}.neg{color:#b3384b;font-weight:600}.zeroish{color:#8b857b}
.ci{color:#8b857b;font-size:.82rem;white-space:nowrap}
.note{background:#f7f7f5;border-left:3px solid #0e7c74;padding:.7rem 1rem;margin:1rem 0;font-size:.93rem}
.corr{background:#fdf6f2;border-left:3px solid #b3384b;padding:.8rem 1.1rem;margin:1.1rem 0;font-size:.93rem}
.corr li{margin:.35rem 0}
.corr .w{color:#b3384b;font-weight:600}
"""

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>What explosives can and cannot tell you about mining &mdash; Critical Materials Atlas</title>
<meta name="description" content="Mining takes 79% of US industrial explosives and coal is 56% of that. But detonator trade is a poor proxy for blasting, only one of ten copper economies shows a correlation whose interval excludes zero, and annual data cannot tell a coincident signal from a two-quarter lead. Revised after adversarial review.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style>@@CSS@@</style></head><body>
@@NAV@@
<section class="hero"><div class="wrap">
  <div class="eyebrow">Upstream &middot; a test that mostly failed</div>
  <h1>What explosives can and cannot tell you about mining</h1>
  <p class="deck">Blasting sits further upstream than anything else this atlas tracks, so a
  bottleneck there would sit above <i>every</i> mined material at once. That is worth measuring. The
  end-use data is solid and surprising: in the United States, mining takes <b>@@MINEPCT@@%</b> of
  industrial explosives and <b>coal is 56%</b> of it. The trade test is not. One country of ten
  shows a correlation whose interval excludes zero, the proxy is weaker than it looks, and annual
  data cannot answer the question that was actually asked. This page was <b>revised after
  review</b>, and what was withdrawn is listed below rather than quietly deleted.</p>
</div></section>

<section class="wrap xp">
  <h2>What explosives are actually used for</h2>
  <p>United States, 2019, industrial explosives and blasting agents sold for consumption, thousand
  metric tons. The United States is the only country that surveys the end-use split &mdash; which is
  also the reason this table cannot be turned into a global statement.</p>
  <table><thead><tr><th>Use</th><th class="n">kt</th><th class="n">share</th><th></th></tr></thead>
  <tbody>@@USEROWS@@</tbody></table>
  <div class="note"><b>Mining is 79%, and within it coal is the bulk.</b> That supports the first
  half of the original claim. It does not support extending it: the United States is an unusually
  coal-heavy mining economy, and in Chile or Peru the mix must be almost entirely metal. Nothing
  here measures that. The table also cannot settle the civil-military split, because military
  explosives are a separate survey and are not in it &mdash; and the market-research figures that
  claim to disagree with each other by nearly a factor of two, so none is quoted.</div>
</section>

<section class="wrap xp">
  <h2>Does explosives trade track mining? In one country of ten.</h2>
  <p>Detonator imports against copper mine production, 2002&ndash;2024, for copper economies that
  <i>import</i> their explosives; the United States, Australia, Russia and Canada are excluded
  because they manufacture their own. The column that matters is year-on-year growth, with its 95%
  interval. The levels column is shown last and greyed for a reason: two series that both trend
  upward for twenty-three years will correlate whatever the mechanism.</p>
  <table><thead><tr><th>Country</th><th class="n">year-on-year r</th><th class="n">95% interval</th>
  <th class="n">copper 2024</th><th class="n">levels r</th></tr></thead>
  <tbody>@@TRS@@</tbody></table>
  <div class="note"><b>@@NPOS@@ of ten intervals exclude zero.</b> Chile is the one, and it is the
  largest copper producer in the set, so it is the case with the most rock behind it. Everywhere
  else the year-on-year relationship is indistinguishable from nothing, and in Mexico and Indonesia
  it points the other way. That is a null result for any general link between explosives trade and
  metal output, and it is reported as one.</div>
</section>

<section class="wrap xp">
  <h2>Can it tell you what is coming? Not at this resolution.</h2>
  <p>Chile, year-on-year growth, correlation at each shift with its 95% interval. A negative shift
  means trade leads output.</p>
  <table><thead><tr><th>Shift</th><th class="n">r</th><th class="n">95% interval</th>
  <th class="n">n</th></tr></thead><tbody>@@LLROWS@@</tbody></table>
  <div class="corr"><b>What this cannot show.</b> The interval at lag 0 is @@CI0@@ and at lag
  &minus;1 is @@CIM1@@. They overlap, so the ranking between them may be noise. And a procurement
  lead of three to nine months would appear at <i>lag 0</i> in annual data, so this test cannot
  separate &ldquo;coincides&rdquo; from &ldquo;leads by two quarters&rdquo; even in principle. The
  first version of this page concluded that explosives coincide with mining rather than lead it.
  That conclusion is withdrawn.</div>
  <p>One measured fact that stands on its own, from the same survey: detonators sold for mining and
  quarrying in the United States <b>fell from @@DET15M@@ million to @@DET19M@@ million</b> units
  between 2015 and 2019, while detonators for oil and gas rose from @@DET15O@@ to @@DET19O@@
  million.</p>
</section>

<section class="wrap xp">
  <h2>What was withdrawn, and why</h2>
  <div class="corr">
  <p>This page was published on 12 September 2026 and revised the same day after an adversarial
  review by two independent language models, run separately on the same brief. They converged on the
  same objections without seeing each other's answers.</p>
  <ul>@@CORRS@@</ul>
  <p>The sharpest point was made by both: the original argument is about explosives <b>prices</b>
  leading a supply surge. This page measures annual import <b>tonnage</b> of one customs code
  against copper output. It was never a test of the price claim, and saying it was is the error
  this revision exists to correct.</p>
  </div>
</section>

<section class="wrap xp">
  <h2>What a real test would need</h2>
  <ul>
    <li><b>Consumption, not trade.</b> Production plus imports minus exports, per country, which
    would put the four excluded manufacturing economies back in.</li>
    <li><b>Unit counts, not tonnes.</b> Customs data reports mass, and in this code the mass is
    dominated by detonating cord rather than by the caps that correspond to blast holes.</li>
    <li><b>Prices.</b> Nothing here touches a price. Bulk blasting agents are ammonium nitrate, so
    their price is mostly an ammonia and gas price &mdash; which is a strong argument on its own
    against reading explosives prices as a clean mining signal.</li>
    <li><b>Monthly data.</b> The monthly trade layer behind this atlas runs to 2026 and is the only
    thing here that could see a lead shorter than a year.</li>
  </ul>
  <p class="howto-src"><b>Sources.</b> End use and detonator counts: USGS Minerals Yearbook 2019,
  <i>Explosives</i>, by Lori E. Apodaca, published March 2024, tables 2 and 3; survey collected by
  the Institute of Makers of Explosives; PDF archived in the repository. Trade: CEPII BACI (Etalab
  Open Licence 2.0). Copper mine production: BGS World Mineral Statistics, mine stage only &mdash;
  the cube holds three organisations' estimates of the same quantity and summing them overstates
  Chile by half. Built by <code>build_explosives.py</code>; figures in
  <code>out/explosives.json</code>, including the withdrawn claims.</p>
</section>
@@FOOT@@
</body></html>
"""


def page(doc):
    use = doc['us_end_use_2019_kt']
    mine_pct = round(sum(u['pct'] for u in use if u['use'] in
                         ('Coal mining', 'Quarrying and nonmetal mining', 'Metal mining')), 1)
    rows = doc['countries']
    ll = doc['lead_lag_chile']

    def ci(c):
        return '&mdash;' if not c else '[%+.2f, %+.2f]' % (c[0], c[1])

    def rspan(v, c):
        if v is None:
            return '&mdash;'
        cls = 'zeroish' if (c and c[0] <= 0 <= c[1]) else ('pos' if v > 0 else 'neg')
        return '<span class="' + cls + '">' + format(v, '+.2f') + '</span>'

    trs = ''.join(
        '<tr><td>' + r['name'] + '</td><td class="n">' +
        rspan(r['r_growth_tonnes'], r['ci_growth']) + '</td><td class="n ci">' +
        ci(r['ci_growth']) + '</td><td class="n">' + format(r['copper_kt_2024'], ',') +
        '</td><td class="n ci">' + (format(r['r_level_tonnes'], '+.2f')
                                    if r['r_level_tonnes'] is not None else '&mdash;') +
        '</td></tr>' for r in rows)

    userows = ''.join(
        '<tr><td>' + u['use'] + '</td><td class="n">' + format(u['kt'], ',') +
        '</td><td class="n">' + format(u['pct'], '.1f') + '%</td>'
        '<td><span class="bar" style="width:' + format(u['pct'] / 100.0 * 14, '.2f') +
        'rem"></span></td></tr>' for u in use)

    LAB = {'-2': 'trade leads 2 years', '-1': 'trade leads 1 year', '0': 'same year',
           '1': 'trade follows 1 year', '2': 'trade follows 2 years'}
    llrows = ''.join(
        '<tr><td>' + LAB[k] + '</td><td class="n">' + rspan(ll[k]['r'], ll[k]['ci']) +
        '</td><td class="n ci">' + ci(ll[k]['ci']) + '</td><td class="n">' + str(ll[k]['n']) +
        '</td></tr>' for k in ('-2', '-1', '0', '1', '2'))

    corrs = ''.join('<li><span class="w">Withdrawn:</span> &ldquo;' + c['withdrawn'] +
                    '&rdquo; &mdash; ' + c['why'] + '.</li>' for c in doc['corrections'])
    det = doc['us_detonators']
    html = TEMPLATE
    for token, value in (
            ('CSS', CSS), ('NAV', NAV), ('FOOT', FOOT),
            ('MINEPCT', format(mine_pct, '.1f')), ('USEROWS', userows), ('TRS', trs),
            ('LLROWS', llrows), ('CORRS', corrs),
            ('NPOS', str(doc['n_countries_ci_above_zero'])),
            ('CI0', ci(ll['0']['ci'])), ('CIM1', ci(ll['-1']['ci'])),
            ('DET15M', format(det[2015]['mining'] / 1e6, '.1f')),
            ('DET19M', format(det[2019]['mining'] / 1e6, '.1f')),
            ('DET15O', format(det[2015]['oilgas'] / 1e6, '.1f')),
            ('DET19O', format(det[2019]['oilgas'] / 1e6, '.1f'))):
        html = html.replace('@@' + token + '@@', value)
    return html


if __name__ == '__main__':
    main()
