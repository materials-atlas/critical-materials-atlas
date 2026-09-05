#!/usr/bin/env python3
"""THE DATA LIBRARY — an index of every external dataset the project holds.

Asked for directly: "even if not in the cube they should be somewhere in the project, save all of
them, and note somewhere we may need them later."

The files already are saved - 3.4 GB across raw/ - but raw/ is gitignored, so the repository knew
nothing about them. A file on one disk with no record of what it is or why it was kept is not an
asset; it is clutter that looks like an asset. This builder writes the record.

  SCANNED   folder, file count, formats, total size, newest file. Computed, so it cannot drift
            from what is actually on disk.
  WRITTEN   what the source is, its licence, and WHY WE MIGHT NEED IT LATER. A script cannot
            infer that, so anything not written up is reported as UNDOCUMENTED rather than
            quietly omitted - which is the pressure that keeps this honest.

Output: DATA_LIBRARY.md (committed - the record survives even though the files do not) and
out/library.json.

Run:  python build_library.py
"""
import os, sys, json, glob, datetime as dt

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw')
DATA_EXT = {'.xlsx', '.xlsb', '.xls', '.csv', '.zip', '.json', '.pdf', '.parquet', '.txt', '.tsv'}

# ── written notes, keyed by folder under raw/. `use` answers "why might we need this later?" ────
NOTES = {
 'iea':        ('IEA Critical Minerals Dataset + report PDFs', 'CC BY 4.0', 'in cube (driver too)',
                'Base-year supply by country at mine AND refining stage - the layer where BGS is '
                'thinnest. Two editions held, two missing.'),
 'iea_drivers': ('IEA activity datasets: Energy & AI annex, Value Added DB, EEI Highlights',
                'MIXED - Energy&AI is CC BY 4.0; Value Added and EEI are NOT CC',
                'driver candidates',
                'Country-year ACTIVITY series for the consumption model (demand = activity x '
                'intensity). Value added by ISIC division is the driver the IEA itself uses. The '
                'non-CC two may be used but never redistributed in out/.'),
 'iea_etp':    ('IEA Energy Technology Perspectives 2017 summaries',
                'RESTRICTED - fee required for use in modelling / derived products',
                'HELD, NOT USABLE',
                'LICENCE-BLOCKED, not merely non-CC: the terms require a paid Licence Agreement to '
                'use this data "in any type of modelling for the purpose of creating derived data '
                'or derived products" - which is exactly what every page here is. Held for '
                'reference so the decision is inspectable and nobody re-downloads it to ask again. '
                'Also a 2018-vintage scenario set, superseded several times.'),
 'iea_rdd':    ('IEA Energy Technology RD&D Budgets (public + private), 1974-2025',
                'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'Country-year-technology R&D SPEND. Money, not an activity a material intensity '
                'can multiply, so not a driver. Kept because it is the best public measure of how '
                'hard a country is trying on a technology - a possible leading indicator for '
                'deployment, and a possible read on SUBSTITUTION effort, which the atlas already '
                'has a layer for. Not redistributable.'),
 'iea_energy_econ': ('IEA Fossil Fuel Subsidies Database, 2010-2024', 'CC BY 4.0', 'reference',
                'Consumption subsidies by country-year. Not a material series - but energy price '
                'support is one of the real reasons SMELTING locates where it does (aluminium and '
                'silicon are power-cost industries). If the chokepoint map is ever pushed from '
                '"where refining is" to "why it is there", this is an input to that argument.'),
 'bgs':        ('BGS World Mineral Statistics full panel', 'Open Government Licence', 'in cube',
                'The spine: 410k records, production + trade by country, 1970-2024.'),
 'baci':       ('CEPII BACI bilateral trade, HS02 and HS17 vintages', 'Free for research',
                'in cube (partly)',
                'HS02 gives 2002-2024 on one nomenclature. Only the 47 mapped codes are ingested; '
                'the rest is deliberate ballast left out.'),
 'usgs_hist':  ('USGS Historical Statistics (DS 140), 84 workbooks', 'US public domain', 'in cube',
                'Depth to 1900 and world production totals. Found by the catalog after sitting '
                'unused except for its price column.'),
 'usgs_mcs':   ('USGS Mineral Commodity Summaries PDFs', 'US public domain', 'partly extracted',
                'RESERVES, refinery output, import reliance and recycling are still unextracted - '
                'the largest known unopened box in the library.'),
 'usgs_critmin': ('USGS critical-minerals deposit map (PP1802)', 'US public domain', 'reference',
                'Deposit points, no time dimension. Site-level grain, so not cube material.'),
 'usgs_outlook': ('USGS Outlook tables', 'US public domain', 'in use',
                'Refining concentration where USGS measures it directly.'),
 'wmd':        ('World Mining Data 6.4, production by country', 'Free, attribution', 'in cube',
                'The only source that marks every cell reported vs estimated.'),
 'activity':   ('Activity drivers: steel, vehicles, EV, electricity, solar, wind, cement, '
                'population, aerospace, semiconductors...', 'mixed public', 'in use',
                'The inputs to the consumption model. Any new driver lands here.'),
 'apparent':   ('Per-metal apparent-consumption inputs', 'derived', 'in use',
                'Feeds build_apparent.py, which is retained because the cube cannot yet do '
                'lithium.'),
 'comtrade':   ('UN Comtrade extracts', 'UN, free', 'in use',
                'Mirror side of the trade reconciliation.'),
 'eucrm':      ('EU Critical Raw Materials assessment', 'EU, reuse permitted', 'reference',
                'Criticality scores and end-use shares - indicators ABOUT materials, so a '
                'dimension rather than cube rows. Also the list vintages used for the ex-ante '
                'freeze test.'),
 'pink':       ('World Bank Pink Sheet commodity prices', 'World Bank, CC BY 4.0', 'reference',
                'Annual public price series - the licence-safe option if a price sidecar is ever '
                'built.'),
 'geodist':    ('CEPII GeoDist country distances', 'Free for research', 'in use',
                'Distance/contiguity for trade-gravity and reallocation work.'),
 'geopolrisk': ('GeoPolRisk inputs (governance indicators)', 'mixed', 'in use',
                'Governance weighting for the criticality layer.'),
 'refining':   ('Refinery and smelter capacity references', 'mixed', 'in use',
                'The midstream layer behind the chokepoint map.'),
 'surveys':    ('National geological survey extracts', 'mixed public', 'reference',
                'Country-specific reserves and production where a survey publishes better than '
                'the global compilations.'),
 'au_ozmin':   ('Geoscience Australia OZMIN', 'CC BY 4.0', 'reference',
                'Australian deposits and resources - a strong reserves source if a reserves layer '
                'is built.'),
 'icmm':       ('ICMM member and site data', 'ICMM terms', 'reference', 'Industry-side context.'),
 'ipis':       ('IPIS artisanal mining site data (DRC)', 'CC BY-SA', 'reference',
                'DIRECTLY relevant to the cobalt gap: BGS under-reports DRC precisely because '
                'artisanal output does not enter national returns.'),
 'jasansky':   ('Jasansky et al. mine-level dataset', 'CC BY 4.0', 'reference',
                'Asset-level mine production - different grain from the cube, but the best public '
                'route to a bottom-up check.'),
 'maus':       ('Maus et al. global mining land use', 'CC BY 4.0', 'reference',
                'Satellite-derived mine footprints; a physical cross-check on where mining is.'),
 'mrds':       ('USGS Mineral Resources Data System', 'US public domain', 'reference',
                'Deposit records, site grain.'),
 'osm':        ('OpenStreetMap extracts', 'ODbL', 'reference',
                'Infrastructure geometry (ports, rail) for logistics work.'),
 'wikidata':   ('Wikidata entity extracts', 'CC0', 'reference', 'Entity reconciliation helper.'),
 'sepin':      ('SEPIN / substitution references', 'mixed', 'reference',
                'Substitution potential inputs.'),
 'bottomup':   ('Bottom-up capacity compilations', 'derived', 'in use',
                'Facility-level buildup behind selected chains.'),
 'valueshare': ('Value-share references', 'derived', 'in use',
                'Stage value distribution along chains.'),
 '_sources':   ('Primary PDFs and source-of-record documents', 'various', 'reference',
                'Where a cited figure can be re-checked against the document it came from.'),
}


