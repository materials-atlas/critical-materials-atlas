#!/usr/bin/env python3
"""Production-constrained reconciliation -- the anchor. An ATTRIBUTION constraint (not a physical identity):
a country's mine-ORIGIN credit is bounded by what it PRODUCES minus what it domestically ABSORBS. Production
is the support of mine-origin attribution; the trade-INDEPENDENT consumption estimate (build_consumption.py)
is a proxy for domestic absorption. Where that bound BINDS it repairs the origin gap -- where customs credit
the refiner/re-exporter, not the mine. Two honest limits are surfaced explicitly: (1) the consumption term
does real work in only ~half the corrected rows -- each row now carries a `top_bind` = how far consumption
moves it vs a zero-consumption baseline; where that is ~0 the anchor is just a midpoint prior, not a
consumption-constrained result; (2) w=0.5 is a documented knob, so corrected shares are midpoints of
[observed, exportable], not point findings.

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
# RECYCLING: a country's own secondary supply meets part of its use, so only (1-R) of its consumption draws
# on PRIMARY exportable. R = approx world recycled/secondary share of supply (USGS MCS + EU CRM end-of-life
# rates; estimates). Assumes recycling arises ~proportional to consumption (scrap is where the metal was used).
# Note: imports are deliberately NOT added -- imported material carries a FOREIGN origin; the anchor traces
# origin to the mine, and re-exported imports surface instead as the 'review' (over-attribution) flag.
RECYCLE = {'copper':0.30,'nickel':0.30,'cobalt':0.25,'silver':0.18,'platinum':0.25,'palladium':0.25,
           'tungsten':0.30,'molybdenum':0.25,'niobium':0.20,'vanadium':0.10,'chromium':0.20,'manganese':0.10,
           'antimony':0.20,'germanium':0.30,'titanium':0.20,'magnesium':0.10,'beryllium':0.10,'tantalum':0.05,
           'lithium':0.05,'magnets':0.05}
# DRIVER MIS-PAIRING (under review): these materials get their consumption country-split from the `semi`
# driver, whose of_what is "silicon-fab materials spend" -- but they are consumed in DIFFERENT industries
# (Ga: compound-semi/LED; Ge: fibre/IR optics, PET; Be: specialty alloys/aerospace), with different geography.
# No open per-country series exists for the right industry, so the split is treated as UNALLOCATABLE: no
# correction is asserted (flagged, not corrected) rather than inherit silicon-fab geography. (tantalum also
# draws on semi but its anchor row is inert -- consumption doesn't bind -- so it is left for a later pass.)
DRIVER_REVIEW = {'gallium': 'split from silicon-fab spend; Ga is consumed in compound-semi/LED — different geography',
                 'germanium': 'split from silicon-fab spend; Ge is consumed in fibre/IR optics & PET — different geography',
                 'beryllium': 'split from silicon-fab spend; Be is consumed in specialty alloys/aerospace — different geography'}

prod = {r['label']: r for r in json.load(open(os.path.join(ROOT,'out','production.json'),encoding='utf8'))['rows']}
_cj = json.load(open(os.path.join(ROOT,'out','consumption.json'),encoding='utf8'))
cons = _cj['matrix']
CONS_MATS = set(_cj['materials'])   # materials we actually have a consumption estimate for
KNOWN = _cj['known_world']          # world consumption per material, in the consumption model's own units
CAP = _cj.get('capture', {})        # per-material share of world demand the consumption model captures
CONF = _cj.get('conf', {})          # per-material confidence in the end-use split (good/moderate/rough)
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
    known = KNOWN.get(mat) or 0                   # world consumption (consumption-model units)
    divergent = mat in STAGE_DIVERGENT
    has_cons = mat in CONS_MATS                    # do we have a real consumption estimate for this material?
    # regime: divergent (stage mismatch) > production-only (no consumption estimate, exportable=production is an
    # ASSUMPTION that fails if the producer consumes at home, e.g. US beryllium) > matched (consumption-anchored)
    regime = 'divergent' if divergent else ('production-only' if not has_cons else 'matched')
    rows = []
    for t in p['top5']:
        iso = t['iso']; o = obs.get(iso, 0.0)
        c = consumption_t(iso, mat)
        # Unit-SAFE: exportable share = production share - (1-R)*consumption share (both % of their world total),
        # so production form (oxide, borate) and consumption form (contained metal) never have to match. R =
        # recycled share: a country's own recycling meets R of its use, so only (1-R) draws on primary supply.
        R = RECYCLE.get(mat, 0.0)
        cons_share = 100*c/known if known else 0.0
        e = max(0.0, t['share'] - (1-R)*cons_share)
        g = e - o
        # A correction is asserted ONLY when it is both physically safe (under-attribution: producer credited
        # LESS than it can supply -> refiner-fronting) AND consumption-anchored (we can rule out domestic use).
        under = regime == 'matched' and g > 10 and mat not in DRIVER_REVIEW
        corrected = round(W_DEFAULT*o + (1-W_DEFAULT)*e, 1) if under else None
        rows.append({'iso': iso, 'name': NAMES.get(iso, iso), 'prod_t': t['tonnes'], 'prod_pc': round(t['share']),
                     'cons_t': round(c), 'obs_pc': round(o, 1), 'expble_pc': round(e, 1),
                     'gap': round(g, 1), 'corrected_pc': corrected,
                     'review': (o > e + 10 and o > 5)})
    top = rows[0]
    # BIND: how far the consumption term moves the correction vs a zero-consumption baseline (C=0, where
    # exportable collapses to production). corrected = w*obs + (1-w)*exportable; corrected(C=0) = w*obs +
    # (1-w)*production. So bind = (1-w)*(production_share - exportable_share) = half the leader's consumption
    # share. ~0 means the mine leader consumes ~none of what it digs -> the anchor is a midpoint prior, not a
    # consumption-constrained result. This is the single most honest number the page can show.
    top_bind = round((1-W_DEFAULT)*max(0.0, top['prod_pc'] - top['expble_pc']), 1)
    # A consumption-anchored pull-up is FIRM when the producer's own consumption is trustworthy — either it is a
    # near-zero consumer (a pure exporter, so uncovered end-uses can't hide at home: DRC cobalt, SA platinum), OR
    # its consumption is well-captured (high capture, non-rough split). It is INDICATIVE when the producer
    # plausibly consumes in end-uses we DON'T capture (US beryllium: capture 0.49 and the US has the industry).
    cap, cf = CAP.get(mat), CONF.get(mat, 'good')
    top_cons_share = 100*consumption_t(top['iso'], mat)/known if known else 0.0
    firm = (regime == 'matched' and top['corrected_pc'] is not None
            and (top_cons_share < 3.0 or ((cap or 1) >= 0.7 and cf != 'rough')))
    results.append({'material': mat, 'title': p.get('title', mat), 'wmd_stage': p.get('wmd_stage','mine'),
                    'regime': regime, 'has_consumption': has_cons, 'capture': cap, 'conf': cf, 'firm': firm,
                    'recycle': RECYCLE.get(mat, 0.0),
                    'stage_note': STAGE_DIVERGENT.get(mat, ''), 'top': top['name'],
                    'top_gap': top['gap'], 'top_obs': top['obs_pc'], 'top_expble': top['expble_pc'],
                    'top_corrected': top['corrected_pc'], 'porigin': (regime=='production-only' and top['gap']>10),
                    'top_bind': top_bind, 'binds': top_bind >= 3,
                    'driver_review': DRIVER_REVIEW.get(mat, ''),
                    'rows': rows})
  matched = [r for r in results if r['regime'] == 'matched']
  corrected = [r for r in matched if r['top_corrected'] is not None]     # consumption-anchored origin-gap repairs
  firm = [r for r in corrected if r['firm']]
  binding = [r for r in corrected if r['binds']]                         # consumption actually moves the anchor >=3pp
  review = [r for r in results if r['driver_review']]                    # split mis-paired to a wrong-industry driver
  mean_gap = round(sum(r['top_gap'] for r in corrected)/len(corrected), 1) if corrected else 0
  return {'w_default': W_DEFAULT, 'n_materials': len(results), 'n_matched': len(matched),
       'n_corrected': len(corrected), 'n_firm': len(firm), 'n_binding': len(binding),
       'n_driver_review': len(review),
       'note': ('Attribution constraint (not physics): mine-origin credit is bounded by production minus a '
                'trade-independent consumption estimate; the mirror-trade origin share is guardrailed (cannot '
                'exceed exportable) and pulled toward the exportable prior at w=0.5 (a documented knob, so '
                'corrected shares are midpoints of [observed, exportable]). Each row carries top_bind = how far '
                'consumption moves it vs a zero-consumption baseline; where ~0 the mine leader consumes almost '
                'none of what it digs, so the anchor is a midpoint prior there, not a consumption-constrained '
                'result. Materials whose consumption split is mis-paired to a wrong-industry driver (gallium/'
                'germanium/beryllium on silicon-fab spend) are flagged driver-review, not corrected. '
                'Stage-divergent materials (mined form != traded form) are flagged, not corrected.'),
       'mean_gap': mean_gap,
       'results': sorted(results, key=lambda r: (r['regime'] != 'matched', -r['top_gap']))}

if __name__ == '__main__':
    out = derive()
    json.dump(out, open(os.path.join(ROOT, 'out', 'anchor.json'), 'w', encoding='utf-8'), indent=1)
    print(f"{out['n_materials']} materials | {out['n_matched']} stage-matched | {out['n_corrected']} corrected "
          f"({out['n_binding']} where consumption actually binds) | {out['n_driver_review']} driver-review | mean gap {out['mean_gap']} pts")
    for r in out['results']:
        tag = r['regime'][:5]
        if r['driver_review']:               note = "  (DRIVER-REVIEW: consumption split mis-paired, not corrected)"
        elif r['top_corrected'] is not None: note = f" -> corrected {r['top_corrected']:>4.0f}%  [bind {r['top_bind']:>4.1f}{'  INERT' if not r['binds'] else ''}]"
        elif r['regime'] == 'divergent':     note = "  (stage-divergent: needs ore/refined match)"
        elif r.get('porigin'):               note = "  (production-only origin gap: needs a consumption estimate)"
        elif r['rows'][0]['review']:         note = "  (review: exports exceed mine surplus -- domestic refining?)"
        else:                                note = "  (consistent: no correction)"
        print(f"  [{tag}] {r['material']:12} top {r['top'][:14]:14} obs {r['top_obs']:>4.0f}% -> exportable {r['top_expble']:>4.0f}%" + note)
    print("wrote out/anchor.json")
