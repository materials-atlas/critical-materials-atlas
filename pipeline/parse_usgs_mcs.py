# -*- coding: utf-8 -*-
"""Turn the cached USGS Mineral Commodity Summaries chapters into a country panel.

Each edition prints two years by country; the panel is every edition's table kept side by side, so a
revision is visible rather than overwritten. Nothing here picks a headline value: usgs_mcs_cube.py
applies the rule (latest edition that reports the year).

Why the tables are read geometrically rather than as text. A footnote marker is printed as a
superscript immediately before the value, and in extracted text "7100,000" is indistinguishable from
a genuine 7,100,000. In the PDF the marker is a separate, smaller span (6.5pt against 10pt), so the
parser reads spans with their font size: small spans become footnote codes, full-size spans values.
The column layout also changes across editions (mine/reserves/reserve base in the 1990s and 2000s,
mine/refinery/reserves in the 2020s), so columns are found from the header line rather than fixed.

Writes pipeline/data/usgs_mcs_history.parquet.
Usage:  python pipeline/parse_usgs_mcs.py [copper ...] [--report]
"""
import argparse
import os
import re
import sys

import fitz
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, 'raw', 'usgs_mcs')
OUT = os.path.join(HERE, 'data', 'usgs_mcs_history.parquet')

CAPTION = re.compile(r'^World\s+(Mine|Refinery|Smelter|Mine and Refinery|Production)[^:]*:', re.I)
YEAR = re.compile(r'^(19|20)\d{2}$')
# the measure each column-group header names
# A column header is a span that is ONLY the header text (with an optional footnote digit): the
# caption wraps into sentences like "Reserves for Canada, Chile, ..." that would otherwise be read as
# a Reserves column sitting on top of a data column.
GROUPS = [('mine', re.compile(r'mine production\s*\d*\s*$', re.I)),
          ('refinery', re.compile(r'refinery production\s*\d*\s*$', re.I)),
          ('smelter', re.compile(r'smelter production\s*\d*\s*$', re.I)),
          ('reserve_base', re.compile(r'reserve base\s*\d*\s*$', re.I)),
          ('reserves', re.compile(r'reserves\s*\d*\s*$', re.I))]
# rows that are not countries
WORLD = re.compile(r'^world\s+total', re.I)
OTHER = re.compile(r'^other\s+countr', re.I)
# USGS names that no ISO table knows, or that it knows differently
USGS_NAMES = {
    'congo (kinshasa)': 'COD', 'congo (brazzaville)': 'COG', 'burma': 'MMR', 'korea, republic of': 'KOR',
    'korea, north': 'PRK', "korea, democratic people's republic of": 'PRK', 'kazakstan': 'KAZ',
    'macedonia': 'MKD', 'serbia and montenegro': 'SCG', 'yugoslavia': 'YUG', 'turkey': 'TUR',
    'iran': 'IRN', 'laos': 'LAO', 'bolivia': 'BOL', 'moldova': 'MDA', 'tanzania': 'TZA',
    'vietnam': 'VNM', 'russia': 'RUS', 'united states': 'USA', 'czechia': 'CZE', 'czech republic': 'CZE',
    'slovakia': 'SVK', 'venezuela': 'VEN', 'syria': 'SYR', 'cote d’ivoire': 'CIV',
    "cote d'ivoire": 'CIV', 'united kingdom': 'GBR', 'south africa': 'ZAF', 'germany': 'DEU',
}
# the unit line is parenthesised in most chapters and bracketed in others ("[Data in metric tons,
# rare-earth-oxide (REO) equivalent, unless otherwise specified]"), which is why rare earths had no
# unit at all from 2010 on and so no tonnes
UNIT_LINE = re.compile(r'\[Data in (?P<b>[^\]]*?)(?:,? unless otherwise \w+)?\]'
                       r'|\(Data in (?P<p>[^)]*?)(?:,? unless otherwise \w+)?\)', re.I | re.S)
TONNES = [(re.compile(r'thousand metric tons', re.I), 1000.0),
          (re.compile(r'metric tons', re.I), 1.0),
          (re.compile(r'million metric tons', re.I), 1e6)]


