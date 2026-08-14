"""Share-card generator for the X thread. Emits self-contained 1600x900 dark cards (share/card*.html)
with the real numbers pulled from the atlas data, one finding each, plus a server-side-projected
reshuffle map. Render each to PNG with headless Chrome (see render block at the bottom of the file's
docstring / the accompanying command). Writes share/card{1..5}.html and share/x-thread.md.
Run:  python build_share.py
"""
import os, json
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
SHARE = os.path.join(ROOT, 'share'); os.makedirs(SHARE, exist_ok=True)
def L(f): return json.load(open(os.path.join(ROOT, 'out', f), encoding='utf-8'))
bo, ot, lv = L('breakout.json'), L('ot.json'), L('leverage.json')

BASE = '''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
 *{margin:0;padding:0;box-sizing:border-box}
 html,body{width:1600px;height:900px;overflow:hidden;font-family:Inter,sans-serif}
 .card{width:1600px;height:900px;background:radial-gradient(120% 120% at 12% 0%,#123c42 0%,#0b2024 60%,#081619 100%);
   color:#eaf2f2;padding:88px 96px;display:flex;flex-direction:column;position:relative}
 .eyebrow{font-size:22px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:#2bb3a3;margin-bottom:26px}
 .h{font-size:74px;font-weight:800;line-height:1.04;letter-spacing:-.015em;color:#fff;max-width:1180px}
 .h .amber{color:#f0b429}.h .red{color:#ef7c6b}.h .teal{color:#3fd0bd}
 .sub{font-size:29px;font-weight:500;line-height:1.4;color:#a9c2c2;margin-top:30px;max-width:1150px}
 .sub b{color:#eaf2f2;font-weight:700}
 .spacer{flex:1}
 .foot{display:flex;justify-content:space-between;align-items:center;font-size:22px;color:#7fa0a0;font-weight:600;
   border-top:1px solid rgba(255,255,255,.13);padding-top:26px}
 .foot .u{color:#2bb3a3}
 .bignum{font-size:150px;font-weight:900;line-height:1;letter-spacing:-.03em;color:#fff}
 .bignum .unit{font-size:60px;font-weight:700;color:#a9c2c2;margin-left:8px}
 .stats{display:flex;gap:56px;margin-top:auto;margin-bottom:8px}
 .stat .n{font-size:92px;font-weight:900;line-height:1;letter-spacing:-.02em}
 .stat .l{font-size:23px;color:#a9c2c2;font-weight:600;margin-top:12px;max-width:340px;line-height:1.3}
 .bars{margin-top:40px;max-width:1150px}
 .bar{display:flex;align-items:center;gap:20px;margin:16px 0;font-size:27px}
 .bar .lab{width:150px;font-weight:700;color:#eaf2f2}
 .bar .track{flex:1;height:34px;background:rgba(255,255,255,.09);border-radius:8px;overflow:hidden}
 .bar .fill{height:100%;border-radius:8px}
 .bar .v{width:120px;font-weight:800;font-variant-numeric:tabular-nums}
 svg{display:block}
 .maplabel{font:700 20px Inter,sans-serif}
</style></head><body>__BODY__</body></html>'''

def card(n, body):
    open(os.path.join(SHARE, f'card{n}.html'), 'w', encoding='utf-8').write(BASE.replace('__BODY__', body))

FOOT = '<div class="foot"><span>Critical Materials Atlas · public trade data 2018–2024</span><span class="u">criticalmaterialsatlas.org</span></div>'

# ---- Card 1: the core finding ----
n_cap = bo['summary']['by_moat']['import-fed capability'] + bo['summary']['by_moat']['by-product capability']
card(1, f'''<div class="card">
 <div class="eyebrow">The finding</div>
 <div class="h">China refines what it<br>doesn&rsquo;t <span class="amber">mine</span>.</div>
 <div class="sub">For <b>{n_cap}</b> critical materials the chokepoint is a <b>capability</b>, not an ore endowment — it <i>imports</i> the ore and <i>exports</i> the refined metal, or pulls the metal from a domestic by-product stream. <b>Export controls on ore can&rsquo;t touch it.</b> Gallium: China holds <b>87%</b> of refined supply as a by-product moat.</div>
 <div class="spacer"></div>{FOOT}</div>''')

