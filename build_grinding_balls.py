# -*- coding: utf-8 -*-
"""Grinding balls don't track mining year by year: the published page for a pre-registered FAIL.

Reads out/grinding_balls.json (written by grinding-balls/gate.py and grinding-balls/throughput.py,
whose rules are in grinding-balls/PREREGISTRATION.md) and writes grinding.html. This builder only
presents; it computes nothing that decides the result.
"""
import io
import json
import math
import os

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
REPO = 'https://github.com/materials-atlas/critical-materials-atlas/blob/main/grinding-balls/'

NAMES = {
    'ARG': 'Argentina', 'AUS': 'Australia', 'BFA': 'Burkina Faso', 'BGR': 'Bulgaria', 'BOL': 'Bolivia',
    'BRA': 'Brazil', 'CAN': 'Canada', 'CHL': 'Chile', 'CHN': 'China', 'CIV': "C&ocirc;te d&rsquo;Ivoire",
    'COD': 'DR Congo', 'COL': 'Colombia', 'ECU': 'Ecuador', 'ESP': 'Spain', 'GHA': 'Ghana', 'GIN': 'Guinea',
    'IDN': 'Indonesia', 'IND': 'India', 'IRN': 'Iran', 'KAZ': 'Kazakhstan', 'MEX': 'Mexico', 'MLI': 'Mali',
    'MNG': 'Mongolia', 'PER': 'Peru', 'PHL': 'Philippines', 'PNG': 'Papua New Guinea', 'POL': 'Poland',
    'RUS': 'Russia', 'SAU': 'Saudi Arabia', 'SDN': 'Sudan', 'SRB': 'Serbia', 'SWE': 'Sweden',
    'TUR': 'T&uuml;rkiye', 'TZA': 'Tanzania', 'USA': 'United States', 'UZB': 'Uzbekistan', 'VEN': 'Venezuela',
    'ZAF': 'South Africa', 'ZMB': 'Zambia', 'ZWE': 'Zimbabwe',
}
TIER_LABEL = {'A': 'imports cover half or more', 'B': 'imports cover under half',
              'excluded': 'imports cover under a tenth', 'flagged': 'flagged'}

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
        '<div><h4>Sources</h4>CEPII BACI &middot; BGS World Mineral Statistics<br>USGS Minerals '
        'Yearbook &middot; mine technical reports</div>'
        '<div class="fineprint">Independent public-data research; figures approximate and '
        'rounded.</div></div></footer>')
CSS = """
.xp{max-width:60rem}
.xp table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
.xp th,.xp td{padding:.38rem .55rem;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top}
.xp td.n,.xp th.n{text-align:right;font-variant-numeric:tabular-nums}
.tA{color:#0e7c74;font-weight:600}.tB{color:#15323a}.tX{color:#8b857b}
.ok{color:#0e7c74;font-weight:700}.no{color:#b3384b;font-weight:700}
.note{background:#f7f7f5;border-left:3px solid #0e7c74;padding:.7rem 1rem;margin:1rem 0;font-size:.93rem}
.corr{background:#fdf6f2;border-left:3px solid #b3384b;padding:.8rem 1.1rem;margin:1.1rem 0;font-size:.93rem}
.corr li{margin:.35rem 0}
.verdict{display:inline-block;background:#b3384b;color:#fff;font-weight:700;letter-spacing:.08em;
 padding:.15rem .6rem;border-radius:4px;font-size:.8rem}
"""

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Grinding balls don&rsquo;t track mining year by year &mdash; Critical Materials Atlas</title>
<meta name="description" content="A pre-registered test of whether imports of steel grinding balls track how much ore a country mills. In the ten countries where imports cover at least half of what the mills need, they did not pass as a year-by-year proxy.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style>@@CSS@@</style></head><body>
@@NAV@@
<section class="hero"><div class="wrap">
  <div class="eyebrow">Upstream &middot; a pre-registered test that failed</div>
  <h1>Grinding balls don&rsquo;t track mining year by year</h1>
  <p class="deck">Mills grind ore with steel balls that wear away as the rock passes through, so a
  country that mills more ore should use more balls. If customs data could see that, it would be a
  public, near-real-time measure of mining activity. We wrote the rules of the test down first and
  then ran it. In the <b>@@NA@@ countries</b> where imports cover at least half of what the mills need, imports did not move
  with ore milled closely enough to use: the estimated response was <b>@@BETA@@</b> against an
  expected one-for-one, and it could not be told apart from zero.</p>
</div></section>

