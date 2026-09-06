# -*- coding: utf-8 -*-
"""Material attributes as a joinable dimension of the cube.

WHY THIS EXISTS
The cube is a fact table: every row is one material, one country, one year, one quantity.
A large class of published figures does not fit that grain at all - an end-of-life recycling
rate, a substitutability class, a companionality percentage. They have no country and no year.
Until now they lived in whatever page happened to need them, which meant "concentration by
recycling rate" was not a query, it was a new script.

They do not have to stay outside. A figure that DESCRIBES a material is a dimension OF the
material, and a dimension joins. This writes them as one tidy table keyed on the atlas material
label, so any cube query can group, filter or sort by them.

THE GOLDEN RULE, AND WHY THIS IS NOT A BREACH
"Never join facts on material alone" - because a fact also carries stage, basis, unit and code
system, and joining on the label alone silently mixes ore with metal. That rule protects FACTS.
An attribute is defined at material grain by construction: cobalt has one EOL-RIR, not one per
stage. So the join key IS the whole key. The guard is uniqueness, asserted below: one row per
(material, attribute), so a join can never fan out a cube row.

Two tables, because two grains:
  dim_material.parquet                 material x attribute        -> joins to the cube on material
  assessment_material_country.parquet  material x country x stage  -> a published SHARE with no
                                                                      year; comparable to one of
                                                                      ours, never summable with a
                                                                      quantity

Run:  python build_cube_dim.py
"""
import json, os, datetime
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'out')
DATA = os.path.join(ROOT, 'pipeline', 'data')
TODAY = datetime.date.today().isoformat()


def load(name):
    with open(os.path.join(OUT, name), encoding='utf-8') as f:
        return json.load(f)


rows = []


def add(material, attribute, num=None, txt=None, unit=None, source=None, vintage=None, note=None):
    """One attribute of one material. Skipped silently when the source has no value for it."""
    if num is None and txt is None:
        return
    if num is not None:
        try:
            num = float(num)
        except (TypeError, ValueError):
            # a censored or qualified figure (">50%") is not a number and must not be coerced
            # into one; it is kept verbatim as text so nothing downstream can average it.
            txt, num = str(num), None
    rows.append({'material': material, 'attribute': attribute,
                 'value_num': num,
                 'value_str': None if txt is None else str(txt),
                 'unit': unit, 'scope': 'material', 'source': source,
                 'vintage': vintage, 'note': note, 'retrieved_at': TODAY})


# -- EU CRM 2023 --------------------------------------------------------------
# The mitigant indicators the assessment publishes per material. They reach us through
# data.json because the profile pages consumed them first; the source is the EU CRM 2023
# final report and is recorded as such.
EUCRM = 'EU CRM 2023 (EC, DOI 10.2873/725585)'
d = load('data.json')['materials']
d = list(d.values()) if isinstance(d, dict) else d
for m in d:
    lab = m['label']
    add(lab, 'eol_rir', num=m.get('recycling'), unit='pct', source=EUCRM, vintage=2023,
        note='end-of-life recycling input rate: share of supply met by recycled end-of-life scrap')
    add(lab, 'substitutability', txt=m.get('substitutability'), source=EUCRM, vintage=2023,
        note='difficulty of substituting the material in its main uses')
    add(lab, 'reserve_life_years', num=m.get('reserve_life'), unit='years',
        source='USGS MCS (reserves / mine production)', vintage=2025)
    add(lab, 'net_import_reliance', num=m.get('net_import_reliance'), unit='pct',
        source='USGS MCS', vintage=2025,
        note='US net import reliance, as published - some are censored (">50%") and stay text')
    if m.get('export_control'):
        add(lab, 'export_control', txt=m['export_control'], source='atlas policy ledger',
            vintage=2025, note='named export-control or licensing regime in force')
    add(lab, 'in_atlas_32', txt='yes', source='atlas scope', vintage=2026)

# -- companionality (USGS / Nassar) -------------------------------------------
NASSAR = 'USGS / Nassar et al. 2015, atlas classification'
for r in load('companionality.json')['rows']:
    add(r['label'], 'companionality', num=r.get('companionality_pct'), unit='pct',
        source=NASSAR, vintage=2015,
        note='share of supply arising as a by-product of another metal')
    add(r['label'], 'companionality_class', txt=r.get('class'), source=NASSAR, vintage=2015)
    if r.get('hosts'):
        add(r['label'], 'host_metals', txt=', '.join(r['hosts']), source=NASSAR, vintage=2015,
            note='the metals it is recovered from')

