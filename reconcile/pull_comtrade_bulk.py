# -*- coding: utf-8 -*-
"""Fetch the whole monthly HS6 series through UN Comtrade's BULK endpoint.

This replaces the per-call crawl entirely. The premium access the UN granted on 8 Oct 2026 is
live on the bulk endpoint with the key already in pipeline/.comtrade_key - no new key, no tier
change (the portal still shows the subscription as "free", and the data API still refuses more
than 12 periods, so the per-call route was never going to improve).

Measured 13 Oct 2026, which is what makes this worth doing:

    per-call crawl, whole corpus          783 days   (17.3M rows/day, measured over 3 days)
    bulk transfer, whole corpus           263 GB, about 7 hours at the 10.3 MB/s their
                                          server serves at
    one reporter-month (France 202506)    112.6 MB gzip, 5,083,358 rows, 34 columns
    rows in the atlas's 54 CRM codes      6,670 of those, 0.131%
    whole corpus kept at that filter      about 16 million rows, 0.4 GB as parquet

So the transfer is large and the RESULT is small, which decides the shape: stream each file
through, keep the rows we want, delete the archive. C: has 26 GB free against 263 GB of transfer,
so landing the archives was never possible - but it is not needed either.

Every kept row keeps all 34 columns. The filter is on PRODUCT, not on detail: customsCode,
motCode and partner2Code are what separate a real import from transit and re-export, and
reference_cube_processed_is_refinery records what dropping them cost last time.

The default filter is baci.crm_codes() - the 54 codes the atlas actually maps. --all-codes keeps
everything instead, which is the mirror-reconciliation case: the UN request was explicitly about
establishing whether a discrepancy is specific to critical materials or general to the data, and
that needs the universe. At 0.4 GB against roughly 300 GB those are different jobs on different
disks, so it is a flag and not a default. See INFRASTRUCTURE.md.

Usage:
  python reconcile/pull_comtrade_bulk.py --plan
  python reconcile/pull_comtrade_bulk.py [--years 2026 2025] [--all-codes] [--max-files N]
"""
import argparse
import csv
import gzip
import io
import json
import os
import re
import shutil
import sys
import time

import pandas as pd
import requests

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

OUTDIR = os.environ.get('CMA_BULK_DIR', os.path.join(ROOT, 'raw', 'comtrade_bulk'))
STATE = os.path.join(OUTDIR, '_state.json')
MANIFEST = os.path.join(OUTDIR, '_manifest.tsv')
LOG = os.path.join(OUTDIR, '_bulk.log')
KEYFILE = os.path.join(ROOT, 'pipeline', '.comtrade_key')

LIST = 'https://comtradeapi.un.org/bulk/v1/get/C/M/HS'
YEAR_MAX, YEAR_MIN = 2026, 2000
MIN_FREE_GB = 5.0            # refuse to start below this: an archive is deleted after each file,
                             # but a 1 GB reporter-month still has to land somewhere first
SIZE = re.compile(r'([\d.]+)\s*(KB|MB|GB)', re.I)


def _key():
    for line in io.open(KEYFILE, encoding='utf-8'):
        line = line.strip()
        if line and not line.startswith('#'):
            return line
    raise SystemExit('no key in %s' % KEYFILE)


def mb(s):
    """fileSize comes back as a STRING - '107.41 MB', '5.76 MB'. int() on it raises."""
    m = SIZE.match(str(s) or '')
    if not m:
        return 0.0
    v, u = float(m.group(1)), m.group(2).upper()
    return v / 1000.0 if u == 'KB' else (v if u == 'MB' else v * 1000.0)


def log(msg):
    os.makedirs(OUTDIR, exist_ok=True)
    line = '%s  %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%S'), msg)
    with io.open(LOG, 'a', encoding='utf-8') as fh:
        fh.write(line)
        fh.flush()
    try:
        sys.stdout.write(line)
        sys.stdout.flush()
    except Exception:
        pass                 # pythonw has no stdout; a working run must not report failure


def load_state():
    if os.path.exists(STATE):
        try:
            return json.load(io.open(STATE, encoding='utf-8'))
        except Exception:
            pass
    return {'done': {}, 'rows': 0, 'bytes_in': 0, 'listings': {}}


