#!/usr/bin/env python3
"""
Supply-risk hub: one page above the eight risk pages, showing where their methods agree.
(Fewer pages, item 11 of the Analysis fix list; published 25 Nov 2026, linked from the Research page.)

It computes nothing new about any material. It reads five scores the risk pages already publish,
ranks each material under each, and counts how many methods put it in the top ten:

    out/risk.json            score      the atlas's supply-risk index (risk.html)
    out/riskmethods.json     topsis     data-driven composite, entropy-TOPSIS (riskmethods.html)
                             gpr_mine   GeoPolRisk on mine production, governance-weighted (riskmethods.html)
                             cvar95     simulated supply loss, mean of the worst 5% (riskmethods.html)
    out/risk_adjusted.json   adjusted   the index re-weighted for supply that cannot respond to price
                                        (risk-adjusted.html)

All five are oriented "higher = riskier". Only materials scored by all five are ranked.
Writes risk-hub.html. Public data; deterministic. Run: python build_risk_hub.py
"""
import html
import io
import json
import os
import statistics

from evidence import badge

ROOT = os.path.dirname(os.path.abspath(__file__))
TOP = 10


def load(p):
    with io.open(os.path.join(ROOT, p), encoding='utf-8') as f:
        return json.load(f)


risk = {m['label']: m for m in load('out/risk.json')['materials']}
rm = {m['label']: m for m in load('out/riskmethods.json')['materials']}
ra = {r['label']: r for r in load('out/risk_adjusted.json')['rows']}

METHODS = [  # (column head, short note, score getter)
    ('Atlas index', 'the published 0-100 index', lambda l: risk[l]['score']),
    ('Entropy-TOPSIS', 'weights set by the data', lambda l: rm[l]['topsis']),
    ('GeoPolRisk', 'mine shares, governance-weighted', lambda l: rm[l]['gpr_mine']),
    ('Simulated loss', 'worst-5% supply loss', lambda l: rm[l]['cvar95']),
    ('Supply response', 'by-products weighted up', lambda l: ra[l]['adjusted']),
]

labels = sorted(l for l in risk if l in rm and l in ra)
if len(labels) < 20:
    raise SystemExit('only %d materials carry all five scores - refusing to publish' % len(labels))

ranks = {}
for head, _, get in METHODS:
    order = sorted(labels, key=lambda l: (-get(l), l))
    for i, l in enumerate(order):
        ranks.setdefault(l, []).append(i + 1)


def spearman(a, b):
    n = len(a)
    return 1 - 6 * sum((x - y) ** 2 for x, y in zip(a, b)) / (n * (n * n - 1))


cols = list(zip(*[ranks[l] for l in labels]))
pairs = [spearman(cols[i], cols[j]) for i in range(len(cols)) for j in range(i + 1, len(cols))]
rho_med = statistics.median(pairs)
rows = sorted(labels, key=lambda l: (-sum(r <= TOP for r in ranks[l]), statistics.median(ranks[l]), l))
all_five = [l for l in labels if all(r <= TOP for r in ranks[l])]
n_all = len(all_five)
e = html.escape


def _agree():
    for k in range(len(METHODS), 0, -1):
        hit = [l for l in rows if sum(r <= TOP for r in ranks[l]) == k]
        if hit:
            names = ', '.join(name(l) for l in hit)
            if k == len(METHODS):
                return '%s rank in the top %d under all %d.' % (names, TOP, k)
            return ('No material is in the top %d under all %d. %s %s in the top %d under %d of the %d.'
                    % (TOP, len(METHODS), names, 'is' if len(hit) == 1 else 'are', TOP, k, len(METHODS)))
    return ''


def name(l):
    return e(risk[l]['title'].split(' (')[0].split(',')[0].strip())


table = []
for l in rows:
    k = sum(r <= TOP for r in ranks[l])
    cells = ''.join('<td class="n%s">%d</td>' % (' top' if r <= TOP else '', r) for r in ranks[l])
    table.append('<tr><th scope="row"><a href="profile-%s">%s</a></th>%s<td class="n k">%d of %d</td></tr>'
                 % (e(l), name(l), cells, k, len(METHODS)))