# -- EU CRM 2011, the ex-ante freeze the concentration finding uses ------------
# NOTE ON VOCABULARY: build_bgs_concentration.py works in BGS labels, where the platinum-group
# metals are one series, `platinum_group_metals`. The cube splits them into `platinum` and
# `palladium`. The 2011 EU list names the group, so the attribute lands on both members and says
# so - the uniqueness guard below is what surfaced the mismatch in the first place.
EU_CRM_2011 = {'antimony': None, 'cobalt': None, 'fluorspar': None, 'graphite': None,
               'rare_earths': None, 'tungsten': None,
               'platinum': 'listed as platinum-group metals, one entry covering the group',
               'palladium': 'listed as platinum-group metals, one entry covering the group'}
for lab, extra in EU_CRM_2011.items():
    add(lab, 'eu_crm_2011', txt='yes', source='EU CRM 2011 (first EU list)', vintage=2011,
        note='on the first EU critical list - the ex-ante set, fixed before the period measured'
             + ('; ' + extra if extra else ''))

# -- data quality, which is also an attribute of the material -----------------
for r in load('pairing.json')['rows']:
    add(r['material'], 'census_plausible', txt='yes' if r.get('census_plausible') else 'no',
        source='atlas / BGS reporter census', vintage=2024,
        note='BGS reporter count >= 8, so a BGS world sum is a plausible census not a partial count')
    add(r['material'], 'bgs_reporters_median', num=r.get('bgs_reporters_median'),
        unit='countries', source='atlas / BGS', vintage=2024)
    add(r['material'], 'bgs_usgs_status', txt=r.get('status'), source='atlas pairing', vintage=2024,
        note='how the two independent compilations compare for this material')

dim = pd.DataFrame(rows)

# -- the guard that makes the join safe ---------------------------------------
dup = dim.duplicated(subset=['material', 'attribute'], keep=False)
if dup.any():
    bad = dim[dup][['material', 'attribute', 'source']].to_string()
    raise SystemExit('DIMENSION IS NOT UNIQUE - a join on material would fan out cube rows:\n' + bad)

# every material must exist in the cube, or the dimension describes something unqueryable
cube_materials = set(pd.read_parquet(os.path.join(DATA, 'cube.parquet'))['material'].unique())
orphan = sorted(set(dim['material']) - cube_materials)
if orphan:
    raise SystemExit('attributes for materials absent from the cube: ' + ', '.join(orphan))

os.makedirs(DATA, exist_ok=True)
dim.to_parquet(os.path.join(DATA, 'dim_material.parquet'), index=False)

# -- second grain: a published share, material x country, no year -------------
eu = load('eucrm.json')
arows = [{'material': lab, 'country_iso2': v.get('iso'), 'country_name': v.get('name'),
          'stage': v.get('stage'), 'measure': 'major_supplier_share', 'value': v.get('pct'),
          'unit': 'pct', 'basis': 'assessment', 'vintage': 2023, 'source': EUCRM,
          'note': 'the EU assessment names one major global supplier and the stage it dominates',
          'retrieved_at': TODAY}
         for lab, v in eu['materials'].items()]
assess = pd.DataFrame(arows)
assess.to_parquet(os.path.join(DATA, 'assessment_material_country.parquet'), index=False)

summary = {
    'generated': TODAY,
    'rule': ('A figure that describes a material is a dimension of the material. It joins on '
             'material alone - safe precisely because it is defined at material grain, unlike a '
             'fact. Uniqueness on (material, attribute) is asserted at build time.'),
    'dim_material': {
        'rows': int(len(dim)), 'materials': int(dim['material'].nunique()),
        'attributes': int(dim['attribute'].nunique()),
        'by_attribute': {k: int(v) for k, v in dim.groupby('attribute').size().items()},
        'by_source': {k: int(v) for k, v in dim.groupby('source').size().items()},
    },
    'assessment_material_country': {
        'rows': int(len(assess)), 'materials': int(assess['material'].nunique()),
        'note': 'a share, not a quantity - comparable to a computed share, never summable with one',
    },
}
with open(os.path.join(OUT, 'dim_material.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=1, ensure_ascii=False)

print('dim_material.parquet: %d rows, %d materials, %d attributes'
      % (len(dim), dim['material'].nunique(), dim['attribute'].nunique()))
for a, n in sorted(dim.groupby('attribute').size().items(), key=lambda x: -x[1]):
    print('   %-24s %d' % (a, n))
print('assessment_material_country.parquet: %d rows' % len(assess))
