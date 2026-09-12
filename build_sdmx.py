# -*- coding: utf-8 -*-
"""Publish the cube as SDMX: a data structure definition, its code lists, and SDMX-CSV.

WHY SDMX
Everything the cube needed, it needed because SDMX already demands it. A data structure
definition names the DIMENSIONS that identify an observation and separates them from the
ATTRIBUTES that merely describe it, and then nothing may be published that does not satisfy
that key. Asking our own data that question found 144 observations sharing a key and three
defects in the sources - see bgs_country.py and out/source_anomalies.json. The standard did not
find them; asking the standard's question did.

What SDMX gives us that we would otherwise author badly:
  - cross-domain code lists for the concepts every statistical dataset shares - REF_AREA,
    TIME_PERIOD, FREQ, UNIT_MEASURE, OBS_STATUS, CONF_STATUS - verified here against the SDMX
    Global Registry rather than from memory;
  - the dimension/attribute distinction, which immediately corrected two of our own choices:
    UNIT_MEASURE is NOT a dimension (it is determined by source and basis, so it describes the
    series rather than identifying it), and native_code IS one (dropping it merges three BGS
    copper forms into a single "processed copper" that means nothing);
  - a serialization other institutions can read without being told anything.

What it does NOT give us, and what nobody should expect it to: there is no standard code list
for a mineral commodity, for mine versus processed, or for gross versus metal content. We still
author those. What changes is that they become declared, versioned artefacts a machine can
enforce, instead of rules living in a docstring.

LICENCE GATE
An export is a redistribution channel and takes the same gate as out/. Every source in the cube
is licensed for redistribution with attribution - BGS under the Open Government Licence, USGS as
US public domain, CEPII BACI under Etalab 2.0, World Mining Data free with attribution, the IEA
Critical Minerals Dataset under CC BY 4.0 - so the whole cube may be published. Sources are
listed per dataflow so that if a future ingest is not redistributable, it is excluded here by
name rather than by anyone remembering.

Run:  python build_sdmx.py
"""
import json, os, gzip, csv, datetime, io
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'pipeline', 'data')
OUT = os.path.join(ROOT, 'out', 'sdmx')
AGENCY = 'CMA'                       # Critical Materials Atlas, the maintenance agency
VERSION = '1.0.0'
TODAY = datetime.date.today().isoformat()

# Verified against the SDMX Global Registry, not typed from memory. The USGS "W" trap is the
# reason: USGS prints W for WITHHELD, SDMX's W means "includes data from another category".
OBS_STATUS = {
    'A': 'Normal value',
    'E': 'Estimated value',
    'N': 'Not significant',
    'O': 'Missing value',
    'Q': 'Missing value; suppressed',
}
CONF_STATUS = {'C': 'Confidential statistical information'}

# Sources, and the licence that lets this file exist at all.
from licences import LICENCES, WITHHELD  # one table, read by every exporter


def codelist(cid, name, codes, desc=None):
    return {'id': cid, 'agencyID': AGENCY, 'version': VERSION, 'name': name,
            'description': desc, 'isFinal': True,
            'codes': [{'id': str(k), 'name': str(v)} for k, v in codes]}


