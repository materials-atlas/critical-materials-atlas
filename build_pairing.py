#!/usr/bin/env python3
"""CROSS-SOURCE CORROBORATION — does a second, independent compilation agree with our number?

Two bodies count world mineral production by different routes. BGS sums the returns that national
statistical offices file; USGS publishes its own world estimate. Neither is derived from the other,
so where they agree, a production figure has genuine corroboration; where they diverge, something is
wrong with one of them OR - far more often - they are not describing the same object.

This is the generalised, automated form of the germanium catch. There, BGS's three reporting cells
summed to 1.4x USGS's entire world estimate, which is only visible if you put the two side by side.
Every material now gets that test.

THE PAIRING IS EXPLICIT, never inferred at run time. The council's rule for a multi-source table is
that you may not join on `material` alone: a ratio between "manganese ore, gross weight" and
"manganese, contained metal" is not a disagreement, it is a category error. So each pairing below
names the BGS form deliberately, and every non-agreement carries its reason.

Run:  python build_pairing.py   ->  out/pairing.json
"""
import os, sys, json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
CUBE = os.path.join(ROOT, 'pipeline', 'data', 'cube.parquet')

# material -> BGS form deliberately paired with the USGS world-production series.
PAIRS = {
    'copper': 'copper, mine', 'molybdenum': 'molybdenum, mine', 'cadmium': 'cadmium',
    'potash': 'potash', 'zinc': 'zinc, mine', 'silver': 'silver, mine', 'lead': 'lead, mine',
    'phosphate': 'phosphate rock', 'platinum': 'platinum group metals, mine', 'bauxite': 'bauxite',
    'antimony': 'antimony, mine', 'mercury': 'mercury', 'fluorspar': 'fluorspar',
    'gold': 'gold, mine', 'strontium': 'strontium minerals', 'tungsten': 'tungsten, mine',
    'vanadium': 'vanadium, mine', 'rhenium': 'rhenium', 'nickel': 'nickel, mine',
    'tin': 'tin, mine', 'asbestos': 'asbestos', 'arsenic': 'arsenic, white',
    'gypsum': 'gypsum and plaster', 'lithium': 'lithium minerals', 'baryte': 'barytes',
    'salt': 'salt', 'zirconium': 'zirconium minerals', 'tellurium': 'tellurium, refined',
    'perlite': 'perlite', 'magnesium': 'magnesite', 'iodine': 'iodine',
    'rare_earths': 'rare earth oxides', 'indium': 'indium, refinery', 'diatomite': 'diatomite',
    'feldspar': 'feldspar', 'talc': 'talc', 'iron': 'iron ore', 'selenium': 'selenium, refined',
    'wollastonite': 'wollastonite', 'germanium': 'germanium metal', 'gallium': 'gallium, primary',
    'mica': 'mica', 'graphite': 'graphite', 'boron': 'borates', 'titanium': 'titanium minerals',
    'bromine': 'bromine', 'cobalt': 'cobalt, mine', 'manganese': 'manganese ore',
    'chromium': 'chromium ores and concentrates', 'bismuth': 'bismuth, mine',
    'cement': 'cement, finished', 'beryllium': 'beryl', 'tantalum': 'tantalum and niobium minerals',
}

