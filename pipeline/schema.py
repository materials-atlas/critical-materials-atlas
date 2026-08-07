# -*- coding: utf-8 -*-
"""Canonical schema + shared helpers for the trade pipeline. EVERY source normalizes into this one
shape, so wide (HS-6), deep (8-10 digit) and mirror layers coexist in a single query surface, and any
adapter can be added in isolation. Get this right once; then adding a country = writing one adapter."""
import os, csv, ssl

# Use certifi's CA bundle for ALL urllib HTTPS fetches (the system store is incomplete here and fails
# cert verification for e.g. Eurostat). Still verifies — just with a complete bundle. One place fixes
# every adapter + fx, so the unattended scheduled refresh doesn't silently skip a source.
try:
    import certifi
    ssl._create_default_https_context = lambda *a, **k: ssl.create_default_context(cafile=certifi.where())
except ImportError:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- the canonical flow record ---
COLUMNS = ['source', 'freq', 'period', 'reporter', 'reporter_name', 'partner', 'partner_name',
           'flow', 'hs6', 'native_code', 'code_level', 'material', 'value_usd', 'qty_kg', 'is_mirror']
DDL = """CREATE TABLE flows(
  source VARCHAR, freq VARCHAR, period INTEGER,
  reporter VARCHAR, reporter_name VARCHAR, partner VARCHAR, partner_name VARCHAR,
  flow VARCHAR, hs6 VARCHAR, native_code VARCHAR, code_level INTEGER,
  material VARCHAR, value_usd DOUBLE, qty_kg DOUBLE, is_mirror BOOLEAN)"""

# FX: EUR->USD. TODO(phase-2): replace the constant with monthly ECB reference rates keyed by period.
EUR_USD = 1.09

# --- country lookups (from BACI's reference table) ---
_cc = list(csv.DictReader(open(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'), encoding='utf8')))
NUM2ISO3 = {r['country_code']: r['country_iso3'] for r in _cc}
NUM2NAME = {r['country_code']: r['country_name'] for r in _cc}
ISO2_ISO3 = {r['country_iso2']: r['country_iso3'] for r in _cc if r.get('country_iso2')}
ISO3_NAME = {r['country_iso3']: r['country_name'] for r in _cc}
FLOW = {'import', 'export'}

# Non-standard country codes used by national sources -> canonical ISO3. BACI has NO Taiwan (uses the
# political proxy S19 "Other Asia, nes") and leaves Namibia's iso2 blank; Eurostat uses EL(Greece),
# XU(UK excl. N.Ireland), XI(N.Ireland); HMRC uses XS(Serbia), XK(Kosovo). Unifying these here is what
# lets the SAME physical flow from two sources dedupe/reconcile instead of splitting on a code mismatch.
# S19->TWN follows standard practice (it is overwhelmingly Taiwan) and calls the entity by its real name.
COUNTRY_FIX = {'TW': 'TWN', 'XS': 'SRB', 'LI': 'LIE', 'NA': 'NAM', 'XU': 'GBR', 'XI': 'GBR',
               'EL': 'GRC', 'UK': 'GBR', 'XK': 'XKV', 'S19': 'TWN'}
ISO3_NAME.setdefault('TWN', 'Taiwan')
ISO3_NAME.setdefault('XKV', 'Kosovo')


def iso3(code):
    """Canonical ISO3 for any source's country code: known fixes first, then BACI's iso2 map, else as-is."""
    if code in COUNTRY_FIX:
        return COUNTRY_FIX[code]
    return ISO2_ISO3.get(code, code)


def cname(code):
    """Human name for a canonical ISO3 code (falls back to the code itself)."""
    return ISO3_NAME.get(code, code)


def row(**kw):
    """Build a canonical row dict, defaulting any missing column to None."""
    return {c: kw.get(c) for c in COLUMNS}


def validate(rows, source):
    """Adversarial gate: a source that fails this never reaches the database. Returns (ok, problems)."""
    p = []
    if not rows:
        return False, ['no rows produced']
    bad_flow = bad_hs6 = bad_level = neg_val = no_mat = 0
    countries = set()
    for r in rows:
        if r.get('flow') not in FLOW: bad_flow += 1
        h = r.get('hs6') or ''
        if len(h) != 6 or not h.isdigit(): bad_hs6 += 1
        if r.get('code_level') not in (6, 8, 10): bad_level += 1
        v = r.get('value_usd')
        if v is not None and v < 0: neg_val += 1
        if not r.get('material'): no_mat += 1
        countries.add(r.get('reporter'))
    if bad_flow: p.append(f'{bad_flow} rows with flow not in import/export')
    if bad_hs6: p.append(f'{bad_hs6} rows with a malformed hs6')
    if bad_level: p.append(f'{bad_level} rows with code_level not in 6/8/10')
    if neg_val: p.append(f'{neg_val} rows with negative value')
    if no_mat: p.append(f'{no_mat} rows with no material assigned')
    if len(countries) < 1: p.append('no reporter countries')
    return (len(p) == 0), p
