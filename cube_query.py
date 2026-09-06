# -*- coding: utf-8 -*-
"""Ask the cube what it has, before asking it a question.

WHY THIS EXISTS
A query cannot be written blind. "Cobalt production" is not a well-formed request: the cube
holds cobalt mine production from four compilations, in three units, on two bases - BGS in
tonnes of metal content, USGS and World Mining Data in gross tonnes, the IEA in thousand
tonnes. Each is defensible; they are not the same number, and summing across them is nonsense.
So the identity has to be pinned before the join, and pinning it requires knowing what is on
offer. That is what metadata is FOR, and it only does the job if it is machine-readable at the
grain a query actually needs - per material, not per cube.

out/cube_summary.json describes the cube's shape (how many rows, which sources, which years).
It cannot answer "for cobalt, what may I pin?". This module answers exactly that, and then
refuses to run any query that is still ambiguous.

  identities(material=...)     what fact identities exist, with years and coverage
  attributes(material=...)     what material attributes exist, with source and vintage
  facts(...)                   rows for ONE pinned identity - raises, with the menu, if more
                               than one identity survives the filter
  attach(df, attribute, ...)   join an attribute onto facts; refuses if it would fan out

Nothing here silently picks for you. A default that guesses is how a doubled tonnage gets
published without anybody noticing.

Run:  python cube_query.py            # writes out/cube_manifest.json and prints an example
"""
import json, os
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'pipeline', 'data')
OUT = os.path.join(ROOT, 'out')

IDENTITY = ['source', 'measure', 'stage', 'basis', 'unit']
_cube = _dim = None


def cube():
    global _cube
    if _cube is None:
        _cube = pd.read_parquet(os.path.join(DATA, 'cube.parquet'))
    return _cube


def dim():
    global _dim
    if _dim is None:
        _dim = pd.read_parquet(os.path.join(DATA, 'dim_material.parquet'))
    return _dim


class Ambiguous(Exception):
    """Raised when a request matches more than one identity. Carries the menu of choices."""


def identities(material=None, measure=None, source=None):
    """What can be pinned. One row per distinct identity, with the coverage behind it."""
    c = cube()
    if material:
        c = c[c.material == material]
    if measure:
        c = c[c.measure == measure]
    if source:
        c = c[c.source == source]
    if not len(c):
        return pd.DataFrame(columns=['material'] + IDENTITY)
    g = (c.groupby(['material'] + IDENTITY, dropna=False)
          .agg(rows=('value', 'size'), year_min=('year', 'min'), year_max=('year', 'max'),
               countries=('country_iso3', 'nunique'),
               tonnage=('value_t', lambda s: bool(s.notna().any())))
          .reset_index().sort_values(['material', 'measure', 'rows'], ascending=[1, 1, 0]))
    return g


def attributes(material=None, attribute=None, current_only=False):
    """What describes a material, and on whose authority. Several vintages may be listed."""
    d = dim()
    if material:
        d = d[d.material == material]
    if attribute:
        d = d[d.attribute == attribute]
    if current_only:
        d = d[d.is_current]
    return d[['material', 'attribute', 'value_num', 'value_str', 'unit',
              'source', 'vintage', 'is_current', 'note']].reset_index(drop=True)


def facts(material, measure=None, source=None, stage=None, basis=None, unit=None, years=None):
    """Rows for ONE identity. If the filter leaves more than one, refuse and show the menu."""
    c = cube()
    c = c[c.material == material]
    for col, val in [('measure', measure), ('source', source), ('stage', stage),
                     ('basis', basis), ('unit', unit)]:
        if val is not None:
            c = c[c[col] == val]
    if years is not None:
        c = c[c.year.between(*years)]
    if not len(c):
        raise Ambiguous(f'no rows for {material} under that filter; '
                        f'call identities({material!r}) to see what exists')
    seen = c.groupby(IDENTITY, dropna=False).size()
    if len(seen) > 1:
        menu = '\n'.join(
            '    ' + ' | '.join('-' if pd.isna(k) else str(k) for k in key) + f'   ({n} rows)'
            for key, n in seen.items())
        raise Ambiguous(
            f'{material}: {len(seen)} identities match - these are different measurements of '
            f'different things and must not be pooled. Pin one:\n'
            f'    source | measure | stage | basis | unit\n{menu}')
    return c


