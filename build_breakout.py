"""Break the chokepoint -- the DECISION layer.

The atlas already proves *where* the chokepoints are and *that* they are a capability
(not an ore endowment). This builder answers the reader's next question -- "so what do I
do about it?" -- by joining four things the atlas computes but never puts in one table:

  PROBLEM   who holds the refined chokepoint, how concentrated (HHI / SPOF), and WHICH
            KIND of moat it is -- because the moat type decides what, if anything, works:
              * import-fed capability  (buys ore, sells refined: JP titanium, ID nickel,
                CN tungsten) -- export controls on ORE cannot touch it; you must build
                refining capability elsewhere.
              * by-product capability  (CN gallium/germanium from domestic alumina/zinc)
                -- there is no ore to redirect; the metal is a companion of a host you
                don't control. Substitution means new by-product recovery lines.
              * integrated (endowment+capability) -- leader mines AND refines; here ore
                access is a real lever (the one case export policy bites).
              * mine-side endowment  (baryte/coking coal/helium) -- geology, not furnace.
  WHO COULD who could realistically stand it up. STRONG signal = product-space capability-
            adjacency with the leader REMOVED (density_exCN) -- but that only exists for the
            8 clean ore->refined pairs. For the rest we fall back to CURRENT alternative-
            supplier share, which is a WEAKER proxy (presence, not latent capability); the
            method is labelled per material so the two are never conflated.
  WHO IS    who is actually building it -- announced pipeline (Lynas/MP/Iluka...) + USGS
            forward capacity to 2029. Thin on purpose-honest: pipeline covers few materials.
            Blank cells are a SOURCING GAP (shown blank), not an implied "no one".
  VERDICT   one plain sentence a reader can act on: capability exists in {X}; only {Y} is
            building; the gap is the vulnerability.

Reads out/{crosswalk,capability,mine_refine,usgs_outlook,pipeline,scenario}.json;
writes out/breakout.json.  Run:  python build_breakout.py
"""
import os, json, sys
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
def L(f): return json.load(open(os.path.join(ROOT, 'out', f), encoding='utf-8'))

cw   = L('crosswalk.json')
cap  = L('capability.json')
mr   = L('mine_refine.json')
usgs = L('usgs_outlook.json').get('materials', {})
pipe = L('pipeline.json').get('materials', {})
scen = {m['label']: m for m in L('scenario.json')['materials']}

# --- label alias: crosswalk key -> the key used in the other files ---
def norm(s): return s.lower().replace(' ', '').replace('(ndfeb)', '').replace('-', '')
def find(key, d):
    """resolve a crosswalk key against another file's keys, tolerant of naming drift."""
    if key in d: return d[key]
    nk = norm(key)
    for k in d:
        if norm(k) == nk: return d[k]
    # magnets <-> 'magnet (NdFeB)' style
    for k in d:
        if nk in norm(k) or norm(k) in nk: return d[k]
    return None

ISO2NAME = {}
for rows in cap.values():
    for r in rows:
        if r.get('iso'): ISO2NAME[r['iso']] = r.get('name', r['iso'])
# fill any ISO2 gaps (countries in USGS/scenario but not in capability) from the BACI table
try:
    import csv
    with _baci.country_file() as fh:
        for row in csv.DictReader(fh):
            iso, nm2 = row.get('country_iso2'), row.get('country_name')
            if iso and iso not in ISO2NAME and nm2 and '(' not in nm2:
                ISO2NAME[iso] = nm2
except Exception:
    pass

def headline(mat, caprows):
    """The chokepoint leader shown in the card. Prefer USGS refining/processing concentration
    where measured (repairs the shared-HS dilution, e.g. gallium's true ~87%); else the
    capability refined-share leader; else the scenario leader. Returns (iso, share%, stage_noun)."""
    u = find(mat, usgs) or {}
    if u.get('top') and u.get('top_share') is not None and u.get('stage') in ('refining', 'processing'):
        return (u['top'], round(u['top_share'], 1), 'refined')
    rows = sorted(caprows or [], key=lambda r: -r.get('ref_world_share', 0))
    if rows:
        return (rows[0]['iso'], round(100 * rows[0]['ref_world_share'], 1), 'refined')
    s = find(mat, scen) or {}
    return (s.get('leader'), s.get('lead_share'), 'supply')

