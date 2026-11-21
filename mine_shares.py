# -*- coding: utf-8 -*-
"""World mine-production shares by country, from ONE documented rule. A library, not a builder.

THE RULE (set 21 Nov 2026): for a material and year, take
  1. the USGS Mineral Commodity Summaries country table (latest edition reporting that year), if we
     hold it for that commodity and it is a MINE table;
  2. else World Mining Data;
  3. else BGS World Mineral Statistics (shares of the countries that report, said so);
and never a hand-typed list. Hand values survive only for materials no source covers, and the
caller must label them.

Why it exists: until 21 Nov the atlas's mine shares were typed by hand in build_static.R. On 3 Oct
2026 a rebuild put an old typed list back over the audited one, every material at once, and
nothing noticed for seven weeks (baryte India -> China, strontium Iran -> Spain, coking coal had
Australia first where World Mining Data has China at 49%).
"""
import os

import pandas as pd

import usgs_mcs_cube as U

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))

# USGS tables in the store that are NOT mine production, though parsed under measure 'mine':
# titanium's is sponge metal (Japan 15%, a country with no titanium mine).
USGS_NOT_MINE = {'titanium'}

_CUBE = None


def _cube():
    global _CUBE
    if _CUBE is None:
        c = pd.read_parquet(os.path.join(ROOT, 'out', 'cube.parquet'),
                            columns=['material', 'measure', 'stage', 'source', 'country_iso3', 'year',
                                     'value', 'value_t', 'native_label'])
        _CUBE = c[(c.measure == 'production') & (c.stage == 'mine') & (c.country_iso3.str.len() == 3)
                  & (c.country_iso3 != 'WLD')]
    return _CUBE


def shares(usgs=None, cube=(), year=2024, native_label=None):
    """-> (source, {iso3: percent}, detail) or (None, {}, None).
    usgs: USGS store commodity name, or None. cube: cube material names (summed).
    native_label: keep only these cube rows (e.g. gem diamonds)."""
    if usgs and usgs not in USGS_NOT_MINE:
        s = U.shares(usgs, 'mine', year)
        if s is not None and len(s):
            s = s.dropna(subset=['iso3'])
            ed = U.panel(usgs, 'mine')
            ed = int(ed[ed.year == year].edition_year.max())
            return ('USGS Mineral Commodity Summaries', dict(zip(s.iso3, s.share * 100)),
                    {'edition': ed, 'year': year})
    c = _cube()
    for src in ('World Mining Data', 'BGS World Mineral Statistics'):
        g = c[c.material.isin(list(cube)) & (c.source == src) & (c.year == year)]
        if native_label:
            g = g[g.native_label == native_label]
        if len(g):
            col = 'value_t' if g.value_t.notna().any() else 'value'
            t = g.groupby('country_iso3')[col].sum()
            t = t[t > 0]
            det = {'year': year, 'reporters': int(len(t)),
                   'measured_as': ', '.join(sorted(g.native_label.dropna().unique()))}
            return src, (t / t.sum() * 100).to_dict(), det
    return None, {}, None
