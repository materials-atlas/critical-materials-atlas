"""Build the 'Who actually refines' atlas page (refiners.html) from out/capability_years.json.

A capability map, not an export map: per material, who actually turns ore into refined metal --
scored by fusing the trade feedstock signature (export-control-proof) with BGS/USGS physical output
(catches the domestic-absorbing refiner). Horizontal bars per stage, coloured by capability class
(teal = refiner visible to trade, amber = domestic-absorbing / trade-blind, grey = raw exporter),
with a 2018-2024 year slider showing capability migrating. Includes the downstream NdFeB magnet stage
(trade-only). Matches the atlas chrome (assets/site.css).
"""
import os, json
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
CAP = json.load(open(os.path.join(ROOT, 'out', 'capability_years.json'), encoding='utf-8'))
EXP = json.load(open(os.path.join(ROOT, 'out', 'exposure.json'), encoding='utf-8'))
OPP = json.load(open(os.path.join(ROOT, 'out', 'opportunity.json'), encoding='utf-8'))
SCN = json.load(open(os.path.join(ROOT, 'out', 'scenario.json'), encoding='utf-8'))
PHYS = json.load(open(os.path.join(ROOT, 'out', 'capability_physical.json'), encoding='utf-8'))
# IEA Critical Minerals Dataset (CC BY 4.0): authoritative REFINING concentration by country, catches the
# trade-blind domestic-absorbers (lithium/graphite/magnets). Local slim has top-1/top-3 refining shares.
import csv as _csv
IEA = {}
_iea_path = os.path.join(ROOT, 'raw', 'iea', 'iea_supply_concentration.csv')
if os.path.exists(_iea_path):
    _i3to2 = {'CHN': 'CN', 'IDN': 'ID', 'COD': 'CD', 'AUS': 'AU', 'CHL': 'CL', 'USA': 'US', 'RUS': 'RU'}
    for _r in _csv.DictReader(open(_iea_path, encoding='utf-8')):
        if _r['stage'] == 'refining':
            IEA[_r['material']] = {'top1': _i3to2.get(_r['top1_country'], _r['top1_country']),
                                   'top1_share': float(_r['top1_share']), 'top3_share': float(_r['top3_share'])}
# EU CRM 2023 (EC official): top global supplier + bottleneck stage for ~31 materials -- the one public
# source with a per-country processing figure for specialty metals.
_eucrm_path = os.path.join(ROOT, 'out', 'eucrm.json')
EUCRM = json.load(open(_eucrm_path, encoding='utf-8'))['materials'] if os.path.exists(_eucrm_path) else {}
# USGS World Minerals Outlook to 2029 (forward capacity): 8 commodities, 2024 concentration + world growth
_usgs_path = os.path.join(ROOT, 'out', 'usgs_outlook.json')
USGS = json.load(open(_usgs_path, encoding='utf-8'))['materials'] if os.path.exists(_usgs_path) else {}
# Diversification pipeline overlay (curated public projects + IEA 2035 context)
_pipe_path = os.path.join(ROOT, 'out', 'pipeline.json')
PIPE = json.load(open(_pipe_path, encoding='utf-8'))['materials'] if os.path.exists(_pipe_path) else {}
# robustness (BACI vs raw Comtrade) + HS-code provenance (auditable caveats)
_rob_path = os.path.join(ROOT, 'out', 'robustness.json')
ROB = json.load(open(_rob_path, encoding='utf-8')) if os.path.exists(_rob_path) else {}
_prov_path = os.path.join(ROOT, 'out', 'code_provenance.json')
PROV = json.load(open(_prov_path, encoding='utf-8'))['materials'] if os.path.exists(_prov_path) else []

# display crosswalk for the traceable ore-pair materials (shown first); everyone else gets its traded code
_CW = {'copper': ('260300', '740311'), 'nickel': ('260400', '750210'), 'cobalt': ('260500', '282200'),
       'tungsten': ('261100', '810194'), 'titanium': ('261400', '810820'), 'antimony': ('261710', '811010'),
       'bauxite': ('260600', '281820'), 'tantalum': ('261590', '810320'), 'niobium': ('261590', '720293'),
       'manganese': ('260200', '8111/7202'), 'magnets': ('2805.30/2846.90', '850511')}
_ORDER1 = ['copper', 'nickel', 'cobalt', 'tungsten', 'titanium', 'antimony', 'bauxite',
           'tantalum', 'niobium', 'manganese', 'magnets']
_d2 = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
_bylab = {m['label']: m for m in _d2['materials']}
def _nm(m):
    t = m['title']; return t[:t.find('(')].strip() if '(' in t else t
def _hs6(m):
    t = m['title']; c = ''.join(ch for ch in t[t.find('(') + 1:t.find(')')] if ch.isdigit()); return c[:6]
_rest = sorted((m['label'] for m in _d2['materials'] if m['label'] not in _ORDER1), key=lambda L: _nm(_bylab[L]))
STAGES = []
for lab in _ORDER1 + _rest:
    m = _bylab.get(lab)
    if not m:
        continue
    key = 'magnet (NdFeB)' if lab == 'magnets' else lab
    ore, ref = _CW.get(lab, ('', _hs6(m)))
    STAGES.append((key, _nm(m), ore, ref))
