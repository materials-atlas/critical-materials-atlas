#!/usr/bin/env python3
"""
The synthesis page — "the state of critical-materials supply" in one screen. Computes cross-cutting
takeaways from every layer (risk index, origin gaps, recycling, China footprint, country vulnerability),
all deterministically from the public data. Writes insights.html.
"""
import json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = os.environ.get('PROFILE_YEAR', '2024')
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
risk = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'risk.json'), encoding='utf8'))['materials']}
NAMES = flows.get('names', {})
MATS = data['materials']
HUBS = {'HK', 'SG', 'AE', 'PA', 'MO', 'GI'}

def cname(i): return NAMES.get(i, i)
def e(s): return html.escape(str(s), quote=True)
def strip(t): return str(t).split(' (')[0]
def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(c.upper()) - 65) for c in iso)
def fmtV(v):
    v = float(v or 0)
    return f'${v/1e9:.1f}B' if v >= 1e9 else f'${v/1e6:.0f}M' if v >= 1e6 else f'${max(1,round(v/1e3))}k'

def top_exporter(label):
    a = (flows.get('materials', {}).get(label)) or []
    o, tot = {}, 0.0
    for f in a:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; tot += f['value']
    if not tot: return None, 0
    c = max(o, key=o.get); return c, o[c] / tot * 100

# --- China footprint ---
cn_mine = sum(1 for m in MATS if (m.get('mined') or [{}])[0].get('c') == 'CN')
cn_ref = sum(1 for m in MATS if (m.get('refined') or [{}])[0].get('c') == 'CN')
cn_exp = sum(1 for m in MATS if top_exporter(m['label'])[0] == 'CN')
full_chain = [strip(m['title']) for m in MATS
              if (m.get('mined') or [{}])[0].get('c') == 'CN'
              and (m.get('refined') or [{}])[0].get('c') == 'CN'
              and top_exporter(m['label'])[0] == 'CN']

# --- origin gaps ---
gaps = []
for m in MATS:
    te, tes = top_exporter(m['label'])
    if not te: continue
    mi = (m.get('mined') or [None])[0]
    if not mi or te == mi['c']: continue
    te_mine = next((x['v'] for x in (m.get('mined') or []) if x['c'] == te), 0)
    gaps.append((tes - te_mine, strip(m['title']), te, mi['c'], m['label']))
gaps.sort(reverse=True)
mismatch = len(gaps)

# --- risk ---
ranked = sorted(MATS, key=lambda m: risk.get(m['label'], {}).get('score', 0), reverse=True)
no_cushion = [m for m in MATS if risk.get(m['label'], {}).get('score', 0) >= 45 and (m.get('recycling') or 0) < 5]
no_cushion.sort(key=lambda m: risk.get(m['label'], {}).get('score', 0), reverse=True)

# --- country vulnerability (inline) ---
def country_rows(iso):
    rows = []
    for m in MATS:
        a = (flows.get('materials', {}).get(m['label'])) or []
        o, tot = {}, 0.0
        for f in a:
            if f['to'] == iso and f['from'] != iso:
                o[f['from']] = o.get(f['from'], 0.0) + f['value']; tot += f['value']
        if not tot: continue
        top = max(o, key=o.get)
        rows.append((tot, o[top] / tot * 100, risk.get(m['label'], {}).get('score', 0)))
    return rows
isos = set()
for m in MATS:
    for f in (flows.get('materials', {}).get(m['label']) or []):
        isos.add(f['to'])
countries = []
for iso in isos:
    if iso in HUBS: continue
    rows = country_rows(iso)
    total = sum(r[0] for r in rows)
    if total < 1e9 or len(rows) < 8: continue
    vuln = round(sum(t * (rk / 100) * (ts / 100) for t, ts, rk in rows) / total * 100)
    countries.append((vuln, total, iso, len(rows)))
countries.sort(reverse=True)

def li_rows(items):
    return ''.join(items)

MOTIF = ('<svg class="hero-motif" viewBox="0 0 560 560" fill="none" aria-hidden="true"><g stroke="#7fd2c8" stroke-opacity=".15" stroke-width="1.1"><circle cx="280" cy="280" r="232"/><ellipse cx="280" cy="280" rx="232" ry="62"/><ellipse cx="280" cy="280" rx="232" ry="132"/><ellipse cx="280" cy="280" rx="232" ry="196"/><ellipse cx="280" cy="280" rx="62" ry="232"/><ellipse cx="280" cy="280" rx="132" ry="232"/><ellipse cx="280" cy="280" rx="196" ry="232"/><line x1="280" y1="48" x2="280" y2="512"/><line x1="48" y1="280" x2="512" y2="280"/></g><g stroke="#9be3da" stroke-opacity=".26" stroke-width="1.4" fill="none"><path d="M120 360 Q 300 110 472 248"/><path d="M158 196 Q 322 300 442 422"/><path d="M120 360 Q 268 430 442 422"/></g><g fill="#bff0e8" fill-opacity=".55"><circle cx="120" cy="360" r="4.2"/><circle cx="472" cy="248" r="4.2"/><circle cx="158" cy="196" r="4.2"/><circle cx="442" cy="422" r="4.2"/></g></svg>')

def card(title, inner):
    return f'<div style="border:1px solid var(--line);border-radius:12px;padding:1.1rem 1.3rem;background:#fff"><h3 style="margin:.1rem 0 .6rem">{title}</h3>{inner}</div>'

