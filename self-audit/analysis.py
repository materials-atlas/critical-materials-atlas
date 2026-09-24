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

# Why a material the USGS does publish is still not tested. Left vague ("no counterpart"), these read
# as gaps in the source; they are limits of our own reading, and the council was right that the
# distinction matters to a reader.
EXCLUSION_REASON = {
    'platinum_group_metals': 'the USGS chapter prints platinum and palladium side by side, each with '
                             'its own pair of years, so reading it needs handling this study does not '
                             'have - our limit, not a gap in the source',
    'magnesite': 'in the older editions the reserve columns are headed where this parser reads a year, '
                 'so reserve values would enter the panel carrying years - our limit, not a gap in '
                 'the source',
    'bismuth': 'same reserve-column fault as magnesite in the 2022 edition - our limit, not a gap in '
               'the source',
}
# the seven materials the EU called critical BEFORE the change window, from build_bgs_concentration.py
EU_CRM_2011 = {'antimony', 'cobalt', 'fluorspar', 'graphite', 'platinum_group_metals', 'rare_earths',
               'tungsten'}
# the study's stated honest finding: cobalt concentrated while the older export-controlled materials
# came off monopoly highs
DIVERGENCE_UP = 'cobalt'
DIVERGENCE_DOWN = ('antimony', 'graphite', 'rare_earths')

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
    # added 2026-09-24 with the widened panel (deviation 3), so the headline can be tested
    'lead': 'lead', 'chromium': 'chromium', 'molybdenum': 'molybdenum', 'fluorspar': 'fluorspar',
    'phosphate rock': 'phosphate_rock', 'phosphate_rock': 'phosphate_rock',
    'barytes': 'barite', 'barite': 'barite', 'feldspar': 'feldspar', 'titanium': 'titanium',
    'vanadium': 'vanadium', 'zinc': 'zinc',
}


SHARE_CUTS = [0.0, 0.25, 0.50, 0.75, 0.90, 1.0]   # producer-size buckets, deviation 4
MIN_BUCKET = 30                                   # below this, fall back to the commodity's whole pool


def size_bucket(share_rank):
    """Which producer-size bucket a country-year falls in, by its rank within that year."""
    for i in range(1, len(SHARE_CUTS)):
        if share_rank <= SHARE_CUTS[i] or i == len(SHARE_CUTS) - 1:
            return i - 1
    return len(SHARE_CUTS) - 2


