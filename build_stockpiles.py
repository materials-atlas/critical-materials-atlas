#!/usr/bin/env python3
"""Strategic stockpiles / days-of-cover -- the buffer that mostly isn't there. The atlas names stockpiling
as a lever on several pages (recycling, gallium, PGM, the geological chokepoints) but never measured who
actually holds a strategic reserve. This does, honestly -- and the honest answer is that for most critical
materials the Western buffer is roughly zero, while China's is real but opaque.

The data is genuinely sparse (China's State Reserve Bureau holdings are secret), so this is curated from
public sources and web-verified, not computed from a comprehensive series:
  - US National Defense Stockpile (DLA): ~$1.0-1.4bn inventory vs an identified shortfall of ~$14.8-15.5bn
    across 88 materials -- the holding is ~6% of that dollar shortfall. NB this is a budget gap in dollars,
    NOT days of cover; and government reserves are only part of the buffer (commercial inventories, scrap
    mobilisation and rationing also absorb a shock). Still, most critical materials are simply not held.
  - Japan (JOGMEC): the model. Stockpiles 7 rare metals -- nickel, chromium, tungsten, cobalt, molybdenum,
    manganese, vanadium -- at ~60 days of consumption (post-2010 policy; target up to 180 days for
    high-risk minerals).
  - China (SRB): holds rare earths, cobalt and others -- levels undisclosed. An information asymmetry as
    much as a material one.
  - EU: a strategic reserve is proposed under the Critical Raw Materials Act, not yet built.

Per the atlas's 32 materials we classify by ONE honest, checkable axis: does any country publish a
per-material DAYS-OF-COVER figure? Only Japan (JOGMEC) does. This is NOT "who holds a reserve" -- the US
NDS/DLA demonstrably holds ~28 commodities (cobalt, tungsten, tantalum, titanium sponge, beryllium,
germanium among ~42), and China's SRB holds more, undisclosed -- it is "whose buffer is quantified in the
open." Per-material US inventory is not reliably public, so we do NOT invent a US count; we state the
transparency gap, which is the real one. Run: python build_stockpiles.py -> out/stockpiles.json
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
LABELS = [m['label'] for m in data['materials']]

# Japan JOGMEC publishes per-material DAYS OF COVER for these (of the atlas's set) — the only country that
# does. (JOGMEC's programme is 7 metals incl. chromium & molybdenum, which aren't in the atlas's 32.)
JAPAN = {'nickel', 'tungsten', 'cobalt', 'manganese', 'vanadium'}

def status(lab):
    if lab in JAPAN:
        return ('quantified', 'Japan (JOGMEC): ~60-day cover, target up to 180 — the only PUBLISHED per-material days of cover')
    # NOT "no reserve": the US NDS may hold it, but on an undisclosed per-material basis; China's SRB is secret.
    return ('unquantified', 'No published days-of-cover (US NDS may hold it undisclosed; China SRB secret; EU not built)')

rows = [{'label': lab, 'buffer': status(lab)[0], 'note': status(lab)[1]} for lab in LABELS]
n_quantified = sum(r['buffer'] == 'quantified' for r in rows)
out = {
    'note': ('Per-material transparency of strategic reserves. The honest axis is not "who holds a buffer" '
             '(the US NDS and China SRB both hold materials) but "whose buffer is quantified in the open" — '
             'only Japan (JOGMEC) publishes per-material days of cover. Curated + web-verified.'),
    'regimes': [
        {'who': 'United States (National Defense Stockpile / DLA)',
         'fact': 'DLA Strategic Materials holds ~28 commodities (incl. cobalt, tungsten, tantalum, titanium sponge, beryllium, germanium); the inventory is ~$1.0-1.4bn vs a ~$14.8-15.5bn identified shortfall — small in dollar terms, and per-material days of cover are not published.',
         'verdict': 'Holds materials, but small relative to identified need and not published on a days-of-cover basis.'},
        {'who': 'Japan (JOGMEC)', 'fact': 'Stockpiles 7 rare metals (incl. cobalt, tungsten, manganese, vanadium, nickel) at ~60 days of consumption; target up to 180 days for high-risk.',
         'verdict': 'The model — the only country publishing per-material days of cover.'},
        {'who': 'South Korea (KORES / MOTIE)', 'fact': 'Holds a rare-metals reserve and publishes coverage TARGETS (e.g. days-of-cover goals), though per-material current levels are less granular than JOGMEC.',
         'verdict': 'A second allied programme with public targets — so "only Japan" is about published per-material cover specifically.'},
        {'who': 'China (State Reserve Bureau)', 'fact': 'Holds rare earths, cobalt and others — levels undisclosed.',
         'verdict': 'Real but opaque: an information asymmetry as much as a material one.'},
        {'who': 'European Union', 'fact': 'A strategic reserve is proposed under the Critical Raw Materials Act.',
         'verdict': 'Not yet built.'},
    ],
    'n_materials': len(rows), 'n_with_published_cover': n_quantified,
    'materials': rows,
}
json.dump(out, open(os.path.join(ROOT, 'out', 'stockpiles.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"of {len(rows)} tracked materials, {n_quantified} have a PUBLISHED per-material days-of-cover (Japan/JOGMEC); "
      f"{len(rows)-n_quantified} do not (held-but-undisclosed or no reserve)")
print("wrote out/stockpiles.json")
