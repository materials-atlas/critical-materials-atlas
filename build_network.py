#!/usr/bin/env python3
"""
Trade-network centrality — the supply chokepoints that concentration (HHI) misses.

Top-exporter share and the export Herfindahl measure how CONCENTRATED a material's trade is. They are
blind to network POSITION: a country can carry a modest export share yet sit on the routes everyone else
depends on. This module builds, per material, the directed weighted trade network (reconciled bilateral
flows) and computes:

  out_share   export share    (out-strength share)        — the classic concentration view, for contrast
  pagerank    flow importance (weighted by trade value)   — recursive centrality in the whole flow
  between     brokerage       (weighted by 1/value dist)  — who sits on the routes between clusters
  through     throughput      ((in+out strength)/2 share) — how much of all trade in the material touches it

Per the supply-chain-network literature (e.g. tungsten / rare-earth / PV trade-network studies), a TRUE
chokepoint is high network centrality CORROBORATED by the bottleneck stage (refining), and validated by a
node-removal fragmentation test — not betweenness alone (which also catches big importers and entrepots).
So each material's top broker is classified:
  processing chokepoint  broker is also the top refiner (network confirms refining control)
  exporter chokepoint    broker is also the top exporter (resource + network aligned)
  redistribution hub     big importer/re-distributor, not the refiner
  transit hub            curated entrepot (HK/SG/NL/AE/BE...) — re-export, not control
and we report how far the network fragments when that one node is removed.

Writes out/network.json + network.html.  Public data only; deterministic; reproducible.
"""
import json, os, html, glob
import networkx as nx

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = os.environ.get('PROFILE_YEAR', '2024')
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
NAMES = flows.get('names', {})
MAT = {m['label']: m for m in data['materials']}
TITLES = {m['label']: m['title'].split(' (')[0] for m in data['materials']}
HUBS = {'HK', 'SG', 'AE', 'PA', 'MO', 'GI', 'NL', 'BE'}   # entrepot / re-export hubs: brokerage = transit
SHARED = {'gallium', 'germanium'}

def cname(i): return NAMES.get(i, i)
def e(s): return html.escape(str(s), quote=True)
def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(c.upper()) - 65) for c in iso)

def build_graph(label):
    G = nx.DiGraph()
    for f in flows.get('materials', {}).get(label) or []:
        u, v, w = f['from'], f['to'], float(f['value'])
        if w <= 0 or u == v:
            continue
        if G.has_edge(u, v):
            G[u][v]['value'] += w
        else:
            G.add_edge(u, v, value=w)
    for _, _, d in G.edges(data=True):
        d['dist'] = 1.0 / d['value']
    return G

def china_centrality(flowsdict, label):
    """China's PageRank, betweenness and throughput-share in one material-year network."""
    G = nx.DiGraph()
    for f in flowsdict.get('materials', {}).get(label) or []:
        u, v, w = f['from'], f['to'], float(f['value'])
        if w <= 0 or u == v:
            continue
        if G.has_edge(u, v):
            G[u][v]['value'] += w
        else:
            G.add_edge(u, v, value=w)
    if G.number_of_edges() < 3 or 'CN' not in G:
        return {'pr': 0.0, 'bet': 0.0, 'through': 0.0}
    for _, _, d in G.edges(data=True):
        d['dist'] = 1.0 / d['value']
    pr = nx.pagerank(G, weight='value')
    bet = nx.betweenness_centrality(G, weight='dist', normalized=True)
    ins = outs = tot = 0.0
    for u, v, d in G.edges(data=True):
        if u == 'CN': outs += d['value']
        if v == 'CN': ins += d['value']
        tot += d['value']
    return {'pr': round(pr.get('CN', 0.0), 3), 'bet': round(bet.get('CN', 0.0), 3),
            'through': round((ins + outs) / (2 * tot) * 100, 1) if tot else 0.0}

def reach_pairs(G):
    """ordered (u,v) pairs with a directed path — a supply-can-reach-demand count."""
    return sum(len(nx.descendants(G, n)) for n in G)

