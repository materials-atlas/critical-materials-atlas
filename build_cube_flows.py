#!/usr/bin/env python3
"""The annual world trade engine -> cube rows. The last source stored only as country totals.

WHAT THIS IS. out/flows_2002.json ... flows_2025.json are the output of reconcile/ - raw UN
Comtrade reconstructed BACI-style into bilateral world trade, one file per year. They are what the
site's world maps and the origin-gap finding actually run on, and until now the cube could not see
them: it held CEPII BACI as country totals in tonnes, and the only bilateral rows in it were
Eurostat's, which stop at the EU border.

Ingesting them makes the cube world-bilateral. "Who exports what to whom, anywhere" becomes a
query instead of a page.

WHICH YEARS GO IN, AND THE ONE THAT DOES NOT.

  2002-2024   measured. Reconciled from reported Comtrade, BACI-validated. obs_status 'A'.
  2025        PROVISIONAL. Reconciled from PARTIAL reporting, with levels calibrated to BACI 2024
              because the raw reconciliation runs high. It is an estimate OF A PAST PERIOD, which
              is a legitimate observation, so it goes in carrying obs_status 'E' - estimated.
  2026        EXCLUDED, deliberately.

The 2026 file is a directional nowcast: its SHARES ARE FROZEN AT 2025 and only the levels move,
scaled by Q1 momentum and Pink Sheet prices, and its own source string says "levels indicative
only". That is not an estimate of something that happened; it is a projection of something that
has not. This repo already settled that question for the IEA - "forecasts must not sit in a table
of observations where a later query could difference them against measured history"
(build_cube_iea.py) - and the same rule decides this one. The 2026 file stays where it is and keeps
driving the pages that are honest about what it is.

MEASURES. Each flow carries value and, before 2025, quantity:
  exports_value  USD, currency_denom USD
  exports        metric tonnes (the files store kg-free integers already in tonnes; see below)
REF_AREA is the exporter and COUNTERPART_AREA the importer, which is what flow_direction='out'
means. The same flow read from the importer's side would be a second observation, not this one.

Run:  python build_cube_flows.py     (invoked by build_cube.py; standalone for inspection)
"""
import glob
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline'))
import schema  # the one ISO door

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'out')
SOURCE = 'CMA annual world reconciliation'
# 2026 is a projection, not an observation - see the header
SKIP_YEARS = {2026}


def _area(code):
    """Flow files use ISO2; the cube and CL_AREA are ISO3. Unresolvable codes are dropped rather
    than bucketed: unlike Comext's residuals these are not a declared 'not allocated' class, so a
    silent _Z here would invent a category the source does not have."""
    out = schema.iso3((code or '').strip())
    return out if (len(out) == 3 and out.isalpha() and out.isupper()) else None


def build():
    rows = []
    for path in sorted(glob.glob(os.path.join(OUT, 'flows_*.json'))):
        try:
            year = int(os.path.basename(path)[len('flows_'):-len('.json')])
        except ValueError:
            continue
        if year in SKIP_YEARS:
            continue
        try:
            d = json.load(io.open(path, encoding='utf-8'))
        except ValueError:
            continue
        provisional = bool(d.get('provisional'))
        status = 'E' if provisional else 'A'
        for material, flows in (d.get('materials') or {}).items():
            for f in flows:
                exp, imp = _area(f.get('from')), _area(f.get('to'))
                if not exp or not imp or exp == imp:
                    continue
                common = dict(material=material, country_iso3=exp, counterpart_area=imp,
                              year=year, measure_family='trade', flow_direction='out',
                              stage=None, code_system=None, native_code=None, native_label=None,
                              sub_commodity=None, basis='gross', source=SOURCE,
                              freq='A', period=year, precision=None, value_flag=None,
                              source_obs_status=None, obs_status=status,
                              native_group=None, native_country=exp,
                              series_id='CMA-ANNUAL:%s:%s' % (material, exp))
                v = f.get('value')
                if v:
                    rows.append(dict(common, measure='exports_value', value=float(v),
                                     unit='USD', currency_denom='USD',
                                     value_t=None, conversion_factor=None))
                q = f.get('qty')
                if q:
                    rows.append(dict(common, measure='exports', value=float(q),
                                     unit='tonnes (metric)', currency_denom='_T',
                                     value_t=float(q), conversion_factor=1.0))
    return rows


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    rows = build()
    yrs = sorted(set(r['year'] for r in rows))
    print('annual world reconciliation ingest')
    print('  rows        %d' % len(rows))
    print('  materials   %d' % len(set(r['material'] for r in rows)))
    print('  exporters   %d   importers %d'
          % (len(set(r['country_iso3'] for r in rows)),
             len(set(r['counterpart_area'] for r in rows))))
    print('  years       %s - %s (%d)' % (yrs[0], yrs[-1], len(yrs)) if yrs else '  years none')
    print('  provisional %d rows carry obs_status E'
          % sum(1 for r in rows if r['obs_status'] == 'E'))
    print('  excluded    %s (projection, not observation)' % sorted(SKIP_YEARS))
