#!/usr/bin/env python3
"""
A dated data release of the download-only files (25 Nov 2026).

WHY. Every rebuild rewrote three large download files - out/cube.csv.gz (24 MB), out/cube_manifest.json
(19 MB) and out/sdmx/mineral_flows.sdmx.csv.gz (48 MB) - and each was committed again, 32-40 times
since August: most of a 1 GB git history. No builder reads them; they exist for readers to download.
So they are committed only on a dated release, made with this script. out/cube.parquet is NOT one of
them: thirteen builders read it, so it must be committed whenever it changes, or a clone would
rebuild different pages.

WHAT IT DOES.
  1. measures the four download files (bytes, sha256, rows / observations / identities);
  2. writes those numbers into data.html, which is hand-written and had drifted (the SDMX line said
     1,664,638 observations and 16.5 MB against 3,664,577 and 47.7 MB; the manifest 13,814 identities
     against 63,658);
  3. writes out/data_release.json - the record check.py --staged compares a staged download file with.
Then stage and commit:  git add out/data_release.json data.html out/cube.csv.gz out/cube_manifest.json
                        out/sdmx/mineral_flows.sdmx.csv.gz

BETWEEN RELEASES, after `runner.py --run`: git checkout -- out/cube.csv.gz out/cube_manifest.json
out/sdmx/mineral_flows.sdmx.csv.gz   (check.py --staged refuses them otherwise).

Not a builder (record_graph/runner skip it by name). Run:  python release_data.py [YYYY-MM-DD]
"""
import datetime
import gzip
import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_ONLY = ['out/cube.csv.gz', 'out/cube_manifest.json', 'out/sdmx/mineral_flows.sdmx.csv.gz']
RECORD = 'out/data_release.json'


def sha(p):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, p), 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def gz_lines(p):
    with gzip.open(os.path.join(ROOT, p), 'rb') as f:
        return sum(1 for _ in f)


def mb(p):
    return os.path.getsize(os.path.join(ROOT, p)) / 1e6


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    datetime.date.fromisoformat(day)
    import pyarrow.parquet as pq
    cube_rows = pq.ParquetFile(os.path.join(ROOT, 'out/cube.parquet')).metadata.num_rows
    csv_rows = gz_lines('out/cube.csv.gz') - 1
    if csv_rows != cube_rows:
        raise SystemExit('cube.csv.gz has %d rows, cube.parquet %d - rebuild before releasing' % (csv_rows, cube_rows))
    obs = gz_lines('out/sdmx/mineral_flows.sdmx.csv.gz') - 1
    with io.open(os.path.join(ROOT, 'out/cube_manifest.json'), encoding='utf-8') as f:
        ident = json.load(f)['n_identities']

    p = os.path.join(ROOT, 'data.html')
    s = io.open(p, encoding='utf-8', newline='').read()
    subs = [
        (r'(The published cube, )[\d.,]+ million rows, [\d.]+&nbsp;MB',
         r'\g<1>%.2f million rows, %.1f&nbsp;MB' % (cube_rows / 1e6, mb('out/cube.parquet'))),
        (r'(The same table as gzipped CSV, )[\d.]+&nbsp;MB', r'\g<1>%.1f&nbsp;MB' % mb('out/cube.csv.gz')),
        (r'[\d,]+( observations as <b>SDMX-CSV</b>, )[\d.]+&nbsp;MB',
         '{:,}'.format(obs) + r'\g<1>%.1f&nbsp;MB' % mb('out/sdmx/mineral_flows.sdmx.csv.gz')),
        (r'(Every one of the <b>)[\d,]+( identities</b>)', r'\g<1>{:,}\g<2>'.format(ident)),
    ]
    for rx, rep in subs:
        s, n = re.subn(rx, rep, s)
        if n != 1:
            raise SystemExit('data.html: pattern matched %d times, expected 1: %s' % (n, rx))
    note = ('<p class="note" id="data-release">Downloads below: data release of %s. The Parquet cube is '
            'updated with every rebuild; the CSV copy, the SDMX export and the manifest are refreshed on each '
            'dated release.</p>' % day)
    if 'id="data-release"' in s:
        s = re.sub(r'<p class="note" id="data-release">.*?</p>', note, s, count=1, flags=re.S)
    else:
        anchor = '  <table>\n    <thead><tr><th>URL</th><th>What</th></tr></thead>'
        anchor = anchor.replace('\n', '\r\n') if '\r\n' in s else anchor
        if s.count(anchor) < 1:
            raise SystemExit('data.html: download table not found')
        s = s.replace(anchor, '  ' + note + ('\r\n' if '\r\n' in s else '\n') + anchor, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)

    rec = {'date': day,
           'rule': 'Download-only files are committed only with a matching entry here (check.py --staged).',
           'files': {f: {'bytes': os.path.getsize(os.path.join(ROOT, f)), 'sha256': sha(f)} for f in DOWNLOAD_ONLY},
           'counts': {'cube_rows': cube_rows, 'sdmx_observations': obs, 'manifest_identities': ident}}
    with io.open(os.path.join(ROOT, RECORD), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rec, f, indent=1)
        f.write('\n')
    print('data release %s: cube %s rows, SDMX %s observations, %s identities' % (day, format(cube_rows, ','),
                                                                                 format(obs, ','), format(ident, ',')))
    print('stage: git add %s data.html %s' % (RECORD, ' '.join(DOWNLOAD_ONLY)))


if __name__ == '__main__':
    main()
