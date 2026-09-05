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


def value_flag(precision):
    """BGS ships no 'estimated' marker, but it does distinguish a reported NIL (the country
    produced nothing - real information) from a trace rounded below 0.5 t, and both differ from a
    missing row. Keep them as flags rather than letting a true zero look like an absence."""
    p = (precision or '').lower()
    if 'nil' in p:
        return 'nil'
    if 'less than' in p:
        return 'trace'
    return None


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

# When the spine was pulled. Kept per row so a later re-pull is distinguishable from this vintage.
try:
    import datetime as _dt
    RETRIEVED = _dt.date.fromtimestamp(
        os.path.getmtime(os.path.join(PANEL, 'copper.json'))).isoformat()
except Exception:
    RETRIEVED = None


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
            code = r.get('bgs_commodity_code')
            rows.append((
                material, group, iso, int(yr),
                'trade' if meas in ('imports', 'exports') else 'production',   # measure_family
                meas,
                {'imports': 'in', 'exports': 'out'}.get(meas),                 # flow_direction
                stage_of(commodity, sub),
                'BGS commodity', code, commodity, sub,                         # native identity
                q, unit, (q * factor) if factor else None, factor, basis,
                'BGS World Mineral Statistics',
                f'BGS:{code}:{meas}',                                          # series_id
                r.get('data_precision_description'), value_flag(r.get('data_precision_description')),
            ))
    df = pd.DataFrame(rows, columns=[
        'material', 'source_group', 'country_iso3', 'year',
        'measure_family', 'measure', 'flow_direction', 'stage',
        'code_system', 'native_code', 'native_label', 'sub_commodity',
        'value', 'unit', 'value_t', 'conversion_factor', 'basis',
        'source', 'series_id', 'precision', 'value_flag'])
    # value_t is only meaningful alongside its factor and basis - enforce, do not trust discipline
    bad = df.value_t.notna() & (df.conversion_factor.isna() | df.basis.isna())
    if bad.any():
        raise SystemExit(f'{bad.sum()} rows carry value_t without factor/basis - refusing to write')
    # in_atlas marks the 32 headline materials; the rest are controls/drivers, kept on purpose
    df['in_atlas'] = df['material'].isin(ATLAS)
    df['retrieved_at'] = RETRIEVED

    # ── second ingest: USGS Historical Statistics (DS 140) ────────────────────────────────────
    # Adds 1900-2023 depth and, in 66 workbooks, a WORLD production column the BGS spine has no
    # equivalent for. Same schema, so nothing downstream changes.
    try:
        import build_cube_usgs
        u = pd.DataFrame(build_cube_usgs.build())
        if len(u):
            u['in_atlas'] = u['material'].isin(ATLAS)
            u['retrieved_at'] = None
            df = pd.concat([df, u], ignore_index=True, sort=False)
    except Exception as e:
        print(f'  USGS historical ingest skipped: {e}')

    # a code is an identifier, never a quantity - keep it textual so sources with alphanumeric
    # codes and sources with numeric ones can share the column
    df['native_code'] = df['native_code'].astype('string')
    return df.sort_values(['source', 'material', 'measure', 'year', 'country_iso3']).reset_index(drop=True)


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
        'sources': {k: int(v) for k, v in df['source'].value_counts().items()},
        'year_span_by_source': {str(k): [int(g.year.min()), int(g.year.max())]
                                for k, g in df.groupby('source')},
        'geographies': int(df['country_iso3'].nunique()),
        'world_rows': int((df['country_iso3'] == 'WLD').sum()),
        'by_measure_family': {k: int(v) for k, v in df['measure_family'].value_counts().items()},
        'series': int(df['series_id'].nunique()),
        'value_flags': {k: int(v) for k, v in df['value_flag'].value_counts().items()},
        'retrieved_at': RETRIEVED,
        'join_rule': 'NEVER join on material alone. The identity of an observation is '
                     '(code_system, native_code, measure, stage, basis, unit). material is a '
                     'convenience label mapped from source_group, not a key.',
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
