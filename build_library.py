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
 'iea_bulk/gas-trade-flows': ('Gas Trade Flows, 31 countries', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'Entry/exit point flows. Method interest rather than content: it is another bilateral flow dataset where both sides report, the same reconciliation problem the trade engine solves.'),
 'iea_bulk/gender-and-energy': ('Gender and Energy', 'CC BY 4.0', 'reference',
                'Workforce and participation indicators for the energy sector. No material dimension; kept for completeness of the collection.'),
 'iea_bulk/global-energy-and-climate-model-key-input-data': ('GEC Model key input data - macro drivers', 'NOT CC - Terms of Use for Non-CC Material', 'driver (high value)',
                'GDP, population, industry value added, steel and cement output: the IEA own driver set, and the closest published match to what our consumption model needs. If any single download here changes the consumption layer, it is this one.'),
 'iea_bulk/global-energy-review-co2-emissions-in-2021': ('Global Energy Review: CO2 emissions 2021', 'CC BY 4.0', 'reference',
                'Dated single-year snapshot; superseded by the Global Energy Review dataset.'),
 'iea_bulk/global-energy-review-dataset': ('Global Energy Review dataset', 'CC BY 4.0', 'reference',
                'Annual world aggregates for supply, generation, technology deployment and CO2. Context and sanity-check numbers rather than an input.'),
 'iea_bulk/global-ev-outlook-2025': ('Global EV Outlook 2025', 'NOT CC - Terms of Use for Non-CC Material', 'driver (prior vintage)',
                'The previous edition. Kept because two editions of the same series show how much the IEA restates EV history - the revision test we could NOT run on the Critical Minerals dataset, because there the editions never share an observed year.'),
 'iea_bulk/global-ev-outlook-2026': ('Global EV Outlook 2026', 'NOT CC - Terms of Use for Non-CC Material', 'driver (refresh)',
                'The source behind our existing `ev` driver. EV sales and stock by country-year, and the battery chemistry splits that decide whether a marginal EV pulls lithium/cobalt/nickel or LFP.'),
 'iea_bulk/greenhouse-gas-emissions-from-energy-highlights': ('GHG Emissions from Energy Highlights', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'Emissions by country-year. Relevant if an embodied-emissions layer is ever built on top of the material flows.'),
 'iea_bulk/household-appliances-database': ('Household Appliances Database, 100+ countries', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'Appliance stock by country is an activity series, and appliances are where a lot of copper, steel and rare-earth magnets physically end up. It becomes a driver the moment a published material-per-appliance intensity exists.'),
 'iea_bulk/household-energy-expenditure-database': ('Household Energy Expenditure Database', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'Energy spend by household. Affordability context, no material link.'),
 'iea_bulk/hydrogen-production-and-infrastructure-projects-database': ('Hydrogen Production and Infrastructure Projects Database', 'CC BY 4.0', 'reference',
                'Project grain, so not cube material - but electrolysers consume iridium and platinum, so this is the demand side of a PGM story the atlas already tells from the supply side.'),
 'iea_bulk/iea-electricity-access-data-collection-template': ('Electricity Access Data Collection Template', 'CC BY 4.0', 'reference',
                'A questionnaire template, not data. Kept only so nobody downloads it twice.'),
 'iea_bulk/monthly-electricity-statistics': ('Monthly Electricity Statistics, 47 countries', 'NOT CC - Terms of Use for Non-CC Material', 'driver',
                'Refreshes the existing `elec` driver, and monthly grain makes it the natural series for testing whether smelting output tracks power availability.'),
 'iea_bulk/monthly-gas-statistics': ('Monthly Gas Statistics, OECD', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'Gas price and supply context. Matters to materials only through energy cost, which is a real driver of where smelting happens.'),
 'iea_bulk/monthly-oil-price-statistics-2': ('Monthly Oil Price Statistics', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'End-use energy prices. The nearest public proxy for the energy cost faced by industry, which is what actually decides smelter economics.'),
 'iea_bulk/monthly-oil-statistics': ('Monthly Oil Statistics, OECD', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'Energy cost context.'),
 'iea_bulk/monthly-reliance-on-russian-oil-for-oecd-countries': ('Reliance on Russian oil, OECD', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'A worked example of import-dependence measurement - the same question the atlas asks of minerals, asked of oil by an institution with better data.'),
 'iea_bulk/net-zero-by-2050-scenario': ('Net Zero by 2050 Scenario data', 'NOT CC - Terms of Use for Non-CC Material', 'reference (scenario)',
                'Forecast, so never a cube row. Useful only as a citable demand narrative, and the 2021 vintage is now itself a historical artefact - what the world thought 2050 looked like.'),
 'iea_bulk/quarterly-coal-statistics': ('Quarterly Coal Statistics (world + OECD trade)', 'NOT CC - Terms of Use for Non-CC Material', 'CUBE CANDIDATE',
                'COKING COAL IS ONE OF OUR 32 MATERIALS. Production and trade by country at quarterly grain - the only bulk download here with a plausible route straight into the cube, once the coking vs thermal split and the annual roll-up are checked.'),
 'iea_bulk/reliance-on-russian-fossil-fuels-in-oecd-and-eu-countries': ('Reliance on Russian fossil fuels, OECD/EU', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'As above: dependence methodology worth reading against our own leverage layer.'),
 'iea_bulk/sdg7-database': ('SDG7: electricity access and clean cooking', 'CC BY 4.0', 'reference',
                'Access rates by country-year. The material link is indirect but real: closing an access gap means grid, which means conductor - it needs a published km-per-connection intensity to become anything more than a narrative.'),
 'iea_bulk/solid-biofuels-consumption-estimation-model': ('Solid biofuels consumption estimation model', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'An estimation MODEL in a spreadsheet, not observations. Worth one read for its method - it solves the same problem our consumption model does, estimating unmeasured consumption from activity proxies.'),
 'iea_bulk/the-energy-security-case-for-tackling-gas-flaring-and-methane-leaks-dataset': ('Gas flaring and methane leaks', 'CC BY 4.0', 'reference',
                'No material link; collection completeness.'),
 'iea_bulk/the-implications-of-oil-and-gas-field-decline-rates-dataset': ('Oil and gas field decline rates', 'CC BY 4.0', 'reference',
                'Decline-rate methodology. Directly analogous to ore-grade decline in mining, which is a question the atlas has not yet asked and probably should.'),
 'iea_bulk/the-role-of-critical-minerals-in-clean-energy-transitions-2': ('The Role of Critical Minerals in Clean Energy Transitions (2021 report data)', 'NOT CC - Terms of Use for Non-CC Material', 'reference',
                'The one dataset on the free list actually ABOUT minerals. Demand by technology and the supply-concentration figures behind the 2021 report - useful as a dated comparator for how the IEA framed concentration before the GCMO series existed.'),
 'iea_bulk/weather-for-energy-tracker': ('Weather for Energy Tracker', 'CC BY 4.0', 'reference (underrated)',
                'The one I wrongly dismissed. Drought curtails hydro, and hydro curtailment curtails ALUMINIUM and silicon smelting - Yunnan is the documented case. A weather series is a real explanatory variable for why refined output moves in a year when capacity did not.'),
 'iea_bulk/world-energy-balances-highlights': ('World Energy Balances Highlights', 'NOT CC - Terms of Use for Non-CC Material', 'driver',
                'Energy balances for 185+ countries. Industrial energy use is a broad activity proxy where no physical output series exists, and the balance structure names the industry sectors.'),
 'iea_bulk/world-energy-investment-2021-datafile': ('World Energy Investment 2021', 'CC BY 4.0', 'reference',
                'Investment by sector and region.'),
 'iea_bulk/world-energy-investment-2022-datafile-2': ('World Energy Investment 2022', 'CC BY 4.0', 'reference',
                'Investment by sector and region.'),
 'iea_bulk/world-energy-investment-2023-datafile-2': ('World Energy Investment 2023', 'CC BY 4.0', 'reference',
                'Investment by sector and region.'),
 'iea_bulk/world-energy-investment-2024-datafile': ('World Energy Investment 2024', 'CC BY 4.0', 'reference',
                'Investment by sector and region.'),
 'iea_bulk/world-energy-investment-2025-datafile': ('World Energy Investment 2025', 'CC BY 4.0', 'reference',
                'Investment by sector and region.'),
 'iea_bulk/world-energy-investment-2026-datafile': ('World Energy Investment 2026', 'CC BY 4.0', 'reference',
                'Latest edition. Six editions together give an investment TIME SERIES by sector - a leading indicator for the capacity that later consumes metal, and one of the few places where the older editions are worth keeping rather than superseded.'),
 'iea_bulk/world-energy-outlook-2025-free-dataset': ('World Energy Outlook 2025 free dataset', 'NOT CC - Terms of Use for Non-CC Material', 'reference (scenario)',
                'Same rule as above: cited, never ingested.'),
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
    # iea_bulk holds one subfolder per dataset - list them individually rather than as one blob,
    # because "31 IEA files" tells a reader nothing and the whole point of this record is that a
    # future question can find the dataset it needs.
    roots = sorted(glob.glob(os.path.join(RAW, '*')))
    bulk = os.path.join(RAW, 'iea_bulk')
    if os.path.isdir(bulk):
        roots = [r for r in roots if r != bulk] + sorted(glob.glob(os.path.join(bulk, '*')))
    for path in roots:
        name = os.path.basename(path)
        rel = os.path.relpath(path, RAW).replace(os.sep, '/')
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
        note = NOTES.get(rel) or NOTES.get(name)
        out.append({
            'folder': f'raw/{rel}', 'n_files': len(files),
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
