# -*- coding: utf-8 -*-
"""Fuse the dependency SCHEME and ETAPE detail into ONE wide, zoomable diagram. LEFT-TO-RIGHT flow:
each pipeline layer is a COLUMN, engine on the left, conclusions on the right, so every arrow runs
through a clear vertical gutter. Each node is compact by default (plain words + formula); its full
method / sources / results sit behind a click-to-open 'details' so the boxes stay small and the graph
stays readable. Dashed red arcs = the 3 feedback loops. Regenerates from project-formulas.html so it
never drifts. -> project-scheme.html  (big on purpose; zoom the page out to see it whole)."""
import re, json

ROOT = r$PSScriptRoot
form = open(ROOT + r'\project-formulas.html', encoding='utf8').read()
form_style = re.search(r'<style>(.*?)</style>', form, re.S).group(1)
legend = re.search(r'<div class="legend">.*?</div>', open(ROOT + r'\project-map.html', encoding='utf8').read(), re.S).group(0)

# --- extract the 20 step cards, balanced ---
body = form[form.index('<h2 class="band">'):form.index('<p class="fine">')]
def extract_cards(html):
    out = []
    for m in re.finditer(r'<div class="step"', html):
        i, depth = m.start(), 0
        for t in re.finditer(r'<div\b|</div>', html[i:]):
            depth += 1 if t.group() != '</div>' else -1
            if depth == 0:
                out.append(html[i:i + t.end()]); break
    return out
cards = extract_cards(body)

# --- graph: layers = pipeline depth (become COLUMNS, left->right); order within = top->bottom ---
LAYERS = [['node-src'], ['step-0'], ['step-1', 'step-6'], ['step-2'],
          ['step-3', 'step-4', 'step-5', 'step-7'],
          ['step-13', 'step-8', 'step-11'],
          ['step-14', 'step-10', 'step-9', 'step-12'],
          ['step-15', 'step-16'],
          ['step-17', 'step-18', 'step-19']]
EDGES = [('node-src', 'step-0'), ('step-0', 'step-1'), ('step-0', 'step-6'), ('step-1', 'step-2'),
         ('step-2', 'step-3'), ('step-2', 'step-4'), ('step-2', 'step-5'), ('step-2', 'step-7'),
         ('step-2', 'step-13'), ('step-2', 'step-16'), ('step-7', 'step-8'), ('step-7', 'step-11'),
         ('step-7', 'step-16'), ('step-8', 'step-9'), ('step-8', 'step-10'), ('step-11', 'step-12'),
         ('step-4', 'step-13'), ('step-13', 'step-14'), ('step-14', 'step-15'), ('step-14', 'step-16'),
         ('step-14', 'step-18'), ('step-5', 'step-16'), ('step-16', 'step-17'), ('step-16', 'step-18'),
         ('step-16', 'step-19')]
FB = [['step-9', 'step-8'], ['step-14', 'step-13'], ['step-15', 'step-0']]

FROM = {0: ['public data'], 1: [0], 2: [1], 3: [2], 4: [2], 5: [2], 6: [0], 7: [2], 8: [7], 9: [8],
        10: [8], 11: [7], 12: [11], 13: [2, 4], 14: [13], 15: [14], 16: [2, 5, 7, 14], 17: [16],
        18: [16, 14], 19: [16]}
TO = {0: [1, 6], 1: [2], 2: [3, 4, 5, 7, 13, 16], 3: [], 4: [13], 5: [16], 6: [], 7: [8, 11, 16],
      8: [9, 10], 9: [], 10: [], 11: [12], 12: [], 13: [14], 14: [15, 16, 18], 15: [], 16: [17, 18, 19],
      17: [], 18: [], 19: []}
def edge_strip(n):
    frm = ' '.join(f'<a href="#step-{x}">{x}</a>' if isinstance(x, int) else x for x in FROM[n])
    to = ' '.join(f'<a href="#step-{x}">{x}</a>' for x in TO[n]) or '&mdash;'
    return f'<div class="edges"><span>&#9664; {frm}</span><span>feeds &#9654; {to}</span></div>'

