# -*- coding: utf-8 -*-
"""Does the atlas's own concentration finding survive its sources' revision noise?

Filed in self-audit/PREREGISTRATION.md (2026-09-24) and its deviation 1, both committed before this
ran. The method, in one line: rebuild each material's country-by-year production exactly as
build_bgs_concentration.py does, multiply every value by (1 + a revision drawn from the empirical pool
of that commodity's measured USGS revisions), recompute the finding, and count how often it keeps its
sign.

Writes out/self_audit.json.  Usage: python self-audit/analysis.py
"""
import io
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DRAWS = 2000
SEED = 20260924
EARLY, LATE = (1995, 2004), (2015, 2024)

# atlas material name (as concentration.json prints it) -> commodity in the USGS revision panel.
# Only these can be tested: a material with no panel counterpart has no measured revision pool.
PANEL = {
    'lithium': 'lithium', 'cobalt': 'cobalt', 'graphite': 'graphite', 'copper': 'copper',
    'antimony': 'antimony', 'tungsten': 'tungsten', 'nickel': 'nickel', 'manganese': 'manganese',
    'tin': 'tin', 'magnesium': 'magnesium', 'gallium': 'gallium', 'germanium': 'germanium',
    'indium': 'indium', 'tellurium': 'tellurium', 'rare_earths': 'rare_earths',
    'rare earths': 'rare_earths',
}


def revision_pools():
    """{commodity: array of signed country-series revisions}, from the USGS panel.

    The same computation the revision study uses - first printing against latest, in tonnes, flagged
    cells dropped - but kept at the country level, because the figures being perturbed are countries.
    """
    d = pd.read_parquet(os.path.join(ROOT, 'pipeline', 'data', 'usgs_mcs_history.parquet'))
    d = d[d.measure.isin(('mine', 'refinery', 'smelter', 'production')) & d.year.notna()].copy()
    d['v'] = d.value_t.where(d.value_t.notna(), d.value)
    pools = {}
    keys = ['commodity', 'measure', 'iso3', 'country_name_raw', 'year']
    for k, g in d[d.row_kind == 'country'].groupby(keys, dropna=False):
        g = g.sort_values('edition_year')
        g = g[g.v.notna() & g.flag.isna()]
        if len(g) < 2 or not g.v.iloc[0]:
            continue
        first, latest = float(g.v.iloc[0]), float(g.v.iloc[-1])
        pools.setdefault(k[0], []).append((latest - first) / first)
    return {c: np.asarray(v, dtype=float) for c, v in pools.items()}


def cube():
    c = pd.read_parquet(os.path.join(ROOT, 'out', 'cube.parquet'),
                        columns=['source', 'source_group', 'measure', 'native_label', 'native_group',
                                 'unit', 'country_iso3', 'year', 'value'])
    return c[(c.source == 'BGS World Mineral Statistics') & (c.measure == 'production')
             & (c.value > 0) & c.country_iso3.notna()]


def series_matrix(c, m):
    """The country-by-year production the concentration study reads, as {year: {iso: value}}."""
    prod = c[c.source_group == m.split(':')[0]]
    if ':' in m:
        prod = prod[prod.native_label == m.split(':', 1)[1]]
    if prod.empty:
        return None
    form = Counter(prod.native_group).most_common(1)[0][0]
    prod = prod[prod.native_group == form]
    unit = Counter(prod.unit).most_common(1)[0][0]
    prod = prod[prod.unit == unit]
    byyr = defaultdict(dict)
    for iso, y, q in zip(prod.country_iso3, prod.year, prod.value):
        y = int(y)
        byyr[y][iso] = byyr[y].get(iso, 0) + float(q)
    return {y: cs for y, cs in byyr.items() if len(cs) >= 5 and sum(cs.values()) > 0}


def hhi_change(byyr):
    """The published statistic: mean HHI over the late window minus the early window."""
    hhi = {y: sum((v / sum(cs.values())) ** 2 for v in cs.values()) for y, cs in byyr.items()}
    early = [hhi[y] for y in hhi if EARLY[0] <= y <= EARLY[1]]
    late = [hhi[y] for y in hhi if LATE[0] <= y <= LATE[1]]
    if not early or not late:
        return None
    return sum(late) / len(late) - sum(early) / len(early)


