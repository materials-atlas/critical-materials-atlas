# -*- coding: utf-8 -*-
"""Extract the by-country production tables from the USGS Minerals Yearbook chapters.

What this is for. The Atlas has a mine layer it trusts and a REFINING layer it has had to
approximate from industry estimates. The Yearbook prints the refining layer outright: for copper
alone, 2022 carries TABLE 20 world mine production, TABLE 21 world SMELTER production and TABLE 22
world REFINERY production, each by country and each five years wide. That is the stage the trade
data cannot see and the stage the whole exporter-versus-producer finding turns on.

Read geometrically, for three reasons measured in the files rather than assumed:

1. THE TEXT STREAM IS NOT THE COLUMN ORDER. On the 2022 copper mine-production table, Albania's
   row arrives in the stream as 2,080 / 2,520 / 3,470 / 3,520 / 4,430 - ascending by value. The x
   coordinates put them in the true order 2,520 / 2,080 / 3,520 / 4,430 / 3,470 against 2018-2022.
   Anything that trusts the reading order silently scrambles every row it touches.

2. FOOTNOTE AND REVISION MARKERS SIT ON THEIR OWN LINE, slightly above the row: Armenia's values
   are at y=121.71 and its "r, e, 3" markers at y=121.34. They are 5.40pt against the values'
   8.04pt, so size separates them - the same mechanism parse_usgs_mcs.py relies on, where a
   superscript footnote marker would otherwise turn 100,000 into 7100,000.

3. A TABLE SPANS PAGES, and each continuation page reprints its caption ("TABLE 20-Continued") and
   its header. So every page can be parsed on its own header rather than inheriting one, which is
   what makes a mid-table page break harmless.

Writes pipeline/data/usgs_myb_production.parquet.
Usage:  python pipeline/parse_usgs_myb.py [copper gallium ...] [--years 2022] [--report]
"""
import argparse
import io
import os
import re
import sys
from collections import Counter

import fitz
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, 'raw', 'usgs_myb')
OUT = os.path.join(HERE, 'data', 'usgs_myb_production.parquet')

CONTENT_PT = 7.0          # below this a span is a marker, not content (measured: 5.40 vs 8.04)
ROW_TOL = 2.0             # a row's spans share a y within this, markers included
LABEL_GAP = 40.0          # a span this far left of the first year column is the row label
INDENT_PT = 3.0           # a label further right than the page's leftmost label by more than this
                          # is a SUB-ROW. Measured on 2022 copper: country labels sit at x=70.7 to
                          # 72.0 and product sub-rows at x=78.2. Without this the parent set by
                          # "Australia:" leaked onto every later country, so no row was ever
                          # classified as a country at all and the level sums were meaningless.

CAPTION = re.compile(r'^TABLE\s+(\d+)', re.I)
# The tables worth taking: a production or capacity table broken down BY COUNTRY, worldwide.
#
# The scope test is as important as the subject. A bare "PRODUCTION CAPACITY" also matches
# "PRIMARY ANNUAL ALUMINUM PRODUCTION CAPACITY IN THE UNITED STATES, BY COMPANY" - a US
# plant-level table whose rows are Alcoa and Century Aluminum, not countries. It was the worst
# offender in the grand-total check, 113-123% over, because company names were being written into
# the country field. Plant-level US capacity is interesting and is a DIFFERENT dataset; mixing it
# into a country panel is how a table silently means something other than its column names.
WANTED = re.compile(r'WORLD\s+(MINE|SMELTER|REFINERY)\s+PRODUCTION'
                    r'|WORLD\s+PRODUCTION'
                    r'|WORLD\s+.{0,40}?PRODUCTION\s+CAPACITY'
                    r'|PRODUCTION,?\s+BY\s+COUNTRY', re.I)
EXCLUDE = re.compile(r'IN\s+THE\s+UNITED\s+STATES|BY\s+COMPANY|BY\s+STATE|BY\s+END\s+USE'
                     r'|U\.S\.\s+(IMPORTS|EXPORTS)', re.I)
