#!/usr/bin/env python3
"""USGS Historical Statistics (Data Series 140) -> cube rows.

Found by the coverage catalog: raw/usgs_hist holds 84 workbooks that have been sitting in the repo
with only their price column ever extracted. They carry annual series from 1900 - and, crucially,
66 of them carry a WORLD PRODUCTION column, which the BGS spine (1970-) cannot provide. That makes
this the cheapest available extension of the cube's time depth by seventy years.

What is ingested, and what is deliberately labelled rather than hidden:
  * US series (production, mine/primary/secondary, imports, exports, stocks, shipments) -> USA
  * World production / world mine / world refinery                                      -> WLD
  * Apparent consumption is USGS's OWN derived series. The council's rule is that derived
    analytics do not belong in a fact cube - but a *source-published* derived series is a
    citable object and an independent check on our own apparent-consumption method. It is kept
    under measure_family='derived_by_source' so it can never be mistaken for an observation.
  * Unit values are a different measure family (price) and are kept apart from tonnages. Nominal
    and constant-1998 dollars are distinct measures, not one series.
  * 'W' (withheld) becomes a row with a NULL value and value_flag='withheld' - a company-
    confidential figure is not the same thing as a zero or a gap. 'NA' rows are dropped.

Run:  python build_cube_usgs.py     (invoked by build_cube.py; standalone for inspection)
"""
import os, sys, glob, warnings
warnings.filterwarnings('ignore')

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, 'raw', 'usgs_hist')

# workbook stem -> atlas material label (only where the atlas has that material; others keep
# their own name and simply ride along as context, exactly as with the BGS groups)
STEM_TO_MATERIAL = {
    'bauxite-and-alumina': 'bauxite', 'phosphate-rock': 'phosphate',
    'platinum-group-metals': 'platinum', 'rare-earths': 'rare_earths',
    'magnesium-metal': 'magnesium', 'magnesium-compounds': 'magnesium',
    'titanium-metal': 'titanium', 'titanium-minerals': 'titanium',
    'titanium-pigments': 'titanium', 'iron-and-steel': 'iron', 'iron-ore': 'iron',
    'barite': 'baryte', 'aluminum': 'aluminium', 'sulfur': 'sulphur',
    'kyanite-and-related-minerals': 'kyanite', 'construction-sand-and-gravel': 'sand_and_gravel',
    'industrial-sand-and-gravel': 'sand_and_gravel', 'boron': 'boron', 'nitrogen': 'nitrogen',
}

