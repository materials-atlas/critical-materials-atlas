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
}

# Held back from every public artefact ON PURPOSE - not an oversight, not a missing licence.
WITHHELD = {
    'CMA monthly mirror reconciliation':
        'derived from UN Comtrade (79% of contributing rows), whose free-tier terms permit use '
        'but not redistribution. The method and the code are public; these values are not.',
}


def public(df, col='source', announce=True):
    """Return only the rows that may leave the building. Fails loudly on an unrecorded source."""
    held = sorted(set(df[col].dropna().unique()) & set(WITHHELD))
    if held and announce:
        for h in held:
            print('  WITHHELD from public output: %s - %s' % (h, WITHHELD[h]))
    out = df[~df[col].isin(WITHHELD)]
    unknown = sorted(set(out[col].dropna().unique()) - set(LICENCES))
    if unknown:
        raise SystemExit(
            'a source has no recorded redistribution licence, so this export cannot be written: '
            + ', '.join(unknown) + '\nAdd it to LICENCES with its terms, or add it to WITHHELD '
            'with the reason it cannot be redistributed.')
    return out