def classify(mat, flags, lead_iso, lead_row):
    """Moat type + note, described for the ACTUAL headline leader (so note and headline never
    name different countries). lead_row is that country's capability record, or None."""
    name = ISO2NAME.get(lead_iso, lead_iso)
    if 'mine_only' in flags:
        return ('mine-side endowment',
                f'{name}’s dominance is geological — a mined commodity with no refining '
                'wedge. Diversification is exploration and off-take agreements, not new furnaces.')
    if lead_row and lead_row.get('feed_import', 0) >= 0.4 and lead_row.get('net_down', 0) >= 0.3:
        return ('import-fed capability',
                f'{name} IMPORTS the ore and EXPORTS the refined metal — the moat is the '
                'furnace, not the mine. Export controls on ore cannot touch it; only building '
                'refining capability elsewhere can.')
    if 'byproduct' in flags:
        return ('by-product capability',
                f'{name} extracts it as a by-product of a domestic host metal at a scale no one '
                'else recovers. There is no ore stream to redirect — substitution means new '
                'by-product recovery lines on someone else’s host.')
    if lead_row and lead_row.get('basis') == 'both' and lead_row.get('ore_world_share', 0) >= 0.15:
        return ('integrated (endowment+capability)',
                f'{name} both mines AND refines it — the one case where ore access is a real '
                'lever, alongside the refining capability.')
    return ('refining capability',
            f'{name} leads the refining stage; the concentration is in processing capacity, '
            'not the mine.')

def who_could(mat, lead_iso):
    """Prefer product-space capability-adjacency (density_exCN); else current alt-share."""
    m = find(mat, mr)
    if m and m.get('miners'):
        cand = [x for x in m['miners']
                if x['c'] != lead_iso and x.get('density_exCN') is not None]
        cand.sort(key=lambda x: -x['density_exCN'])
        out = [{'iso': x['c'], 'name': ISO2NAME.get(x['c'], x['c']),
                'score': round(x['density_exCN'], 3),
                'mines': x.get('mines'), 'refines': x.get('refines')} for x in cand[:5]]
        if out:
            return {'method': 'capability-adjacency', 'strong': True,
                    'desc': 'product-space density with the leader removed -- latent '
                            'capability to stand up refining, not just present output',
                    'candidates': out}
    u = find(mat, usgs)
    if u and u.get('by'):
        alt = [(k, v) for k, v in u['by'].items() if k != lead_iso]
        alt.sort(key=lambda kv: -kv[1])
        out = [{'iso': k, 'name': ISO2NAME.get(k, k), 'score': round(v, 1)} for k, v in alt[:5]]
        if out:
            return {'method': 'current-share', 'strong': False,
                    'desc': 'current alternative-supplier share (a WEAKER proxy: it shows '
                            'who already produces, not who could scale) -- no capability-'
                            'adjacency available for this code',
                    'candidates': out}
    s = find(mat, scen)
    if s and s.get('fallbacks'):
        out = [{'iso': f['iso'], 'name': f.get('name', ISO2NAME.get(f['iso'], f['iso'])),
                'score': f.get('export_share')}
               for f in s['fallbacks'][:6] if f['iso'] != lead_iso][:5]
        return {'method': 'current-share', 'strong': False,
                'desc': 'fallback exporters from the shock model (present output, not '
                        'latent capability)', 'candidates': out}
    return {'method': None, 'strong': False,
            'desc': 'no alternative-supplier signal in public data -- a genuine chokepoint '
                    'OR a sourcing gap', 'candidates': []}

def who_is(mat):
    p = find(mat, pipe)
    projects = (p or {}).get('projects', []) if isinstance(p, dict) else []
    u = find(mat, usgs) or {}
    fwd = None
    if u.get('world_2024') and u.get('world_2029'):
        fwd = {'from': u['world_2024'], 'to': u['world_2029'],
               'growth_pct': u.get('world_growth_pct'), 'stage': u.get('stage')}
    return {'projects': projects, 'forward': fwd,
            'iea': (p or {}).get('iea') if isinstance(p, dict) else None,
            'gap': not projects and not fwd}

