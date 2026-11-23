#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The homepage (index.html), as a build step.

Until 22 Nov 2026 the homepage was a page typed by hand. Its figures were typed too, so nothing
stopped one of them from going stale, and a total ("58 chains") sat in the hero for weeks after
the number had moved. This script writes the page from the built data and stops if a sentence on
it is no longer true.

THE RULES THE PAGE FOLLOWS (decided by the owner, November 2026)
  no totals   No count of materials, chains or pages in a headline, a strip or an intro. The atlas
              grows, so any "of N" is wrong the week after it is written. The page says "most" or
              "a few" and names examples. Exact numbers live in the full tables.
  plain       Statements, not slogans. No long dashes, no arrows in the text.
  one figure  A single chart, and its selection rule is printed under it. Three marks a row: the
              largest exporter's share of exports, the same country's share of mining (near zero
              by the rule, which is the point), and the largest miner's share of mining.

WHAT IS CHECKED BEFORE THE PAGE IS WRITTEN
  "for most materials the largest exporter is not the largest miner"   out/origin_gap_all.json
  "Germany was the largest exporter of strontium carbonate and mined none"   out/origin_gap_all.json
  "in most chains the most concentrated stage comes after the mine",
  "in a few it is the mine itself"                                     chokepoint_map.json
  the naive benchmark's hit rate, and "no model beats it reliably"     out/nowcast_bootstrap.json
