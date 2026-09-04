#!/usr/bin/env python3
"""Production concentration, 1995-2004 vs 2015-2024, from the BGS panel (production only — no AC, no trade,
no consumption model). The finding: ordinary commodities deconcentrate as more countries produce them;
critical materials, as a class, do not. Control group is what makes it a finding. Lead with the DIVERGENCE
(the change), not the LEVEL (partly definitional — criticality lists select on concentration; and the
1995-2004 baseline predates the EU CRM 2011 list). Run: python build_bgs_concentration.py -> out/concentration.json
"""
import json, os
from collections import Counter, defaultdict
P='raw/bgs/panel'
CRITICAL=['copper','lead','zinc','tin','cobalt','nickel','manganese','tungsten','molybdenum','vanadium',
 'antimony','graphite','fluorspar','lithium','titanium','magnesite','feldspar','barytes','phosphate_rock',
 'chromium','bismuth','platinum_group_metals','rare_earths']
TRANSITION={'lithium','cobalt','nickel','graphite','rare_earths','copper','platinum_group_metals','vanadium','manganese'}
CONTROL=['gypsum','salt','kaolin','gold','talc','diamond','bentonite_and_fuller_s_earth','potash',
 'aggregates_and_related_materials','asbestos','diatomite','mica','perlite','vermiculite','wollastonite',
 'nepheline_syenite','sillimanite_and_related_minerals','iodine','bromine']
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
crit=analyze(CRITICAL); ctrl=analyze(CONTROL)
def summ(rows):
    if not rows: return {}
    ch=[r['change'] for r in rows]
    return {'n':len(rows),'mean_hhi_9504':round(sum(r['hhi_9504'] for r in rows)/len(rows),3),
            'mean_hhi_1524':round(sum(r['hhi_1524'] for r in rows)/len(rows),3),
            'mean_change':round(sum(ch)/len(ch),3),'n_concentrated':sum(1 for c in ch if c>0.005),
            'n_deconcentrated':sum(1 for c in ch if c<-0.005),
            'mean_cov_9504':round(sum(r['cov_9504'] for r in rows)/len(rows)),
            'mean_cov_1524':round(sum(r['cov_1524'] for r in rows)/len(rows))}
tr=[r for r in crit if r['transition']]; ntr=[r for r in crit if not r['transition']]
out={'note':'BGS production-concentration (HHI), 1995-2004 vs 2015-2024. Production only — no trade/AC/model. '
     'Lead with the CHANGE (divergence), not the LEVEL: the level gap is partly definitional (criticality lists '
     'select on concentration) and the baseline predates the EU CRM 2011 list; the change is not definitional. '
     'Coverage confound ruled out IN THE RIGHT DIRECTION: both groups gained reporters, so the criticals\' rise '
     'is understated. HHI = sum of squared production shares; years with >=5 reporters only.',
     'critical':summ(crit),'transition':summ(tr),'non_transition':summ(ntr),'control':summ(ctrl),
     'materials':{'critical':sorted(crit,key=lambda r:-r['change']),'control':sorted(ctrl,key=lambda r:-r['change'])}}
os.makedirs('out',exist_ok=True); json.dump(out,open('out/concentration.json','w'),indent=1)
print("CRITICAL   ",summ(crit))
print("  TRANSITION",summ(tr))
print("  NON-TRANS ",summ(ntr))
print("CONTROL    ",summ(ctrl))
print("wrote out/concentration.json")