def spans(page):
    out = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                t = s['text'].strip()
                if t:
                    out.append({'x0': s['bbox'][0], 'x1': s['bbox'][2], 'y': round(s['bbox'][1], 1),
                                'size': round(s['size'], 1), 'text': t})
    return out


def lines(sp, tol=2.0):
    """Group spans into visual lines by y, each sorted left to right."""
    out = []
    for s in sorted(sp, key=lambda s: (s['y'], s['x0'])):
        if out and abs(s['y'] - out[-1][0]['y']) <= tol:
            out[-1].append(s)
        else:
            out.append([s])
    return out


def line_text(ln):
    return ' '.join(s['text'] for s in ln).strip()


def body_size(page_lines):
    """The modal font size: anything smaller in a table row is a footnote marker."""
    c = {}
    for ln in page_lines:
        for s in ln:
            c[s['size']] = c.get(s['size'], 0) + len(s['text'])
    return max(c, key=c.get) if c else 10.0


NUM = re.compile(r'^\(?[\d,]+(?:\.\d+)?\)?$')
# Some editions typeset the footnote marker inside the value span as a glyph ("*3,670" for footnote 3
# on 3,670). Only NON-DIGIT leading marks are stripped: a leading digit stays part of the number,
# because "7100,000" would otherwise lose its 1 or its 7 - that ambiguity is what the span sizes solve.
MARKED = re.compile(r'^(?P<mark>[^\d(\s—–-]+)(?P<num>\(?[\d,]+(?:\.\d+)?\)?)$')
SPECIAL = {'w': 'withheld', 'na': 'not available', 'nа': 'not available', '—': 'zero', '-': 'zero',
           '--': 'zero', '—': 'zero', '–': 'zero', 'xx': 'not applicable', 'e': None}


def cell_value(text):
    """(value, flag, mark) - flag records W / NA / zero dash / small-quantity reference."""
    t = text.strip().rstrip('e').strip()
    mark = ''
    m = MARKED.match(t)
    if m and m.group('mark') not in ('$',):
        mark, t = m.group('mark'), m.group('num')
    low = t.lower()
    if low in SPECIAL:
        return ((0.0, 'zero') if SPECIAL[low] == 'zero' else (None, SPECIAL[low])) + (mark,)
    if NUM.match(t):
        neg = t.startswith('(') and t.endswith(')')
        v = float(t.strip('()').replace(',', ''))
        # a parenthesised single digit is a footnote reference ("less than 1/2 unit"), not a value
        if neg and v < 10:
            return None, 'less than half a unit', mark
        return (-v if neg else v), None, mark
    return None, 'unparsed:' + t[:12], mark


