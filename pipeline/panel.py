# -*- coding: utf-8 -*-
"""A fixed reporter panel for monthly aggregates. Asked for by a reader, 9 Sep 2026.

THE PROBLEM IT SOLVES
Raw monthly totals are not comparable across months, because the set of reporters filing moves:
56 -> 46 -> 39 inside 2025-26 alone. A total that falls may mean less trade or one fewer file. And
the corollary is worse: a falling reporter count means missing tonnes can never be said to have
"gone nowhere" - they may sit in a file that stopped filing.

THE RULE
Keep only reporters that filed BOTH a value and a weight in EVERY month of the window, then
aggregate. Smaller panel, honest comparison. The helper returns the panel explicitly so a page can
say how many reporters it stands on, rather than hiding the number inside a total.

WHAT IT READS
The cube's monthly layer (pipeline/data/cube.parquet, freq='M'), where money and weight are
separate measures (exports_value / exports, imports_value / imports) at reporter x month x HS6.

Usage:
    from panel import fixed_panel, panel_series
    reps = fixed_panel('811010', 'exports', 202412, 202606)          # the reporters
    s = panel_series('811010', 'exports', 202412, 202606)             # monthly totals on that panel
"""
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUBE = os.path.join(ROOT, 'pipeline', 'data', 'cube.parquet')


def _months(lo, hi):
    out, y, m = [], lo // 100, lo % 100
    while y * 100 + m <= hi:
        out.append(y * 100 + m)
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def _monthly(hs6, direction, lo, hi, source=None):
    c = pd.read_parquet(CUBE, columns=['source', 'freq', 'period', 'native_code', 'country_iso3', 'measure', 'value'])
    c = c[(c.freq == 'M') & (c.native_code == str(hs6)) & c.period.between(lo, hi)]
    if source:
        c = c[c.source == source]
    return c


def fixed_panel(hs6, direction='exports', lo=202412, hi=202606, source=None):
    """Reporters with BOTH a weight row and a value row in EVERY month of [lo, hi]."""
    c = _monthly(hs6, direction, lo, hi, source)
    months = _months(lo, hi)
    w = c[c.measure == direction].groupby('country_iso3').period.nunique()
    v = c[c.measure == direction + '_value'].groupby('country_iso3').period.nunique()
    both = w[(w == len(months))].index.intersection(v[(v == len(months))].index)
    return sorted(both)


def panel_series(hs6, direction='exports', lo=202412, hi=202606, source=None):
    """Monthly totals (tonnes and USD) over the fixed panel only, with the panel size attached."""
    reps = fixed_panel(hs6, direction, lo, hi, source)
    c = _monthly(hs6, direction, lo, hi, source)
    c = c[c.country_iso3.isin(reps)]
    t = c[c.measure == direction].groupby('period').value.sum().rename('tonnes')
    u = c[c.measure == direction + '_value'].groupby('period').value.sum().rename('usd')
    out = pd.concat([t, u], axis=1).reindex(_months(lo, hi))
    out['reporters'] = len(reps)
    out['usd_per_t'] = out.usd / out.tonnes
    return out


if __name__ == '__main__':
    import sys
    hs6 = sys.argv[1] if len(sys.argv) > 1 else '811010'
    lo, hi = 202412, 202606
    reps = fixed_panel(hs6, 'exports', lo, hi)
    print('HS %s exports, %d..%d: fixed panel = %d reporters: %s' % (hs6, lo, hi, len(reps), ' '.join(reps)))
    print(panel_series(hs6, 'exports', lo, hi).round(1).to_string())