One sentence is NOT checked by this script: the IEA cross-check ("most of the minerals the IEA
rates as high-risk"). iea-risk-check.html is a hand page with no data file behind it.

THE CHART'S SELECTION RULE
A row is drawn only if (1) the largest exporter is not the largest miner, by value and by tonnes,
(2) the same country leads by value and by tonnes and its two shares agree within a factor of two,
and (3) that country mined under 1% of world output. Rule 2 removes rows where the customs
quantities are not usable (a seller with 13% of the value and 66% of the tonnes is a data defect,
not a finding). An unknown mine share is not "under 1%": the row is left out.

UPDATED is the day this page's text or layout last changed. Change it with the page.

The welcome text names no institution (the owner's rule, 22 Nov 2026): sources belong with the
data, in the figure's source line and in the coverage table, not in the introduction.

Reads out/origin_gap_all.json, chokepoint_map.json, out/nowcast_bootstrap.json, out/cube.parquet. Writes index.html.
Deterministic. Run: python build_home.py
"""
import html
import io
import json
import os

import baci
import duckdb

ROOT = os.path.dirname(os.path.abspath(__file__))
UPDATED = '22 November 2026'


def load(*parts):
    return json.load(open(os.path.join(ROOT, *parts), encoding='utf8'))


def e(s):
    return html.escape(str(s), quote=True)


def pct(v):
    return ('%.0f' % v) if v >= 1 else ('under 1' if v > 0 else '0')


G = load('out', 'origin_gap_all.json')

# The years on the page are read from the store, not typed. On 22 Nov 2026 the page said "trade is
# covered from 2002", which is where the CEPII series starts; the atlas's own series, reconciled
# from UN Comtrade, starts earlier. The owner caught it.
_CUBE = os.path.join(ROOT, 'out', 'cube.parquet').replace(os.sep, '/')


def span(where):
    lo, hi = duckdb.connect().execute(
        f"select min(year), max(year) from '{_CUBE}' where {where}").fetchone()
    if lo is None:
        raise SystemExit('home: no rows in the store for ' + where)
    return int(lo), int(hi)


BACI0, BACI1 = span("source = 'CEPII BACI (HS02)'")
CMA0, CMA1 = span("source = 'CMA two-sided reconciliation'")
PROD0, PROD1 = span("source = 'BGS World Mineral Statistics' and measure = 'production'")
YEAR = G['year']
rows = G['rows']

NAME = {r.iso2: r.name for r in baci.countries().itertuples() if r.iso2 and r.name}
NAME.update({'AE': 'United Arab Emirates', 'US': 'United States', 'KR': 'South Korea', 'RU': 'Russia',
             'CD': 'DR Congo', 'GB': 'United Kingdom', 'CH': 'Switzerland', 'TR': 'Turkey', 'DE': 'Germany'})
SHORT = {'Diamonds (rough, gem)': 'Rough diamonds', 'Titanium, unwrought': 'Titanium metal',
         'Nickel, unwrought': 'Nickel metal', 'Tantalum, unwrought': 'Tantalum metal',
         'Beryllium, unwrought': 'Beryllium metal'}


def cn(c):
    return NAME.get(c, c)


# ---------------------------------------------------------------- the sentences, checked
n_gap = sum(bool(r['gap_value']) for r in rows)
if not 2 * n_gap > len(rows):
    raise SystemExit('home: "for most materials the largest exporter is not the largest miner" is no longer true')
n_gap_t = sum(bool(r['gap_tonnes']) for r in rows)
if not 2 * n_gap_t > len(rows):
    raise SystemExit('home: "the result holds in tonnes" is no longer true')
# The opening example (23 Nov 2026: strontium carbonate replaced gold - a reviewer: gold is well known
# and on few critical-materials lists). Refuse to publish the sentence if the store stops supporting it.
lead = next(r for r in rows if r['material'] == 'strontium')
if not (lead['top_exporter'] == 'DE' and lead['top_exporter_mine_share'] == 0):
    raise SystemExit('home: the opening example (Germany sells the most strontium carbonate and mines none) is no longer true')

chains = load('chokepoint_map.json')['rows']
after_mine = sum(r['mechanism'] in ('thermodynamic', 'byproduct', 'capability') for r in chains)
at_mine = sum(r['mechanism'] == 'geological' for r in chains)
if not 2 * after_mine > len(chains):
    raise SystemExit('home: "in most value chains the most concentrated stage comes after the mine" is no longer true')
if not 0 < 4 * at_mine < len(chains):
    raise SystemExit('home: "in a few chains it is the mine itself" is no longer true')

B = load('out', 'nowcast_bootstrap.json')
naive = next(m for m in B['models'] if m['model'].startswith('persistence'))
HIT = '%.0f' % naive['top_hit_pct']
if B['holm_significant_better'] or B['two_way_material_year']['better_than_persistence_holm']:
    raise SystemExit('home: a model now beats the naive benchmark; the nowcast sentence must be rewritten')


# ---------------------------------------------------------------- the chart
def steady(r):
    a, b = r['top_exporter_share'], r.get('top_exporter_share_tonnes')
    return r['top_exporter'] == r.get('top_exporter_tonnes') and b and max(a, b) <= 2 * min(a, b)


sel = [r for r in rows if r['gap_value'] and r['gap_tonnes'] and steady(r)
       and r.get('top_exporter_mine_share') is not None and r['top_exporter_mine_share'] < 1]
sel.sort(key=lambda r: (-r['top_exporter_share'], r['material']))
if not 3 <= len(sel) <= 12:
    raise SystemExit('home: the chart rule keeps %d rows; the figure was designed for a handful' % len(sel))
if lead not in sel:
    raise SystemExit('home: strontium carbonate is the opening example but the chart rule no longer keeps it')

chart = []
for r in sel:
    t = SHORT.get(r['title'], r['title'])
    x, m = r['top_exporter_share'], r['top_exporter_mine_share']
    tip = (f"{cn(r['top_exporter'])}: {pct(x)}% of world exports of {t.lower()} by value, "
           f"{pct(m)}% of world mine production. Largest miner: {cn(r['top_miner'])}, {pct(r['top_miner_share'])}%.")
    chart.append(
        f'<div class="row" tabindex="0" data-tip="{e(tip)}" aria-label="{e(tip)}">'
        f'<span class="mat">{e(t)}</span>'
        f'<span class="track"><i class="ln" style="left:{m:.1f}%;width:{x - m:.1f}%"></i>'
        f'<i class="big" style="left:{r["top_miner_share"]:.1f}%"></i>'
        f'<i class="d mine" style="left:{m:.1f}%"></i><i class="d exp" style="left:{x:.1f}%"></i></span>'
        f'<span class="who"><b>{e(cn(r["top_exporter"]))}</b> {pct(x)}% of exports. '
        f'Largest miner: {e(cn(r["top_miner"]))}, {pct(r["top_miner_share"])}%.</span></div>')

PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png"><link rel="icon" type="image/png" sizes="96x96" href="/favicon-96.png"><link rel="icon" type="image/png" sizes="48x48" href="/favicon-48.png"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><link rel="icon" href="/favicon.ico" sizes="any"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Critical Materials Atlas: who mines, refines and sells critical raw materials</title>
<meta name="description" content="Who mines critical raw materials, who refines them and who sells them. Public statistics only, from reserves to mine, refinery and export market.">
<meta property="og:title" content="Critical Materials Atlas: who mines, refines and sells critical raw materials">
<meta property="og:description" content="Who mines critical raw materials, who refines them and who sells them. Public statistics only, from reserves to mine, refinery and export market.">
<meta property="og:image" content="https://criticalmaterialsatlas.org/share/card-home.png">
<meta property="og:image:width" content="1600"><meta property="og:image:height" content="900">
<meta property="og:url" content="https://criticalmaterialsatlas.org/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Critical Materials Atlas">
<link rel="canonical" href="https://criticalmaterialsatlas.org/">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 :root{--paper:#fbfaf7;--teal:#0e7c74;--teal-soft:#a9d3ce;--rule:#e4e2dc}
 body{background:var(--paper)}
 .topbar{background:rgba(251,250,247,.95)}
 .topbar .wrap{max-width:1280px}
 .topnav a{white-space:nowrap}
 .wrap{max-width:1080px;margin:0 auto;padding:0 22px}
 h1,h2{font-family:'Source Serif 4',Georgia,serif;color:var(--navy);font-weight:600;letter-spacing:-.01em}
 .top{padding:3.2rem 0 1.4rem}
 .top h1{font-size:2.55rem;line-height:1.12;margin:0;max-width:21ch}
 .top .deck{font-size:1.08rem;line-height:1.6;color:var(--ink-soft);max-width:62ch;margin:1.1rem 0 0}
 .top .go{margin:1.5rem 0 0;display:flex;flex-wrap:wrap;align-items:center;gap:1.2rem;font-size:.95rem}
 .top .go .btn{background:var(--navy);color:#fff;font-weight:600;padding:.62rem 1.15rem;border-radius:4px}
 .top .go .btn:hover{background:#1d4a52;text-decoration:none}
 .top .meta{font-size:.82rem;color:var(--mut);margin:1.4rem 0 0}
 @media(max-width:640px){.top h1{font-size:1.9rem}}
 section{padding:2.2rem 0;border-top:1px solid var(--rule)}
 section h2{font-size:1.6rem;line-height:1.2;margin:0 0 .5rem;padding:0;border:0;max-width:34ch}
 section>.wrap>p{max-width:68ch;color:var(--ink-soft);margin:.4rem 0 0}
 /* the figure */
 .fig{margin:1.5rem 0 0;position:relative}
 .fig .legend{display:flex;flex-wrap:wrap;gap:.3rem 1.6rem;font-size:.84rem;color:var(--ink-soft);margin:0 0 .9rem}
 .fig .legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:.45rem;vertical-align:-1px}
 .fig .legend .exp{background:var(--teal)} .fig .legend .mine{background:var(--paper);box-shadow:inset 0 0 0 2px var(--teal)}
 .fig .legend .big{width:3px;height:13px;border-radius:0;background:var(--navy);margin:0 .6rem 0 .25rem;vertical-align:-2px}
 .axis,.row{display:grid;grid-template-columns:150px minmax(0,1fr) 300px;column-gap:18px;align-items:center}
 .axis{font-size:.74rem;color:var(--mut);font-variant-numeric:tabular-nums;margin-bottom:.2rem}
 .axis .ticks{position:relative;height:1.1rem}
 .axis .ticks span{position:absolute;transform:translateX(-50%)}
 .axis .ticks span:first-child{transform:none}.axis .ticks span:last-child{transform:translateX(-100%)}
 .row{padding:.42rem 0;border-top:1px solid var(--rule);font-size:.9rem;outline:0}
 .row:hover,.row:focus-visible{background:#f3f1ea}
 .row .mat{color:var(--ink);font-weight:600}
 .row .who{color:var(--mut);font-size:.84rem}.row .who b{color:var(--ink);font-weight:600}
 .track{position:relative;height:22px;background:
   linear-gradient(to right,var(--rule) 1px,transparent 1px) 0 0/25% 100%,
   linear-gradient(to left,var(--rule) 1px,transparent 1px) 100% 0/1px 100% no-repeat}
 .track .ln{position:absolute;top:10px;height:2px;background:var(--teal-soft)}
 .track .d{position:absolute;top:6px;width:10px;height:10px;margin-left:-5px;border-radius:50%;box-shadow:0 0 0 2px var(--paper)}
 .track .exp{background:var(--teal)}
 .track .big{position:absolute;top:2px;width:3px;height:18px;margin-left:-1.5px;background:var(--navy);box-shadow:0 0 0 1px var(--paper)}
 .track .mine{background:var(--paper);box-shadow:inset 0 0 0 2px var(--teal),0 0 0 2px var(--paper)}
 .row:hover .d,.row:focus-visible .d{box-shadow:0 0 0 2px #f3f1ea}
 .row:hover .mine,.row:focus-visible .mine{background:#f3f1ea;box-shadow:inset 0 0 0 2px var(--teal),0 0 0 2px #f3f1ea}
 .fig .note{font-size:.82rem;color:var(--mut);max-width:78ch;margin:1rem 0 0;line-height:1.55}
 #tip{position:absolute;z-index:5;max-width:330px;background:var(--navy);color:#fff;font-size:.8rem;line-height:1.45;padding:.55rem .7rem;border-radius:4px;pointer-events:none;display:none}
 @media(max-width:760px){
   .axis{display:none}
   .row{grid-template-columns:1fr;row-gap:.25rem}
 }
 /* plain lists and tables */
 ol.find{margin:1.1rem 0 0;padding:0;list-style:none;counter-reset:f;max-width:74ch}
 ol.find li{counter-increment:f;position:relative;padding:.85rem 0 .85rem 2.4rem;border-top:1px solid var(--rule);color:var(--ink-soft)}
 ol.find li::before{content:counter(f);position:absolute;left:0;top:.85rem;font-family:'Source Serif 4',Georgia,serif;font-size:1.25rem;color:var(--teal);line-height:1.2}
 ol.find b{color:var(--ink);font-weight:600}
 table.cov{border-collapse:collapse;width:100%;margin:1.1rem 0 0;font-size:.9rem}
 table.cov th{font-size:.74rem;font-weight:600;color:var(--mut);text-align:left;padding:.4rem .9rem .4rem 0;border-bottom:1px solid var(--line-strong)}
 table.cov td{padding:.6rem .9rem .6rem 0;border-bottom:1px solid var(--rule);vertical-align:top;color:var(--ink-soft)}
 table.cov td:first-child{color:var(--ink);font-weight:600;white-space:nowrap}
 @media(max-width:700px){table.cov th:nth-child(3),table.cov td:nth-child(3){display:none}}
 ul.plain{margin:1rem 0 0;padding:0;list-style:none;max-width:74ch}
 ul.plain li{padding:.6rem 0;border-top:1px solid var(--rule);color:var(--ink-soft)}
 ul.plain li a{font-weight:600}
 .lftr{background:#12272c;color:#a4b9b6;margin-top:1.6rem;padding:2.4rem 0 2rem;font-size:.86rem;line-height:1.6}
 .lftr .cols{display:grid;grid-template-columns:2fr 1fr 1fr;gap:2rem;margin-bottom:1.2rem}
 @media(max-width:720px){.lftr .cols{grid-template-columns:1fr;gap:1.3rem}}
 .lftr h4{font-size:.78rem;color:#fff;margin:0 0 .6rem;font-weight:600}
 .lftr a{color:#c1d6d2;text-decoration:none;display:block;padding:.15rem 0}.lftr a:hover{color:#fff}
 .lftr .fine{font-size:.76rem;color:#7c918d;border-top:1px solid rgba(255,255,255,.13);padding-top:1.2rem;line-height:1.5}
</style>
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
{"@type":"Organization","@id":"https://criticalmaterialsatlas.org/#org","name":"Critical Materials Atlas","url":"https://criticalmaterialsatlas.org/","logo":"https://criticalmaterialsatlas.org/apple-touch-icon.png","description":"Independent public-data research on critical raw materials: where they are mined, refined, traded and held in reserve, and how concentrated each stage is."},
{"@type":"WebSite","@id":"https://criticalmaterialsatlas.org/#site","url":"https://criticalmaterialsatlas.org/","name":"Critical Materials Atlas","publisher":{"@id":"https://criticalmaterialsatlas.org/#org"},"inLanguage":"en","description":"Who mines critical raw materials, who refines them and who sells them, from public statistics only."}
]}
</script>
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="explorer">Explore</a><a href="value-chains">Value chains</a><a href="analysis">Research</a><a href="method" class="hideable">Method</a></nav>
</div></header>
<main id="main">

<div class="top"><div class="wrap">
  <h1>Who mines critical raw materials, who refines them and who sells them</h1>
  <p class="deck">The atlas follows each material from reserves to mine, refinery and export market. Every figure comes from public statistics, and the sources are listed with the data.</p>
  <div class="go"><a class="btn" href="explorer">Open the explorer</a><a href="findings">Read the findings</a><a href="data">Download the data</a></div>
  <p class="meta">Independent research, not affiliated with any institution. Updated @@UPDATED@@.</p>
</div></div>

<section><div class="wrap">
  <h2>In @@YEAR@@ Germany was the largest exporter of strontium carbonate and mined none of it.</h2>
  <p>It is not an exception. For most materials measured, the country that exports the most is not the country that mines the most. Often the seller is another mining country. In the cases below it is a refinery, a smelter or a trading hub in a country that mines almost none of the material.</p>
  <div class="fig" id="fig">
    <div class="legend"><span><i class="exp"></i>Largest exporter&rsquo;s share of world exports</span><span><i class="mine"></i>The same country&rsquo;s share of world mine production</span><span><i class="big"></i>Largest miner&rsquo;s share of world mine production</span></div>
    <div class="axis"><span></span><span class="ticks"><span style="left:0">0%</span><span style="left:25%">25%</span><span style="left:50%">50%</span><span style="left:75%">75%</span><span style="left:100%">100%</span></span><span></span></div>
    @@CHART@@
    <div id="tip" role="status"></div>
    <p class="note">Shown: the materials whose largest exporter mined less than 1% of world output in @@YEAR@@, where the same country leads by value and by tonnes. Each material is measured on its main traded form, and trade inside finished goods is not counted. Exports: CEPII BACI, @@YEAR@@, by value. Mine production: USGS, World Mining Data or BGS. <a href="origin-gap-all">Full table, every material measured</a>.</p>
  </div>
</div></section>

<section><div class="wrap">
  <h2>Findings</h2>
  <ol class="find">
    <li><b>The largest exporter is usually not the largest miner.</b> The result holds whether trade is counted in dollars or in tonnes. <a href="origin-gap-all">The origin gap</a></li>
    <li><b>In most value chains the most concentrated stage comes after the mine.</b> It is usually refining, by-product recovery or product qualification. In a few chains it is the mine itself. <a href="chokepoint-map">The chokepoint map</a></li>
    <li><b>China&rsquo;s export controls of 2023 to 2025 left no clear mark in European and American import records.</b> That was the pre-registered test, and it is reported as filed. Antimony and bismuth are the exception, read as exploratory. <a href="export-controls">Export controls</a></li>
    <li><b>For most critical materials, no country publishes how many days of supply its stockpile would cover.</b> Japan does, for a few. The United States holds stocks but does not say how long they would last. <a href="stockpiles">Stockpiles</a></li>
  </ol>
</div></section>

<section><div class="wrap">
  <h2>Checks on the method</h2>
  <ol class="find">
    <li><b>The nowcast is tested against a naive benchmark.</b> Out of sample, last year&rsquo;s largest exporter is still the largest exporter @@HIT@@% of the time. None of the forecasting models tested beats that benchmark reliably, and the page says so. <a href="nowcast-backtest">Nowcast backtest</a></li>
    <li><b>The risk index is checked against the IEA.</b> Built from public data alone, it places most of the minerals the IEA rates as high-risk in its own top third. <a href="iea-risk-check">IEA cross-check</a></li>
  </ol>
</div></section>

<section><div class="wrap">
  <h2>What the atlas covers</h2>
  <table class="cov">
    <thead><tr><th>Stage</th><th>What is measured</th><th>Sources</th><th>Open</th></tr></thead>
    <tbody>
      <tr><td>Reserves</td><td>Economically recoverable reserves by country</td><td>USGS</td><td><a href="explorer">Explorer</a></td></tr>
      <tr><td>Mine production</td><td>Annual output by country, @@PROD0@@ to @@PROD1@@</td><td>USGS, World Mining Data, BGS</td><td><a href="trends">Trends</a></td></tr>
      <tr><td>Refining</td><td>Refined output and capacity by country</td><td>IEA, USGS, BGS</td><td><a href="refiners">Refiners</a></td></tr>
      <tr><td>Trade</td><td>Bilateral flows in value and tonnes. The CEPII series runs from @@BACI0@@ to @@BACI1@@. The atlas&rsquo;s own reconciliation of UN Comtrade runs from @@CMA0@@ to @@CMA1@@, the last year being incomplete.</td><td>UN Comtrade, CEPII BACI</td><td><a href="explorer">Explorer</a></td></tr>
      <tr><td>Concentration</td><td>How much of each stage one country holds</td><td>Computed from the above</td><td><a href="network">Trade network</a></td></tr>
      <tr><td>Value chains</td><td>End-use chains from raw material to finished product</td><td>IEA, OECD, IRENA, industry bodies</td><td><a href="value-chains">Value chains</a></td></tr>
    </tbody>
  </table>
</div></section>

<section><div class="wrap">
  <h2>Tools</h2>
  <ul class="plain">
    <li><a href="breakout">Alternatives to a concentrated supplier.</a> For each chokepoint, which countries and companies could supply an alternative, and which are building one.</li>
    <li><a href="ot">Reallocation stress test.</a> Removes the largest exporter of a material and reallocates the remaining exports, with a map before and after.</li>
    <li><a href="leverage">Importer exposure.</a> For each importing country and material, the share of supply that comes from a single source.</li>
  </ul>
</div></section>

<section><div class="wrap">
  <h2>Method and data</h2>
  <p>Every figure traces to a public source. The trade reconciliation is checked against the official CEPII series, which starts from the same customs records; each commodity carries a reliability grade, and errors found in review are published with their corrections. The code and the data are open.</p>
  <ul class="plain">
    <li><a href="methodology">Methodology and validation</a></li>
    <li><a href="confidence">Reliability of each commodity</a></li>
    <li><a href="robustness">Robustness tests</a></li>
    <li><a href="data">Open data and API</a></li>
    <li><a href="mailto:contact@criticalmaterialsatlas.org">Report an error: contact@criticalmaterialsatlas.org</a></li>
  </ul>
</div></section>

</main>
<footer class="lftr"><div class="wrap">
  <div class="cols">
    <div><h4>Critical Materials Atlas</h4><p style="margin:0;max-width:46ch">Independent public-data research on critical raw materials. Not affiliated with, nor representing, any institution.</p></div>
    <div><h4>Navigate</h4><a href="explorer">Explore</a><a href="value-chains">Value chains</a><a href="analysis">Research</a><a href="reports">Reports</a><a href="method">Method</a></div>
    <div><h4>More</h4><a href="about">About</a><a href="updates">Updates</a><a href="data">Open data</a><a href="brief">One-page brief (PDF)</a><a href="https://github.com/materials-atlas/critical-materials-atlas">Source code</a><a href="mailto:contact@criticalmaterialsatlas.org">Contact</a></div>
  </div>
  <div class="fine">Sources: USGS Mineral Commodity Summaries, BGS World Mineral Statistics, World Mining Data, IEA Critical Minerals Outlook, UN Comtrade and CEPII BACI (Gaulier and Zignago 2010), Eurostat, World Bank. Figures are rounded.</div>
</div></footer>
<script>
(function(){var f=document.getElementById('fig'),t=document.getElementById('tip');if(!f||!t)return;
 function show(r,x,y){t.textContent=r.getAttribute('data-tip');t.style.display='block';var b=f.getBoundingClientRect();
  var l=Math.min(Math.max(0,x-b.left+14),b.width-t.offsetWidth);t.style.left=l+'px';t.style.top=(y-b.top+16)+'px';}
 f.querySelectorAll('.row').forEach(function(r){
  r.addEventListener('mousemove',function(ev){show(r,ev.clientX,ev.clientY);});
  r.addEventListener('mouseleave',function(){t.style.display='none';});
  r.addEventListener('focus',function(){var b=r.getBoundingClientRect();show(r,b.left+160,b.bottom-16);});
  r.addEventListener('blur',function(){t.style.display='none';});});})();
</script>
</body></html>
'''

for _k, _v in (('BACI0', BACI0), ('BACI1', BACI1), ('CMA0', CMA0), ('CMA1', CMA1), ('PROD0', PROD0), ('PROD1', PROD1)):
    PAGE = PAGE.replace('@@%s@@' % _k, str(_v))
page = (PAGE.replace('@@YEAR@@', str(YEAR)).replace('@@UPDATED@@', UPDATED).replace('@@HIT@@', HIT)
        .replace('@@CHART@@', '\n    '.join(chart)))
if '@@' in page:
    raise SystemExit('home: a placeholder was left in the page')
io.open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf8', newline='\n').write(page)
print('index.html written | chart rows:', len(sel), [r['material'] for r in sel],
      '| gap %d of %d by value' % (n_gap, len(rows)), '| naive hit', HIT + '%')
