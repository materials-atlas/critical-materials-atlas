# -*- coding: utf-8 -*-
"""Fetch the USGS Minerals Yearbook, volume I (Metals and Minerals), chapter by chapter.

Why this and not the Mineral Commodity Summaries we already hold. The MCS is two pages a
commodity: world mine production, reserves, a price. The Yearbook is the long chapter behind it,
and it carries the tables the Atlas has had to approximate - refinery and smelter output by plant
and by country, which is exactly the layer the UN's "Industrial Statistics" pointer was meant to
supply and does not (see the council verdict: ICS is fullest where USGS, BGS, ICSG, the IAI and
ILZSG already cover us, and empty where we approximate). Before this, the repository held
precisely one Yearbook file, `_sources/usgs_myb_explosives_2019.pdf`.

Driven by the published index, not by guessed URLs. Each year has its own directory listing at
pubs.usgs.gov/myb/vol1/<year>/, and the set of chapters differs by year - 83 in 2019, 32 in 2021,
26 in 2022, because recent years are still being released a commodity at a time. Guessing
<commodity> x <year> would spend most of its requests on 404s and would silently miss any
commodity whose slug we failed to imagine.

pubs.usgs.gov refuses WebFetch but serves a browser user agent, which is why one is set here -
see reference_usgs_fetch_route.

Resumable: a chapter already on disk is never fetched again, so an interrupted run costs nothing.
"""
import io
import os
import re
import sys
import time

import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(ROOT, 'raw', 'usgs_myb')
MANIFEST = os.path.join(OUTDIR, '_manifest.tsv')
INDEX = 'https://pubs.usgs.gov/myb/vol1/%d/'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

YEAR_MAX, YEAR_MIN = 2023, 1994
SLEEP = 0.6                      # a public document server, fetched a few thousand times


def chapters(year, session):
    """The chapter slugs this year actually published, read off its directory listing."""
    try:
        r = session.get(INDEX % year, headers=UA, timeout=60)
    except Exception as e:
        print('   %d  index unreachable (%s)' % (year, type(e).__name__), flush=True)
        return []
    if r.status_code != 200:
        print('   %d  index http %s' % (year, r.status_code), flush=True)
        return []
    return sorted(set(re.findall(r'myb1-%d-([a-z0-9\-]+)\.pdf' % year, r.text)))


def main():
    only = [int(a) for a in sys.argv[1:] if a.isdigit()]
    years = only or list(range(YEAR_MAX, YEAR_MIN - 1, -1))
    os.makedirs(OUTDIR, exist_ok=True)
    s = requests.Session()

    got = new = skipped = failed = 0
    rows = []
    for year in years:
        slugs = chapters(year, s)
        if not slugs:
            continue
        print('%d: %d chapters' % (year, len(slugs)), flush=True)
        ydir = os.path.join(OUTDIR, str(year))
        os.makedirs(ydir, exist_ok=True)
        for slug in slugs:
            name = 'myb1-%d-%s.pdf' % (year, slug)
            dest = os.path.join(ydir, name)
            if os.path.exists(dest) and os.path.getsize(dest) > 2048:
                skipped += 1
                rows.append((year, slug, os.path.getsize(dest), 'on disk'))
                continue
            url = (INDEX % year) + name
            try:
                r = s.get(url, headers=UA, timeout=180)
                if r.status_code != 200 or len(r.content) < 2048:
                    print('   %-28s http %s, %d bytes - skipped'
                          % (slug, r.status_code, len(r.content)), flush=True)
                    failed += 1
                    rows.append((year, slug, 0, 'http %s' % r.status_code))
                    continue
                tmp = dest + '.part'
                with io.open(tmp, 'wb') as fh:
                    fh.write(r.content)
                os.replace(tmp, dest)          # never leave a half file looking complete
                new += 1
                rows.append((year, slug, len(r.content), 'fetched'))
            except Exception as e:
                print('   %-28s ERROR %s' % (slug, type(e).__name__), flush=True)
                failed += 1
                rows.append((year, slug, 0, type(e).__name__))
            time.sleep(SLEEP)
        got += len(slugs)

    with io.open(MANIFEST, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('year\tchapter\tbytes\tstatus\n')
        for r in sorted(rows):
            fh.write('%d\t%s\t%d\t%s\n' % r)

    total = sum(os.path.getsize(os.path.join(d, f))
                for d, _, fs in os.walk(OUTDIR) for f in fs if f.endswith('.pdf'))
    print()
    print('chapters listed %d   fetched now %d   already held %d   failed %d'
          % (got, new, skipped, failed))
    print('on disk: %.1f MB in %s' % (total / 1e6, os.path.relpath(OUTDIR, ROOT)))
    print('manifest: %s' % os.path.relpath(MANIFEST, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