# column header (lowercased) -> (measure, measure_family, stage, geography)
COLMAP = {
    'imports': ('imports', 'trade', 'unspecified', 'USA'),
    'imports for consumption': ('imports', 'trade', 'unspecified', 'USA'),
    'exports': ('exports', 'trade', 'unspecified', 'USA'),
    'production': ('production', 'production', 'unspecified', 'USA'),
    'mine production': ('production', 'production', 'mine', 'USA'),
    'primary production': ('production', 'production', 'processed', 'USA'),
    'secondary production': ('production_secondary', 'production', 'processed', 'USA'),
    'smelter production': ('production', 'production', 'processed', 'USA'),
    'refinery production': ('production', 'production', 'processed', 'USA'),
    'shipments': ('shipments', 'trade', 'unspecified', 'USA'),
    'government shipments': ('shipments_government', 'trade', 'unspecified', 'USA'),
    'stocks': ('stocks', 'stocks', 'unspecified', 'USA'),
    'industry stocks': ('stocks_industry', 'stocks', 'unspecified', 'USA'),
    'government stocks': ('stocks_government', 'stocks', 'unspecified', 'USA'),
    'apparent consumption': ('apparent_consumption', 'derived_by_source', 'unspecified', 'USA'),
    'reported consumption': ('consumption', 'consumption', 'unspecified', 'USA'),
    'consumption': ('consumption', 'consumption', 'unspecified', 'USA'),
    'world production': ('production', 'production', 'unspecified', 'WLD'),
    'world mine production': ('production', 'production', 'mine', 'WLD'),
    'world refinery production': ('production', 'production', 'processed', 'WLD'),
    'world production (gross weight)': ('production', 'production', 'unspecified', 'WLD'),
    # Added 16 Sep 2026: world headers that carried a qualifier or a footnote digit, so the exact
    # match above dropped them silently - bismuth lost its world MINE series back to 1912 and
    # vermiculite its world series entirely. Each column keeps its own native_code, so lithium's
    # three world series stay three series.
    'world mine production (metal content)': ('production', 'production', 'mine', 'WLD'),
    'world production (lithium content)': ('production', 'production', 'unspecified', 'WLD'),
    'world production (lithium carbonate equivalent)': ('production', 'production', 'unspecified', 'WLD'),
    'world production2': ('production', 'production', 'unspecified', 'WLD'),
    # Added 17 Sep 2026: the US domestic detail the exact match was dropping. Components that sit
    # inside a total get their OWN measure name, so summing a measure can never double-count them.
    'producer shipments': ('shipments', 'trade', 'unspecified', 'USA'),
    'mine shipments': ('shipments', 'trade', 'mine', 'USA'),
    'production (sold or used)': ('production', 'production', 'unspecified', 'USA'),
    'sold or used': ('production', 'production', 'unspecified', 'USA'),
    'production (sales)': ('production', 'production', 'unspecified', 'USA'),
    'crushed and ground - sold or used by producers': ('production', 'production', 'processed', 'USA'),
    'refined garnet production': ('production', 'production', 'processed', 'USA'),
    'secondary production old scrap': ('production_secondary_old_scrap', 'production', 'processed', 'USA'),
    'secondary production new scrap': ('production_secondary_new_scrap', 'production', 'processed', 'USA'),
    'secondary production toll-refined': ('production_secondary_toll', 'production', 'processed', 'USA'),
    'new scrap': ('scrap_new', 'production', 'processed', 'USA'),
    'refinery scrap': ('scrap_refinery', 'production', 'processed', 'USA'),
    'recycled': ('production_secondary', 'production', 'processed', 'USA'),
    'total stocks': ('stocks', 'stocks', 'unspecified', 'USA'),
    'lme stocks': ('stocks_lme', 'stocks', 'unspecified', 'USA'),
    'estimated consumption': ('consumption', 'consumption', 'unspecified', 'USA'),
    'reported chromite ore consumption': ('consumption', 'consumption', 'mine', 'USA'),
    'reported chromium ferroalloy and metal consumption': ('consumption', 'consumption', 'processed', 'USA'),
    'reported consumption mn ore': ('consumption', 'consumption', 'mine', 'USA'),
    'reported consumption mn alloys': ('consumption', 'consumption', 'processed', 'USA'),
    'imports (feldspar and nepheline syenite)': ('imports', 'trade', 'unspecified', 'USA'),
    'imports (nepheline syenite)': ('imports_nepheline_syenite', 'trade', 'unspecified', 'USA'),
    # not tonnes: kept with their own unit, never converted
    'employment': ('employment', 'labour', 'unspecified', 'USA', 'employees'),
    'net import reliance (%)': ('net_import_reliance', 'derived_by_source', 'unspecified', 'USA', 'percent'),
    'production value ($)': ('production_value', 'price', 'unspecified', 'USA', 'USD'),
}



# Rows whose repeated year label USGS itself contradicts. Not a rule - a list, each entry carrying
# the publication that fixes the date, so no other repeated year is ever relabelled on a guess.
# Checked 16 Sep 2026 against the Mineral Commodity Summaries PDFs.
RELABEL = {
    ('nickel.xlsx', 2019): (2020, 'USGS Mineral Commodity Summaries 2022, Nickel: world mine production '
                                  '2020 = 2,510,000 t (this row: 2,510,000); LME cash 2020 = $13,772/t '
                                  '(this row: 13,800). https://pubs.usgs.gov/periodicals/mcs2022/mcs2022-nickel.pdf'),
    ('cadmium.xlsx', 2021): (2022, 'USGS Mineral Commodity Summaries 2024, Cadmium: 2022 refined production '
                                   '212 t, imports 99 t, exports 68 t, price $3.42/kg (this row: 212, 99, 68, '
                                   '3420). https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-cadmium.pdf'),
}

def classify(col):
    c = ' '.join(str(col).split()).lower().strip()
    if 'unit value' in c:
        real = '98$' in c or '98 $' in c
        return (('unit_value_real98' if real else 'unit_value_nominal'), 'price',
                'unspecified', 'USA', '1998 USD/t' if real else 'USD/t')
    hit = COLMAP.get(c)
    if hit:
        return hit if len(hit) == 5 else hit + ('metric tons',)
    return None


ANOMALIES = []