def scan():
    out = []
    for path in sorted(glob.glob(os.path.join(RAW, '*'))):
        name = os.path.basename(path)
        if os.path.isfile(path):
            continue
        files, size, newest = [], 0, 0
        for dirpath, _, fnames in os.walk(path):
            for fn in fnames:
                if os.path.splitext(fn)[1].lower() in DATA_EXT:
                    fp = os.path.join(dirpath, fn)
                    try:
                        size += os.path.getsize(fp)
                        newest = max(newest, os.path.getmtime(fp))
                    except OSError:
                        continue
                    files.append(os.path.splitext(fn)[1].lower())
        if not files:
            continue
        note = NOTES.get(name)
        out.append({
            'folder': f'raw/{name}', 'n_files': len(files),
            'size_mb': round(size / 1e6, 1),
            'formats': sorted(set(files)),
            'newest': dt.date.fromtimestamp(newest).isoformat() if newest else None,
            'dataset': note[0] if note else None,
            'licence': note[1] if note else None,
            'status': note[2] if note else 'UNDOCUMENTED',
            'why_we_might_need_it': note[3] if note else None,
        })
    return sorted(out, key=lambda r: -r['size_mb'])


if __name__ == '__main__':
    rows = scan()
    undoc = [r['folder'] for r in rows if r['status'] == 'UNDOCUMENTED']
    total = round(sum(r['size_mb'] for r in rows) / 1000, 2)
    doc = {
        'note': 'Every external dataset held under raw/. The FILES are gitignored (3.4 GB, and all '
                're-downloadable from the documented sources); THIS RECORD is committed, so the '
                'repository always knows what was collected, under what licence, and why it was '
                'kept - even on a machine where the files are absent.',
        'rule': 'A dataset that is not in the cube is not thereby useless. Three intakes: cube '
                '(mineral quantity per country-year), driver (activity series per country-year), '
                'reference (everything a question might need later). A non-CC licence permits use '
                'but never redistribution in out/.',
        'total_gb': total, 'folders': len(rows), 'undocumented': undoc, 'library': rows,
    }
    json.dump(doc, open(os.path.join(ROOT, 'out', 'library.json'), 'w', encoding='utf-8'), indent=1)

    md = ['# Data library', '',
          f'Every external dataset the project holds: **{len(rows)} sources, {total} GB**.', '',
          'The files live under `raw/`, which is gitignored - they are large and all re-downloadable',
          'from the sources below. **This record is committed**, so the repository always knows what',
          'was collected, under what licence, and why it was kept, even where the files are absent.',
          '', 'Not being in the cube does not make a dataset useless. There are three intakes:', '',
          '| Intake | Test |', '|---|---|',
          '| **cube** | a mineral quantity for a country and a year |',
          '| **driver** | an activity series per country-year that an intensity can apply to |',
          '| **reference** | everything a future question might need |', '',
          '**A non-CC licence permits use but never redistribution in `out/`.**', '',
          '| Folder | Dataset | Licence | Status | Files | MB | Why we might need it |',
          '|---|---|---|---|---|---|---|']
    for r in rows:
        md.append(f"| `{r['folder']}` | {r['dataset'] or '**UNDOCUMENTED**'} | {r['licence'] or '?'} "
                  f"| {r['status']} | {r['n_files']} | {r['size_mb']} | "
                  f"{r['why_we_might_need_it'] or '—'} |")
    if undoc:
        md += ['', f'**Undocumented folders needing a note: {", ".join(undoc)}**']
    md += ['', '---', '',
           '*Generated by `build_library.py`. Sizes and file counts are scanned from disk; the',
           'dataset, licence and reason are written by hand, because a script cannot infer why a',
           'file was kept. Anything unwritten shows as UNDOCUMENTED rather than being omitted.*']
    open(os.path.join(ROOT, 'DATA_LIBRARY.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')

    print(f'WROTE DATA_LIBRARY.md + out/library.json — {len(rows)} sources, {total} GB')
    if undoc:
        print(f'   UNDOCUMENTED ({len(undoc)}): {", ".join(undoc)}')
    else:
        print('   every folder documented')
