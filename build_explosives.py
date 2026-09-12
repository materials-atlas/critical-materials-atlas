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

THE SECOND REVIEW ASKED FOR A GATE, AND THE GATE SETTLES IT
Asked to improve the study rather than kill it, both reviewers gave the same first instruction:
before estimating anything, check whether imported explosives could even BE the input. Compare what
a country imports against what its mines must consume.

Calibrated on the USGS survey itself rather than on assumed engineering constants. US metal mining
of every kind consumed 155 kt of explosives in 2019 (table 3); US copper mine output was 1,260 kt
contained. Attributing EVERY kilogram to copper - deliberately generous, since that 155 kt also
blasted gold, iron and everything else - gives at most 0.123 kt of explosive per kt of contained
copper. Applied to 2024:

    Chile   5,506 kt Cu -> at most 677 kt of explosives needed; imported 2.9 kt  =  0.4%
    Peru    2,736 kt Cu -> at most 337 kt needed;              imported 117.3 kt = 34.9%

And the number that ends the argument: WORLD TRADE IN PREPARED EXPLOSIVES WAS 445 kt IN 2024 -
less than what Chile's copper mines alone consume. Explosives are not a traded commodity in any
meaningful sense. ANFO is mixed on site from ammonium nitrate and diesel, and bulk emulsion is
manufactured at the mine gate, so the thing that moves across a border is the feedstock, not the
explosive.

That is fatal to the design and it is also the most interesting thing here. The one country with a
statistically real correlation, Chile, imports 0.4% of the relevant flow - so that correlation was
measuring an import residual, not blasting. The one country where imports are a serious share of
consumption, Peru at 35%, shows no correlation at all (+0.14, interval [-0.30, 0.53]).

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


# USGS Minerals Yearbook 2019 table 3: US METAL MINING of every kind consumed this much.
US_METAL_EXPLOSIVES_KT_2019 = 155.0


def coverage(trade, prod):
    """Could imports even be the input? A ceiling, built to be generous to the hypothesis.

    The intensity comes from the USGS survey, not from an assumed powder factor: US metal mining's
    total explosives consumption divided by US contained copper, attributing every kilogram to
    copper even though the same explosives blasted gold and iron. That makes the resulting need a
    CEILING, so any country whose imports fall far below it fails the test conclusively rather than
    arguably.
    """
    us_cu = prod.get(('USA', 2019))
    if not us_cu:
        return None, []
    intensity = US_METAL_EXPLOSIVES_KT_2019 / (us_cu / 1000.0)     # kt explosive per kt Cu
    out = []
    for i3 in TEST:
        cu = prod.get((i3, 2024))
        if not cu:
            continue
        ceiling = (cu / 1000.0) * intensity
        imp = trade.get((i3, 2024), {}).get('360200', {}).get('t', 0) / 1000.0
        an = trade.get((i3, 2024), {}).get('310230', {}).get('t', 0) / 1000.0
        out.append({'iso': i3, 'name': NAMES.get(i3, i3), 'cu_kt': round(cu / 1000.0),
                    'ceiling_kt': round(ceiling), 'imp_3602_kt': round(imp, 1),
                    'imp_an_kt': round(an, 1),
                    'pct_of_ceiling': round(100.0 * imp / ceiling, 1) if ceiling else None})
    out.sort(key=lambda r: -(r['pct_of_ceiling'] or 0))
    return round(intensity, 3), out


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

    intensity, cov = coverage(trade, prod)
    world_3602_kt = round(sum(d.get('360200', {}).get('t', 0)
                              for (i3, y), d in trade.items() if y == 2024) / 1000.0)
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
        'coverage_gate': {
            'question': 'could imported explosives even be the input?',
            'intensity_kt_per_kt_cu': intensity,
            'intensity_source': ('USGS Minerals Yearbook 2019 table 3: US metal mining of every kind '
                                 'consumed 155 kt of explosives in 2019, divided by US contained '
                                 'copper that year, attributing every kilogram to copper - a '
                                 'deliberately generous CEILING'),
            'world_prepared_explosives_traded_kt_2024': world_3602_kt,
            'rows': cov,
            'verdict': ('world trade in prepared explosives is smaller than the consumption ceiling '
                        'of Chile alone, so explosives are not meaningfully traded: ANFO is mixed on '
                        'site and bulk emulsion is made at the mine gate. Trade data cannot measure '
                        'blasting.'),
        },
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
    print('  COVERAGE GATE: %.3f kt explosive per kt Cu (USGS-calibrated ceiling)' % intensity)
    print('  world prepared-explosives trade 2024: %d kt' % world_3602_kt)
    for r in cov:
        print('   %-12s %5d kt Cu | ceiling %5d kt | imported %6.1f kt = %5s%% of ceiling'
              % (r['name'], r['cu_kt'], r['ceiling_kt'], r['imp_3602_kt'], r['pct_of_ceiling']))
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
<title>Explosives don&rsquo;t travel &mdash; Critical Materials Atlas</title>
<meta name="description" content="World trade in prepared explosives was 445 kt in 2024 - less than Chile's copper mines alone consume. Explosives are mixed at the mine, not shipped, so trade data cannot measure blasting. Chile's apparently strong correlation rests on 0.4% of the flow.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style>@@CSS@@</style></head><body>
@@NAV@@
<section class="hero"><div class="wrap">
  <div class="eyebrow">Upstream &middot; a question answered by arithmetic, not regression</div>
  <h1>Explosives don&rsquo;t travel</h1>
  <p class="deck">Blasting sits further upstream than anything else this atlas tracks, so a
  bottleneck there would sit above <i>every</i> mined material at once. Whether trade data can see it
  turns out to be settled by one number. <b>World trade in prepared explosives was @@WORLD3602@@
  kilotonnes in 2024</b> &mdash; less than the consumption ceiling of <b>Chile&rsquo;s copper mines
  alone</b>. Explosives are mixed on site from ammonium nitrate and diesel, or made at the mine
  gate; what crosses a border is the feedstock, not the explosive. So the customs data cannot
  measure blasting, and the correlation this page originally reported was built on
  <b>0.4%</b> of the relevant flow.</p>
