#!/usr/bin/env python3
"""THE HARMONIZED CUBE — one long fact table behind every analysis.

Why this exists (the observation that prompted it): the atlas had grown a *page-oriented* data
layout — 107 per-analysis JSON files in out/, each with its own vocabulary — plus a trade-only
parquet store in pipeline/data/. Production, trade and reserves could not be queried together
without going through a page. That makes every analysis look like a separate project.

This builder inverts it: sources land in ONE tidy long table

    material | country_iso3 | year | measure | stage | value | unit | value_t | basis | source

so an analysis becomes a *query* (a branch), not a silo. Concentration, apparent consumption and
the production panel are then three questions asked of the same table, not three pipelines.

v1 spine = the BGS World Mineral Statistics panel (410k records, 1970-2024, production + imports +
exports, one vocabulary already). BACI trade and USGS/WMD shares are the next ingests — the schema
below is deliberately source-agnostic so they slot in without changing consumers.

Run:  python build_cube.py        ->  pipeline/data/cube.parquet + out/cube_summary.json
"""
import os, sys, json, glob
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(ROOT, 'raw', 'bgs', 'panel')

# ── material vocabulary ────────────────────────────────────────────────────────────────────────
# BGS erml_group (the panel filename) -> the atlas's canonical label. Groups with no atlas material
# are KEPT (they are the control group and the drivers) and simply carry their own name.
GROUP_TO_MATERIAL = {
    'bauxite__alumina_and_aluminium': 'bauxite', 'barytes': 'baryte', 'borates': 'boron',
    'phosphate_rock': 'phosphate', 'tantalum_and_niobium': 'tantalum',
    'platinum_group_metals': 'platinum', 'iron_and_steel': 'iron', 'magnesite': 'magnesium',
    'sillimanite_and_related_minerals': 'sillimanite', 'bentonite_and_fuller_s_earth': 'bentonite',
    'aggregates_and_related_materials': 'aggregates',
}
ATLAS = set()
try:
    ATLAS = {m['label'] for m in json.load(
        open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))['materials']}
except Exception:
    pass

# ── stage classification ───────────────────────────────────────────────────────────────────────
# BGS encodes the stage in the commodity name ("copper, refined", "iron ore", "germanium metal").
# Stage is a property of the FORM, so it applies to trade rows too (what form crossed the border).
MINE = ('ore', 'mine', 'concentrate', 'bauxite', 'rough', 'crude', 'run of mine')
PROC = ('refined', 'metal', 'smelter', 'alumina', 'oxide', 'ferro', 'unwrought', 'slab',
        'primary', 'secondary', 'sponge', 'pigment', 'chemical', 'compound', 'salt', 'sulphate',
        'carbonate', 'hydroxide', '白')  # last is a guard against odd encodings, harmless


def stage_of(commodity, sub):
    s = f"{commodity or ''} {sub or ''}".lower()
    if any(k in s for k in MINE):
        return 'mine'
    if any(k in s for k in PROC):
        return 'processed'
    return 'unspecified'


# ── unit harmonization ─────────────────────────────────────────────────────────────────────────
# value_t = tonnes where the unit is convertible; basis says whether that tonnage is gross weight
# or contained metal. Non-mass units (carats, cubic metres) keep value only — never silently
# coerced, because a carat is not a tonne.
UNITS = {
    'tonnes (metric)':          (1.0,   'gross'),
    'tonnes':                   (1.0,   'gross'),
    'kilograms':                (0.001, 'gross'),
    'tonnes (metal content)':   (1.0,   'content'),
    'kilograms (metal content)': (0.001, 'content'),
    'tonnes (Al2O3 content)':   (1.0,   'content'),
    'tonnes (K2O content)':     (1.0,   'content'),
    'tonnes (P2O5 content)':    (1.0,   'content'),
    'tonnes (contained)':       (1.0,   'content'),
}
MEASURE = {'Production': 'production', 'Imports': 'imports', 'Exports': 'exports'}


def build():
    rows = []
    files = [f for f in sorted(glob.glob(os.path.join(PANEL, '*.json')))
             if 'pairing' not in os.path.basename(f) and not os.path.basename(f).startswith('_summary')]
    for fn in files:
        group = os.path.basename(fn)[:-5]
        if group.startswith('_'):
            continue
        material = GROUP_TO_MATERIAL.get(group, group)
        try:
            recs = json.load(open(fn, encoding='utf-8'))
        except Exception as e:
            print(f'  skip {group}: {e}')
            continue
        for r in recs:
            iso = r.get('country_iso3_code')
            q = r.get('quantity')
            yr = (r.get('year') or '')[:4]
            meas = MEASURE.get(r.get('bgs_statistic_type_trans'))
            if not iso or not yr.isdigit() or meas is None or q in (None, ''):
                continue
            try:
                q = float(q)
            except (TypeError, ValueError):
                continue
            unit = r.get('units') or ''
            factor, basis = UNITS.get(unit, (None, None))
            commodity = r.get('bgs_commodity_trans')
            sub = r.get('bgs_sub_commodity_trans')
            rows.append((
                material, group, iso, int(yr), meas,
                stage_of(commodity, sub), commodity, sub,
                q, unit, (q * factor) if factor else None, basis,
                'BGS World Mineral Statistics', r.get('data_precision_description'),
            ))
    df = pd.DataFrame(rows, columns=[
        'material', 'source_group', 'country_iso3', 'year', 'measure', 'stage',
        'commodity', 'sub_commodity', 'value', 'unit', 'value_t', 'basis',
        'source', 'precision'])
    # in_atlas marks the 32 headline materials; the rest are controls/drivers, kept on purpose
    df['in_atlas'] = df['material'].isin(ATLAS)
    return df.sort_values(['material', 'measure', 'year', 'country_iso3']).reset_index(drop=True)


if __name__ == '__main__':
    df = build()
    outdir = os.path.join(ROOT, 'pipeline', 'data')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'cube.parquet')
    df.to_parquet(path, index=False, compression='zstd')

    summary = {
        'note': 'Harmonized long fact table. One row = one (material, country, year, measure, form). '
                'Analyses are queries against this, not separate pipelines. v1 spine = BGS World '
                'Mineral Statistics; BACI trade and USGS/WMD are the next ingests.',
        'rows': int(len(df)),
        'materials': int(df['material'].nunique()),
        'materials_in_atlas': int(df.loc[df['in_atlas'], 'material'].nunique()),
        'countries': int(df['country_iso3'].nunique()),
        'year_min': int(df['year'].min()), 'year_max': int(df['year'].max()),
        'by_measure': {k: int(v) for k, v in df['measure'].value_counts().items()},
        'by_stage': {k: int(v) for k, v in df['stage'].value_counts().items()},
        'tonnage_convertible_pct': round(100 * df['value_t'].notna().mean(), 1),
        'sources': sorted(df['source'].unique().tolist()),
    }
    json.dump(summary, open(os.path.join(ROOT, 'out', 'cube_summary.json'), 'w', encoding='utf-8'),
              indent=1)

    mb = os.path.getsize(path) / 1e6
    print(f'WROTE pipeline/data/cube.parquet — {len(df):,} rows, {mb:.1f} MB')
    print(f'  {summary["materials"]} materials ({summary["materials_in_atlas"]} atlas), '
          f'{summary["countries"]} countries, {summary["year_min"]}–{summary["year_max"]}')
    print(f'  measures: {summary["by_measure"]}')
    print(f'  stages:   {summary["by_stage"]}')
    print(f'  tonnage-convertible: {summary["tonnage_convertible_pct"]}%')
