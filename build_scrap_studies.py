# -*- coding: utf-8 -*-
"""Does scrap answer price? The two pre-registered scrap studies on one page.

Reads out/scrap_response.json, out/scrap_response_per_metal.json and out/scrap_trade.json, written by
scrap-response/response.py, scrap-response/per_metal.py and scrap-trade/flows.py. Every figure on the
page comes from those files; the exploratory regressions in the filings are described, not quoted,
because they are not in them.

Writes scrap.html.  Usage: python build_scrap_studies.py
"""
import io
import json
import math
import os

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
OUT_HTML = os.path.join(ROOT, 'scrap.html')
REPO = 'https://github.com/materials-atlas/critical-materials-atlas/blob/main/'
HALF = math.log(1.5)                                  # the filings read a +50% real price rise

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
        '<div><h4>Sources</h4>USGS historical statistics (DS 140) &middot; World Bank Pink Sheet'
        '<br>CEPII BACI</div>'
        '<div class="fineprint">Independent public-data research; figures approximate and '
        'rounded.</div></div></footer>')
CSS = """
.xp{max-width:60rem}
.xp table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
.xp th,.xp td{padding:.38rem .55rem;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top}
.xp td.n,.xp th.n{text-align:right;font-variant-numeric:tabular-nums}
.tbl{overflow-x:auto}
.note{background:#f7f7f5;border-left:3px solid #0e7c74;padding:.7rem 1rem;margin:1rem 0;font-size:.93rem}
.dim{color:#6b675f}
.verdict{display:inline-block;background:#15323a;color:#fff;font-weight:700;letter-spacing:.08em;
 padding:.15rem .6rem;border-radius:4px;font-size:.8rem}
"""

# The per-metal readings as the filings word them.
RECOVERY_READING = {'not_shown_to_respond': 'not shown to respond',
                    'untestable_at_0.2': 'untestable at 0.2'}
TRADE_READING = {'follows_price_strongly': 'moves with price', 'follows_price_modestly': 'modest',
                 'untestable_at_0.2': 'untestable'}
# scrap-trade deviation 2: tin is reported but not read (nine exporters; the estimate is about the
# size of the smallest effect they could detect).
TRADE_NOT_READ = {'tin'}


def load(name):
    with io.open(os.path.join(ROOT, 'out', name), encoding='utf-8') as f:
        return json.load(f)


def word(n):
    return {2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight',
            9: 'nine'}.get(n, str(n))


def sgn(x, nd=2):
    return ('%+.' + str(nd) + 'f') % x


def pv(p):
    return '&lt;0.001' if p < 0.001 else '%.2f' % p if p >= 0.01 else '%.3f' % p


