#!/usr/bin/env python3
"""CEPII BACI bilateral trade -> cube rows (country-year, mapped codes only).

Third ingest. BACI reconciles the two sides of every reported shipment, so it is the best public
bilateral trade source; the HS02 vintage runs 2002-2024, which matches the depth the cube now has
on the production side.

TWO DELIBERATE NARROWINGS, both on the council's advice:

  * ONLY MAPPED CODES. "Full BACI is ballast - ingest mapped CRM-relevant codes only, catalog the
    rest." 47 HS6 codes are mapped to atlas materials in out/crosswalk.json; the other ~5,000 stay
    out of the fact table and live in the coverage catalog instead.

  * AGGREGATED TO COUNTRY-YEAR. The cube's grain is (material, country, year, measure). Bilateral
    pairs are a different grain and would silently double every total the moment someone summed
    the column. Exports are summed over destinations, imports over origins; the bilateral detail
    stays in pipeline/data/ where the trade layer already uses it.

An HS code is a poor proxy for a material - several carry more than one metal - so the mapping is
recorded per row in native_code, and the crosswalk's own `flags` (e.g. 'shared' HS lines) travel
with it. Never treat an HS-mapped tonnage as a measurement of the metal itself.

Run:  python build_cube_baci.py     (invoked by build_cube.py; standalone for inspection)
"""
import os, sys, json, zipfile, csv, io
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS02_V202601.zip')
CODES_CSV = None  # served by _baci.country_file()


def load_maps():
    cw = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))
    code2mat = {}                                     # hs6 -> list of (material, stage)
    for mat, v in cw.items():
        for c in (v.get('ore_hs') or []):
            code2mat.setdefault(str(c), []).append((mat, 'mine'))
        for c in (v.get('refined_hs') or []):
            code2mat.setdefault(str(c), []).append((mat, 'processed'))
        # COMPOUND: the traded chemical one step from the metal (antimony oxides, lithium
        # hydroxide, nickel sulphate...). Its own stage, because a tonne of oxide is not a tonne
        # of metal and must never be summed with one. Added 9 Sep 2026; see build_crosswalk.py.
        for c in (v.get('compound_hs') or []):
            code2mat.setdefault(str(c), []).append((mat, 'compound'))
    num2iso = {}
    with _baci.country_file() as f:
        for row in csv.DictReader(f):
            code = row.get('country_code') or row.get('code')
            iso = row.get('country_iso3') or row.get('iso_3digit_alpha') or row.get('iso3')
            if code and iso and len(str(iso)) == 3:
                num2iso[str(code).strip()] = str(iso).strip()
    return code2mat, num2iso


def build(years=None):
    code2mat, num2iso = load_maps()
    wanted = set(code2mat)
    agg = {}                                          # (mat, stage, iso, year, measure) -> tonnes
    for yr in _baci.NOMENCLATURE['HS02']:          # 2002-2024, all in HS02 - as the archive loop always did
        if years and yr not in years:
            continue
        for row in _baci.year(yr, columns=['i', 'j', 'k', 'q'], codes=wanted, nom='HS02').itertuples(index=False):
            k = row.k
            q = row.q
            if q != q:
                continue                          # value-only row: no tonnage to record
            if q <= 0:
                continue
            ex, im = num2iso.get(str(row.i)), num2iso.get(str(row.j))
            for mat, stage in code2mat[k]:
                if ex:
                    key = (mat, stage, ex, yr, 'exports', k)
                    agg[key] = agg.get(key, 0.0) + q
                if im:
                    key = (mat, stage, im, yr, 'imports', k)
                    agg[key] = agg.get(key, 0.0) + q
    rows = []
    for (mat, stage, iso, yr, meas, k), tonnes in agg.items():
        rows.append({
            'material': mat, 'source_group': f'BACI HS02:{k}', 'country_iso3': iso, 'year': yr,
            'measure_family': 'trade', 'measure': meas,
            'flow_direction': 'in' if meas == 'imports' else 'out', 'stage': stage,
            'code_system': 'HS02', 'native_code': k, 'native_label': f'HS {k}',
            'sub_commodity': None, 'value': tonnes, 'unit': 'tonnes (metric)',
            'value_t': tonnes, 'conversion_factor': 1.0, 'basis': 'gross',
            'source': 'CEPII BACI (HS02)', 'series_id': f'BACI-HS02:{k}:{meas}',
            'precision': None, 'value_flag': None,
        })
    return rows


if __name__ == '__main__':
    import pandas as pd
    sys.stdout.reconfigure(encoding='utf-8')
    df = pd.DataFrame(build())
    print(f'{len(df):,} rows | {df.material.nunique()} materials | '
          f'{df.country_iso3.nunique()} countries | {df.year.min()}-{df.year.max()}')
    print('  by measure:', df.measure.value_counts().to_dict())
    print('  distinct HS codes:', df.native_code.nunique())