def perturbed_changes(byyr, pool, rng):
    """DRAWS recomputations of the statistic, each country-year value scaled by (1 + a drawn revision)."""
    years = sorted(byyr)
    isos = [sorted(byyr[y]) for y in years]
    vals = [np.array([byyr[y][i] for i in ii], dtype=float) for y, ii in zip(years, isos)]
    early_idx = [k for k, y in enumerate(years) if EARLY[0] <= y <= EARLY[1]]
    late_idx = [k for k, y in enumerate(years) if LATE[0] <= y <= LATE[1]]
    if not early_idx or not late_idx:
        return None
    out = np.empty(DRAWS, dtype=float)
    for d in range(DRAWS):
        hhis = []
        for v in vals:
            e = rng.choice(pool, size=len(v), replace=True)
            w = v * (1.0 + e)
            w = np.clip(w, 0.0, None)          # a revision cannot take production below zero
            s = w.sum()
            hhis.append(float(((w / s) ** 2).sum()) if s > 0 else np.nan)
        early = np.nanmean([hhis[k] for k in early_idx])
        late = np.nanmean([hhis[k] for k in late_idx])
        out[d] = late - early
    return out


def verdict(share_same_sign):
    if share_same_sign >= 0.95:
        return 'robust'
    if share_same_sign >= 0.50:
        return 'fragile'
    return 'not supported'


def main():
    pools = revision_pools()
    c = cube()
    published = json.load(io.open(os.path.join(ROOT, 'out', 'concentration.json'), encoding='utf-8'))
    rows_published = published['materials']['critical'] if isinstance(published['materials'], dict) \
        else published['materials']
    rng = np.random.default_rng(SEED)

    rows, excluded = [], []
    for r in rows_published:
        m = r['material']
        panel = PANEL.get(m.split(':')[0].replace('_', ' ')) or PANEL.get(m.split(':')[0])
        if not panel or panel not in pools or len(pools[panel]) < 20:
            excluded.append({'material': m, 'reason': 'no counterpart in the revision panel'
                             if not panel else 'panel counterpart has too few measured revisions'})
            continue
        byyr = series_matrix(c, m)
        if not byyr:
            excluded.append({'material': m, 'reason': 'no usable BGS series in the cube'})
            continue
        base = hhi_change(byyr)
        if base is None:
            excluded.append({'material': m, 'reason': 'one of the two windows is empty'})
            continue
        sims = perturbed_changes(byyr, pools[panel], rng)
        same = float(np.mean(np.sign(sims) == np.sign(base)))
        rows.append({
            'material': m, 'panel_commodity': panel,
            'published_change': r['change'], 'recomputed_change': round(base, 4),
            'share_same_sign': round(same, 4),
            'p05': round(float(np.percentile(sims, 5)), 4),
            'p95': round(float(np.percentile(sims, 95)), 4),
            'median_sim': round(float(np.median(sims)), 4),
            'revision_pool_n': int(len(pools[panel])),
            'revision_pool_median_abs': round(float(np.median(np.abs(pools[panel]))), 4),
            'verdict': verdict(same),
        })

    # the headline claim: the MEDIAN change across the tested materials, under the same draws
    head = None
    if rows:
        base_med = float(np.median([r['recomputed_change'] for r in rows]))
        rng2 = np.random.default_rng(SEED + 1)
        sims = []
        per_material = {}
        for r in rows:
            byyr = series_matrix(c, r['material'])
            per_material[r['material']] = perturbed_changes(byyr, pools[r['panel_commodity']], rng2)
        stack = np.vstack([per_material[r['material']] for r in rows])
        med_draws = np.median(stack, axis=0)
        head = {'published_median_change': round(base_med, 4),
                'share_same_sign': round(float(np.mean(np.sign(med_draws) == np.sign(base_med))), 4),
                'p05': round(float(np.percentile(med_draws, 5)), 4),
                'p95': round(float(np.percentile(med_draws, 95)), 4),
                'verdict': verdict(float(np.mean(np.sign(med_draws) == np.sign(base_med)))),
                'n_materials': len(rows)}
        sims = None

    res = {'filing': 'self-audit/PREREGISTRATION.md', 'draws': DRAWS, 'seed': SEED,
           'windows': {'early': list(EARLY), 'late': list(LATE)},
           'proxy': 'BGS production tested against USGS-measured revisions; every row is a proxy row',
           'headline': head, 'materials': rows, 'excluded': excluded,
           'n_tested': len(rows), 'n_excluded': len(excluded)}
    with io.open(os.path.join(ROOT, 'out', 'self_audit.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    for r in sorted(rows, key=lambda r: r['share_same_sign']):
        print('%-28s published %+.3f  recomputed %+.3f  sign survives %5.1f%%  [%+.3f, %+.3f]  %s'
              % (r['material'], r['published_change'], r['recomputed_change'],
                 100 * r['share_same_sign'], r['p05'], r['p95'], r['verdict'].upper()))
    if head:
        print('\nHEADLINE median change %+.3f over %d materials: sign survives %.1f%% of draws '
              '[%+.3f, %+.3f] -> %s' % (head['published_median_change'], head['n_materials'],
                                        100 * head['share_same_sign'], head['p05'], head['p95'],
                                        head['verdict'].upper()))
    print('tested %d, excluded %d' % (len(rows), len(excluded)))


if __name__ == '__main__':
    main()
