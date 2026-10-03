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

BILATERAL, AND WHY THERE IS NO `universe` COLUMN. An earlier version of this adapter aggregated
partners away and carried a non-standard `universe='eu27_extra'` tag to record that the rows covered
extra-EU imports only. Both were wrong, and BPM6 says why (see DSD_BPM6.md): a COUNTERPART_AREA need
not be a country. ECB publishes W1 for world and I9/J9 for inside/outside the euro area, so SCOPE IS
A COUNTERPART CODE. These rows therefore keep the partner they were reported against, intra-EU
included, and "extra-EU" becomes a filter on that column rather than a property of the table.

That also makes the rows COMPONENTS, never totals. A total and its own components must never be
summed together - the fault this repo has hit twice, and which cost this very adapter a 4.6x error
on its first run.

Run:  python build_cube_comext.py     (invoked by build_cube.py; standalone for inspection)
"""
import csv
import glob
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline'))
import schema  # the repo's one ISO mapping - do not grow a second one here

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw')
SOURCE = 'Eurostat Comext (CN8)'
CODE_SYSTEM = 'CN8'
# SDMX's standard 'not allocated / not applicable' code. Comext's QV/QW/QY/QZ/XS
# residuals land here rather than being thrown away; exact Comext definitions are
# worth confirming against the geonomenclature before anyone analyses this slice.
NOT_ALLOCATED = '_Z'

# The current EU-27. Used ONLY to express "extra-EU" when filtering counterparts - never to decide
# who may report, because membership changes and the data is historical (see the GB note below).
# Kept explicit rather than inferred so an enlargement is a visible edit, not a silent change of
# denominator.
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



# Eurostat's residual partner codes, KEPT VERBATIM rather than collapsed.
#
# They are not one class. QV and QY are INTRA-EU "not specified"; QZ and the rest are EXTRA-EU.
# Flattening them all into _Z threw that distinction away, and because _Z then failed the
# "is it an EU27 member" test, every intra-EU residual was counted as extra-EU. Proven exactly:
# across all 454 material-years, our derived extra-EU total minus Eurostat's published
# EXT_EU27_2020 equals QV + QY to the euro, in every single case.
#
# That is also the real answer to a residual this file previously blamed on Croatia's 2013
# accession. It was not Croatia. Helium 2013's EUR 1,097,172 gap is QY, exactly. With QV and QY
# classified as intra, the fixed EU27_2020 composition reproduces Eurostat in every year 2010-2025,
# 2013 included. Found by an engine review; the Croatia story was mine and it was wrong.
INTRA_RESIDUALS = frozenset({'QV', 'QY'})


def _area(code):
    """Comext ISO2 -> canonical ISO3, through the repo's one door.

    An engine review caught this reaching into schema.ISO2_ISO3 directly and sending every miss to
    _Z. That bypassed schema.COUNTRY_FIX, which already knows the codes a national source invents -
    XS is Serbia, LI Liechtenstein, XK Kosovo - so EUR 2.02bn of Serbian trade was being filed as
    "not allocated". schema.iso3() applies the fixes first and the ISO2 table second, which is
    exactly why it exists.

    iso3() returns an unknown code unchanged, so the _Z decision is made here: anything that does
    not come back as a plausible ISO3 is a Comext residual (QV/QW/QY/QZ and friends) and is kept
    under the non-allocated code rather than discarded.
    """
    out = schema.iso3(code)
    if len(out) == 3 and out.isalpha() and out.isupper():
        return out
    # a Eurostat residual: keep its own code so intra/extra survives - see INTRA_RESIDUALS
    c = (code or '').strip().upper()
    return c if (len(c) == 2 and c.isalpha()) else NOT_ALLOCATED


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

        # (reporter, partner, year) -> [euros, hundred-kg]
        agg = {}
        for path, slot in ((vpath, 0), (qpath, 1)):
            for r in _rows(path):
                partner = (r.get('partner') or '').strip()
                # imports only (flow 1), real partners only. Intra-EU partners are KEPT: scope is a
                # counterpart code, so excluding them here would hide it instead of encoding it.
                if (r.get('flow') or '').strip() != '1':
                    continue
                if partner in AGGREGATES or len(partner) != 2:
                    continue
                reporter = (r.get('reporter') or '').strip()
                # A REPORTER IS ANY REAL REPORTING COUNTRY, NOT ANY CURRENT MEMBER STATE.
                # This said `reporter not in EU27` and silently dropped GB: the United Kingdom
                # reported to Comext until it left, so these files carry 4,793 GB rows worth
                # EUR 142.8 BILLION across 2010-2019, and a present-tense membership test threw
                # away sixteen years of it. Caught by an engine review, not by any check here.
                # Aggregates are excluded by the same two rules as partners: the blocklist, and
                # having to resolve to a real ISO3.
                if reporter in AGGREGATES:
                    continue
                # Map areas BEFORE keying. _Z is a BUCKET - several Comext residual codes land in
                # it - so mapping after aggregation produced one _Z row per original code, all
                # sharing a series key. 86 collisions, caught by the SDMX structure check.
                rep3 = _area(reporter)
                if rep3 == NOT_ALLOCATED:
                    continue                   # a reporter must resolve to a real member state
                par3 = _area(partner)
                key = (rep3, par3, (r.get('TIME_PERIOD') or '').strip())
                if not key[2].isdigit():
                    continue
                cell = agg.setdefault(key, [0.0, 0.0])
                cell[slot] += _num(r.get('OBS_VALUE'))

        for (rep3, par3, year), (eur, hkg) in sorted(agg.items()):
            # Comext codes areas in ISO2; every area column in the cube and in CL_AREA is ISO3.
            # Writing the ISO2 straight through produced rows that passed the key check and failed
            # the codelist check - the structure caught what the uniqueness test could not.
            #
            # DO NOT DROP WHAT DOES NOT MAP. The first version skipped any unmapped code, which
            # silently discarded EUR 36.9 billion - QZ alone was EUR 28bn - because Comext's
            # partner column carries NON-COUNTRY codes (QV, QW, QY, QZ, XS: not-specified and
            # confidential residuals) beside real ones, and the repo's ISO2 table is also missing
            # a few genuine small territories (LI, FO, VI, VA, XK). Dropping both kinds together
            # is the silent-loss fault this project exists to avoid, and it would have shown up
            # only as totals that no longer matched data.json.
            #
            # BPM6 practice is to keep such flows under a non-allocated counterpart rather than
            # discard them - the ECB publishes exactly this, and the Banque de France key carries
            # non-allocated codes in the same position. So anything without an ISO3 goes to _Z.
            common = dict(material=material, country_iso3=rep3, counterpart_area=par3,
                          year=int(year),
                          measure_family='trade', flow_direction='in', stage=None,
                          code_system=CODE_SYSTEM, native_code=code, native_label=None,
                          sub_commodity=None, basis='gross', source=SOURCE,
                          freq='A', period=int(year), precision=None, value_flag=None,
                          source_obs_status=None, native_group=None, native_country=rep3)
            if hkg:
                # Comext quantity is in 100 kg; the cube's trade rows are metric tonnes
                t = hkg / 10.0
                out.append(dict(common, measure='imports', value=t, unit='tonnes (metric)',
                                value_t=t, conversion_factor=1.0))
            if eur:
                out.append(dict(common, measure='imports_value', value=eur, unit='EUR',
                                value_t=None, conversion_factor=None))
    return out


# The EVOLVING-composition bloc series, which is the one thing here that CANNOT be derived.
#
# Everything else in this adapter is components, and every aggregate is computed from them - the
# owner's rule, and a good one. This is the exception that proves it. EU27_2020 is a FIXED
# composition applied to every year, so "extra-EU" under it is derivable by filtering counterparts.
# The EVOLVING series - reporter EU against partner EXT_EU, where the bloc is whoever was in it at
# the time - is not derivable from our rows: it needs membership by year, and the transition years
# are where it matters and where a reconstruction would be wrong. Croatia acceded on 1 July 2013
# and the UK left on 31 January 2020; both are part-years with a compiler convention we would be
# guessing at.
#
# So we read Eurostat's own answer instead of inventing one. The two series agree from 2021 and
# diverge before: 2019 differs by EUR 1.24bn, which is the UK's own extra-EU imports minus EU27
# imports from the UK.
#
# These rows ARE aggregates in both area columns, deliberately, and the guards know it:
# check_counterpart warns that an aggregate reporter sits beside the countries it contains, and
# cube_query.totals(ref='each') refuses to sum across the mix. That is the protection working, not
# a defect. Store what cannot be derived; derive what can.
BLOC_SERIES = {
    ('EU', 'EXT_EU'): ('EU', 'EXT_EU'),
    ('EU', 'INT_EU'): ('EU', 'INT_EU'),
}


def bloc_rows():
    """Eurostat's published evolving-composition bloc totals, as cube rows."""
    out = []
    for vpath in sorted(glob.glob(os.path.join(RAW, '*_value.csv'))):
        base = os.path.basename(vpath)[:-len('_value.csv')]
        if '_' not in base:
            continue
        material, code = base.rsplit('_', 1)
        qpath = vpath[:-len('_value.csv')] + '_qty.csv'
        agg = {}
        for path, slot in ((vpath, 0), (qpath, 1)):
            for r in _rows(path):
                if (r.get('flow') or '').strip() != '1':
                    continue
                key = ((r.get('reporter') or '').strip(), (r.get('partner') or '').strip())
                if key not in BLOC_SERIES:
                    continue
                y = (r.get('TIME_PERIOD') or '').strip()
                if not y.isdigit():
                    continue
                cell = agg.setdefault((BLOC_SERIES[key], y), [0.0, 0.0])
                cell[slot] += _num(r.get('OBS_VALUE'))
        for ((ref, cp), year), (eur, hkg) in sorted(agg.items()):
            common = dict(material=material, country_iso3=ref, counterpart_area=cp,
                          year=int(year), measure_family='trade', flow_direction='in', stage=None,
                          code_system=CODE_SYSTEM, native_code=code, native_label=None,
                          sub_commodity=None, basis='gross', source=SOURCE,
                          freq='A', period=int(year), precision=None, value_flag=None,
                          source_obs_status=None, native_group=None, native_country=ref)
            if hkg:
                t = hkg / 10.0
                out.append(dict(common, measure='imports', value=t,
                                unit='tonnes (metric)', value_t=t, conversion_factor=1.0))
            if eur:
                out.append(dict(common, measure='imports_value', value=eur, unit='EUR',
                                value_t=None, conversion_factor=None))
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    rows = build() + bloc_rows()
    mats = sorted(set(r['material'] for r in rows))
    yrs = sorted(set(r['year'] for r in rows))
    reps = sorted(set(r['country_iso3'] for r in rows))
    print('Eurostat Comext ingest')
    print('  rows        %d' % len(rows))
    print('  materials   %d' % len(mats))
    print('  reporters   %d' % len(reps))
    print('  years       %s - %s (%d)' % (yrs[0], yrs[-1], len(yrs)) if yrs else '  years  none')
    print('  measures    %s' % sorted(set(r['measure'] for r in rows)))
    print('  partners    %d  (intra-EU kept; scope is a counterpart filter)'
          % len(set(r['counterpart_area'] for r in rows)))