# Why a pairing cannot agree. Recording the reason is the point: an unexplained 2.8 invites someone
# to "fix" a number that was never wrong, and an unexplained 1.0 invites false confidence.
REASONS = {
    'manganese': 'BGS counts manganese ORE at gross weight; USGS counts CONTAINED manganese. '
                 'Ore grades ~30-50% Mn, which is the whole ratio.',
    'chromium':  'BGS counts chromite ORE at gross weight; USGS counts contained chromium.',
    'beryllium': 'BGS counts BERYL (the ore mineral); USGS counts contained beryllium. Beryl is '
                 'roughly 4% Be.',
    'tantalum':  'BGS publishes tantalum AND niobium minerals as one gross-ore series; USGS '
                 'publishes contained tantalum alone. Different numerator and different basis.',
    'titanium':  'BGS counts titanium MINERALS (ilmenite + rutile, gross); USGS reports on a '
                 'TiO2-content basis.',
    'bismuth':   'STAGE mismatch: the USGS world series here is refinery production, the BGS form '
                 'is mine output.',
    'cement':    'Scale mismatch between the two series - unresolved; do not use this pair until '
                 'the units are reconciled.',
    'cobalt':    'Unresolved. Both are nominally mine output on a contained basis, so a 0.6 ratio '
                 'is a real disagreement rather than a category error - worth investigating.',
    'bromine':   'Unresolved: likely a compound-vs-element basis difference.',
    'boron':     'BGS counts borate MINERALS (gross); USGS reports boron content.',
    'graphite':  'Unresolved: natural-graphite scope differs between the two.',
    'mica':      'Unresolved: sheet vs scrap/flake mica scope differs.',
    'germanium':   'BGS carries only 3-4 reporting countries for germanium metal, so its sum is not '
                   'a world total; USGS states outright that reliable world estimates cannot be made. '
                   'The near-agreement here is coincidence, not corroboration - this is the material '
                   'that prompted the whole check.',
    'gallium':     'BGS gallium coverage is thin and USGS publishes an estimate rather than a census; '
                   'neither side is a measured world total.',
    'iron':        'Iron ore scope differs: crude-ore vs usable-ore reporting is not consistent '
                   'between the two bodies.',
    'feldspar':    'Within compilation tolerance. No structural basis difference identified; the two '
                   'bodies revise on different schedules and BGS country coverage varies by year.',
    'talc':        'Within compilation tolerance; talc/pyrophyllite scope differs slightly.',
    'selenium':    'Within compilation tolerance; refinery-output coverage differs by year.',
    'wollastonite': 'Within compilation tolerance; few producers, so one country revision moves the '
                    'ratio noticeably.',

}


def build():
    c = pd.read_parquet(CUBE)
    b = c[c.source.str.startswith('BGS')]
    u = c[(c.source.str.startswith('USGS')) & (c.country_iso3 == 'WLD') & (c.measure == 'production')]
    rows = []
    for mat, form in sorted(PAIRS.items()):
        uu = u[u.material == mat].groupby('year').value_t.sum()
        bb = b[(b.material == mat) & (b.measure == 'production') & (b.native_label == form)
               & (b.value_t > 0)]
        if bb.empty or uu.empty:
            continue
        bs = bb.groupby('year').value_t.sum()
        yrs = sorted(set(bs.index) & set(uu.index) & set(range(2005, 2024)))
        if len(yrs) < 5:
            continue
        ratios = bs.loc[yrs].values / uu.loc[yrs].values
        r = float(np.median(ratios))
        spread = float(np.percentile(ratios, 90) - np.percentile(ratios, 10))
        status = ('corroborated' if 0.90 <= r <= 1.11 else
                  'close' if 0.80 <= r <= 1.25 else 'not_comparable')
        n_rep = int(bb[bb.year.isin(yrs)].groupby('year').country_iso3.nunique().median())
        rows.append({
            'material': mat, 'bgs_form': form, 'usgs_series': 'world production',
            'ratio': round(r, 3), 'ratio_spread_p10_p90': round(spread, 3),
            'years': [int(min(yrs)), int(max(yrs))], 'n_years': len(yrs),
            'bgs_reporters_median': n_rep, 'status': status,
            'reason': REASONS.get(mat) if status != 'corroborated' else None,
        })
    return rows


if __name__ == '__main__':
    rows = build()
    counts = {}
    for r in rows:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    out = {
        'note': 'Cross-source corroboration of world production. BGS national returns SUMMED vs the '
                'USGS world estimate - two independent compilations, neither derived from the other. '
                'ratio = median(BGS sum / USGS world) over the overlapping years. corroborated = '
                'within ~10%. A "not_comparable" row is usually a basis or stage difference, not an '
                'error: the pairing is stated explicitly and the reason recorded, because an '
                'unexplained ratio invites someone to fix a number that was never wrong.',
        'method': 'Pairings are declared in build_pairing.py, never inferred at run time. Joining on '
                  'material alone would compare gross ore against contained metal.',
        'summary': counts, 'n_materials': len(rows), 'rows': sorted(rows, key=lambda r: r['material']),
    }
    json.dump(out, open(os.path.join(ROOT, 'out', 'pairing.json'), 'w', encoding='utf-8'), indent=1)
    print(f'WROTE out/pairing.json — {len(rows)} materials paired')
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f'   {k}: {v}')
    unexplained = [r['material'] for r in rows if r['status'] != 'corroborated' and not r['reason']]
    if unexplained:
        print(f'   NO REASON RECORDED (fix or investigate): {", ".join(unexplained)}')
