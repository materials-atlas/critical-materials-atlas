# -*- coding: utf-8 -*-
"""Add a `qty` (metric tonnes) field to each edge in out/flows_2024.json, from BACI 2024's quantity column.
Values are LEFT UNTOUCHED — we only attach tonnage to the edges already there, keyed by (material, from, to),
using the SAME code->material mapping the atlas build uses (HS6 from each material's data.json title).
Reads BACI from stdin (stream `unzip -p ... BACI_HS17_Y2024_V202601.csv`)."""
import sys, json, csv, os, re, collections

ROOT = r$PSScriptRoot
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))

# code2labels: HS6 -> [material labels]  (mirror of build_flows_years.ps1)
code2labels = collections.defaultdict(list)
for m in data['materials']:
    mm = re.search(r'\(([^)]*)\)', m['title'])
    digits = re.sub(r'\D', '', mm.group(1)) if mm else ''
    if len(digits) >= 6:
        code2labels[digits[:6]].append(m['label'])
# hafnium HS2022 code 811231 did not exist pre-HS2022 -> folds into 811292 (HS17)
if '811231' in code2labels:
    code2labels['811292'].extend(code2labels.pop('811231'))
tracked = set(code2labels)

# BACI numeric country code -> ISO2
num2iso = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'), encoding='utf8')):
    if r.get('country_iso2') and r['country_iso2'] != 'NA':
        num2iso[r['country_code']] = r['country_iso2']

# stream BACI: sum tonnes per (label, from_iso2, to_iso2)
qty = collections.defaultdict(float)
sys.stdin.readline()  # header t,i,j,k,v,q
n = kept = 0
for line in sys.stdin:
    n += 1
    p = line.rstrip('\n').split(',')
    if len(p) < 6:
        continue
    k = p[3]
    if k not in tracked:
        continue
    frm = num2iso.get(p[1]); to = num2iso.get(p[2])
    if not frm or not to or frm == to:
        continue
    q = p[5]
    if not q or q == 'NA':
        continue
    try:
        t = float(q)  # BACI q is already in metric tonnes
    except ValueError:
        continue
    if t <= 0:
        continue
    for lab in code2labels[k]:
        qty[(lab, frm, to)] += t
        kept += 1
print(f"  scanned {n:,} BACI rows, {kept:,} tracked qty contributions across {len(set(x[0] for x in qty))} materials")

# attach qty to each existing edge (value untouched)
fp = os.path.join(ROOT, 'out', 'flows_2024.json')
fj = json.load(open(fp, encoding='utf8'))
attached = missing = 0
for lab, edges in fj['materials'].items():
    for e in edges:
        t = qty.get((lab, e['from'], e['to']))
        if t is not None:
            e['qty'] = round(t)
            attached += 1
        else:
            missing += 1
json.dump(fj, open(fp, 'w', encoding='utf8'), separators=(',', ':'), ensure_ascii=False)
print(f"  attached tonnes to {attached} edges, {missing} had no BACI quantity (left without qty)")
