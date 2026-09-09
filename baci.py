# -*- coding: utf-8 -*-
"""CEPII BACI, the one door. Phase 2 of ARCHITECTURE.md.

WHY THIS FILE EXISTS
Measured by running every builder under an audit hook: 56 builders open raw/baci/ themselves - 39
unzip the archives, 15 read only the country-code file - and 53 of them hold their own copy of the
country mapping. Twenty carry an identical two-line override dict (Taiwan, and Namibia whose ISO2
"NA" collides with the missing-value sentinel). Identical today by luck: nothing enforces it, and
one correction to that mapping would have to be made in twenty places, which is exactly how the
Republic-of-Congo fix had to be made twice.

So this is the only legal reader of raw/baci/. Everything else reads the extract through it.

WHAT IT SERVES
- countries()   the BACI numeric code -> iso2, iso3, name, with the two overrides applied ONCE.
- year(y)       one archive member as a DataFrame: t, i, j, k, v, q - the whole basket, ~11M rows
                for a recent year - read from extract/baci/<HS>/Y<year>.parquet, not the zip.
                i and j come back as BACI numeric codes; ask for iso='iso3' or 'iso2' to map them.
- years(...)    several, concatenated.
- crm_codes()   the 47 HS6 codes the atlas tracks (out/crosswalk.json, the superset of the
                pipeline's 31), so year(y, codes=crm_codes()) is the cube-grain subset.

WHAT IT PRESERVES, DELIBERATELY
- k is a STRING. HS codes carry leading zeros (010121) and any integer inference destroys them.
- v and q are floats with NULL where BACI wrote the literal NA. Readers that used to test for
  the string "NA" must test isna() instead - the acceptance harness catches any that were missed.
- i and j stay numeric until you ask, because some readers key on the number and some on ISO.

WHAT IT DOES NOT DO
It does not open a zip. extract_baci.py (top level, one writer) does that, once, and this module
refuses to serve a year that has not been extracted rather than quietly falling back to the
archive - a fallback would be a second door.
"""
import csv
import functools
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, 'raw', 'baci')
EXTRACT = os.path.join(ROOT, 'extract', 'baci')
VINTAGE = 'V202601'

# Which nomenclature holds which years. HS02 stops at 2016 and HS17 begins there, and nothing
# in this repository should ever have to know that again.
NOMENCLATURE = {'HS02': range(2002, 2017), 'HS17': range(2017, 2025)}

# The two overrides that twenty files carried separately. Taiwan is not in CEPII's ISO table;
# Namibia's ISO2 is the string "NA", which every csv reader on earth treats as missing.
FORCE = {
    '490': {'iso2': 'TW', 'iso3': 'TWN', 'name': 'Taiwan'},
    '516': {'iso2': 'NA', 'iso3': 'NAM', 'name': 'Namibia'},
}


class NotExtracted(Exception):
    """The year exists in the archive but not in extract/. Run extract_baci.py."""


def nomenclature(year):
    for nom, yrs in NOMENCLATURE.items():
        if year in yrs:
            return nom
    raise ValueError('BACI %s has no year %s' % (VINTAGE, year))


def path(year):
    return os.path.join(EXTRACT, nomenclature(year), 'Y%d.parquet' % year)


def _extracted(p):
    # DuckDB creates its target before it fails, so a 0-byte parquet can exist. Existence is not
    # extraction; the accessor once reported "extracted years: 2024" over an empty file.
    try:
        return os.path.getsize(p) > 1024
    except OSError:
        return False


def available():
    """Years actually present in extract/, so a caller can plan rather than crash."""
    out = []
    for nom, yrs in NOMENCLATURE.items():
        for y in yrs:
            if _extracted(path(y)):
                out.append(y)
    return out


@functools.lru_cache(maxsize=1)
def countries():
    """BACI numeric code -> iso2, iso3, name. One table, the overrides applied once."""
    p = os.path.join(RAW, 'country_codes_%s.csv' % VINTAGE)
    rows = {}
    with open(p, encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            code = (r.get('country_code') or '').strip()
            if not code:
                continue
            rows[code] = {
                'code': code,
                'iso2': (r.get('country_iso2') or '').strip() or None,
                'iso3': (r.get('country_iso3') or '').strip() or None,
                'name': (r.get('country_name') or '').strip() or None,
            }
    for code, fix in FORCE.items():
        rows.setdefault(code, {'code': code, 'iso2': None, 'iso3': None, 'name': None}).update(fix)
    df = pd.DataFrame(sorted(rows.values(), key=lambda x: int(x['code'])))
    return df.set_index('code', drop=False)


def code_maps():
    """The dicts the old readers built by hand: num->iso2, num->iso3, iso2->name."""
    c = countries()
    num2iso2 = {k: v for k, v in c['iso2'].items() if v}
    num2iso3 = {k: v for k, v in c['iso3'].items() if v}
    iso2name = {v['iso2']: v['name'] for _, v in c.iterrows() if v['iso2']}
    return num2iso2, num2iso3, iso2name


@functools.lru_cache(maxsize=1)
def crm_codes():
    cw = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))
    return frozenset(str(c) for v in cw.values()
                     for c in (v.get('ore_hs') or []) + (v.get('refined_hs') or []))


def year(y, columns=None, codes=None, iso=None):
    """One year of BACI. columns: subset of t,i,j,k,v,q. codes: keep only these HS6.
    iso: None (numeric i/j), 'iso3' or 'iso2' - adds i_iso / j_iso columns."""
    p = path(y)
    if not _extracted(p):
        raise NotExtracted('BACI %d is not in extract/ - run: python extract_baci.py' % y)
    want = list(columns) if columns else ['t', 'i', 'j', 'k', 'v', 'q']
    need = set(want) | ({'k'} if codes else set()) | ({'i', 'j'} if iso else set())
    df = pd.read_parquet(p, columns=sorted(need, key=['t', 'i', 'j', 'k', 'v', 'q'].index))
    if codes:
        df = df[df['k'].isin(set(codes))]
    if iso:
        m = countries()[iso]
        df = df.assign(i_iso=df['i'].astype(str).map(m), j_iso=df['j'].astype(str).map(m))
    keep = [c for c in ['t', 'i', 'j', 'k', 'v', 'q'] if c in want]
    if iso:
        keep += ['i_iso', 'j_iso']
    return df[keep].reset_index(drop=True)


def years(ys, **kw):
    return pd.concat([year(y, **kw) for y in ys], ignore_index=True)


if __name__ == '__main__':
    av = available()
    print('BACI %s  extracted years: %s' % (VINTAGE, ('%d..%d (%d)' % (av[0], av[-1], len(av))) if av else 'NONE'))
    c = countries()
    print('countries: %d codes | with iso3: %d | forced: %s' % (len(c), c['iso3'].notna().sum(), ', '.join(FORCE)))
    print('CRM codes: %d' % len(crm_codes()))