def classify(c, label, te):
    if c in HUBS:
        return 'transit hub'
    refined = MAT[label].get('refined') or []
    top_ref = refined[0]['c'] if refined else None
    if top_ref and c == top_ref:
        return 'processing chokepoint'
    if c == te:
        return 'exporter chokepoint'
    return 'redistribution hub'

def analyse(label):
    G = build_graph(label)
    if G.number_of_edges() < 4 or G.number_of_nodes() < 4:
        return None
    pr = nx.pagerank(G, weight='value')
    bet = nx.betweenness_centrality(G, weight='dist', normalized=True)
    ins, outs, tot = {n: 0.0 for n in G}, {n: 0.0 for n in G}, 0.0
    for u, v, d in G.edges(data=True):
        outs[u] += d['value']; ins[v] += d['value']; tot += d['value']
    share = {n: (outs[n] / tot * 100 if tot else 0.0) for n in G}
    through = {n: ((ins[n] + outs[n]) / (2 * tot) * 100 if tot else 0.0) for n in G}

    def top(d, k=1): return sorted(d, key=d.get, reverse=True)[:k]
    te, tb, tp = top(share)[0], top(bet)[0], top(pr)[0]

    # fragmentation: how many reachable supply->demand pairs vanish when the top broker is removed
    frag = None
    if G.number_of_nodes() <= 240:
        base = reach_pairs(G)
        if base:
            H = G.copy(); H.remove_node(tb)
            frag = round((1 - reach_pairs(H) / base) * 100, 1)

    return {
        'label': label, 'title': TITLES.get(label, label), 'shared': label in SHARED,
        'nodes': G.number_of_nodes(), 'edges': G.number_of_edges(),
        'top_exporter': {'c': te, 'share': round(share[te], 1)},
        'chokepoint': {'c': tb, 'bet': round(bet[tb], 3), 'through': round(through[tb], 1),
                       'exp_share': round(share.get(tb, 0), 1), 'kind': classify(tb, label, te),
                       'is_hub': tb in HUBS, 'frag': frag},
        'top_flow': {'c': tp, 'pr': round(pr[tp], 3)},
        'brokers': [{'c': n, 'bet': round(bet[n], 3), 'through': round(through[n], 1),
                     'is_hub': n in HUBS} for n in top(bet, 5)],
    }

KINDCOL = {'processing chokepoint': '#c0392b', 'exporter chokepoint': '#0e7c74',
           'redistribution hub': '#b35e16', 'transit hub': '#9aa6ad'}

