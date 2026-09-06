# -*- coding: utf-8 -*-
"""Fetch OECD-ITIC: published CIF/FOB margins by importer, exporter, product and year.

WHY THIS REPLACES WHAT WE BUILT
Everything the pipeline does to estimate a freight coefficient - the per-product medians, the
borrowed CEPII 2008 coefficients, the locally-set anchor, the ceiling of our own invention -
exists only because we believed no current published series covered it. One does.

  OECD International Transport and Insurance Costs of merchandise trade (ITIC)
  CIF/FOB margins, % of import CIF value, by REF_AREA (importer) x COUNTERPART_AREA (exporter)
  x HS2017 heading x year, 200+ economies, 1995-2022.
  Method: reported CIF and FOB from ~30 economies, gravity model for the rest - CEPII's design,
  maintained eighteen years past the dataset it descends from.

THE ENDPOINT, because it cost an hour to find. The documented public SDMX host faults on this
dataflow: /public/rest/data/ returns "doesn't contain a mapping set" on v1.0 and a null-reference
error on v1.1. The Data Explorer reaches the data on a DIFFERENT path - /sti-public/ - which
works. The structure endpoints work on both. Watching the browser's own network traffic was the
only way to find that; no documentation mentions it.

    https://sdmx.oecd.org/sti-public/rest/data/OECD.SDD.TPS,DSD_ITIC@DF_ITIC,1.1/<key>

GRAIN: products are HS2017 HEADINGS (4-digit). HS17_2602 returns data; HS17_260200 returns 404.
So a 6-digit code inherits its 4-digit parent's margin, which is stated wherever it is used.

Run:  python fetch_itic.py
"""
import csv, io, json, os, sys, time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'raw', 'oecd_itic')
BASE = ('https://sdmx.oecd.org/sti-public/rest/data/'
        'OECD.SDD.TPS,DSD_ITIC@DF_ITIC,1.1/')
YEARS = (2018, 2022)   # ITIC's latest release ends at 2022


def hs4_codes():
    """The HS4 headings our own trade data actually uses."""
    import pandas as pd
    f = pd.read_parquet(os.path.join(HERE, 'data', 'flows.parquet'), columns=['hs6'])
    return sorted({str(h)[:4] for h in f.hs6.dropna().unique() if len(str(h)) >= 4})


def fetch(hs4):
    url = (BASE + '..C_F.C.HS17_%s..?startPeriod=%d&endPeriod=%d&format=csvfile'
           % (hs4, YEARS[0], YEARS[1]))
    req = urllib.request.Request(url, headers={'User-Agent': 'critical-materials-atlas'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read().decode('utf-8')
    except Exception as e:
        return None if '404' in str(e) else ('ERROR ' + str(e))


def main():
    os.makedirs(OUT, exist_ok=True)
    codes = hs4_codes()
    print('HS4 headings used by our trade data: %d' % len(codes))
    rows, missing, errors = [], [], []
    for i, c in enumerate(codes, 1):
        txt = fetch(c)
        if txt is None:
            missing.append(c)
            print('  %-5s no data' % c)
        elif txt.startswith('ERROR'):
            errors.append((c, txt[:80]))
            print('  %-5s %s' % (c, txt[:60]))
        else:
            r = list(csv.DictReader(io.StringIO(txt)))
            rows.extend(r)
            print('  %-5s %6d observations' % (c, len(r)))
        time.sleep(0.4)

    path = os.path.join(OUT, 'itic_margins.csv')
    if rows:
        keep = ['REF_AREA', 'COUNTERPART_AREA', 'COMM_HS2017', 'TIME_PERIOD', 'OBS_VALUE',
                'OBS_STATUS', 'METHODOLOGY_TYPE', 'UNIT_MEASURE']
        with open(path, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keep)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, '') for k in keep})
    meta = {
        'source': 'OECD International Transport and Insurance Costs of merchandise trade (ITIC)',
        'dataflow': 'OECD.SDD.TPS:DSD_ITIC@DF_ITIC(1.1)',
        'endpoint': BASE + '  (NOTE: /sti-public/, not the documented /public/ - that path '
                           'faults on this dataflow)',
        'measure': 'C_F, CIF/FOB margin, unit PT_IM_CIF = percent of import CIF value',
        'grain': 'REF_AREA = importer, COUNTERPART_AREA = exporter, COMM_HS2017 = HS2017 HEADING '
                 '(4-digit; 6-digit returns 404), annual',
        'years': list(YEARS), 'rows': len(rows),
        'hs4_requested': len(codes), 'hs4_missing': missing, 'errors': errors,
        'obs_status_note': 'I = imputed by the gravity model; reported values are flagged '
                           'differently. METHODOLOGY_TYPE ME = model estimate, AG = aggregate.',
        'retrieved_at': time.strftime('%Y-%m-%d'),
    }
    json.dump(meta, open(os.path.join(OUT, 'SOURCE.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print('\nwrote %s: %d observations across %d headings (%d had none)'
          % (os.path.relpath(path, ROOT), len(rows), len(codes) - len(missing), len(missing)))


if __name__ == '__main__':
    main()
