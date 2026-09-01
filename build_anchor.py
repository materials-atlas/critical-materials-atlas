#!/usr/bin/env python3
"""Production-constrained reconciliation -- the anchor. A trade reconciliation should obey physics: a country
cannot EXPORT more of a material than it PRODUCES minus what it CONSUMES at home. With a trade-INDEPENDENT
consumption estimate (build_consumption.py) that becomes a testable constraint on the mirror trade, and it
repairs the origin gap -- where customs credit the refiner/re-exporter, not the mine.

Inputs (all independent):  production.json (WMD, per-country tonnes) . consumption.json (activity x calibrated
intensity, trade-independent) . flows_2024.json (the atlas's reconciled mirror trade, qty in tonnes).

Per producing country c:
    exportable(c)       = max(0, production(c) - consumption(c))
    exportable_share(c) = exportable(c) / sum_producers exportable        (physical prior on export origin)
Two levers combine into a corrected origin share:
    guardrailed(c)      = min(observed_share(c), exportable_share(c))      (HARD: can't export more than supply)
    corrected(c)        ~ w*guardrailed(c) + (1-w)*exportable_share(c)     (SOFT prior; w = trust in trade)
    (renormalised across the producer set; w = W_DEFAULT, documented & tunable.)

STAGE MATCHING is mandatory: the constraint is valid only where the MINED form is the TRADED form. For
materials mined and traded at different stages (lithium: spodumene->carbonate; graphite: flake->processed)
the naive comparison mis-signals, so they are flagged 'divergent' and reported but NOT corrected here --
they need two-stage (ore vs refined) handling. Run: python build_anchor.py -> out/anchor.json
"""
import csv, json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
W_DEFAULT = 0.5   # equal-weight blend of observed trade and physical exportable prior (documented, tunable)
# mined form != traded form in the HS codes we track -> constraint not valid without stage matching
STAGE_DIVERGENT = {'lithium': 'mined as spodumene, traded as carbonate/oxide',
                   'graphite': 'mined as flake, traded as spherical/processed (re-exported)'}

prod = {r['label']: r for r in json.load(open(os.path.join(ROOT,'out','production.json'),encoding='utf8'))['rows']}
_cj = json.load(open(os.path.join(ROOT,'out','consumption.json'),encoding='utf8'))
cons = _cj['matrix']
CONS_MATS = set(_cj['materials'])   # materials we actually have a consumption estimate for
fj = json.load(open(os.path.join(ROOT,'out','flows_2024.json'),encoding='utf8'))
flows, NAMES = fj['materials'], fj['names']
I2to3 = {}
for r in csv.DictReader(open(os.path.join(ROOT,'raw','baci','country_codes_V202601.csv'),encoding='utf-8')):
    if r.get('country_iso2') and r.get('country_iso3'): I2to3[r['country_iso2']] = r['country_iso3']

def consumption_t(iso2, mat):
    a3 = I2to3.get(iso2)
    if not a3 or a3 not in cons: return 0.0
    d = cons[a3]['demand'].get(mat)
    return d['t'] if d and d.get('basis') == 'calibrated' else 0.0

def export_share(mat):
    q = defaultdict(float)
    for f in flows.get(mat, []): q[f['from']] += (f.get('qty') or 0)
    tot = sum(q.values()) or 1
    return {k: 100*v/tot for k, v in q.items()}

def derive():
  results = []
  for mat, p in prod.items():
    if mat not in flows or not p.get('top5'): continue
    obs = export_share(mat)                       # WORLD base: c's exports / world exports
    world_t = p.get('world_tonnes') or 0
    divergent = mat in STAGE_DIVERGENT
    has_cons = mat in CONS_MATS                    # do we have a real consumption estimate for this material?
    # regime: divergent (stage mismatch) > production-only (no consumption estimate, exportable=production is an
    # ASSUMPTION that fails if the producer consumes at home, e.g. US beryllium) > matched (consumption-anchored)
    regime = 'divergent' if divergent else ('production-only' if not has_cons else 'matched')
    rows = []
    for t in p['top5']:
        iso = t['iso']; o = obs.get(iso, 0.0)
        c = consumption_t(iso, mat)
        e = 100*max(0.0, t['tonnes'] - c)/world_t if world_t else 0.0   # WORLD base: exportable / world production
        g = e - o
        # A correction is asserted ONLY when it is both physically safe (under-attribution: producer credited
        # LESS than it can supply -> refiner-fronting) AND consumption-anchored (we can rule out domestic use).
        under = regime == 'matched' and g > 10
        corrected = round(W_DEFAULT*o + (1-W_DEFAULT)*e, 1) if under else None
        rows.append({'iso': iso, 'name': NAMES.get(iso, iso), 'prod_t': t['tonnes'], 'prod_pc': round(t['share']),
                     'cons_t': round(c), 'obs_pc': round(o, 1), 'expble_pc': round(e, 1),
                     'gap': round(g, 1), 'corrected_pc': corrected,
                     'review': (o > e + 10 and o > 5)})
    top = rows[0]
    results.append({'material': mat, 'title': p.get('title', mat), 'wmd_stage': p.get('wmd_stage','mine'),
                    'regime': regime, 'has_consumption': has_cons,
                    'stage_note': STAGE_DIVERGENT.get(mat, ''), 'top': top['name'],
                    'top_gap': top['gap'], 'top_obs': top['obs_pc'], 'top_expble': top['expble_pc'],
                    'top_corrected': top['corrected_pc'], 'porigin': (regime=='production-only' and top['gap']>10),
                    'rows': rows})
  matched = [r for r in results if r['regime'] == 'matched']
  corrected = [r for r in matched if r['top_corrected'] is not None]     # consumption-anchored origin-gap repairs
  mean_gap = round(sum(r['top_gap'] for r in corrected)/len(corrected), 1) if corrected else 0
  return {'w_default': W_DEFAULT, 'n_materials': len(results), 'n_matched': len(matched),
       'n_corrected': len(corrected), 'mean_gap': mean_gap,
       'note': ('Production-constrained anchor: exportable = production - trade-independent consumption; the '
                'mirror-trade origin share is guardrailed (cannot exceed exportable) and pulled toward the '
                'physical prior. Corrects the refiner-fronting origin gap for stage-matched materials; '
                'stage-divergent materials (mined form != traded form) are flagged, not corrected.'),
       'results': sorted(results, key=lambda r: (r['regime'] != 'matched', -r['top_gap']))}

if __name__ == '__main__':
    out = derive()
    json.dump(out, open(os.path.join(ROOT, 'out', 'anchor.json'), 'w', encoding='utf-8'), indent=1)
    print(f"{out['n_materials']} materials | {out['n_matched']} stage-matched | {out['n_corrected']} origin-gap corrected | mean gap {out['mean_gap']} pts")
    for r in out['results']:
        tag = r['regime'][:5]
        if r['top_corrected'] is not None:   note = f" -> corrected {r['top_corrected']:>4.0f}%"
        elif r['regime'] == 'divergent':     note = "  (stage-divergent: needs ore/refined match)"
        elif r.get('porigin'):               note = "  (production-only origin gap: needs a consumption estimate)"
        elif r['rows'][0]['review']:         note = "  (review: exports exceed mine surplus -- domestic refining?)"
        else:                                note = "  (consistent: no correction)"
        print(f"  [{tag}] {r['material']:12} top {r['top'][:14]:14} obs {r['top_obs']:>4.0f}% -> exportable {r['top_expble']:>4.0f}%" + note)
    print("wrote out/anchor.json")