def save_state(st):
    os.makedirs(OUTDIR, exist_ok=True)
    tmp = STATE + '.tmp'
    json.dump(st, io.open(tmp, 'w', encoding='utf-8'))
    os.replace(tmp, STATE)


def periods(years):
    """Monthly periods, newest first, never one in the future."""
    now = time.gmtime()
    out = []
    for y in years:
        last = 12 if y < now.tm_year else (now.tm_mon if y == now.tm_year else 0)
        for m in range(last, 0, -1):
            out.append('%d%02d' % (y, m))
    return out


def listing(session, headers, period, st):
    """Every reporter's file for one period, in ONE call. Cached: the listing rarely changes,
    and re-listing 324 periods on each resume would be the only expensive part of a restart."""
    hit = st.setdefault('listings', {}).get(period)
    if hit:
        return hit
    for attempt in range(4):
        try:
            r = session.get(LIST, headers=headers, params={'period': period}, timeout=180)
            if r.status_code == 200:
                rows = [{'reporterCode': d.get('reporterCode'), 'fileUrl': d.get('fileUrl'),
                         'fileSize': d.get('fileSize'),
                         'publicationDate': d.get('publicationDate')}
                        for d in (r.json().get('data') or []) if d.get('fileUrl')]
                st['listings'][period] = rows
                return rows
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(20 * (attempt + 1))
                continue
            log('   %s listing http %s' % (period, r.status_code))
            return []
        except Exception as e:
            time.sleep(10 * (attempt + 1))
    log('   %s listing unreachable' % period)
    return []