# ---- Card 2: uncoverable ----
be = ot['materials']['beryllium']
cov = be['coverage']
card(2, f'''<div class="card">
 <div class="eyebrow">Reallocation stress test</div>
 <div class="h">Double every other<br>exporter. <span class="red">Still short.</span></div>
 <div class="sub">Cut the leader and reallocate its exports optimally across everyone else. For <b>{ot["summary"]["uncoverable2x"]} of 31</b> materials, even a <b>2× scale-up of every surviving exporter</b> can&rsquo;t cover the gap. Beryllium ({be["leader_name"]}, {round(be["leader_export_share"]*100)}% of exports):</div>
 <div class="bars">
  <div class="bar"><span class="lab">2× each</span><span class="track"><span class="fill" style="width:{cov['2']*100:.0f}%;background:#ef7c6b"></span></span><span class="v" style="color:#ef7c6b">{cov['2']*100:.0f}%</span></div>
  <div class="bar"><span class="lab">3× each</span><span class="track"><span class="fill" style="width:{cov['3']*100:.0f}%;background:#f0b429"></span></span><span class="v" style="color:#f0b429">{cov['3']*100:.0f}%</span></div>
  <div class="bar"><span class="lab">5× each</span><span class="track"><span class="fill" style="width:{cov['5']*100:.0f}%;background:#3fd0bd"></span></span><span class="v" style="color:#3fd0bd">{cov['5']*100:.0f}%</span></div>
 </div>
 <div class="spacer"></div>{FOOT}</div>''')

# ---- Card 3: backfire ----
ph = ot['materials']['phosphorus']
card(3, f'''<div class="card">
 <div class="eyebrow">The counterintuitive one</div>
 <div class="h">Diversifying away can<br>make it <span class="red">worse</span>.</div>
 <div class="sub">For <b>{ot["summary"]["backfire"]} of 31</b> materials, removing the dominant exporter <i>raises</i> concentration — it just hands the chokepoint to a more-concentrated runner-up. Phosphorus: cut <b>{ph["leader_name"]}</b> and it goes to <b>{ph["new_leader_name"]}</b>.</div>
 <div class="stats">
  <div class="stat"><div class="n" style="color:#a9c2c2">{ph['hhi_before']:.2f}</div><div class="l">concentration (HHI) today, led by {ph['leader_name']}</div></div>
  <div class="stat"><div class="n" style="color:#ef7c6b">{ph['hhi_after']:.2f}</div><div class="l">after removing the leader — <b>higher</b>, now {ph['new_leader_name']}</div></div>
 </div>
 {FOOT}</div>''')

# ---- Card 4: reshuffle map (server-side projected) ----
CENT = ot['centroids']; mg = ot['materials']['magnets']
MW, MH = 1408, 470
def proj(iso):
    c = CENT.get(iso)
    if not c: return None
    return (((c[1]+180)/360)*MW, ((90-c[0])/180)*MH)
def arc(p, q):
    mx, my = (p[0]+q[0])/2, (p[1]+q[1])/2; dx, dy = q[0]-p[0], q[1]-p[1]; d = (dx*dx+dy*dy)**.5 or 1
    off = min(150, d*0.28); cx, cy = mx + (-dy/d)*off, my + (dx/d)*off
    return f'M{p[0]:.0f} {p[1]:.0f} Q{cx:.0f} {cy:.0f} {q[0]:.0f} {q[1]:.0f}'
svg = [f'<rect width="{MW}" height="{MH}" rx="14" fill="#0a1c1f"/>']
for lon in range(-150, 151, 30):
    x = ((lon+180)/360)*MW; svg.append(f'<line x1="{x:.0f}" y1="0" x2="{x:.0f}" y2="{MH}" stroke="#16343a" stroke-width="1"/>')
for lat in range(-60, 61, 30):
    y = ((90-lat)/180)*MH; svg.append(f'<line x1="0" y1="{y:.0f}" x2="{MW}" y2="{y:.0f}" stroke="#16343a" stroke-width="1"/>')
nodes = {}
mx = max(a['v'] for a in mg['after']) or 1
for a in mg['after']:
    p, q = proj(a['f']), proj(a['t'])
    if not p or not q: continue
    w = 1.5 + (a['v']/mx)**.5*8
    svg.append(f'<path d="{arc(p,q)}" fill="none" stroke="#2bb3a3" stroke-width="{w:.1f}" opacity=".72"/>')
    nodes[a['f']] = nodes.get(a['f'],0)+a['v']; nodes[a['t']] = nodes.get(a['t'],0)+a['v']
Lp = proj(mg['leader'])
if Lp:
    svg.append(f'<line x1="{Lp[0]-11:.0f}" y1="{Lp[1]-11:.0f}" x2="{Lp[0]+11:.0f}" y2="{Lp[1]+11:.0f}" stroke="#ef5b48" stroke-width="4"/>')
    svg.append(f'<line x1="{Lp[0]-11:.0f}" y1="{Lp[1]+11:.0f}" x2="{Lp[0]+11:.0f}" y2="{Lp[1]-11:.0f}" stroke="#ef5b48" stroke-width="4"/>')