def main():
    rows = [r for r in (analyse(m['label']) for m in data['materials']) if r]
    rows.sort(key=lambda r: r['chokepoint']['bet'], reverse=True)

    # cross-material "systemic broker" tally: weighted top-3 brokerage appearances (3/2/1)
    sys_b, sys_exp = {}, {}
    for r in rows:
        for i, b in enumerate(r['brokers'][:3]):
            sys_b[b['c']] = sys_b.get(b['c'], 0) + (3 - i)
        sys_exp[r['top_exporter']['c']] = sys_exp.get(r['top_exporter']['c'], 0) + 1
    systemic = sorted(
        ({'c': c, 'name': cname(c), 'broker_score': s, 'export_lead': sys_exp.get(c, 0),
          'is_hub': c in HUBS} for c, s in sys_b.items()),
        key=lambda x: x['broker_score'], reverse=True)[:12]

    n_proc = sum(1 for r in rows if r['chokepoint']['kind'] == 'processing chokepoint')

    # temporal: China's network centrality across the measured 2002-2024 series
    tflows = {}
    for p in glob.glob(os.path.join(ROOT, 'out', 'flows_20*.json')):
        fd = json.load(open(p, encoding='utf8'))
        if fd.get('provisional') or fd.get('nowcast_kind'):
            continue
        tflows[int(os.path.basename(p)[6:10])] = fd
    tyears = sorted(tflows)
    tmats = {}
    for m in data['materials']:
        lab = m['label']
        cc = [china_centrality(tflows[y], lab) for y in tyears]
        tmats[lab] = {'pr': [c['pr'] for c in cc], 'bet': [c['bet'] for c in cc], 'through': [c['through'] for c in cc]}
    nm = len(tmats) or 1
    cn_through = [round(sum(tmats[l]['through'][i] for l in tmats) / nm, 1) for i in range(len(tyears))]
    cn_pr = [round(sum(tmats[l]['pr'][i] for l in tmats) / nm, 3) for i in range(len(tyears))]
    temporal = {'years': tyears, 'cn_through_index': cn_through, 'cn_pr_index': cn_pr, 'materials': tmats}

    json.dump({'year': YEAR,
               'method': 'directed weighted trade network; pagerank(value), betweenness(1/value), node-removal fragmentation',
               'materials': rows, 'systemic': systemic, 'n_processing': n_proc, 'temporal': temporal},
              open(os.path.join(ROOT, 'out', 'network.json'), 'w', encoding='utf8'), indent=1)
    print(f"China network-throughput index: {cn_through[0]:.0f}% ({tyears[0]}) -> {cn_through[-1]:.0f}% ({tyears[-1]})")

    # ---- page ----
    motif = ('<svg class="hero-motif" viewBox="0 0 560 560" fill="none" aria-hidden="true"><g stroke="#7fd2c8" stroke-opacity=".15" stroke-width="1.1"><circle cx="280" cy="280" r="232"/><ellipse cx="280" cy="280" rx="232" ry="62"/><ellipse cx="280" cy="280" rx="232" ry="132"/><ellipse cx="280" cy="280" rx="232" ry="196"/><ellipse cx="280" cy="280" rx="62" ry="232"/><ellipse cx="280" cy="280" rx="132" ry="232"/><ellipse cx="280" cy="280" rx="196" ry="232"/><line x1="280" y1="48" x2="280" y2="512"/><line x1="48" y1="280" x2="512" y2="280"/></g><g stroke="#9be3da" stroke-opacity=".26" stroke-width="1.4" fill="none"><path d="M120 360 Q 300 110 472 248"/><path d="M158 196 Q 322 300 442 422"/><path d="M120 360 Q 268 430 442 422"/></g><g fill="#bff0e8" fill-opacity=".55"><circle cx="120" cy="360" r="4.2"/><circle cx="472" cy="248" r="4.2"/><circle cx="158" cy="196" r="4.2"/><circle cx="442" cy="422" r="4.2"/></g></svg>')

    HUBSPAN = ' <span style="color:#9aa6ad;font-size:.78rem">entrepot hub</span>'
    srows = []
    for i, s in enumerate(systemic, 1):
        hub = HUBSPAN if s['is_hub'] else ''
        srows.append(
            f'<tr><td class="n" style="color:#9aa6ad">{i}</td>'
            f'<td>{flag(s["c"])} {e(s["name"])}{hub}</td>'
            f'<td class="n" style="font-weight:800;color:#15323a">{s["broker_score"]}</td>'
            f'<td class="n" style="color:#0e7c74">{s["export_lead"]}</td></tr>')
    sysrows = ''.join(srows)

    matrows = []
    for r in rows:
        cp, te = r['chokepoint'], r['top_exporter']
        kc = KINDCOL.get(cp['kind'], '#9aa6ad')
        same = cp['c'] == te['c']
        fragtxt = f'{cp["frag"]:.0f}%' if cp['frag'] is not None else '—'
        matrows.append(
            f'<tr><td><a href="profile-{e(r["label"])}.html">{e(r["title"])}</a>{" ⛓" if r["shared"] else ""}</td>'
            f'<td>{flag(te["c"])} {e(cname(te["c"]))} <span style="color:#9aa6ad">{te["share"]:.0f}%</span></td>'
            f'<td>{flag(cp["c"])} {e(cname(cp["c"]))} '
            f'<span style="color:#9aa6ad">{cp["exp_share"]:.0f}% exp · {cp["through"]:.0f}% through</span></td>'
            f'<td style="color:{kc};font-weight:600;font-size:.82rem">{e(cp["kind"])}</td>'
            f'<td class="n" title="share of supply→demand routes that break if this node is removed">{fragtxt}</td></tr>')

    out = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trade-network chokepoints — Critical Materials Atlas</title>