records = []
for mat, meta in cw.items():
    flags = meta.get('flags', [])
    caprows = find(mat, cap)
    lead_iso, lead_share, stage_noun = headline(mat, caprows)
    if 'mine_only' in flags: stage_noun = 'total'   # no refining stage — "~X% of total supply"
    lead_row = next((r for r in (caprows or []) if r.get('iso') == lead_iso), None)
    moat_type, note = classify(mat, flags, lead_iso, lead_row)
    is_ = who_is(mat)
    s = find(mat, scen) or {}
    u = find(mat, usgs) or {}
    name = mat.replace('(NdFeB)', '').replace('(ndfeb)', '').strip().title()
    commodity = s.get('name')  # the HS commodity title (e.g. "Magnesium, unwrought")
    could = who_could(mat, lead_iso)
    # never let the leader appear among its own alternatives (leaders can differ by source)
    could['candidates'] = [c for c in could['candidates'] if c['iso'] != lead_iso]
    # distinguish a real sourcing gap from materials where buildout simply isn't the constraint:
    #   chokepoint = concentrated single-country lock, we lack buildout data (the true to-do)
    #   diffuse    = leader < 30% with fallbacks — not a single-country chokepoint
    #   endowment  = mine-side geology — diversification is exploration/off-take, not capacity
    if not is_['gap']:
        is_['gap_kind'] = None
    elif moat_type == 'mine-side endowment':
        is_['gap_kind'] = 'endowment'
    elif (lead_share or 0) < 30 and not s.get('spof'):
        is_['gap_kind'] = 'diffuse'
    else:
        is_['gap_kind'] = 'chokepoint'
    # verdict sentence
    top = could['candidates'][:2]
    who = ', '.join(c['name'] for c in top) if top else None
    seen = set(); bnames = []
    for p in is_['projects']:
        b = p['name'].split(' -- ')[0].split(' — ')[0].strip()
        if b not in seen: seen.add(b); bnames.append(b)
    build = ', '.join(bnames[:2]) if bnames else None
    if moat_type == 'mine-side endowment':
        verdict = note
    else:
        parts = []
        if lead_share: parts.append(f'{ISO2NAME.get(lead_iso, lead_iso)} holds ~{lead_share:.0f}% of {stage_noun} supply')
        if who: parts.append(('capability-adjacent alternatives' if could['strong']
                              else 'current alternatives') + f': {who}')
        else: parts.append('no clear alternative surfaced')
        if build: parts.append(f'being built: {build}')
        elif is_.get('forward'): parts.append('forward capacity tracked (USGS Outlook)')
        elif is_.get('gap_kind') == 'diffuse': parts.append('not a single-country chokepoint — buildout not the constraint')
        elif is_.get('gap_kind') == 'endowment': parts.append('mine-side endowment — exploration/off-take, not new capacity')
        elif is_.get('iea'): parts.append('no diversification pipeline — structural (see note)')
        else: parts.append('no diversification project tracked (sourcing gap)')
        verdict = '; '.join(parts) + '.'
    records.append({
        'label': mat, 'name': name, 'commodity': commodity, 'title_code': meta.get('title_code'),
        'flags': flags,
        'problem': {'leader': lead_iso, 'leader_name': ISO2NAME.get(lead_iso, lead_iso),
                    'leader_share': lead_share, 'stage_noun': stage_noun,
                    'moat_type': moat_type, 'moat_note': note,
                    'hhi': u.get('hhi') if u.get('stage') in ('refining', 'processing') else None,
                    'spof': s.get('spof', False),
                    'shared': s.get('shared', False)},
        'who_could': could, 'who_is': is_, 'verdict': verdict})

# rank: chokepoints with a real, actionable answer first; SPOF + high share to the top
def rank(r):
    return (-(r['problem'].get('leader_share') or 0), 0 if r['problem']['spof'] else 1)
records.sort(key=rank)

MOAT_ORDER = ['import-fed capability', 'by-product capability',
              'integrated (endowment+capability)', 'refining capability',
              'mine-side endowment']
summary = {'n': len(records),
           'by_moat': {m: sum(1 for r in records if r['problem']['moat_type'] == m) for m in MOAT_ORDER},
           'strong_alt': sum(1 for r in records if r['who_could']['strong']),
           'has_buildout': sum(1 for r in records if not r['who_is']['gap']),
           'chokepoint_gap': sum(1 for r in records if r['who_is'].get('gap_kind') == 'chokepoint'),
           'buildout_gap': sum(1 for r in records if r['who_is']['gap'])}