def attach(df, attribute, source=None, vintage=None, column=None):
    """Join a material attribute onto fact rows without ever fanning them out.

    The whole point of the check: an attribute may legitimately have several vintages, so the
    caller either names one or accepts the current one. If what survives is still more than one
    row per material, this refuses rather than returning a table with doubled tonnages in it.
    """
    d = dim()
    d = d[d.attribute == attribute]
    if source is not None:
        d = d[d.source == source]
    if vintage is not None:
        d = d[d.vintage == vintage]
    if source is None and vintage is None:
        d = d[d.is_current]
    if not len(d):
        raise Ambiguous(f'no attribute {attribute!r} under that filter; '
                        f'call attributes(attribute={attribute!r}) to see sources and vintages')
    n = d.groupby('material').size()
    if (n > 1).any():
        rows = d[d.material.isin(n[n > 1].index)][['material', 'source', 'vintage']]
        raise Ambiguous(f'{attribute}: more than one row per material would attach, which '
                        f'duplicates every fact row it touches. Name a source or vintage:\n'
                        + rows.to_string(index=False))
    col = column or attribute
    vals = d.set_index('material').apply(
        lambda r: r.value_num if pd.notna(r.value_num) else r.value_str, axis=1)
    before = len(df)
    out = df.copy()
    out[col] = out.material.map(vals)
    assert len(out) == before, 'attach changed the row count - this must be impossible'
    return out


def write_manifest():
    """The machine-readable answer to 'what is in here, and what may I pin?'"""
    ids = identities()
    dd = dim()
    man = {
        'note': ('What the cube and its material dimension actually contain, at the grain a query '
                 'must pin. A material name alone is never a well-formed request: cobalt mine '
                 'production exists from four compilations on two bases in three units. Read this '
                 'before writing a filter; cube_query.facts() refuses anything still ambiguous.'),
        'identity_key': IDENTITY,
        'attribute_key': ['material', 'attribute', 'source', 'vintage'],
        'join_rule': ('Facts: pin the full identity. Attributes: name a vintage or take '
                      'is_current. Never match on the material label alone.'),
        'n_identities': int(len(ids)),
        'n_materials': int(ids.material.nunique()),
        'materials': {},
    }
    for m, g in ids.groupby('material'):
        man['materials'][m] = {
            'facts': [{'source': r.source, 'measure': r.measure,
                       'stage': None if pd.isna(r.stage) else r.stage,
                       'basis': None if pd.isna(r.basis) else r.basis,
                       'unit': None if pd.isna(r.unit) else r.unit,
                       'years': [int(r.year_min), int(r.year_max)], 'rows': int(r.rows),
                       'countries': int(r.countries), 'tonnage_convertible': bool(r.tonnage)}
                      for r in g.itertuples()],
            'attributes': [{'attribute': r.attribute, 'source': r.source,
                            'vintage': None if pd.isna(r.vintage) else int(r.vintage),
                            'is_current': bool(r.is_current)}
                           for r in dd[dd.material == m].itertuples()],
        }
    path = os.path.join(OUT, 'cube_manifest.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(man, f, indent=1, ensure_ascii=False)
    return man, path


if __name__ == '__main__':
    man, path = write_manifest()
    print('wrote %s: %d identities across %d materials'
          % (os.path.relpath(path, ROOT), man['n_identities'], man['n_materials']))

    print('\nWhat can be pinned for cobalt production:')
    print(identities('cobalt', measure='production')
          [['source', 'stage', 'basis', 'unit', 'year_min', 'year_max', 'rows']]
          .to_string(index=False))

    print('\nAsking blind, the way a query should not be written:')
    try:
        facts('cobalt', measure='production')
    except Ambiguous as e:
        print('  refused ->', str(e).split('\n')[0])

    print('\nAsking with the identity pinned:')
    f = facts('cobalt', measure='production', source='BGS World Mineral Statistics',
              stage='mine', basis='content', unit='tonnes (metal content)', years=(2015, 2024))
    print('  %d rows, %d countries, %d-%d'
          % (len(f), f.country_iso3.nunique(), f.year.min(), f.year.max()))
    j = attach(f, 'eol_rir')
    print('  attached eol_rir=%g, still %d rows' % (j.eol_rir.iloc[0], len(j)))