STAGE = [('REFINERY', 'refinery'), ('SMELTER', 'smelter'), ('MINE', 'mine'),
         ('CAPACITY', 'capacity'), ('WORLD PRODUCTION', 'production')]
YEAR = re.compile(r'^(19|20)\d{2}$')
# A single-line country carries its product in the same cell - "Chile, primary", "Albania,
# concentrates" - so the country field has to be trimmed or it will never join to the atlas's
# country list. Only a KNOWN qualifier is stripped: real country names contain commas too
# ("Korea, Republic of", "Bolivia, Plurinational State of"), and splitting on the comma would
# quietly rename them.
QUALIFIER = re.compile(r',\s*(primary\s+and\s+secondary|primary|secondary|concentrates?|'
                       r'leaching,?\s*electrowon|refined|metal|smelter|mine|'
                       r'direct\s+shipping\s+ores?|ores?\s+and\s+concentrates?)\s*$', re.I)
NUM = re.compile(r'^\(?-?[\d,]+(\.\d+)?\)?$')
# Values that are not numbers but are meaningful, straight from the USGS conventions.
NOTVALUE = {'--': 'nil', 'NA': 'not available', 'W': 'withheld', '(3)': 'see footnote'}

# These tables are HIERARCHICAL, and leaving that to be inferred is how a reader double-counts.
# A country may print sub-rows by product ("Chile:" over "Concentrates" and "Leaching, electrowon")
# then its own "Total"; the table closes with "Grand total" and an "Of which" breakdown. Summing
# the column adds all four levels: for 2022 copper mine output that is 65.7 Mt against a printed
# grand total of 21.9 Mt. So every row is tagged, and nothing has to be guessed from the label.
GRAND = re.compile(r'^grand\s+total$', re.I)
OFWHICH = re.compile(r'^of\s+which', re.I)
# A country's own total is not always printed as "Total". The refinery tables split primary from
# secondary output, so China's country line reads "Total, primary and secondary" above its
# "Total, primary" and "Secondary" components - and matching only "Total" left the country level
# 54.6% short of the printed grand total. "Total, primary" alone must NOT match: it is a component.
TOTAL_ONLY = re.compile(r'^total(,?\s*primary\s+and\s+secondary)?$', re.I)


def spans(page):
    """(y, x, size, text) for every non-empty span on the page."""
    out = []
    for blk in page.get_text('dict').get('blocks', []):
        for ln in blk.get('lines', []):
            for sp in ln.get('spans', []):
                t = (sp.get('text') or '').strip()
                if t:
                    out.append((sp['bbox'][1], sp['bbox'][0], sp.get('size', 0.0), t))
    out.sort()
    return out


def grouped_rows(sp):
    """Spans gathered into rows by y, each row's spans sorted by x."""
    rows = []
    for y, x, size, t in sp:
        if rows and abs(y - rows[-1][0]) <= ROW_TOL:
            rows[-1][1].append((x, size, t))
        else:
            rows.append((y, [(x, size, t)]))
    return [(y, sorted(cells)) for y, cells in rows]


def captions_of(rows):
    """Every table caption on the page, as (row_index, table_no, subject).

    A page can carry TWO tables, and reading only the first caption loses the second silently.
    On the 2020 barite chapter, page 11 holds TABLE 7 (U.S. imports of barium chemicals) above
    TABLE 8 (BARITE: WORLD PRODUCTION, BY COUNTRY) - the one table in the chapter we want. Table 7
    does not match, so the whole page was skipped and barite produced no rows at all. The 2021
    helium chapter is the worse version of the same shape: there TABLE 7 is a production-capacity
    table, which DOES match, so the page was accepted and TABLE 8's rows would have been read in
    under the capacity table's subject and unit.
    """
    out = []
    for i, (y, cells) in enumerate(rows):
        joined = ' '.join(t for _, size, t in cells if size >= CONTENT_PT).strip()
        m = CAPTION.match(joined)
        if m:
            subject = []
            for y2, c2 in rows[i + 1:i + 4]:
                line = ' '.join(t for _, size, t in c2 if size >= CONTENT_PT).strip()
                if line:
                    subject.append(line)
            out.append((i, int(m.group(1)), ' '.join(' '.join(subject).split())))
    return out