</div></section>

<section class="wrap xp">
  <h2>Could imported explosives even be the input?</h2>
  <p>This is the test that should come before any regression, and it is arithmetic. The intensity is
  calibrated on the USGS survey rather than an assumed engineering constant: US metal mining of
  every kind consumed 155 kt of explosives in 2019, and US copper mine output was 1,260 kt
  contained. Attributing <i>every kilogram</i> to copper &mdash; generous, since the same explosives
  blasted gold and iron &mdash; gives at most <b>@@INTENSITY@@ kt of explosive per kt of contained
  copper</b>. That makes the resulting figure a ceiling, so a country falling far below it fails
  conclusively rather than arguably.</p>
  <table><thead><tr><th>Country</th><th class="n">copper 2024</th>
  <th class="n">explosives ceiling</th><th class="n">prepared explosives imported</th>
  <th class="n">share of ceiling</th></tr></thead><tbody>@@COVROWS@@</tbody></table>
  <div class="corr"><b>Eight of ten import under 5% of what their mines must consume.</b> The
  explosives are made where they are used. That is not a data problem to work around; it is the
  physical fact that ANFO is two commodity inputs mixed in a truck at the pit.</div>
</section>

<section class="wrap xp">
  <h2>What that does to the correlation</h2>
  <p>The original version of this page reported that detonator imports track copper output in Chile,
  and that Chile was the one country whose confidence interval excluded zero. Both statements are
  still arithmetically true. Set beside the coverage test they invert.</p>
  <table><thead><tr><th>Country</th><th class="n">imports as share of ceiling</th>
  <th class="n">year-on-year r</th><th class="n">95% interval</th></tr></thead>
  <tbody>@@INVROWS@@</tbody></table>
  <div class="corr"><b>The country with the signal has almost no imports; the country with the
  imports has no signal.</b> Chile buys 0.4% of its prepared explosives abroad and shows r = +0.71.
  Peru buys about a third of its requirement abroad &mdash; the one case where the proxy is
  defensible &mdash; and shows +0.14, an interval straddling zero. A correlation computed on a 0.4%
  residual is measuring import substitution, not blasting.</div>
</section>

<section class="wrap xp">
  <h2>What explosives are actually used for</h2>
  <p>The one piece of this that stands on its own. United States, 2019, industrial explosives and
  blasting agents sold for consumption, thousand metric tons. The United States is the only country
  that surveys the end-use split, which is also why it cannot be turned into a global statement.</p>
  <table><thead><tr><th>Use</th><th class="n">kt</th><th class="n">share</th><th></th></tr></thead>
  <tbody>@@USEROWS@@</tbody></table>
  <div class="note"><b>Mining of all kinds is @@MINEPCT@@%, and within it coal is the bulk.</b> That
  supports the first half of the original argument. It does not license extending it: the United
  States is an unusually coal-heavy mining economy, and nothing here measures the mix anywhere else.
  The table also cannot settle the civil-military split, because military explosives are a separate
  survey and are not in it. Detonators sold for mining and quarrying <b>fell from @@DET15M@@ to
  @@DET19M@@ million units</b> between 2015 and 2019 while oil-and-gas detonators rose from
  @@DET15O@@ to @@DET19O@@ million.</div>
</section>

