#!/usr/bin/env python3
"""SOURCE METADATA — what each compilation actually measures, and why they differ.

The owner's request: "we need the metadata of all sources which will explain in what the difference
consists." Until now that knowledge lived scattered across builder docstrings, SOURCE.md files and
the pairing map's reason strings. A reader comparing two numbers had no single place to learn that
one counts gross ore and the other contained metal.

Two halves, deliberately:
  * COVERAGE is COMPUTED from the cube - years, countries, materials, row counts, measures. It
    cannot go stale, and it cannot flatter the source.
  * INTERPRETATION is WRITTEN. What a compilation means by "production", whose numbers it is
    really carrying, and where it is known to be thin are things a script cannot infer. Each note
    below is a claim we are making and can be held to.

Run:  python build_sources.py   ->  out/sources.json
"""
import os, sys, json
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))

# ── written interpretation. Keyed by the `source` value carried on every cube row. ─────────────
META = {
 'BGS World Mineral Statistics': {
   'publisher': 'British Geological Survey (UK)', 'licence': 'Open Government Licence',
   'url': 'https://www2.bgs.ac.uk/mineralsuk/statistics/wms.cfc?method=searchWMS',
   'edition': 'live OGC API, pulled 2026-09-04',
   'what_it_is': 'A compilation of the statistical returns that national statistical offices file. '
                 'BGS does not measure production; it collects and standardises what states report.',
   'measures': 'production, imports and exports, by commodity FORM',
   'basis': 'Whatever the reporting country used. Mixed across commodities: some series are gross '
            'ore weight, some contained metal, and the unit string says which.',
   'stage': 'Carried in the commodity name itself - "copper, mine" and "copper, refined" are '
            'separate series, which is why a stage filter alone can silently sum several forms.',
   'strengths': ['Longest per-country panel we hold (1970-2024) with trade alongside production',
                 'Form-level granularity: the stage is explicit, not inferred',
                 'Marks a reported NIL distinctly from a missing row'],
   'limits': ['A sum over its reporters is NOT a world total. Coverage varies enormously by '
              'commodity: 3 reporters for germanium metal against 40+ for refined copper.',
              'Under-captures output that never enters a national return - its DRC cobalt cell is '
              'roughly half what other compilations show, and the gap grows with artisanal mining.',
              'Cement has ~32 reporters and no China or India, so it is a European sub-panel.',
              'Trade reporting collapses after 2018 for most commodities.'],
   'differs_because': 'It reports what states report. Where a state under-reports, mis-stages or '
                      'does not file, BGS inherits that exactly - which is a feature for '
                      'traceability and a trap for anyone summing it as a world figure.',
 },
 'USGS Historical Statistics (DS 140)': {
   'publisher': 'United States Geological Survey', 'licence': 'US public domain',
   'url': 'https://www.usgs.gov/centers/national-minerals-information-center',
   'edition': 'Data Series 140 workbooks',
   'what_it_is': 'Long-run annual series per commodity: US supply and demand back to 1900, plus a '
                 'WORLD production column for most commodities.',
   'measures': 'US production (mine/smelter/primary/secondary), imports, exports, stocks, '
               'apparent consumption, unit values; and world production totals',
   'basis': 'Metric tons unless the workbook notes otherwise; content vs gross varies by commodity.',
   'stage': 'Named per column ("mine production", "refinery production").',
   'strengths': ['Depth no other source here approaches - 1900 onward',
                 'World totals that give a denominator independent of summing national returns',
                 'Marks withheld (company-confidential) cells rather than dropping them'],
   'limits': ['Country detail is US-only; the world figures are totals, not country breakdowns.',
              'Apparent consumption is USGS\'s own derived series, not an observation - it is '
              'stored under measure_family "derived_by_source" so it can never be mistaken for one.',
              'World figures are estimates, and USGS says so where it cannot make a reliable one.'],
   'differs_because': 'USGS estimates a world total; BGS adds up reporters. Where reporting is '
                      'incomplete the two must differ, and the USGS figure is usually the larger.',
 },
 'CEPII BACI (HS02)': {
   'publisher': 'CEPII (France), from UN Comtrade', 'licence': 'Free for research, registration',
   'url': 'https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37',
   'edition': 'V202601, HS02 nomenclature, 2002-2024',
   'what_it_is': 'Bilateral trade reconciled by CEPII: every shipment is reported by both the '
                 'exporter and the importer, and BACI resolves the two into one value per flow.',
   'measures': 'trade quantities and values by HS6 product code',
   'basis': 'Gross shipped weight of a PRODUCT, not contained metal.',
   'stage': 'Whatever the HS code describes - which is a product class, not a material.',
   'strengths': ['Both sides of each flow already reconciled',
                 '23 years on one nomenclature, so trends are not broken by code revisions'],
   'limits': ['An HS code is not a material. Several carry more than one metal, and a code can '
              'mix stages. Only the 47 codes mapped in our crosswalk are ingested.',
              'Re-exports and entrepot trade inflate the countries that handle rather than produce.',
              'Aggregated here to country-year; the bilateral pairs stay in the trade layer.'],
   'differs_because': 'It measures what crossed a border in a product class, which is not what a '
                      'country produced of a metal. Differencing it against production requires the '
                      'form and the code to be paired deliberately.',
 },
 'World Mining Data': {
   'publisher': 'Austrian Federal Ministry (BMF)', 'licence': 'Free, attribution',
   'url': 'https://www.world-mining-data.info/',
   'edition': '6.4 Production by country, 2020-2024',
   'what_it_is': 'An annual world compilation of mine production by country and commodity.',
   'measures': 'mine production',
   'basis': 'Stated per sheet; several are content-basis and the sheet title says so '
            '("Chromium (Cr2O3)" is an oxide basis, not contained chromium).',
   'stage': 'Mine only.',
   'strengths': ['The only source here that marks every cell REPORTED or ESTIMATED',
                 'Broad country coverage for a compact file'],
   'limits': ['Recent years only (2020-2024) - no depth', 'Mine stage only, no refining, no trade'],
   'differs_because': 'It estimates where a country does not report, so it fills holes BGS leaves '
                      'empty. That makes it closer to a world total and further from a pure return.',
 },
 'IEA Critical Minerals Dataset': {
   'publisher': 'International Energy Agency', 'licence': 'CC BY 4.0',
   'url': 'https://www.iea.org/data-and-statistics/data-product/critical-minerals-dataset',
   'edition': 'May 2025 edition (base year 2024). Four editions exist: Jul 2023, May 2024, '
              'May 2025, Jul 2026 - we hold ONE.',
   'what_it_is': 'Supply and demand for energy-transition minerals. Mostly projections; the first '
                 'column of the supply sheet is an observed base year.',
   'measures': 'country-level production at mine and refining stage - OBSERVED base-year column only',
   'basis': 'Contained metal / refined product, in thousand tonnes. NOT gross ore.',
   'stage': 'Explicit: separate mining and refining blocks.',
   'strengths': ['Refining by country, which is the layer where BGS is thinnest and where the '
                 'chokepoint argument actually lives',
                 'Covers the energy-transition minerals in most demand for analysis'],
   'limits': ['Only 6 minerals, one observed year per edition.',
              'Everything beyond the base-year column is a SCENARIO and is deliberately not '
              'ingested: a forecast must not sit where a query could difference it against '
              'measured history and call the result a trend.',
              'Its published top-1 / top-3 shares are already-computed concentration statistics '
              'and are not ingested either - the cube stores observations and computes '
              'concentration itself.',
              'WE HOLD ONE EDITION OF FOUR. Each edition carries its own observed base year, so '
              'the other three would turn a single snapshot into a 2022-2025 series AND expose how '
              'much the IEA revises between editions. Download needs a free IEA account.'],
   'differs_because': 'It reports contained metal at a stage it names explicitly. Against BGS ore '
                      'series the ratio can be 40x - lithium as contained metal versus spodumene '
                      'at gross weight - which is a unit difference, not a disagreement.',
 },
}