def fetch_one(session, headers, period, rep, keep, outdir):
    """Download, filter, write parquet, delete the archive. Returns (rows_kept, bytes_in)."""
    tmp = os.path.join(outdir, '_tmp_%s_%s.txt.gz' % (period, rep['reporterCode']))
    got = 0
    with session.get(rep['fileUrl'], headers=headers, timeout=1800, stream=True) as resp:
        if resp.status_code != 200:
            log('   %s %-5s download http %s' % (period, rep['reporterCode'], resp.status_code))
            return None, 0
        with io.open(tmp, 'wb') as fh:
            for chunk in resp.iter_content(1 << 20):
                fh.write(chunk)
                got += len(chunk)
    try:
        # pyarrow, not the csv module: measured on France 202506, 13.1 s against 38.8 s for
        # the identical 6,670 rows and all 34 columns. The job is decode-bound, not
        # download-bound - that file arrives in 10.5 s - so the reader sets the finish date.
        import pyarrow as pa
        import pyarrow.csv as pv
        import pyarrow.compute as pc
        import pyarrow.parquet as pq
        with gzip.open(tmp, 'rb') as fh:
            tbl = pv.read_csv(
                fh,
                parse_options=pv.ParseOptions(delimiter='\t'),
                read_options=pv.ReadOptions(block_size=1 << 24),
                # cmdCode must stay TEXT. Inferred as an integer it loses its leading zero
                # and '010121' stops matching the code list, silently keeping nothing.
                convert_options=pv.ConvertOptions(
                    strings_can_be_null=False,
                    column_types={'cmdCode': pa.string()}))
        if 'cmdCode' not in tbl.column_names:
            log('   %s %-5s no cmdCode column - skipped' % (period, rep['reporterCode']))
            return None, got
        if keep is not None:
            tbl = tbl.filter(pc.is_in(tbl['cmdCode'], value_set=pa.array(sorted(keep))))
        n = tbl.num_rows
        if n:
            d = os.path.join(outdir, period[:4])
            os.makedirs(d, exist_ok=True)
            dest = os.path.join(d, '%s_%s.parquet' % (period, rep['reporterCode']))
            tmp_p = dest + '.part'
            pq.write_table(tbl, tmp_p, compression='zstd')
            os.replace(tmp_p, dest)    # never leave a half file looking complete
        return n, got
    finally:
        try:
            os.remove(tmp)             # the archive is never kept: 263 GB against 26 GB free
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, nargs='*')
    ap.add_argument('--all-codes', action='store_true',
                    help='keep every product, not just the 54 the atlas maps (needs ~300 GB)')
    ap.add_argument('--max-files', type=int, default=0, help='stop after N files (a smoke test)')
    ap.add_argument('--plan', action='store_true')
    a = ap.parse_args()

    keep = None
    if not a.all_codes:
        import baci
        keep = set(baci.crm_codes())

    years = a.years or list(range(YEAR_MAX, YEAR_MIN - 1, -1))
    pers = periods(years)
    st = load_state()
    headers = {'Ocp-Apim-Subscription-Key': _key()}
    s = requests.Session()

    if a.plan:
        print('BULK monthly HS6 pull - PLAN ONLY')
        print('  endpoint   %s' % LIST)
        print('  output     %s' % OUTDIR)
        print('  periods    %d (%s .. %s)' % (len(pers), pers[-1], pers[0]))
        print('  filter     %s' % ('ALL products' if keep is None
                                   else '%d critical-material HS6 codes' % len(keep)))
        print('  already done %s reporter-months' % format(len(st.get('done', {})), ','))
        print('  rows kept so far %s' % format(st.get('rows', 0), ','))
        sample = pers[:3]
        tot = 0.0
        for p in sample:
            rows = listing(s, headers, p, st)
            g = sum(mb(x['fileSize']) for x in rows) / 1000.0
            print('    %s  %3d reporters  %.2f GB' % (p, len(rows), g))
            tot += g
        if sample:
            print('  mean %.2f GB per period -> about %.0f GB over %d periods'
                  % (tot / len(sample), tot / len(sample) * len(pers), len(pers)))
        save_state(st)
        return 0

    free = shutil.disk_usage(ROOT[:3]).free / 1e9
    if free < MIN_FREE_GB:
        raise SystemExit('only %.1f GB free, need %.1f - refusing to start' % (free, MIN_FREE_GB))

    os.makedirs(OUTDIR, exist_ok=True)
    log('START  periods=%d  filter=%s  free=%.1f GB'
        % (len(pers), 'all' if keep is None else '%d codes' % len(keep), free))
    t0 = time.time()
    files = rows_kept = 0
    bytes_in = 0
    try:
        for period in pers:
            reps = listing(s, headers, period, st)
            if not reps:
                continue
            todo = [r for r in reps
                    if '%s|%s' % (period, r['reporterCode']) not in st['done']]
            if not todo:
                continue
            log('%s: %d reporter(s), %d to fetch, %.2f GB listed'
                % (period, len(reps), len(todo),
                   sum(mb(r['fileSize']) for r in reps) / 1000.0))
            for rep in todo:
                if a.max_files and files >= a.max_files:
                    log('stopping: --max-files %d reached' % a.max_files)
                    raise KeyboardInterrupt
                # Check the disk on EVERY file, not only at startup. This runs unattended for
                # the better part of a day on a machine nobody is watching, and the archives it
                # streams through are up to a gigabyte each; a full disk part-way through would
                # otherwise show up as a pile of unreadable half files.
                if shutil.disk_usage(OUTDIR).free / 1e9 < MIN_FREE_GB:
                    log('stopping: only %.1f GB free, below the %.1f GB floor'
                        % (shutil.disk_usage(OUTDIR).free / 1e9, MIN_FREE_GB))
                    raise KeyboardInterrupt
                n, got = fetch_one(s, headers, period, rep, keep, OUTDIR)
                if n is None:
                    continue
                files += 1
                rows_kept += n
                bytes_in += got
                st['done']['%s|%s' % (period, rep['reporterCode'])] = {
                    'rows': n, 'in_mb': round(got / 1e6, 2),
                    'published': rep.get('publicationDate')}
                st['rows'] = int(st.get('rows', 0)) + n
                st['bytes_in'] = int(st.get('bytes_in', 0)) + got
                save_state(st)
                with io.open(MANIFEST, 'a', encoding='utf-8') as fh:
                    fh.write('%s\t%s\t%d\t%.2f\t%s\n'
                             % (period, rep['reporterCode'], n, got / 1e6,
                                rep.get('publicationDate') or ''))
    except KeyboardInterrupt:
        pass
    finally:
        save_state(st)
        dt = max(time.time() - t0, 0.001)
        log('END  %d files, %s rows kept, %.1f GB in, %.1f min, %.1f MB/s'
            % (files, format(rows_kept, ','), bytes_in / 1e9, dt / 60,
               bytes_in / 1e6 / dt))
    return 0


if __name__ == '__main__':
    sys.exit(main())
