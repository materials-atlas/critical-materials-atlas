# -*- coding: utf-8 -*-
"""Amendment A, part B: read the transit candidates' own imports from China against the filed rule.

Reads export-controls/comtrade/candidates_from_china.parquet (fetch_comtrade_ec.py) and adds a
'part_b' block to out/export_controls_origins.json. Derived figures only.
Usage: python export-controls/partb.py
"""
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from analysis import CONTROLS, shift, months                  # noqa: E402

OUT = os.path.join(ROOT, 'out', 'export_controls_origins.json')
SRC = os.path.join(HERE, 'comtrade', 'candidates_from_china.parquet')
REPORTER = {'MY': 458, 'KR': 410}
TREATED = {'C5': 'antimony', 'C6': 'bismuth'}


def main():
    o = json.load(open(OUT, encoding='utf-8'))
    d = pd.read_parquet(SRC)
    d['t'] = pd.to_numeric(d.netWgt, errors='coerce') / 1000
    ctl = {c[0]: c for c in CONTROLS if c[1] == 'EU'}
    last = str(d.period.max())
    o['part_b'] = {}
    for cid in ('C5', 'C6'):
        _, _, _, _, ann, eff, _, _ = ctl[cid]
        for par in o['controls'][cid]['transit_candidates']:
            rep = REPORTER[par]
            s = d[d.reporterCode == rep].groupby(d.period.astype(str)).t.sum()
            reported = sorted(set(d[d.reporterCode == rep].period.astype(str)))
            pre = months(shift(ann, -24), shift(ann, -1))
            # months 0-12 after entry into force, as far as the candidate has reported (Comtrade publishes
            # a reporter's months together; a month inside the reported span with no row is no trade)
            post_all = months(eff, shift(eff, 12))
            span_end = max(reported) if reported else None
            post = [m for m in post_all if span_end and m <= span_end]
            pre_m = float(s.reindex(pre).fillna(0).mean())
            post_m = float(s.reindex(post).fillna(0).mean()) if post else None
            if post_m is None:
                reading = 'no answer'
            elif post_m >= 1.5 * pre_m and post_m - pre_m >= 10:
                reading = 'consistent with rerouting'
            else:
                reading = 'not consistent'
            o['part_b']['%s_%s' % (cid, par)] = {
                'control': cid, 'material': TREATED[cid], 'candidate': par, 'reporter_code': rep,
                'imports_from_china_t_month_pre': round(pre_m, 2),
                'imports_from_china_t_month_0_12': round(post_m, 2) if post_m is not None else None,
                'post_months_available': len(post), 'post_months_filed': len(post_all),
                'last_month_reported': span_end, 'reading': reading}
            print(cid, par, o['part_b']['%s_%s' % (cid, par)])
    o['part_b_last_month_in_file'] = last
    # Amendment A deviation 7 (added after review): Korea's bismuth exports, world and by partner, pre-period
    # (24 months before the bismuth announcement) against months 0-10 after entry into force (Feb-Dec 2025,
    # the months Korea has reported). Months with no record inside the span count as zero.
    kx = os.path.join(HERE, 'comtrade', 'korea_bismuth_exports.parquet')
    if os.path.exists(kx):
        _, _, _, _, ann, eff, _, _ = ctl['C6']
        x = pd.read_parquet(kx)
        x['t'] = pd.to_numeric(x.netWgt, errors='coerce') / 1000
        x['p'] = x.period.astype(str)
        rep = sorted(set(x.p))
        pre = [m for m in months(shift(ann, -24), shift(ann, -1))]
        post = [m for m in months(eff, shift(eff, 12)) if m <= rep[-1]]
        EU27 = {40, 56, 100, 191, 196, 203, 208, 233, 246, 251, 276, 300, 348, 372, 380, 428, 440, 442, 470, 528,
                616, 620, 642, 703, 705, 724, 752}
        def mean(sel, ms):
            return float(x[sel].groupby('p').t.sum().reindex(ms).fillna(0).mean())
        o['korea_bismuth_exports'] = {
            'pre': [pre[0], pre[-1]], 'post': [post[0], post[-1]], 'post_months': len(post),
            'world_t_month': [round(mean(x.partnerCode == 0, pre), 1), round(mean(x.partnerCode == 0, post), 1)],
            'usa_t_month': [round(mean(x.partnerCode == 842, pre), 1), round(mean(x.partnerCode == 842, post), 1)],
            'eu27_t_month': [round(mean(x.partnerCode.isin(EU27), pre), 1), round(mean(x.partnerCode.isin(EU27), post), 1)],
            'china_t_month': [round(mean(x.partnerCode == 156, pre), 1), round(mean(x.partnerCode == 156, post), 1)]}
        print('korea exports', o['korea_bismuth_exports'])
    json.dump(o, open(OUT, 'w', encoding='utf-8'), indent=1)


if __name__ == '__main__':
    main()