PAIRWISE = [
 ('BGS vs USGS', 'BGS sums national returns; USGS estimates a world total. Where reporting is '
  'incomplete USGS is usually larger - the honest reading of a gap is coverage, not error.'),
 ('BGS vs IEA', 'BGS often reports ORE at gross weight where IEA reports CONTAINED metal. Lithium '
  'is the extreme case (~40x). Always check `basis` before differencing.'),
 ('BGS vs WMD', 'Both are country-level mine production, so these are genuinely comparable - but '
  'WMD estimates where a country is silent and BGS leaves the cell empty.'),
 ('production vs BACI', 'Production is of a MATERIAL; BACI is of a PRODUCT CLASS (an HS code). '
  'They can only be differenced where a crosswalk explicitly pairs the form to the code.'),
]


def main():
    c = pd.read_parquet(os.path.join(ROOT, 'pipeline', 'data', 'cube.parquet'))
    out = []
    for src, g in c.groupby('source'):
        m = dict(META.get(src, {}))
        m.update({
            'source': src,
            'coverage': {           # COMPUTED - never hand-maintained
                'rows': int(len(g)), 'materials': int(g.material.nunique()),
                'geographies': int(g.country_iso3.nunique()),
                'years': [int(g.year.min()), int(g.year.max())],
                'measures': sorted(g.measure.unique().tolist()),
                'stages': sorted(g.stage.dropna().unique().tolist()),
                'units': sorted(g.unit.dropna().unique().tolist())[:6],
                'series': int(g.series_id.nunique()),
                'pct_convertible_to_tonnes': round(100 * g.value_t.notna().mean(), 1),
            },
        })
        out.append(m)
    out.sort(key=lambda r: -r['coverage']['rows'])
    doc = {
        'note': 'What each compilation measures and why they differ. COVERAGE is computed from the '
                'cube and cannot go stale. INTERPRETATION is written by hand, because what a source '
                'MEANS by "production" is not inferable from its rows - each note is a claim we can '
                'be held to.',
        'golden_rule': 'Two numbers are comparable only when code_system, basis, stage and unit '
                       'agree. Joining on material alone turns a definition difference into a false '
                       'contradiction.',
        'pairwise': [{'pair': p, 'difference': d} for p, d in PAIRWISE],
        'sources': out,
    }
    json.dump(doc, open(os.path.join(ROOT, 'out', 'sources.json'), 'w', encoding='utf-8'), indent=1)
    print(f'WROTE out/sources.json — {len(out)} sources')
    for r in out:
        cv = r['coverage']
        print(f"  {r['source'][:38]:<40} {cv['rows']:>7,} rows  {cv['years'][0]}-{cv['years'][1]}  "
              f"{cv['materials']:>3} mats  {cv['geographies']:>3} geos"
              + ('' if r.get('publisher') else '   << NO WRITTEN METADATA'))


if __name__ == '__main__':
    main()
