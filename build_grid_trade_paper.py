# -*- coding: utf-8 -*-
"""Research note for buildout-study/: transformers and electrical steel in world trade, 2012-2024.

Every number on the page is read from out/buildout_study.json (written by buildout-study/analysis.py,
committed before its first run) or from buildout-study/exploratory_electrical_boom.json (an unfiled,
labelled exploratory check). Nothing here computes a result. References are copied from
buildout-study/literature.md, where each source was opened and quoted on 2026-09-18.

The study was filed as a test. Its pre-trend rule failed and three reviewers showed that the
transformer-specific reading does not survive a comparison with other electrical equipment, so the
page is written as a descriptive note, and says why.

Writes grid-trade.html.  Usage: python build_grid_trade_paper.py
"""
import io
import json
import math
import os
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
REPO = 'https://github.com/materials-atlas/critical-materials-atlas/blob/main/buildout-study/'
DOC = os.path.join(ROOT, 'out', 'buildout_study.json')
EXPL = os.path.join(ROOT, 'buildout-study', 'exploratory_electrical_boom.json')
OUT = os.path.join(ROOT, 'grid-trade.html')

NAMES = {'CHN': 'China', 'JPN': 'Japan', 'RUS': 'Russia', 'DEU': 'Germany', 'KOR': 'South Korea',
         'MEX': 'Mexico', 'TUR': 'Türkiye', 'USA': 'the United States', 'NLD': 'the Netherlands',
         'SGP': 'Singapore'}

REFS = [
    ('DOE2024', 'U.S. Department of Energy (2024). <i>Large Power Transformer Resilience: Report to Congress</i>. July 2024.',
     'https://www.energy.gov/sites/default/files/2024-10/EXEC-2022-001242%20-%20Large%20Power%20Transformer%20Resilience%20Report%20signed%20by%20Secretary%20Granholm%20on%207-10-24.pdf'),
    ('DOE2022', 'U.S. Department of Energy (2022). <i>Electric Grid Supply Chain Review: Large Power Transformers and High Voltage Direct Current Systems. Supply Chain Deep Dive Assessment</i>. February 2022.',
     'https://www.energy.gov/sites/default/files/2022-02/Electric%20Grid%20Supply%20Chain%20Report%20-%20Final.pdf'),
    ('GAO2023', 'U.S. Government Accountability Office (2023). <i>Electricity Grid: DOE Could Better Support Industry Efforts to Ensure Adequate Transformer Reserves</i>. GAO-23-106180.',
     'https://www.gao.gov/products/gao-23-106180'),
    ('IEA2023', 'International Energy Agency (2023). <i>Electricity Grids and Secure Energy Transitions</i>. Paris, October 2023.',
     'https://www.iea.org/reports/electricity-grids-and-secure-energy-transitions'),
    ('IEA2025', 'International Energy Agency (2025). <i>Building the Future Transmission Grid: Strategies to Navigate Supply Chain Challenges</i>. Paris, February 2025.',
     'https://www.iea.org/reports/building-the-future-transmission-grid'),
    ('NLR2026', 'Ramasamy, V., Cooperman, A., Jayswal, R. and Seward, M. (2026). <i>Large Power Transformer Supply Chain Gap Analysis and Domestic Content Strategies for Hydropower Rehabilitation: Supplemental Report</i>. NLR/TP-5700-96742, National Laboratory of the Rockies.',
     'https://docs.nlr.gov/docs/fy26osti/96742.pdf'),
    ('BLS', 'U.S. Bureau of Labor Statistics. <i>PPI by Commodity: Machinery and Equipment: Power and Distribution Transformers, Except Parts</i> (WPU117409), annual average of monthly values.',
     'https://fred.stlouisfed.org/series/WPU117409'),
    ('GZ2010', 'Gaulier, G. and Zignago, S. (2010). "BACI: International Trade Database at the Product-Level. The 1994-2007 Version." CEPII Working Paper 2010-23.',
     'http://www.cepii.fr/PDF_PUB/wp/2010/wp2010-23.pdf'),
    ('Schott2004', 'Schott, P. K. (2004). "Across-Product Versus Within-Product Specialization in International Trade." <i>Quarterly Journal of Economics</i> 119(2): 647-678.',
     'https://doi.org/10.1162/0033553041382201'),
    ('Silver2007', 'Silver, M. (2007). "Do Unit Value Export, Import, and Terms of Trade Indices Represent or Misrepresent Price Indices?" IMF Working Paper 07/121.',
     'https://doi.org/10.5089/9781451866858.001'),
    ('Shapiro2022', 'Shapiro, A. H. (2022). "Decomposing Supply and Demand Driven Inflation." Federal Reserve Bank of San Francisco Working Paper 2022-18.',
     'https://doi.org/10.24148/wp2022-18'),
]
REFNUM = {k: i + 1 for i, (k, _, _) in enumerate(REFS)}
PCT = {}


