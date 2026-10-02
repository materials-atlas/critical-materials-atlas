#!/usr/bin/env python3
"""Eurostat Comext (CN 8-digit) -> cube rows. The source the cube was missing.

WHY THIS EXISTS. The atlas began life as a Comext study: the repository's first commit, 22 June
2026, is a "Comext trade-dependency demo scaffold". That layer still runs, still feeds
out/data.json and the homepage HHI, and until now it was the ONE source family that never entered
the harmonized cube. So the oldest data in the project was also the least queryable.

WHAT IT ADDS THAT NOTHING ELSE HAS. Granularity, not corroboration:

  * CN 8-DIGIT. Everything else in the cube is HS-6, where 811292 is a single code covering BOTH
    gallium and germanium. CN-8 splits it - 81129289 gallium, 81129295 germanium - and the same is
    true for several other baskets. The monthly pipeline already exploits this through its own
    Eurostat adapter, but that cache holds four months. These files hold sixteen years.
  * 2010-2025, 32 reporting member states, per material.

WHY IT IS NOT A CROSS-CHECK ON BACI, stated here so nobody later treats it as one. EU member
states report to Eurostat, and Eurostat transmits the EU's figures onward to UN Comtrade, which is
what BACI is built from. Comext and the EU slice of BACI therefore share an origin: they are one
witness recorded twice, not two witnesses. Measured on magnets 2024 - Comext says China is 92.7% of
extra-EU imports, BACI filtered to extra-EU imports says 90.3%. That closeness is the fingerprint
of a shared source, not independent confirmation. Same fault as the USA->CAN placebo, and the same
reason reconcile.py refuses to pair BACI with the mirror feed.

THE UNIVERSE PROBLEM, and why these rows carry a `universe` tag. Every other trade row in the cube
is world-scope: a country's imports from anywhere. These rows are EXTRA-EU IMPORTS ONLY - intra-EU
trade is excluded, because the question this source was built to answer is where Europe's supply
enters the bloc from. Without a tag saying so, a row here looks like a world row and a later
GROUP BY would silently mix the two universes. The tag is what makes the key honest.

Run:  python build_cube_comext.py     (invoked by build_cube.py; standalone for inspection)
"""
import csv
import glob
import io
import os
import sys

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw')
SOURCE = 'Eurostat Comext (CN8)'
UNIVERSE = 'eu27_extra'          # extra-EU imports only - see the header
CODE_SYSTEM = 'CN8'

# The reporting bloc. A partner inside it is intra-EU trade and is excluded, which is the whole
# point of the "extra" in extra-EU. Kept explicit rather than inferred so an enlargement is a
# visible edit rather than a silent change of denominator.
EU27 = {'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT',
        'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'}
# Comext mixes AGGREGATE codes in with real countries, in BOTH the partner and the reporter column:
# EU, EU27_2020, EA (euro area) and EA21 all appear beside AT, BE, DE... Summing a column without
# excluding them adds the bloc to its own members. Measured on magnets 2024, that inflated the
# total 4.6x - EUR 3.58bn against the true EUR 784,821,501 - and it is the same fault as Comtrade
# returning an all-modes total alongside its own components.
#
# The rule used below is stricter and cannot rot: a reporter must BE an EU27 member state, so every
# aggregate is excluded by construction rather than by blocklist. Verified: the 27 member states
# sum to the EU aggregate row exactly, to the euro.
AGGREGATES = {'EU', 'EU27_2020', 'EU28', 'EA', 'EA21', 'EXT_EU', 'EXT_EU27_2020',
              'WORLD', 'TOTAL', 'EXTRA_EU'}


def _rows(path):
    if not os.path.exists(path):
        return []
    with io.open(path, encoding='utf-8', errors='replace') as fh:
        return list(csv.DictReader(fh))


def _num(s):
    try:
        return float(str(s).replace(':', '').strip() or 0)
    except ValueError:
        return 0.0


def build():
    """One list of cube rows. Two measures per (material, reporter, year): tonnes and euros."""
    out = []
    for vpath in sorted(glob.glob(os.path.join(RAW, '*_value.csv'))):
        base = os.path.basename(vpath)[:-len('_value.csv')]
        if '_' not in base:
            continue
        material, code = base.rsplit('_', 1)
        qpath = vpath[:-len('_value.csv')] + '_qty.csv'

        # (reporter, year) -> [euros, hundred-kg]
        agg = {}
        for path, slot in ((vpath, 0), (qpath, 1)):
            for r in _rows(path):
                partner = (r.get('partner') or '').strip()
                # imports only (flow 1), real partners only, outside the bloc only
                if (r.get('flow') or '').strip() != '1':
                    continue
                if partner in EU27 or partner in AGGREGATES or len(partner) != 2:
                    continue
                reporter = (r.get('reporter') or '').strip()
                if reporter not in EU27:        # excludes EU / EU27_2020 / EA / EA21 aggregates
                    continue
                key = (reporter, (r.get('TIME_PERIOD') or '').strip())
                if not key[1].isdigit():
                    continue
                cell = agg.setdefault(key, [0.0, 0.0])
                cell[slot] += _num(r.get('OBS_VALUE'))

        for (reporter, year), (eur, hkg) in sorted(agg.items()):
            common = dict(material=material, country_iso3=reporter, year=int(year),
                          measure_family='trade', flow_direction='in', stage=None,
                          code_system=CODE_SYSTEM, native_code=code, native_label=None,
                          sub_commodity=None, basis='gross', source=SOURCE, universe=UNIVERSE,
                          freq='A', period=int(year), precision=None, value_flag=None,
                          source_obs_status=None, native_group=None, native_country=reporter)
            if hkg:
                # Comext quantity is in 100 kg; the cube's trade rows are metric tonnes
                t = hkg / 10.0
                out.append(dict(common, measure='imports', value=t, unit='tonnes (metric)',
                                value_t=t, conversion_factor=1.0))
            if eur:
                out.append(dict(common, measure='imports_value', value=eur, unit='EUR',
                                value_t=None, conversion_factor=None))
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    rows = build()
    mats = sorted(set(r['material'] for r in rows))
    yrs = sorted(set(r['year'] for r in rows))
    reps = sorted(set(r['country_iso3'] for r in rows))
    print('Eurostat Comext ingest')
    print('  rows        %d' % len(rows))
    print('  materials   %d' % len(mats))
    print('  reporters   %d' % len(reps))
    print('  years       %s - %s (%d)' % (yrs[0], yrs[-1], len(yrs)) if yrs else '  years  none')
    print('  measures    %s' % sorted(set(r['measure'] for r in rows)))
    print('  universe    %s  (intra-EU trade excluded by construction)' % UNIVERSE)