<section class="wrap xp">
  <h2>Result <span class="verdict">FAIL</span></h2>
  <p>Year-to-year growth in forged-ball imports (customs code 7326.11, tonnes, imports minus exports)
  against growth in ore milled, with country and year effects, @@Y0@@&ndash;@@Y1@@. Every threshold below
  was committed before the test ran.</p>
  <table><thead><tr><th>Check</th><th>Rule set in advance</th><th>Result</th><th></th></tr></thead>
  <tbody>@@CONDROWS@@</tbody></table>
  <div class="note"><b>In the long run the link is real.</b> Across years, countries that mill more ore
  do import more balls (with country and year effects: @@LEVELS@@). The rules said in advance that a
  relationship visible only in levels does not count, because it says nothing about whether imports
  follow mining from one year to the next, which is what a proxy has to do.</div>
</section>

<section class="wrap xp">
  <h2>What this does not say</h2>
  <ul>
    <li><b>Not that balls are unrelated to mining.</b> Several features of public data pull a
    year-to-year estimate toward zero. Ore milled has to be estimated from metal output with fixed
    global ore grades, so changes in grade, recovery or the share of ore that is leached rather than
    milled show up as noise. Mines buy balls in lumps and hold stock. Customs tonnages are noisy. For a
    true one-for-one response to appear as @@BETA@@, the noise in measured ore growth would need to be
    about twice its real variation, which is plausible for annual data.</li>
    <li><b>Nothing about Chile, Peru, Australia or Canada.</b> Their net imports cover well under half
    of what their mills are estimated to need (Chile, for one, has large domestic ball plants), so
    imports cannot stand for their mills, and they were never in the test.</li>
    <li><b>Nothing about ore grades.</b> The planned grade test needs a public series of the grade of
    ore entering the mills for one of the ten countries. None was found, so it was not run.</li>
  </ul>
</section>

<section class="wrap xp">
  <h2>Where imports could be the input</h2>
  <p>Before any regression, a coverage check: could a country&rsquo;s net ball imports physically
  supply its mills? Ball demand is ore milled times a consumption rate taken from @@NSRC@@ mine
  technical reports (copper 0.33&ndash;0.88, gold 0.46&ndash;1.01, lead-zinc 0.36&ndash;0.74 kg of steel
  per tonne of ore). Countries milling more than 20 Mt of ore in 2024; imports and demand averaged
  over 2022&ndash;24. A country enters the test if net imports cover at least half of mid-range demand.</p>
  <table><thead><tr><th>Country</th><th class="n">ore milled 2024</th><th class="n">ball demand</th>
  <th class="n">net imports</th><th class="n">coverage</th><th>group</th></tr></thead>
  <tbody>@@GATEROWS@@</tbody></table>
  <div class="note">Two known weak spots. Brazil&rsquo;s balls also grind iron ore, which is not
  counted, so Brazil looks better covered than it is. DR Congo&rsquo;s ore is rich and much of its
  copper is leached, not milled, so a fixed global grade overstates the rock it mills.</div>
</section>

<section class="wrap xp">
  <h2>How it was done, and reviewed</h2>
  <p>The design was drafted with two independent language models acting as advisors, and the rules,
  bands and controls were committed to the repository before any result existed: the
  <a href="@@REPO@@PREREGISTRATION.md">pre-registration</a>, with a dated log of every change made
  afterwards. Consumption rates come from primary mine reports, each with page and quotation
  (<a href="@@REPO@@intensity_sources.csv">sources</a>); cement output from seven editions of the USGS
  <i>Minerals Yearbook</i>.</p>
  <div class="corr">
  <p><b>Reviewed by one engine only.</b> This atlas&rsquo;s studies are normally reviewed adversarially
  by two independent language models run separately. For this result only one of the two was
  available; it was given the rules, the code and every number before publication. It found three
  errors; none changed the verdict:</p>
  <ul>
    <li>A failed control (Australia) had been written up as &ldquo;not counted&rdquo; after the result
    was seen. It is now reported as failed, with the reason it was unusable.</li>
    <li>The coverage check set net imports to zero after averaging three years instead of before, as
    the rules said. Corrected: Bulgaria moves up a group; the ten test countries are unchanged.</li>
    <li>Pass/fail was judged on rounded numbers. It now uses exact values; nothing changes.</li>
  </ul>
  </div>
  <p class="howto-src"><b>Sources.</b> Trade: CEPII BACI HS 2002, V202601 (Etalab Open Licence 2.0),
  with flows priced outside 0.4&ndash;3&times; the year&rsquo;s median dropped. Mine production: BGS
  World Mineral Statistics. Cement: USGS Minerals Yearbook, <i>Cement</i>, table 22. Consumption
  rates: mine technical reports listed in the sources file. Built by
  <code>build_grinding_balls.py</code> from <code>out/grinding_balls.json</code>, which holds every
  figure on this page.</p>
