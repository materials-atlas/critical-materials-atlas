#!/usr/bin/env python3
"""Strategic stockpiles / days-of-cover -- the buffer that mostly isn't there. The atlas names stockpiling
as a lever on several pages (recycling, gallium, PGM, the geological chokepoints) but never measured who
actually holds a strategic reserve. This does, honestly -- and the honest answer is that for most critical
materials the Western buffer is roughly zero, while China's is real but opaque.

The data is genuinely sparse (China's State Reserve Bureau holdings are secret), so this is curated from
public sources and web-verified, not computed from a comprehensive series:
  - US National Defense Stockpile (DLA): ~$1.0-1.4bn inventory vs an identified shortfall of ~$14.8-15.5bn
    across 88 materials -- it covers only ~6% of the net shortfall. Most critical materials: not held.
  - Japan (JOGMEC): the model. Stockpiles 7 rare metals -- nickel, chromium, tungsten, cobalt, molybdenum,
    manganese, vanadium -- at ~60 days of consumption (post-2010 policy; target up to 180 days for
    high-risk minerals).
  - China (SRB): holds rare earths, cobalt and others -- levels undisclosed. An information asymmetry as
    much as a material one.
  - EU: a strategic reserve is proposed under the Critical Raw Materials Act, not yet built.

Per the atlas's 32 materials, we classify the strategic buffer: an allied (Japan) stockpile, a token/US
holding, or none. Run: python build_stockpiles.py -> out/stockpiles.json
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
LABELS = [m['label'] for m in data['materials']]

# Japan JOGMEC stockpiles these (of the atlas's set); ~60 days cover, up to 180 for high-risk
JAPAN = {'nickel', 'tungsten', 'cobalt', 'manganese', 'vanadium'}   # (+chromium, molybdenum: not tracked here)
# atlas materials with a meaningful strategic buffer somewhere; everything else relies on the spot market

def status(lab):
    if lab in JAPAN:
        return ('allied', 'Japan (JOGMEC) ~60 days; up to 180-day target')
    return ('none', 'No public strategic reserve — spot-market dependent')

rows = [{'label': lab, 'buffer': status(lab)[0], 'note': status(lab)[1]} for lab in LABELS]
n_allied = sum(r['buffer'] == 'allied' for r in rows)
out = {
    'note': ('Strategic-stockpile status per material. Curated + web-verified; China SRB holdings are '
             'secret, so this measures the PUBLIC Western/allied buffer, which is the honest gap.'),
    'regimes': [
        {'who': 'United States (National Defense Stockpile / DLA)',
         'fact': '~$1.0-1.4bn held vs a ~$14.8-15.5bn identified shortfall across 88 materials — covers ~6% of the net shortfall.',
         'verdict': 'Largely depleted since the Cold War; most critical materials not held.'},
        {'who': 'Japan (JOGMEC)', 'fact': 'Stockpiles 7 rare metals (incl. cobalt, tungsten, manganese, vanadium, nickel) at ~60 days of consumption; target up to 180 days for high-risk.',
         'verdict': 'The model — a deliberate buffer built after the 2010 rare-earth shock.'},
        {'who': 'China (State Reserve Bureau)', 'fact': 'Holds rare earths, cobalt and others — levels undisclosed.',
         'verdict': 'Real but opaque: an information asymmetry as much as a material one.'},
        {'who': 'European Union', 'fact': 'A strategic reserve is proposed under the Critical Raw Materials Act.',
         'verdict': 'Not yet built.'},
    ],
    'n_materials': len(rows), 'n_with_allied_buffer': n_allied,
    'materials': rows,
}
json.dump(out, open(os.path.join(ROOT, 'out', 'stockpiles.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"of {len(rows)} tracked materials, {n_allied} have an allied (Japan) strategic stockpile; "
      f"{len(rows)-n_allied} rely on the spot market")
print("wrote out/stockpiles.json")
