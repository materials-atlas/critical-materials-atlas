#!/usr/bin/env python3
"""Inter-rater reliability of the mechanism taxonomy (author-run; answers an adversarial-council demand).
The council objected that the 58 chokepoints were coded by one person with no independent check. So the
58 stages were re-coded by a SECOND, independent classifier working BLIND — given only each chain's
product, binding stage, holder and share plus the eight mechanism definitions, with the atlas's own
label and its physics rationale hidden (taxonomy_recoding.json). This script scores the agreement.

Reports raw agreement and Cohen's kappa between the atlas coding (chokepoint_map.json) and the blind
second coding, and lists every disagreement. This is a consistency check, not a substitute for a panel
of domain experts — but kappa >= 0.8 is 'almost perfect' agreement on the Landis & Koch scale.

Run: python build_taxonomy_agreement.py   ->  writes out/taxonomy_agreement.json
"""
import os, json
from collections import Counter

ROOT = os.path.dirname(os.path.abspath(__file__))
VALID = {'thermodynamic', 'byproduct', 'capability', 'geological',
         'governance', 'policy', 'diffuse', 'fragility'}

atlas = {r['chain']: r['mechanism'] for r in json.load(open(os.path.join(ROOT, 'chokepoint_map.json'), encoding='utf-8'))['rows']}
second = json.load(open(os.path.join(ROOT, 'taxonomy_recoding.json'), encoding='utf-8'))['coding']

keys = [k for k in atlas if k in second and atlas[k] in VALID and second[k] in VALID]
n = len(keys)
po = sum(atlas[k] == second[k] for k in keys) / n
ca, cb = Counter(atlas[k] for k in keys), Counter(second[k] for k in keys)
pe = sum((ca[c] / n) * (cb[c] / n) for c in VALID)
kappa = (po - pe) / (1 - pe)

disagree = [{'chain': k, 'atlas': atlas[k], 'second': second[k]} for k in keys if atlas[k] != second[k]]

out = {
    'note': ('Inter-rater reliability of the 8-mechanism taxonomy: atlas coding vs an independent blind '
             're-coding of all 58 chokepoints. A consistency check, not a domain-expert panel.'),
    'n_chains': n,
    'raw_agreement_pct': round(100 * po, 1),
    'cohens_kappa': round(kappa, 3),
    'interpretation': ('almost perfect (Landis & Koch >0.80)' if kappa > 0.8 else
                       'substantial (0.61-0.80)' if kappa > 0.6 else 'moderate or lower'),
    'n_disagreements': len(disagree),
    'disagreements': sorted(disagree, key=lambda d: d['chain']),
}
json.dump(out, open(os.path.join(ROOT, 'out', 'taxonomy_agreement.json'), 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False)

print(f"atlas vs blind second coder: {n} chains")
print(f"  raw agreement {out['raw_agreement_pct']}%   Cohen's kappa {out['cohens_kappa']} ({out['interpretation']})")
print(f"  {out['n_disagreements']} disagreements:")
for d in out['disagreements']:
    print(f"    {d['chain']:16} atlas={d['atlas']:14} second={d['second']}")
print("\nwrote out/taxonomy_agreement.json")
