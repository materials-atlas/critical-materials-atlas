# -*- coding: utf-8 -*-
"""Fetch the EU customs record (Eurostat Comext monthly, CN8) for the export-controls and EU grid-supply
studies, 2019-01 to 2026-07.

The page's world figures end in 2024 (CEPII BACI). This extends it from the EU's side: for each month
from 2024-01 to the latest published, downloads full_v2_YYYYMM.7z, keeps only rows whose product code
starts with one of the page's lines, writes ai-buildout/eu_data/comext_YYYYMM.parquet, and deletes the
archive, so the disk never holds more than one raw month. Resumable.

All months are read in HS 2022 (CN 2024-2026), so no code changes underneath the comparison. HS 2022
split 8541.40 into 8541.41-8541.49; the prefix 85414 keeps the whole former line together.

Eurostat data, reused under the Commission's reuse policy (CC BY 4.0). Network fetcher: the runner
must never run it.

Usage:  python ai-buildout/fetch_comext_ai.py [--start 202401] [--end 202607]
"""
import argparse
import datetime
import os
import re
import shutil
import sys
import time
import urllib.request

import duckdb
import py7zr

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, 'eu_data')
TMP = os.path.join(HERE, '_comext_tmp')
LOG = os.path.join(OUTDIR, 'fetch.log')
DIR_URL = 'https://ec.europa.eu/eurostat/api/dissemination/files?dir=comext%2FCOMEXT_DATA%2FPRODUCTS'
FILE_URL = 'https://ec.europa.eu/eurostat/api/dissemination/files?file=comext%2FCOMEXT_DATA%2FPRODUCTS%2F'
PREFIXES = [
    # export-controls: treated
    '81129289', '81129295', '25041000', '85051110', '28053031', '28469060',
    '81101000', '81102000', '81109000', '26171000', '8106',
    # export-controls: comparisons
    '81041100', '81041900', '25262000', '25111000', '85051910', '28469040', '28461000',
    # grid supply
    '850421', '850422', '850423', '72251100', '72261100', '854460', '8535', '85372091', '85372099',
    '85044086', '902830']
KEEP = ['REPORTER', 'PARTNER', 'TRADE_TYPE', 'PRODUCT_NC', 'FLOW', 'PERIOD', 'VALUE_EUR', 'QUANTITY_KG']


def log(msg):
    os.makedirs(OUTDIR, exist_ok=True)
    line = '%s  %s' % (datetime.datetime.now().isoformat(timespec='seconds'), msg)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    print(line, flush=True)


def fetch(url, path=None, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'critical-materials-atlas/export-controls'})
            with urllib.request.urlopen(req, timeout=300) as r:
                if path is None:
                    return r.read()
                with open(path, 'wb') as f:
                    shutil.copyfileobj(r, f, 1 << 20)
                return path
        except Exception as e:
            log('  retry %d after %s: %s' % (i + 1, type(e).__name__, e))
            time.sleep(10 * (i + 1))
    raise RuntimeError('failed: ' + url)


def months_available():
    listing = fetch(DIR_URL).decode('utf-8', 'replace')
    # Months only: the yearly totals (period YYYY52) match the same pattern and would double-count.
    return sorted(m for m in set(re.findall(r'full_v2_(\d{6})\.7z', listing)) if 1 <= int(m[4:]) <= 12)


def one_month(ym):
    out = os.path.join(OUTDIR, 'comext_%s.parquet' % ym)
    if os.path.exists(out):
        return 'skip'
    os.makedirs(TMP, exist_ok=True)
    z = os.path.join(TMP, 'full_v2_%s.7z' % ym)
    t0 = time.time()
    fetch(FILE_URL + 'full_v2_%s.7z' % ym, z)
    with py7zr.SevenZipFile(z) as a:
        a.extractall(TMP)
    dats = [os.path.join(TMP, f) for f in os.listdir(TMP) if f.lower().endswith('.dat')]
    if len(dats) != 1:
        raise RuntimeError('%s: expected one .dat, found %s' % (ym, dats))
    like = ' or '.join("PRODUCT_NC like '%s%%'" % c for c in PREFIXES)
    con = duckdb.connect()
    tmp_out = out + '.part'
    con.execute("""copy (select %s from read_csv(?, header=true, all_varchar=true) where %s)
                   to '%s' (format parquet)""" % (', '.join(KEEP), like, tmp_out.replace('\\', '/')), [dats[0]])
    n = con.execute("select count(*) from read_parquet('%s')" % tmp_out.replace('\\', '/')).fetchone()[0]
    con.close()
    os.replace(tmp_out, out)
    for f in os.listdir(TMP):
        os.remove(os.path.join(TMP, f))
    log('%s  %d rows  %.0fs' % (ym, n, time.time() - t0))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='201901')
    ap.add_argument('--end', default='202607')
    a = ap.parse_args()
    todo = [m for m in months_available() if a.start <= m <= a.end]
    log('months to consider: %d (%s to %s)' % (len(todo), todo[0], todo[-1]))
    for ym in todo:
        try:
            one_month(ym)
        except Exception as e:
            log('%s  FAILED %s: %s' % (ym, type(e).__name__, e))
    shutil.rmtree(TMP, ignore_errors=True)
    have = sorted(f[7:13] for f in os.listdir(OUTDIR) if f.startswith('comext_') and f.endswith('.parquet'))
    log('done: %d months on disk, missing %s' % (len(have), [m for m in todo if m not in have] or 'none'))


if __name__ == '__main__':
    sys.exit(main())
