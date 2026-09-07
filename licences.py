# -*- coding: utf-8 -*-
"""Who may see what leaves this repository. One table, read by every exporter.

WHY THIS FILE EXISTS
It exists because the rule was written in one exporter and not the other, and the gap shipped.
build_sdmx.py correctly refused to publish our monthly reconciliation - and build_cube.py, four
lines of `to_parquet` with no gate at all, wrote the same 59,577 rows into out/cube.parquet, which
is served publicly. The SDMX export was clean and the plain download was not.

A licence rule enforced in one place out of two is not a rule, it is a habit. So it lives here and
both exporters import it.

THE PRINCIPLE
A derived statistic does not launder the terms of the data it was derived from. Aggregating,
reconciling and re-basing UN Comtrade values at HS6 x month x country produces something close
enough to its input that publishing it is redistribution in all but name. Our method is public and
our code is public; those particular numbers are not ours to hand out.
"""

# Sources we may redistribute, with the terms that allow it.
LICENCES = {
    'BGS World Mineral Statistics': 'Open Government Licence v3.0 (attribution required)',
    'USGS Historical Statistics (DS 140)': 'US Government public domain',
    'CEPII BACI (HS02)': 'Etalab Open Licence 2.0 (attribution: Gaulier & Zignago 2010)',
    'World Mining Data': 'Free with attribution (BMK Austria / WMD)',
    'IEA Critical Minerals Dataset': 'CC BY 4.0',
    # OUR OWN derived statistic. Two independent customs declarations of the same shipment, put
    # through our freight correction, our agreement test and our geometric mean. Nobody else
    # publishes this number, and it is not a copy of anything.
    'CMA two-sided reconciliation':
        'CC BY 4.0 (Critical Materials Atlas). Derived statistic, not a redistribution: '
        'computed from two independent national declarations, neither of which it reproduces.',
}

# Held back from every public artefact ON PURPOSE - not an oversight, not a missing licence.
WITHHELD = {
    'CMA single-declaration passthrough':
        'only one customs service declared these shipments, so the figure is that service - '
        'mostly UN Comtrade - at most deflated by our freight markup. Calling it our derivation '
        'would be a fiction, and publishing it would be republishing Comtrade under our name.',
}

# WHAT WE OWE A CUSTOMER WE SAY NO TO.
# "You cannot have this" is not an answer a research firm can sell. Every withheld source carries
# the exact recipe to fetch the same rows first-hand - endpoint, parameters, the account needed and
# what it costs - so the refusal costs the customer an afternoon, not the analysis.
RETRIEVAL = {
    'CMA single-declaration passthrough': {
        'holder': 'United Nations Statistics Division - UN Comtrade',
        'why_not': 'Comtrade free-tier terms permit use and analysis but not bulk '
                   'redistribution of the underlying records.',
        'cost': 'Free. A registered account gives an API key: 100,000 records per call, '
                '500 calls per day.',
        'register': 'https://comtradeplus.un.org/  ->  sign in  ->  API Management',
        'endpoint': 'https://comtradeapi.un.org/data/v1/get/C/M/HS',
        'parameters': {
            'reporterCode': 'the declaring country, UN M49 numeric (e.g. 152 = Chile)',
            'period': 'YYYYMM, comma-separated, up to 12 per call',
            'cmdCode': 'the HS6 codes in out/materials_hs6.json',
            'flowCode': 'M for imports, X for exports',
            'partnerCode': '0 for world, or the partner M49 code',
            'motCode': '0 - the all-modes total. Omitting this returns the SAME cell several '
                       'times split by transport mode, and summing them double-counts.',
        },
        'reproduce': 'pipeline/adapter_comtrade.py performs exactly these calls and '
                     'pipeline/reconcile.py turns them into these rows. Both are public.',
        'gotcha': 'The keyless preview endpoint silently truncates every response at 500 rows. '
                  'If a call returns exactly 500 records, it is truncated, not complete.',
    },
}


def recipe(source):
    """How a customer gets the withheld rows themselves. Returns None if none is needed."""
    return RETRIEVAL.get(source)


def public(df, col='source', announce=True):
    """Return only the rows that may leave the building. Fails loudly on an unrecorded source."""
    held = sorted(set(df[col].dropna().unique()) & set(WITHHELD))
    if held and announce:
        for h in held:
            print('  WITHHELD from public output: %s - %s' % (h, WITHHELD[h]))
            if h not in RETRIEVAL:
                raise SystemExit(
                    'refusing to withhold %s with no retrieval recipe. Telling a customer "no" '
                    'without telling them where to get it themselves is not a product.' % h)
    out = df[~df[col].isin(WITHHELD)]
    unknown = sorted(set(out[col].dropna().unique()) - set(LICENCES))
    if unknown:
        raise SystemExit(
            'a source has no recorded redistribution licence, so this export cannot be written: '
            + ', '.join(unknown) + '\nAdd it to LICENCES with its terms, or add it to WITHHELD '
            'with the reason it cannot be redistributed.')
    return out