def cite(*keys):
    return '<sup class="cite">[%s]</sup>' % ','.join('<a href="#ref-%s">%d</a>' % (k, REFNUM[k]) for k in keys)


def r0(x):
    """Conventional rounding (half up), so 12.5 prints as 13 and not as 12."""
    return int(Decimal(str(x)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def pct(b):
    v = PCT.get(round(b, 4))
    v = v if v is not None else 100 * (math.exp(b) - 1)
    return ('%+d%%' % r0(v)) if r0(v) != 0 else '0%'


def pct_raw(b):
    """A log-point bound shown as a percent, so an interval sits in the same unit as its estimate."""
    return '%+d%%' % r0(100 * (math.exp(b) - 1))


def sh(x):
    return '%d%%' % r0(100 * x)


def fp(p):
    return '&lt;0.001' if p < 0.001 else ('%.3f' % p)


def num(x, fmt='%+.2f'):
    """Signed number. Where two decimals would print 0.00 for a value that is not zero, three are
    used, so an interval that crosses zero never loses its minus sign."""
    s = fmt % x
    if s in ('-0.00', '+0.00'):
        return '0' if x == 0 else '%+.3f' % x
    return s


def _collect(o):
    if isinstance(o, dict):
        if 'beta' in o and 'pct' in o:
            PCT[round(o['beta'], 4)] = o['pct']
        for v in o.values():
            _collect(v)
    elif isinstance(o, list):
        for v in o:
            _collect(v)


def coef(e, n):
    v = e['coefs'][n] if 'coefs' in e else e[n]
    return v['beta'], v.get('p_wild_line', v.get('p_cluster_exporter')), v


def event_chart(price, volume):
    W, H, L, R, T, B = 720, 300, 52, 118, 18, 36
    years = sorted(int(y) for y in price)
    lo = min(min(v['ci95'][0] for v in price.values()), min(v['ci95'][0] for v in volume.values()))
    hi = max(max(v['ci95'][1] for v in price.values()), max(v['ci95'][1] for v in volume.values()))
    lo, hi = math.floor(lo * 10) / 10, math.ceil(hi * 10) / 10

    def x(y):
        return L + (y - years[0]) / (years[-1] - years[0]) * (W - L - R)

    def yv(v):
        return T + (hi - v) / (hi - lo) * (H - T - B)
    g = ['<rect x="%.1f" y="%d" width="%.1f" height="%d" class="post"/>'
         % (x(2020.5), T, x(2024) - x(2020.5) + 8, H - T - B)]
    tick = lo
    while tick <= hi + 1e-9:
        g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="%s"/>'
                 % (L, W - R, yv(tick), yv(tick), 'zero' if abs(tick) < 1e-9 else 'grid'))
        g.append('<text x="%d" y="%.1f" class="ax" text-anchor="end">%s</text>'
                 % (L - 6, yv(tick) + 4, '0' if abs(tick) < 1e-9 else '%+.1f' % tick))
        tick = round(tick + 0.1, 10)
    for y in years:
        if y % 2 == 0 or y == 2019:
            g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%d</text>' % (x(y), H - B + 18, y))
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
        g.append('<text x="%.1f" y="%.1f" class="lab %s">%s %s</text>'
                 % (pts[-1][0] + 10, pts[-1][1] + 4, cls, label, num(series[str(years[-1])]['beta'])))
    return ('<svg viewBox="0 0 %d %d" role="img" aria-label="Year-by-year gap between transformers and '
            'construction and handling machinery relative to 2019, for unit values and tonnes, with 95%% '
            'intervals">%s</svg>' % (W, H, ''.join(g)))


def main():
    d = json.load(io.open(DOC, encoding='utf-8'))
    x = json.load(io.open(EXPL, encoding='utf-8'))
    _collect(d)
    _collect(x)
    D, C = d['designs'], d['checks']
    B, Cn, Cg = D['B_transformers'], D['C_net_of_materials'], D['C_goes_only']
    bp2, pp2, vp2 = coef(B['price'], 'TxP2')
    bv2, pv2, _ = coef(B['volume'], 'TxP2')
    cont_p, cont_pp, _ = coef(C['contaminated_controls']['price'], 'TxP2')
    cont_v, cont_vp, _ = coef(C['contaminated_controls']['volume'], 'TxP2')
    ele_p, ele_pp, _ = coef(x['luv'], 'TxP2')
    ele_v, ele_vp, _ = coef(x['lq'], 'TxP2')
    ev_p, ev_v = C['event_study']['B_price'], C['event_study']['B_volume']
    gc = C['suppliers_goes_combined']
    bls = C['bls_validation']
    per_line = {k: coef(D['B_' + k]['price'], 'TxP2') for k in ('850421', '850422', '850423')}
    cn1, _, _ = coef(Cn['price'], 'TxP1')
    cg2, _, _ = coef(Cg['price'], 'TxP2')
    cg1, _, _ = coef(Cg['price'], 'TxP1')
    chip = d['chip_equipment_described_only']['848620']
    us, eu, rest = C['importer_USA'], C['importer_EU27'], C['importer_rest']

    def trow(label, e, n='TxP2'):
        b, p, v = coef(e, n)
        ci = v.get('ci95_wild_line')
        return ('<tr><td>%s</td><td class="n">%s <span class="mut">(%s)</span></td><td class="n">%s</td>'
                '<td class="n mut">%s</td></tr>' % (label, num(b, '%+.3f'), pct(b), fp(p),
                                                    ('%s to %s' % (num(ci[0]), num(ci[1]))) if ci else 'exporter-clustered'))

    core_rows = ''.join([
        trow('Transformers vs the filed comparison machinery &mdash; unit value', B['price']),
        trow('Transformers vs the filed comparison machinery &mdash; tonnes', B['volume']),
        trow('Transformers vs construction machinery only (welding machines removed) &mdash; unit value <span class="tag">exploratory</span>',
             x['transformers_vs_construction_only_luv']),
        trow('Transformers vs construction machinery only &mdash; tonnes <span class="tag">exploratory</span>',
             x['transformers_vs_construction_only_lq']),
        trow('Motors, pumps, compressors vs the filed comparison machinery &mdash; unit value <span class="tag">exploratory</span>', x['luv']),
        trow('Motors, pumps, compressors vs the filed comparison machinery &mdash; tonnes <span class="tag">exploratory</span>', x['lq']),
        trow('Transformers vs motors, pumps, compressors &mdash; unit value', C['contaminated_controls']['price']),
        trow('Transformers vs motors, pumps, compressors &mdash; tonnes', C['contaminated_controls']['volume']),
    ])
    mat_rows = ''.join([
        trow('Unit value, no netting (as above)', B['price']),
        trow('Net of electrical steel only (an input most of the comparison goods do not use)', Cg['price']),
        trow('Net of electrical steel and copper, 25% each (as filed)', Cn['price']),
    ])

    def imp_row(name, e):
        cells = []
        for k in ('B_price', 'B_volume'):
            b, p, v = coef(e[k], 'TxP2')
            ci = v['ci95_wild_line']
            cells.append('<td class="n">%s</td><td class="n mut">%s to %s</td>'
                         % (pct(b), pct_raw(ci[0]), pct_raw(ci[1])))
        return '<tr><td>%s</td>%s</tr>' % (name, ''.join(cells))
    imp_rows = imp_row('United States', us) + imp_row('European Union (27)', eu) + imp_row('Rest of the world', rest)

    goes_rows = ''.join(
        '<tr><td>%s</td><td class="n">$%.1fbn</td><td class="n">%d</td><td class="n">%s</td><td class="n">%s</td>'
        '<td class="n">%s</td><td class="n">%s</td></tr>'
        % (y, gc[y]['value_musd'] / 1000.0, gc[y]['exporters_above_1pct'], sh(gc[y]['china_share']),
           sh(gc[y]['japan_share']), sh(gc[y]['russia_share']), sh(gc[y]['top3_share']))
        for y in ('2019', '2022', '2024'))

    refs = ''.join('<li id="ref-%s">%s <a href="%s">%s</a></li>'
                   % (k, t, u, u.replace('https://', '').replace('http://', '').split('/')[0]) for k, t, u in REFS)

    subs = {
        'NFY': format(d['sample']['flow_years'], ','),
        'BP2': pct(bp2), 'BV2': pct(bv2),
        'ELP': pct(ele_p), 'ELV': pct(ele_v), 'ELPp': fp(ele_pp), 'ELVp': fp(ele_vp),
        'COP': pct(cont_p), 'COPp': fp(cont_pp), 'COV': pct(cont_v), 'COVp': fp(cont_vp),
        'EV22': num(ev_p['2022']['beta']), 'EV23': num(ev_p['2023']['beta']), 'EV24': num(ev_p['2024']['beta']),
        'EV12': num(ev_p['2012']['beta']), 'EVV23': num(ev_v['2023']['beta']), 'EVV24': num(ev_v['2024']['beta']),
        'EVV17': num(ev_v['2017']['beta']), 'EVV18': num(ev_v['2018']['beta']),
        'CO2P': pct(x['transformers_vs_construction_only_luv']['TxP2']['beta']),
        'CO2V': pct(x['transformers_vs_construction_only_lq']['TxP2']['beta']),
        'LOWUV': pct(C['freight_heavy_low_uv']['coefs']['TxP2']['beta']),
        'LOWUVp': fp(C['freight_heavy_low_uv']['coefs']['TxP2']['p_wild_line']),
        'HIUV': pct(C['freight_light_high_uv']['coefs']['TxP2']['beta']),
        'HIUVp': fp(C['freight_light_high_uv']['coefs']['TxP2']['p_wild_line']),
        'RESULTS': 'https://github.com/materials-atlas/critical-materials-atlas/blob/main/out/buildout_study.json',
        'USVL': pct_raw(C['importer_USA']['B_volume']['coefs']['TxP2']['ci95_wild_line'][0]),
        'USVH': pct_raw(C['importer_USA']['B_volume']['coefs']['TxP2']['ci95_wild_line'][1]),
        'EVV24L': num(ev_v['2024']['ci95'][0]), 'EVV24H': num(ev_v['2024']['ci95'][1]),
        'EV24L': num(ev_p['2024']['ci95'][0]), 'EV24H': num(ev_p['2024']['ci95'][1]),
        'CHART': event_chart(ev_p, ev_v),
        'COREROWS': core_rows, 'MATROWS': mat_rows, 'IMPROWS': imp_rows, 'GOESROWS': goes_rows,
        'G19C': sh(gc['2019']['china_share']), 'G24C': sh(gc['2024']['china_share']),
        'G19R': sh(gc['2019']['russia_share']), 'G24R': sh(gc['2024']['russia_share']),
        'G19T': sh(gc['2019']['top3_share']), 'G24T': sh(gc['2024']['top3_share']),
        'G19N': str(gc['2019']['exporters_above_1pct']), 'G24N': str(gc['2024']['exporters_above_1pct']),
        'G19J': sh(gc['2019']['japan_share']), 'G24J': sh(gc['2024']['japan_share']),
        'CG1': pct(cg1), 'CG2': pct(cg2), 'CN1': pct(cn1),
        'PL21': '%s, %s and %s' % tuple(pct(per_line[k][0]) for k in ('850421', '850422', '850423')),
        'PLP': '%s, %s and %s' % tuple(fp(per_line[k][1]) for k in ('850421', '850422', '850423')),
        'MDE': '%.2f' % vp2['mde_80'], 'NLINES': str(vp2['lines_in_bootstrap']),
        'BLSC': '%.2f' % bls['corr_annual_changes'],
        'BLS19': '%.0f' % bls['ppi']['2019'], 'BLS22': '%.0f' % bls['ppi']['2022'], 'BLS24': '%.0f' % bls['ppi']['2024'],
        'GPL': num(C['placebo_2015_16_A_goes']['coefs']['TxP1']['beta']),
        'GPLp': fp(C['placebo_2015_16_A_goes']['coefs']['TxP1']['p_wild_line']),
        'CHIP17': '%.0f' % (chip['2017']['value_musd'] / 1000.0), 'CHIP24': '%.0f' % (chip['2024']['value_musd'] / 1000.0),
        'CHIPTOP': ', '.join('%s (%s)' % (NAMES.get(i, i), sh(s)) for i, s in chip['2024']['top3']),
        'CHN21V': pct(coef(C['exporter_China']['B_volume'], 'TxP1')[0]),
        'CHN21Vp': fp(coef(C['exporter_China']['B_volume'], 'TxP1')[1]),
        'REFS': refs, 'REPO': REPO,
    }
    for k in REFNUM:
        subs['C_' + k] = cite(k)
    html = TEMPLATE
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
<title>Transformers and electrical steel in world trade, 2012&ndash;2024 &mdash; Critical Materials Atlas</title>
<meta name="description" content="A research note from a pre-registered study of world trade in transformers and grain-oriented electrical steel: what the customs record shows after 2021, what it cannot separate, and how the supply of electrical steel concentrated.">
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
.tag{font-size:.72rem;background:#eef2f1;color:#15323a;padding:.05rem .35rem;border-radius:3px;white-space:nowrap}
.tbl{overflow-x:auto;margin:.8rem 0}
.tbl table{border-collapse:collapse;width:100%;font-size:.86rem;min-width:36rem}
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
  <div class="eyebrow">Research note &middot; from a pre-registered study &middot; 18 September 2026</div>
  <h1>Transformers and electrical steel in world trade, 2012&ndash;2024</h1>
  <p class="meta">Critical Materials Atlas. Filing, code, data, deviations and review record:
  <a href="@@REPO@@">buildout-study</a>.</p>
</div></section>

<section class="wrap paper">
<div class="abstract"><b>Abstract.</b> Official sources record transformer lead times rising from under
a year before 2020 to about three years by 2024. We set out to test, in world trade data, whether the
build-out showed up in transformer prices or volumes. The test was pre-registered; its pre-trend rule
failed, and review showed that the result is not specific to transformers, so this is a descriptive
note. From @@NFY@@ exporter&ndash;importer&ndash;product flow-years (CEPII BACI, 2012&ndash;2024), four things
can be said. <b>Goods that share the demand of electrification</b> &mdash; transformers, and electric
motors, pumps and compressors &mdash; rose in unit value and in tonnes relative to a set of heavy machinery
(lifts, cranes, crushers, concrete mixers and welding machines) after 2020. <b>Transformers rose more than
motors, pumps and compressors taken together</b>: in 2023&ndash;24 their unit values stood @@BP2@@ and their
tonnes @@BV2@@ above that machinery, against @@ELP@@ and @@ELV@@; but the part specific to transformers
(@@COP@@ in unit value, p&nbsp;=&nbsp;@@COPp@@) is at the edge of what these data can detect. <b>How much is the
cost of steel and copper</b> cannot be settled here. And <b>world exports of grain-oriented electrical
steel</b>, the core of every transformer, concentrated: China's share of export value rose from @@G19C@@ to
@@G24C@@ and the three largest exporters' from @@G19T@@ to @@G24T@@ between 2019 and 2024. Unit values are
not prices; they track the US transformer producer price index only moderately.</div>

<h2>1. What we set out to test, and why this is a note</h2>
<p>Before the pandemic a large power transformer could be ordered with a lead time of under a year; by
2024 "36-month lead times" were "commonly quoted", with a maximum of 60 months@@C_DOE2024@@. Average lead
times for large power transformers almost doubled from 2021&ndash;22 to 2023&ndash;24, and power-transformer
prices rose by around 75% in real terms since 2019, according to the International Energy Agency's industry
survey@@C_IEA2025@@. The US producer price index for power and distribution transformers averaged @@BLS19@@
in 2019, @@BLS22@@ in 2022 and @@BLS24@@ in 2024@@C_BLS@@.</p>
<p>Those are national figures and surveys. We asked what world trade shows, and whether the rise in its
value came through prices or through volumes. In demand-and-supply terms, prices and quantities moving
together indicate demand shifting along a supply curve@@C_Shapiro2022@@; we hoped to measure how steep that
curve was for traded grid equipment. The design was filed before any estimate, after two independent
language models reviewed a draft as referees and a research agent assembled the literature under a rule
that every source be opened before use.</p>
<p>Two things turned the test into a description. <b>The filed pre-trend rule failed</b>: transformer
unit values were drifting relative to the controls long before 2021, so the before-and-after comparisons
cannot be read as effects. And the referees' objection that <b>the pattern may be a boom in electrical
equipment generally</b> turned out to be right: against motors, pumps and compressors, the transformer
gap is no longer clearly different from zero. What follows reports what the trade record shows, labels
what could not be separated, and says what would settle it.</p>

<h2>2. Background</h2>
<p>A utility's lead times for large transformers went from 12&ndash;18 months to 18&ndash;36
months@@C_GAO2023@@. With materials in hand, manufacturing takes 12 to 16 weeks, but lead times for the
inputs lengthened too@@C_DOE2022@@. Manufacturers reported record order backlogs in 2024@@C_IEA2025@@.</p>
<p>Grain-oriented electrical steel (GOES) and the copper conductor "each account for roughly 25 percent
of final LPT production costs"@@C_DOE2024@@, and labour on average 36 percent of manufacturing
cost@@C_DOE2024@@. GOES prices rose 70% in 2022 compared with 2020@@C_IEA2023@@ and "doubled between 2021
and mid-2023"@@C_IEA2025@@. Russia accounted for almost 10% of global GOES production capacity in 2020
and its exports were sanctioned@@C_IEA2023@@. The United States has one GOES producer, which can meet
12&ndash;20% of domestic demand@@C_DOE2024@@.</p>
<p>Against a pure equipment story: US large-transformer plants raised capacity utilisation from 40% to
78% between 2011 and 2023, as reported by a national laboratory citing the US International Trade
Commission@@C_NLR2026@@; and "the primary cause of delays in transmission projects remains permitting,
particularly in advanced economies"@@C_IEA2025@@.</p>

<h2>3. Data and method</h2>
<p>Trade flows are CEPII BACI@@C_GZ2010@@ in the HS 2002 nomenclature for every year, so no code changes
under the series. A flow is one exporter&ndash;importer pair in one six-digit line; a flow-year enters at
USD 100,000 or more with a positive tonnage, and unit values more than ten times above or below the
line's median that year are dropped. The transformer lines are liquid-dielectric transformers 8504.21
(up to 650 kVA), 8504.22 (over 650 up to 10,000 kVA) and 8504.23 (over 10,000 kVA). The filed comparison
goods are lifts, cranes, crushers, concrete mixers and electric welding machines. Welding machines are
themselves electrical equipment, so a construction-only version without them is reported beside the
filed one. Electric motors (8501.52/53), pumps (8413.70) and compressors (8414.80) were filed as a check
on shared electrification demand.</p>
<p>Each estimate compares a flow with itself over time (flow and year effects), which removes some of
the product-mix change that makes aggregate unit values unreliable@@C_Schott2004@@@@C_Silver2007@@ but
not mix within a flow. The gaps below are averages over 2023&ndash;24 against 2012&ndash;2020. Because the
shock is to product markets, inference is a wild bootstrap clustered by customs line; with
@@NLINES@@ lines, a p-value near 0.01 is suggestive, not conclusive, and the smallest 2023&ndash;24 gap
the main comparison could reliably detect is @@MDE@@ log points.</p>

<h2>4. What the trade record shows</h2>
<h3>4.1 Transformers rose: first in unit value, late in tonnes</h3>
<figure class="fig">@@CHART@@
<figcaption><b>Transformers relative to the filed comparison machinery, by year.</b> Log points
relative to 2019; teal = unit value, navy = tonnes; whiskers are 95% intervals from the same
line-level bootstrap as the tables; shaded: 2021&ndash;24.</figcaption></figure>
<p>Relative to the comparison machinery, transformer unit values fell from @@EV12@@ in 2012 to zero in
2019, were already @@EV22@@ in 2022, and reached @@EV23@@ in 2023 and @@EV24@@ in 2024 (interval
@@EV24L@@ to @@EV24H@@). Relative tonnes rose from @@EVV17@@ in 2017 to @@EVV18@@ in 2018, stayed roughly
level through 2023 (@@EVV23@@), and reached @@EVV24@@ in 2024 (@@EVV24L@@ to @@EVV24H@@). The relative rise
appears in unit values first and in tonnes only in the last year.</p>

<h3>4.2 Not only transformers</h3>
<div class="tbl"><table><thead><tr><th>2023&ndash;24, relative to 2012&ndash;2020</th><th class="n">gap</th><th class="n">p</th><th class="n">95% interval</th></tr></thead>
<tbody>@@COREROWS@@</tbody></table></div>
<p class="meta"><span class="tag">exploratory</span> rows were not in the filing; they were run after review
to answer the referees' question directly and are labelled wherever they appear.</p>
<p>Against construction machinery alone, without the welding machines, the transformer gaps are
@@CO2P@@ in unit value and @@CO2V@@ in tonnes, close to the filed comparison. Motors, pumps and compressors
also rose relative to the filed comparison machinery: @@ELP@@ in unit value (p&nbsp;=&nbsp;@@ELPp@@) and
@@ELV@@ in tonnes (p&nbsp;=&nbsp;@@ELVp@@). Transformers rose about twice as much as those goods taken
together. Measured directly against them, the transformer gap is @@COP@@ in unit value
(p&nbsp;=&nbsp;@@COPp@@) and @@COV@@ in tonnes (p&nbsp;=&nbsp;@@COVp@@), with intervals that include zero. The
honest reading is that goods sharing the demand of electrification gained on other heavy machinery after
2020, transformers more than the others, and that nine customs lines cannot establish how much of the
transformer excess is specific to transformers.
The three transformer size classes point the same way (@@PL21@@) but none is distinguishable from zero on
its own (p = @@PLP@@).</p>

<h3>4.3 Steel and copper: unsettled</h3>
<div class="tbl"><table><thead><tr><th>Transformer unit value, 2023&ndash;24</th><th class="n">gap</th><th class="n">p</th><th class="n">95% interval</th></tr></thead>
<tbody>@@MATROWS@@</tbody></table></div>
<p>The filed adjustment nets a quarter of the real change in the GOES unit value and a quarter of the real
change in the copper price from transformers only. The referees showed why that is fragile: the comparison
machinery also contains copper and ordinary steel, and because both input prices peaked in 2021&ndash;22,
netting them from one side alone pushes the earlier gap down (@@CN1@@) and so widens the rise from
2021&ndash;22 to 2023&ndash;24 almost mechanically. Netting only electrical steel, which most of the
comparison goods do not use, leaves @@CG1@@ in 2021&ndash;22 and @@CG2@@ in 2023&ndash;24. Neither version
accounts for labour, about 36% of manufacturing cost for large units, or for the long lag between order
and delivery, which means 2023&ndash;24 shipments may have been priced on earlier inputs. How much of the transformer rise is materials is not settled by these data.</p>

<h3>4.4 World exports of electrical steel concentrated</h3>
<div class="tbl"><table><thead><tr><th>GOES, 7225.11 + 7226.11</th><th class="n">world exports</th><th class="n">exporters &gt;1%</th><th class="n">China</th><th class="n">Japan</th><th class="n">Russia</th><th class="n">top 3</th></tr></thead>
<tbody>@@GOESROWS@@</tbody></table></div>
<p>This is the clearest fact in the trade record, and it does not depend on unit values or on any
comparison group; the shares are shares of export value. Between 2019 and 2024 China's share of world GOES
exports rose from @@G19C@@ to @@G24C@@, Russia's fell
from @@G19R@@ to @@G24R@@ after sanctions, and Japan's stayed near a quarter (@@G19J@@ and @@G24J@@). The
number of exporters with more than 1% of the market fell from @@G19N@@ to @@G24N@@ and the three largest
went from @@G19T@@ to @@G24T@@. The price of GOES in trade, by contrast, cannot be read: in a placebo
period, 2015&ndash;16, its unit value moved by @@GPL@@ (p&nbsp;=&nbsp;@@GPLp@@) relative to other alloy steel,
so its post-2021 movements are within its normal swings.</p>

<h3>4.5 Where the transformers went</h3>
<div class="tbl"><table><thead><tr><th>Importer, 2023&ndash;24</th><th class="n">unit value</th><th class="n">95% interval</th><th class="n">tonnes</th><th class="n">95% interval</th></tr></thead>
<tbody>@@IMPROWS@@</tbody></table></div>
<p>The intervals for single importing regions are wide; the US tonnage estimate in particular runs from
@@USVL@@ to @@USVH@@. They are shown as heterogeneity, not as findings. One exporter
result is also worth recording: flows from China fell in tonnes in 2021&ndash;22 (@@CHN21V@@,
p&nbsp;=&nbsp;@@CHN21Vp@@).</p>

<h2>5. What failed, and what the checks say</h2>
<div class="box"><b>The pre-trend rule failed</b> for all five designs it was applied to: pre-period years
lay outside &plusmn;0.05 log points of 2019 (for transformer unit values, every year from 2014 to 2017).
Difference-in-differences language was withdrawn as the filing required.</div>
<ul>
<li><b>Unit values are not prices.</b> The annual change in the unit value of US transformer imports
correlates with the change in the BLS producer price index at only @@BLSC@@. Unit values carry product
mix; the direction of that bias is not known, so the unit-value gaps are neither upper nor lower bounds on
price change.</li>
<li><b>Copper wire</b> (7408.11, wire over 6 mm across, largely rod rather than transformer winding wire)
showed no gap relative to copper cathode after 2022; it says little about transformers either way.</li>
<li><b>Where the gap sits.</b> Split at the median unit value, the 2023&ndash;24 transformer gap is
@@LOWUV@@ in the lower half (p&nbsp;=&nbsp;@@LOWUVp@@) and @@HIUV@@ in the upper half
(p&nbsp;=&nbsp;@@HIUVp@@): it sits in the lower-value flows.</li>
<li><b>Other checks</b> filed in advance &mdash; a placebo period for transformers, alternative unit-value
bands, leaving out each line, and splits by exporter &mdash; are in the <a href="@@RESULTS@@">results
file</a>. All of them use the filed comparison machinery; none compares transformers with other
electrical goods, so none bears on the transformer-specific question.</li>
</ul>

<h2>6. What this cannot say</h2>
<ul>
<li>Nothing about AI or data centres specifically: every buyer of electrical equipment is in these flows.</li>
<li>Nothing about domestic production: a country that builds its own transformers never appears in trade.</li>
<li>Not whether supply was constrained, or by what &mdash; factories, electrical steel, labour or permitting.</li>
<li>Not causal.</li>
<li>Chip-making equipment was never tested (its value per tonne measures which machines were shipped). For
the record, world exports of machines for making semiconductor devices (8486.20) were $@@CHIP17@@bn in
2017 and $@@CHIP24@@bn in 2024, read in the HS 2017 nomenclature because the code does not exist in HS
2002; the largest exporters in 2024 were @@CHIPTOP@@.</li>
</ul>

<h2>7. What would settle it</h2>
<p>Monthly national trade data at eight or ten digits, which split transformers by rating finely enough to
hold product mix fixed; producer price series by rating from more than one country; and order and
capacity data from manufacturers, which trade data cannot see. The concentration of electrical-steel
exports, by contrast, is already visible and needs no further identification: it is a fact about who
exported the core material of transformers in 2024, though not about who could produce it.</p>

<h2>Review record</h2>
<p>Design: reviewed before filing by two independent language models as journal referees, which changed
the question, the controls, the inference and the claims. Literature: assembled by a research agent under
a rule that every source be opened and quoted. Result: an earlier version was reviewed by the same two referees and by a separate fact-checking
agent, which traced every number to the results file and every quotation to the verified literature.
Their reports turned the paper into this note: the event-study intervals were recomputed with the
headline procedure, the electrical-steel figures were widened to both customs lines, a material-netting
variant was added, and the comparison with other electrical goods was moved into the main text. This
version was then checked again by all three. Eleven dated deviations are logged in the filing.</p>

<h2>References</h2>
<ol class="refs">@@REFS@@</ol>
<p class="meta">Data: CEPII BACI (Etalab Open Licence 2.0), World Bank Pink Sheet and CPI (CC BY 4.0), BLS
(public domain). Built by <code>build_grid_trade_paper.py</code> from <code>out/buildout_study.json</code>.
Cite as: Critical Materials Atlas (2026). Zenodo. https://doi.org/10.5281/zenodo.21948855</p>
</section>
@@FOOT@@
</body></html>
""".replace('@@NAV@@', NAV).replace('@@FOOT@@', FOOT)


if __name__ == '__main__':
    main()
