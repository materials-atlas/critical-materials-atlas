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
  DERIVED   read_by, reaches_cube - taken from out/graph.json, the OBSERVED dependency graph.
            ONE SCOPE LIMIT, stated because it changes what "unread" means: the recorder does not
            run pipeline/, which has its own entry point and whose scripts spend API quota. So a
            folder only the pipeline opens would read as unread. Those are found by SEARCHING THE
            PIPELINE'S SOURCE for the folder name - grep, which is exactly the weaker evidence
            this project rejected for the main graph - and are labelled as such, never merged in
            with the observed readers. Two folders (raw/oecd_itic, raw/_sources) are in that state
            today, and the honest fix is to record the pipeline, not to widen this word.
            Phase 4 of ARCHITECTURE.md: the register answers *what do we hold*, the graph answers
            *what feeds what*, and licences.py answers *what may leave*. Three questions, three
            files, no overlap - so these are never typed here and never stored twice.

WHY DERIVING THIS IS WORTH THE TROUBLE
The `status` column is a human claim ("in cube", "driver", "reference"). The graph is a
measurement. Where they disagree the register now says so: a folder marked *in cube* that no
builder reads is either a stale claim or a deleted reader, and either way somebody should know.
That comparison is the point - a register that only repeats what someone typed cannot catch the
thing a register exists to catch.

Output: DATA_LIBRARY.md (committed - the record survives even though the files do not) and
out/library.json.