def page():
    R, M, T = load('scrap_response.json'), load('scrap_response_per_metal.json'), load('scrap_trade.json')

    # study 1, pooled: share of consumption, points per +50% real price over two years
    hy = R['headline']['with_year_effects']['share']
    pooled = {'est': hy['cumulative'] * HALF, 'lo': hy['ci95'][0] * HALF, 'hi': hy['ci95'][1] * HALF,
              'p': hy['p'], 'mde': hy['mde_80pct_power'] * HALF, 'n': hy['n'], 'k': hy['materials']}
    sh = R['secondary_share_by_material']

    # study 1, per metal (Amendment A)
    order = sorted(M['metals'], key=lambda m: M['metals'][m]['pink']['elasticity']['mde_80pct_power'])
    rec_rows, testable = [], []
    for m in order:
        e = M['metals'][m]['pink']['elasticity']
        uv = M['metals'][m]['unit_value']['elasticity']['cumulative']
        rd = M['metals'][m]['pink']['reading']
        assert rd in RECOVERY_READING, rd
        if rd == 'not_shown_to_respond':
            testable.append(m)
        rec_rows.append('<tr><td>%s</td><td class="n">%s</td><td class="n">%s to %s</td><td class="n">%s</td>'
                        '<td class="n">%.2f</td><td class="n">%s</td><td>%s</td></tr>'
                        % (m.capitalize(), sgn(e['cumulative']), sgn(e['ci95'][0]), sgn(e['ci95'][1]), pv(e['p']),
                           e['mde_80pct_power'], sgn(uv), RECOVERY_READING[rd]))
    am = M['across_metals']['pink']
    thr = M['threshold_elasticity']
    tst = ' and '.join(testable)
    tst_share = ' and '.join('%s %d%%' % (m, round(sh[m]['median_secondary_share_pct'])) for m in testable)
    tst_mde = ' and '.join('%.2f' % M['metals'][m]['pink']['elasticity']['mde_80pct_power'] for m in testable)

    # study 2, trade
    tw = T['headline']['without_year_effects']
    ty = T['headline']['with_year_effects']
    fw, lw = tw['fit'], tw['lagged_only']
    tr_rows = []
    for m, v in sorted(T['checks']['by_metal'].items(), key=lambda kv: -kv[1]['countries']):
        rd = 'not reliable' if m in TRADE_NOT_READ else TRADE_READING.get(v['reading'], v['reading'].replace('_', ' '))
        tr_rows.append('<tr><td>%s</td><td class="n">%s</td><td class="n">%s to %s</td><td class="n">%s</td>'
                       '<td class="n">%.2f</td><td class="n">%d</td><td>%s</td></tr>'
                       % (m.capitalize(), sgn(v['cumulative']), sgn(v['ci95'][0]), sgn(v['ci95'][1]), pv(v['p']),
                          v['mde'], v['countries'], rd))
    imp = T['checks']['imports_as_dv']['without_year_effects']['cumulative']
    pl = T['checks']['placebo_future_prices']

    tok = {
        'CSS': CSS, 'NAV': NAV, 'FOOT': FOOT, 'REPO': REPO,
        'Y0': str(M['window'][0]), 'Y1': str(M['window'][1]),
        'PY0': str(R['window'][0]), 'PY1': str(R['window'][1]),
        'NMAT': str(len(R['materials'])), 'PK': str(pooled['k']), 'PN': '{:,}'.format(pooled['n']),
        'PEST': sgn(pooled['est']), 'PLO': sgn(pooled['lo']), 'PHI': sgn(pooled['hi']),
        'PP': pv(pooled['p']), 'PMDE': '%.1f' % pooled['mde'],
        'NMET': str(len(M['metals'])), 'THR': '%.1f' % thr, 'RECROWS': '\n'.join(rec_rows),
        'TST': tst, 'TSTC': tst[:1].upper() + tst[1:], 'TSTSHARE': tst_share, 'TSTMDE': tst_mde,
        'AMEAN': sgn(am['mean_cumulative']), 'ALO': sgn(am['ci95'][0]), 'AHI': sgn(am['ci95'][1]),
        'TY0': str(T['years'][0]), 'TY1': str(T['years'][1]),
        'TPAIRS': str(T['pairs_headline']), 'TCTY': str(T['countries_headline']),
        'TCUM': sgn(fw['cumulative']), 'TLO': sgn(fw['ci95'][0]), 'THI': sgn(fw['ci95'][1]),
        'TSAME': sgn(fw['per_lag']['dp0']['beta']), 'TLAG': sgn(lw['cumulative']), 'TLAGP': pv(lw['p']),
        'TLAGMDE': '%.2f' % lw['mde_80pct_power'],
        'TYCUM': sgn(ty['fit']['cumulative']), 'TYP': pv(ty['fit']['p']),
        'TIMP': sgn(imp), 'TPL': sgn(pl['cumulative']), 'TPLP': pv(pl['p']),
        'TRROWS': '\n'.join(tr_rows),
        'NUNT': word(len(M['metals']) - len(testable)), 'NMETW': word(len(M['metals'])),
        'TINN': word(T['checks']['by_metal']['tin']['countries']), 'TNMET': word(len(T['headline_metals'])),
    }
    html = TEMPLATE
    for k, v in tok.items():
        html = html.replace('@@%s@@' % k, v)
    return html


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Does scrap answer price? &mdash; Critical Materials Atlas</title>
<meta name="description" content="Two pre-registered tests of whether recycled metal responds to price, on seventy years of US data and on world scrap trade: nothing is shown in the two years after a price rise.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style>@@CSS@@</style></head><body>
@@NAV@@
<section class="hero"><div class="wrap">
  <div class="eyebrow">Secondary supply &middot; two pre-registered tests</div>
  <h1>Does scrap answer price?</h1>
  <p class="deck">A common hope in critical-materials policy is that when a metal gets expensive,
  recycling fills part of the gap. We tested it twice, each time filing the design before running it:
  on US recovery of scrap, and on world trade in scrap. <b>Neither shows more recycled metal in the two
  years after a price rise.</b> Where the data were good enough to see a response of the size that
  would matter, it was not there.</p>
</div></section>

<section class="wrap xp">
  <h2>1. Does US recovery of scrap rise after prices do?</h2>
  <p><span class="verdict">NOT SHOWN</span></p>
  <p>The first design pooled @@NMAT@@ metals from the US Geological Survey&rsquo;s historical statistics,
  @@PY0@@&ndash;@@PY1@@, and asked whether scrap-derived supply, as a share of US consumption, rises in the
  two years after a 50% real price rise. On @@PN@@ metal-years over @@PK@@ metals, the answer was
  @@PEST@@ points of consumption (95% interval @@PLO@@ to @@PHI@@, p&nbsp;=&nbsp;@@PP@@). But the smallest
  response this design could reliably detect was @@PMDE@@ points, and the filing had said 1 point
  would matter. So that first result could not tell a useful response from none, and we said so.</p>
  <p>A second design, filed before it was run, took each metal on its own, @@Y0@@&ndash;@@Y1@@, on
  World Bank market prices, and asked whether a metal&rsquo;s scrap tonnes rise by at least @@THR@@% per 1%
  of price within two years. Each metal is reported with the smallest response its own series could
  have seen; a metal that could not see @@THR@@ is called untestable, not a null.</p>
  <div class="tbl"><table><thead><tr><th>Metal</th><th class="n">two-year elasticity</th>
  <th class="n">95% interval</th><th class="n">p</th><th class="n">smallest it could see</th>
  <th class="n">on USGS unit values</th><th>reading</th></tr></thead>
  <tbody>@@RECROWS@@</tbody></table></div>
  <p><b>@@TSTC@@ could have seen a response at the filed threshold, and show none.</b> Their series could
  detect @@TSTMDE@@; both estimates are close to zero and their intervals exclude @@THR@@. These are the
  metals where recycling is already largest (median share of US consumption from scrap:
  @@TSTSHARE@@). Across all @@NMETW@@ metals the mean response is @@AMEAN@@ (95% interval @@ALO@@ to
  @@AHI@@). Using a unit value instead of a market price changes no reading.</p>
  <div class="note">One exploratory result, not filed and not built on: after a price rise, the
  recycled <i>share</i> of consumption rose for aluminium and lead while recycled <i>tonnes</i> did not.
  Unfiled regressions on the same data suggest the reason is that consumption fell. If so, a higher
  share would mean less demand, not more recycling. It is a hypothesis for a separate test on other
  countries; the figures are in the <a href="@@REPO@@scrap-response/PREREGISTRATION.md">filing</a>.</div>
