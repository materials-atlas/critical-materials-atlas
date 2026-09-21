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
    json.dump(o, open(OUT, 'w', encoding='utf-8'), indent=1)


if __name__ == '__main__':
    main()