<meta name="description" content="The supply chokepoints that concentration misses: a directed-network analysis of who controls the trade routes for 32 critical materials — brokers, processing hubs and re-export transit, validated by a node-removal fragmentation test.">
<meta property="og:title" content="Trade-network chokepoints">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="findings.html">Findings</a>
  <a href="risk.html" class="hideable">Risk</a><a href="profiles.html" class="hideable">Profiles</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero">{motif}<div class="wrap">
  <div class="eyebrow">Method · network position</div>
  <h1>The trade routes concentration misses</h1>
  <p class="deck">Top-exporter share tells you how <i>concentrated</i> a material's trade is. It says nothing about who sits <i>on the routes</i>. Treating each material's bilateral flows as a directed network surfaces the brokers and processing hubs that the customs ledger hides — and a node-removal test shows how far the network fragments without them.</p>
</div></section>
<article style="max-width:1000px">
  <div class="callout">A country can hold a small export share yet be the node everything routes through. This finds those brokers and processing hubs &mdash; and tests how much of the trade breaks without them.
  <details class="howto"><summary>How it&rsquo;s built, and how to read it</summary>
  <p>I build each material&rsquo;s directed, value-weighted trade network and rank countries by <b>betweenness</b> (brokerage) and <b>PageRank</b> (recursive flow importance), then classify the top broker against the refining stage: a <span style="color:{KINDCOL['processing chokepoint']}">processing chokepoint</span> is also the top refiner (centrality coincides with refining dominance), a <span style="color:{KINDCOL['redistribution hub']}">redistribution hub</span> is a big importer that re-distributes, a <span style="color:{KINDCOL['transit hub']}">transit hub</span> is a curated entrepot (re-export, not control). The last column is a resilience test: the share of supply→demand routes that break when that single node is removed.</p>
  <p class="howto-src"><b>Read with care:</b> betweenness on a trade network also reflects import <i>size</i> — a big buyer scores high without &ldquo;controlling&rdquo; anything — so treat this as <b>trade-routing centrality</b> (exploratory), and &ldquo;processing chokepoint&rdquo; as &ldquo;most-central <i>and</i> the top refiner&rdquo;, not proof of control. Computed by <code>build_network.py</code>.</p>
  </details></div>

  <h2 style="margin:1.6rem 0 .5rem">Who sits on the trade routes</h2>
  <p class="note" style="margin-top:0">Weighted tally of top-3 brokerage appearances across all {len(rows)} materials, beside how many each <i>leads as exporter</i>. The gap is the point: the most-central nodes are processing and redistribution hubs, not the resource-rich exporters.</p>
  <table style="max-width:560px">
    <thead><tr><th class="n">#</th><th>Country</th><th class="n" title="weighted top-3 brokerage appearances (3/2/1)">broker score</th><th class="n" title="materials it is the top exporter of">exports #1</th></tr></thead>
    <tbody>{sysrows}</tbody>
  </table>

  <h2 style="margin:2rem 0 .5rem">Per material — exporter vs network chokepoint</h2>
  <table>
    <thead><tr><th>Material</th><th>Top exporter</th><th>Network chokepoint</th><th>type</th><th class="n" title="% of supply→demand routes lost if the chokepoint node is removed">fragility</th></tr></thead>
    <tbody>{''.join(matrows)}</tbody>
  </table>
  <p class="note">{n_proc} of {len(rows)} materials have a <b>processing chokepoint</b> — a network broker that is also the dominant refiner. ⛓ gallium and germanium share one HS6 code (811292; hafnium is separate). Computed from <a href="out/flows_{YEAR}.json">flows_{YEAR}.json</a> → <a href="out/network.json">network.json</a>.</p>

  <h2 style="margin:2rem 0 .5rem">China's network centrality over time</h2>
  <p class="note" style="margin-top:0">Network centrality captures China as the processing/redistribution <i>hub</i> — importer <i>and</i> broker, not just exporter — so it rises even where China barely exports (it imports the ore). Bold = China's average throughput share across all 32 materials; thin lines = materials where China is the processing hub. Throughput = share of a material's trade value touching China. Measured 2002–2024; same trade-routing-centrality caveat as above.</p>
  <div style="background:#fff;border:1px solid #e3e9e8;border-radius:10px;padding:1rem .8rem .4rem;margin:.6rem 0"><div id="cnchart" style="width:100%;height:400px"></div></div>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="./">Interactive atlas</a><br><a href="findings.html">The origin gap</a><br><a href="risk.html">Supply-risk index</a><br><a href="scenarios.html">Supply-shock scenarios</a></div>
  <div><h4>Sources</h4>UN Comtrade · CEPII BACI<br>USGS · IEA · World Bank</div>
  <div class="fineprint">Network position is one lens; betweenness on a trade network also reflects import size. Method documented.</div>