Run:  python build_library.py
"""
import os, sys, json, glob, datetime as dt

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw')
DATA_EXT = {'.xlsx', '.xlsb', '.xls', '.csv', '.zip', '.json', '.pdf', '.parquet', '.txt', '.tsv',
            '.gpkg', '.xlsm'}
# .gpkg and .xlsm added 11 Sep 2026. Their absence did not shrink the table - it DELETED ROWS.
# A folder whose files are all unrecognised was skipped silently, so raw/maus (24.7 MB of
# mining-footprint polygons, read by build_commodity_attribution.py) and raw/sepin (97.3 MB,
# read by build_mining_expansion.py) were held, used, and absent from the record of what we
# hold. A filter that drops data without saying so is the defect this whole file exists
# against, and it was sitting inside it.

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
 'oecd_itic':  ('OECD International Transport and Insurance Costs of merchandise trade (ITIC)',
                'OECD Terms and Conditions - redistribution and commercial use permitted with '
                'attribution; acknowledgment must propagate to sub-licensees',
                'in use (the CIF/FOB coefficient)',
                'The published CIF/FOB margin per importer-exporter-HS2017 heading-year, 976,568 '
                'observations 2015-2024. It REPLACED our own freight estimation entirely: the '
                'per-product medians, the borrowed CEPII 2008 coefficients, the locally-anchored '
                'level and our invented 10% ceiling are all now fallback that fires zero times. '
                'Verbatim from the terms, checked 6 Sep 2026: "you can extract from, download, '
                'copy, adapt, print, distribute, share and embed Data for any purpose, even for '
                'commercial use. You must give appropriate credit to the OECD by using the '
                'citation associated with the relevant Data." Caveat in the same terms: some '
                'content may be owned by third parties and the user is responsible for checking - '
                'ITIC is an OECD statistical product built from member reporting, so this is noted '
                'rather than resolved. Cite as: OECD (2026), International Transport and Insurance '
                'Costs of merchandise trade (ITIC), OECD Data Explorer, accessed 6 September 2026. '
                'NOTE 95% of margins are gravity-model imputations (OBS_STATUS I), not reported '
                'values - published is not the same as observed.'),
 'bgs':        ('BGS World Mineral Statistics full panel', 'Open Government Licence', 'in cube',
                'The spine: 410k records, production + trade by country, 1970-2024.'),
 'baci':       ('CEPII BACI bilateral trade, HS02 and HS17 vintages',
                'Etalab Open Licence 2.0 (redistribution permitted, attribution required)',
                'in cube (partly)',
                'HS02 gives 2002-2024 on one nomenclature. Only the 47 mapped codes are ingested; '
                'the rest is deliberate ballast left out. LICENCE CORRECTED 6 Sep 2026: this was '
                'recorded as "Free for research", which understated it and would have blocked '
                'republication. CEPII licenses BACI under Etalab 2.0 - an open licence permitting '
                'reproduction, redistribution and commercial reuse with attribution, and declared '
                'compatible with CC BY 4.0 - so the BACI-derived rows in out/cube.csv.gz are '
                'properly published, not a leak. Required citation: Gaulier, G. and Zignago, S. '
                '(2010), BACI: International Trade Database at the Product-Level.'),
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
 'sepin':      ('Machine-learning mine-area predictions, "mine-predictions-precise-v1"',
                'UNVERIFIED - no licence file shipped with the download; check before republishing',
                'in use (mining expansion)',
                'CORRECTED 11 Sep 2026. This was written up as "SEPIN / substitution references - '
                'substitution potential inputs", which is not what the file is; nobody caught it '
                'because .gpkg was outside DATA_EXT and the row never appeared in the table. '
                'Measured from the file itself: one layer, 109,517 polygons, columns iso_a3, '
                'country_name, year (2016-2024), area - PREDICTED mining areas per country-year, '
                'and build_mining_expansion.py reads it. Predictions are not observations: this '
                'measures where a model thinks mining is, which is the right input for a trend in '
                'disturbed area and the wrong input for any statement about output.'),
 'bottomup':   ('Bottom-up capacity compilations', 'derived', 'in use',
                'Facility-level buildup behind selected chains.'),
 'valueshare': ('Value-share references', 'derived', 'in use',
                'Stage value distribution along chains.'),
 '_sources':   ('Primary PDFs and source-of-record documents', 'various', 'reference',
                'Where a cited figure can be re-checked against the document it came from.'),
}


SKIPPED = []          # folders holding files whose extensions DATA_EXT does not recognise


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
            # LOUD, not silent. A folder with files but none we recognise is exactly how two used
            # datasets went missing from the register; it is now reported and the extension named,
            # so the fix is to widen DATA_EXT deliberately rather than to never find out.
            other = []
            for dirpath, _, fnames in os.walk(path):
                other += [os.path.splitext(fn)[1].lower() for fn in fnames]
            if other:
                SKIPPED.append((f'raw/{rel}', sorted(set(e for e in other if e))))
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


# ── derived from the observed graph, never typed ────────────────────────────────────────────────
CUBE_FILES = ('pipeline/data/cube.parquet', 'out/cube.parquet')


def pipeline_mentions(folders):
    """{folder: [pipeline scripts naming it]}. GREP, not observation - see the scope limit above."""
    out = {f: [] for f in folders}
    for sub in ('pipeline', 'reconcile'):
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.py'):
                continue
            try:
                txt = open(os.path.join(d, fn), encoding='utf-8', errors='replace').read()
            except OSError:
                continue
            for f in folders:
                name = f.split('/', 1)[1] if '/' in f else f
                if name and name in txt:
                    out[f].append(f'{sub}/{fn}')
    return out


def graph_facts(folders):
    """{folder: (readers, reaches_cube)} from out/graph.json.

    reaches_cube is transitive: a folder reaches the cube if some builder reads it and that
    builder, or something downstream of it, writes a cube file. Direct-reader-only would have
    said no for every source that arrives through an intermediate JSON, which is most of them.
    Absent graph => every field is None, and the register says "not measured" rather than "no".
    """
    gp = os.path.join(ROOT, 'out', 'graph.json')
    if not os.path.exists(gp):
        return {f: (None, None) for f in folders}
    try:
        g = json.load(open(gp, encoding='utf-8'))['builders']
    except Exception:
        return {f: (None, None) for f in folders}

    prod = {}
    for b, v in g.items():
        for w in v.get('writes', ()):
            prod.setdefault(w, set()).add(b)
    edges = {}
    for b, v in g.items():
        for r in v.get('reads', ()):
            for p in prod.get(r, ()):
                if p != b:
                    edges.setdefault(p, set()).add(b)

    cube_writers = {b for f in CUBE_FILES for b in prod.get(f, ())}
    # walk BACKWARDS from the cube's writers: everything that can reach them reaches the cube
    rev = {}
    for p, cs in edges.items():
        for c in cs:
            rev.setdefault(c, set()).add(p)
    reaches, work = set(cube_writers), list(cube_writers)
    while work:
        n = work.pop()
        for p in rev.get(n, ()):
            if p not in reaches:
                reaches.add(p)
                work.append(p)

    facts = {}
    for f in folders:
        pre = f.rstrip('/') + '/'
        # A DIRECTORY LISTING IS NOT A READER. The audit hook records os.scandir as a read with a
        # trailing slash, and this very builder scans every folder under raw/ to size it - so the
        # first version of this line reported all 64 folders as read by something, including the
        # ones nothing opens. Only an actual file open counts.
        readers = sorted(b for b, v in g.items()
                         if any(not r.endswith('/') and (r == f or r.startswith(pre))
                                for r in v.get('reads', ())))
        facts[f] = (readers, bool(set(readers) & reaches))
    return facts


if __name__ == '__main__':
    rows = scan()
    facts = graph_facts([r['folder'] for r in rows])
    mentions = pipeline_mentions([r['folder'] for r in rows])
    for r in rows:
        readers, reaches = facts[r['folder']]
        r['read_by'] = readers
        r['n_readers'] = None if readers is None else len(readers)
        r['reaches_cube'] = reaches
        r['named_in_pipeline_source'] = mentions.get(r['folder']) or []
    # The claim against the measurement. A folder the register calls "in cube" that nothing reads
    # is the drift this file now exists to surface; it is reported, never silently reconciled.
    # A CANDIDATE is not a claim. 'CUBE CANDIDATE' means somebody thinks it should be ingested,
    # not that it is - and the first version of this line reported it as a contradiction with
    # the graph, which would have taught the reader to ignore this section.
    def claims_cube(r):
        st = (r.get('status') or '').lower()
        return 'cube' in st and 'candidate' not in st
    contested = [r for r in rows if r['n_readers'] is not None
                 and (claims_cube(r) != bool(r['reaches_cube']))]
    unread = [r['folder'] for r in rows
              if r.get('n_readers') == 0 and not r['named_in_pipeline_source']]
    only_pipeline = [r for r in rows
                     if r.get('n_readers') == 0 and r['named_in_pipeline_source']]
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
        'derived': 'read_by and reaches_cube come from out/graph.json, the OBSERVED dependency '
                   'graph - never typed here. status is a human claim; where the two disagree the '
                   'folder is listed under contested, because that disagreement is the point.',
        'total_gb': total, 'folders': len(rows), 'undocumented': undoc,
        'unread': unread, 'contested': [r['folder'] for r in contested],
        'skipped_unrecognised': [{'folder': f, 'extensions': e} for f, e in SKIPPED],
        'only_named_in_pipeline_source': [r['folder'] for r in only_pipeline],
        'scope_limit': 'The recorder does not run pipeline/, so a folder only the pipeline opens '
                       'would read as unread. Those are found by searching the pipeline source for '
                       'the folder name - grep, weaker evidence - and listed separately.',
        'library': rows,
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
          '| Folder | Dataset | Licence | Status | Read by | Files | MB | Why we might need it |',
          '|---|---|---|---|---|---|---|---|']
    for r in rows:
        n = r.get('n_readers')
        rb = '?' if n is None else (('pipeline only' if r['named_in_pipeline_source'] else '**nothing**') if n == 0 else
                                    f"{n} builder{'s' if n != 1 else ''}"
                                    + (' &rarr; cube' if r.get('reaches_cube') else ''))
        md.append(f"| `{r['folder']}` | {r['dataset'] or '**UNDOCUMENTED**'} | {r['licence'] or '?'} "
                  f"| {r['status']} | {rb} | {r['n_files']} | {r['size_mb']} | "
                  f"{r['why_we_might_need_it'] or '—'} |")
    if undoc:
        md += ['', f'**Undocumented folders needing a note: {", ".join(undoc)}**']
    if unread:
        md += ['', '## Held, and read by nothing', '',
               'Measured from the observed dependency graph, not from grep. This is not a list of',
               'mistakes - a reference dataset is kept precisely so a future question can reach it -',
               'but a folder here is costing disk and attention for a use that has not happened yet.',
               '']
        for f in unread:
            r = next(x for x in rows if x['folder'] == f)
            md.append(f"- `{f}` &mdash; {r['size_mb']} MB, {r['n_files']} files, status *{r['status']}*")
        if only_pipeline:
            md += ['', 'Excluded from that list, and worth stating rather than hiding: the recorder does',
                   'not run `pipeline/`, which has its own entry point. These folders show no observed',
                   'reader but are NAMED IN THE PIPELINE SOURCE, which is grep - weaker evidence than',
                   'the rest of this table rests on. Recording the pipeline is the real fix.', '']
            for r in only_pipeline:
                md.append(f"- `{r['folder']}` &mdash; named in {', '.join('`%s`' % x for x in r['named_in_pipeline_source'])}")
    if contested:
        md += ['', '## The register and the graph disagree', '',
               'The **status** column is written by a person; **read by** is measured. Where one says',
               'a folder feeds the cube and the other does not, both cannot be right, and neither is',
               'quietly corrected here.', '']
        for r in contested:
            md.append(f"- `{r['folder']}` &mdash; written up as *{r['status']}*, but the graph says "
                      f"{r['n_readers']} reader(s) and "
                      f"{'a path to' if r['reaches_cube'] else 'NO path to'} the cube.")
    md += ['', '---', '',
           '*Generated by `build_library.py`. Sizes and file counts are scanned from disk; the',
           'dataset, licence and reason are written by hand, because a script cannot infer why a',
           'file was kept. Anything unwritten shows as UNDOCUMENTED rather than being omitted.*']
    open(os.path.join(ROOT, 'DATA_LIBRARY.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')

    print(f'WROTE DATA_LIBRARY.md + out/library.json — {len(rows)} sources, {total} GB')
    if SKIPPED:
        print(f'   SKIPPED - files held, extension not recognised ({len(SKIPPED)}):')
        for f, exts in SKIPPED:
            print(f'      {f}  {" ".join(exts)}')
    if undoc:
        print(f'   UNDOCUMENTED ({len(undoc)}): {", ".join(undoc)}')
    else:
        print('   every folder documented')
    if rows and rows[0].get('n_readers') is None:
        print('   graph absent - read_by/reaches_cube not measured this run')
    else:
        print(f'   read by something: {sum(1 for r in rows if r["n_readers"])} of {len(rows)}'
              f' | reaching the cube: {sum(1 for r in rows if r["reaches_cube"])}')
        if only_pipeline:
            print(f'   pipeline-only, unobserved ({len(only_pipeline)}): '
                  f'{", ".join(r["folder"] for r in only_pipeline)}')
        if unread:
            print(f'   READ BY NOTHING ({len(unread)}): {", ".join(unread)}')
        if contested:
            print(f'   STATUS CONTESTED BY THE GRAPH ({len(contested)}): '
                  f'{", ".join(r["folder"] for r in contested)}')