def revision_pools():
    """Revision pools keyed by (commodity, measure), and the same split by producer size.

    Two restrictions the first version of this study did not have, both found by review:

    * **One table per pool.** A chapter can print more than one production table, and the parser
      labels them with the same measure. The USGS titanium chapter prints mineral concentrates in
      thousand tonnes of contained TiO2 AND sponge metal in tonnes, and 156 sponge rows were pooled
      with 336 concentrate rows - different quantity, different unit, same `mine` label. Each pool is
      therefore restricted to the dominant (caption, unit) pair within its measure.
    * **Stage, not just commodity.** The pool must come from the stage the perturbed figures are. The
      atlas's lead concentration series is BGS "Lead, refined" while the USGS lead chapter prints only
      mine production, so perturbing one with the other would be a category error. Callers ask for a
      stage and get nothing if the chapter does not print it.
    """
    d = pd.read_parquet(os.path.join(ROOT, 'pipeline', 'data', 'usgs_mcs_history.parquet'))
    d = d[d.measure.isin(('mine', 'refinery', 'smelter', 'production')) & d.year.notna()].copy()
    d['v'] = d.value_t.where(d.value_t.notna(), d.value)
    d = d[d.row_kind == 'country']
    # The caption's wording drifts between editions for the SAME table ("World Mine Production and
    # Reserves" / "World Mine Production, Reserves, and Reserve Base"), so matching on it literally
    # throws away most of a pool. What has to be separated is a different PRODUCT in the same chapter -
    # titanium sponge metal beside mineral concentrates - which shows up ahead of "Production". So the
    # caption is cut back to what it says is being produced, and the dominant one kept.
    # The pool is already grouped by measure, so the caption only has to separate different PRODUCTS.
    # Stage words are therefore removed too: copper prints its mine column sometimes under "World Mine
    # Production" and sometimes under "World Mine and Refinery Production", and keeping only the
    # commoner caption silently discarded 194 of 714 real mine revisions.
    d['caption_stem'] = (d.table_caption.fillna('')
                         .str.replace(r'(?i)[ ,]*(and )?reserves?( base)?.*$', '', regex=True)
                         .str.replace(r'(?i)[ ,]*and (production )?capacity.*$', '', regex=True)
                         .str.replace(r'(?i)\b(mine|refinery|smelter|primary)\b', '', regex=True)
                         .str.replace(r'(?i)\band\b', ' ', regex=True)
                         .str.replace(r'\s+', ' ', regex=True).str.strip())
    keep = []
    for (c, m), g in d.groupby(['commodity', 'measure']):
        top = g.caption_stem.value_counts().idxmax()
        keep.append(g[g.caption_stem == top])
    d = pd.concat(keep) if keep else d

    pools, sized = {}, []
    keys = ['commodity', 'measure', 'iso3', 'country_name_raw', 'year']
    for k, g in d.groupby(keys, dropna=False):
        g = g.sort_values('edition_year')
        g = g[g.v.notna() & g.flag.isna()]
        if len(g) < 2 or not g.v.iloc[0]:
            continue
        first, latest = float(g.v.iloc[0]), float(g.v.iloc[-1])
        rev = (latest - first) / first
        pools.setdefault((k[0], k[1]), []).append(rev)
        sized.append({'commodity': k[0], 'measure': k[1], 'year': k[4], 'first': first, 'rev': rev})
    s = pd.DataFrame(sized)
    # a country-year's size is its share of that commodity-year-measure total, from the FIRST
    # printings - the same vintage the revision is measured against
    s['share'] = s['first'] / s.groupby(['commodity', 'measure', 'year'])['first'].transform('sum')
    s['rank'] = s.groupby(['commodity', 'measure', 'year'])['share'].rank(pct=True)
    s['bucket'] = [size_bucket(r) for r in s['rank']]
    by_size = {}
    for (c, m, b), g in s.groupby(['commodity', 'measure', 'bucket']):
        by_size[(c, m, int(b))] = np.asarray(g.rev.values, dtype=float)
    return ({k: np.asarray(v, dtype=float) for k, v in pools.items()}, by_size)


def bgs_stage(form):
    """Which stage a BGS form describes, so the pool can be drawn from the same stage."""
    f = (form or '').lower()
    if 'refined' in f or 'refinery' in f or 'smelter' in f or 'metal, ' in f:
        return 'refinery'
    return 'mine'


def pool_for(commodity, stage, pools):
    """The revision pool for a commodity at a stage, or None if the chapter does not print it."""
    order = ('mine', 'production') if stage == 'mine' else ('refinery', 'smelter', 'production')
    for m in order:
        p = pools.get((commodity, m))
        if p is not None and len(p) >= 20:
            return p, m
    return None, None


def cube():
    c = pd.read_parquet(os.path.join(ROOT, 'out', 'cube.parquet'),
                        columns=['source', 'source_group', 'measure', 'native_label', 'native_group',
                                 'unit', 'country_iso3', 'year', 'value'])
    return c[(c.source == 'BGS World Mineral Statistics') & (c.measure == 'production')
             & (c.value > 0) & c.country_iso3.notna()]


def series_matrix(c, m, want_form=False):
    """The country-by-year production the concentration study reads, as {year: {iso: value}}.

    With want_form, also returns the BGS form it picked - which names the stage, and so the revision
    pool that may legitimately be drawn on.
    """
    prod = c[c.source_group == m.split(':')[0]]
    if ':' in m:
        prod = prod[prod.native_label == m.split(':', 1)[1]]
    if prod.empty:
        return (None, None) if want_form else None
    form = Counter(prod.native_group).most_common(1)[0][0]
    prod = prod[prod.native_group == form]
    unit = Counter(prod.unit).most_common(1)[0][0]
    prod = prod[prod.unit == unit]
    byyr = defaultdict(dict)
    for iso, y, q in zip(prod.country_iso3, prod.year, prod.value):
        y = int(y)
        byyr[y][iso] = byyr[y].get(iso, 0) + float(q)
    out = {y: cs for y, cs in byyr.items() if len(cs) >= 5 and sum(cs.values()) > 0}
    return (out, form) if want_form else out


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