def rows_for(path):
    import openpyxl
    stem = os.path.basename(path)[:-5]
    material = STEM_TO_MATERIAL.get(stem, stem.replace('-', '_'))
    out = []
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    header = None
    seen_years = set()
    for row in ws.iter_rows(max_col=20, values_only=True):     # ONE pass (read_only)
        if row is None:
            continue
        c0 = str(row[0]).strip() if row[0] is not None else ''
        if header is None:
            if c0.lower() == 'year':
                header = list(row)
            continue
        if not c0[:4].isdigit():
            continue
        year = int(c0[:4])
        # Two USGS workbooks repeat their final year LABEL on two rows carrying different
        # figures: cadmium.xlsx has 2021 twice (241 t and 212 t), nickel.xlsx has 2019 twice.
        # The second row is almost certainly the following year - the unit value moves the way
        # the next year's price did - but "almost certainly" is not a year, and writing an
        # inferred date into a source column is how a guess becomes a fact. So the labelled row
        # is kept and the repeat is diverted to out/source_anomalies.json with its raw values,
        # visible and recoverable, rather than silently averaged into the one above it.
        fix = RELABEL.get((os.path.basename(path), year))
        if year in seen_years and fix and fix[0] not in seen_years:
            # Evidence-backed, per row: the repeat IS the following year (see RELABEL).
            ANOMALIES.append({'file': os.path.basename(path), 'material': material,
                              'repeated_year': year, 'row': [str(c) for c in row[:8]],
                              'kept': 'RELABELLED as %d' % fix[0], 'evidence': fix[1],
                              'why': 'the source repeats a year label; a later USGS publication '
                                     'prints these exact figures under the following year'})
            year = fix[0]
        elif year in seen_years:
            ANOMALIES.append({'file': os.path.basename(path), 'material': material,
                              'repeated_year': year, 'row': [str(c) for c in row[:8]],
                              'kept': 'the first row carrying this year',
                              'why': 'the source repeats a year label on two rows of different '
                                     'figures; the true year of the second cannot be read off '
                                     'the file'})
            continue
        seen_years.add(year)
        for i, cell in enumerate(row):
            if i == 0 or i >= len(header) or header[i] is None:
                continue
            spec = classify(header[i])
            if not spec:
                continue
            measure, family, stage, geo, unit = spec
            raw = str(cell).strip() if cell is not None else ''
            if raw in ('', 'NA', 'na', '--', 'None'):
                continue
            flag, val = None, None
            if raw.upper() in ('W', 'XX'):
                flag = 'withheld'                     # company-confidential, not a zero
            else:
                try:
                    val = float(raw.replace(',', ''))
                except ValueError:
                    continue
            out.append({
                'material': material, 'source_group': stem, 'country_iso3': geo, 'year': year,
                'measure_family': family, 'measure': measure,
                'flow_direction': {'imports': 'in', 'exports': 'out'}.get(measure),
                'stage': stage, 'code_system': 'USGS DS140 column',
                'native_code': f'{stem}:{str(header[i]).strip()}',
                'native_label': str(header[i]).strip(), 'sub_commodity': None,
                'value': val, 'unit': unit,
                'value_t': val if (unit == 'metric tons' and val is not None) else None,
                'conversion_factor': 1.0 if unit == 'metric tons' else None,
                'basis': 'gross' if unit == 'metric tons' else None,
                'source': 'USGS Historical Statistics (DS 140)',
                'series_id': f'USGS-DS140:{stem}:{measure}:{geo}',
                'precision': None, 'value_flag': flag,
            })
    wb.close()
    return out


def build():
    rows = []
    for f in sorted(glob.glob(os.path.join(HIST, '*.xlsx'))):
        try:
            rows.extend(rows_for(f))
        except Exception as e:
            print(f'  skip {os.path.basename(f)}: {e}')
    if ANOMALIES:
        import json as _json
        path = os.path.join(ROOT, 'out', 'source_anomalies.json')
        prev = {}
        if os.path.exists(path):
            try:
                prev = _json.load(open(path, encoding='utf-8'))
            except Exception:
                prev = {}
        prev['usgs_ds140_repeated_year'] = {
            'note': 'Rows where the source repeats a year label on two rows of different '
                    'figures. A row is RELABELLED only where a later USGS publication prints those '
                    'exact figures under the following year (the evidence is on the row); any other '
                    'repeat is discarded here, raw values kept, rather than given an invented date.',
            'rows': ANOMALIES}
        _json.dump(prev, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print(f'  {len(ANOMALIES)} repeated-year rows recorded in out/source_anomalies.json')
    return rows


if __name__ == '__main__':
    import pandas as pd
    sys.stdout.reconfigure(encoding='utf-8')
    df = pd.DataFrame(build())
    print(f'{len(df):,} rows from {df.source_group.nunique()} commodities, '
          f'{int(df.year.min())}-{int(df.year.max())}')
    print('  by geography:', df.country_iso3.value_counts().to_dict())
    print('  by family:   ', df.measure_family.value_counts().to_dict())
    print('  withheld:    ', int((df.value_flag == 'withheld').sum()))
