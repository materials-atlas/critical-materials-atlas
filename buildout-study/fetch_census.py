# -*- coding: utf-8 -*-
"""Amendment C: fetch US general imports (Census international trade API) for the study's lines.

One call per six-digit line per year, ten-digit detail, all origin countries, all months of that year.
Writes buildout-study/us_data/census_<line>_<year>.parquet. Resumable. The API key is read from
pipeline/.census_key (gitignored) and is never printed or written anywhere. Census data are US
government works (public domain). Network fetcher: named fetch_* so the runner never runs it.

Usage:  python buildout-study/fetch_census.py [--start 2012] [--end 2026]
"""
import argparse
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
LINES6 = ['850421', '850422', '850423', '722511', '722611',
          '842810', '842649', '847420', '847431', '851531', '851539',
          '850152', '850153', '841370', '841480']
FIELDS = ['CTY_CODE', 'CTY_NAME', 'I_COMMODITY', 'GEN_VAL_MO', 'GEN_QY1_MO', 'GEN_QY2_MO',
          'UNIT_QY1', 'UNIT_QY2', 'SUMMARY_LVL']
LAST = '2026-07'


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
                    url, headers={'User-Agent': 'critical-materials-atlas/buildout-study'}), timeout=300) as r:
                body = r.read()
            if not body.strip():
                return []                                     # Census returns an empty body for no rows
            return json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code == 204:
                return []
            reason = 'HTTP %d' % e.code
        except Exception as e:
            reason = type(e).__name__
        # never log the URL: it carries the key
        log('  retry %d (%s)' % (i + 1, reason))
        time.sleep(8 * (i + 1))
    raise RuntimeError('Census call failed after %d tries' % tries)


def one(line, year):
    out = os.path.join(OUTDIR, 'census_%s_%d.parquet' % (line, year))
    if os.path.exists(out):
        return 'skip'
    last_m = 7 if year == 2026 else 12
    rows = get({'get': ','.join(FIELDS), 'COMM_LVL': 'HS10', 'I_COMMODITY': line + '*',
                'time': 'from %d-01 to %d-%02d' % (year, year, last_m), 'key': key()})
    if rows:
        d = pd.DataFrame(rows[1:], columns=rows[0])
        d['month'] = d['time'].str.replace('-', '')
    else:
        d = pd.DataFrame(columns=FIELDS + ['time', 'month'])
    d.to_parquet(out + '.part', index=False)
    os.replace(out + '.part', out)
    log('%s %d  %d rows' % (line, year, len(d)))
    return len(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=2012)
    ap.add_argument('--end', type=int, default=2026)
    ap.add_argument('--lines', default=','.join(LINES6))
    a = ap.parse_args()
    for year in range(a.start, a.end + 1):
        for line in a.lines.split(','):
            try:
                one(line, year)
            except Exception as e:
                log('%s %d  FAILED %s' % (line, year, type(e).__name__))
    have = [f for f in os.listdir(OUTDIR) if f.endswith('.parquet')]
    log('done: %d line-years on disk' % len(have))


if __name__ == '__main__':
    sys.exit(main())
