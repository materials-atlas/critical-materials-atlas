#!/usr/bin/env python3
"""IEA Critical Minerals Dataset -> cube rows. The fifth source, and a correction.

The owner asked why the IEA Global Critical Minerals Outlook was not in the cube. The answer I had
been giving - "IEA is scenario projections, and forecasts must not sit in a table of observations" -
was true of most of it and WRONG about the part that matters.

The Data Explorer's "Total supply for key minerals" sheet is laid out as country x year, and its
FIRST column is that edition's OBSERVED base year, not a projection. It gives country-level
supply for copper, cobalt, lithium, nickel, graphite and magnet rare earths at BOTH the mining and
refining stage - and refining-by-country is precisely the layer where BGS coverage is thinnest and
where the atlas's chokepoint argument actually lives.

So the rule was right but applied too bluntly. What is ingested and what is not:
  INGESTED  each edition's base-year column only - country-level, current, an observation. The
            base year is DETECTED per file (May-2025 observes 2024; Jul-2026 observes 2025) and the
            edition travels with the row, so two editions are two vintages rather than a collision.
  NOT       the 2030 / 2035 / 2040 columns. Those are scenario projections; mixing them into a table of
            observations would let a later query difference a forecast against measured history and
            call the result a trend.
  NOT       the demand-scenario files (STEPS / APS / NZE growth multipliers) for the same reason.
  NOT       iea_supply_concentration.csv's top1_share / top3_share. Those are already-computed
            concentration statistics; the cube stores observations and computes concentration
            itself. Storing a derived index would freeze someone else's methodology into our data.

Licence: IEA Critical Minerals Dataset, CC BY 4.0, attribution required.

Run:  python build_cube_iea.py     (invoked by build_cube.py; standalone for inspection)
"""
import os, sys, csv, warnings
warnings.filterwarnings('ignore')

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
import glob as _glob
XLSX_GLOB = os.path.join(ROOT, 'raw', 'iea', 'CM_Data_Explorer*.xlsx')
CODES = os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv')
SHEET = '2 Total supply for key minerals'
# Each EDITION publishes its own observed base year in the first year column - May-2025 observes
# 2024, Jul-2026 observes 2025. So the base year is detected per file rather than assumed, and the
# edition travels with the row: two editions are two vintages of the same series, not a collision.
EDITION_OF = {'CM_Data_Explorer.xlsx': '2025-05', 'CM_Data_Explorer_2026-07.xlsx': '2026-07',
              'CM_Data_Explorer_2024-05.xlsx': '2024-05', 'CM_Data_Explorer_2023-07.xlsx': '2023-07'}

IEA_TO_MATERIAL = {
    'copper': 'copper', 'cobalt': 'cobalt', 'lithium': 'lithium', 'nickel': 'nickel',
    'graphite': 'graphite', 'magnet rare earth elements': 'rare_earths',
}
STAGE = {'mining': 'mine', 'refining': 'processed'}
# IEA units differ per mineral; the sheet is in kt for the base metals and kt for the minor ones
# as published. Values are used as given, in thousand tonnes, and converted to tonnes.
KT_TO_T = 1000.0


