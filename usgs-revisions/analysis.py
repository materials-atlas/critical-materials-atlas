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
BANDS = [(0.02, 'firm'), (0.05, 'soft'), (float('inf'), 'weak')]
UP_SHARE = 0.60
BGS_FORMS = {'copper': ('copper, mine', 'copper, refined'), 'antimony': ('antimony, mine', 'antimony, refined'),
             'cobalt': ('cobalt, mine', 'cobalt, refined'), 'graphite': ('graphite', None),
             'tungsten': ('tungsten, mine', None), 'rare_earths': ('rare earth minerals', None)}


def store():
    d = pd.read_parquet(os.path.join(ROOT, 'pipeline', 'data', 'usgs_mcs_history.parquet'))
    d = d[d.measure.isin(FLOWS) & d.year.notna()].copy()
    # compare in tonnes: a chapter that switched from thousand tonnes to tonnes is not a revision
    d['v'] = d.value_t.where(d.value_t.notna(), d.value)
    d['year'] = d.year.astype(int)
    return d


def revisions(d):
    """One row per commodity, series and year with at least two editions reporting it."""
    rows, dropped = [], 0
    keys = ['commodity', 'measure', 'row_kind', 'iso3', 'country_name_raw', 'year']
    for k, g in d.groupby(keys, dropna=False):
        if k[2] not in ('country', 'world_printed'):
            continue
        g = g.sort_values('edition_year')
        g = g[g.v.notna() & (g.flag.isna())]
        if len(g) < 2 or not g.v.iloc[0]:
            dropped += 1
            continue
        first, latest = float(g.v.iloc[0]), float(g.v.iloc[-1])
        second = float(g.v.iloc[1])
        rows.append({'commodity': k[0], 'measure': k[1], 'row_kind': k[2], 'iso3': k[3],
                     'country': k[4], 'year': k[5], 'editions': int(len(g)),
                     'first_edition': int(g.edition_year.iloc[0]), 'latest_edition': int(g.edition_year.iloc[-1]),
                     'first': first, 'latest': latest,
                     'revision': (latest - first) / first,
                     'after_first_revision': (latest - second) / second if second else None})
    return pd.DataFrame(rows), dropped


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
        up = float((g[g.measure == 'mine'].revision > 0).mean()) if len(g[g.measure == 'mine']) else None
        settle = g[(g.row_kind == 'world_printed') & (g.measure == 'mine')].after_first_revision.abs()
        out[c] = {
            'world_median_abs_revision': med_w,
            'world_years': int(len(w)),
            'world_max_abs_revision': float(w.revision.abs().max()) if len(w) else None,
            'china_median_abs_revision': float(cn.revision.abs().median()) if len(cn) else None,
            'china_years': int(len(cn)),
            'country_median_abs_revision': float(g[g.row_kind == 'country'].revision.abs().median()),
            'share_revised_up': up,
            'direction': ('revised up more often than down' if up is not None and up >= UP_SHARE else
                          'revised down more often than up' if up is not None and up <= 1 - UP_SHARE else
                          'no consistent direction'),
            'band': band(med_w) if med_w is not None else None,
            'median_abs_change_after_first_revision': float(settle.median()) if settle.notna().any() else None,
        }
    return out


def mine_vs_refine(d):
    """China and the top refiners against their mine share, newest year each commodity reports both."""
    out = {}
    for c in sorted(d.commodity.unique()):
        p_mine, p_ref = U.panel(c, 'mine'), U.panel(c, 'refinery')
        if p_ref.empty:
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
            m = p_mine[(p_mine.year == year) & (p_mine.iso3 == iso)].value
            r = p_ref[(p_ref.year == year) & (p_ref.iso3 == iso)].value
            rows.append({'iso3': iso,
                         'country': (p_ref[(p_ref.year == year) & (p_ref.iso3 == iso)].country_name_raw.iloc[0]
                                     if len(r) else p_mine[(p_mine.year == year) & (p_mine.iso3 == iso)].country_name_raw.iloc[0]),
                         'mine': float(m.iloc[0]) if len(m) else None,
                         'refinery': float(r.iloc[0]) if len(r) else None,
                         'mine_share': float(m.iloc[0]) / tm if len(m) else None,
                         'refinery_share': float(r.iloc[0]) / tr if len(r) else None})
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
            bb = b[b.bgs_commodity_trans == form]
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
                uw = float(w[w.year == y].world_printed.iloc[0])
                bc = float(bb[(bb.year == y) & (bb.country_iso3_code == 'CHN')].quantity.sum())
                uc = p[(p.year == y) & (p.iso3 == 'CHN')]
                uc_v = float(uc.value_t.iloc[0]) if len(uc) and pd.notna(uc.value_t.iloc[0]) else (
                    float(uc.value.iloc[0]) if len(uc) else None)
                # the world total is printed in the chapter's unit; convert with the same factor a
                # country row used, so both sides are tonnes
                f = None
                cc = d[(d.commodity == c) & (d.measure == measure) & (d.year == y) & d.value_t.notna()]
                if len(cc):
                    f = float(cc.value_t.iloc[0]) / float(cc.value.iloc[0])
                uw_t = uw * f if f else None
                if uw_t and bw:
                    recs.append({'year': int(y), 'usgs_world_t': uw_t, 'bgs_world_t': bw,
                                 'world_gap': uw_t / bw - 1,
                                 'usgs_china_t': uc_v, 'bgs_china_t': bc if bc else None,
                                 'china_gap': (uc_v / bc - 1) if (uc_v and bc) else None})
            if recs:
                out['%s_%s' % (c, measure)] = {
                    'bgs_form': form, 'years': [recs[0]['year'], recs[-1]['year']],
                    'median_abs_world_gap': float(np.median([abs(r['world_gap']) for r in recs])),
                    'median_abs_china_gap': float(np.median([abs(r['china_gap']) for r in recs
                                                             if r['china_gap'] is not None])) if any(
                        r['china_gap'] is not None for r in recs) else None,
                    'rows': recs}
    return out


def main():
    d = store()
    r, dropped = revisions(d)
    res = {'filing': 'usgs-revisions/PREREGISTRATION.md',
           'store': 'pipeline/data/usgs_mcs_history.parquet',
           'editions': U.editions(), 'series_dropped_for_missing_first_value': dropped,
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
    print('measurable series %d (dropped %d)' % (len(r), dropped))
    for c, s in res['by_commodity'].items():
        print('%-12s world median |rev| %5.1f%% over %2d years (max %5.1f%%), China %5.1f%%, up %3.0f%% -> %s [%s]'
              % (c, 100 * (s['world_median_abs_revision'] or 0), s['world_years'],
                 100 * (s['world_max_abs_revision'] or 0), 100 * (s['china_median_abs_revision'] or 0),
                 100 * (s['share_revised_up'] or 0), s['direction'], s['band']))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
