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


def series_id(d):
    """What identifies one series across editions. Needs row_kind, iso3 and country_name_raw.

    The printed label is not it. The world-total row is labelled with a rounding note that changes
    from one edition to the next ("World total (may be rounded)" / "World total (rounded)" / "World
    total"), and a country can be renamed between two editions (Czech Republic / Czechia). Keyed on
    the label, such a year split into two series of one printing each. In the revisions study that
    dropped 27 world-total years and 3 country years as "printed in one edition only"; in panel()
    below it returned the same country twice for one year. Found on 22 Nov 2026 from a count that
    did not add up. A country is its code where it has one; a world total is its label without the
    rounding note, which keeps titanium's ilmenite total apart from its combined one. A country row
    that carries no code is still its printed label.
    """
    s = d.country_name_raw.astype(object).copy()
    w = d.row_kind == 'world_printed'
    s[w] = (d.loc[w, 'country_name_raw']
            .str.replace(r'\s*\((may be )?rounded\)', '', regex=True)
            .str.replace(r',\s*(may be )?rounded\)', ')', regex=True).str.strip())
    c = (d.row_kind == 'country') & d.iso3.notna()
    s[c] = d.loc[c, 'iso3']
    return s


def store_stamp():
    """What the store held when a study read it, so check.py can tell that it has changed since.

    The revisions study and the self-audit are run by hand and are not in the runner's graph. Twice
    the store grew under them and the published numbers stayed as they were, with no symptom. Each
    study now writes this stamp into its output and check.py compares it with the store as it is.
    Integers only, so the stamp does not depend on the order or the precision of a float sum.
    """
    c = _store()
    return {'rows': int(len(c)),
            'chapters': int(c.groupby(['commodity', 'edition_year']).ngroups),
            'value_sum_thousandths': int((c.value.fillna(0) * 1000).round().astype('int64').sum())}


def built_from(*relpaths):
    """A short hash of the files a page was built from.

    The builder of a hand-run study page writes it into the page; check.py recomputes it. A page that
    was not rebuilt after its result or its filing changed (or whose builder stopped on an error and
    left the old page in place) then fails the check instead of staying published. Line endings are
    normalised so that a checkout on another system gives the same hash.
    """
    import hashlib
    import io
    h = hashlib.sha256()
    for p in relpaths:
        with io.open(os.path.join(ROOT, p), encoding='utf-8', newline='') as f:
            h.update(f.read().replace('\r\n', '\n').encode('utf-8'))
    return h.hexdigest()[:16]


def panel(commodity, measure='mine', countries_only=True):
    """One row per country-year: the value as the latest edition that reports that year gives it."""
    c = _store()
    c = c[(c.commodity == commodity) & (c.measure == measure) & c.year.notna()]
    if countries_only:
        c = c[c.row_kind == 'country']
    # keyed on what the series is, not on its printed label: see series_id()
    c = c.assign(_series=series_id(c)).sort_values('edition_year')
    last = (c.groupby(['commodity', 'row_kind', '_series', 'year'], dropna=False).tail(1)
            .drop(columns='_series').copy())
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