def name_to_iso():
    m = {}
    with open(CODES, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            n, iso = row.get('country_name'), row.get('country_iso3')
            if n and iso and len(iso) == 3:
                m[n.strip().lower()] = iso.strip()
    m.update({
        'united states': 'USA', 'russia': 'RUS', 'china': 'CHN', 'chile': 'CHL', 'peru': 'PER',
        'japan': 'JPN', 'india': 'IND', 'indonesia': 'IDN', 'australia': 'AUS',
        'democratic republic of the congo': 'COD', 'dr congo': 'COD',
        'democratic republic of congo': 'COD', 'south korea': 'KOR', 'korea': 'KOR',
        'south africa': 'ZAF', 'brazil': 'BRA', 'canada': 'CAN', 'philippines': 'PHL',
        'zimbabwe': 'ZWE', 'argentina': 'ARG', 'mexico': 'MEX', 'finland': 'FIN',
        'madagascar': 'MDG', 'new caledonia': 'NCL', 'myanmar': 'MMR', 'malaysia': 'MYS',
        'mozambique': 'MOZ', 'tanzania': 'TZA', 'poland': 'POL', 'kazakhstan': 'KAZ',
        'zambia': 'ZMB', 'turkey': 'TUR', 'vietnam': 'VNM', 'estonia': 'EST', 'norway': 'NOR',
        "lao people's democratic republic": 'LAO', 'laos': 'LAO',
    })
    return m


def build():
    out = []
    for path in sorted(_glob.glob(XLSX_GLOB)):
        out.extend(_build_one(path))
    return out


def _build_one(XLSX):
    import openpyxl
    n2i = name_to_iso()
    edition = EDITION_OF.get(os.path.basename(XLSX), 'unknown')
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    rows_x = list(wb[SHEET].iter_rows(max_col=20, values_only=True))
    wb.close()

    # the year header row, and THIS edition's observed base year = its earliest year column
    year_row = next((r for r in rows_x if r and sum(
        1 for c in r if isinstance(c, (int, float)) and 2000 < c < 2100) >= 2), None)
    if year_row is None:
        return []
    years_present = [int(c) for c in year_row if isinstance(c, (int, float)) and 2000 < c < 2100]
    OBS_YEAR = min(years_present)
    out, unmapped = [], set()
    for ri, r in enumerate(rows_x):
        for ci, cell in enumerate(r):
            if not (cell and isinstance(cell, str) and ' - ' in cell):
                continue
            head = cell.strip()
            mineral, _, stage_txt = head.partition(' - ')
            stage_key = stage_txt.split('(')[0].strip().lower()
            material = IEA_TO_MATERIAL.get(mineral.strip().lower())
            if not material or stage_key not in STAGE:
                continue
            # the 2024 column for THIS block: the first year column at or after the header column
            col = next((i for i, v in enumerate(year_row)
                        if i >= ci and isinstance(v, (int, float)) and v == OBS_YEAR), None)
            if col is None:
                continue
            for rr in rows_x[ri + 1:]:
                if not rr or ci >= len(rr) or rr[ci] in (None, ''):
                    break                                  # block ends at the first blank label
                label = str(rr[ci]).strip()
                if col >= len(rr) or rr[col] in (None, ''):
                    continue
                try:
                    v = float(rr[col])
                except (TypeError, ValueError):
                    continue
                low = label.lower()
                if low.startswith('rest of world'):
                    continue                               # a residual, not a country
                iso = 'WLD' if low == 'total' else n2i.get(low)
                if not iso:
                    unmapped.add(label); continue
                if v <= 0:
                    continue
                out.append({
                    'material': material, 'source_group': f'IEA {edition}:{head}',
                    'country_iso3': iso,
                    'year': OBS_YEAR, 'measure_family': 'production', 'measure': 'production',
                    'flow_direction': None, 'stage': STAGE[stage_key],
                    'code_system': f'IEA CM Data Explorer {edition}', 'native_code': head,
                    'native_label': head, 'sub_commodity': None,
                    'value': v, 'unit': 'thousand tonnes',
                    'value_t': v * KT_TO_T, 'conversion_factor': KT_TO_T, 'basis': 'gross',
                    'source': 'IEA Critical Minerals Dataset', 'series_id': f'IEA {edition}:{head}:production',
                    'precision': None, 'value_flag': None,
                })
    if unmapped:
        print(f'  IEA {edition}: unmapped labels {sorted(unmapped)[:4]}')
    print(f'  IEA {edition}: base year {OBS_YEAR}, {len(out)} rows')
    return out


if __name__ == '__main__':
    import pandas as pd
    sys.stdout.reconfigure(encoding='utf-8')
    df = pd.DataFrame(build())
    if df.empty:
        print('no rows'); raise SystemExit
    print(f'{len(df)} rows | {df.material.nunique()} materials | {df.country_iso3.nunique()} geographies')
    print('  by stage:', df.stage.value_counts().to_dict())
    print('  world rows:', int((df.country_iso3 == 'WLD').sum()))
    for m in sorted(df.material.unique()):
        d = df[df.material == m]
        print(f'   {m:<12} {len(d):>3} rows  stages {sorted(d.stage.unique())}')
