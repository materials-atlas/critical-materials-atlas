# -*- coding: utf-8 -*-
"""The research paper for buildout-study/: grid equipment in world trade, 2012-2024.

Every number on the page is read from out/buildout_study.json (written by buildout-study/analysis.py,
committed before its first run). Nothing here computes a result; it only presents one. References are
copied from buildout-study/literature.md, where each source was opened and quoted on 2026-09-18.

Writes grid-trade.html.  Usage: python build_grid_trade_paper.py
"""
import io
import json
import math
import os

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
REPO = 'https://github.com/materials-atlas/critical-materials-atlas/blob/main/buildout-study/'
DOC = os.path.join(ROOT, 'out', 'buildout_study.json')
OUT = os.path.join(ROOT, 'grid-trade.html')

NAMES = {'CHN': 'China', 'JPN': 'Japan', 'RUS': 'Russia', 'DEU': 'Germany', 'KOR': 'South Korea',
         'MEX': 'Mexico', 'TUR': 'Türkiye', 'USA': 'United States', 'KAZ': 'Kazakhstan'}

REFS = [
    ('DOE2024', 'U.S. Department of Energy (2024). <i>Large Power Transformer Resilience: Report to Congress</i>. July 2024.',
     'https://www.energy.gov/sites/default/files/2024-10/EXEC-2022-001242%20-%20Large%20Power%20Transformer%20Resilience%20Report%20signed%20by%20Secretary%20Granholm%20on%207-10-24.pdf'),
    ('DOE2022', 'U.S. Department of Energy (2022). <i>Electric Grid Supply Chain Review: Large Power Transformers and High Voltage Direct Current Systems</i>. February 2022.',
     'https://www.energy.gov/sites/default/files/2022-02/Electric%20Grid%20Supply%20Chain%20Report%20-%20Final.pdf'),
    ('BIS2020', 'U.S. Department of Commerce, Bureau of Industry and Security (2020). <i>The Effect of Imports of Transformers and Transformer Components on the National Security</i>. Final report, 15 October 2020.',
     'https://www.bis.gov/media/documents/redacted-goes-report-updated-10-26-21.pdf'),
    ('GAO2023', 'U.S. Government Accountability Office (2023). <i>Electricity Grid: DOE Could Better Support Industry Efforts to Ensure Adequate Transformer Reserves</i>. GAO-23-106180.',
     'https://www.gao.gov/products/gao-23-106180'),
    ('IEA2023', 'International Energy Agency (2023). <i>Electricity Grids and Secure Energy Transitions</i>. Paris.',
     'https://www.iea.org/reports/electricity-grids-and-secure-energy-transitions'),
    ('IEA2025', 'International Energy Agency (2025). <i>Building the Future Transmission Grid: Strategies to Navigate Supply Chain Challenges</i>. Paris, February 2025.',
     'https://www.iea.org/reports/building-the-future-transmission-grid'),
    ('NLR2026', 'Ramasamy, V., Cooperman, A., Jayswal, R. and Seward, M. (2026). <i>Large Power Transformer Supply Chain Gap Analysis and Domestic Content Strategies for Hydropower Rehabilitation</i>. NLR/TP-5700-96742, National Laboratory of the Rockies.',
     'https://docs.nlr.gov/docs/fy26osti/96742.pdf'),
    ('BLS', 'U.S. Bureau of Labor Statistics. Producer Price Index by Commodity: Power and Distribution Transformers, Except Parts (WPU117409).',
     'https://fred.stlouisfed.org/series/WPU117409'),
    ('GZ2010', 'Gaulier, G. and Zignago, S. (2010). "BACI: International Trade Database at the Product-Level." CEPII Working Paper 2010-23.',
     'http://www.cepii.fr/PDF_PUB/wp/2010/wp2010-23.pdf'),
    ('Schott2004', 'Schott, P. K. (2004). "Across-Product Versus Within-Product Specialization in International Trade." <i>Quarterly Journal of Economics</i> 119(2): 647-678.',
     'https://doi.org/10.1162/0033553041382201'),
    ('HS2011', 'Hallak, J. C. and Schott, P. K. (2011). "Estimating Cross-Country Differences in Product Quality." <i>Quarterly Journal of Economics</i> 126(1): 417-474.',
     'https://doi.org/10.1093/qje/qjq003'),
    ('Silver2007', 'Silver, M. (2007). "Do Unit Value Export, Import, and Terms of Trade Indices Represent or Misrepresent Price Indices?" IMF Working Paper 07/121.',
     'https://doi.org/10.5089/9781451866858.001'),
    ('Kilian2009', 'Kilian, L. (2009). "Not All Oil Price Shocks Are Alike: Disentangling Demand and Supply Shocks in the Crude Oil Market." <i>American Economic Review</i> 99(3): 1053-1069.',
     'https://doi.org/10.1257/aer.99.3.1053'),
    ('KM2012', 'Kilian, L. and Murphy, D. P. (2012). "Why Agnostic Sign Restrictions Are Not Enough." <i>Journal of the European Economic Association</i> 10(5): 1166-1188.',
     'https://doi.org/10.1111/j.1542-4774.2012.01080.x'),
    ('Shapiro2022', 'Shapiro, A. H. (2022). "Decomposing Supply and Demand Driven Inflation." Federal Reserve Bank of San Francisco Working Paper 2022-18.',
     'https://doi.org/10.24148/wp2022-18'),
]
REFNUM = {k: i + 1 for i, (k, _, _) in enumerate(REFS)}