def main():
    # highest risk
    hr = ''.join(
        f'<li><a href="profile-{e(m["label"])}.html">{e(strip(m["title"]))}</a> '
        f'<b style="color:#c0392b">{risk[m["label"]]["score"]}</b>'
        f'<span style="color:#9aa6ad"> · {"un-recyclable" if (m.get("recycling") or 0)<5 else str(m.get("recycling"))+"% recycled"}</span></li>'
        for m in ranked[:6])
    # origin gaps
    og = ''.join(
        f'<li><a href="profile-{e(lab)}.html">{e(t)}</a> · {flag(te)} {e(cname(te))} exports, mined in {flag(mi)} {e(cname(mi))} '
        f'<b style="color:#b4532b">+{g:.0f}pp</b></li>'
        for g, t, te, mi, lab in gaps[:6])
    # no cushion
    nc = ''.join(
        f'<li><a href="profile-{e(m["label"])}.html">{e(strip(m["title"]))}</a> · risk <b>{risk[m["label"]]["score"]}</b>, '
        f'{(m.get("recycling") or 0)}% recycled</li>' for m in no_cushion[:6])
    # countries
    cc = ''.join(
        f'<li><a href="profile-country-{e(iso)}.html">{flag(iso)} {e(cname(iso))}</a> '
        f'<b>{vuln}</b><span style="color:#9aa6ad">/100 · {fmtV(total)}</span></li>'
        for vuln, total, iso, n in countries[:6])
    chain = (', '.join(e(c) for c in full_chain) or '—')

    out = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The state of critical-materials supply — Critical Materials Atlas</title>
<meta name="description" content="The whole atlas in one screen: highest-risk materials, the biggest origin gaps, China's footprint, the materials with no recycling cushion, and the most-exposed economies.">
<meta property="og:title" content="The state of critical-materials supply">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style> .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem;margin:1rem 0}} .grid2 ul{{margin:.2rem 0;padding-left:1.1rem}} .grid2 li{{margin:.3rem 0;font-size:.92rem}} @media(max-width:740px){{.grid2{{grid-template-columns:1fr}}}} </style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="findings.html">Findings</a><a href="risk.html" class="hideable">Risk</a>
  <a href="profiles.html" class="hideable">Profiles</a><a href="countries.html" class="hideable">Countries</a>
  <a href="https://github.com/materials-atlas/comtrade-reconcile" class="hideable">Engine</a></nav>
</div></header>
<section class="hero">{MOTIF}<div class="wrap">
  <div class="eyebrow">Synthesis · {YEAR}</div>
  <h1>The state of critical-materials supply</h1>
  <p class="deck">The whole atlas in one screen — the highest-risk materials, the biggest origin gaps, China's footprint across the chain, the materials with no recycling cushion, and the most-exposed economies. Every figure links to its detail.</p>
</div></section>
<section class="stats"><div class="wrap">
  <div class="stat"><div class="n">{len(MATS)}</div><div class="l">critical materials</div></div>
  <div class="stat"><div class="n">{mismatch}<span style="color:var(--faint);font-weight:600">/{len(MATS)}</span></div><div class="l">top exporter ≠ top miner</div></div>
  <div class="stat"><div class="n">{cn_exp}</div><div class="l">China is the top exporter</div></div>
  <div class="stat"><div class="n">{len(full_chain)}</div><div class="l">China leads mine + refine + export</div></div>
</div></section>
<article style="max-width:1000px">
  <div class="grid2">
    {card('Highest supply risk', f'<ul>{hr}</ul><p class="note"><a href="risk.html">full index →</a></p>')}
    {card('The refiner illusion — biggest origin gaps', f'<ul>{og}</ul><p class="note"><a href="findings.html">the finding →</a></p>')}
    {card('No recycling cushion', f'<p style="font-size:.9rem;color:#667179;margin:.1rem 0 .5rem">High-risk and barely recycled — a disruption has no secondary supply to fall back on.</p><ul>{nc}</ul>')}
    {card('Most-exposed economies', f'<ul>{cc}</ul><p class="note"><a href="countries.html">all countries →</a></p>')}
  </div>
  <div class="callout"><b>China's footprint.</b> Across the {len(MATS)} materials, China is the top <b>miner</b> in {cn_mine}, the top <b>refiner</b> in {cn_ref}, and the top <b>exporter</b> in {cn_exp}. It leads the <i>entire</i> chain — mine, refine and export — in {len(full_chain)}: {chain}. But the origin gap shows the reverse case too: many apparent dependencies on European/Japanese refiners are really upstream dependencies on African and Latin-American mines.</div>
  <p class="note">Computed by build_insights.py from the public data (<a href="out/data.json">data.json</a>, <a href="out/flows_{YEAR}.json">flows_{YEAR}.json</a>, <a href="out/risk.json">risk.json</a>). Trade year {YEAR}.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="./">Interactive atlas</a><br><a href="findings.html">The origin gap</a><br><a href="risk.html">Supply-risk index</a><br><a href="scenarios.html">Shock scenarios</a></div>
  <div><h4>Sources</h4>UN Comtrade · CEPII BACI<br>USGS · IEA · EU CRM · World Bank</div>
  <div class="fineprint">A synthesis of public-data layers. Not an official criticality assessment.</div>
</div></footer>
</body></html>'''
    open(os.path.join(ROOT, 'insights.html'), 'w', encoding='utf8', newline='\n').write(out)
    print(f'wrote insights.html  (China: top miner {cn_mine}, refiner {cn_ref}, exporter {cn_exp}, full-chain {len(full_chain)}; mismatches {mismatch})')

if __name__ == '__main__':
    main()
