# -*- coding: utf-8 -*-
"""Fetch the annual USGS Mineral Commodity Summaries chapters for one commodity, every edition.

Each MCS edition carries only two years by country, so a country panel has to be stitched from all
editions. This downloads them; parse_usgs_mcs.py turns them into pipeline/data/usgs_mcs_history.parquet.

The editions live on three hosts and under four naming schemes (coppemcs96.pdf, mcs-2012-coppe.pdf,
the 2019 s3fs path, mcsYYYY-copper.pdf), so the list is resolved from the commodity's own USGS
"statistics and information" page rather than guessed. pubs.usgs.gov refuses a plain fetch but serves
a browser user agent (see the atlas note on fetching USGS).

PDFs are cached under raw/usgs_mcs/<commodity>/ (gitignored, like every other raw holding): they are
the publisher's files, kept locally, and only derived figures are published.

Network fetcher: named fetch_* so the runner never runs it.
Usage:  python pipeline/fetch_usgs_mcs.py copper [--list] [--refresh]
"""
import argparse
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, 'raw', 'usgs_mcs')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/124.0 Safari/537.36')
PAGE = 'https://www.usgs.gov/centers/national-minerals-information-center/%s-statistics-and-information'
# the commodity's page slug, where it differs from the atlas's name for the material
SLUG = {'copper': 'copper', 'tungsten': 'tungsten', 'antimony': 'antimony', 'graphite': 'graphite',
        'rare_earths': 'rare-earths', 'cobalt': 'cobalt', 'bismuth': 'bismuth',
        'gallium': 'gallium', 'germanium': 'germanium', 'lithium': 'lithium', 'nickel': 'nickel',
        'manganese': 'manganese', 'tin': 'tin', 'indium': 'indium', 'tellurium': 'tellurium',
        'magnesium': 'magnesium', 'titanium': 'titanium', 'vanadium': 'vanadium', 'zinc': 'zinc'}
# the file-name stem each commodity's pre-2008 chapters use (USGS abbreviations, not ours)
# Only where the page carries several commodities' chapters and the stem cannot be inferred safely
# (rare earths sits beside scandium and yttrium). Everything else is read off the page's own links.
STEM = {'copper': 'coppe', 'tungsten': 'tungs', 'antimony': 'antim', 'graphite': 'graph',
        'rare_earths': 'raree', 'cobalt': 'cobal', 'bismuth': 'bismu'}


def infer_stem(names, commodity):
    """The file stem the commodity's own chapters use, from the page's links."""
    if commodity in STEM:
        return STEM[commodity]
    counts = {}
    for n in names:
        m = re.fullmatch(r'mcs-(\d{4})-([a-z]+)\.pdf', n)
        if m:
            counts[m.group(2)] = counts.get(m.group(2), 0) + 1
    if not counts:
        return commodity[:5]
    best = max(counts, key=counts.get)
    ties = [k for k, v in counts.items() if v == counts[best]]
    if len(ties) > 1:
        # several commodities share the page; prefer the stem closest to the name we asked for
        ties.sort(key=lambda s: (not commodity.startswith(s[:3]), s))
        return ties[0]
    return best


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.geturl()


def editions(commodity):
    """Every MCS chapter link on the commodity page, as {edition_year: url}."""
    html, _ = get(PAGE % SLUG[commodity])
    html = html.decode('utf-8', 'replace')
    out = {}
    names = [h.rsplit('/', 1)[-1].lower() for h in re.findall(r'href="([^"]+\.pdf)"', html)]
    stem = infer_stem(names, commodity)
    slug = SLUG[commodity]
    for href in sorted(set(re.findall(r'href="([^"]+\.pdf)"', html))):
        name = href.rsplit('/', 1)[-1].lower()
        # the commodity's own chapter only: a page like rare earths also links mcs-2010-scand.pdf and
        # mcs-2010-yttri.pdf, and matching on the year alone silently downloaded yttrium instead
        m = re.fullmatch(r'mcs-(\d{4})-' + re.escape(stem) + r'\.pdf', name) or             re.fullmatch(r'mcs(\d{4})-' + re.escape(slug) + r'\.pdf', name)
        if m:
            out[int(m.group(1))] = href
            continue
        # 1996-2007: coppemcs96.pdf .. coppemcs07.pdf
        m = re.match(re.escape(stem) + r'mcs(\d{2})\.pdf$', name)
        if m:
            yy = int(m.group(1))
            out[1900 + yy if yy >= 90 else 2000 + yy] = href
    return dict(sorted(out.items()))


VOLUMES = {y: 'https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/'
              'mineral-pubs/mcs/mcs%d.pdf' % y for y in range(2000, 2004)}