def place(card):
    n = int(re.search(r'<span class="num">(\d+)</span>', card).group(1))
    card = re.sub(r'<div class="step" style="([^"]*)">',
                  lambda m: f'<div class="step gnode" id="step-{n}" style="{m.group(1)}">', card, count=1)
    # collapse method/sources/results into a click-to-open details so the node stays compact
    card = re.sub(r'(<dl class="meta">.*?</dl>)',
                  lambda m: '<details class="more"><summary>method, sources &amp; results</summary>' + m.group(1) + '</details>',
                  card, count=1, flags=re.S)
    return card.replace('</h3>', '</h3>' + edge_strip(n), 1)

srcnode = ('<div class="gnode srcnode" id="node-src"><b>Public data</b>'
           '<small>Comtrade &middot; BACI<br>USGS &middot; IEA &middot; WGI</small></div>')
nodes = srcnode + '\n'.join(place(c) for c in cards)

CSS = r"""
 html{height:100%}
 body{background:#f5f8f7;height:100vh;display:flex;flex-direction:column;overflow:hidden}
 header.top{flex:0 0 auto;padding:.7rem 0 .65rem}
 header.top .wrap{max-width:1640px}
 header.top .eyebrow{font-size:.78rem}
 header.top h1{font-size:2.15rem;margin:.05rem 0 .25rem}
 header.top p{font-size:1rem;max-width:none;color:#d2e2df;line-height:1.38;margin:.15rem 0 0}
 header.top .keych{font-size:.86rem;margin-top:.35rem}
 .scroller{flex:1 1 auto;min-height:0;overflow:hidden;padding:0;position:relative;cursor:grab;background:#eef2f1}
 .scroller.grabbing{cursor:grabbing}
 .sitefoot{flex:0 0 auto;border-top:1px solid var(--line);background:#eef2f1;padding:.5rem 1.2rem}
 .graph{position:absolute;left:0;top:0;margin:0}
 svg.wires{position:absolute;left:0;top:0;z-index:0;overflow:visible;pointer-events:none}
 .gnode{position:absolute;background:#fff;border:1px solid var(--line);border-top:3px solid var(--c,var(--faint));
   border-radius:12px;padding:.75rem .9rem;margin:0!important;box-shadow:0 1px 2px rgba(20,50,58,.06),0 10px 26px rgba(20,50,58,.08)}
 .gnode h3{margin:.05rem 0 .3rem;font-size:.98rem}
 .gnode .plain{font-size:.82rem;margin:.2rem 0 .4rem}
 .gnode .fxlabel{margin-top:.3rem}.gnode .fx{overflow-x:auto;font-size:.82rem}
 .gnode .meta{font-size:.8rem}
 .more{margin-top:.45rem;border-top:1px dashed var(--line);padding-top:.3rem}
 .more>summary{cursor:pointer;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--accent);list-style:none}
 .more>summary::-webkit-details-marker{display:none}
 .more>summary::before{content:"\25B8  expand ";color:var(--faint)}
 .more[open]>summary::before{content:"\25BE  collapse ";color:var(--faint)}
 .srcnode{display:flex;flex-direction:column;justify-content:center;text-align:center;border-top-color:var(--spine);color:var(--navy)}
 .srcnode b{font-size:.95rem}.srcnode small{color:var(--mut);margin-top:.2rem;font-size:.76rem}
 .edges{display:none;gap:.5rem .8rem;flex-wrap:wrap;font-size:.7rem;color:var(--faint);font-weight:600;margin:.1rem 0 .4rem}
 .edges a{color:var(--c);text-decoration:none;background:color-mix(in srgb,var(--c) 10%,#fff);
   border:1px solid color-mix(in srgb,var(--c) 25%,var(--line));border-radius:100px;padding:.02rem .4rem}
 svg.wires path{fill:none}
 svg.wires .w{stroke:#7f9c96;stroke-width:1.9px;opacity:.9;marker-end:url(#ah)}
 svg.wires .w.fb{stroke:var(--systemic);stroke-width:2px;stroke-dasharray:7 4;opacity:.95;marker-end:url(#ahf)}
 .legend{display:flex;flex-wrap:wrap;gap:1rem;margin:.2rem 0 0;font-size:.82rem;color:var(--mut)}
 .legend span{display:inline-flex;align-items:center;gap:.4rem}.legend b{width:.7rem;height:.7rem;border-radius:3px;display:inline-block}
 .fbkey{display:inline-flex;align-items:center;gap:.35rem;color:var(--mut);font-size:.82rem}
 .fbkey i{width:1.5rem;height:0;border-top:2px dashed var(--systemic);display:inline-block}
 .howto{background:var(--sunk);border:1px solid var(--line);border-radius:12px;padding:.7rem 1rem;font-size:.85rem;color:var(--mut);margin:.4rem 0 1rem}
 .howto b{color:var(--ink)}
 .controlbar{flex:0 0 auto;background:#eef2f1;border-bottom:1px solid var(--line);
   padding:.5rem 1.2rem;display:flex;flex-wrap:wrap;gap:.5rem 1.2rem;align-items:center}
 .tools{display:flex;gap:.4rem;align-items:center;font-size:.82rem;color:var(--mut)}
 .tools button{font:inherit;cursor:pointer;border:1px solid var(--line);background:#fff;border-radius:8px;padding:.22rem .6rem;color:var(--ink)}
 .tools button:hover{background:var(--sunk)}
 .tools .grp{display:inline-flex;gap:.2rem;margin-right:.3rem}
 .zoomwrap{position:absolute;left:0;top:0}
 .graph{transform-origin:0 0;will-change:transform}
 .fine{font-size:.9rem}
 @media(max-width:1000px){
   body{height:auto;overflow:visible;display:block}
   .scroller{flex:none;overflow:visible;padding:0;min-height:0}
   .zoomwrap{width:auto!important;height:auto!important}
   .graph{width:auto!important;height:auto!important;transform:none!important;display:flex;flex-direction:column;gap:1rem}
   svg.wires{display:none}.edges{display:flex}.controlbar .tools .zoomgrp{display:none}
   .gnode{position:static!important;left:auto!important;top:auto!important;width:auto!important}
 }
"""