def parse_edition(path, commodity, edition_year):
    doc = fitz.open(path)
    rows, caption, unit_text, factor = [], None, None, None
    for pno in range(len(doc)):
        page = doc[pno]
        L = lines(spans(page))
        base = body_size(L)
        if unit_text is None:
            # searched across the whole page, not line by line: the rare-earth chapters wrap the unit
            # line ("(Data in metric tons of rare-earth-oxide (REO) equivalent unless otherwise
            # noted)") and a per-line search missed it, leaving those editions with no tonnes at all
            page_text = ' '.join(line_text(ln) for ln in L)
            m = UNIT_LINE.search(page_text)
            if m:
                unit_text = re.sub(r'\s+', ' ', m.group('b') or m.group('p') or '').strip()
                for rx, f in TONNES:
                    if rx.search(unit_text):
                        factor = f
                        break
        # find the table caption
        start = None
        for i, ln in enumerate(L):
            if CAPTION.match(line_text(ln)):
                start, caption = i, line_text(ln).split(':')[0]
                break
        if start is None:
            continue
        # group headers and the year row
        groups, year_cells, hdr_end, est_marks = [], [], None, []
        for i in range(start, min(start + 12, len(L))):
            txt = line_text(L[i])
            for s in L[i]:
                if len(s['text'].strip()) > 28:
                    continue
                for name, rx in GROUPS:
                    if rx.match(s['text'].strip()):
                        groups.append({'measure': name, 'x': (s['x0'] + s['x1']) / 2})
                        break
            # an estimate marker can sit on a header line ABOVE the year row, over its column
            # ("Mine production" then a superscript e); 29 chapters print it that way
            est_marks += [(s['x0'] + s['x1']) / 2 for s in L[i]
                          if s['size'] < base - 0.6 and s['text'].strip() == 'e']
            ys = [s for s in L[i] if YEAR.match(s['text'].rstrip('e'))]
            if ys and len(ys) >= 1 and not re.search(r'[A-Za-z]{4}', txt.replace('e', '')):
                for s in ys:
                    est = s['text'].endswith('e')
                    if not est:  # a superscript 'e' sits in its own small span just after
                        est = any(abs(o['x0'] - s['x1']) < 6 and o['size'] < base and o['text'].strip() == 'e'
                                  for o in L[i])
                    xc = (s['x0'] + s['x1']) / 2
                    est = est or any(abs(m - xc) < 25 for m in est_marks)
                    year_cells.append({'year': int(s['text'].rstrip('e')), 'x': xc, 'is_estimate': est})
                hdr_end = i
                break
        if hdr_end is None or not year_cells:
            continue
        # columns: the year cells, plus reserve-type groups that have no year of their own
        cols = []
        for yc in year_cells:
            g = min(groups, key=lambda g: abs(g['x'] - yc['x'])) if groups else {'measure': 'mine'}
            cols.append({'x': yc['x'], 'measure': g['measure'], 'year': yc['year'],
                         'is_estimate': yc['is_estimate']})
        for g in groups:
            if g['measure'] in ('reserves', 'reserve_base') and all(abs(g['x'] - c['x']) > 12 for c in cols):
                cols.append({'x': g['x'], 'measure': g['measure'], 'year': None, 'is_estimate': False})
        # data rows
        for ln in L[hdr_end + 1:]:
            label_spans = [s for s in ln if s['size'] >= base - 0.6 and not NUM.match(s['text'].rstrip('e'))
                           and not MARKED.match(s['text'].rstrip('e'))
                           and not (len(s['text'].split()) > 1 and
                                    all(NUM.match(q.rstrip('e')) or MARKED.match(q.rstrip('e'))
                                        for q in s['text'].split()))
                           and s['text'].strip().lower() not in SPECIAL]
            if not label_spans:
                continue
            label = ' '.join(s['text'] for s in label_spans if s['x0'] < min(c['x'] for c in cols) - 10).strip()
            label = re.sub(r'\s+', ' ', label).strip(' .:')
            if not label or len(label) > 60:
                continue
            values = [s for s in ln if s['size'] >= base - 0.6 and s['x0'] >= min(c['x'] for c in cols) - 40
                      and (NUM.match(s['text'].rstrip('e')) or MARKED.match(s['text'].rstrip('e'))
                           or s['text'].strip().lower() in SPECIAL
                           or all(NUM.match(q.rstrip('e')) or MARKED.match(q.rstrip('e'))
                                  for q in s['text'].split()) and len(s['text'].split()) > 1)]
            if not values:
                if WORLD.match(label):
                    break
                continue
            # Some rows put two columns in one span ("966,000 1,000,000"): split it and place each
            # part across the span's width, so each lands in its own column.
            expanded = []
            for s in values:
                parts = s['text'].split()
                if len(parts) > 1 and all(NUM.match(q.rstrip('e')) or MARKED.match(q.rstrip('e')) for q in parts):
                    span_w = s['x1'] - s['x0']
                    chars = sum(len(q) for q in parts) + len(parts) - 1
                    at = s['x0']
                    for q in parts:
                        w = span_w * len(q) / chars
                        expanded.append(dict(s, text=q, x0=at, x1=at + w))
                        at += w + span_w / chars
                else:
                    expanded.append(s)
            values = expanded
            # a footnote marker is a small span printed immediately before its own value, so it is
            # attached to that value rather than to the whole row
            marks = [s for s in ln if s['size'] < base - 0.6]
            kind = 'world_printed' if WORLD.match(label) else 'other_countries' if OTHER.match(label) else 'country'
            for s in values:
                xc = (s['x0'] + s['x1']) / 2
                col = min(cols, key=lambda c: abs(c['x'] - xc))
                if abs(col['x'] - xc) > 60:
                    continue
                v, flag, mark = cell_value(s['text'])
                notes = [k['text'] for k in marks
                         if -2 <= s['x0'] - k['x1'] < 8 or -2 <= k['x0'] - s['x1'] < 8]
                if mark:
                    notes = notes + [mark]
                # a small 'e' against the value is the estimate marker, not a footnote code
                cell_est = 'e' in notes
                notes = [n for n in notes if n != 'e']
                rows.append({
                    'commodity': commodity, 'country_name_raw': label, 'year': col['year'],
                    'measure': col['measure'], 'value': v, 'unit': unit_text,
                    'value_t': (v * factor) if (v is not None and factor and col['measure'] in
                                                ('mine', 'refinery', 'smelter')) else None,
                    'is_estimate': bool(col['is_estimate']) or s['text'].strip().endswith('e') or cell_est,
                    'flag': flag, 'edition_year': edition_year, 'page': pno + 1,
                    'footnote_codes': ','.join(notes) if notes else None,
                    'table_caption': caption, 'row_kind': kind})
            if kind == 'world_printed':
                break
        break
    return rows


