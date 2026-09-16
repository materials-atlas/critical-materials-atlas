# -*- coding: utf-8 -*-
"""USGS Historical Statistics (DS 140) prices and world production, read from the published cube.

Replaces raw/usgs_hist/usgs_prices_slim.csv, a hand-extracted table that differed from the source
in two ways the cube does not: it wrote nickel's 2020 row and cadmium's 2022 row over 2019 and
2021 (the workbooks repeat those year labels; see build_cube_usgs.RELABEL), and it had no record
of which world-production column it took. Here the choice is written down.
"""
import os

import pandas as pd

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))

# When a workbook carries several world columns, the one the old slim table used comes first.
WORLD_ORDER = ['World production', 'World production (gross weight)', 'World mine production',
               'World mine production (metal content)', 'World production2',
               'World refinery production']


def prices():
    """DataFrame commodity, year, uv_nominal, uv_98, world_production - one row per commodity-year."""
    c = pd.read_parquet(os.path.join(ROOT, 'out', 'cube.parquet'),
                        columns=['source', 'source_group', 'measure', 'country_iso3', 'year',
                                 'value', 'native_label'])
    u = c[c.source == 'USGS Historical Statistics (DS 140)']
    key = ['source_group', 'year']
    nom = u[u.measure == 'unit_value_nominal'].groupby(key).value.first().rename('uv_nominal')
    r98 = u[u.measure == 'unit_value_real98'].groupby(key).value.first().rename('uv_98')
    w = u[(u.measure == 'production') & (u.country_iso3 == 'WLD')
          & u.native_label.isin(WORLD_ORDER)].copy()
    # ONE column per commodity (the first in WORLD_ORDER that the workbook has), never a per-year
    # fallback: splicing mine output onto refinery output where the first runs out would invent a
    # series that exists in no column.
    w['rank'] = w.native_label.map({n: i for i, n in enumerate(WORLD_ORDER)})
    chosen = w.groupby('source_group')['rank'].min()
    w = w[w['rank'] == w.source_group.map(chosen)]
    wp = w.groupby(key).value.first().rename('world_production')
    t = pd.concat([nom, r98, wp], axis=1).reset_index().rename(columns={'source_group': 'commodity'})
    return t.sort_values(['commodity', 'year']).reset_index(drop=True)


def rows():
    """The same table as dicts, with None for a missing value (a 0.0 is a value, not a blank)."""
    for r in prices().itertuples(index=False):
        yield {'commodity': r.commodity, 'year': int(r.year),
               'uv_nominal': None if pd.isna(r.uv_nominal) else float(r.uv_nominal),
               'uv_98': None if pd.isna(r.uv_98) else float(r.uv_98),
               'world_production': None if pd.isna(r.world_production) else float(r.world_production)}