def header_of(rows):
    """{year: x} from the header line, or {} when this page has no year header."""
    for y, cells in rows:
        years = {int(t): x for x, size, t in cells if size >= CONTENT_PT and YEAR.match(t)}
        if len(years) >= 2:
            return years
    return {}


def stage_of(subject):
    up = subject.upper()
    for needle, name in STAGE:
        if needle in up:
            return name
    return 'production'


def unit_of(subject):
    m = re.search(r'\(([^)]*(?:tons|kilograms|grams|carats|cubic|pounds|troy)[^)]*)\)',
                  subject, re.I)
    return ' '.join(m.group(1).split()) if m else ''


def page_rows(rows, years):
    """(label_x, label, values, markers) for each candidate row, header and footnotes dropped."""
    first_year_x = min(years.values())
    out = []
    for y, cells in rows:
        content = [(x, t) for x, size, t in cells if size >= CONTENT_PT]
        markers = ' '.join(t for x, size, t in cells if size < CONTENT_PT)
        if not content:
            continue
        label_parts = [(x, t) for x, t in content if x < first_year_x - LABEL_GAP]
        values = [(x, t) for x, t in content if x >= first_year_x - LABEL_GAP]
        if not label_parts:
            continue
        label = ' '.join(t for _, t in label_parts).strip()
        if YEAR.match(label) or label.lower().startswith('country or locality'):
            continue                                     # the header itself
        if re.match(r'^\d+\s*[A-Z(]', label) or len(label) > 70:
            continue                                     # a footnote paragraph, not a row
        out.append((min(x for x, _ in label_parts), label, values, markers))
    return out


def parse_page(rows, years):
    """Rows of (kind, country, label, year, value, note, markers) from one page of a table."""
    out = []
    order = sorted(years.items(), key=lambda kv: kv[1])
    cand = page_rows(rows, years)
    if not cand:
        return out
    # The country indent is the leftmost indent that RECURS. Taking the plain minimum put base_x
    # at 36.1 on the 2022 copper page - page furniture in the left margin - which made every real
    # row look indented, so nothing was ever classified as a country. Levels that matter appear
    # many times over (countries at x=72.0, product sub-rows at 79.5, a country Total at 87.1);
    # furniture and the table caption appear once.
    counts = Counter(round(lx, 0) for lx, _, _, _ in cand)
    recurring = [x for x, n in counts.items() if n >= 3]
    base_x = min(recurring) if recurring else min(lx for lx, _, _, _ in cand)
    parent, parent_kind = '', ''
    for label_x, label, values, markers in cand:
        top_level = label_x <= base_x + INDENT_PT
        if not values:
            # "Mexico:" heads indented sub-rows; "Of which:" heads the grand total's breakdown.
            # Only a row at the country indent can be a parent - otherwise the table caption,
            # which also carries no values, became the parent of every row beneath it.
            if top_level or OFWHICH.match(label):
                parent = label.rstrip(':')
                parent_kind = 'of_which' if OFWHICH.match(parent) else 'country'
            continue
        # The header line repeats inside some tables with a non-year label ("Company and
        # location"), and its cells ARE the years, so it would otherwise be stored as a row whose
        # value for 2020 is 2020. A row whose every value is one of this table's own years is the
        # header, whatever its label says.
        numeric = [t for _, t in values if NUM.match(t)]
        if numeric and all(t.replace(',', '') in {str(y) for y in years} for t in numeric):
            continue
        for x, t in values:
            # the year whose column centre is nearest this value
            yr = min(order, key=lambda kv: abs(kv[1] - x))[0]
            note = NOTVALUE.get(t)
            val = None
            if note is None and NUM.match(t):
                neg = t.startswith('(') and t.endswith(')')
                try:
                    val = float(t.strip('()').replace(',', ''))
                    if neg:
                        val = -val
                except ValueError:
                    val = None
            if val is None and note is None:
                continue                                 # not a value and not a known convention
            if GRAND.match(label):
                kind, country = 'grand_total', ''
            elif OFWHICH.match(label):
                kind, country = 'of_which', ''
            elif parent_kind == 'of_which':
                kind, country = 'of_which', ''
            elif TOTAL_ONLY.match(label) and parent:
                kind, country = 'country_total', parent
            elif parent and not top_level:
                kind, country = 'subrow', parent
            else:
                kind, country = 'country', label
            country = QUALIFIER.sub('', country).strip().rstrip(':') if country else country
            out.append({'parent': parent, 'label': label, 'kind': kind, 'country': country,
                        'year': yr, 'value': val, 'note': note, 'markers': markers})
        if GRAND.match(label):
            parent, parent_kind = '', ''     # the grand total closes the country list
        elif values and top_level and not TOTAL_ONLY.match(label):
            parent, parent_kind = '', ''     # a country printed on one line ends the previous group
    return out


