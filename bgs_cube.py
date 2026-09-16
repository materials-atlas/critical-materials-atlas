# -*- coding: utf-8 -*-
"""BGS World Mineral Statistics shares, read from the published cube.

Replaces raw/bgs_production_shares.json, a separate pull from the BGS OGC API that duplicated what
the cube already ingests from the BGS panel. The rules are the fetcher's (build_bgs_production.py), plus one fix (see below):
first commodity form that has a usable year, newest of 2024-2020 with >= 3 countries, top five.
"""
import os

import pandas as pd

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
PREFER = [2024, 2023, 2022, 2021, 2020]

# atlas label -> BGS bgs_commodity_trans candidates (first that returns a usable year wins)
FORMS = {
    'antimony': ['antimony, mine'], 'arsenic': ['arsenic, white', 'arsenic'], 'baryte': ['barytes'],
    'bauxite': ['bauxite'], 'beryllium': ['beryl'], 'boron': ['boron minerals', 'borates', 'boron'],
    'cobalt': ['cobalt, mine'], 'copper': ['copper, mine'], 'fluorspar': ['fluorspar'],
    'gallium': ['gallium'], 'germanium': ['germanium'], 'graphite': ['graphite'],
    'lithium': ['lithium minerals'], 'magnesium': ['magnesite'], 'magnets': ['rare earth minerals'],
    'manganese': ['manganese ore'], 'nickel': ['nickel, mine'], 'niobium': ['niobium', 'columbium'],
    'phosphate': ['phosphate rock'], 'phosphorus': ['phosphate rock'],
    'platinum': ['platinum'], 'palladium': ['palladium'],
    'strontium': ['strontium minerals'], 'tantalum': ['tantalum'],
    'titanium': ['titanium minerals', 'ilmenite'], 'tungsten': ['tungsten, mine'], 'vanadium': ['vanadium'],
}

_C = None


def _bgs():
    global _C
    if _C is None:
        import baci
        c = pd.read_parquet(os.path.join(ROOT, 'out', 'cube.parquet'),
                            columns=['source', 'measure', 'native_label', 'native_group', 'country_iso3', 'year', 'value'])
        c = c[(c.source == 'BGS World Mineral Statistics') & (c.measure == 'production') & (c.value > 0)]
        cc = baci.countries()
        i3to2 = {r3: r2 for r3, r2 in zip(cc['iso3'], cc['iso2']) if r3 and r2}
        _C = c.assign(iso2=c.country_iso3.map(i3to2)).dropna(subset=['iso2'])
    return _C


def top_shares(candidates):
    """The fetcher's record for one material, or None."""
    c = _bgs()
    for form in candidates:
        s = c[c.native_label == form]
        if s.empty:
            continue
        # BGS files some forms under one name: 'lithium minerals' also carries Chile's and
        # Argentina's lithium CARBONATE (erml 'Lithium', code 707), which the API pull summed into
        # ore tonnes. Keep the dominant BGS form group, as the concentration study does.
        s = s[s.native_group == s.native_group.value_counts().idxmax()]
        by = s.groupby(['year', 'iso2']).value.sum()
        years = {int(y): by.loc[y] for y in by.index.get_level_values(0).unique()}
        ok = lambda y: y in years and len(years[y]) >= 3 and years[y].sum() > 0
        yr = next((y for y in PREFER if ok(y)), None)
        if yr is None:
            recent = sorted((y for y in years if y >= 2020 and ok(y)), reverse=True)
            yr = recent[0] if recent else None
        if yr is None:
            continue
        tot = float(years[yr].sum())
        top = sorted(years[yr].items(), key=lambda kv: -kv[1])
        return {'commodity': form, 'year': yr, 'world_tonnes': round(tot),
                'top5': [{'iso': i, 'tonnes': round(t), 'share': round(100 * t / tot, 1)} for i, t in top[:5]]}
    return None
