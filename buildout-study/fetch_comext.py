# -*- coding: utf-8 -*-
"""Amendment B: fetch the EU customs record (Eurostat Comext monthly, CN8) for the study's lines.

For each month from 2012-01 to the latest published, downloads full_v2_YYYYMM.7z, extracts it, keeps
only rows whose eight-digit product code belongs to one of the study's six-digit lines, writes that to
buildout-study/eu_data/comext_YYYYMM.parquet, and deletes the archive and the extracted file, so the
disk never holds more than one raw month. Resumable: a month whose parquet exists is skipped.

Eurostat data, reused under the Commission's reuse policy (CC BY 4.0). Network fetcher: the runner
must never run it.

Usage:  python buildout-study/fetch_comext.py [--start 201201] [--end 202607]
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
LOG = os.path.join(HERE, 'eu_data', 'fetch.log')
DIR_URL = 'https://ec.europa.eu/eurostat/api/dissemination/files?dir=comext%2FCOMEXT_DATA%2FPRODUCTS'
FILE_URL = 'https://ec.europa.eu/eurostat/api/dissemination/files?file=comext%2FCOMEXT_DATA%2FPRODUCTS%2F'
LINES6 = ['850421', '850422', '850423', '722511', '722611',
          '842810', '842649', '847420', '847431', '851531', '851539',
          '850152', '850153', '841370', '841480']
KEEP = ['REPORTER', 'PARTNER', 'TRADE_TYPE', 'PRODUCT_NC', 'FLOW', 'STAT_PROCEDURE', 'SUPPL_UNIT',
        'PERIOD', 'VALUE_EUR', 'QUANTITY_KG', 'QUANTITY_SUPPL_UNIT']


def log(msg):
    os.makedirs(OUTDIR, exist_ok=True)
    line = '%s  %s' % (datetime.datetime.now().isoformat(timespec='seconds'), msg)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    print(line, flush=True)


def fetch(url, path=None, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'critical-materials-atlas/buildout-study'})
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
    return sorted(set(re.findall(r'full_v2_(\d{6})\.7z', listing)))


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
    dat = dats[0]
    like = ' or '.join("PRODUCT_NC like '%s%%'" % c for c in LINES6)
    con = duckdb.connect()
    tmp_out = out + '.part'
    con.execute("""copy (select %s from read_csv(?, header=true, all_varchar=true) where %s)
                   to '%s' (format parquet)""" % (', '.join(KEEP), like, tmp_out.replace('\\', '/')), [dat])
    n = con.execute("select count(*) from read_parquet('%s')" % tmp_out.replace('\\', '/')).fetchone()[0]
    con.close()
    os.replace(tmp_out, out)
    for f in os.listdir(TMP):
        os.remove(os.path.join(TMP, f))
    log('%s  %d rows  %.0fs' % (ym, n, time.time() - t0))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='201201')
    ap.add_argument('--end', default=None)
    a = ap.parse_args()
    avail = months_available()
    todo = [m for m in avail if m >= a.start and (a.end is None or m <= a.end)]
    log('months to consider: %d (%s to %s)' % (len(todo), todo[0], todo[-1]))
    for ym in todo:
        try:
            one_month(ym)
        except Exception as e:
            log('%s  FAILED %s: %s' % (ym, type(e).__name__, e))
    shutil.rmtree(TMP, ignore_errors=True)
    have = sorted(f[7:13] for f in os.listdir(OUTDIR) if f.startswith('comext_') and f.endswith('.parquet'))
    missing = [m for m in todo if m not in have]
    log('done: %d months on disk, missing %s' % (len(have), missing or 'none'))


if __name__ == '__main__':
    sys.exit(main())