def iso3_map():
    sys.path.insert(0, ROOT)
    import baci
    cc = baci.countries()
    m = {str(n).strip().lower(): i for n, i in zip(cc['name'], cc['iso3']) if n and i}
    m.update(USGS_NAMES)
    return m


def to_iso3(name, m):
    n = re.sub(r'\s+', ' ', name).strip().lower().strip(' .')
    n = re.sub(r'\d+$', '', n).strip()
    return m.get(n) or m.get(n.replace('the ', ''))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('commodities', nargs='*', default=['copper'])
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()
    m = iso3_map()
    allrows = []
    for c in (a.commodities or ['copper']):
        d = os.path.join(RAW, c)
        for f in sorted(os.listdir(d)):
            if not f.endswith('.pdf'):
                continue
            ed = int(f[3:7])
            rows = parse_edition(os.path.join(d, f), c, ed)
            if a.report:
                yrs = sorted({r['year'] for r in rows if r['year']})
                ms = sorted({r['measure'] for r in rows})
                print('%s %d: %3d rows, years %s, measures %s, countries %d' % (
                    c, ed, len(rows), yrs, ms, len({r['country_name_raw'] for r in rows if r['row_kind'] == 'country'})))
            allrows += rows
    if not allrows:
        sys.exit('no rows parsed')
    df = pd.DataFrame(allrows)
    df['iso3'] = [to_iso3(n, m) if k == 'country' else ('WLD' if k == 'world_printed' else None)
                  for n, k in zip(df.country_name_raw, df.row_kind)]
    # the computed world sum, kept beside the printed total the table shows
    sums = (df[df.row_kind.isin(['country', 'other_countries'])]
            .groupby(['commodity', 'edition_year', 'measure', 'year'], dropna=False)
            .agg(value=('value', 'sum'), unit=('unit', 'first'), page=('page', 'first'),
                 table_caption=('table_caption', 'first'), is_estimate=('is_estimate', 'max')).reset_index())
    sums['country_name_raw'] = 'World total (computed sum)'
    sums['row_kind'] = 'world_computed'
    sums['iso3'] = 'WLD'
    df = pd.concat([df, sums], ignore_index=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_parquet(OUT, index=False)
    print('wrote %s: %d rows, %d editions, %d commodities'
          % (OUT, len(df), df.edition_year.nunique(), df.commodity.nunique()))
    miss = sorted({n for n, i, k in zip(df.country_name_raw, df.iso3, df.row_kind)
                   if k == 'country' and not i})
    if miss:
        print('unmapped country names (%d): %s' % (len(miss), ', '.join(miss[:15])))


if __name__ == '__main__':
    main()