DATA = json.dumps({'stages': CAP['stages'], 'years': CAP['years'], 'latest': CAP['latest'],
                   'exposure': EXP['materials'], 'exp_year': EXP['year'], 'opportunity': OPP,
                   'ranking': EXP['ranking'], 'scenario': SCN['materials'], 'physical': PHYS, 'iea': IEA, 'eucrm': EUCRM, 'usgs': USGS, 'pipeline': PIPE, 'rob': ROB, 'prov': PROV,
                   'order': [{'key': k, 'name': n, 'ore': o, 'ref': r} for k, n, o, r in STAGES]},
                  ensure_ascii=False)

HTML = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Who actually refines — Critical Materials Atlas</title>
<meta name="description" content="A capability map, not an export map: fusing the trade feedstock signature (imports ore, exports refined) with BGS/USGS physical output to show who actually turns ore into refined metal across all 32 critical materials, 2018-2024.">
<meta property="og:title" content="Who actually refines — capability map">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .capgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:20px;margin:1.2rem 0}
 .capcard{border:1px solid var(--line);border-radius:12px;padding:14px 16px 16px;background:var(--bg)}
 .capcard h3{font-size:1rem;margin:0 0 2px;display:flex;justify-content:space-between;align-items:baseline;gap:8px}
 .capcard h3 .hs{font-size:.66rem;color:var(--faint);font-weight:500;letter-spacing:.2px}
 .capcard .lead{font-size:.76rem;color:var(--mut);margin:0 0 8px;min-height:2.1em}
 .capcard .lead b{color:var(--ink)}
 .choke{display:flex;align-items:center;gap:7px;font-size:.72rem;color:var(--mut);margin:0 0 9px;flex-wrap:wrap}
 .choke .pill{font-size:.64rem;font-weight:700;text-transform:uppercase;letter-spacing:.3px;
   padding:2px 7px;border-radius:20px;color:#fff}
 .pill-extreme{background:#b4291f} .pill-high{background:#d1701a} .pill-moderate{background:#c79a1a} .pill-diffuse{background:#8a94a0}
 .choke b{color:var(--ink-soft)}
 .row{display:flex;align-items:center;gap:8px;margin:5px 0;font-size:.8rem}
 .row .who{width:118px;flex:0 0 118px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 .row .track{flex:1;height:15px;background:var(--bg-soft);border-radius:4px;position:relative;overflow:hidden}
 .row .fill{display:block;height:100%;border-radius:4px 3px 3px 4px}
 .row .val{width:34px;flex:0 0 34px;text-align:right;font-variant-numeric:tabular-nums;color:var(--ink-soft);font-weight:600}
 .row .tag{font-size:.64rem;color:var(--mut);white-space:nowrap}
 .cf-refiner{background:#0e8f83} .cf-absorb{background:#e08a1f} .cf-raw{background:#8a94a0}
 .ct-refiner{color:#0b6f66} .ct-absorb{color:#a5641a} .ct-raw{color:#6b7681}
 .controls{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:.4rem 0 .2rem;
   padding:12px 16px;border:1px solid var(--line);border-radius:10px;background:var(--bg-soft)}
 .controls input[type=range]{flex:1;min-width:180px;accent-color:var(--accent)}
 .controls .yr{font-size:1.5rem;font-weight:800;color:var(--navy);font-variant-numeric:tabular-nums;min-width:74px}
 .controls .hint{font-size:.74rem;color:var(--mut)}
 .caplegend{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:.78rem;color:var(--ink-soft);margin:.2rem 0 0}
 .caplegend span{display:flex;align-items:center;gap:6px} .caplegend i{width:12px;height:12px;border-radius:3px;display:inline-block}
 .cand{font-size:.72rem;color:var(--mut);margin:9px 0 0;padding-top:8px;border-top:1px dashed var(--line)}
 .cand span{color:var(--faint)}
 .choke-all{margin:1rem 0 .5rem}
 .crow{display:flex;align-items:center;gap:9px;margin:3px 0;font-size:.8rem}
 .crow .cm{width:172px;flex:0 0 172px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 .crow .ct{flex:1;height:15px;background:var(--bg-soft);border-radius:4px;overflow:hidden}
 .crow .cfill{display:block;height:100%;border-radius:4px} .crow .cv{width:70px;flex:0 0 70px;font-size:.72rem;color:var(--ink-soft)}
 .cb-extreme{background:#b4291f} .cb-high{background:#d1701a} .cb-moderate{background:#c79a1a} .cb-diffuse{background:#8a94a0}
 .scn-row{display:grid;grid-template-columns:170px 200px 1fr auto;gap:12px;align-items:center;
   font-size:.8rem;padding:6px 10px;border-radius:7px;margin:3px 0}
 .scn-row.spof{background:#fbeeec;border:1px solid #e7c6bf}
 .scn-row .sm{font-weight:600;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 .scn-row .sl{color:var(--ink-soft)} .scn-row .sf{color:var(--mut)}
 .spofbadge{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.3px;color:#fff;background:#b4291f;padding:2px 8px;border-radius:20px;white-space:nowrap}
 .formbadge{font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.3px;color:#7a4a12;background:#fbead0;border:1px solid #ecc98d;padding:2px 7px;border-radius:20px;white-space:nowrap}
 .scn-forms{margin:-1px 0 6px 10px;padding:7px 12px;border-left:2px solid #ecc98d;background:#fffaf1;border-radius:0 7px 7px 0;font-size:.75rem;color:var(--mut)}
 .scn-forms .fh{font-weight:700;color:var(--ink-soft);margin-bottom:3px}
 .scn-forms .fr{display:grid;grid-template-columns:150px 1fr auto;gap:10px;padding:2px 0;align-items:baseline}
 .scn-forms .fr .fl{font-weight:600;color:var(--ink)} .scn-forms .fr .fv{color:var(--mut)}
 .scn-forms .yes{color:#b4291f;font-weight:700} .scn-forms .no{color:#0e8f83;font-weight:700}
 @media(max-width:720px){.scn-row{grid-template-columns:1fr;gap:2px}.scn-forms .fr{grid-template-columns:1fr}}
 .pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;margin:1rem 0}
 .pcard{border:1px solid var(--line);border-radius:11px;padding:12px 14px 13px;background:var(--bg)}
 .pcard h3{font-size:.94rem;margin:0 0 8px;display:flex;justify-content:space-between;gap:8px;align-items:baseline}
 .pcard h3 .pl{font-size:.66rem;color:var(--mut);font-weight:500;white-space:nowrap}
 .prow{display:grid;grid-template-columns:92px 1fr 86px;gap:8px;align-items:center;font-size:.73rem;margin:5px 0}
 .prow .pw{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .pbars{display:flex;flex-direction:column;gap:2px}
 .pbar{height:7px;border-radius:3px;background:var(--bg-soft);position:relative;overflow:hidden}
 .pbar i{position:absolute;left:0;top:0;bottom:0;border-radius:3px}
 .pmine i{background:#9aa6ad} .pref i{background:#0e8f83}
 .prow .pt{font-size:.63rem;color:var(--mut);text-align:right;line-height:1.15}
 .pdual{font-size:.72rem;color:var(--mut);margin:.1rem 0 0;display:flex;gap:14px}
 .pdual span{display:flex;align-items:center;gap:5px} .pdual i{width:11px;height:8px;border-radius:2px;display:inline-block}
 .iea{font-size:.68rem;color:var(--accent);margin:8px 0 0;padding-top:7px;border-top:1px dashed var(--line)}
 .iea b{color:var(--ink-soft)}
 .pipe{margin:8px 0 0;padding-top:7px;border-top:1px dashed var(--line)}
 .pipe .ph{font-size:.66rem;font-weight:700;color:var(--hot);text-transform:uppercase;letter-spacing:.3px}
 .pipe .ctx{font-size:.66rem;color:var(--mut);margin:2px 0 4px;line-height:1.4}
 .pipe .pj{display:inline-block;margin:2px 4px 0 0;padding:1px 7px;border-radius:11px;background:var(--bg-soft);
   border:1px solid var(--line);font-size:.64rem;color:var(--ink-soft);cursor:help}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="findings.html">Findings</a>
  <a href="product-space.html" class="hideable">Product space</a><a href="complexity.html" class="hideable">Complexity</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · capability, not exports</div>
  <h1>Who actually refines</h1>
  <p class="deck">The refiner is not the miner &mdash; but the exporter is not always the refiner either. This is a <b>capability map</b>: for each material it fuses two lenses to show who genuinely turns ore into refined metal. The <b>trade feedstock signature</b> (a country that <i>imports ore and exports refined</i> is transforming it &mdash; a fingerprint that survives export controls) plus <b>BGS/USGS physical output</b>, which catches the <i>domestic-absorbing</i> refiner &mdash; a giant like China that refines enormous volumes but consumes them at home, so it never shows up in refined exports.</p>
</div></section>
<article style="max-width:1180px">
  <div class="callout"><b>A chokepoint</b> is a stage of the supply chain where so few countries hold the capacity that everyone else depends on them &mdash; a point where one supplier&rsquo;s decision (an export ban, an accident, a policy) can squeeze the whole world. We measure it at the <i>refining</i> stage with the <b>HHI</b> (Herfindahl index, the sum of squared national shares): 0 = perfectly spread, 1 = a single country. Above 0.25 is concentrated, above 0.5 extreme.
  <br><br>A country scores as capable if <i>either</i> lens sees it: <code>cap = max(physical share, trade score)</code>. Colour marks the class that matters most &mdash; can the trade data even see it? <span class="ct-refiner"><b>Teal</b></span> = a refiner visible in trade (it exports refined). <span class="ct-absorb"><b>Amber</b></span> = a domestic-absorbing refiner only physical data catches. <span class="ct-raw"><b>Grey</b></span> = a raw exporter (ships ore, no refining). The sub-type on each bar says <i>how</i>: integrated (mines + refines), import-fed (refines imported ore), or mine-to-metal.
  <details class="howto"><summary>How it&rsquo;s measured &amp; caveats</summary>
  <p>From the BACI bilateral matrix, per country &times; material: <code>net_down = (refined_exp &minus; refined_imp)/(refined_exp + refined_imp)</code> (&gt;0 = net exporter of refined), <code>feedstock_import = ore_imp/(ore_imp+ore_exp)</code> (~1 = sources ore by import), and <code>trade_score = refined_world_share &times; max(net_down,0)</code> &mdash; a robust, re-export-penalised, export-control-proof marker. Physical refined share is BGS/USGS from the atlas data. <code>cap = max(physical, trade_score)</code>.</p>
  <p class="howto-src"><b>Caveats:</b> the <b>physical share is a single recent vintage</b>, so the year slider moves the <i>trade</i> signal, not the physical one &mdash; migration is clearest where trade carries the story (e.g. the magnet stage). The <b>NdFeB magnet stage is trade-only</b> (no physical magnet series), so premium magnet makers that net-import magnets (Japan, Germany) are undercounted &mdash; the same trade-blindness, now without a physical rescue. REE feedstock codes (2805.30 / 2846.90) are aggregated. Refining concentration is cross-checked against two authoritative sources: the <b>IEA Critical Minerals Dataset</b> (CC BY 4.0) &mdash; refining <i>capacity</i> by country for the energy-transition minerals &mdash; and the <b>EU Critical Raw Materials 2023 study</b> (European Commission), which gives the top global supplier and bottleneck stage (extraction vs processing) for ~31 materials, including the specialty metals where trade and USGS/BGS fall silent (tungsten, gallium, germanium, PGMs). A third, <i>forward</i> layer &mdash; the <b>USGS World Minerals Outlook to 2029</b> (SIR 2025-5021, CC0) &mdash; adds 2024 capacity concentration and world capacity growth for 8 commodities (lithium capacity is set to roughly double; magnesium contracts). A final <b>diversification pipeline</b> overlay names representative publicly announced projects building capacity outside the dominant producer (Lynas, MP Materials, Iluka, Rio Tinto Rincón, Umicore…), with the IEA&rsquo;s aggregate finding that refining/downstream capacity still lags mining to 2035 &mdash; curated, not exhaustive (the IEA&rsquo;s project-level list is not public). The capability score <code>cap = max(physical share, trade score)</code> mixes two units, so read it as a <i>detector and a class</i> (integrated / import-fed / …), not a cardinal 0–1 measure — the bar length is indicative, the type is the finding. The IEA / EU-CRM / USGS cross-check lines are different <i>vintages and stages</i>, so they can disagree with the bar and with each other (that&rsquo;s expected, not an error). &ldquo;Most product-space-adjacent non-refiners&rdquo;: raw density is ~95–98% just a country&rsquo;s overall <i>diversity</i> (big diversified economies are close to everything — a control-test finding), so the list is ranked on density with breadth (diversity + ECI) <b>regressed out</b> — proximity to <i>this</i> stage beyond what size alone buys. Even so, read them as <i>plausible</i>, not destined. Built by <code>build_feedstock.py</code>. <b>See also</b> <a href="breakout.html">Break the chokepoint</a> (the decision layer: what kind of moat, who could break it, who is building it), <a href="refining.html">The refining wedge</a> (does concentration rise from ore to metal? + IEA capacity), the <a href="product-space.html">product-space map</a> and <a href="complexity.html">complexity</a>.</p>
  </details></div>

  <h2 style="margin:1.6rem 0 .3rem;font-size:1.18rem">Capability over time — all 32 materials</h2>
  <p class="note" style="margin-top:0">Trade-based capability score with the year slider. The first ~11 (a clean ore&rarr;refined HS pair) carry the full feedstock fingerprint &mdash; <i>import-fed</i> vs <i>mine-to-metal</i>; the rest are typed from physical mine-vs-refine. Below, the same 32 get a plain mine-vs-refine read, then the chokepoint ranking and the supply-shock test.</p>
  <div class="controls">
    <span class="yr" id="yr"></span>
    <input type="range" id="slider" min="0" step="1">
    <span class="hint">drag to watch capability migrate, 2018&rarr;2024</span>
  </div>
  <div class="caplegend">
    <span><i style="background:#0e8f83"></i> refiner (visible in trade)</span>
    <span><i style="background:#e08a1f"></i> domestic-absorbing (physical only)</span>
    <span><i style="background:#8a94a0"></i> raw exporter</span>
  </div>

  <div class="capgrid" id="grid"></div>

  <h2 style="margin:2rem 0 .3rem;font-size:1.18rem">Every critical material — who mines it vs who refines it</h2>
  <p class="note" style="margin-top:0">The cards above score capability from <i>trade</i>, with the full ore&rarr;refined feedstock fingerprint where a clean HS pair exists (~11 materials) and a physical-derived type otherwise. This second grid gives the same <b>all 32</b> materials the plainest read of all &mdash; each country&rsquo;s <b>mine</b> share (grey) above its <b>refine</b> share (teal), the mine&rarr;refine handoff itself: a country that refines far more than it mines is <b>import-fed</b>; one that does both is <b>integrated</b>; one that digs but doesn&rsquo;t refine is a <b>raw exporter</b>.</p>
  <div class="pdual"><span><i style="background:#9aa6ad"></i> mine share</span><span><i style="background:#0e8f83"></i> refine share</span></div>
  <div class="pgrid" id="pgrid"></div>

  <h2 style="margin:1.9rem 0 .3rem;font-size:1.18rem">All critical materials, by refining chokepoint</h2>
  <p class="note" style="margin-top:0"><b id="ck-head"></b> The full ore&rarr;refined <i>trade</i> fingerprint (import-fed vs mine-to-metal) needs a clean HS pair, which ~11 of 32 materials have; the rest are typed from physical shares. Refining <i>concentration</i> needs only refined-output shares, so it spans all 29 that report them. HHI over BGS/USGS refined shares (magnets: HS 850511 exports). Colour = chokepoint band.</p>
  <div class="choke-all" id="ranking"></div>

  <h2 style="margin:1.9rem 0 .3rem;font-size:1.18rem">The fallback test — if the top refiner stopped supplying</h2>
  <p class="note" style="margin-top:0"><b id="scn-head"></b> A supply-shock <i>counterfactual</i>, not a forecast. The leader&rsquo;s share of world refined <b>output</b> is the magnitude at risk; the <b>fallback</b> is who else <i>exports</i> the refined form onto the world market — the countries the rest of the world could actually buy from (a hoarded-at-home refiner is not a fallback; an exporter is). A material is a single point of failure only if the leader holds &ge;50% of output <i>and</i> no other exporter reaches a third of its export volume. Export fallbacks can include re-export hubs, so read them as availability, not independent capacity. This is an export-share <b>screen</b>, not a capacity test — the <a href="ot.html">reallocation stress test</a> asks the harder question of whether the world&rsquo;s remaining capacity could actually cover a cut, and by design flags a <i>different</i>, stricter set as &ldquo;structurally uncoverable.&rdquo; Materials whose refined form has no separable trade series (gallium and germanium share the &ldquo;other minor metals&rdquo; basket HS 811292) <b>cannot be run through this trade screen</b>, so they carry a <b>production-based read</b> instead (USGS MCS / EU CRM): gallium is a genuine near-monopoly chokepoint, while germanium is concentrated but has real alternative refiners (Umicore, Teck, Russia) the shared code hides. And where a material trades in more than one refined form (tungsten as metal vs APT chemical; manganese as metal vs ferro-alloys), the verdict can <b>change with the form</b> — the leader can be a single point of failure in one and have a real backup exporter in another; those rows carry a &ldquo;depends on form&rdquo; note with the per-form breakdown.</p>
  <div id="scn" style="margin:.6rem 0 1rem"></div>

  <p class="note">Reading it: the <b>miner and the refiner are usually different countries</b>, and the refiner sits downstream where the value is. The amber bars are the story the export data alone would miss &mdash; China refining copper, alumina and titanium sponge for its own industry, invisible to any trade metric. At the <b>magnet stage</b>, capability collapses onto a single country: watch China climb from 0.39 (2018) to 0.58 (2024) as the rest of the world stays near zero.</p>
  <details class="howto" style="margin:1.4rem 0"><summary style="font-weight:600;font-size:1rem">Robustness &amp; HS-code provenance</summary>
  <p class="note" id="rob-note" style="margin-top:.6rem"></p>
  <div style="overflow-x:auto;margin:.4rem 0 1rem"><table id="rob-tbl" style="font-size:.78rem;border-collapse:collapse;min-width:520px"></table></div>
  <h4 style="margin:.4rem 0 .2rem">HS-code provenance — which codes are clean</h4>
  <div style="overflow-x:auto"><table id="prov-tbl" style="font-size:.78rem;border-collapse:collapse;min-width:640px"></table></div>
  <p class="howto-src">Independent robustness: two separate reconciliations of UN Comtrade &mdash; <b>BACI</b> (CEPII) and the <b>Harvard Growth Lab</b> Atlas (Bustos-Yildirim method, queried live via its public GraphQL API) &mdash; plus <b>raw</b> reporter-declared Comtrade. Agreement between the two independent reconciliations is the belt-and-braces check; a &#9888; marks a leader that differs from BACI. OECD BIMTS is balanced trade at aggregate (not HS6) level, so it can&rsquo;t cross-check individual refined codes. Built by <code>build_robustness.py</code> + <code>build_harvard.py</code>; provenance by <code>build_provenance.py</code>.</p>
  </details>

  <p class="note" style="color:var(--faint);font-size:.76rem">Method lineage: Hidalgo &amp; Hausmann product space / economic complexity; feedstock-signature capability mapping addresses the export-RCA-&ne;-capability critique (constrain with physical output; read the direction of transformation). Cf. the product-space paper on China&rsquo;s critical minerals (Frontiers Env. Sci. 2023) and the Fitness-Criticality algorithm (Valverde-Carbonell, Pietrobelli &amp; Men&eacute;ndez, Resources Policy 2024).</p>
</article>
<script>
const D=DATA_PLACEHOLDER;
const S=document.getElementById('slider'), YR=document.getElementById('yr'), GRID=document.getElementById('grid');
S.max=D.years.length-1; S.value=D.years.indexOf(D.latest);
function flag(iso){ if(!iso||iso.length!==2) return ''; return iso.toUpperCase().replace(/./g,c=>String.fromCodePoint(0x1F1E6-65+c.charCodeAt(0)))+' '; }
function cls(t){ if(t.startsWith('domestic-absorbing')) return 'absorb'; if(t==='raw exporter'||t==='feedstock exporter') return 'raw'; return 'refiner'; }
function subtype(t){ return t.replace(' refiner','').replace('domestic-absorbing','domestic-absorbing').replace('mine-to-metal','mine→metal'); }
const SCALE=0.9;   // cap is ~world-share; fixed scale so years/materials compare
function render(){
  const yi=+S.value, year=D.years[yi]; YR.textContent=year;
  GRID.innerHTML='';
  for(const st of D.order){
    const rows=(D.stages[st.key]&&D.stages[st.key][year])||[];
    const shown=rows.filter(r=>r.cap>=0.03).slice(0,7);
    const top=shown[0];
    const card=document.createElement('div'); card.className='capcard';
    let lead='';
    if(top){ const basis = top.basis==='both'?'trade + physical confirm it':top.basis.startsWith('physical')?'<b>only physical data sees it</b> (absorbs output)':'trade signature';
      lead=`Top: <b>${flag(top.iso)}${top.name}</b> &mdash; ${basis}.`; }
    else lead='No country clears the capability floor.';
    const ex=D.exposure[st.key]; let choke='';
    if(ex){ const rel=(ex.reliant||[]).slice(0,4).map(r=>flag(r.iso).trim()).join(' ');
      choke=`<div class="choke"><span class="pill pill-${ex.band}">${ex.band} chokepoint</span>`+
        `<span>HHI <b>${ex.hhi.toFixed(2)}</b> · ${flag(ex.top)}<b>${ex.top}</b> ${ex.top_share.toFixed(0)}%`+
        `${rel?` · reliant: ${rel}`:''}</span></div>`; }
    card.innerHTML=`<h3>${st.name}<span class="hs">${st.ore?st.ore+' → ':''}${st.ref}</span></h3><p class="lead">${lead}</p>${choke}`;
    for(const r of shown){
      const c=cls(r.type); const w=Math.max(3,Math.min(100,r.cap/SCALE*100));
      const row=document.createElement('div'); row.className='row';
      row.innerHTML=`<span class="who" title="${r.name}">${flag(r.iso)}${r.name}</span>`+
        `<span class="track"><span class="fill cf-${c}" style="width:${w}%"></span></span>`+
        `<span class="val">${r.cap.toFixed(2)}</span>`+
        `<span class="tag ct-${c}">${subtype(r.type)}</span>`;
      card.appendChild(row);
    }
    const op=D.opportunity[st.key];
    if(op&&op.candidates&&op.candidates.length){
      const cands=op.candidates.slice(0,5).map(c=>flag(c.c).trim()).join(' ');
      const corr=op.density_eci_corr;
      const f=document.createElement('p'); f.className='cand';
      f.innerHTML=`<span>most product-space-adjacent non-refiners${corr!=null?`, breadth removed <span style="opacity:.7">(raw density is ${Math.round(corr*100)}% just diversity)</span>`:''}:</span> ${cands} <span style="opacity:.7">— proximity beyond overall diversity; plausible, not destined.</span>`;
      card.appendChild(f);
    }
    GRID.appendChild(card);
  }
}
S.addEventListener('input',render); render();
// physical mine-vs-refine capability cards (all 29 materials)
const PG=document.getElementById('pgrid');
const ptag={'integrated (mine+refine)':'integrated','import-fed refiner':'import-fed','mine-to-metal refiner':'mine→metal','raw exporter':'raw exporter'};
const _physOrder=D.ranking.map(r=>r.label).concat(Object.keys(D.physical).filter(l=>!D.ranking.some(r=>r.label===l)));
for(const lab of _physOrder){
  const rk={label:lab}; const p=D.physical[lab]; if(!p) continue;
  const card=document.createElement('div'); card.className='pcard';
  let h=`<h3>${p.name}<span class="pl">⛏ ${flag(p.mine_leader).trim()} · ⚗ ${flag(p.refine_leader).trim()}</span></h3>`;
  for(const r of p.rows){
    h+=`<div class="prow"><span class="pw" title="${r.iso}">${flag(r.iso).trim()}</span>`+
       `<span class="pbars"><span class="pbar pmine" title="mine ${r.mine}%"><i style="width:${Math.min(100,r.mine)}%"></i></span>`+
       `<span class="pbar pref" title="refine ${r.refine}%"><i style="width:${Math.min(100,r.refine)}%"></i></span></span>`+
       `<span class="pt">${ptag[r.type]||r.type}</span></div>`;
  }
  const ie=D.iea[rk.label], eu=D.eucrm[rk.label];
  if(ie||eu){
    h+='<p class="iea">';
    if(ie) h+=`IEA refining capacity: ${flag(ie.top1).trim()} <b>${ie.top1_share.toFixed(0)}%</b> · top-3 ${ie.top3_share.toFixed(0)}%`;
    if(ie&&eu) h+='<br>';
    if(eu) h+=`EU CRM 2023 (${eu.stage}): ${flag(eu.iso).trim()} <b>${eu.pct}%</b>`;
    h+='</p>';
  }
  const ug=D.usgs[rk.label];
  if(ug){
    const g=ug.world_growth_pct, arrow=g>3?'↑':g<-3?'↓':'→';
    h+=`<p class="iea" style="color:#8a5cf0">USGS outlook 2029 (${ug.stage} capacity): ${flag(ug.top).trim()} <b>${ug.top_share.toFixed(0)}%</b> in 2024 · world capacity <b>${g>=0?'+':''}${g}%</b> ${arrow}</p>`;
  }
  const pp=D.pipeline[rk.label];
  if(pp){
    h+='<div class="pipe"><span class="ph">Diversification pipeline → ~2035</span>';
    if(pp.iea) h+=`<p class="ctx">${pp.iea}</p>`;
    h+=pp.projects.map(p=>`<span class="pj" title="${p.stage} · ${p.status}">${flag(p.iso)}${p.name}</span>`).join('');
    h+='</div>';
  }
  card.innerHTML=h; PG.appendChild(card);
}
// all-materials chokepoint ranking (latest year, static)
const RK=document.getElementById('ranking'), CKH=document.getElementById('ck-head');
const ext=D.ranking.filter(r=>r.band==='extreme').length, cn=D.ranking.filter(r=>r.top==='CN').length;
CKH.textContent=`${ext} of ${D.ranking.length} are extreme chokepoints; China is the single largest refiner of ${cn} of them.`;
for(const r of D.ranking){
  const el=document.createElement('div'); el.className='crow';
  const partial=(r.listed_pct!=null&&r.listed_pct<80)?` <span title="physical breakdown covers only ${r.listed_pct}% of world output — HHI is a lower bound" style="color:var(--faint)">·${r.listed_pct}%◐</span>`:'';
  el.innerHTML=`<span class="cm" title="${r.name}">${r.name}</span>`+
    `<span class="ct"><span class="cfill cb-${r.band}" style="width:${Math.max(2,r.hhi*100)}%"></span></span>`+
    `<span class="cv">${r.hhi.toFixed(2)} · ${flag(r.top).trim()} ${r.top_share.toFixed(0)}%${partial}</span>`;
  RK.appendChild(el);
}
// supply-shock stress test
const SCN=document.getElementById('scn'), SH=document.getElementById('scn-head');
const spofs=D.scenario.filter(r=>r.spof), cnspof=spofs.filter(r=>r.leader==='CN').length;
const nShared=D.scenario.filter(r=>r.shared).length, nAssessable=D.scenario.length-nShared;
SH.textContent=`Only ${spofs.length} of ${nAssessable} assessable materials fail this export-fallback screen — no other exporter reaches a third of the leader's volume, the single points of failure on this measure (China leads ${cnspof}). A separate capacity test on the reallocation page flags a different set as structurally uncoverable; ${nShared} materials that share the 811292 trade basket (gallium, germanium) can't be run through the trade screen, so they carry a production-based read instead.`;
for(const r of D.scenario){
  const el=document.createElement('div'); el.className='scn-row'+(r.spof?' spof':'');
  const badge = r.form_dependent
    ? `<span class="formbadge" title="single point of failure in one refined form but not another">depends on form</span>`
    : (r.spof?`<span class="spofbadge">single point</span>`:`<span></span>`);
  const p=r.prod||{};
  const detail = r.shared
    ? `<span class="sl">${flag(r.leader).trim()} <b>${(p.usgs_bgs_share||r.lead_share).toFixed(0)}%</b> production${p.eucrm_share!=null?` · ${p.eucrm_share}% EU CRM`:''}</span>`+
      `<span class="sf">Trade can&rsquo;t separate it (811292 basket) — read from production instead. ${p.note||''}</span>`+
      (p.verdict==='chokepoint'
        ? `<span class="spofbadge" title="verdict from USGS/EU CRM production data, not trade">chokepoint · production</span>`
        : `<span class="formbadge" style="background:#dff3f0;color:#0e7a70;border-color:#a6e0d8" title="production-concentrated but real alternative refiners exist">has alt refiners</span>`)
    : `<span class="sl">${flag(r.leader).trim()} <b>${r.lead_share.toFixed(0)}%</b> output · ${r.lead_export_share.toFixed(0)}% exports</span>`+
      `<span class="sf">fallback exporters: ${(r.fallbacks||[]).map(f=>`${flag(f.iso).trim()} ${f.export_share.toFixed(0)}%`).join(' · ')||'none'}</span>`+
      badge;
  el.innerHTML=`<span class="sm" title="${r.name}">${r.name}</span>`+detail;
  SCN.appendChild(el);
  if(r.by_form&&r.by_form.length){
    const fx=document.createElement('div'); fx.className='scn-forms';
    const rows=r.by_form.map(f=>{
      const fb=(f.fallbacks||[]).map(x=>`${flag(x.iso).trim()} ${x.export_share.toFixed(0)}%`).join(' · ')||'none';
      return `<div class="fr"><span class="fl">${f.label}</span>`+
        `<span class="fv">${flag(r.leader).trim()} ${f.lead_export_share.toFixed(0)}% exports · fallback ${fb}</span>`+
        `<span class="${f.spof?'yes':'no'}">${f.spof?'single point':'has backup'}</span></div>`;
    }).join('');
    fx.innerHTML=`<div class="fh">By refined form — ${r.form_dependent?'the answer changes with the form':'consistent across forms'}:</div>`+rows;
    SCN.appendChild(fx);
  }
}
// robustness note + HS-code provenance table
if(D.rob&&D.rob.rows){
  document.getElementById('rob-note').innerHTML=
    (function(){
      const nm={'740311':'copper','750210':'nickel','282200':'cobalt','810194':'tungsten','810820':'titanium','811010':'antimony','281820':'bauxite','810320':'tantalum','720293':'niobium','850511':'magnets'};
      const reconDiff=D.rob.rows.filter(r=>'recon_match' in r && !r.recon_match).map(r=>nm[r.code]||r.code);
      const comDiff=D.rob.rows.filter(r=>'comtrade_match' in r && !r.comtrade_match).map(r=>nm[r.code]||r.code);
      const reconTxt=reconDiff.length?`the exception${reconDiff.length>1?'s are':' is'} ${reconDiff.join(', ')}`:'with no exceptions';
      return `<b>Trade robustness (${D.rob.year}):</b> two <i>independent</i> reconciliations of UN Comtrade &mdash; CEPII&rsquo;s <b>BACI</b> and the Harvard Growth Lab&rsquo;s <b>Bustos-Yildirim</b> series &mdash; agree on the refining leader for <b>${D.rob.recon_match} of ${D.rob.recon_n}</b> refined codes (${reconTxt}). Against <b>raw</b> Comtrade (reporter-declared) BACI agrees ${D.rob.comtrade_match}/${D.rob.comtrade_n}; the codes where raw Comtrade differs (${comDiff.join(', ')||'none'}) are largely ones where <i>both</i> reconciliations agree with each other, pinning the divergence on Comtrade reporter gaps rather than the reconciliation. Every extreme chokepoint agrees across all three sources.`;
    })();
}
const rt=document.getElementById('rob-tbl');
if(rt&&D.rob.rows){
  rt.innerHTML='<tr style="text-align:left;border-bottom:1px solid var(--line)"><th>Refined code</th><th>BACI (CEPII)</th><th>raw Comtrade</th><th>Harvard (B-Y)</th></tr>'+
    D.rob.rows.map(r=>`<tr style="border-bottom:1px solid var(--bg-soft)"><td>${r.code}</td>`+
      `<td><b>${r.baci_top}</b> ${r.baci_share}%</td>`+
      `<td>${r.comtrade_top?flag(r.comtrade_top).trim()+' '+r.comtrade_share+'%'+(r.comtrade_match?'':' ⚠'):'—'}</td>`+
      `<td>${r.harvard_top?flag(r.harvard_top).trim()+' '+r.harvard_share+'%'+(r.recon_match?'':' ⚠'):'—'}</td></tr>`).join('');
}
const pcol={'clean':'#0b6f66','refined':'#6b7681','shared':'#b4291f','by-product':'#a5641a','mine':'#6b7681'};
function pc(f){for(const k in pcol) if(f.startsWith(k)) return pcol[k]; return '#6b7681';}
const PT=document.getElementById('prov-tbl');
if(PT&&D.prov){
  PT.innerHTML='<tr style="text-align:left;border-bottom:1px solid var(--line)"><th>Material</th><th>Ore HS6</th><th>Refined HS6</th><th>Refined stage</th><th>Data-quality flag</th></tr>'+
    D.prov.map(r=>`<tr style="border-bottom:1px solid var(--bg-soft)"><td>${r.name}</td><td>${r.ore||'—'}</td><td>${r.refined}</td><td style="color:var(--mut)">${r.refined_stage}</td><td style="color:${pc(r.flag)};font-weight:600">${r.flag}</td></tr>`).join('');
}
</script>
</body></html>'''

out = os.path.join(ROOT, 'refiners.html')
open(out, 'w', encoding='utf-8').write(HTML.replace('DATA_PLACEHOLDER', DATA))
print('WROTE', out)