</section>

<section class="wrap xp">
  <h2>2. Does scrap trade follow price?</h2>
  <p><span class="verdict">SAME YEAR ONLY</span></p>
  <p>If recovery does not rise, scrap might still move: collected in one country and shipped to where
  prices pay. The second study took world trade in @@TNMET@@ metals&rsquo; scrap from CEPII BACI,
  @@TY0@@&ndash;@@TY1@@, for @@TPAIRS@@ country&ndash;metal pairs among the small exporters of each
  (@@TCTY@@ countries), with the same two-year shape.</p>
  <p>Scrap exports rise with price by @@TCUM@@% per 1% (95% interval @@TLO@@ to @@THI@@), but
  <b>all of it is in the same year</b> (@@TSAME@@% per 1%). The two following years add nothing: @@TLAG@@
  (p&nbsp;=&nbsp;@@TLAGP@@), where the design could have seen @@TLAGMDE@@. Within a year prices and
  shipments are set together, so this is movement with the cycle, not a demonstrated supply response.
  Imports of the same scrap rise too (@@TIMP@@% per 1%), which is what a boom that lifts everything looks
  like, not scrap being redirected. Once the common cycle is removed with year effects, the estimate
  (@@TYCUM@@, p&nbsp;=&nbsp;@@TYP@@) swings from year to year in a way the filing said would disqualify it,
  and it is not claimed. A placebo on future prices shows nothing (@@TPL@@, p&nbsp;=&nbsp;@@TPLP@@).</p>
  <div class="tbl"><table><thead><tr><th>Scrap of</th><th class="n">elasticity, same year + two</th>
  <th class="n">95% interval</th><th class="n">p</th><th class="n">smallest it could see</th>
  <th class="n">exporters</th><th>reading</th></tr></thead>
  <tbody>@@TRROWS@@</tbody></table></div>
  <p class="dim">Without year effects, so every row carries the common cycle. Tin rests on @@TINN@@
  exporters and an estimate about the size of the smallest they could detect, so it is not read.</p>
</section>

<section class="wrap xp">
  <h2>What the two say together</h2>
  <p>As far as open data can see, both sides of the scrap system move with price within the year, and
  neither is shown to move in the two years afterwards. No evidence was found that a price rise
  brings a growing stream of recycled metal, whether by recovering more of it or by moving it.</p>
  <p>That is narrower than &ldquo;recycling does not respond to price&rdquo;. It is US recovery and
  world trade only; the tests are predictive, not causal; @@NUNT@@ of the @@NMETW@@ metals in the first study
  cannot see the threshold at all; and nothing here covers the newer critical materials, which have
  no such series. For a policy that counts on scrap to cushion a price shock within a couple of years,
  it is still the relevant evidence: on the metals where it can be checked, it did not.</p>
  <p class="howto-src"><b>Filings and code.</b> Each design was committed before its first run and each
  deviation is logged with its date:
  <a href="@@REPO@@scrap-response/PREREGISTRATION.md">scrap recovery</a> (with Amendment A, the per-metal
  design) and <a href="@@REPO@@scrap-trade/PREREGISTRATION.md">scrap trade</a>.
  <b>Sources.</b> US Geological Survey, historical statistics for mineral and material commodities
  (DS&nbsp;140); World Bank commodity prices (Pink Sheet); CEPII BACI, release V202601 (Etalab Open
  Licence 2.0). Built by <code>build_scrap_studies.py</code> from <code>out/scrap_response.json</code>,
  <code>out/scrap_response_per_metal.json</code> and <code>out/scrap_trade.json</code>.</p>
</section>
@@FOOT@@
</body></html>
"""


def main():
    html = page()
    assert '@@' not in html, 'unfilled token'
    with io.open(OUT_HTML, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    print('wrote', OUT_HTML)


if __name__ == '__main__':
    main()