JS = """
<script>
const LAYERS=%s, EDGES=%s, FB=%s;
const wof=id=>id==='node-src'?210:365;
function layout(){
  const graph=document.querySelector('.graph'), svg=document.querySelector('svg.wires');
  if(matchMedia('(max-width:1000px)').matches){svg.innerHTML='';graph.style.width='';graph.style.height='';
    LAYERS.flat().forEach(id=>{const e=document.getElementById(id);e.style.position='';e.style.left=e.style.top=e.style.width='';});return;}
  const HGAP=104, VGAP=30, PAD=30;
  LAYERS.flat().forEach(id=>{const e=document.getElementById(id);e.style.position='absolute';e.style.width=wof(id)+'px';});
  const colH=LAYERS.map(L=>L.reduce((s,id)=>s+document.getElementById(id).offsetHeight,0)+VGAP*(L.length-1));
  const canvasH=Math.max.apply(0,colH)+PAD*2;
  let x=PAD; const colX=LAYERS.map((L,li)=>{const cw=Math.max.apply(0,L.map(wof)); const xi=x; x+=cw+HGAP; return [xi,cw];});
  const canvasW=x-HGAP+PAD;
  LAYERS.forEach((L,li)=>{let y=(canvasH-colH[li])/2; const [xi,cw]=colX[li];
    L.forEach(id=>{const e=document.getElementById(id);e.style.left=(xi+(cw-e.offsetWidth)/2)+'px';e.style.top=y+'px';y+=e.offsetHeight+VGAP;});});
  graph.style.width=canvasW+'px';graph.style.height=canvasH+'px';graph._cw=canvasW;graph._ch=canvasH;
  svg.style.width=canvasW+'px';svg.style.height=canvasH+'px';svg.setAttribute('viewBox','0 0 '+canvasW+' '+canvasH);
  const P=id=>{const e=document.getElementById(id);return{l:e.offsetLeft,t:e.offsetTop,r:e.offsetLeft+e.offsetWidth,b:e.offsetTop+e.offsetHeight,cy:e.offsetTop+e.offsetHeight/2};};
  const defs='<defs>'+
    '<marker id="ah" markerWidth="9" markerHeight="9" refX="7.5" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#7f9c96"/></marker>'+
    '<marker id="ahf" markerWidth="9" markerHeight="9" refX="7.5" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#c0392b"/></marker></defs>';
  let p='';
  EDGES.forEach(e=>{const s=P(e[0]),d=P(e[1]);const x1=s.r,y1=s.cy,x2=d.l,y2=d.cy,mx=(x1+x2)/2;
    p+='<path class="w" d="M'+x1+','+y1+' C'+mx+','+y1+' '+mx+','+y2+' '+x2+','+y2+'"/>';});
  FB.forEach((e,i)=>{const s=P(e[0]),d=P(e[1]);const topY=8+i*20;   // arc back over the top
    p+='<path class="w fb" d="M'+s.l+','+(s.t+12)+' C'+(s.l-70)+','+topY+' '+(d.r+70)+','+topY+' '+d.r+','+(d.t+12)+'"/>';});
  svg.innerHTML=defs+p;
  if(window._Z==null) fitScreen();   // scheme opens small (whole thing framed); scroll-wheel to zoom in and read
  else applyT();
}
const G=()=>document.querySelector('.graph'), SC=()=>document.querySelector('.scroller');
const clampZ=z=>Math.max(.12,Math.min(2.4,z));
function applyT(){
  const g=G(); if(!g._cw||matchMedia('(max-width:1000px)').matches){if(g)g.style.transform='';return;}
  g.style.transform='translate('+window._TX+'px,'+window._TY+'px) scale('+window._Z+')';
  const lab=document.getElementById('zlab'); if(lab)lab.textContent=Math.round(window._Z*100)+'%%';
}
function zoomAt(mx,my,f){                 // zoom keeping the point under the cursor fixed
  const nz=clampZ(window._Z*f);
  const wx=(mx-window._TX)/window._Z, wy=(my-window._TY)/window._Z;
  window._TX=mx-wx*nz; window._TY=my-wy*nz; window._Z=nz; applyT();
}
function zoomBy(f){const sc=SC();zoomAt(sc.clientWidth/2,sc.clientHeight/2,f);}
function setZoom(z){const sc=SC();zoomAt(sc.clientWidth/2,sc.clientHeight/2,clampZ(z)/window._Z);}
function fitScreen(){const g=G(),sc=SC();const z=Math.max(.12,Math.min(1,(sc.clientWidth-28)/g._cw,(sc.clientHeight-28)/g._ch));
  window._Z=z;window._TX=(sc.clientWidth-g._cw*z)/2;window._TY=(sc.clientHeight-g._ch*z)/2;applyT();}
function fitW(){const g=G(),sc=SC();const z=Math.max(.12,Math.min(1,(sc.clientWidth-28)/g._cw));
  window._Z=z;window._TX=14;window._TY=14;applyT();}
function setAll(open){document.querySelectorAll('details.more').forEach(d=>d.open=open);layout();}
function bind(){
  const sc=SC();
  // wheel ANYWHERE zooms only the scheme (and blocks the browser from zooming the whole page)
  addEventListener('wheel',e=>{if(matchMedia('(max-width:1000px)').matches)return;
    e.preventDefault();const r=sc.getBoundingClientRect();
    const mx=Math.max(0,Math.min(r.width,e.clientX-r.left)), my=Math.max(0,Math.min(r.height,e.clientY-r.top));
    zoomAt(mx,my, e.deltaY<0?1.12:1/1.12);},{passive:false});
  let drag=false,lx=0,ly=0;
  sc.addEventListener('mousedown',e=>{if(matchMedia('(max-width:1000px)').matches)return;
    if(e.target.closest('summary,a,button'))return;   // let clicks on expanders/links work
    drag=true;lx=e.clientX;ly=e.clientY;sc.classList.add('grabbing');e.preventDefault();});
  addEventListener('mousemove',e=>{if(!drag)return;
    window._TX+=e.clientX-lx;window._TY+=e.clientY-ly;lx=e.clientX;ly=e.clientY;applyT();});
  addEventListener('mouseup',()=>{drag=false;sc.classList.remove('grabbing');});
}
addEventListener('load',()=>{layout();setTimeout(layout,300);bind();
  document.querySelectorAll('details.more').forEach(d=>d.addEventListener('toggle',layout));});
addEventListener('resize',()=>{clearTimeout(window._wt);window._wt=setTimeout(layout,140);});
</script>
""" % (json.dumps(LAYERS), json.dumps(EDGES), json.dumps(FB))