def parse_chapter(path):
    m = re.search(r'myb1-(\d{4})-([a-z0-9\-]+)\.pdf$', os.path.basename(path))
    if not m:
        return []
    edition, commodity = int(m.group(1)), m.group(2)
    doc = fitz.open(path)
    recs = []
    cur = None                      # (table_no, subject) carried across continuation pages
    try:
        for pno in range(doc.page_count):
            rows = grouped_rows(spans(doc[pno]))
            caps = captions_of(rows)
            # Each caption owns the band of rows from itself to the next caption. A page with no
            # caption at all is a continuation of whatever table was running.
            bands = []
            if not caps:
                if cur is not None:
                    bands.append((rows, cur))
            else:
                for j, (i, tno, subject) in enumerate(caps):
                    end = caps[j + 1][0] if j + 1 < len(caps) else len(rows)
                    if i > 0 and j == 0 and cur is not None:
                        bands.append((rows[:i], cur))      # tail of the previous table
                    ok = WANTED.search(subject or '') and not EXCLUDE.search(subject or '')
                    cur = (tno, subject) if ok else None
                    if cur is not None:
                        bands.append((rows[i:end], cur))
            for band, (tno, subject) in bands:
                years = header_of(band)
                if not years:
                    continue
                for r in parse_page(band, years):
                    r.update({'commodity': commodity, 'edition': edition, 'table': tno,
                              'stage': stage_of(subject), 'unit': unit_of(subject),
                              'page': pno + 1, 'subject': subject})
                    recs.append(r)
    finally:
        doc.close()
    return recs


