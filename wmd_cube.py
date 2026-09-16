# -*- coding: utf-8 -*-
"""World Mining Data, read from the published cube instead of the WMD spreadsheet.

The cube ingests every WMD sheet (build_cube_wmd.py) and keeps WMD's own country spelling in
native_country, so a page that quotes WMD can still print the names WMD prints. One door: builders
that used to open raw/wmd/*.xlsx each with their own parser call this instead.
"""
import os

import pandas as pd

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
_CACHE = {}


def _frame(year):
    if year not in _CACHE:
        c = pd.read_parquet(os.path.join(ROOT, 'out', 'cube.parquet'),
                            columns=['source', 'source_group', 'measure', 'year', 'value',
                                     'native_country'])
        _CACHE[year] = c[(c.source == 'World Mining Data') & (c.measure == 'production')
                         & (c.year == year) & (c.value > 0)]
    return _CACHE[year]


def sheets(year=2024):
    """The WMD sheet names that carry data for `year`."""
    return {g[len('WMD:'):] for g in _frame(year).source_group.unique()}


def parse_sheet(sheet, year=2024):
    """{WMD country name: production} for one sheet and year, in WMD's own units."""
    rows = _frame(year)
    rows = rows[rows.source_group == 'WMD:' + sheet]
    return {str(n): float(v) for n, v in rows.groupby('native_country').value.sum().items()}
