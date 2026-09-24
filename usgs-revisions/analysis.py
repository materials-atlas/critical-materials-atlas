# -*- coding: utf-8 -*-
"""How much the USGS revises its own production figures, as filed in usgs-revisions/PREREGISTRATION.md.

Also computes the two descriptive panels the same page carries:
  - the mine-against-refinery split by country (one source, the same table);
  - where USGS and BGS disagree on the same measure and year.

Writes out/usgs_revisions.json. Committed before its first run.
Usage: python usgs-revisions/analysis.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import usgs_mcs_cube as U                                     # noqa: E402

OUT = os.path.join(ROOT, 'out', 'usgs_revisions.json')
FLOWS = ('mine', 'refinery', 'smelter')
# The six the filing names. The panel behind it now holds more (the store is a general layer), but
# widening the study is a scope change and belongs in an amendment, not in a quiet rerun.
FILED = ('copper', 'tungsten', 'antimony', 'graphite', 'cobalt', 'rare_earths')
BANDS = [(0.02, 'firm'), (0.05, 'soft'), (float('inf'), 'weak')]
UP_SHARE = 0.60
BGS_FORMS = {'copper': ('copper, mine', 'copper, refined'), 'antimony': ('antimony, mine', 'antimony, refined'),
             'cobalt': ('cobalt, mine', 'cobalt, refined'), 'graphite': ('graphite', None),
             'tungsten': ('tungsten, mine', None), 'rare_earths': ('rare earth oxides', None)}


def store():
    d = pd.read_parquet(os.path.join(ROOT, 'pipeline', 'data', 'usgs_mcs_history.parquet'))
    d = d[d.measure.isin(FLOWS) & d.year.notna() & d.commodity.isin(FILED)].copy()
    # compare in tonnes: a chapter that switched from thousand tonnes to tonnes is not a revision
    d['v'] = d.value_t.where(d.value_t.notna(), d.value)
    d['year'] = d.year.astype(int)
    return d


def revisions(d):
    """One row per commodity, series and year with at least two editions reporting it."""
    rows, dropped, one_edition, flagged = [], 0, 0, 0
    keys = ['commodity', 'measure', 'row_kind', 'iso3', 'country_name_raw', 'year']
    for k, g in d.groupby(keys, dropna=False):
        if k[2] not in ('country', 'world_printed'):
            continue
        g = g.sort_values('edition_year')
        n_all = g.edition_year.nunique()
        g = g[g.v.notna() & (g.flag.isna())]
        if len(g) < 2 or not g.v.iloc[0]:
            dropped += 1
            # the two reasons are different and were reported as one: a series printed in only one
            # edition (the newest data year, or a year either side of a gap in the cached editions)
            # could never have been measured; a flagged one lost its printings to a dash, W or NA
            if n_all < 2:
                one_edition += 1
            else:
                flagged += 1
            continue
        first, latest = float(g.v.iloc[0]), float(g.v.iloc[-1])
        second = float(g.v.iloc[1])
        rows.append({'commodity': k[0], 'measure': k[1], 'row_kind': k[2], 'iso3': k[3],
                     'country': k[4], 'year': k[5], 'editions': int(len(g)),
                     'first_edition': int(g.edition_year.iloc[0]), 'latest_edition': int(g.edition_year.iloc[-1]),
                     'first': first, 'latest': latest,
                     'revision': (latest - first) / first,
                     'after_first_revision': (latest - second) / second if second else None})
    return pd.DataFrame(rows), {'total': dropped, 'only_one_edition': one_edition,
                                'lost_to_a_flag': flagged}


def band(x):
    for lim, name in BANDS:
        if x < lim:
            return name
    return 'weak'


def summarise(r):
    out = {}
    for c, g in r.groupby('commodity'):
        w = g[(g.row_kind == 'world_printed') & (g.measure == 'mine')]
        cn = g[(g.iso3 == 'CHN') & (g.measure == 'mine')]
        med_w = float(w.revision.abs().median()) if len(w) else None
        mine = g[g.measure == 'mine']
        # up, down and UNCHANGED are three different things: a reprint that does not move is not a
        # revision down, and unchanged reprints are common here (China's rare earths)
        up = float((mine.revision > 0).mean()) if len(mine) else None
        down = float((mine.revision < 0).mean()) if len(mine) else None
        same = float((mine.revision == 0).mean()) if len(mine) else None
        settle = g[(g.row_kind == 'world_printed') & (g.measure == 'mine')].after_first_revision.abs()
        out[c] = {
            'world_median_abs_revision': med_w,
            'world_years': int(len(w)),
            'world_max_abs_revision': float(w.revision.abs().max()) if len(w) else None,
            'china_median_abs_revision': float(cn.revision.abs().median()) if len(cn) else None,
            'china_years': int(len(cn)),
            'country_median_abs_revision': float(g[g.row_kind == 'country'].revision.abs().median()),
            'share_revised_up': up, 'share_revised_down': down, 'share_unchanged': same,
            'share_revised_up_over': 'every mine series in the commodity: each country and the '
                                     'printed world total',
            'direction': ('revised up more often than down' if up is not None and up >= UP_SHARE else
                          'revised down more often than up' if down is not None and down >= UP_SHARE else
                          'no consistent direction'),
            'band': band(med_w) if med_w is not None else None,
            # deviation 3: not computable. Each data year is printed exactly twice in this series, so
            # there is no third printing to settle towards; the count of years with three or more
            # editions is reported instead of a number that would always be zero.
            'years_with_three_or_more_editions': int((g[(g.row_kind == 'world_printed') &
                                                        (g.measure == 'mine')].editions >= 3).sum()),
            'editions_per_measurable_year': 2,
            # deviation 2: the same medians over the last ten data years, added after seeing that the
            # largest revisions are from the 1990s. Descriptive; the filed headline is unchanged.
            'world_median_abs_revision_recent': (float(w[w.year >= w.year.max() - 9].revision.abs().median())
                                                 if len(w[w.year >= w.year.max() - 9]) else None),
            'recent_years': ([int(w[w.year >= w.year.max() - 9].year.min()),
                              int(w.year.max())] if len(w) else None),
            'band_recent': (band(float(w[w.year >= w.year.max() - 9].revision.abs().median()))
                            if len(w[w.year >= w.year.max() - 9]) else None),
        }
    return out


def mine_vs_refine(d):
    """China and the top refiners against their mine share, newest year each commodity reports both."""
    out = {}
    for c in sorted(d.commodity.unique()):
        p_mine, p_ref = U.panel(c, 'mine'), U.panel(c, 'refinery')
        # both stages, with years, or the pair says nothing: indium is refinery-only here
        if p_ref.empty or p_mine.empty or p_ref.year.isna().all() or p_mine.year.isna().all():
            continue
        year = int(min(p_mine.year.max(), p_ref.year.max()))
        w_mine, w_ref = U.world(c, 'mine'), U.world(c, 'refinery')

        def tot(w):
            s = w[w.year == year].world_printed
            return float(s.iloc[0]) if len(s) else None
        tm, tr = tot(w_mine), tot(w_ref)
        if not tm or not tr:
            continue
        rows = []
        for iso in sorted(set(p_mine[p_mine.year == year].iso3) | set(p_ref[p_ref.year == year].iso3)):
            if not iso:
                continue
            mrow = p_mine[(p_mine.year == year) & (p_mine.iso3 == iso)]
            rrow = p_ref[(p_ref.year == year) & (p_ref.iso3 == iso)]
            m, r = mrow.value, rrow.value
            # the chapter prints a dash, not a zero, where a country does not mine at all
            mine_flag = mrow.flag.iloc[0] if len(mrow) and pd.notna(mrow.flag.iloc[0]) else None
            ref_flag = rrow.flag.iloc[0] if len(rrow) and pd.notna(rrow.flag.iloc[0]) else None
            rows.append({'iso3': iso,
                         'country': (p_ref[(p_ref.year == year) & (p_ref.iso3 == iso)].country_name_raw.iloc[0]
                                     if len(r) else p_mine[(p_mine.year == year) & (p_mine.iso3 == iso)].country_name_raw.iloc[0]),
                         'mine': float(m.iloc[0]) if len(m) else None,
                         'refinery': float(r.iloc[0]) if len(r) else None,
                         'mine_share': float(m.iloc[0]) / tm if len(m) else None,
                         'refinery_share': float(r.iloc[0]) / tr if len(r) else None,
                         'mine_printed': 'dash' if mine_flag == 'zero' else None,
                         'refinery_printed': 'dash' if ref_flag == 'zero' else None})
        out[c] = {'year': year, 'world_mine': tm, 'world_refinery': tr,
                  'rows': sorted(rows, key=lambda x: -(x['refinery_share'] or 0))}
    return out


def bgs_compare(d):
    """USGS against BGS on the same commodity, measure and year - levels, not directions."""
    out = {}
    for c, (mine_form, ref_form) in BGS_FORMS.items():
        path = os.path.join(ROOT, 'raw', 'bgs', 'panel', '%s.json' % ('rare_earths' if c == 'rare_earths' else c))
        if not os.path.exists(path):
            continue
        b = pd.DataFrame(json.load(open(path, encoding='utf-8')))
        if b.empty:
            continue
        b['year'] = b.year.str[:4].astype(int)
        for measure, form in (('mine', mine_form), ('refinery', ref_form)):
            if not form:
                continue
            # production only: the BGS panel carries Imports and Exports rows under the same form,
            # and summing them made graphite's "world production" the sum of all three
            bb = b[(b.bgs_commodity_trans == form) &
                   (b.bgs_statistic_type_trans.str.lower() == 'production')]
            if bb.empty:
                continue
            w = U.world(c, measure)
            if w.empty or 'world_printed' not in w:
                continue
            p = U.panel(c, measure)
            recs = []
            for y in sorted(set(w.year) & set(bb.year)):
                if y < 2002:
                    continue
                bw = float(bb[bb.year == y].quantity.sum())
                n_rep = int(bb[(bb.year == y) & (bb.quantity > 0)].country_iso3_code.nunique())
                uw = float(w[w.year == y].world_printed.iloc[0])
                # in tonnes, from the very row that printed it: deriving a factor from another
                # edition applied 1,000 to a graphite figure already in tonnes (a 1000x error in the
                # 2017 row of the published output)
                wr = d[(d.commodity == c) & (d.measure == measure) & (d.year == y) &
                       (d.row_kind == 'world_printed')].sort_values('edition_year')
                uw_t = float(wr.v.iloc[-1]) if len(wr) and pd.notna(wr.v.iloc[-1]) else None
                bc = float(bb[(bb.year == y) & (bb.country_iso3_code == 'CHN')].quantity.sum())
                uc = p[(p.year == y) & (p.iso3 == 'CHN')]
                uc_v = float(uc.value_t.iloc[0]) if len(uc) and pd.notna(uc.value_t.iloc[0]) else (
                    float(uc.value.iloc[0]) if len(uc) else None)
                if uw_t and bw:
                    recs.append({'year': int(y), 'bgs_countries_reporting': n_rep,
                                 'usgs_world_t': uw_t, 'bgs_world_t': bw,
                                 'world_gap': uw_t / bw - 1,
                                 'usgs_china_t': uc_v, 'bgs_china_t': bc if bc else None,
                                 'china_gap': (uc_v / bc - 1) if (uc_v and bc) else None})
            if recs:
                med_rep = float(np.median([r['bgs_countries_reporting'] for r in recs]))
                # what the median would have been under the conversion this code used before
                # deviation 8: a factor taken from an arbitrary country row of another edition. Kept so
                # the size of that fault is on the record rather than asserted from memory.
                old = []
                for r in recs:
                    cc = d[(d.commodity == c) & (d.measure == measure) & (d.year == r['year']) &
                           d.value_t.notna() & (d.value != 0)]
                    wr = d[(d.commodity == c) & (d.measure == measure) & (d.year == r['year']) &
                           (d.row_kind == 'world_printed')].sort_values('edition_year')
                    if len(cc) and len(wr):
                        f = float(cc.value_t.iloc[0]) / float(cc.value.iloc[0])
                        old.append(abs(float(wr.value.iloc[-1]) * f / r['bgs_world_t'] - 1))
                    else:
                        old.append(abs(r['world_gap']))
                # how many countries the USGS table itself carries with a positive figure, so the page
                # can compare like with like instead of quoting a remembered number
                up = U.panel(c, measure)
                usgs_rep = [int(((up.year == r['year']) & (up.value > 0)).sum()) for r in recs]
                out['%s_%s' % (c, measure)] = {
                    'bgs_form': form, 'years': [recs[0]['year'], recs[-1]['year']],
                    'bgs_median_countries_reporting': med_rep,
                    'usgs_countries_with_output': [int(min(usgs_rep)), int(max(usgs_rep))],
                    'median_abs_world_gap_before_unit_fix': float(np.median(old)),
                    # a BGS form with almost no reporters is a residual category, not the same basket:
                    # 'rare earths' carries one country while 'rare earth oxides' carries nine
                    'bgs_rows': 'production only',
                    'like_for_like': bool(med_rep >= 3),
                    'median_abs_world_gap': float(np.median([abs(r['world_gap']) for r in recs])),
                    'median_abs_china_gap': float(np.median([abs(r['china_gap']) for r in recs
                                                             if r['china_gap'] is not None])) if any(
                        r['china_gap'] is not None for r in recs) else None,
                    'rows': recs}
    return out


def main():
    d = store()
    r, dropped = revisions(d)
    full = pd.read_parquet(os.path.join(ROOT, 'pipeline', 'data', 'usgs_mcs_history.parquet'))
    res = {'filing': 'usgs-revisions/PREREGISTRATION.md',
           # counted over the commodities this study measures, not the whole store: the panel now
           # holds more commodities than the study covers, and the page quotes these numbers
           'chapters_read': int(full[full.commodity.isin(d.commodity.unique())]
                                .groupby(['commodity', 'edition_year']).ngroups),
           'country_series': int(full[(full.row_kind == 'country') & full.iso3.notna() & full.year.notna() &
                                      full.commodity.isin(d.commodity.unique())]
                                 .groupby(['commodity', 'measure', 'iso3', 'year']).ngroups),
           'commodities_measured': sorted(d.commodity.unique().tolist()),
           'store_commodities': sorted(full.commodity.unique().tolist()),
           'store': 'pipeline/data/usgs_mcs_history.parquet',
           'editions': U.editions(), 'series_dropped': dropped,
           'measurable_series': int(len(r)),
           'latest_year_excluded': {c: int(g.year.max()) + 1 for c, g in r.groupby('commodity')},
           'by_commodity': summarise(r),
           'mine_vs_refine': mine_vs_refine(d),
           'usgs_vs_bgs': bgs_compare(d)}
    # the biggest single revisions, for the page to name
    big = r.reindex(r.revision.abs().sort_values(ascending=False).index).head(12)
    res['largest_revisions'] = [{k: (int(v) if isinstance(v, (np.integer,)) else
                                     float(v) if isinstance(v, (np.floating,)) else v)
                                 for k, v in row.items()} for row in big.to_dict('records')]
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1, default=float)
    print('measurable series %d (dropped %d: %d one edition, %d lost to a flag)'
          % (len(r), dropped['total'], dropped['only_one_edition'], dropped['lost_to_a_flag']))
    for c, s in res['by_commodity'].items():
        print('%-12s world median |rev| %5.1f%% over %2d years (max %5.1f%%), China %5.1f%%, up %3.0f%% -> %s [%s]'
              % (c, 100 * (s['world_median_abs_revision'] or 0), s['world_years'],
                 100 * (s['world_max_abs_revision'] or 0), 100 * (s['china_median_abs_revision'] or 0),
                 100 * (s['share_revised_up'] or 0), s['direction'], s['band']))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