def cite(*keys):
    return '<sup class="cite">[%s]</sup>' % ','.join('<a href="#ref-%s">%d</a>' % (k, REFNUM[k]) for k in keys)


PCT = {}                                                       # beta -> percent as stored by the analysis


def pct(b):
    """The percent the analysis stored (computed from the unrounded coefficient), so the page and the
    filing never disagree by a rounding step; recomputed only if the coefficient is not in the file."""
    v = PCT.get(round(b, 4))
    return '%+.0f%%' % (v if v is not None else 100 * (math.exp(b) - 1))


def _collect_pct(o):
    if isinstance(o, dict):
        if 'beta' in o and 'pct' in o:
            PCT[round(o['beta'], 4)] = o['pct']
        for v in o.values():
            _collect_pct(v)
    elif isinstance(o, list):
        for v in o:
            _collect_pct(v)


def fp(p):
    return '&lt;0.001' if p < 0.001 else ('%.3f' % p)


def coef(e, n):
    v = e['coefs'][n]
    return v['beta'], v.get('p_wild_line', v.get('p_cluster_exporter')), v


def event_chart(price, volume):
    """Year-by-year relative gaps, base 2019, with line-bootstrap 95% intervals. Two series, one axis."""
    W, H, L, R, T, B = 720, 300, 52, 118, 18, 36
    years = sorted(int(y) for y in price)
    lo = min(min(v['ci95'][0] for v in price.values()), min(v['ci95'][0] for v in volume.values()))
    hi = max(max(v['ci95'][1] for v in price.values()), max(v['ci95'][1] for v in volume.values()))
    lo, hi = math.floor(lo * 10) / 10, math.ceil(hi * 10) / 10

    def x(y):
        return L + (y - years[0]) / (years[-1] - years[0]) * (W - L - R)

    def yv(v):
        return T + (hi - v) / (hi - lo) * (H - T - B)
    g = []
    g.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" class="post"/>'
             % (x(2020.5), T, x(2024) - x(2020.5) + 8, H - T - B))
    tick = lo
    while tick <= hi + 1e-9:
        g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="%s"/>'
                 % (L, W - R, yv(tick), yv(tick), 'zero' if abs(tick) < 1e-9 else 'grid'))
        g.append('<text x="%d" y="%.1f" class="ax" text-anchor="end">%+.1f</text>' % (L - 6, yv(tick) + 4, tick))
        tick = round(tick + 0.1, 10)
    for y in years:
        if y % 2 == 0 or y == 2019:
            g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%d</text>' % (x(y), H - B + 18, y))
    g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">2021&ndash;24</text>'
             % ((x(2020.5) + x(2024)) / 2, T + 12))
    for series, cls, dx, label in ((price, 'p', -3, 'unit value'), (volume, 'v', 3, 'tonnes')):
        pts = []
        for y in years:
            v = series[str(y)]
            X = x(y) + dx
            g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="ci %s"/>'
                     % (X, X, yv(v['ci95'][0]), yv(v['ci95'][1]), cls))
            pts.append((X, yv(v['beta'])))
        g.append('<polyline points="%s" class="ln %s"/>' % (' '.join('%.1f,%.1f' % p for p in pts), cls))
        for X, Y in pts:
            g.append('<circle cx="%.1f" cy="%.1f" r="4" class="pt %s"/>' % (X, Y, cls))
        g.append('<text x="%.1f" y="%.1f" class="lab %s">%s %+.2f</text>'
                 % (pts[-1][0] + 10, pts[-1][1] + 4, cls, label, series[str(years[-1])]['beta']))
    return ('<svg viewBox="0 0 %d %d" role="img" aria-label="Year-by-year gap between transformers and '
            'heavy capital goods, in log points relative to 2019, for unit values and tonnes">%s</svg>'
            % (W, H, ''.join(g)))


