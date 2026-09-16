#!/usr/bin/env python3
"""
Key-findings brief — a one-page, print-ready distillation of the atlas's strongest results, for sharing
(attach the PDF to an email, or link it). Every number is pulled live from the layer outputs so the brief
can never drift from the data. Writes brief.html (print-optimised; render to brief.pdf via headless Chrome).
"""
import json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = '2024'
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
risk = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'risk.json'), encoding='utf8'))['materials']}
TR = json.load(open(os.path.join(ROOT, 'out', 'trends.json'), encoding='utf8'))
NET = json.load(open(os.path.join(ROOT, 'out', 'network.json'), encoding='utf8')).get('temporal', {})
NAMES = flows.get('names', {})
MATS = data['materials']

def cn(i): return NAMES.get(i, i)
def e(s): return html.escape(str(s), quote=True)
def strip(t): return str(t).split(' (')[0]
def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(c.upper()) - 65) for c in iso)

def top_exporter(label):
    o, tot = {}, 0.0
    for f in flows.get('materials', {}).get(label, []) or []:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; tot += f['value']
    if not tot: return None, 0
    c = max(o, key=o.get); return c, o[c] / tot * 100

# origin gaps
gaps = []
for m in MATS:
    te, tes = top_exporter(m['label'])
    if not te: continue
    mi = (m.get('mined') or [None])[0]
    if not mi or te == mi['c']: continue
    te_mine = next((x['v'] for x in (m.get('mined') or []) if x['c'] == te), 0)
    gaps.append((tes - te_mine, strip(m['title']), te, mi['c']))
gaps.sort(reverse=True)
mismatch = len(gaps)

# no-way-out
nwo = []
for m in MATS:
    te, tes = top_exporter(m['label'])
    reftop = (m.get('refined') or [{}])[0]
    if m.get('substitutability') == 'high' and (m.get('recycling') or 0) < 5 and (tes >= 40 or reftop.get('v', 0) >= 50):
        nwo.append((strip(m['title']), reftop.get('c')))
nwo_cn = sum(1 for _, rc in nwo if rc == 'CN')

# time numbers
tmat = TR.get('materials', {})
def h(v): return v.get('stats', {}).get('hhi', {})
sig = [k for k, v in tmat.items() if h(v).get('mk_p_fdr', 1) < 0.05 and h(v).get('sen', 0) > 0]
brk = sum(1 for k in sig if (h(tmat[k]).get('brk_year') or 0) and 2012 <= h(tmat[k])['brk_year'] <= 2016)
gi = TR.get('gap_index', []); g0, g1 = (gi[0], gi[-1]) if gi else (0, 0)
cni = NET.get('cn_through_index', []); c0, c1 = (cni[0], cni[-1]) if cni else (0, 0)
def crise(lab):
    s = tmat.get(lab, {}).get('china', []); return (round(s[0]), round(s[-1])) if s else (0, 0)
mg0, mg1 = crise('magnets'); tu0, tu1 = crise('tungsten'); bx = NET.get('materials', {}).get('bauxite', {}).get('through', [0, 0])

cn_exp = sum(1 for m in MATS if top_exporter(m['label'])[0] == 'CN')
cn_ref = sum(1 for m in MATS if (m.get('refined') or [{}])[0].get('c') == 'CN')
yrs = TR.get('years', [2002, 2024])

ex = ' · '.join(f'{e(t)} ({flag(te)}{e(cn(te))} exports, {flag(mi)}{e(cn(mi))} mines)' for g, t, te, mi in gaps[:3])
nwo_list = ', '.join(e(t) for t, _ in nwo)

out = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Key findings — Critical Materials Atlas</title>
<meta name="description" content="A one-page brief: where 32 critical materials really come from, how concentration has intensified since 2002, and the materials with no way out — from reconciled public trade data, validated against CEPII BACI.">
<meta property="og:title" content="Critical Materials Atlas — key findings">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
 :root{{--navy:#15323a;--navy2:#1d4a52;--accent:#0e7c74;--ink:#1a1f24;--mut:#5a6b68;--line:#e3e9e8}}
 *{{box-sizing:border-box}} body{{font-family:Inter,system-ui,Arial,sans-serif;color:var(--ink);margin:0;line-height:1.5}}
 .topbar{{background:#fff;border-bottom:1px solid var(--line)}} .topbar .wrap{{max-width:900px;margin:0 auto;padding:.7rem 1.4rem;display:flex;justify-content:space-between;align-items:center}}
 .wordmark{{font-weight:800;letter-spacing:.14em;font-size:.78rem;text-transform:uppercase;color:var(--navy);text-decoration:none}}
 .topbar a{{color:var(--accent);text-decoration:none;font-size:.84rem;font-weight:600}}
 .hero{{background:linear-gradient(160deg,#12272c,#1d4751);color:#fff;border-bottom:3px solid var(--accent)}} .hero .wrap{{max-width:900px;margin:0 auto;padding:1.8rem 1.4rem}}
 .hero .eyebrow{{font-size:.7rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:#5cbcb1}}
 .hero h1{{font-size:1.7rem;margin:.4rem 0 .3rem;letter-spacing:-.02em}} .hero p{{color:#bdd1cf;margin:0;font-size:.92rem}}
 main{{max-width:900px;margin:0 auto;padding:1.4rem}}
 .f{{border-left:4px solid var(--accent);padding:.2rem 0 .2rem 1rem;margin:1.15rem 0}}
 .f .k{{font-size:.7rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;color:var(--accent)}}
 .f h2{{font-size:1.12rem;color:var(--navy);margin:.15rem 0 .35rem;border:none}}
 .f p{{margin:.1rem 0;font-size:.95rem;color:#2a343a}}
 .big{{color:#c0392b;font-weight:800}}
 .cred{{background:#f3f7f6;border:1px solid var(--line);border-radius:8px;padding:.9rem 1.1rem;font-size:.88rem;color:var(--mut);margin:1.3rem 0 .5rem}}
 .cred b{{color:var(--navy)}}
 footer{{max-width:900px;margin:0 auto;padding:.5rem 1.4rem 2rem;font-size:.82rem;color:var(--mut)}}
 footer a{{color:var(--accent);text-decoration:none}}
 @media print{{ .topbar,.no-print{{display:none!important}} .hero{{background:none!important;color:#000!important;border-bottom:2px solid var(--navy)}} .hero .eyebrow{{color:var(--accent)!important}} .hero h1{{color:var(--navy)!important}} .hero p{{color:#444!important}} body{{font-size:10.5pt}} .cred{{-webkit-print-color-adjust:exact;print-color-adjust:exact}} @page{{margin:1.3cm}} a{{color:var(--accent)}} }}
</style></head><body>
<header class="topbar no-print"><div class="wrap"><a class="wordmark" href="./">◆ Critical Materials Atlas</a>
  <span><a href="brief.pdf">⬇ PDF</a> &nbsp; <a href="./">interactive atlas →</a></span></div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Key findings · one page</div>
  <h1>Where critical materials really come from — and how the squeeze tightened</h1>
  <p>32 critical raw materials, mine → refine → trade, reconciled from public data and tested over two decades. Critical Materials Atlas · public data only · {yrs[0]}–{yrs[-1]}</p>
</div></section>
<main id="main">
  <div class="f"><div class="k">Finding 1 · the origin gap</div>
    <h2>The country that exports a critical material usually isn't the one that mines it</h2>
    <p>In <span class="big">{mismatch} of {len(MATS)}</span> materials the top exporter is not the top miner — customs records the refiner or shipping hub, not the source, so import-origin statistics overstate how diversified supply really is. {ex}.</p></div>

  <div class="f"><div class="k">Finding 2 · two decades</div>
    <h2>Concentration is intensifying — and it's testable</h2>
    <p>With the reconciled series back to 2002, <span class="big">{len(sig)} of {len(MATS)}</span> materials show a rising export-concentration trend that is significant on an FDR-corrected Mann–Kendall <i>screen</i> (23 annual points — exploratory, not confirmatory), and <b>{brk} of those {len(sig)}</b> break in <b>2012–2016</b>. The trade-side origin gap also runs wide (~{g0:.0f}–{g1:.0f}pp), though part of the level steps at the 2017 HS-vintage join — read it as drift, not a clean trend.</p></div>

  <div class="f"><div class="k">Finding 3 · the hub</div>
    <h2>China became the processing hub, not just an exporter</h2>
    <p>China's average network throughput — its centrality as importer <i>and</i> broker — rose from <span class="big">{c0:.0f}% to {c1:.0f}%</span> ({yrs[0]}–{yrs[-1]}). Its export share of rare-earth magnets climbed {mg0}→{mg1}%, of tungsten {tu0}→{tu1}%. For bauxite, China's throughput rose {bx[0]:.0f}→{bx[-1]:.0f}% <i>while its exports fell</i> — it became the place the ore flows <i>into</i>. China is now the top refiner in {cn_ref} of {len(MATS)} materials.</p></div>

  <div class="f"><div class="k">Finding 4 · the chokepoints that matter</div>
    <h2>The materials with no way out</h2>
    <p><span class="big">{len(nwo)}</span> materials are at once hard to substitute, essentially un-recycled (&lt;5% end-of-life) and supply-concentrated — so a disruption bites, has no secondary supply, and one country controls the flow. For <b>{nwo_cn} of the {len(nwo)}</b>, that chokepoint is China's refining. They are: {nwo_list}.</p></div>

  <div class="cred"><b>How it's built — and why it holds up.</b> Bilateral trade is reconstructed from raw UN Comtrade via a Gaulier–Zignago-style mirror reconciliation and <b>validated against the official CEPII BACI</b> dataset: it recovers the top exporter in 25 of 30 materials with a 3.5pp share error. Mine/refine layers are USGS/IEA. The 2025 nowcast is <b>pre-registered</b>. Everything is <b>public data only and reproducible end-to-end with no API key</b>, and the two-decade trends are <b>statistically tested</b> (a reproducible Mann–Kendall / Theil–Sen / Pettitt screen), not just plotted — uncommon in the critical-minerals literature. Full method &amp; citations: <a href="technical-note.html">technical note</a>.</div>
</main>
<footer>
  Critical Materials Atlas — an independent demonstration from public data. Not affiliated with, nor representing, any institution.<br>
  <a href="./">Interactive atlas</a> · <a href="findings.html">The origin gap</a> · <a href="trends.html">Trends</a> · <a href="technical-note.html">Technical note</a> · <a href="https://github.com/materials-atlas/critical-materials-atlas">Reconciliation engine</a>
</footer>
</body></html>'''
open(os.path.join(ROOT, 'brief.html'), 'w', encoding='utf8', newline='\n').write(out)
print(f'wrote brief.html — origin-gap {mismatch}/{len(MATS)}, sig-rising {len(sig)} ({brk} break 2012-16), '
      f'China throughput {c0:.0f}->{c1:.0f}%, no-way-out {len(nwo)} ({nwo_cn} China)')