# The 1996-1999 volumes exist only as scans (mcs-YYYYocr.pdf). Their OCR breaks both the words
# ("Kaza ks tan") and the column order, and they carry no superscript tier, which is what tells a
# footnote marker from a digit here. They are left out rather than parsed badly.


def chapter_pages(doc, commodity):
    """The pages of one commodity's chapter inside a full volume."""
    want = commodity.replace('_', ' ').upper()
    alt = {'RARE EARTHS': 'RARE EARTHS', 'GRAPHITE': 'GRAPHITE'}.get(want, want)
    head = re.compile(r'^\s*\d*\s*(%s|%s)\b' % (re.escape(want), re.escape(alt)), re.M)
    other = re.compile(r'^\s*\d*\s*[A-Z][A-Z \-()]{3,}$', re.M)
    pages = []
    for i in range(len(doc)):
        t = doc[i].get_text()[:300]
        if head.search(t) and ('Data in' in doc[i].get_text() or 'Domestic Production' in doc[i].get_text()):
            pages = [i]
            for j in range(i + 1, min(i + 3, len(doc))):
                nxt = doc[j].get_text()[:300]
                if head.search(nxt) or not other.search(nxt):
                    pages.append(j)
                else:
                    break
            break
    return pages


def from_volumes(commodity, refresh=False):
    """Cut the commodity's chapter out of each full volume, so the editions the commodity page does
    not link (2000-2003) join the panel in the same form as the rest."""
    import fitz
    out = os.path.join(RAW, commodity)
    os.makedirs(out, exist_ok=True)
    for y, url in VOLUMES.items():
        path = os.path.join(out, 'mcs%d.pdf' % y)
        if os.path.exists(path) and not refresh:
            continue
        vol = os.path.join(RAW, '_volumes', 'mcs%d.pdf' % y)
        os.makedirs(os.path.dirname(vol), exist_ok=True)
        if not os.path.exists(vol):
            body, _ = get(url, timeout=300)
            if not body.startswith(b'%PDF'):
                print('  %d volume not a PDF' % y)
                continue
            with open(vol, 'wb') as f:
                f.write(body)
            time.sleep(1)
        with fitz.open(vol) as doc:
            pages = chapter_pages(doc, commodity)
            if not pages:
                print('  %d: %s chapter not found in the volume' % (y, commodity))
                continue
            cut = fitz.open()
            cut.insert_pdf(doc, from_page=pages[0], to_page=pages[-1])
            cut.save(path)
            cut.close()
        print('  %d  from volume, pages %s' % (y, [p + 1 for p in pages]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('commodity')
    ap.add_argument('--list', action='store_true', help='resolve the editions and stop')
    ap.add_argument('--refresh', action='store_true', help='re-download editions already cached')
    ap.add_argument('--volumes', action='store_true',
                    help='also cut 2000-2003 chapters out of the full yearly volumes')
    a = ap.parse_args()
    if a.commodity not in SLUG:
        sys.exit('unknown commodity: add its USGS page slug to SLUG')
    eds = editions(a.commodity)
    print('%s: %d editions, %d..%d' % (a.commodity, len(eds), min(eds), max(eds)))
    if a.list:
        for y, u in eds.items():
            print(' ', y, u)
        return
    out = os.path.join(RAW, a.commodity)
    os.makedirs(out, exist_ok=True)
    for y, url in eds.items():
        path = os.path.join(out, 'mcs%d.pdf' % y)
        if os.path.exists(path) and not a.refresh:
            continue
        try:
            body, final = get(url)
        except Exception as e:
            print('  %d FAILED %s' % (y, e))
            continue
        if not body.startswith(b'%PDF'):
            # the old minerals.usgs.gov paths redirect to an HTML landing page
            print('  %d not a PDF (redirected to %s)' % (y, final))
            continue
        # confirm the chapter is the commodity asked for, not a neighbour on the same page
        head = ''
        try:
            import fitz
            with fitz.open(stream=body, filetype='pdf') as doc:
                head = doc[0].get_text()[:400].upper()
        except Exception:
            pass
        want = a.commodity.replace('_', ' ').upper().rstrip('S')
        if head and want[:6] not in head:
            print('  %d SKIPPED: first page does not mention %s (%r)' % (y, want, ' '.join(head.split())[:60]))
            continue
        with open(path, 'wb') as f:
            f.write(body)
        print('  %d  %6d bytes' % (y, len(body)))
        time.sleep(1)
    if a.volumes:
        from_volumes(a.commodity, a.refresh)
    have = sorted(int(f[3:7]) for f in os.listdir(out) if f.startswith('mcs') and f.endswith('.pdf'))
    print('cached %d editions: %s' % (len(have), ', '.join(str(y) for y in have)))
    missing = [y for y in eds if y not in have]
    if missing:
        print('missing:', missing)


if __name__ == '__main__':
    main()