def build():
    c = pd.read_parquet(os.path.join(DATA, 'cube.parquet'))
    os.makedirs(OUT, exist_ok=True)

    # Three states, not two. A source is either redistributable (LICENCES), deliberately held
    # back (WITHHELD), or unrecorded - and unrecorded still stops the build.
    held = sorted(set(c["source"].unique()) & set(WITHHELD))
    for h in held:
        print("  WITHHELD from the export: %s - %s" % (h, WITHHELD[h]))
    if held:
        c = c[~c["source"].isin(WITHHELD)]

    unlicensed = sorted(set(c['source'].unique()) - set(LICENCES))
    if unlicensed:
        raise SystemExit(
            'a source in the cube has no recorded redistribution licence, so this export cannot '
            'be written: ' + ', '.join(unlicensed) + '\nAdd it to LICENCES with its terms, or '
            'add it to WITHHELD with the reason it cannot be redistributed.')

    def uniq(col):
        return sorted(x for x in c[col].dropna().unique())

    lists = [
        codelist('CL_MATERIAL', 'Material', [(m, m.replace('_', ' ')) for m in uniq('material')],
                 'Atlas material labels. No standard code list exists for mineral commodities; '
                 'this is ours, mapped from each source vocabulary at ingest.'),
        codelist('CL_MEASURE', 'Measure', [(m, m.replace('_', ' ')) for m in uniq('measure')]),
        codelist('CL_STAGE', 'Supply-chain stage',
                 [(s, s) for s in uniq('stage')],
                 'Where in the chain the quantity is counted. mine and processed are NOT '
                 'comparable quantities of the same thing.'),
        codelist('CL_BASIS', 'Measurement basis', [(b, b) for b in uniq('basis')],
                 'gross = whole material weight; content = contained metal. Confusing the two '
                 'is the largest single error available in this subject.'),
        codelist('CL_SOURCE', 'Compilation',
                 [(s, s) for s in uniq('source')],
                 'The compilation an observation comes from. A dimension, not an attribute: two '
                 'compilations counting the same year are two observations, not a conflict.'),
        codelist('CL_UNIT_MEASURE', 'Unit of measure', [(u, u) for u in uniq('unit')]),
        codelist('CL_AREA', 'Reference area',
                 [(a, a) for a in uniq('country_iso3')],
                 'ISO 3166-1 alpha-3, plus dissolved states kept under their own codes '
                 '(SUN, YUG, CSK, DDR, SCG, ANT, ZAR, DEU_FRG, YMD) rather than merged into '
                 'successors.'),
        codelist('CL_OBS_STATUS', 'Observation status', sorted(OBS_STATUS.items()),
                 'SDMX cross-domain CL_OBS_STATUS (subset used here), verified against the SDMX '
                 'Global Registry v2.3.'),
        codelist('CL_CONF_STATUS', 'Confidentiality status', sorted(CONF_STATUS.items()),
                 'SDMX cross-domain CL_CONF_STATUS (subset used here), Registry v1.4.'),
        codelist('CL_FREQ', 'Frequency',
                 [(f, {'A': 'Annual', 'M': 'Monthly'}.get(f, f)) for f in uniq('freq')],
                 'SDMX cross-domain CL_FREQ. Read from the data, never asserted: this list said Annual only while the file already carried monthly observations.'),
    ]

    dsd = {
        'id': 'DSD_MINERAL_FLOWS', 'agencyID': AGENCY, 'version': VERSION,
        'name': 'Mineral production, trade and stocks by country and year',
        'note': ('Dimensions identify an observation; attributes describe it. The split is not '
                 'cosmetic - it is what makes the key checkable. UNIT_MEASURE sits in attributes '
                 'because it is determined by SOURCE and BASIS and adds nothing to identity; '
                 'NATIVE_CODE sits in dimensions because without it three BGS copper forms '
                 'collapse into one meaningless "processed copper".'),
        'dimensions': [
            {'id': 'FREQ', 'codelist': 'CL_FREQ'},
            {'id': 'SOURCE', 'codelist': 'CL_SOURCE'},
            {'id': 'MATERIAL', 'codelist': 'CL_MATERIAL'},
            {'id': 'MEASURE', 'codelist': 'CL_MEASURE'},
            {'id': 'STAGE', 'codelist': 'CL_STAGE'},
            {'id': 'BASIS', 'codelist': 'CL_BASIS'},
            {'id': 'NATIVE_CODE', 'codelist': None,
             'note': "the source's own commodity code - the form actually counted"},
            {'id': 'REF_AREA', 'codelist': 'CL_AREA'},
            {'id': 'TIME_PERIOD', 'codelist': None, 'role': 'time'},
        ],
        'measure': {'id': 'OBS_VALUE',
                    'note': 'in the units of UNIT_MEASURE, as published by the source. Tonnage '
                            'is derivable via CONVERSION_FACTOR; it is not a second measure.'},
        'attributes': [
            {'id': 'UNIT_MEASURE', 'codelist': 'CL_UNIT_MEASURE', 'attachment': 'series'},
            {'id': 'CONVERSION_FACTOR', 'codelist': None, 'attachment': 'series',
             'note': 'multiplier to metric tonnes, absent where no defensible one exists'},
            {'id': 'CODE_SYSTEM', 'codelist': None, 'attachment': 'series'},
            {'id': 'NATIVE_LABEL', 'codelist': None, 'attachment': 'series'},
            {'id': 'OBS_STATUS', 'codelist': 'CL_OBS_STATUS', 'attachment': 'observation'},
            {'id': 'CONF_STATUS', 'codelist': 'CL_CONF_STATUS', 'attachment': 'observation'},
        ],
    }

    dataflow = {
        'id': 'DF_MINERAL_FLOWS', 'agencyID': AGENCY, 'version': VERSION,
        'name': 'Critical Materials Atlas - mineral flows',
        'structure': f'{AGENCY}:DSD_MINERAL_FLOWS({VERSION})',
        'sources_and_licences': LICENCES,
        'observations': int(len(c)),
        'series_key': [d['id'] for d in dsd['dimensions'] if d['id'] != 'TIME_PERIOD'],
    }

    structure = {'meta': {'prepared': TODAY, 'sender': {'id': AGENCY,
                                                        'name': 'Critical Materials Atlas'}},
                 'data': {'codelists': lists, 'dataStructures': [dsd], 'dataflows': [dataflow]}}
    with open(os.path.join(OUT, 'structure.json'), 'w', encoding='utf-8') as f:
        json.dump(structure, f, indent=1, ensure_ascii=False)

    # ── SDMX-CSV ────────────────────────────────────────────────────────────────────────────
    d = c.copy()
    # FREQ AND TIME_PERIOD COME FROM THE DATA. Both were hardcoded to the annual case, and once
    # monthly rows arrived that published 557,121 observations labelled 'A' with a bare year in
    # TIME_PERIOD - so June and July 2026 became the same period and collided. Nothing was
    # malformed and every value sat in its code list, which is why a structural check passed it.
    # An SDMX consumer would have loaded it, trusted the key, and got silently wrong answers.
    d['FREQ'] = d['freq']
    # SDMX-TS period format: annual is YYYY, monthly is YYYY-MM.
    per = d['period'].astype('int64').astype(str)
    d['year'] = per.where(d['freq'] != 'M', per.str[:4] + '-' + per.str[4:6])
    d['STRUCTURE'] = 'dataflow'
    d['STRUCTURE_ID'] = f'{AGENCY}:DF_MINERAL_FLOWS({VERSION})'
    d['ACTION'] = 'I'
    ren = {'source': 'SOURCE', 'material': 'MATERIAL', 'measure': 'MEASURE', 'stage': 'STAGE',
           'basis': 'BASIS', 'native_code': 'NATIVE_CODE', 'country_iso3': 'REF_AREA',
           'year': 'TIME_PERIOD', 'value': 'OBS_VALUE', 'unit': 'UNIT_MEASURE',
           'conversion_factor': 'CONVERSION_FACTOR', 'code_system': 'CODE_SYSTEM',
           'native_label': 'NATIVE_LABEL', 'obs_status': 'OBS_STATUS',
           'conf_status': 'CONF_STATUS'}
    d = d.rename(columns=ren)
    cols = (['STRUCTURE', 'STRUCTURE_ID', 'ACTION', 'FREQ']
            + [x for x in dataflow['series_key'] if x != 'FREQ']
            + ['TIME_PERIOD', 'OBS_VALUE'] + [a['id'] for a in dsd['attributes']])
    missing = [x for x in cols if x not in d.columns]
    if missing:
        raise SystemExit('the cube has no column for: ' + ', '.join(missing)
                         + ' - rebuild it with build_cube.py first')
    d = d[cols]

    path = os.path.join(OUT, 'mineral_flows.sdmx.csv.gz')
    # mtime=0: gzip writes the current time into its header, so rebuilding an IDENTICAL table
    # produced a different file every single time - churning a multi-megabyte binary in git and
    # counting as a reproducibility failure that was never about the data. Found 12 Sep by
    # decompressing both sides and finding them equal.
    with gzip.GzipFile(path, 'wb', mtime=0) as _raw, \
            io.TextIOWrapper(_raw, encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in d.itertuples(index=False):
            w.writerow(['' if pd.isna(v) else v for v in row])

    summary = {
        'generated': TODAY,
        'note': ('The cube as SDMX. Dimensions identify, attributes describe, and the series key '
                 'is checkable - which is the whole reason for adopting the standard.'),
        'structure': 'out/sdmx/structure.json',
        'data': 'out/sdmx/mineral_flows.sdmx.csv.gz',
        'agency': AGENCY, 'dsd': dsd['id'], 'dataflow': dataflow['id'], 'version': VERSION,
        'observations': int(len(c)),
        'codelists': {l['id']: len(l['codes']) for l in lists},
        'obs_status_counts': {k: int(v) for k, v in c['obs_status'].value_counts().items()},
        'licences': LICENCES,
    }
    with open(os.path.join(ROOT, 'out', 'sdmx.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)

    print('wrote out/sdmx/structure.json  (%d code lists, 1 DSD, 1 dataflow)' % len(lists))
    for l in lists:
        print('   %-18s %4d codes' % (l['id'], len(l['codes'])))
    print('wrote out/sdmx/mineral_flows.sdmx.csv.gz  (%d observations, %.1f MB)'
          % (len(d), os.path.getsize(path) / 1e6))
    print('observation status:', summary['obs_status_counts'])


if __name__ == '__main__':
    build()