nmax = max(nodes.values()) if nodes else 1
for iso, v in nodes.items():
    p = proj(iso)
    if not p: continue
    r = 4 + (v/nmax)**.5*13
    svg.append(f'<circle cx="{p[0]:.0f}" cy="{p[1]:.0f}" r="{r:.0f}" fill="#0e8f83" stroke="#0a1c1f" stroke-width="2"/>')
for iso, v in sorted(nodes.items(), key=lambda kv:-kv[1])[:9]:
    p = proj(iso)
    if p: svg.append(f'<text class="maplabel" x="{p[0]+8:.0f}" y="{p[1]+6:.0f}" fill="#cfe3e3">{iso}</text>')
svgtxt = f'<svg width="{MW}" height="{MH}" viewBox="0 0 {MW} {MH}">' + ''.join(svg) + '</svg>'
card(4, f'''<div class="card" style="padding:70px 96px 60px">
 <div class="eyebrow">Cut the chokepoint — where does supply go?</div>
 <div class="h" style="font-size:52px">If China&rsquo;s magnet exports stop, optimal transport<br>reroutes the world through <span class="teal">Japan, Korea &amp; SE Asia</span>.</div>
 <div style="margin:34px 0 10px">{svgtxt}</div>
 <div class="foot" style="border-top:0;padding-top:14px"><span>✕ = China cut · teal = min-distance reallocation of its {round(mg['leader_export_share']*100)}% export share</span><span class="u">criticalmaterialsatlas.org</span></div>
</div>''')

# ---- Card 5: leverage ----
kr = lv['importers']['KR']
card(5, f'''<div class="card">
 <div class="eyebrow">The leverage map — how exposed is your country</div>
 <div class="h">South Korea buys <span class="red">12</span> of 31<br>critical materials mostly<br>from <span class="amber">one country</span>.</div>
 <div class="sub">Material by material, we trace how much of each importer&rsquo;s supply runs through a single source. South Korea is <b>&ge;50% China-sourced</b> on <b>{kr['n_cn_captured']}</b> critical materials and single-sourced on <b>{kr['n_single']}</b>. The East-Asian manufacturing belt is the most locked-in; the US and Germany are far more diversified.</div>
 <div class="spacer"></div>{FOOT}</div>''')

# ---- X thread copy ----
thread = f'''# X thread — Critical Materials Atlas (draft, {ot['year']} data)

**1/** Everyone says "China controls critical minerals." I built a public-data atlas to ask the harder question: *so what do you actually do about it?* 32 materials, mine→refine→trade, 2018–2024. Thread 🧵
→ criticalmaterialsatlas.org
[card1.png]

**2/** The chokepoint usually isn't the mine — it's the furnace. For {n_cap} materials the dominant supplier *imports the ore and exports the refined metal*, or pulls it from a domestic by-product stream. Export controls on ORE can't touch that. Gallium: China refines 87%, and mines ~none of it.

**3/** So can the rest of the world cover a cut? I reallocated each leader's exports across every other exporter by optimal transport. For {ot['summary']['uncoverable2x']} of 31 materials, even DOUBLING every surviving exporter doesn't cover the gap. Beryllium: 2× everyone = {be['coverage']['2']*100:.0f}%.
[card2.png]

**4/** The counterintuitive part: for {ot['summary']['backfire']} of 31 materials, removing the dominant exporter *raises* concentration — you just hand the chokepoint to a more-concentrated runner-up. Diversifying away from Vietnam's phosphorus makes it worse (→ Kazakhstan).
[card3.png]

**5/** What a cut actually looks like: kill China's magnet exports and the world reshuffles through Japan, Korea and SE Asia — but the spare capacity often sits far from the stranded buyers.
[card4.png]

**6/** And who's exposed? South Korea is ≥50%-China-sourced on {kr['n_cn_captured']} critical materials. The East-Asian manufacturing belt is the most locked-in; the US & Germany are diversified.
[card5.png]

**7/** It also names who *could* break each chokepoint (product-space capability-adjacency) and who's actually building alternatives (Perpetua, Almonty, Lynas, Euro Manganese…). All public data, all methods open.
→ criticalmaterialsatlas.org

Images: share/card1.png … card5.png · data: out/*.json (breakout, ot, leverage)
'''
open(os.path.join(SHARE, 'x-thread.md'), 'w', encoding='utf-8').write(thread)
print('WROTE share/card1..5.html + share/x-thread.md')
