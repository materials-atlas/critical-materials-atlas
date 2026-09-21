# -*- coding: utf-8 -*-
"""Fetch US general imports (Census international trade API) for the export-controls study, 2021 to July 2026.

One call per line per year, ten-digit detail, all origin countries. Writes
ai-buildout/us_data/census_<line>_<year>.parquet. Resumable. The API key is read from
pipeline/.census_key (gitignored) and is never printed or logged. Census data are US government works
(public domain). Network fetcher: named fetch_* so the runner never runs it.

Usage:  python ai-buildout/fetch_census_ai.py
"""
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTDIR = os.path.join(HERE, 'us_data')
LOG = os.path.join(OUTDIR, 'fetch.log')
API = 'https://api.census.gov/data/timeseries/intltrade/imports/hs'
PREFIXES = ['811292', '250410', '380110', '850511', '8110', '8106', '810411', '810419',
            '2526', '2511', '850519']
FIELDS = ['CTY_CODE', 'CTY_NAME', 'I_COMMODITY', 'GEN_VAL_MO', 'GEN_QY1_MO', 'UNIT_QY1',
          'GEN_QY2_MO', 'UNIT_QY2', 'SUMMARY_LVL']
YEARS = {2021: 12, 2022: 12, 2023: 12, 2024: 12, 2025: 12, 2026: 7}


def key():
    return open(os.path.join(ROOT, 'pipeline', '.census_key')).read().strip()


def log(msg):
    os.makedirs(OUTDIR, exist_ok=True)
    line = '%s  %s' % (datetime.datetime.now().isoformat(timespec='seconds'), msg)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    print(line, flush=True)


def get(params, tries=6):
    url = API + '?' + urllib.parse.urlencode(params, safe='*,:+')
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={'User-Agent': 'critical-materials-atlas/export-controls'}), timeout=300) as r:
                body = r.read()
            return json.loads(body) if body.strip() else []
        except urllib.error.HTTPError as e:
            if e.code == 204:
                return []
            reason = 'HTTP %d' % e.code
        except Exception as e:
            reason = type(e).__name__
        log('  retry %d (%s)' % (i + 1, reason))                # never log the URL: it carries the key
        time.sleep(8 * (i + 1))
    raise RuntimeError('Census call failed after %d tries' % tries)


def one(line, year, last_m):
    out = os.path.join(OUTDIR, 'census_%s_%d.parquet' % (line, year))
    if os.path.exists(out):
        return 'skip'
    rows = get({'get': ','.join(FIELDS), 'COMM_LVL': 'HS10', 'I_COMMODITY': line + '*',
                'time': 'from %d-01 to %d-%02d' % (year, year, last_m), 'key': key()})
    if rows:
        d = pd.DataFrame(rows[1:], columns=rows[0])
        d = d.loc[:, ~d.columns.duplicated()]                 # the API echoes filter fields as columns
        d['month'] = d['time'].str.replace('-', '')
    else:
        d = pd.DataFrame(columns=FIELDS + ['time', 'month'])
    d.to_parquet(out + '.part', index=False)
    os.replace(out + '.part', out)
    log('%s %d  %d rows' % (line, year, len(d)))
    return len(d)


def main():
    for year, last_m in YEARS.items():
        for line in PREFIXES:
            try:
                one(line, year, last_m)
            except Exception as e:
                log('%s %d  FAILED %s' % (line, year, type(e).__name__))
    log('done: %d line-years on disk' % len([f for f in os.listdir(OUTDIR) if f.endswith('.parquet')]))


if __name__ == '__main__':
    sys.exit(main())