def main():
    d = json.load(io.open(DOC, encoding='utf-8'))
    _collect_pct(d)
    D, C = d['designs'], d['checks']
    B, Cn, G, Cu = D['B_transformers'], D['C_net_of_materials'], D['A_goes'], D['A_copper_wire']
    bp1, pp1, _ = coef(B['price'], 'TxP1')
    bp2, pp2, vp2 = coef(B['price'], 'TxP2')
    bv1, pv1, _ = coef(B['volume'], 'TxP1')
    bv2, pv2, _ = coef(B['volume'], 'TxP2')
    cn1, pc1, _ = coef(Cn['price'], 'TxP1')
    cn2, pc2, _ = coef(Cn['price'], 'TxP2')
    keep = cn2 / bp2
    ev_p, ev_v = C['event_study']['B_price'], C['event_study']['B_volume']
    bls = C['bls_validation']
    sup = C['suppliers']
    g19, g24 = sup['722511']['2019'], sup['722511']['2024']
    t19, t24 = sup['850423']['2019'], sup['850423']['2024']
    us, eu, rest = C['importer_USA'], C['importer_EU27'], C['importer_rest']
    n_flow_years = d['sample']['flow_years']
    placebo_b = C['placebo_2015_16_B_transformers']['coefs']['TxP1']
    placebo_g = C['placebo_2015_16_A_goes']['coefs']['TxP1']
    chip = d['chip_equipment_described_only']['848620']

    def row(label, e, side='price'):
        cells = []
        for n in ('TxP1', 'TxP2'):
            b, p, v = coef(e, n)
            ci = v.get('ci95_wild_line')
            cells.append('<td class="n">%+.3f <span class="mut">(%s)</span></td><td class="n">%s</td>'
                         '<td class="n mut">%s</td>'
                         % (b, pct(b), fp(p), '%+.2f to %+.2f' % tuple(ci) if ci else 'exporter-clustered'))
        return '<tr><td>%s</td>%s</tr>' % (label, ''.join(cells))

    main_rows = ''.join([
        row('Transformers vs heavy capital goods &mdash; unit value', B['price']),
        row('Transformers vs heavy capital goods &mdash; tonnes', B['volume']),
        row('Transformers net of steel and copper cost &mdash; unit value', Cn['price']),
        row('Grain-oriented electrical steel vs other alloy steel &mdash; unit value', G['price']),
        row('Grain-oriented electrical steel vs other alloy steel &mdash; tonnes', G['volume']),
        row('Copper wire vs copper cathode &mdash; unit value', Cu['price']),
        row('Copper wire vs copper cathode &mdash; tonnes', Cu['volume']),
    ])

    def imp_row(name, e):
        out = []
        for k in ('B_price', 'B_volume', 'C_price'):
            b, p, _ = coef(e[k], 'TxP2')
            out.append('<td class="n">%+.2f <span class="mut">(%s)</span></td><td class="n">%s</td>' % (b, pct(b), fp(p)))
        return '<tr><td>%s</td>%s</tr>' % (name, ''.join(out))
    imp_rows = imp_row('United States', us) + imp_row('European Union (27)', eu) + imp_row('Rest of the world', rest)

    def sup_row(code, label):
        s = sup[code]
        cells = ''.join('<td class="n">%d</td><td class="n">%.0f%%</td><td class="n">%.0f%%</td>'
                        % (s[y]['exporters_above_1pct'], 100 * s[y]['china_share'], 100 * s[y]['top3_share'])
                        for y in ('2019', '2024'))
        return '<tr><td>%s</td>%s</tr>' % (label, cells)
    sup_rows = (sup_row('722511', 'Grain-oriented electrical steel, 600 mm+') +
                sup_row('850423', 'Transformers over 10,000 kVA') +
                sup_row('850422', 'Transformers 650&ndash;10,000 kVA') +
                sup_row('850421', 'Transformers up to 650 kVA') +
                sup_row('740811', 'Copper wire'))

    pre = C['pretrend_rule']
    loo = C['leave_one_line_out']
    loo_b = [v['TxP2'] for k, v in loo.items() if k.startswith('B_') and v]
    band02 = C['uv_band_0.2_5']['coefs']['TxP2']
    bandno = C['uv_band_none']['coefs']['TxP2']
    heavy = C['freight_heavy_low_uv']['coefs']
    light = C['freight_light_high_uv']['coefs']
    cont = C['contaminated_controls']['price']['coefs']['TxP2']
    s20 = D['C_shares_0.20']['price']['coefs']['TxP2']['beta']
    s30 = D['C_shares_0.30']['price']['coefs']['TxP2']['beta']
    chn = C['exporter_China']['B_price']['coefs']['TxP2']
    nchn = C['exporter_not_China']['B_price']['coefs']['TxP2']

    refs = ''.join('<li id="ref-%s">%s <a href="%s">%s</a></li>' % (k, t, u, u.replace('https://', '').split('/')[0])
                   for k, t, u in REFS)

    html = TEMPLATE
    subs = {
        'NFY': format(n_flow_years, ','),
        'BP2': pct(bp2), 'BV2': pct(bv2), 'PP2': fp(pp2), 'PV2': fp(pv2),
        'BP1': pct(bp1), 'BV1': pct(bv1), 'PP1': fp(pp1), 'PV1': fp(pv1),
        'CN1': pct(cn1), 'CN2': pct(cn2), 'PC1': fp(pc1), 'PC2': fp(pc2),
        'KEEP': '%.0f' % (100 * keep), 'MATSHARE': '%.0f' % (100 * (1 - keep)),
        'EV12': '%+.2f' % ev_p['2012']['beta'], 'EV24': '%+.2f' % ev_p['2024']['beta'],
        'EVV12': '%+.2f' % ev_v['2012']['beta'], 'EVV24': '%+.2f' % ev_v['2024']['beta'],
        'CHART': event_chart(ev_p, ev_v),
        'MAINROWS': main_rows, 'IMPROWS': imp_rows, 'SUPROWS': sup_rows,
        'USV': '%+.2f' % coef(us['B_volume'], 'TxP2')[0], 'USVP': pct(coef(us['B_volume'], 'TxP2')[0]),
        'USVp': fp(coef(us['B_volume'], 'TxP2')[1]),
        'USC': pct(coef(us['C_price'], 'TxP2')[0]), 'USCp': fp(coef(us['C_price'], 'TxP2')[1]),
        'EUP': pct(coef(eu['B_price'], 'TxP2')[0]), 'EUV': pct(coef(eu['B_volume'], 'TxP2')[0]),
        'EUC': pct(coef(eu['C_price'], 'TxP2')[0]), 'EUCp': fp(coef(eu['C_price'], 'TxP2')[1]),
        'G19C': '%.0f' % (100 * g19['china_share']), 'G24C': '%.0f' % (100 * g24['china_share']),
        'G19N': str(g19['exporters_above_1pct']), 'G24N': str(g24['exporters_above_1pct']),
        'G19T': '%.0f' % (100 * g19['top3_share']), 'G24T': '%.0f' % (100 * g24['top3_share']),
        'GP2': pct(coef(G['price'], 'TxP2')[0]), 'GPp2': fp(coef(G['price'], 'TxP2')[1]),
        'GPL': '%+.2f' % placebo_g['beta'], 'GPLp': fp(placebo_g['p_wild_line']),
        'BPL': '%+.3f' % placebo_b['beta'], 'BPLp': fp(placebo_b['p_wild_line']),
        'CUP1': pct(coef(Cu['price'], 'TxP1')[0]), 'CUPp1': fp(coef(Cu['price'], 'TxP1')[1]),
        'CUP2': pct(coef(Cu['price'], 'TxP2')[0]),
        'BLSC': '%.2f' % bls['corr_annual_changes'], 'BLSL': '%.2f' % bls['corr_levels'],
        'BLS19': '%.0f' % bls['ppi']['2019'], 'BLS22': '%.0f' % bls['ppi']['2022'], 'BLS24': '%.0f' % bls['ppi']['2024'],
        'LOOLO': '%+.2f' % min(loo_b), 'LOOHI': '%+.2f' % max(loo_b),
        'B02': '%+.2f' % band02['beta'], 'BNO': '%+.2f' % bandno['beta'],
        'HV2': '%+.2f' % heavy['TxP2']['beta'], 'HVp2': fp(heavy['TxP2']['p_wild_line']),
        'LT2': '%+.2f' % light['TxP2']['beta'], 'LTp2': fp(light['TxP2']['p_wild_line']),
        'CONT': '%+.2f' % cont['beta'], 'CONTp': fp(cont['p_wild_line']),
        'S20': pct(s20), 'S30': pct(s30),
        'CHN2': '%+.2f' % chn['beta'], 'NCHN2': '%+.2f' % nchn['beta'],
        'MDE': '%.2f' % vp2['mde_80'], 'NLINES': str(vp2['lines_in_bootstrap']),
        'CHIP12': format(chip['2012']['value_musd'] / 1000.0, '.0f'),
        'CHIP24': format(chip['2024']['value_musd'] / 1000.0, '.0f'),
        'CHIPTOP': ', '.join('%s %.0f%%' % (NAMES.get(i, i), 100 * s) for i, s in chip['2024']['top3']),
        'REFS': refs, 'REPO': REPO,
    }
    for k in REFNUM:
        subs['C_' + k] = cite(k)
    for k, v in subs.items():
        html = html.replace('@@%s@@' % k, v)
    assert '@@' not in html, [l for l in html.split('\n') if '@@' in l][:3]
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(html)
    print('wrote', OUT)