</section>
@@FOOT@@
</body></html>
"""


def fmt_p(p):
    return '&lt;0.001' if p < 0.001 else format(p, '.2f' if p >= 0.01 else '.3f')


def page(doc):
    t = doc['throughput_test']
    m, c = t['main'], t['conditions']
    loo = t['leave_one_out_beta']
    hr, pl, neg = t['horse_race_cement_2003_2023'], t['placebo_731815'], t['negative_control_australia']
    lv = t['robustness']['levels_with_fe']

    def res(ok):
        return '<span class="ok">pass</span>' if ok else '<span class="no">fail</span>'

    conds = [
        ('Imports follow ore milled', 'response between 0.4 and 1.5, p &lt; 0.05',
         'response %.2f (95%% interval %.2f to %.2f), p = %s' % (m['beta'], m['ci95_cluster'][0],
                                                               m['ci95_cluster'][1], fmt_p(m['p_cluster'])),
         c['1_beta_in_band_and_significant']),
        ('Not driven by one country', 'dropping any one country keeps it between 0.3 and 1.7',
         'ranges %.2f to %.2f' % (min(loo.values()), max(loo.values())), c['2_leave_one_out_in_band']),
        ('Not cement', 'still in band with cement output added, and stronger than cement',
         'response %.2f; cement shows no link (t = %.2f)' % (hr['beta'], hr['t_cement']),
         c['3_horse_race_cement']),
        ('Placebo: screws and bolts', 'no link to ore milled',
         'response %.2f, p = %s' % (pl['beta'], fmt_p(pl['p_cluster'])), c['4_placebo_731815_fails']),
        ('Australia: iron ore', 'iron ore, which is not milled, shows no link',
         'failed on only %d years: Australia exported more balls than it imported until 2017' % neg['n'],
         c['5_australia_iron_ore_ci_includes_zero']),
    ]
    condrows = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (a, b, r, res(ok))
                       for a, b, r, ok in conds)

    cls = {'A': 'tA', 'B': 'tB'}

    def kt(v):
        return format(v, '.1f') if v < 10 else format(v, '.0f')

    # coverage is rounded DOWN so a country just under the one-half line never reads as 50%
    gaterows = ''.join(
        '<tr><td>%s</td><td class="n">%s Mt</td><td class="n">%.0f kt</td><td class="n">%s kt</td>'
        '<td class="n">%d%%</td><td class="%s">%s</td></tr>' % (
            NAMES.get(r['iso3'], r['iso3']), format(round(r['ore_milled_2024_mt']), ','),
            r['ball_demand_kt']['mid'], kt(r['apparent_consumption_kt']),
            math.floor(100 * (r['ratio_to_mid'] or 0) + 1e-9),
            cls.get(r['tier'], 'tX'), TIER_LABEL[r['tier']])
        for r in doc['countries'])

    with io.open(os.path.join(ROOT, 'grinding-balls', 'intensity_sources.csv'), encoding='utf-8') as f:
        nsrc = sum(1 for _ in f) - 1

    html = TEMPLATE
    for token, value in (
            ('CSS', CSS), ('NAV', NAV), ('FOOT', FOOT), ('REPO', REPO),
            ('NA', str(doc['tier_counts']['A'])), ('BETA', format(m['beta'], '.2f')),
            ('Y0', str(t['years'][0])), ('Y1', str(t['years'][1])),
            ('CONDROWS', condrows), ('GATEROWS', gaterows), ('NSRC', str(nsrc)),
            ('LEVELS', 'response %.2f, p = %s' % (lv['beta'], fmt_p(lv['p_cluster'])))):
        html = html.replace('@@' + token + '@@', value)
    assert '@@' not in html, 'unfilled token'
    return html


def main():
    doc = json.load(io.open(os.path.join(ROOT, 'out', 'grinding_balls.json'), encoding='utf-8'))
    assert doc['throughput_test']['result'] == 'FAIL', 'page text is written for the FAIL result'
    io.open(os.path.join(ROOT, 'grinding.html'), 'w', encoding='utf-8', newline='\n').write(page(doc))
    print('grinding.html written')


if __name__ == '__main__':
    main()
