# -*- coding: utf-8 -*-
"""USGS Mineral Commodity Summaries, stitched into a country panel, read from the parsed store.

The store (pipeline/data/usgs_mcs_history.parquet, written by pipeline/parse_usgs_mcs.py) keeps every
edition's table, so one data year appears in two or more editions with different values: the USGS
revises the prior year and marks the current one as an estimate.

THE HEADLINE RULE, decided once and applied here: for each commodity, country, year and measure, take
the value from the LATEST edition that reports that year. That is the USGS's own most recent judgment
of it. `revisions()` shows what was discarded, so a revision is never silent.

Readers:
  panel(commodity, measure)  headline series, one row per country-year
  revisions(...)             every edition's value for a country-year, to see what changed
  world(commodity, measure)  the printed world total beside the sum of the countries
"""
import os

import pandas as pd

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, 'pipeline', 'data', 'usgs_mcs_history.parquet')
_C = None


def _store():
    global _C
    if _C is None:
        _C = pd.read_parquet(STORE)
    return _C


def editions(commodity=None):
    c = _store()
    if commodity:
        c = c[c.commodity == commodity]
    return sorted(c.edition_year.unique().tolist())


def panel(commodity, measure='mine', countries_only=True):
    """One row per country-year: the value as the latest edition that reports that year gives it."""
    c = _store()
    c = c[(c.commodity == commodity) & (c.measure == measure) & c.year.notna()]
    if countries_only:
        c = c[c.row_kind == 'country']
    c = c.sort_values('edition_year')
    keys = ['commodity', 'country_name_raw', 'iso3', 'year'] if countries_only else \
           ['commodity', 'country_name_raw', 'row_kind', 'year']
    last = c.groupby(keys, dropna=False).tail(1).copy()
    last['year'] = last['year'].astype(int)
    return last.sort_values(['year', 'country_name_raw']).reset_index(drop=True)


def revisions(commodity, measure='mine', iso3=None, year=None):
    """Every edition's value for a country-year, oldest edition first."""
    c = _store()
    c = c[(c.commodity == commodity) & (c.measure == measure) & c.year.notna()]
    if iso3:
        c = c[c.iso3 == iso3]
    if year:
        c = c[c.year == year]
    return c.sort_values(['year', 'edition_year'])[
        ['country_name_raw', 'iso3', 'year', 'edition_year', 'value', 'is_estimate', 'flag']].reset_index(drop=True)


def world(commodity, measure='mine'):
    """The printed world total and the sum of the countries, per year, latest edition reporting it."""
    c = _store()
    c = c[(c.commodity == commodity) & (c.measure == measure) & c.year.notna() &
          c.row_kind.isin(['world_printed', 'world_computed'])]
    c = c.sort_values('edition_year').groupby(['row_kind', 'year']).tail(1)
    p = c.pivot_table(index='year', columns='row_kind', values='value')
    p.index = p.index.astype(int)
    if {'world_printed', 'world_computed'} <= set(p.columns):
        p['rounding_gap'] = p['world_computed'] - p['world_printed']
    return p.reset_index()


def shares(commodity, measure='mine', year=None):
    """Country shares of the printed world total for one year (default: the latest year held)."""
    p = panel(commodity, measure)
    if p.empty:
        return None
    y = int(year or p.year.max())
    s = p[p.year == y]
    w = world(commodity, measure)
    tot = float(w[w.year == y].world_printed.iloc[0]) if not w[w.year == y].empty else float(s.value.sum())
    out = s[['iso3', 'country_name_raw', 'value', 'is_estimate']].copy()
    out['share'] = (out.value / tot).round(4)
    return out.sort_values('value', ascending=False).reset_index(drop=True)
