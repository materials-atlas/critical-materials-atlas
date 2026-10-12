# -*- coding: utf-8 -*-
"""Cube ingest for the USGS Minerals Yearbook by-country production tables.

What this adds that nothing else holds: REFINERY output for the minor metals. 282 country-years
of bismuth, cadmium, indium and cobalt refining have no counterpart anywhere in the cube - the
layer the atlas had to approximate from industry estimates, and the layer UNSD Industrial
Commodity Statistics was supposed to supply and does not.

Three decisions worth stating, because each one could have been made wrongly and silently:

1. SMELTER GETS ITS OWN STAGE. The cube's vocabulary is mine / processed / compound / unspecified,
   with no smelter. Mapping smelter output into `processed` would destroy the finding that paid
   for this ingest: audit_myb_vs_cube.py shows `processed` behaves as REFINERY output (copper
   median ratio 1.000 against the refinery tables, 0.957 against the smelter tables, and where a
   country-year has both the cube is closer to refinery 71% of the time). Chile's 2013 smelter
   output is 1.36 Mt against a cube 2.75 Mt, which is its REFINED output. So smelter is emitted as
   `stage='smelter'`, a new value. Nothing is lost: consumers filter on the stage they want, and
   `schema.py` declares no closed vocabulary.

2. THE SELENIUM-TELLURIUM CHAPTER IS SPLIT BY ITS UNIT. One chapter covers two materials, and the
   cube holds them separately. The caption says which: "Kilograms, selenium content" against
   "Kilograms, tellurium content". That is a reading of the source, not an allocation.

3. THE AMBIGUOUS STAGES STAY OUT. The generic "WORLD PRODUCTION" tables (27,509 rows, 53
   commodities) do not say which stage they count - for some commodities it is mine output, for
   others refined metal - and `capacity` is not output at all. Guessing would put a number in the
   cube whose meaning nobody could recover, so both are excluded by name here rather than mapped
   to `unspecified`, where they would look like observations.

Usage:  python build_cube_myb.py          (standalone: prints what it would contribute)
"""
import os
import sys

MYB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'pipeline', 'data', 'usgs_myb_production.parquet')

# Yearbook chapter slug -> cube material. Only confident mappings; anything else is reported.
# platinum-group and zirconium-hafnium are deliberately absent: the cube holds platinum,
# palladium and rhodium separately, and zirconium and hafnium separately, so a group total cannot
# be assigned to one of them.
MATERIAL = {
    'copper': 'copper', 'lead': 'lead', 'zinc': 'zinc', 'tin': 'tin', 'cobalt': 'cobalt',
    'indium': 'indium', 'bismuth': 'bismuth', 'cadmium': 'cadmium', 'nickel': 'nickel',
    'antimony': 'antimony', 'molybdenum': 'molybdenum', 'silver': 'silver', 'gold': 'gold',
    'lithium': 'lithium', 'mercury': 'mercury', 'niobium': 'niobium', 'tantalum': 'tantalum',
    'titanium': 'titanium', 'zirconium': 'zirconium', 'fluorspar': 'fluorspar',
    'boron': 'boron', 'bromine': 'bromine', 'gypsum': 'gypsum', 'kyanite': 'kyanite',
    'rare-earths': 'rare_earths',
}
STAGE = {'refinery': 'processed', 'smelter': 'smelter', 'mine': 'mine'}
SOURCE = 'USGS Minerals Yearbook'


def _split_selenium_tellurium(df):
    """The one chapter covering two materials, separated by the content word in its unit."""
    sel = df.unit.str.contains('selenium', case=False, na=False)
    tel = df.unit.str.contains('tellurium', case=False, na=False)
    df.loc[sel, 'material'] = 'selenium'
    df.loc[tel, 'material'] = 'tellurium'
    return df


def build():
    import pandas as pd
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline'))
    import parse_usgs_mcs as M

    if not os.path.exists(MYB):
        print('  MYB ingest skipped: %s not built yet' % os.path.basename(MYB))
        return []
    d = pd.read_parquet(MYB)

    d = d[d.stage.isin(STAGE) & d.value_t.notna() & (d.value_t > 0)].copy()
    d['material'] = d.commodity.map(MATERIAL)
    d = _split_selenium_tellurium(d)
    unmapped = sorted(set(d.loc[d.material.isna(), 'commodity']))
    d = d.dropna(subset=['material'])

    m = M.iso3_map()
    # A country row resolves to its ISO3; the printed world total is the cube's WLD.
    d['country_iso3'] = [
        'WLD' if k == 'grand_total' else M.to_iso3(c or '', m)
        for k, c in zip(d.kind, d.country)]
    d = d[d.kind.isin(('country', 'country_total', 'grand_total'))]
    unresolved = sorted(set(d.loc[d.country_iso3.isna(), 'country'].dropna()))
    d = d.dropna(subset=['country_iso3'])

    # The same country-year is printed by several editions, five years to a table. The latest
    # edition wins, which is the revision rule usgs_mcs_cube.py already applies to the MCS.
    d = (d.sort_values('edition')
          .groupby(['material', 'country_iso3', 'year', 'stage'], as_index=False).last())

    out = []
    for r in d.itertuples(index=False):
        out.append({
            'material': r.material, 'source_group': 'USGS MYB %d' % r.edition,
            'country_iso3': r.country_iso3, 'year': int(r.year),
            'measure_family': 'production', 'measure': 'production',
            'flow_direction': None, 'stage': STAGE[r.stage],
            'code_system': 'USGS Minerals Yearbook vol. I', 'native_code': str(r.table),
            'native_label': r.subject[:180], 'sub_commodity': None,
            'value': float(r.value), 'unit': r.unit,
            'value_t': float(r.value_t), 'conversion_factor': None,
            'basis': 'content' if 'content' in (r.unit or '').lower() else 'gross',
            'source': SOURCE,
            'series_id': 'USGS MYB:%s:%s:%s' % (r.material, r.stage, r.country_iso3),
            'precision': None,
            'value_flag': 'estimated_by_source' if 'e' in (r.markers or '').split(', ') else None,
        })
    if unmapped:
        print('  MYB: chapters with no cube material (%d): %s'
              % (len(unmapped), ', '.join(unmapped[:8])))
    if unresolved:
        print('  MYB: country names unresolved (%d): %s'
              % (len(unresolved), ', '.join(unresolved[:6])))
    print('  MYB: %d rows, %d materials, stages %s'
          % (len(out), d.material.nunique(), sorted(set(STAGE[s] for s in d.stage))))
    return out


if __name__ == '__main__':
    import pandas as pd
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    df = pd.DataFrame(build())
    if df.empty:
        print('no rows')
        raise SystemExit
    print()
    print('%s rows | %d materials | %d geographies | years %d-%d'
          % (format(len(df), ','), df.material.nunique(), df.country_iso3.nunique(),
             df.year.min(), df.year.max()))
    print('by stage: %s' % df.stage.value_counts().to_dict())
    print()
    print('%-14s %-11s %6s  %s' % ('material', 'stage', 'rows', 'countries'))
    for (mat, st), g in df.groupby(['material', 'stage']):
        print('%-14s %-11s %6d  %d' % (mat, st, len(g), g.country_iso3.nunique()))