PAYLOAD = {'summary': summary, 'materials': records}
json.dump(PAYLOAD,
          open(os.path.join(ROOT, 'out', 'breakout.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)

# ---------------------------------------------------------------------------
# Self-contained page (data inlined, matches the site shell + assets/nav.js).
# ---------------------------------------------------------------------------
PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Break the chokepoint — Critical Materials Atlas</title>
<meta name="description" content="From finding to decision: for every critical-material chokepoint, which kind of moat holds it (import-fed vs by-product capability), who could realistically break it (product-space capability-adjacency), and who is actually building alternative capacity.">
<meta property="og:title" content="Break the chokepoint — the decision layer">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .sumstrip{display:flex;flex-wrap:wrap;gap:10px 14px;margin:1.1rem 0 .3rem}
 .sumstrip .s{border:1px solid var(--line);border-radius:10px;padding:9px 13px;background:var(--bg-soft);font-size:.78rem;color:var(--mut)}
 .sumstrip .s b{display:block;font-size:1.35rem;color:var(--navy);font-weight:800;font-variant-numeric:tabular-nums;line-height:1.1}
 .filterbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:1.1rem 0 .2rem}
 .filterbar .chip{font:inherit;font-size:.74rem;font-weight:600;cursor:pointer;border:1px solid var(--line);
   background:var(--bg);color:var(--ink-soft);border-radius:20px;padding:5px 12px;display:inline-flex;align-items:center;gap:6px}
 .filterbar .chip i{width:9px;height:9px;border-radius:50%;display:inline-block}
 .filterbar .chip.off{opacity:.38}
 .filterbar input[type=search]{font:inherit;font-size:.8rem;padding:6px 11px;border:1px solid var(--line);border-radius:8px;min-width:180px;flex:1;max-width:280px}
 .bgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(370px,1fr));gap:18px;margin:1rem 0}
 .bcard{border:1px solid var(--line);border-radius:13px;padding:15px 17px 16px;background:var(--bg);display:flex;flex-direction:column;gap:11px}
 .bcard h3{font-size:1.05rem;margin:0;display:flex;justify-content:space-between;align-items:baseline;gap:8px}
 .bcard h3 .hs{font-size:.64rem;color:var(--faint);font-weight:600;letter-spacing:.2px;white-space:nowrap}
 .bcard .commodity{font-size:.68rem;color:var(--faint);margin:-8px 0 0}
 .sec{border-top:1px solid var(--bg-soft);padding-top:9px}
 .sec .lbl{font-size:.62rem;text-transform:uppercase;letter-spacing:.09em;font-weight:700;color:var(--faint);margin:0 0 5px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
 .moat{font-size:.62rem;font-weight:700;letter-spacing:.02em;padding:2px 8px;border-radius:20px;color:#fff;text-transform:none}
 .m-import{background:#0072B2}.m-byproduct{background:#B8860B}.m-integrated{background:#009E73}
 .m-refining{background:#56607a}.m-endow{background:#8a94a0}
 .spofb{font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.03em;color:#fff;background:#b4291f;padding:2px 8px;border-radius:20px}
 .leadline{font-size:.92rem;color:var(--ink);margin:0 0 5px}.leadline b{color:var(--navy);font-weight:800}
 .leadline .hhi{font-size:.72rem;color:var(--mut);font-weight:500}
 .moatnote{font-size:.76rem;color:var(--mut);line-height:1.4;margin:0}
 .crow{display:flex;align-items:center;gap:8px;margin:4px 0;font-size:.76rem}
 .crow .cw{width:120px;flex:0 0 120px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--ink-soft)}
 .crow .ct{flex:1;height:13px;background:var(--bg-soft);border-radius:4px;overflow:hidden}
 .crow .cf{display:block;height:100%;border-radius:4px}
 .crow .cv{width:52px;flex:0 0 52px;text-align:right;font-variant-numeric:tabular-nums;color:var(--mut);font-size:.7rem}
 .method{font-size:.6rem;font-weight:700;padding:2px 7px;border-radius:5px;text-transform:none;letter-spacing:0}
 .method.strong{background:#e2f0ec;color:#0b6f66}.method.weak{background:#eef0f3;color:#6b7681}
 .mdesc{font-size:.68rem;color:var(--faint);line-height:1.35;margin:6px 0 0;font-style:italic}
 .proj{font-size:.77rem;color:var(--ink-soft);margin:3px 0;display:flex;gap:6px;align-items:baseline}
 .proj .pf{flex:0 0 auto}.proj .ps{color:var(--faint);font-size:.68rem}
 .fwd{font-size:.72rem;color:var(--mut);margin:5px 0 0}
 .gap{font-size:.75rem;color:#a5641a;background:#fdf4e7;border:1px solid #f0dcc0;border-radius:7px;padding:6px 9px;margin:2px 0 0}
 .softgap{font-size:.73rem;color:var(--mut);background:var(--bg-soft);border:1px solid var(--line);border-radius:7px;padding:6px 9px;margin:2px 0 0;font-style:italic}
 .verdict{font-size:.82rem;color:var(--ink);line-height:1.45;background:var(--bg-soft);border-radius:9px;padding:9px 12px;margin-top:2px}
 .verdict b{color:var(--navy)}
 .empty{color:var(--faint);font-style:italic;padding:2rem;text-align:center}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · from finding to decision</div>
  <h1>Break the chokepoint</h1>
  <p class="deck">Knowing that <b>China refines what it doesn&rsquo;t mine</b> is only half an answer &mdash; the reader&rsquo;s next question is <i>so what do I do about it?</i> This page turns each chokepoint into a decision. For every critical material it asks three things in order: <b>what kind of moat</b> holds the chokepoint (because the moat type decides what can work) &mdash; <i>import-fed</i> capability that no ore embargo can touch, a <i>by-product</i> lock with no ore stream to redirect, or a genuine <i>endowment</i>; <b>who could realistically break it</b>, ranked by product-space capability-adjacency with the leader removed; and <b>who is actually building</b> the alternative. The gap between <i>could</i> and <i>is</i> is the vulnerability &mdash; and the to-do list.</p>
</div></section>
<article style="max-width:1180px">
  <div class="callout"><b>Why the moat type is the first question.</b> A chokepoint is not a chokepoint is not a chokepoint. If a leader <i>imports the ore and exports the refined metal</i> (Japan&rsquo;s titanium sponge, Indonesia&rsquo;s nickel, China&rsquo;s tungsten), the moat is the <b>furnace</b> &mdash; tariffs or export controls on ore are useless; only new refining capability elsewhere breaks it. If the leader extracts the metal as a <i>by-product</i> of a domestic host it already controls (China&rsquo;s gallium from its own alumina, germanium from zinc), there is <b>no ore stream to redirect at all</b> &mdash; substitution means standing up new by-product recovery on someone else&rsquo;s host metal. Only where a leader genuinely <i>mines and refines</i> its own resource does ore access become a real lever. Same 87% share, three completely different answers.
  <details class="howto"><summary>How &ldquo;who could&rdquo; is measured &amp; caveats</summary>
  <p><b>Who could break it</b> uses two signals, always labelled so they are never confused. The <b>strong</b> one (<span style="color:#0b6f66;font-weight:600">capability-adjacency</span>) is the product-space <i>density</i> of each country to the refined product <i>with the leader removed</i> &mdash; latent capability to stand the stage up, not merely present output. It exists only for the <b>8 clean ore&rarr;refined HS pairs</b>. For the rest we fall back to the <span style="color:#6b7681;font-weight:600">current alternative-supplier share</span> &mdash; a <i>weaker</i> proxy (who already produces, which is not who could scale). <b>Who is building</b> is announced public projects (Lynas, MP Materials, Iluka, Rio Tinto Rincón, Umicore…) plus USGS forward capacity to 2029; it is <i>curated, not exhaustive</i>, so a blank is a <b>sourcing gap</b> &mdash; shown blank, not read as &ldquo;no one&rdquo;.</p>
  <p class="howto-src"><b>Caveats.</b> Refined-share leaders are <i>export-based</i>, so a giant that refines huge volumes but <b>consumes them at home</b> is understated &mdash; cobalt shows Finland, not China, for exactly this reason (China&rsquo;s refined cobalt stays in China). Where the USGS Outlook measures refining concentration directly (gallium, magnesium, titanium…) we use its share instead, which repairs the shared-code dilution (gallium reads its true ~87%, not the 811292-diluted figure). The moat <i>type</i> comes from the trade feedstock signature + the HS-code provenance flags; the <i>share</i> from USGS where available else the capability layer. Built by <code>build_breakout.py</code> from <code>capability.json</code>, <code>mine_refine.json</code>, <code>usgs_outlook.json</code>, <code>pipeline.json</code> and <code>scenario.json</code>. <b>See also</b> <a href="ot.html">the reallocation stress test</a> (can the rest actually cover a cut, in tonnage — and does removal just shift the chokepoint?), <a href="leverage.html">the leverage map</a> (how exposed is each importing country), <a href="refiners.html">Who actually refines</a>, <a href="product-space.html">the product-space map</a>, and <a href="scenarios.html">shock scenarios</a>.</p>
  </details></div>

  <div class="sumstrip" id="sum"></div>
  <div class="filterbar" id="filters"></div>
  <div class="bgrid" id="grid"></div>
</article>
<script>
const D = __DATA__;
function flag(iso){ if(!iso||iso.length!==2) return ''; return iso.toUpperCase().replace(/./g,c=>String.fromCodePoint(0x1F1E6-65+c.charCodeAt(0)))+' '; }
const MOAT = {
  'import-fed capability':{c:'m-import',k:'import-fed'},
  'by-product capability':{c:'m-byproduct',k:'by-product'},
  'integrated (endowment+capability)':{c:'m-integrated',k:'integrated'},
  'refining capability':{c:'m-refining',k:'refining'},
  'mine-side endowment':{c:'m-endow',k:'endowment'}};
function nm(iso,name){ return (flag(iso)+ (name||iso)).trim(); }

// summary strip
const S=D.summary, sum=document.getElementById('sum');
sum.innerHTML =
  `<div class="s"><b>${S.n}</b>critical materials</div>`+
  `<div class="s"><b>${S.by_moat['import-fed capability']+S.by_moat['by-product capability']}</b>capability moats<br><span style="font-size:.68rem">(furnace / by-product, no ore lever)</span></div>`+
  `<div class="s"><b>${S.strong_alt}</b>with a capability-adjacent<br>alternative (product-space)</div>`+
  `<div class="s"><b>${S.has_buildout}</b>with tracked buildout<br><span style="font-size:.68rem">projects underway</span></div>`+
  `<div class="s"><b>${S.chokepoint_gap}</b>chokepoints with no<br>tracked buildout <span style="font-size:.68rem">&mdash; the to-do</span></div>`;

// filter chips
const active=new Set(Object.keys(MOAT));
const fb=document.getElementById('filters');
Object.entries(MOAT).forEach(([full,info])=>{
  const b=document.createElement('button'); b.className='chip'; b.dataset.moat=full;
  const swatch={'m-import':'#0072B2','m-byproduct':'#B8860B','m-integrated':'#009E73','m-refining':'#56607a','m-endow':'#8a94a0'}[info.c];
  b.innerHTML=`<i style="background:${swatch}"></i>${info.k} <span style="color:var(--faint);font-weight:500">${S.by_moat[full]}</span>`;
  b.onclick=()=>{ if(active.has(full)){active.delete(full);b.classList.add('off');} else {active.add(full);b.classList.remove('off');} render(); };
  fb.appendChild(b);
});
const srch=document.createElement('input'); srch.type='search'; srch.placeholder='search material or country…';
srch.oninput=render; fb.appendChild(srch);

function gapMsg(kind){
  if(kind==='diffuse') return `<div class="softgap">Not a single-country chokepoint (leader &lt;30% with fallback suppliers) — buildout is not the binding constraint here.</div>`;
  if(kind==='endowment') return `<div class="softgap">Mine-side endowment — the answer is exploration &amp; off-take agreements, not new processing capacity.</div>`;
  return `<div class="gap">No public diversification project tracked for this concentrated stage — either a real sourcing gap, or a supplier the market hasn&rsquo;t moved to replace (e.g. a well-supplied ally).</div>`;
}
function bar(width,color){ return `<span class="cf" style="width:${Math.max(3,Math.min(100,width))}%;background:${color}"></span>`; }
function card(r){
  const p=r.problem, mo=MOAT[p.moat_type]||MOAT['refining capability'];
  const spof = p.spof?`<span class="spofb">single point</span>`:'';
  const hhi = p.hhi!=null?`<span class="hhi"> · HHI ${p.hhi.toFixed(2)}</span>`:'';
  // who could
  const cc=r.who_could, strong=cc.strong;
  let could='';
  if(cc.candidates.length){
    const mx = strong ? Math.max(...cc.candidates.map(c=>c.score||0),0.001)
                      : Math.max(...cc.candidates.map(c=>c.score||0),1);
    could = cc.candidates.map(c=>{
      const w = strong ? (c.score/mx)*100 : (c.score/mx)*100;
      const val = strong ? (c.score!=null?c.score.toFixed(2):'') : (c.score!=null?c.score.toFixed(0)+'%':'');
      return `<div class="crow"><span class="cw">${nm(c.iso,c.name)}</span><span class="ct">${bar(w,strong?'#0b6f66':'#8a94a0')}</span><span class="cv">${val}</span></div>`;
    }).join('');
  } else could = `<div class="mdesc">no alternative surfaced in public data — a hard chokepoint or a sourcing gap.</div>`;
  // who is
  const wi=r.who_is; let is='';
  if(wi.projects && wi.projects.length){
    is = wi.projects.slice(0,4).map(pr=>`<div class="proj"><span class="pf">${flag(pr.iso)}</span><span><b>${pr.name}</b> <span class="ps">${pr.stage||''}${pr.status?' · '+pr.status:''}</span></span></div>`).join('');
  }
  if(wi.forward){ is += `<div class="fwd">USGS capacity ${wi.forward.stage||''}: ${wi.forward.from}&rarr;${wi.forward.to} kt by 2029 (${wi.forward.growth_pct>=0?'+':''}${wi.forward.growth_pct}%)</div>`; }
  if(wi.gap && !is){ is = gapMsg(wi.gap_kind); }
  return `<div class="bcard" data-moat="${p.moat_type}" data-txt="${(r.name+' '+(r.commodity||'')+' '+p.leader_name+' '+cc.candidates.map(c=>c.name).join(' ')).toLowerCase()}">
    <h3><span>${r.name}</span><span class="hs">${r.title_code||''} · ${(r.flags||[]).join('/')||'—'}</span></h3>
    ${r.commodity?`<div class="commodity">${r.commodity}</div>`:''}
    <div class="sec">
      <div class="lbl">The chokepoint <span class="moat ${mo.c}">${mo.k} capability</span>${spof}</div>
      <div class="leadline">${flag(p.leader)}<b>${p.leader_name}</b> ~${p.leader_share!=null?p.leader_share.toFixed(0):'?'}% of ${p.stage_noun||'refined'} supply${hhi}</div>
      <div class="moatnote">${p.moat_note}</div>
    </div>
    <div class="sec">
      <div class="lbl">Who could break it <span class="method ${strong?'strong':'weak'}">${strong?'capability-adjacency':'current share (weak proxy)'}</span></div>
      ${could}
      <div class="mdesc">${cc.desc}</div>
    </div>
    <div class="sec">
      <div class="lbl">Who is building it</div>
      ${is || (wi.iea ? `<div class="softgap">${wi.iea}</div>` : gapMsg(wi.gap_kind))}
    </div>
    <div class="verdict">${r.verdict}</div>
  </div>`;
}
function render(){
  const q=(srch.value||'').trim().toLowerCase();
  const rows=D.materials.filter(r=>active.has(r.problem.moat_type) && (!q || (r.name+' '+(r.commodity||'')+' '+r.problem.leader_name+' '+r.who_could.candidates.map(c=>c.name).join(' ')).toLowerCase().includes(q)));
  const g=document.getElementById('grid');
  g.innerHTML = rows.length ? rows.map(card).join('') : `<div class="empty">No materials match — widen the filters or clear the search.</div>`;
}
render();
</script>
</body></html>'''
PAGE = PAGE.replace('__DATA__', json.dumps(PAYLOAD, ensure_ascii=False))
open(os.path.join(ROOT, 'breakout.html'), 'w', encoding='utf-8').write(PAGE)
print('WROTE breakout.html (self-contained)')

print(f"=== Break the chokepoint: {len(records)} materials ===")
print('moat mix:', summary['by_moat'])
print(f"strong (capability-adjacency) alternatives: {summary['strong_alt']}/{len(records)}  |  "
      f"buildout sourcing-gaps: {summary['buildout_gap']}/{len(records)}")
print('\ntop chokepoints by refined share:')
for r in records[:12]:
    p = r['problem']
    print(f"  {r['name'][:16]:16} {str(p['leader'] or '?'):3} "
          f"{('%.0f%%' % p['leader_share']) if p['leader_share'] else '  ?':>4} "
          f"{p['moat_type'][:26]:26} alt:{r['who_could']['method'] or '-':<20} "
          f"{'BUILD' if not r['who_is']['gap'] else 'gap'}")
print('\nWROTE out/breakout.json')
