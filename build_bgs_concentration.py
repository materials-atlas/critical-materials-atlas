#!/usr/bin/env python3
"""Production concentration, 1995-2004 vs 2015-2024, from the BGS panel (production only — no AC, no trade,
no consumption model). The finding: ordinary commodities deconcentrate as more countries produce them;
critical materials, as a class, do not. Control group is what makes it a finding. Lead with the DIVERGENCE
(the change), not the LEVEL (partly definitional — criticality lists select on concentration; and the
1995-2004 baseline predates the EU CRM 2011 list). Run: python build_bgs_concentration.py -> out/concentration.json
"""
import json, os, statistics as st
from collections import Counter, defaultdict
P='raw/bgs/panel'
CRITICAL=['copper','lead','zinc','tin','cobalt','nickel','manganese','tungsten','molybdenum','vanadium',
 'antimony','graphite','fluorspar','lithium','titanium','magnesite','feldspar','barytes','phosphate_rock',
 'chromium','bismuth','platinum_group_metals','rare_earths']
TRANSITION={'lithium','cobalt','nickel','graphite','rare_earths','copper','platinum_group_metals','vanadium','manganese'}
# Clean control group: genuinely ordinary commodities with market-structure (not cartel or regulatory)
# producer sets. Excluded on purpose: cement & iron/steel (they are DRIVERS in our own consumption model
# -> circular); diamond (cartel/structurally concentrated, behaves like a critical); asbestos (progressive
# bans collapsed the producer set -> policy shock, not market structure); wollastonite/nepheline/sillimanite/
# iodine/bromine (thin, geologically concentrated -> diamond-like noise).
CONTROL=['salt','silver','gypsum','gold','kaolin','talc','potash','diatomite',
 'aggregates_and_related_materials','mica','perlite','vermiculite','bentonite_and_fuller_s_earth']
def series(m):
    fn=f'{P}/{m}.json'
    if not os.path.exists(fn): return None,None
    d=json.load(open(fn)); prod=[r for r in d if r['bgs_statistic_type_trans']=='Production' and r['quantity'] and r['quantity']>0 and r['country_iso3_code']]
    if not prod: return None,None
    form=Counter(r['erml_commodity'] for r in prod).most_common(1)[0][0]; prod=[r for r in prod if r['erml_commodity']==form]
    unit=Counter(r['units'] for r in prod).most_common(1)[0][0]; prod=[r for r in prod if r['units']==unit]
    byyr=defaultdict(dict)
    for r in prod: byyr[int(r['year'][:4])][r['country_iso3_code']]=byyr[int(r['year'][:4])].get(r['country_iso3_code'],0)+r['quantity']
    hhi={y:sum((v/sum(cs.values()))**2 for v in cs.values()) for y,cs in byyr.items() if len(cs)>=5 and sum(cs.values())>0}
    cov={y:len(cs) for y,cs in byyr.items() if len(cs)>=5}
    return hhi,cov
def decade(h,a,b):
    v=[h[y] for y in h if a<=y<=b]; return sum(v)/len(v) if v else None
def analyze(names):
    rows=[]
    for m in names:
        h,cov=series(m)
        if not h: continue
        e,l=decade(h,1995,2004),decade(h,2015,2024)
        ec,lc=decade(cov,1995,2004),decade(cov,2015,2024)
        if e is None or l is None: continue
        rows.append({'material':m,'hhi_9504':round(e,3),'hhi_1524':round(l,3),'change':round(l-e,3),
                     'cov_9504':round(ec),'cov_1524':round(lc),'transition':m in TRANSITION})
    return rows
# Genuinely comparable controls: globally-traded, geology-sited non-critical commodities (mined where the
# resource is, not next to the point of use). The rest of CONTROL are transport-limited industrial minerals
# (gypsum/salt/aggregates/talc/perlite/kaolin/bentonite...) that deconcentrate for logistics reasons, not as
# a clean counterfactual. So the comparable subset is the real control; the wider set is context.
COMPARABLE={'gold','silver','potash'}
EXTREMES={'lithium','cobalt'}  # the two materials that carry the critical MEAN (leave-one-out test)
crit=analyze(CRITICAL)
ctrl=analyze(CONTROL)
for r in ctrl: r['comparable']=r['material'] in COMPARABLE
def summ(rows):
    if not rows: return {}
    ch=[r['change'] for r in rows]
    return {'n':len(rows),
            'mean_change':round(st.mean(ch),3),'median_change':round(st.median(ch),3),
            'mean_hhi_9504':round(st.mean(r['hhi_9504'] for r in rows),3),
            'mean_hhi_1524':round(st.mean(r['hhi_1524'] for r in rows),3),
            'n_concentrated':sum(1 for c in ch if c>0.005),'n_deconcentrated':sum(1 for c in ch if c<-0.005),
            'mean_cov_9504':round(st.mean(r['cov_9504'] for r in rows)),
            'mean_cov_1524':round(st.mean(r['cov_1524'] for r in rows))}
tr=[r for r in crit if r['transition']]; ntr=[r for r in crit if not r['transition']]
crit_ex=[r for r in crit if r['material'] not in EXTREMES]      # leave-one-out: drop the two extremes
comp=[r for r in ctrl if r['comparable']]                        # gold/silver/potash
out={'note':'BGS production-concentration (HHI of national production shares), 1995-2004 vs 2015-2024. '
     'Production only - no trade, no apparent consumption, no model. THE FINDING IS THE MEDIAN, NOT THE MEAN: '
     'the critical MEAN (+0.034) is carried almost entirely by lithium (+0.504) and cobalt (+0.310) - remove '
     'them and it goes to -0.002. The MEDIAN (+0.046) is robust to that (+0.044 without the two), so the '
     'TYPICAL critical material did concentrate modestly, while the often-cited average is really two materials. '
     'The LEVEL gap is partly definitional (criticality lists select on concentration) and the baseline predates '
     'the EU CRM 2011 list. CONTROL CAVEAT: most "ordinary minerals" are transport-sited (deconcentrate for '
     'logistics, not a counterfactual); the genuinely comparable, globally-traded controls are gold/silver/potash. '
     'SELECTION CAVEAT: critical lists were rewritten 2011-2023, inside the window, and lithium was listed partly '
     'because it concentrated - a full ex-ante freeze is the outstanding robustness check; the median\'s '
     'leave-one-out robustness is a partial defence. COVERAGE: reporter counts rose in both groups on average, '
     'but that does NOT correct a nonlinear per-row measure and the single biggest mover (lithium) LOST reporters '
     '(10->7); so the two largest movers are shown separately, not folded into an averaged coverage claim.',
     'critical':summ(crit),'critical_ex_extremes':summ(crit_ex),
     'transition':summ(tr),'non_transition':summ(ntr),
     'control_all':summ(ctrl),'control_comparable':summ(comp),
     'materials':{'critical':sorted(crit,key=lambda r:-r['change']),'control':sorted(ctrl,key=lambda r:-r['change'])}}
os.makedirs('out',exist_ok=True); json.dump(out,open('out/concentration.json','w'),indent=1)
print("CRITICAL         ",summ(crit))
print("  minus Li+Co    ",summ(crit_ex))
print("CONTROL all (13) ",summ(ctrl))
print("CONTROL comp (3) ",summ(comp))
print("wrote out/concentration.json")
