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

THE TEST, stated because the principle above was here all along and still got misread - by me,
2026-10-02, when I argued the opposite to the owner and had to retract it.

    Collect everything. Publish what cannot SUBSTITUTE for someone else's product.

Not "did we transform it". Transformation does not shrink granularity, and granularity is what
makes an output a substitute. An index, a chart, a model coefficient, a country total - nobody
rebuilds Comtrade from those. A bilateral table at material x country-pair x year largely IS their
product, however much work went into it.

Two consequences that are easy to get backwards:

  * THE CONSTRAINT IS PER SOURCE, NOT PER SHAPE. Eurostat Comext is CC BY 4.0 and explicitly
    permits commercial re-use with attribution, so OUR BILATERAL COMEXT ROWS ARE FINE. "Bilateral
    is risky" is the wrong rule; "Comtrade-derived bilateral is risky" is the right one.

  * THE THRESHOLD IS PER DOWNLOAD. UN Comtrade's published terms (shop.un.org, read 2026-10-02)
    charge for re-dissemination but exempt "a small number of records (up to 100,000)" and
    public free-of-charge visualization/analytics, which they define as limiting 100,000 records
    per download. So twenty-five yearly files of ~17,000 rows each, drawing maps on a free site,
    sit inside the exemption. One parquet carrying all 368,838 of them at once does not.

That is a reading of a terms page, not legal advice, and whether N files count as N downloads is a
question for subscriptions@un.org. Where it is ambiguous this file takes the reading least
favourable to us.
"""

# Sources we may redistribute, with the terms that allow it.
LICENCES = {
    'BGS World Mineral Statistics': 'Open Government Licence v3.0 (attribution required)',
    'USGS Historical Statistics (DS 140)': 'US Government public domain',
    'CEPII BACI (HS02)': 'Etalab Open Licence 2.0 (attribution: Gaulier & Zignago 2010)',
    'World Mining Data': 'Free with attribution (BMK Austria / WMD)',
    'IEA Critical Minerals Dataset': 'CC BY 4.0',
    # Verified against Eurostat's own copyright notice on 2026-10-02
    # (ec.europa.eu/eurostat/web/main/help/copyright-notice): re-use is permitted, including for
    # commercial purposes, provided the source is acknowledged and any changes are indicated.
    # Changes we make and therefore must state: aggregation to (reporter, counterpart, year),
    # 100 kg converted to metric tonnes, and Comext's own aggregate reporter codes (EU, EU27_2020,
    # EA, EA21) dropped so that a column sum cannot add the bloc to its own member states.
    'Eurostat Comext (CN8)':
        'CC BY 4.0 (© European Union, Eurostat). Re-use permitted including commercially, with '
        'source acknowledgement and an indication of changes made.',
    # OUR OWN derived statistic. Two independent customs declarations of the same shipment, put
    # through our freight correction, our agreement test and our geometric mean. Nobody else
    # publishes this number, and it is not a copy of anything.
    'CMA two-sided reconciliation':
        'CC BY 4.0 (Critical Materials Atlas). Derived statistic, not a redistribution: '
        'computed from two independent national declarations, neither of which it reproduces.',
}

# Held back from every public artefact ON PURPOSE - not an oversight, not a missing licence.
WITHHELD = {
    # Withheld from the BULK EXTRACT ONLY, and that distinction is the whole point. The same flows
    # stay public as out/flows_YYYY.json - twenty-five files, largest 17,258 rows - because each
    # one is a free public visualization under the holder's own threshold. What is withheld is
    # bundling all 368,838 into a single parquet, which is extraction by their definition.
    #
    # It is a mixture and that is why it cannot be published whole: reconcile/reconcile.py
    # reconciles two-sided flows (ours) and KEEPS ONE-SIDED FLOWS (line 8, Comtrade's), and the
    # output carries only from/to/value/qty, so the two cannot be separated after the fact. If
    # they could, the derived half would be ours to give.
    'CMA annual world reconciliation':
        'a mixture we cannot split: two-sided reconciliation of ours beside one-sided UN Comtrade '
        'flows passed through, indistinguishable in the output. Bundling 368,838 of them in one '
        'download is re-dissemination by the terms of the holder itself. The same rows remain '
        'public per year at out/flows_YYYY.json, each far under the 100,000-record threshold.',
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
    # The friendliest refusal in this file: the data is not behind a paywall, it is on our own site
    # one year at a time. Only the single-file bundle is withheld.
    'CMA annual world reconciliation': {
        'holder': 'Critical Materials Atlas (derived) over United Nations - UN Comtrade (source)',
        'why_not': 'the two-sided reconciliation is ours, but one-sided Comtrade flows are passed '
                   'through in the same table and cannot be separated after the fact. Bundling '
                   'them all in one download is re-dissemination under UN Comtrade terms.',
        'cost': 'Free, and no account needed.',
        'register': 'not required',
        'endpoint': 'https://criticalmaterialsatlas.org/out/flows_YYYY.json',
        'parameters': {
            'YYYY': '2002 through 2025, one file per year',
        },
        'note': 'Identical rows, one year per request - largest file 17,258 records, well inside '
                'the 100,000-per-download exemption set by the holder. Concatenate them yourself if you '
                'need the panel; what we may not do is hand you the concatenation.',
    },
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