def perturbed_changes_stratified(byyr, commodity, measure, pool, by_size, rng):
    """As perturbed_changes, but each country-year draws from revisions of similarly sized producers.

    Post-hoc (deviation 4), reported beside the filed test and never in place of it.
    """
    years = sorted(byyr)
    vals, buckets = [], []
    for y in years:
        isos = sorted(byyr[y])
        v = np.array([byyr[y][i] for i in isos], dtype=float)
        tot = v.sum()
        rank = (np.argsort(np.argsort(v)) + 1) / len(v)      # percentile rank within the year
        vals.append(v)
        buckets.append(np.array([size_bucket(r) for r in rank]))
    early_idx = [k for k, y in enumerate(years) if EARLY[0] <= y <= EARLY[1]]
    late_idx = [k for k, y in enumerate(years) if LATE[0] <= y <= LATE[1]]
    if not early_idx or not late_idx:
        return None, None
    # which pool each bucket actually draws from, so the fallbacks can be reported
    draw_from, fell_back = {}, 0
    for b in range(len(SHARE_CUTS) - 1):
        p = by_size.get((commodity, measure, b))
        if p is None or len(p) < MIN_BUCKET:
            draw_from[b] = pool
            fell_back += 1
        else:
            draw_from[b] = p
    out = np.empty(DRAWS, dtype=float)
    for d in range(DRAWS):
        hhis = []
        for v, bk in zip(vals, buckets):
            e = np.array([rng.choice(draw_from[int(b)]) for b in bk])
            w = np.clip(v * (1.0 + e), 0.0, None)
            s = w.sum()
            hhis.append(float(((w / s) ** 2).sum()) if s > 0 else np.nan)
        out[d] = np.nanmean([hhis[k] for k in late_idx]) - np.nanmean([hhis[k] for k in early_idx])
    return out, fell_back


def verdict(share_same_sign):
    if share_same_sign >= 0.95:
        return 'robust'
    if share_same_sign >= 0.50:
        return 'fragile'
    return 'not supported'