</div></footer>
</body></html>'''
    _netjs = """<script>
fetch('out/network.json').then(r=>r.json()).then(N=>{
  const T=N.temporal; if(!T||!T.years) return;
  const COL=['#15323a','#c77f0a','#6d5fb0','#b4532b','#3f9b46','#0e7c74'];
  const NM={bauxite:'Bauxite',lithium:'Lithium carbonate',graphite:'Natural graphite',manganese:'Manganese ore',cobalt:'Cobalt'};
  const KEY=Object.keys(NM).filter(k=>T.materials[k]);
  const c=echarts.init(document.getElementById('cnchart'));
  c.setOption({
    tooltip:{trigger:'axis',valueFormatter:v=>v==null?'':v.toFixed(0)+'%'},
    legend:{top:0,type:'scroll'},
    grid:{left:48,right:20,top:34,bottom:30},
    xAxis:{type:'category',data:T.years,boundaryGap:false},
    yAxis:{type:'value',name:'China throughput %',min:0,axisLabel:{formatter:'{value}%'}},
    series:[{name:'avg (all 32)',type:'line',smooth:true,showSymbol:false,lineWidth:3.4,data:T.cn_through_index,itemStyle:{color:'#15323a'}}].concat(
      KEY.map((k,i)=>({name:NM[k],type:'line',smooth:true,showSymbol:false,lineWidth:1.8,data:T.materials[k].through,itemStyle:{color:COL[(i+1)%6]}})))
  });
  window.addEventListener('resize',()=>c.resize());
});
</script>
"""
    out = out.replace('</body></html>', _netjs + '</body></html>')
    open(os.path.join(ROOT, 'network.html'), 'w', encoding='utf8', newline='\n').write(out)

    print(f'wrote network.html + out/network.json — {len(rows)} materials, {n_proc} processing chokepoints')
    print('\nSYSTEMIC BROKERS (weighted top-3 brokerage):')
    for s in systemic[:8]:
        tag = ' [entrepot]' if s['is_hub'] else ''
        print(f"  {s['name']:<22} broker {s['broker_score']:>2}  exports#1 in {s['export_lead']}{tag}")
    print('\nPROCESSING CHOKEPOINTS (broker == top refiner):')
    for r in rows:
        cp = r['chokepoint']
        if cp['kind'] == 'processing chokepoint':
            fr = f"{cp['frag']:.0f}% fragility" if cp['frag'] is not None else ''
            print(f"  {r['title']:<22} {cp['c']} ({cp['through']:.0f}% throughput, exports only {cp['exp_share']:.0f}%)  {fr}")

if __name__ == '__main__':
    main()