PAGES = [
    ('Start here', [
        ('risk-index', 'Choose the weights', 'One index, your settings: trade value, tonnes or mine production; governance, recycling and substitutes on or off. A second tool on the same page weights eight criteria with sliders.'),
        ('risk', 'The published index', 'The fixed 0-100 score every material profile quotes, with its four components shown on each row.'),
    ]),
    ('Other ways to score it', [
        ('riskmethods', 'Three methods from the literature', 'Entropy-TOPSIS, GeoPolRisk and a simulated supply loss, on the same public data.'),
        ('criticality', 'Concentration in risky places', 'The same concentration counts for more in a weakly governed producer.'),
        ('geopolrisk', 'Scored in tonnes', 'Physical production instead of trade value; the unit changes the ranking.'),
        ('risk-adjusted', 'When supply cannot respond to price', 'By-product metals cannot raise output when prices rise; the index re-weighted for that.'),
    ]),
    ('A check', [
        ('iea-risk-check', 'Against the IEA', 'Does the public-data index recover the IEA\'s list of highest-risk materials?'),
    ]),
]
cards = []
for group, items in PAGES:
    cards.append('<h3>%s</h3><div class="cards">' % e(group))
    for href, title, text in items:
        if not os.path.exists(os.path.join(ROOT, href + '.html')):
            raise SystemExit('missing page %s.html' % href)
        cards.append('<a class="card" href="%s"><b>%s</b><span>%s</span></a>' % (href, e(title), e(text)))
    cards.append('</div>')

agree_text = _agree()          # names are escaped by name() already
heads = ''.join('<th scope="col">%s<small>%s</small></th>' % (e(h), e(n)) for h, n, _ in METHODS)
year = load('out/risk.json').get('year', '')

page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Supply risk: where the methods agree · Critical Materials Atlas</title>
<meta name="description" content="The atlas scores supply risk five ways. This page ranks every material under each and shows which ones rank high under all of them.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:.8rem;margin:.6rem 0 1.4rem}}
 .card{{display:block;border:1px solid #dbe7e5;border-radius:10px;padding:.8rem .9rem;text-decoration:none;color:#15323a;background:#fff}}
 .card:hover{{border-color:#0e7c74}}
 .card b{{display:block;margin-bottom:.25rem}} .card span{{font-size:.84rem;color:#5a6b68}}
 table.agree{{border-collapse:collapse;width:100%;font-size:.86rem;margin:.6rem 0}}
 table.agree th,table.agree td{{padding:.32rem .5rem;border-bottom:1px solid #eef3f2;text-align:left}}
 table.agree thead th{{font-size:.76rem;vertical-align:bottom}} table.agree thead small{{display:block;font-weight:500;color:#5a6b68}}
 table.agree td.n{{text-align:right;font-variant-numeric:tabular-nums;color:#5a6b68}}
 table.agree td.top{{color:#fff;background:#0e7c74;font-weight:700}}
 table.agree td.k{{color:#15323a;font-weight:700;white-space:nowrap}}
 .wrapx{{overflow-x:auto}}
</style>
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="explorer">Explore</a><a href="value-chains">Value chains</a><a href="analysis">Research</a><a href="method">Method</a><a href="data">Download data</a></nav>
</div></header>
<main id="main">
<section class="hero"><div class="wrap">
  <div class="eyebrow">Risk · one question, several methods</div>
  <h1>Supply risk: where the methods agree</h1>
  <p style="margin:.55rem 0 0;font-size:.82rem;opacity:.92">Headline figures on this page: {badge('modelled')}</p>
  <p class="deck">The atlas scores supply risk five ways. They weigh concentration, governance, tonnes and the ability of supply to respond differently, so their rankings differ. A material that ranks high under all of them is a safer conclusion than one that tops a single list.</p>
</div></section>
<article style="max-width:1040px">
<h2>Ranked under each method</h2>
<p>{len(labels)} materials carry all five scores. Shaded cells are a top-{TOP} rank. {agree_text} Across the ten pairs of methods, the median rank correlation is {rho_med:.2f}: the methods agree only in part.</p>
<div class="wrapx"><table class="agree">
<thead><tr><th scope="col">Material</th>{heads}<th scope="col">Top {TOP}</th></tr></thead>
<tbody>
{chr(10).join(table)}
</tbody></table></div>
<p class="note">Ranks, 1 = riskiest, among the {len(labels)} materials scored by all five methods; ties broken alphabetically. Each score comes from the page that publishes it, for trade year {e(str(year))}. A rank is not a forecast of a shortage: none of these methods sees stocks, contracts or how long a new supplier takes to qualify.</p>
<h2>The pages behind it</h2>
{chr(10).join(cards)}
</article>
</main>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value chains</a><br><a href="analysis">Research</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>Scores from the atlas's risk pages: risk.json, riskmethods.json, risk_adjusted.json</div>
  <div class="fineprint">Found an error, or want to challenge a figure? Write to <a href="mailto:contact@criticalmaterialsatlas.org">contact@criticalmaterialsatlas.org</a>.</div>
</div></footer>
</body></html>
'''
with io.open(os.path.join(ROOT, 'risk-hub.html'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(page)
print('risk-hub.html: %d materials, %d in the top %d under all five, median rho %.2f' % (len(labels), n_all, TOP, rho_med))
for l in rows[:12]:
    print('  %-14s %s  %d/5' % (l, ranks[l], sum(r <= TOP for r in ranks[l])))
