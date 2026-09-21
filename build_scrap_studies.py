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
.tag{font-size:.72rem;background:#eef2f1;color:#15323a;padding:.05rem .35rem;border-radius:3px;white-space:nowrap}
.src{font-size:.78rem;color:#6b7478;margin:-.1rem 0 1rem;line-height:1.5}.src code{font-size:.74rem}
.fig{margin:1.2rem 0}.fig svg{width:100%;height:auto;display:block}
.fig figcaption{font-size:.86rem;color:#5a6468;margin-top:.4rem;max-width:44rem}
.fig .grid{stroke:#e3e6e5;stroke-width:1}.fig .zero{stroke:#8b9396;stroke-width:1}
.fig .thr{stroke:#b3384b;stroke-width:1;stroke-dasharray:3 3}.fig .thrlab{fill:#b3384b}
.fig .reach{stroke:#e8e6e1;stroke-width:12;stroke-linecap:round}
.fig .ci{stroke-width:2.5;opacity:.55}.fig .dot{stroke:#fcfcfb;stroke-width:2}
.fig .ax{font:11px Inter,system-ui,sans-serif;fill:#5a6468}
.fig .ax.row{font-size:12px;fill:#15323a}.fig .val{font-weight:600;fill:#15323a}
.fig .lagbar{fill:#15323a}.fig .sharebar{fill:#009287}
.cite{font-size:.72rem}.cite a{text-decoration:none}
.refs{max-width:46rem;padding-left:1.1rem}.refs li{margin:.45rem 0;font-size:.9rem;line-height:1.55}
.xp h3{margin-top:1.6rem;font-size:1.02rem}
.verdict{display:inline-block;background:#15323a;color:#fff;font-weight:700;letter-spacing:.08em;
 padding:.15rem .6rem;border-radius:4px;font-size:.8rem}
"""

# Literature, assembled 2026-09-20 under the atlas's rule that every source is opened before use.
REFS = [
    ('Soderholm2019',
     'S&ouml;derholm, P. and Ekvall, T. (2020). "Metal markets and recycling policies: impacts and '
     'challenges." <i>Mineral Economics</i> 33(1&ndash;2): 257&ndash;272 (published online 2019).',
     'https://doi.org/10.1007/s13563-019-00184-5'),
    ('Blomberg2009',
     'Blomberg, J. and S&ouml;derholm, P. (2009). "The economics of secondary aluminium supply: an '
     'econometric analysis based on European data." <i>Resources, Conservation and Recycling</i> '
     '53(8): 455&ndash;463.', 'https://doi.org/10.1016/j.resconrec.2009.03.001'),
    ('Fu2017',
     'Fu, X., Ueland, S. M. and Olivetti, E. (2017). "Econometric modeling of recycled copper supply." '
     '<i>Resources, Conservation and Recycling</i> 122: 219&ndash;226.',
     'https://doi.org/10.1016/j.resconrec.2017.02.012'),
    ('Sibley2011',
     'Sibley, S. F. (2011). "Overview of flow studies for recycling metal commodities in the United '
     'States." US Geological Survey Circular 1196-AA.', 'https://pubs.usgs.gov/circ/circ1196-AA/'),
    ('Ryter2021',
     'Ryter, J., Fu, X., Bhuwalka, K., Roth, R. and Olivetti, E. A. (2021). "Emission impacts of '
     "China's solid waste import ban and COVID-19 in the copper supply chain.\" <i>Nature "
     'Communications</i> 12: 3753.', 'https://doi.org/10.1038/s41467-021-23874-7'),
    ('Ioannidis2017',
     'Ioannidis, J. P. A., Stanley, T. D. and Doucouliagos, H. (2017). "The power of bias in economics '
     'research." <i>The Economic Journal</i> 127(605): F236&ndash;F265.',
     'https://doi.org/10.1111/ecoj.12461'),
    ('Kelly2014',
     'Kelly, T. D. and Matos, G. R., comps. (2014). <i>Historical statistics for mineral and material '
     'commodities in the United States</i>. US Geological Survey Data Series 140.',
     'https://www.usgs.gov/centers/national-minerals-information-center/'
     'historical-statistics-mineral-and-material-commodities'),
    ('WorldBank2026',
     'World Bank (2026). <i>World Bank Commodities Price Data (The Pink Sheet)</i>, with its '
     '"Description of Price Series" annex. Prospects Group, Washington, DC.',
     'https://www.worldbank.org/en/research/commodity-markets'),
    ('Gaulier2010',
     'Gaulier, G. and Zignago, S. (2010). "BACI: International Trade Database at the Product-Level." '
     'CEPII Working Paper 2010-23.', 'https://www.cepii.fr/pdf_pub/wp/2010/wp2010-23.pdf'),
    ('Silver2007',
     'Silver, M. (2007). "Do unit value export, import, and terms of trade indices represent or '
     'misrepresent price indices?" IMF Working Paper WP/07/121.',
     'https://www.imf.org/en/Publications/WP/Issues/2016/12/31/'
     'Do-Unit-Value-Export-Import-and-Terms-of-Trade-Indices-Represent-or-Misrepresent-Price-20943'),
    ('Gaulier2008',
     'Gaulier, G., Martin, J., M&eacute;jean, I. and Zignago, S. (2008). "International trade price '
     'indices." CEPII Working Paper 2008-10.', 'https://www.cepii.fr/baci_data/tradeprices_wp.pdf'),
]
REFNUM = {k: i + 1 for i, (k, _, _) in enumerate(REFS)}


def cite(*keys):
    return ('<sup class="cite">[%s]</sup>'
            % ','.join('<a href="#ref-%s">%d</a>' % (k, REFNUM[k]) for k in keys))


GH = 'https://github.com/materials-atlas/critical-materials-atlas/blob/main/'
# Where each table and figure comes from: the raw source, then the file holding the computed numbers.
SOURCES = {
    'usgs': ('US Geological Survey, historical statistics (DS 140)',
             'https://www.usgs.gov/centers/national-minerals-information-center/'
             'historical-statistics-mineral-and-material-commodities'),
    'pink': ('World Bank commodity prices (Pink Sheet)',
             'https://www.worldbank.org/en/research/commodity-markets'),
    'baci': ('CEPII BACI, release V202601',
             'https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37'),
}
RESULTS = {'pooled': 'out/scrap_response.json', 'per_metal': 'out/scrap_response_per_metal.json',
           'trade': 'out/scrap_trade.json', 'extras': 'out/scrap_trade_extras.json'}


def src(sources, results, note=''):
    a = ' &middot; '.join('<a href="%s">%s</a>' % (SOURCES[k][1], SOURCES[k][0]) for k in sources)
    b = ', '.join('<a href="%s%s"><code>%s</code></a>' % (GH, RESULTS[k], RESULTS[k]) for k in results)
    return ('<p class="src"><b>Source:</b> %s. Computed values: %s.%s</p>'
            % (a, b, (' ' + note) if note else ''))


# The per-metal readings as the filings word them.
RECOVERY_READING = {'not_shown_to_respond': 'not shown to respond',
                    'untestable_at_0.2': 'untestable at 0.2'}
# The trade study's stored readings were decided on p-values; its own power rule says an estimate
# smaller than what the design could reliably detect is not read (scrap-trade deviation 4, and the
# rule the companion study filed). The page applies that rule to every metal, so nickel and tin are
# not read as responses even though their p-values are below 0.05.
def trade_reading(v):
    if abs(v['cumulative']) >= v['mde']:
        return 'same-year comovement; lags not shown'
    if v['p'] < 0.05:
        return 'positive, but below the filed power bar, so not read'
    return 'not distinguishable from zero'


# Validated for colour-vision separation against the page surface (dataviz validator, 20 Sep 2026).
CAN_SEE, CANNOT = '#009287', '#7d5ba6'


def ci_chart(rows, lo, hi, step, title, threshold=None, W=720, rh=30,
             legend=('can see the threshold', 'cannot')):
    """One row per metal: estimate, its 95% interval, and the smallest effect it could detect."""
    L, R, T = 190, 24, 34
    H = T + rh * len(rows) + 34

    def x(v):
        return L + (min(max(v, lo), hi) - lo) / float(hi - lo) * (W - L - R)
    g = []
    t = lo
    while t <= hi + 1e-9:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%.1f" class="%s"/>'
                 % (x(t), x(t), T - 10, H - 30, 'zero' if abs(t) < 1e-9 else 'grid'))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%s</text>'
                 % (x(t), H - 12, ('%+.1f' % t) if t else '0'))
        t = round(t + step, 10)
    if threshold is not None:
        for v in (threshold, -threshold):
            if lo <= v <= hi:
                g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%.1f" class="thr"/>' % (x(v), x(v), T - 10, H - 30))
        g.append('<text x="%.1f" y="%d" class="ax thrlab" text-anchor="middle">filed threshold %.1f</text>'
                 % (x(threshold), T - 18, threshold))
    for i, (label, est, clo, chi, mde, can) in enumerate(rows):
        y = T + rh * i + 10
        col = CAN_SEE if can else CANNOT
        g.append('<text x="0" y="%.1f" class="ax row">%s</text>' % (y + 4, label))
        # the blind spot: everything inside this band is too small for the design to tell from zero
        g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="reach"/>' % (x(-mde), x(mde), y, y))
        g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="ci" stroke="%s"/>'
                 % (x(clo), x(chi), y, y, col))
        g.append('<circle cx="%.1f" cy="%.1f" r="5" class="dot" fill="%s"><title>%s: %+.2f (%+.2f to %+.2f), '
                 'a response smaller than %.2f would not have been detected with 80%% certainty</title></circle>'
                 % (x(est), y, col, label, est, clo, chi, mde))
    w0 = 26 + 6 * len(legend[0])
    leg = ('<circle cx="%d" cy="%d" r="5" fill="%s"/><text x="%d" y="%d" class="ax">%s</text>'
           '<circle cx="%d" cy="%d" r="5" fill="%s"/><text x="%d" y="%d" class="ax">%s</text>'
           '<line x1="%d" x2="%d" y1="%d" y2="%d" class="reach"/><text x="%d" y="%d" class="ax">not detectable with 80%% certainty</text>'
           % (6, 12, CAN_SEE, 16, 16, legend[0], w0, 12, CANNOT, w0 + 10, 16, legend[1],
              w0 + 24 + 6 * len(legend[1]), w0 + 54 + 6 * len(legend[1]), 12, 12,
              w0 + 60 + 6 * len(legend[1]), 16))
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s%s</svg>' % (W, H, title, leg, ''.join(g))


def lag_chart(terms, title, W=720, H=210):
    """The shape of the response in time: same year, one year later, two years later."""
    L, R, T, B = 60, 20, 24, 40
    vals = [v for _, v, _ in terms]
    hi = max(0.6, max(vals) * 1.15)
    lo = min(-0.2, min(vals) * 1.15)
    bw = (W - L - R) / float(len(terms))

    def y(v):
        return T + (hi - v) / (hi - lo) * (H - T - B)
    g = []
    for t in (-0.2, 0.0, 0.2, 0.4, 0.6):
        if lo <= t <= hi:
            g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="%s"/>'
                     % (L, W - R, y(t), y(t), 'zero' if abs(t) < 1e-9 else 'grid'))
            g.append('<text x="%d" y="%.1f" class="ax" text-anchor="end">%+.1f</text>' % (L - 6, y(t) + 4, t))
    for i, (lab, v, pv) in enumerate(terms):
        X = L + i * bw + bw * 0.22
        top, bot = (y(max(v, 0)), y(min(v, 0)))
        g.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" class="lagbar"><title>%s: %+.2f, p %s</title></rect>'
                 % (X, top, bw * 0.56, max(bot - top, 1), lab, v, pv))
        g.append('<text x="%.1f" y="%.1f" class="ax val" text-anchor="middle">%+.2f</text>'
                 % (X + bw * 0.28, top - 6 if v >= 0 else bot + 14, v))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%s</text>' % (X + bw * 0.28, H - B + 20, lab))
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>' % (W, H, title, ''.join(g))


def share_chart(pairs, title, W=720, rh=22):
    """How much of US consumption each metal already gets from scrap."""
    L, R, T = 190, 40, 14
    H = T + rh * len(pairs) + 26
    hi = max(v for _, v in pairs)
    hi = 10 * (int(hi / 10) + 1)

    def x(v):
        return L + v / float(hi) * (W - L - R)
    g = []
    for t in range(0, hi + 1, 10):
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%.1f" class="grid"/>' % (x(t), x(t), T, H - 22))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%d%%</text>' % (x(t), H - 6, t))
    for i, (lab, v) in enumerate(pairs):
        y = T + rh * i + 4
        g.append('<text x="0" y="%.1f" class="ax row">%s</text>' % (y + 11, lab))
        g.append('<rect x="%d" y="%.1f" width="%.1f" height="12" rx="3" class="sharebar"><title>%s: a median of %.1f%% of US consumption over the study years</title></rect>'
                 % (L, y + 2, max(x(v) - L, 1), lab, v))
        g.append('<text x="%.1f" y="%.1f" class="ax val">%.0f%%</text>' % (x(v) + 6, y + 12, v))
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>' % (W, H, title, ''.join(g))


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
    qy = R['headline']['without_year_effects']['share']

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
        rd = trade_reading(v)
        tr_rows.append('<tr><td>%s</td><td class="n">%s</td><td class="n">%s to %s</td><td class="n">%s</td>'
                       '<td class="n">%.2f</td><td class="n">%d</td><td>%s</td></tr>'
                       % (m.capitalize(), sgn(v['cumulative']), sgn(v['ci95'][0]), sgn(v['ci95'][1]), pv(v['p']),
                          v['mde'], v['countries'], rd))
    rec_fig_rows = [(m.capitalize(), M['metals'][m]['pink']['elasticity']['cumulative'],
                 M['metals'][m]['pink']['elasticity']['ci95'][0], M['metals'][m]['pink']['elasticity']['ci95'][1],
                 M['metals'][m]['pink']['elasticity']['mde_80pct_power'],
                 M['metals'][m]['pink']['reading'] == 'not_shown_to_respond') for m in order]
    rec_fig = ci_chart(rec_fig_rows, -0.8, 0.8, 0.4,
                       'Two-year response of US scrap recovery to price, by metal, with 95% intervals and '
                       'the smallest response each metal could detect', threshold=thr)
    tr_order = sorted(T['checks']['by_metal'], key=lambda m: -T['checks']['by_metal'][m]['countries'])
    tr_rows_fig = [(m.capitalize(), T['checks']['by_metal'][m]['cumulative'],
                    T['checks']['by_metal'][m]['ci95'][0], T['checks']['by_metal'][m]['ci95'][1],
                    T['checks']['by_metal'][m]['mde'],
                    abs(T['checks']['by_metal'][m]['cumulative']) > T['checks']['by_metal'][m]['mde'])
                   for m in tr_order]
    tr_fig = ci_chart(tr_rows_fig, -3.5, 5.5, 1.0,
                      'Response of scrap exports to price, same year and two years, by metal, with '
                      '95% intervals and the smallest response each could detect',
                      legend=('estimate above its detectable size', 'estimate below it'))
    pl = fw['per_lag']
    lag_fig = lag_chart([('same year', pl['dp0']['beta'], pv(pl['dp0']['p'])),
                         ('one year later', pl['dp1']['beta'], pv(pl['dp1']['p'])),
                         ('two years later', pl['dp2']['beta'], pv(pl['dp2']['p']))],
                        'The response of scrap exports to price by year: all of it is in the same year')
    share_pairs = sorted(((m.capitalize(), sh[m]['median_secondary_share_pct'])
                          for m in sh if m in M['metals'] or sh[m]['median_secondary_share_pct'] >= 19),
                         key=lambda kv: -kv[1])[:10]
    share_fig = share_chart(share_pairs,
                            'Median share of US consumption met by scrap, by metal, over the study years')

    def chk(label, d, fmt='%+.2f', scale=1.0, note=''):
        return ('<tr><td>%s</td><td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>'
                % (label, fmt % (d['cumulative'] * scale), pv(d['p']), note))
    RC = R['checks']
    rec_checks = ''.join([
        chk('Primary (newly mined) supply, same equation <span class="tag">elasticity of primary tonnes, '
            'not points</span>', RC['primary_supply']['with_year_effects'],
            note='a weak positive estimate, interval %+.2f to %+.2f; not conclusive, and its difference '
                 'from the scrap estimate was never tested'
                 % tuple(RC['primary_supply']['with_year_effects']['ci95'])),
        chk('Placebo: future prices', RC['placebo_future_prices']['with_year_effects'], scale=HALF,
            fmt='%+.2f points',
            note='nothing shows, and this check could only have seen %.1f points, so it is weak '
                 'evidence rather than a pass'
                 % (RC['placebo_future_prices']['with_year_effects']['mde_80pct_power'] * HALF)),
        chk('Placebo: another material&rsquo;s price', RC['placebo_other_material']['with_year_effects'],
            scale=HALF, fmt='%+.2f points', note='larger than the headline itself; not a pass'),
        chk('Excluding gold, silver and platinum', RC['excluding_investment_metals']['with_year_effects'],
            scale=HALF, fmt='%+.2f points'),
        chk('Excluding recession years', RC['excluding_recessions'], scale=HALF, fmt='%+.2f points'),
        chk('Adding the same year&rsquo;s price', RC['contemporaneous'], scale=HALF, fmt='%+.2f points'),
        chk('1973&ndash;2022 only', RC['window_1973_2022'], scale=HALF, fmt='%+.2f points'),
        chk('1953&ndash;1990 only', RC['window_1953_1990'], scale=HALF, fmt='%+.2f points'),
        ('<tr><td>Poisson on levels, to keep years with no secondary production '
         '<span class="tag">not the filed check</span></td><td class="n">%+.3f</td><td class="n">%s</td>'
         '<td>the filing added it to keep zero years; there are none in the sample, so this is a '
         'contemporaneous levels association and carries no weight</td></tr>'
         % (RC['poisson_levels_keeps_zeros']['beta_logp'], pv(RC['poisson_levels_keeps_zeros']['p']))),
    ])
    loo = R['checks']['leave_one_out']
    loo_lo = min(v['points_per_50pct'] for v in loo.values())
    loo_hi = max(v['points_per_50pct'] for v in loo.values())
    TC = T['checks']
    X = load('scrap_trade_extras.json')
    XL = X['leave_one_year_out']

    def xc(f):
        return ('%+.2f <span class="dim">(%s)</span>' % (f['cumulative'], pv(f['p']))) if f else '&ndash;'
    ex_rows = []
    for y in XL['years']:
        a, b = XL['fits'][str(y)]['with_year_effects'], XL['fits'][str(y)]['without_year_effects']
        ex_rows.append('<tr><td>Leave out %d</td><td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>'
                       % (y, xc(a), xc(b), 'claimed estimate still above its detectable size'))
    for lab, key in (('Steel (7204), on T&uuml;rkiye&rsquo;s import unit value', 'steel_line'),
                     ('Gold (7112), on the Pink Sheet price', 'gold_line')):
        a, b = X[key]['with_year_effects'], X[key]['without_year_effects']
        ex_rows.append('<tr><td>%s <span class="dim">%d pairs</span></td><td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>'
                       % (lab, X[key]['pairs'], xc(a), xc(b),
                          'not read: endogenous price' if key == 'steel_line' else 'nothing readable'))
    STW = X['steel_line']['with_year_effects']['per_lag']
    uvc = [v['log_corr_with_metal_price'] for v in TC['unit_value_sanity'].values()
           if v['log_corr_with_metal_price'] is not None]
    tr_checks = ''.join([
        chk('Imports instead of exports', TC['imports_as_dv']['without_year_effects'],
            note='both sides of the same flows rise together, which looks more like a boom than a '
                 'redirection; the design cannot rule out either'),
        chk('Value instead of tonnes', TC['value_not_tonnes']['without_year_effects'],
            note='not independent evidence: scrap unit values track the metal price, and a unit value is '
                 'a value per tonne whose product mix shifts, not a price@@C_Silver2007@@@@C_Gaulier2008@@'),
        chk('Placebo: future prices', TC['placebo_future_prices'],
            note='nothing shows, and this check could have seen %.2f, so it is a pass'
                 % TC['placebo_future_prices']['mde_80pct_power']),
        chk('Placebo: another metal&rsquo;s price', TC['placebo_other_metal']['fit'],
            note='nothing shows, and this check could have seen %.2f, so it is a pass'
                 % TC['placebo_other_metal']['fit']['mde_80pct_power']),
        chk('Large exporters, separately', TC['large_exporters'],
            note='underpowered rather than empty: 13 clusters, and it could only have seen %.2f'
                 % TC['large_exporters']['mde_80pct_power']),
        chk('Before 2018', TC['before_2018']),
        ('<tr><td>Leave one metal out (claimed specification)</td><td class="n">%+.2f to %+.2f</td>'
         '<td class="n">%s</td><td>the same-year comovement does not depend on any one metal</td></tr>'
         % (min(v['cumulative'] for v in TC['leave_one_metal_out_without_year_effects'].values()),
            max(v['cumulative'] for v in TC['leave_one_metal_out_without_year_effects'].values()),
            'all &lt;0.001')),
        ('<tr><td>Scrap unit values against the metal price</td><td class="n">%.2f to %.2f</td>'
         '<td class="n">&ndash;</td><td>log correlation, for the seven lines with a price series '
         '(steel has none): scrap prices track the metal price, which is why the value check above is '
         'not independent evidence</td></tr>'
         % (min(uvc), max(uvc))),
        chk('From 2018', TC['from_2018'],
            note='China&rsquo;s scrap import restrictions fall here &mdash; its Category 7 copper-scrap ban '
                 'took effect in December 2018 and redirected flows through Malaysia, South Korea, '
                 'Taiwan and others@@C_Ryter2021@@ &mdash; and the period is too short to say anything'),
    ])
    imp = T['checks']['imports_as_dv']['without_year_effects']['cumulative']
    pl = T['checks']['placebo_future_prices']

    tok = {
        'CSS': CSS, 'NAV': NAV, 'FOOT': FOOT, 'REPO': REPO,
        'Y0': str(M['window'][0]), 'Y1': str(M['window'][1]),
        'PY0': str(R['window'][0]), 'PY1': str(R['window'][1]),
        'NMAT': str(len(R['materials'])), 'PK': str(pooled['k']), 'PN': '{:,}'.format(pooled['n']),
        'PEST': sgn(pooled['est']), 'PLO': sgn(pooled['lo']), 'PHI': sgn(pooled['hi']),
        'PP': pv(pooled['p']), 'PMDE': '%.1f' % pooled['mde'],
        'PL1': '%+.2f' % (hy['per_lag']['dp1']['beta'] * HALF),
        'PL2': '%+.2f' % (hy['per_lag']['dp2']['beta'] * HALF),
        'PL2P': pv(hy['per_lag']['dp2']['p']),
        'NMET': str(len(M['metals'])), 'THR': '%.1f' % thr, 'RECROWS': '\n'.join(rec_rows),
        'TST': tst, 'TSTC': tst[:1].upper() + tst[1:], 'TSTSHARE': tst_share, 'TSTMDE': tst_mde,
        'AMEAN': sgn(am['mean_cumulative']), 'ALO': sgn(am['ci95'][0]), 'AHI': sgn(am['ci95'][1]),
        'TY0': str(T['years'][0]), 'TY1': str(T['years'][1]),
        'TPAIRS': str(T['pairs_headline']), 'TCTY': str(T['countries_headline']),
        'TCUM': sgn(fw['cumulative']), 'TLO': sgn(fw['ci95'][0]), 'THI': sgn(fw['ci95'][1]),
        'TSAME': sgn(fw['per_lag']['dp0']['beta']),
        'TL1': sgn(fw['per_lag']['dp1']['beta']), 'TL2': sgn(fw['per_lag']['dp2']['beta']), 'TLAG': sgn(lw['cumulative']), 'TLAGP': pv(lw['p']),
        'TLAGMDE': '%.2f' % lw['mde_80pct_power'],
        'TYCUM': sgn(ty['fit']['cumulative']), 'TYP': pv(ty['fit']['p']),
        'TIMP': sgn(imp), 'TPL': sgn(pl['cumulative']), 'TPLP': pv(pl['p']),
        'REFLIST': ''.join('<li id="ref-%s">%s <a href="%s">link</a></li>' % (k, t, u) for k, t, u in REFS),
        'SRC_REC': src(['usgs', 'pink'], ['per_metal'],
                       'Market prices for the estimates, USGS unit values for the comparison column.'),
        'SRC_POOL': src(['usgs'], ['pooled'], 'The pooled design uses USGS unit values as the price.'),
        'SRC_SHARE': src(['usgs'], ['pooled']),
        'SRC_TRADE': src(['baci', 'pink'], ['trade']),
        'SRC_EXTRAS': src(['baci', 'pink'], ['extras']),
        'EXROWS': ''.join(ex_rows), 'EXY1': str(XL['years'][0]), 'EXY2': str(XL['years'][1]),
        'STL1': '%+.2f' % STW['dp1']['beta'], 'STL2': '%+.2f' % STW['dp2']['beta'], 'STL2P': pv(STW['dp2']['p']),
        'RECFIG': rec_fig, 'TRFIG': tr_fig, 'LAGFIG': lag_fig, 'SHAREFIG': share_fig,
        'RECCHECKS': rec_checks, 'TRCHECKS': tr_checks,
        'LOOLO': '%+.2f' % (loo_lo), 'LOOHI': '%+.2f' % (loo_hi),
        'EXINV_Y': '%+.2f' % (RC['excluding_investment_metals']['with_year_effects']['cumulative'] * HALF),
        'EXINV_N': '%+.2f' % (RC['excluding_investment_metals']['without_year_effects']['cumulative'] * HALF),
        'TRROWS': '\n'.join(tr_rows),
        'QEST': sgn(qy['cumulative'] * HALF), 'QLO': sgn(qy['ci95'][0] * HALF), 'QHI': sgn(qy['ci95'][1] * HALF),
        'QP': pv(qy['p']), 'QMDE': '%.1f' % (qy['mde_80pct_power'] * HALF),
        'UVMAX': '%.2f' % max(abs(v['pink']['elasticity']['cumulative'] - v['unit_value']['elasticity']['cumulative'])
                              for v in M['metals'].values()),
        'LEADUV': '%.2f' % M['metals']['lead']['unit_value']['elasticity']['mde_80pct_power'],
        'LEADSHP': pv(M['metals']['lead']['pink']['share']['p']),
        'ALSHP': pv(M['metals']['aluminium']['pink']['share']['p']),
        'TYMDE': '%.2f' % ty['fit']['mde_80pct_power'],
        'NUNT': word(len(M['metals']) - len(testable)), 'NMETW': word(len(M['metals'])),
        'TINN': word(T['checks']['by_metal']['tin']['countries']), 'TNMET': word(len(T['headline_metals'])),
    }
    for k in REFNUM:
        tok['C_' + k] = cite(k)
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
  on US recovery of scrap, and on world trade in scrap. <b>Neither shows a detectable increase in recycled metal in
  the two years after a price rise.</b> In the recovery study only two metals had the power to see a
  response at the size the filing said would matter, and in those two the tonnes were not there. For
  lead, the other filed equation &mdash; the recycled <i>share</i> of consumption &mdash; does show a
  rise; the two disagree, and both are below.</p>
</div></section>

<section class="wrap xp">
  <h2>1. Does US recovery of scrap rise after prices do?</h2>
  <p><span class="verdict">NOT SHOWN</span></p>
  <p>The first design pooled @@NMAT@@ metals from the US Geological Survey&rsquo;s historical statistics,
  @@PY0@@&ndash;@@PY1@@, and asked whether scrap-derived supply, as a share of US consumption, rises in the
  two years after a 50% rise in that metal's real price, measured by the USGS unit value &mdash; which
  is value per tonne of apparent consumption, not a market price@@C_Kelly2014@@. Sixteen metals are in scope; @@PK@@ have an apparent-consumption series, so the share equation
  estimates on @@PN@@ metal-years over those @@PK@@ (gold has none). The answer was
  @@PEST@@ points of consumption with year effects (95% interval @@PLO@@ to @@PHI@@, p&nbsp;=&nbsp;@@PP@@)
  and @@QEST@@ points without them (@@QLO@@ to @@QHI@@, p&nbsp;=&nbsp;@@QP@@). But the smallest response
  this design could reliably detect was @@PMDE@@ and @@QMDE@@ points, and the filing had said 1 point
  would matter. So that first result could not tell a useful response from none, and we said so. Within it the two
  lags point opposite ways &mdash; @@PL1@@ points after one year and @@PL2@@ after two
  (p&nbsp;=&nbsp;@@PL2P@@) &mdash; and a share that falls two years after a price rise is as easily the
  denominator moving, consumption recovering faster than scrap, as anything about scrap supply.</p>
  <p>A second design, filed before it was run, took each metal on its own, @@Y0@@&ndash;@@Y1@@, on
  World Bank market prices &mdash; which is why it covers @@NMETW@@ metals and not sixteen: only those have
  both a Pink Sheet price and a US secondary-production series &mdash; and asked whether a metal&rsquo;s
  scrap tonnes rise by at least @@THR@@% per 1%
  of price within two years. The threshold came from the first filing, not from the
  literature, but it happens to sit at the bottom of the published range: a survey of the econometric
  estimates puts the own-price elasticity of secondary supply at roughly 0.20 to 0.39@@C_Soderholm2019@@,
  with 0.21 estimated for European secondary aluminium@@C_Blomberg2009@@. For
  the six base metals the prices are London Metal Exchange cash quotations for primary or refined
  metal, and for gold a spot bullion price@@C_WorldBank2026@@ &mdash; in no case the price a scrap
  collector is paid, which is a gap between the regressor and the decision it stands for. Each metal is reported with the smallest response its own series could
  have seen; a metal that could not see @@THR@@ is called untestable, not a null.</p>
  <figure class="fig">@@RECFIG@@
  <figcaption><b>Which metals could answer, and what they answered.</b> Each metal's two-year response
  of scrap tonnes to price, with its 95% interval; the faint band is the bar the filing set before the estimates
  &mdash; a response inside it would not have been detected with 80% certainty by that metal's series. Teal: the series could see a response at the filed threshold. Violet: it could
  not, so its estimate is untestable rather than a null.</figcaption></figure>
  <div class="tbl"><table><thead><tr><th>Metal</th><th class="n">two-year elasticity</th>
  <th class="n">95% interval</th><th class="n">p</th><th class="n">smallest it could see (80% power)</th>
  <th class="n">on USGS unit values</th><th>reading</th></tr></thead>
  <tbody>@@RECROWS@@</tbody></table></div>
  @@SRC_REC@@
  <p><b>@@TSTC@@ could have seen a response at the filed threshold, and show none that large.</b> Their series could
  detect @@TSTMDE@@; both estimates are close to zero and their intervals exclude @@THR@@. Among the seven tested, these are the metals where recycling is largest (median share of US consumption from scrap:
  @@TSTSHARE@@). The lead result depends on which price is used: on the USGS unit value its series
  could only have seen @@LEADUV@@, which would make it untestable too, so aluminium is the one metal
  whose reading holds on both price measures. As a descriptive summary across all @@NMETW@@ metals, five of them untestable at the threshold, the
  unweighted mean of the seven responses is @@AMEAN@@, and their spread puts a descriptive 95% band of
  @@ALO@@ to @@AHI@@ around it &mdash; a summary of seven estimates, not an inferential interval. Using the USGS unit value instead of a market price moves no estimate by more
  than @@UVMAX@@.</p>
  <figure class="fig">@@SHAREFIG@@
  <figcaption><b>Why aluminium and lead matter most.</b> The median share of US consumption met by
  scrap over the study years, for the ten metals with the largest shares (mercury's rests on a series
  that ends in 1997). The two metals whose data can see the filed threshold are also among
  those where recycling is largest, so a response there would have mattered most for policy.</figcaption></figure>
  @@SRC_SHARE@@
  <h3>The filed checks</h3>
  <div class="tbl"><table><thead><tr><th>Check (points of consumption per +50% price, unless noted)</th>
  <th class="n">estimate</th><th class="n">p</th><th>reading</th></tr></thead>
  <tbody>@@RECCHECKS@@</tbody></table></div>
  @@SRC_POOL@@
  <p class="dim">Leaving out one metal at a time moves the headline between @@LOOLO@@ and @@LOOHI@@ points, and
  no version is significant: no single metal drives it. Four of these checks carry year effects and
  four do not; where they differ the difference is large &mdash; excluding gold, silver and platinum
  gives @@EXINV_Y@@ points with year effects and @@EXINV_N@@ without.</p>
  <p class="dim">The per-metal share results quoted below come from the second design, on market
  prices: <a href="@@REPO@@scrap-response/PREREGISTRATION.md">Amendment A</a> and
  <a href="https://github.com/materials-atlas/critical-materials-atlas/blob/main/out/scrap_response_per_metal.json"><code>out/scrap_response_per_metal.json</code></a>.</p>
  <div class="note">One thing the filed equations disagree about. The filed share equation says the
  recycled <i>share</i> of consumption rose after a price rise &mdash; for lead (p&nbsp;=&nbsp;@@LEADSHP@@)
  and, not significantly, for aluminium (p&nbsp;=&nbsp;@@ALSHP@@) &mdash; while the filed tonnage equation
  shows no matching rise in the tonnes.
  Unfiled regressions on the same data suggest the reason is that consumption fell. If so, a higher
  share would mean less demand, not more recycling. It is a hypothesis for a separate test on other
  countries; the figures are in the <a href="@@REPO@@scrap-response/PREREGISTRATION.md">filing</a>.</div>
</section>

<section class="wrap xp">
  <h2>2. Does scrap trade follow price?</h2>
  <p><span class="verdict">SAME YEAR ONLY</span></p>
  <p>If recovery is not shown to rise, scrap might still move: collected in one country and shipped to where
  prices pay. The second study took world trade in @@TNMET@@ metals&rsquo; scrap from CEPII BACI,
  @@TY0@@&ndash;@@TY1@@, for @@TPAIRS@@ country&ndash;metal pairs among the small exporters of each
  (@@TCTY@@ countries), with the same two-year shape. BACI values are reconciled from both sides of each
  flow, weighted by how reliably each country reports@@C_Gaulier2010@@, so an export figure here is not
  one country's declaration. <b>The headline is therefore the small exporters
  of each metal</b>, where a response is easiest to see; the large exporters, who ship most of the
  tonnes, are a separate check below and it is underpowered.</p>
  <p>Keeping the common cycle in, scrap exports rise with price by @@TCUM@@% per 1% (95% interval @@TLO@@ to @@THI@@), but
  <b>almost all of it is in the same year</b>: the three terms of that estimate are @@TSAME@@ in the same
  year, @@TL1@@ a year later and @@TL2@@ two years later. Estimated on its own, without the same-year term,
  the two-year response is @@TLAG@@ (p&nbsp;=&nbsp;@@TLAGP@@), where the design could have seen about @@TLAGMDE@@. Within a year prices and
  shipments are set together, so this is movement with the cycle, not a demonstrated supply response.
  Imports of the same scrap rise too (@@TIMP@@% per 1%, without year effects), which looks more like a
  boom than a redirection; the design cannot rule out either, nor a drawdown of stocks. Once the
  common cycle is removed with year effects, the estimate (@@TYCUM@@, p&nbsp;=&nbsp;@@TYP@@) oscillates
  from year to year, the smallest effect it could see is @@TYMDE@@, and it is not claimed. A placebo on future prices shows nothing (@@TPL@@, p&nbsp;=&nbsp;@@TPLP@@).</p>
  <figure class="fig">@@LAGFIG@@
  <figcaption><b>All of the response is in the same year.</b> The three terms of the claimed
  specification: a price rise and scrap shipments move together within the year, and nothing
  detectable follows in the next two (the design could have seen about @@TLAGMDE@@ there). Within a year, prices and quantities are set together, so this is comovement, not a
  demonstrated supply response.</figcaption></figure>
  @@SRC_TRADE@@
  <figure class="fig">@@TRFIG@@
  <figcaption><b>By metal, with what each could detect.</b> Cumulative response of scrap exports to
  price, 95% intervals, and the faint band each metal's exporters could not have detected with 80%
  certainty.
  Tin's estimate is about the size of what its nine exporters could see, so it is not read.</figcaption></figure>
  <h3>Three checks the filing promised, run afterwards</h3>
  <p>The filing named three more checks that the first run did not contain. They were written and
  committed before they touched the data, and run on the same sample, prices and estimator.</p>
  <div class="tbl"><table><thead><tr><th>Check</th><th class="n">with year effects</th>
  <th class="n">without year effects</th><th>reading</th></tr></thead><tbody>@@EXROWS@@</tbody></table></div>
  @@SRC_EXTRAS@@
  <p class="dim">Leaving out the two years with the largest world price moves (@@EXY1@@ and @@EXY2@@,
  defined in the code before the run) leaves the claimed estimate above its detectable size either
  way, so it is not one episode. Gold shows nothing readable. <b>Steel is the one line in either study
  with a response after the same year</b> once year effects remove the common cycle &mdash;
  @@STL1@@ a year later and @@STL2@@ two years later (p&nbsp;@@STL2P@@) &mdash; but it is not read: its
  price is the unit value of T&uuml;rkiye&rsquo;s own scrap imports, the marginal buyer, so it moves with
  the same shocks as the exports it is meant to explain, and a unit value is not a
  price@@C_Silver2007@@. It is the one place where a better price series would be worth having.</p>
  <p class="dim">Both the chart above and the table below are the cycle-inclusive specification, without
  year effects, and the elasticity is cumulative over the same year and the two that follow.</p>
  <div class="tbl"><table><thead><tr><th>Scrap of</th><th class="n">elasticity, same year + two</th>
  <th class="n">95% interval</th><th class="n">p</th><th class="n">smallest it could see (80% power)</th>
  <th class="n">exporters</th><th>reading</th></tr></thead>
  <tbody>@@TRROWS@@</tbody></table></div>
  @@SRC_TRADE@@
  <h3>The filed checks</h3>
  <div class="tbl"><table><thead><tr><th>Check</th><th class="n">estimate</th><th class="n">p</th>
  <th>reading</th></tr></thead><tbody>@@TRCHECKS@@</tbody></table></div>
  @@SRC_TRADE@@
  <p class="dim">The first two checks keep the headline's specification, which leaves the common cycle in; the
  placebos, the exporter split and the two period splits carry year effects, which remove it.</p>
  <p class="dim">The last column applies the rule the filings set: an estimate smaller than what its own
  exporters could have detected with 80% power is not read as a response, even where its p-value is below
  0.05 &mdash; that bar was set before the estimates, and a realised sample can still put a significant
  coefficient inside it. A reading of &ldquo;same-year
  comovement&rdquo; means the cumulative estimate is larger than the smallest effect that metal's
  exporters could have detected, and &mdash; as the chart above shows for the six together &mdash; that
  the mass of it sits in the same year rather than in the two that follow; lead clears its own bar
  narrowly (+0.65 against 0.60). Tin rests on @@TINN@@
  exporters and an estimate about the size of the smallest they could detect, so it is not read.</p>
</section>

<section class="wrap xp">
  <h2>What the two say together</h2>
  <p>As far as open data can see, neither US recovery nor the scrap exports of the smaller exporters,
  the sample the trade headline rests on, is shown to rise in the two years
  after a price rise. Neither result is novel: the US Geological Survey plotted price against old-scrap
  recycling efficiency for twenty-five metals and found no relationship (R&sup2;&nbsp;=&nbsp;0.05), a
  cross-metal comparison at three base years rather than a within-metal response@@C_Sibley2011@@, and an autoregressive model of
  recycled copper supply found industrial activity and world output carrying the series, with limited
  dependence on the copper price@@C_Fu2017@@. Scrap trade moves with price within the year; whether US recovery does was not
  part of either filed test (an exploratory run, in the scrap-trade filing, suggests it does). No evidence was found that a price rise brings
  more recovered metal, or more cross-border shipments of scrap, over the following two years (the one
  exception, steel on an endogenous price, is reported above and not read); within
  the year itself, shipments do move with price &mdash; which is as consistent with a boom that lifts
  both sides, or with stocks being drawn down, as with metal being redirected.</p>
  <p><b>What neither study can say, as both filings require it to be said.</b> New and old scrap are
  mixed: the US statistics separate them only for aluminium, so a rise in "scrap" can be a factory
  off-cut returning faster rather than an old product being collected. Prompt scrap from fabrication
  rarely crosses a border and home scrap never does, so the trade study sees merchant scrap only.
  Neither study sees capacity: they see the supply that appeared, not what could have been recovered.
  BACI's tonnages are estimated for many flows, and the trade study's dependent variable is tonnes.
  And policy moves this market as much as price does &mdash; export licences, import bans and duties
  all act on the same flows.</p>
  <p>That is narrower than &ldquo;recycling does not respond to price&rdquo;. It is US recovery and
  world trade only; the tests are predictive, not causal; @@NUNT@@ of the @@NMETW@@ metals in the first study
  cannot see the threshold &mdash; and underpowered designs are the rule rather than the exception in
  empirical economics, which is why an unpowered null is weak evidence on its own@@C_Ioannidis2017@@ &mdash;
  the two metals that were powered are the exception, and their intervals do exclude a response at the
  filed size;
  and nothing here covers the newer critical materials, which have no such series. For a policy that counts on scrap to cushion a price shock within a couple of years,
  it is still the relevant evidence: on the metals where it can be checked, no response of that size
  was detected in the two years after. Within the shock year itself, scrap does move between countries,
  which may reallocate metal even where it creates none.</p>
  <h3>References</h3>
  <ol class="refs">@@REFLIST@@</ol>

  <h3>Data</h3>
  <ol class="refs">
  <li><b>US production, consumption and recovery.</b> US Geological Survey, <i>Historical Statistics for
  Mineral and Material Commodities in the United States</i>, Data Series 140 (a US government work).
  <a href="https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities">usgs.gov</a>.</li>
  <li><b>Market prices.</b> World Bank commodity price data (the &ldquo;Pink Sheet&rdquo;), monthly,
  averaged to the year and deflated to 1998 dollars by the deflator implied by the USGS nominal and
  real pair. <a href="https://www.worldbank.org/en/research/commodity-markets">worldbank.org</a>.</li>
  <li><b>Scrap trade.</b> CEPII BACI, release V202601, under the Etalab Open Licence 2.0.
  <a href="https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37">cepii.fr</a>. Method:
  Gaulier, G. and Zignago, S. (2010), CEPII Working Paper 2010-23.
  <a href="http://www.cepii.fr/PDF_PUB/wp/2010/wp2010-23.pdf">wp2010-23</a>.</li>
  </ol>
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