def validate(df):
    """Check the extraction against the tables' OWN printed grand totals.

    The only check that needs no external source: each table prints its world total, so summing
    one row per country must reproduce it. USGS rounds to three significant digits and says so, so
    agreement is never exact - the question is the distribution. This is what caught the two
    defects that mattered: company names being written into the country field (aluminum capacity,
    113-123% over) and a country total printed as "Total, primary and secondary" rather than
    "Total" (copper refinery, 54.6% short).
    """
    import numpy as np
    rows = []
    for k, s in df.groupby(['commodity', 'edition', 'table', 'stage', 'year']):
        g = s[s.kind == 'grand_total'].value
        if not len(g) or not np.isfinite(g.iloc[0]) or g.iloc[0] == 0:
            continue
        tot = s[s.kind == 'country_total'].set_index('country').value
        plain = s[s.kind == 'country'].set_index('country').value
        per = pd.concat([tot, plain[~plain.index.isin(tot.index)]]).dropna()
        if per.empty:
            continue
        rows.append({'commodity': k[0], 'edition': k[1], 'stage': k[3], 'year': k[4],
                     'printed': g.iloc[0], 'summed': per.sum(), 'countries': len(per),
                     'pct': 100 * (per.sum() - g.iloc[0]) / g.iloc[0]})
    if not rows:
        print('no table printed a grand total to check against')
        return
    v = pd.DataFrame(rows)
    ab = v.pct.abs()
    print()
    print('%d tables checked against their own printed grand total, %d commodities'
          % (len(v), v.commodity.nunique()))
    for lo, hi, lbl in ((0, 0.5, 'within 0.5%'), (0.5, 2, '0.5-2%'),
                        (2, 10, '2-10%'), (10, 1e9, 'over 10%')):
        n = int(((ab >= lo) & (ab < hi)).sum())
        print('   %-13s %5d  (%4.1f%%)' % (lbl, n, 100.0 * n / len(v)))
    print('   median deviation %.3f%%, 90th percentile %.2f%%' % (ab.median(), ab.quantile(0.9)))
    worst = v.reindex(ab.sort_values(ascending=False).index).head(5)
    if len(worst) and abs(worst.pct.iloc[0]) >= 2:
        print('   worst, which is where to look next:')
        for _, r in worst.iterrows():
            print('      %-20s %d %-11s %d  printed %12s  summed %12s  %+7.1f%%'
                  % (r.commodity, r.edition, r.stage, r.year,
                     format(int(r.printed), ','), format(int(r.summed), ','), r.pct))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('commodities', nargs='*')
    ap.add_argument('--years', type=int, nargs='*')
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--validate', action='store_true',
                    help="check the extraction against each table's own printed grand total")
    a = ap.parse_args()

    files = []
    for ydir in sorted(os.listdir(RAW)):
        if not ydir.isdigit() or (a.years and int(ydir) not in a.years):
            continue
        for f in sorted(os.listdir(os.path.join(RAW, ydir))):
            if not f.endswith('.pdf'):
                continue
            if a.commodities and not any(c in f for c in a.commodities):
                continue
            files.append(os.path.join(RAW, ydir, f))

    print('%d chapter(s) to read' % len(files), flush=True)
    recs, empty = [], []
    for i, f in enumerate(files, 1):
        try:
            got = parse_chapter(f)
        except Exception as e:
            print('   %-46s FAILED %s' % (os.path.basename(f), type(e).__name__), flush=True)
            continue
        recs.extend(got)
        if not got:
            empty.append(os.path.basename(f))
        if a.report or i % 25 == 0:
            print('   %-46s %5d rows' % (os.path.basename(f), len(got)), flush=True)

    df = pd.DataFrame(recs)
    if df.empty:
        print('nothing extracted')
        return 1
    df = df[['commodity', 'edition', 'table', 'stage', 'unit', 'kind', 'country',
             'parent', 'label', 'year', 'value', 'note', 'markers', 'page', 'subject']]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_parquet(OUT, index=False)

    print()
    print('%s rows from %d chapters -> %s'
          % (format(len(df), ','), len(files) - len(empty), os.path.relpath(OUT, ROOT)))
    print('commodities %d   editions %s' % (df.commodity.nunique(),
                                            '-'.join(str(x) for x in (df.edition.min(), df.edition.max()))))
    print('by stage:')
    for stage, n in df.stage.value_counts().items():
        print('   %-12s %8s rows   %3d commodities'
              % (stage, format(n, ','), df[df.stage == stage].commodity.nunique()))
    if empty:
        print('no table found in %d chapter(s): %s%s'
              % (len(empty), ', '.join(empty[:6]), ' ...' if len(empty) > 6 else ''))
    if a.validate:
        validate(df)
    return 0


if __name__ == '__main__':
    sys.exit(main())