def main():
    pools, by_size = revision_pools()
    c = cube()
    published = json.load(io.open(os.path.join(ROOT, 'out', 'concentration.json'), encoding='utf-8'))
    rows_published = published['materials']['critical'] if isinstance(published['materials'], dict) \
        else published['materials']
    rng = np.random.default_rng(SEED)

    rows, excluded = [], []
    for r in rows_published:
        m = r['material']
        panel = PANEL.get(m.split(':')[0].replace('_', ' ')) or PANEL.get(m.split(':')[0])
        if not panel:
            excluded.append({'material': m, 'reason': EXCLUSION_REASON.get(
                m, 'no counterpart in the revision panel')})
            continue
        byyr, form = series_matrix(c, m, want_form=True)
        stage = bgs_stage(form)
        pool, pool_measure = pool_for(panel, stage, pools)
        if pool is None:
            excluded.append({'material': m, 'reason':
                             'the atlas series is %s (BGS %r) and the USGS chapter prints no %s table '
                             'to measure revisions on - perturbing one stage with another would be a '
                             'category error' % (stage, form, stage)})
            continue
        if not byyr:
            excluded.append({'material': m, 'reason': 'no usable BGS series in the cube'})
            continue
        base = hhi_change(byyr)
        if base is None:
            excluded.append({'material': m, 'reason': 'one of the two windows is empty'})
            continue
        sims = perturbed_changes(byyr, pool, rng)
        same = float(np.mean(np.sign(sims) == np.sign(base)))
        strat, fell_back = perturbed_changes_stratified(byyr, panel, pool_measure, pool, by_size, rng)
        same_s = float(np.mean(np.sign(strat) == np.sign(base))) if strat is not None else None
        rows.append({
            'material': m, 'panel_commodity': panel,
            'published_change': r['change'], 'recomputed_change': round(base, 4),
            'share_same_sign': round(same, 4),
            'p05': round(float(np.percentile(sims, 5)), 4),
            'p95': round(float(np.percentile(sims, 95)), 4),
            'median_sim': round(float(np.median(sims)), 4),
            'bgs_form': form, 'stage': stage, 'pool_measure': pool_measure,
            'revision_pool_n': int(len(pool)),
            'revision_pool_median_abs': round(float(np.median(np.abs(pool))), 4),
            'verdict': verdict(same),
            # post-hoc, deviation 4: the same test drawing from similarly sized producers
            'stratified_share_same_sign': round(same_s, 4) if same_s is not None else None,
            'stratified_p05': round(float(np.percentile(strat, 5)), 4) if strat is not None else None,
            'stratified_p95': round(float(np.percentile(strat, 95)), 4) if strat is not None else None,
            'stratified_verdict': verdict(same_s) if same_s is not None else None,
            'stratified_buckets_fell_back': fell_back,
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
            pl, _ = pool_for(r['panel_commodity'], r['stage'], pools)
            per_material[r['material']] = perturbed_changes(byyr, pl, rng2)
        stack = np.vstack([per_material[r['material']] for r in rows])
        med_draws = np.median(stack, axis=0)
        rng3 = np.random.default_rng(SEED + 2)
        strat_stack = []
        for r in rows:
            byyr = series_matrix(c, r['material'])
            pl, pm = pool_for(r['panel_commodity'], r['stage'], pools)
            s, _ = perturbed_changes_stratified(byyr, r['panel_commodity'], pm, pl, by_size, rng3)
            strat_stack.append(s)
        strat_med = np.median(np.vstack(strat_stack), axis=0)
        head = {'published_median_change': round(base_med, 4),
                'share_same_sign': round(float(np.mean(np.sign(med_draws) == np.sign(base_med))), 4),
                'p05': round(float(np.percentile(med_draws, 5)), 4),
                'p95': round(float(np.percentile(med_draws, 95)), 4),
                'verdict': verdict(float(np.mean(np.sign(med_draws) == np.sign(base_med)))),
                'n_materials': len(rows),
                'stratified_share_same_sign': round(float(np.mean(np.sign(strat_med) == np.sign(base_med))), 4),
                'stratified_p05': round(float(np.percentile(strat_med, 5)), 4),
                'stratified_p95': round(float(np.percentile(strat_med, 95)), 4),
                'stratified_verdict': verdict(float(np.mean(np.sign(strat_med) == np.sign(base_med))))}
        sims = None

    # deviation 5: the claims the concentration study actually stands behind, on the same draws
    claims = {}
    if rows:
        per = {r['material']: per_material[r['material']] for r in rows}
        ex = [m for m in per if m in EU_CRM_2011]
        if ex:
            base_ex = float(np.median([next(r['recomputed_change'] for r in rows if r['material'] == m)
                                       for m in ex]))
            draws_ex = np.median(np.vstack([per[m] for m in ex]), axis=0)
            claims['ex_ante_2011'] = {
                'materials': sorted(ex), 'n_tested': len(ex), 'n_in_claim': len(EU_CRM_2011),
                'published_median_change': round(base_ex, 4),
                'share_same_sign': round(float(np.mean(np.sign(draws_ex) == np.sign(base_ex))), 4),
                'p05': round(float(np.percentile(draws_ex, 5)), 4),
                'p95': round(float(np.percentile(draws_ex, 95)), 4),
                'verdict': verdict(float(np.mean(np.sign(draws_ex) == np.sign(base_ex))))}
        down = [m for m in DIVERGENCE_DOWN if m in per]
        if DIVERGENCE_UP in per and down:
            up_draws = per[DIVERGENCE_UP]
            down_draws = np.median(np.vstack([per[m] for m in down]), axis=0)
            both = float(np.mean((up_draws > 0) & (down_draws < 0)))
            claims['divergence'] = {
                'up': DIVERGENCE_UP, 'down': sorted(down),
                'share_both_hold': round(both, 4),
                'share_up_holds': round(float(np.mean(up_draws > 0)), 4),
                'share_down_holds': round(float(np.mean(down_draws < 0)), 4),
                'verdict': verdict(both)}

    res = {'filing': 'self-audit/PREREGISTRATION.md', 'draws': DRAWS, 'seed': SEED,
           'claims': claims,
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
    for k, v in claims.items():
        print('%-14s %s' % (k, {kk: vv for kk, vv in v.items() if kk != 'materials'}))
    print('tested %d, excluded %d' % (len(rows), len(excluded)))


if __name__ == '__main__':
    main()
