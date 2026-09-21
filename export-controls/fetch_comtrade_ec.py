# -*- coding: utf-8 -*-
"""Amendment A, part B: the transit candidates' own monthly imports from China, from UN Comtrade.

Candidates from origins.py (out/export_controls_origins.json): Malaysia for antimony, the Republic of
Korea for bismuth. Imports reported by the candidate, partner China (156), January 2022 to July 2026,
HS 811010 (unwrought antimony) and the HS 8106 bismuth lines (810600 before HS 2022, 810610 and 810690
after). Totals only (motCode=0, customsCode=C00, partner2Code=0), six months per call.

The key is read by pipeline/adapter_comtrade.py from pipeline/.comtrade_key and never printed. Raw
records go only to export-controls/comtrade/ (gitignored) and are never redistributed. Network
fetcher: named fetch_* so the runner never runs it.  Usage: python export-controls/fetch_comtrade_ec.py
"""
import json
import os
import sys
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import adapter_comtrade as ct                                  # noqa: E402  _get, BASE, key

OUTDIR = os.path.join(HERE, 'comtrade')
CANDIDATES = {458: ['811010'], 410: ['810600', '810610', '810690']}   # Malaysia: antimony; Korea: bismuth
MONTHS = ['%d%02d' % (y, m) for y in range(2022, 2027) for m in range(1, 13) if '%d%02d' % (y, m) <= '202607']
BLOCKS = [MONTHS[i:i + 6] for i in range(0, len(MONTHS), 6)]
FIELDS = ('reporterCode', 'partnerCode', 'cmdCode', 'flowCode', 'period', 'primaryValue', 'netWgt',
          'qtyUnitAbbr', 'qty', 'isReported')


def main():
    if not ct.API_KEY:
        sys.exit('no Comtrade key')
    os.makedirs(OUTDIR, exist_ok=True)
    rows = []
    for rep, codes in CANDIDATES.items():
        for b in BLOCKS:
            q = ('%s?reporterCode=%d&partnerCode=156&period=%s&cmdCode=%s&flowCode=M&motCode=0&customsCode=C00'
                 '&partner2Code=0' % (ct.BASE, rep, ','.join(b), ','.join(codes)))
            data = ct._get(q)
            time.sleep(ct._PAUSE)
            recs = (data or {}).get('data', []) or []
            print(rep, b[0], b[-1], 'rows', len(recs) if data is not None else 'FAILED', flush=True)
            rows += [{f: r.get(f) for f in FIELDS} for r in recs]
    pd.DataFrame(rows).to_parquet(os.path.join(OUTDIR, 'candidates_from_china.parquet'), index=False)
    print('rows', len(rows))


if __name__ == '__main__':
    main()