HEAD = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Critical Materials Atlas &mdash; the build as one diagram</title>
<style>{form_style}{CSS}</style></head>
<body>
<header class="top"><div class="wrap">
  <div class="eyebrow">Project scheme &middot; the whole dependency tree in one picture</div>
  <h1>The whole atlas as one diagram</h1>
  <p>The <a href="project-map.html">dependency scheme</a> and the <a href="project-formulas.html">step-by-step method</a>, fused. It reads <b>left&nbsp;&rarr;&nbsp;right</b>: public data on the far left, each column one step deeper into the pipeline, conclusions on the right. Every arrow crosses a clear gutter between columns &mdash; solid grey = a dependency, <b style="color:var(--systemic)">dashed red</b> = one of the three feedback loops where a later result reaches back to fix an earlier one. Each box shows the plain-English idea and the formula; click <b>expand</b> on any box for its full method, sources and results. This bar stays at normal size &mdash; the diagram below is its own canvas: <b>scroll to zoom in on wherever your mouse is, drag to pan</b>, or use the buttons (<b>Fit screen</b> frames the whole thing).</p>
  <div class="keych"><span>Notation: <b>m</b> = material &middot; <b>c</b> = companionality (% by-product) &middot; <b>S</b> = shock size &middot; <b>uv</b> = implied unit value (price)</span></div>