NAV = ('<header class="topbar"><div class="wrap">'
       '<a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>'
       '<nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a>'
       '<a href="value-chains">Value Chains</a><a href="analysis">Analysis</a>'
       '<a href="reports">Reports</a><a href="method">Method</a></nav></div></header>')
FOOT = ('<footer class="siteftr"><div class="wrap">'
        '<div><h4>Critical Materials Atlas</h4>Public-data value-chain research. Not affiliated '
        'with, nor representing, any institution.</div>'
        '<div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value '
        'Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br>'
        '<a href="method">Method</a></div>'
        '<div><h4>Sources</h4>CEPII BACI &middot; BLS &middot; World Bank</div>'
        '<div class="fineprint">Independent public-data research.</div></div></footer>')

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Grid equipment in world trade, 2012&ndash;2024 &mdash; Critical Materials Atlas</title>
<meta name="description" content="A pre-registered study of world trade in transformers, grain-oriented electrical steel and copper wire: after 2021, did the build-out show up in prices or in volumes, and how much of the transformer price rise is the cost of steel and copper?">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style>
.paper{max-width:46rem}
.paper p,.paper li{line-height:1.62}
.paper h2{margin-top:2.2rem}
.paper h3{margin-top:1.4rem;font-size:1.05rem}
.abstract{background:#f4f7f6;border-left:3px solid #0e7c74;padding:1rem 1.2rem;margin:1.2rem 0}
.meta{color:#5a6468;font-size:.9rem}
.cite{font-size:.72rem}.cite a{text-decoration:none}
.tbl{overflow-x:auto;margin:.8rem 0}
.tbl table{border-collapse:collapse;width:100%;font-size:.86rem;min-width:40rem}
.tbl th,.tbl td{padding:.36rem .5rem;border-bottom:1px solid #e3e6e5;text-align:left;vertical-align:top}
.tbl td.n,.tbl th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.mut{color:#6b7478}
.fig{margin:1.2rem 0}.fig svg{width:100%;height:auto;display:block}
.fig figcaption{font-size:.86rem;color:#5a6468;margin-top:.4rem}
.fig .grid{stroke:#e3e6e5;stroke-width:1}.fig .zero{stroke:#8b9396;stroke-width:1}
.fig .post{fill:#0e7c74;opacity:.06}
.fig .ax{font:11px Inter,system-ui,sans-serif;fill:#5a6468}
.fig .ln{fill:none;stroke-width:2}.fig .ln.p{stroke:#0e7c74}.fig .ln.v{stroke:#15323a}
.fig .ci{stroke-width:1.5;opacity:.35}.fig .ci.p{stroke:#0e7c74}.fig .ci.v{stroke:#15323a}
.fig .pt{stroke:#fff;stroke-width:2}.fig .pt.p{fill:#0e7c74}.fig .pt.v{fill:#15323a}
.fig .lab{font:600 12px Inter,system-ui,sans-serif}.fig .lab.p{fill:#0e7c74}.fig .lab.v{fill:#15323a}
.box{background:#f7f7f5;border-left:3px solid #15323a;padding:.8rem 1.1rem;margin:1rem 0;font-size:.93rem}
.refs li{margin:.3rem 0;font-size:.88rem}
</style></head><body>
@@NAV@@
<section class="hero"><div class="wrap">
  <div class="eyebrow">Research paper &middot; pre-registered &middot; 18 September 2026</div>
  <h1>Grid equipment in world trade, 2012&ndash;2024: did prices or volumes carry the build-out?</h1>
  <p class="meta">Critical Materials Atlas. Pre-registration, code, data and review record:
  <a href="@@REPO@@">buildout-study</a>.</p>
</div></section>

<section class="wrap paper">
<div class="abstract"><b>Abstract.</b> Transformers, the grain-oriented electrical steel in their cores
and the copper in their windings are bought by every part of the electricity build-out. Official
sources record transformer lead times rising from under a year before 2020 to three years by 2024. We
ask what world trade shows, using @@NFY@@ exporter&ndash;importer&ndash;product flow-years from CEPII BACI,
2012&ndash;2024, in a design fixed before any estimate. Relative to heavy capital goods, transformer
trade showed no price or volume gap in 2021&ndash;22, when producer prices rose most, and in
2023&ndash;24 both rose: unit values by @@BP2@@ and tonnes by @@BV2@@. Traded supply rose with demand but
at a rising price. Net of the cost of electrical steel and copper, @@KEEP@@% of the 2023&ndash;24 price gap
remains. The comparison is a relative pattern, not a clean before-and-after: transformer unit values
had been falling relative to the controls through 2012&ndash;2019, so what the data show is a reversal.
Meanwhile world exports of grain-oriented electrical steel concentrated sharply: China's share rose
from @@G19C@@% to @@G24C@@% and the three largest exporters from @@G19T@@% to @@G24T@@%.</div>

<h2>1. Introduction</h2>
<p>Public discussion of the investment wave in computing and electrification concentrates on chips.
The equipment that carries electricity to them has had a harder run. Before the pandemic a large power
transformer could be ordered with a lead time of under a year; by 2024, "36-month lead times" were
"commonly quoted", with a maximum of 60 months@@C_DOE2024@@. Average lead times for large transformers
almost doubled from 2021&ndash;22 to 2023&ndash;24 and prices rose by around 75% in real terms, according
to the International Energy Agency's industry survey@@C_IEA2025@@. The US producer price index for power
and distribution transformers went from @@BLS19@@ in 2019 to @@BLS22@@ in 2022 and @@BLS24@@ in
2024@@C_BLS@@.</p>
<p>Those sources are national, or surveys. This paper asks what the <b>world trade</b> record shows, and
asks it in a form that separates two stories. A demand boom met by expanding supply raises the value of
trade through volumes. Demand meeting supply that cannot expand quickly raises it through prices. Prices
and volumes rising together is demand moving along an upward-sloping supply curve@@C_Shapiro2022@@@@C_KM2012@@,
and the ratio of the two says how steep that curve was. We therefore measure <b>how elastic traded supply
was</b>, relative to comparable goods, and how much of any transformer price rise is simply the cost of
the steel and copper inside it.</p>
<p>Four findings. <b>First</b>, in 2021&ndash;22, when the US producer price index rose most, transformer
trade showed no gap relative to heavy capital goods (unit value @@BP1@@, p&nbsp;=&nbsp;@@PP1@@; tonnes
@@BV1@@, p&nbsp;=&nbsp;@@PV1@@); the cost pressure of those years hit the control goods too. <b>Second</b>, in
2023&ndash;24 both unit values (@@BP2@@, p&nbsp;=&nbsp;@@PP2@@) and tonnes (@@BV2@@, p&nbsp;=&nbsp;@@PV2@@)
rose relative to the controls. <b>Third</b>, net of electrical-steel and copper costs, @@KEEP@@% of that
price gap remains, so materials alone do not explain it. <b>Fourth</b>, the trade in grain-oriented
electrical steel became far more concentrated, mostly in China. Section 7 states what none of this can
show.</p>

<h2>2. Background</h2>
<p><b>Lead times and prices.</b> The official record agrees on the direction and disagrees on
magnitudes. One large US utility's lead times went from 12&ndash;18 months to 18&ndash;36
months@@C_GAO2023@@. Manufacturing a transformer with materials in hand takes only weeks; the delay is
the order queue@@C_DOE2022@@. Manufacturers reported record order backlogs in 2024@@C_IEA2025@@.</p>
<p><b>Cost structure.</b> Grain-oriented electrical steel (GOES) and the copper conductor "each account
for roughly 25 percent of final LPT production costs"@@C_DOE2024@@@@C_BIS2020@@. GOES "prices have
doubled between 2021 and mid-2023"@@C_IEA2025@@. Copper is different: "from 2021 to 2023, supply grew at
a faster pace than demand, leading to a decline and stabilisation of prices"@@C_IEA2025@@. The United
States has one GOES producer, which can meet 12&ndash;20% of domestic demand@@C_DOE2024@@.</p>
<p><b>Evidence against a pure equipment story.</b> US large-transformer plants raised capacity
utilisation from 40% to 78% between 2011 and 2023, as reported by a national laboratory citing the US
International Trade Commission@@C_NLR2026@@: domestic output did respond. And "the primary cause of
delays in transmission projects remains permitting, particularly in advanced economies"@@C_IEA2025@@.</p>

<h2>3. Data</h2>
<p>Trade flows are CEPII BACI@@C_GZ2010@@, read in the HS 2002 nomenclature for every year so that no
code changes under the series. A <b>flow</b> is one exporter&ndash;importer pair in one six-digit customs
line. A flow-year enters if it is worth at least USD 100,000 and reports a positive tonnage; unit value is
value over tonnes, and flow-years more than ten times above or below their line's median in that year are
dropped as unit errors. The sample is @@NFY@@ flow-years.</p>
<div class="tbl"><table><thead><tr><th>Design</th><th>Treated lines</th><th>Control lines</th></tr></thead><tbody>
<tr><td>A. Inputs</td><td>GOES 7225.11, 7226.11; copper wire 7408.11</td><td>Other alloy flat steel 7225.30/.40/.50/.99; copper cathode 7403.11</td></tr>
<tr><td>B. Transformers</td><td>Liquid-dielectric transformers 8504.21 (&le;650 kVA), 8504.22 (650&ndash;10,000 kVA), 8504.23 (&gt;10,000 kVA)</td><td>Lifts 8428.10, cranes 8426.49, crushers 8474.20, concrete mixers 8474.31, welding machines 8515.31/.39</td></tr>
<tr><td>C. Transformers net of materials</td><td>As B, unit value minus 0.25 &times; real GOES unit value and 0.25 &times; real copper price</td><td>As B</td></tr>
</tbody></table></div>
<p>The controls are heavy capital goods containing steel and copper but with no grid, motor or vehicle
function; electric motors, pumps and compressors share the electrification demand and appear only as a
labelled robustness check. The copper price is the World Bank Pink Sheet; both it and the GOES unit
value are deflated by the US consumer price index before the adjustment in design C, so that only
relative input-cost movement is removed. The external benchmark is the BLS transformer producer price
index@@C_BLS@@.</p>

<h2>4. Method</h2>
<p>For flow <i>f</i> in line <i>l</i> and year <i>t</i>, in levels,</p>
<p style="text-align:center"><i>y</i><sub>ft</sub> = &beta;<sub>1</sub>(T<sub>l</sub> &times; 2021&ndash;22) + &beta;<sub>2</sub>(T<sub>l</sub> &times; 2023&ndash;24) + &alpha;<sub>f</sub> + &gamma;<sub>t</sub> + &epsilon;<sub>ft</sub>,</p>
<p>where <i>y</i> is the log unit value or log tonnes, T marks the treated lines, &alpha; are flow effects
and &gamma; year effects. Holding the flow fixed removes most of the product-mix change that makes
aggregate unit values unreliable@@C_Schott2004@@@@C_HS2011@@@@C_Silver2007@@, though not mix within a
flow. Because the treatment is a shock to a product market, inference is by a <b>wild cluster bootstrap
at the level of the customs line</b> (Webb weights, 9,999 draws, null imposed); exporter-clustered
errors are reported beside it. With @@NLINES@@ lines, this is deliberately conservative: the smallest
2023&ndash;24 price gap the transformer design could detect with 80% power is @@MDE@@ log points.</p>
<p>The design, thresholds and checks were filed before any estimate, after two independent language
models reviewed a first draft as referees; the draft, the filing, three dated deviations and the code
are in the <a href="@@REPO@@">study folder</a>. One filed rule failed and is reported as such: section 6.</p>

<h2>5. Results</h2>
<h3>5.1 Transformers: both price and volume, and only after 2022</h3>
<div class="tbl"><table><thead><tr><th rowspan="2">Comparison</th><th colspan="3">2021&ndash;22</th><th colspan="3">2023&ndash;24</th></tr>
<tr><th class="n">gap</th><th class="n">p</th><th class="n">95% interval</th><th class="n">gap</th><th class="n">p</th><th class="n">95% interval</th></tr></thead>
<tbody>@@MAINROWS@@</tbody></table></div>
<p class="meta">Gaps are log points relative to each design's 2012&ndash;2020 average, with the percent in brackets.
p-values and intervals are from the line-level wild bootstrap, except copper wire (one treated line
against one control line, where a line bootstrap cannot run: exporter-clustered).</p>
<p>In 2023&ndash;24 the value of transformer trade grew, relative to the controls, through prices and
volumes in about equal measure. In the language of section 1, demand rose along an upward-sloping traded
supply: not a price squeeze with frozen volumes, and not a volume boom at stable prices.</p>

<h3>5.2 A reversal, not a step</h3>
<figure class="fig">@@CHART@@
<figcaption><b>Transformers relative to heavy capital goods, by year.</b> Log points relative to 2019;
teal = unit value, navy = tonnes; whiskers are 95% line-bootstrap intervals; the shaded band is
2021&ndash;24.</figcaption></figure>
<p>The year-by-year gaps change how the table should be read. Transformer unit values were falling
relative to the controls for most of the decade, from @@EV12@@ in 2012 to zero in 2019, and then rose to
@@EV24@@ in 2024. Relative tonnes were @@EVV12@@ in 2012, level from 2018, and @@EVV24@@ in 2024. The
average-gap coefficients compare 2023&ndash;24 with a pre-period that was itself drifting, so they
understate the size of the turn and overstate how clean it is.</p>

<h3>5.3 How much is steel and copper</h3>
<p>Taking out a quarter of the real change in the GOES unit value and a quarter of the real change in the
copper price leaves a 2021&ndash;22 gap of @@CN1@@ (p&nbsp;=&nbsp;@@PC1@@) and a 2023&ndash;24 gap of
@@CN2@@ (p&nbsp;=&nbsp;@@PC2@@). In the earlier period, material costs more than account for the
transformer unit values; in the later one, @@KEEP@@% of the gap remains (a net gap of @@S20@@ with cost shares of 20% each,
@@S30@@ with 30% each). By the filed rule, the 2023&ndash;24 rise is not explained by those two
materials alone. Tank steel, oil and labour are not netted out; no verified source gives their shares.</p>

<h3>5.4 The inputs</h3>
<p><b>Copper wire</b> shows no build-out signature: its premium over copper cathode moved by
@@CUP1@@ (p&nbsp;=&nbsp;@@CUPp1@@) in 2021&ndash;22 and was flat afterwards (@@CUP2@@), as the IEA's
account of copper supply outrunning demand would predict@@C_IEA2025@@. <b>Grain-oriented electrical
steel</b> shows a 2023&ndash;24 unit-value gap of @@GP2@@ (p&nbsp;=&nbsp;@@GPp2@@), but its placebo fails:
in a fake 2015&ndash;16 post period it moves by @@GPL@@ (p&nbsp;=&nbsp;@@GPLp@@). Its prices swing that much in
ordinary years, so the trade data cannot distinguish its post-2021 movement from its normal volatility.</p>

<h3>5.5 Who supplied it</h3>
<div class="tbl"><table><thead><tr><th rowspan="2">Line</th><th colspan="3">2019</th><th colspan="3">2024</th></tr>
<tr><th class="n">exporters &gt;1%</th><th class="n">China</th><th class="n">top 3</th><th class="n">exporters &gt;1%</th><th class="n">China</th><th class="n">top 3</th></tr></thead>
<tbody>@@SUPROWS@@</tbody></table></div>
<p>The price and volume of GOES trade are hard to read; its structure is not. Between 2019 and 2024 the
number of exporters above 1% of world GOES exports fell from @@G19N@@ to @@G24N@@, the three largest went
from @@G19T@@% to @@G24T@@% of the market, and China's share rose from @@G19C@@% to @@G24C@@%, as Russian
exports, about a tenth of world capacity, fell under sanctions@@C_IEA2023@@. The transformer lines
themselves stayed broadly supplied.</p>

<h3>5.6 Where it landed</h3>
<div class="tbl"><table><thead><tr><th>Importer, 2023&ndash;24</th><th class="n">unit value</th><th class="n">p</th><th class="n">tonnes</th><th class="n">p</th><th class="n">net of materials</th><th class="n">p</th></tr></thead>
<tbody>@@IMPROWS@@</tbody></table></div>
<p>The United States and the European Union tell different stories. Into the United States, tonnes rose
by @@USVP@@ relative to the controls (p&nbsp;=&nbsp;@@USVp@@) while the unit-value gap net of materials was
@@USC@@ (p&nbsp;=&nbsp;@@USCp@@): the US adjustment ran through volume, consistent with the rise in US
transformer imports the national laboratories record@@C_NLR2026@@. Into the European Union both moved,
prices by @@EUP@@ and tonnes by @@EUV@@, and a gap of @@EUC@@ remained after materials
(p&nbsp;=&nbsp;@@EUCp@@).</p>

<h2>6. Robustness, and the rule that failed</h2>
<div class="box"><b>The pre-trend rule failed.</b> The filing required every pre-period year from 2014
to 2018 to lie within &plusmn;0.05 log points of 2019 before difference-in-differences language could be
used. No design met it. The results above are therefore described as relative patterns, and the
reversal in section 5.2 is the honest reading.</div>
<ul>
<li><b>Placebo period.</b> Transformers in a fake 2015&ndash;16 post period: @@BPL@@ (p&nbsp;=&nbsp;@@BPLp@@),
consistent with the pre-2019 decline and not with a spurious rise.</li>
<li><b>Unit-value band.</b> The 2023&ndash;24 price gap is @@B02@@ with the band at 0.2&ndash;5 times the
median and @@BNO@@ with no band.</li>
<li><b>Leave one line out.</b> Dropping any single treated or control line leaves the 2023&ndash;24 price
gap between @@LOOLO@@ and @@LOOHI@@.</li>
<li><b>Freight.</b> Heavy, low-value flows, where freight costs bite: @@HV2@@ (p&nbsp;=&nbsp;@@HVp2@@);
light, high-value flows: @@LT2@@ (p&nbsp;=&nbsp;@@LTp2@@). The gap sits in the heavier flows, but in
2023&ndash;24, after the 2021&ndash;22 freight spike had passed.</li>
<li><b>Exporters.</b> The 2023&ndash;24 price gap is @@CHN2@@ for flows from China and @@NCHN2@@ for all other
exporters.</li>
<li><b>Contaminated controls.</b> Against motors, pumps and compressors, which share the electrification
demand, the gap shrinks to @@CONT@@ (p&nbsp;=&nbsp;@@CONTp@@), as it should if those goods rose too.</li>
<li><b>Are unit values prices?</b> The annual change in the unit value of US transformer imports
correlates with the change in the BLS producer price index at only @@BLSC@@ (levels: @@BLSL@@). Unit values
carry product mix as well as price, and every price result here inherits that weakness.</li>
</ul>

<h2>7. What this cannot say</h2>
<ul>
<li><b>Nothing about AI or data centres specifically.</b> Every buyer of grid equipment is in these
flows: utilities, renewable developers, factories, vehicle makers.</li>
<li><b>Nothing about domestic production.</b> A country that builds its own transformers never appears
in trade. US plants' rising utilisation is outside these data.</li>
<li><b>Unit values are not prices.</b> Within a six-digit line, a shift towards larger or more efficient
transformers raises unit value without any price change; the price gaps are upper bounds.</li>
<li><b>Not causal, and silent on why.</b> The data show that traded supply rose at a rising price; they
do not show whether factories, electrical steel, skilled labour or permitting was the constraint, and the
IEA names permitting as the main cause of transmission delays in advanced economies@@C_IEA2025@@.</li>
<li><b>Chip-making equipment is not tested.</b> Its unit values per tonne measure which machines were
shipped. Its trade grew from $@@CHIP12@@bn in 2012 to $@@CHIP24@@bn in 2024; the largest exporters in 2024
were @@CHIPTOP@@.</li>
</ul>

<h2>8. Conclusion</h2>
<p>World trade in transformers carried the electricity build-out through both prices and volumes, and
only from 2023: traded supply expanded, but at a rising price, after a decade in which transformers had
been getting cheaper relative to comparable capital goods. The cost of steel and copper explains the
2021&ndash;22 movement and @@MATSHARE@@% of the later one. The part of the chain that became genuinely
more concentrated is the steel inside the transformer, where one country now supplies over a third of
world exports and the three largest over two-thirds. For a buyer, the practical reading is that
transformer supply did respond to demand, but through the order book and the price; for a policy
maker, the concentration in electrical steel, not in transformers, is the exposure the trade data can
see.</p>

<h2>Review record</h2>
<p>The design was reviewed before filing by two independent language models acting as journal referees;
both named input costs, weak controls and over-claiming as the main problems, and the filing records
what changed. The literature was assembled by a research agent under a rule that every source be
opened and quoted before use; sources it could not open are listed as such. The result will be reviewed
by the same two referees before this page is published.</p>

<h2>References</h2>
<ol class="refs">@@REFS@@</ol>
<p class="meta">Data: CEPII BACI (Etalab Open Licence 2.0), World Bank Pink Sheet and CPI (CC BY 4.0),
BLS (public domain). Built by <code>build_grid_trade_paper.py</code> from <code>out/buildout_study.json</code>.
Cite as: Critical Materials Atlas (2026). Zenodo. https://doi.org/10.5281/zenodo.21948855</p>
</section>
@@FOOT@@
</body></html>
""".replace('@@NAV@@', NAV).replace('@@FOOT@@', FOOT)


if __name__ == '__main__':
    main()