<section class="wrap xp">
  <h2>What was withdrawn, and why</h2>
  <div class="corr">
  <p>This page was published on 12 September 2026, reviewed adversarially by two independent
  language models run separately on the same brief, and rewritten twice. The first review found the
  claims below unsupported. The second was asked to improve the design rather than dismiss it, and
  its first instruction &mdash; test whether imports could be the input before estimating anything
  &mdash; produced the arithmetic at the top of this page, which is a better answer than the
  regression it replaced.</p>
  <ul>@@CORRS@@</ul>
  <p>The deepest error was never a statistical one. The original argument concerns explosives
  <b>prices</b> leading a supply surge; this page measured annual import <b>tonnage</b> of one
  customs code. It was not a test of that claim, and it should not have been presented as one.</p>
  </div>
</section>

<section class="wrap xp">
  <h2>What a real test would need</h2>
  <ul>
    <li><b>Consumption, not trade.</b> Domestic production plus imports minus exports. Without it
    the only observable countries are the ones that barely import, and they are not representative.</li>
    <li><b>Ammonium nitrate split by grade.</b> Blasting-grade and fertiliser-grade share one
    customs code, and 8.5 Mt of it trades annually against 0.44 Mt of prepared explosives.</li>
    <li><b>Unit counts, not tonnes.</b> Customs data reports mass, and in the detonator code the
    mass is dominated by detonating cord rather than by the caps that correspond to blast holes.</li>
    <li><b>Prices.</b> Nothing here touches one. Bulk blasting agents are ammonium nitrate, so their
    price is mostly an ammonia and gas price &mdash; a strong argument in itself against reading
    explosives prices as a clean mining signal.</li>
  </ul>
  <p class="howto-src"><b>Sources.</b> End use, detonator counts and the intensity calibration: USGS
  Minerals Yearbook 2019, <i>Explosives</i>, by Lori E. Apodaca, published March 2024, tables 2 and
  3; survey collected by the Institute of Makers of Explosives; PDF archived in the repository.
  Trade: CEPII BACI (Etalab Open Licence 2.0). Copper mine production: BGS World Mineral Statistics,
  mine stage only &mdash; the cube holds three organisations' estimates of the same quantity and
  summing them overstates Chile by half. Built by <code>build_explosives.py</code>; every figure,
  including the withdrawn claims, is in <code>out/explosives.json</code>.</p>
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

    gate = doc['coverage_gate']
    byiso = {r['iso']: r for r in rows}
    covrows = ''.join(
        '<tr><td>' + g['name'] + '</td><td class="n">' + format(g['cu_kt'], ',') +
        ' kt</td><td class="n">' + format(g['ceiling_kt'], ',') + ' kt</td><td class="n">' +
        format(g['imp_3602_kt'], '.1f') + ' kt</td><td class="n"><span class="' +
        ('pos' if (g['pct_of_ceiling'] or 0) >= 10 else 'neg') + '">' +
        format(g['pct_of_ceiling'] or 0, '.1f') + '%</span></td></tr>'
        for g in gate['rows'])
    invrows = ''.join(
        '<tr><td>' + g['name'] + '</td><td class="n">' + format(g['pct_of_ceiling'] or 0, '.1f') +
        '%</td><td class="n">' + rspan(byiso[g['iso']]['r_growth_tonnes'],
                                       byiso[g['iso']]['ci_growth']) +
        '</td><td class="n ci">' + ci(byiso[g['iso']]['ci_growth']) + '</td></tr>'
        for g in gate['rows'] if g['iso'] in byiso)

    corrs = ''.join('<li><span class="w">Withdrawn:</span> &ldquo;' + c['withdrawn'] +
                    '&rdquo; &mdash; ' + c['why'] + '.</li>' for c in doc['corrections'])
    det = doc['us_detonators']
    html = TEMPLATE
    for token, value in (
            ('CSS', CSS), ('NAV', NAV), ('FOOT', FOOT),
            ('MINEPCT', format(mine_pct, '.1f')), ('USEROWS', userows), ('TRS', trs),
            ('COVROWS', covrows), ('INVROWS', invrows), ('CORRS', corrs),
            ('WORLD3602', format(gate['world_prepared_explosives_traded_kt_2024'], ',')),
            ('INTENSITY', format(gate['intensity_kt_per_kt_cu'], '.3f')),
            ('DET15M', format(det[2015]['mining'] / 1e6, '.1f')),
            ('DET19M', format(det[2019]['mining'] / 1e6, '.1f')),
            ('DET15O', format(det[2015]['oilgas'] / 1e6, '.1f')),
            ('DET19O', format(det[2019]['oilgas'] / 1e6, '.1f'))):
        html = html.replace('@@' + token + '@@', value)
    return html


if __name__ == '__main__':
    main()
