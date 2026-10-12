# -*- coding: utf-8 -*-
"""Set the USGS Minerals Yearbook against the refining layer the atlas already uses.

Why it matters. The atlas's processed-stage production is 29,015 rows, almost all BGS, and the
exporter-versus-producer finding rests on it: if the refining layer is wrong about WHERE refining
happens, the headline is wrong. The Yearbook is an independent official source for the same
quantity on nine commodities, so it can corroborate or contradict.

What it found, 12 Oct 2026:

1. THE TWO SOURCES AGREE. Median ratio exactly 1.000 for cobalt, copper, indium, lead, tin and
   zinc; 72% of 1,620 country-year pairs within 10%, 93% within a factor of two.

2. THE CUBE'S "processed" STAGE IS REFINERY OUTPUT, not smelter - now evidenced rather than
   assumed, which matters because "processed" is ambiguous enough for a reader to put smelting in
   it. Against the Yearbook's refinery tables copper runs at a median 1.000; against its smelter
   tables, 0.957 and only half within 10%. Where a country-year has both, the cube value is
   closer to the REFINERY figure 71% of the time. The largest apparent disagreements are all
   copper smelter for Chile and the DRC - Chile 2013 smelter 1.36 Mt against a cube 2.75 Mt,
   which is Chile's REFINED output. So the residue is not error; it is the stage.

   Tin and zinc are the exception that proves it: their smelter tables match at a median 1.000,
   because for those metals smelting yields the refined metal. The distinction only bites for
   copper, where smelting and refining are genuinely separate steps.

3. 282 OBSERVATIONS ARE NEW. Bismuth (79), cadmium (80) and indium (50) refinery output are
   country-years the cube holds nothing for - the minor metals the council said UNSD Industrial
   Commodity Statistics would not cover, and does not.

Usage:  python audit_myb_vs_cube.py [--full]
"""
import argparse
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))

MYB = os.path.join(ROOT, 'pipeline', 'data', 'usgs_myb_production.parquet')
CUBE = os.path.join(ROOT, 'pipeline', 'data', 'cube.parquet')

# Yearbook chapter -> cube material. selenium-tellurium is one chapter covering two materials and
# cannot be mapped to a single one, so it is excluded by name rather than silently lost.
MATERIAL = {'copper': 'copper', 'lead': 'lead', 'zinc': 'zinc', 'cobalt': 'cobalt',
            'indium': 'indium', 'bismuth': 'bismuth', 'cadmium': 'cadmium', 'tin': 'tin'}


def yearbook():
    """One row per material, country, year and stage, in tonnes, latest edition winning."""
    import parse_usgs_mcs as M
    df = pd.read_parquet(MYB)
    y = df[(df.stage.isin(['refinery', 'smelter']))
           & (df.kind.isin(['country', 'country_total']))
           & df.value_t.notna()].copy()
    skipped = sorted(set(y.commodity) - set(MATERIAL))
    y = y[y.commodity.isin(MATERIAL)].copy()
    y['material'] = y.commodity.map(MATERIAL)
    m = M.iso3_map()
    y['iso3'] = [M.to_iso3(c, m) for c in y.country]
    unresolved = sorted(set(y.loc[y.iso3.isna(), 'country']))
    y = y.dropna(subset=['iso3'])
    # The same country-year appears in several editions; the latest edition wins, which is the
    # revision rule usgs_mcs_cube.py already applies to the Mineral Commodity Summaries.
    y = (y.sort_values('edition')
           .groupby(['material', 'iso3', 'year', 'stage'], as_index=False)
           .last()[['material', 'iso3', 'year', 'stage', 'value_t', 'edition']])
    return y, skipped, unresolved


def cube():
    c = pd.read_parquet(CUBE)
    c = c[(c.stage == 'processed') & (c.measure == 'production')
          & c.material.isin(MATERIAL.values()) & c.value_t.notna()]
    return (c.groupby(['material', 'country_iso3', 'year'], as_index=False)
             .value_t.max().rename(columns={'country_iso3': 'iso3', 'value_t': 'cube_t'}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--full', action='store_true', help='also list every disagreement')
    a = ap.parse_args()

    y, skipped, unresolved = yearbook()
    c = cube()
    print('Yearbook refining observations usable: %s   cube processed rows: %s'
          % (format(len(y), ','), format(len(c), ',')))
    if skipped:
        print('   chapters not mapped to one material: %s' % ', '.join(skipped))
    if unresolved:
        print('   country names that did not resolve to ISO3 (%d): %s'
              % (len(unresolved), ', '.join(unresolved[:10])))

    j = y.merge(c, on=['material', 'iso3', 'year'], how='outer', indicator=True)
    print()
    print('coverage:  both %s   Yearbook only %s   cube only %s'
          % (format(int((j._merge == 'both').sum()), ','),
             format(int((j._merge == 'left_only').sum()), ','),
             format(int((j._merge == 'right_only').sum()), ',')))

    b = j[(j._merge == 'both') & (j.value_t > 0) & (j.cube_t > 0)].copy()
    b['ratio'] = b.value_t / b.cube_t
    print()
    print('=== agreement over %s pairs ===' % format(len(b), ','))
    for lo, hi, lbl in ((0.98, 1.02, 'within 2%'), (0.9, 1.1, 'within 10%'),
                        (0.5, 2.0, 'within 2x')):
        n = int(((b.ratio >= lo) & (b.ratio <= hi)).sum())
        print('   %-12s %6d  (%4.1f%%)' % (lbl, n, 100.0 * n / len(b)))
    print('   median ratio %.3f' % b.ratio.median())

    print()
    print('=== by material and stage: which stage does the cube actually hold? ===')
    t = b.groupby(['material', 'stage']).agg(
        pairs=('ratio', 'size'), median=('ratio', 'median'),
        within10=('ratio', lambda s: round(100.0 * ((s >= .9) & (s <= 1.1)).mean(), 1)))
    print(t.to_string())

    cu = b[b.material == 'copper']
    w = cu.pivot_table(index=['iso3', 'year'], columns='stage',
                       values=['value_t', 'cube_t']).dropna()
    if len(w):
        closer = ((w[('value_t', 'refinery')] - w[('cube_t', 'refinery')]).abs()
                  < (w[('value_t', 'smelter')] - w[('cube_t', 'refinery')]).abs()).mean()
        print()
        print('copper country-years carrying both stages: %d' % len(w))
        print('   the cube value is closer to the REFINERY figure in %.0f%%, smelter in %.0f%%'
              % (100 * closer, 100 * (1 - closer)))

    print()
    print('=== what the cube does not have at all ===')
    new = j[j._merge == 'left_only']
    if len(new):
        print(new.groupby(['material', 'stage']).size().to_string())

    if a.full:
        b['gap_t'] = (b.value_t - b.cube_t).abs()
        out = b[(b.ratio < 0.9) | (b.ratio > 1.1)].nlargest(40, 'gap_t')
        print()
        print('=== the 40 largest disagreements by tonnes at stake ===')
        print(out[['material', 'stage', 'iso3', 'year', 'value_t', 'cube_t', 'ratio']]
              .to_string(index=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