</div></header>

<div class="controlbar">
  <div class="tools">
    <span class="zoomgrp grp"><button onclick="zoomBy(1/1.18)">&minus;</button><button onclick="fitScreen()">Fit screen</button><button onclick="fitW()">Fit width</button><button onclick="setZoom(1)">100%</button><button onclick="zoomBy(1.18)">+</button><span id="zlab" style="min-width:2.6rem;text-align:center">100%</span></span>
    <span class="grp"><button onclick="setAll(true)">Expand all</button><button onclick="setAll(false)">Collapse all</button></span>
    <span class="fbkey"><i></i> feedback loop</span>
  </div>
  {legend}
</div>

<div class="scroller">
  <div class="zoomwrap">
    <div class="graph">
      <svg class="wires"></svg>
      {nodes}
    </div>
  </div>
</div>

<div class="sitefoot">
<p class="fine" style="margin:0">Internal diagram &mdash; generated by <code>build_scheme.py</code> from <a href="project-map.html">project-map.html</a> (edges) and <a href="project-formulas.html">project-formulas.html</a> (detail), so it never drifts. Regenerate any time. Live atlas: <a href="https://criticalmaterialsatlas.org/">criticalmaterialsatlas.org</a></p>
</div>
{JS}
</body></html>
"""
open(ROOT + r'\project-scheme.html', 'w', encoding='utf8').write(HEAD)
print(f'wrote project-scheme.html  (left-to-right, {len(cards)} nodes in {len(LAYERS)} columns, {len(EDGES)} edges + {len(FB)} loops)')
