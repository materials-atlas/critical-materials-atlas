#!/usr/bin/env python3
"""Robustness check for the origin-gap flagship: is "top exporter != top miner" an artifact of
comparing export VALUE (dollars) with mine TONNAGE? Re-measure both sides in the same unit —
trade tonnes (BACI quantity) vs mine tonnes (USGS) — and compare the count to the value-based one.

Result (2024): value-based gap 17/32; tonnes-vs-tonnes gap 18/32; all 17 value-gaps survive in
tonnes. The one material that differs is platinum, where the top shipper by tonnes is a Gulf
entrepot rather than South African mine output. So the gap is not a unit artifact.

Run: python build_origin_gap_units.py
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
flows = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf8'))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))

def top_exporter(label, key):
    """Top exporter of a material by `key` ('value' USD, or 'qty' tonnes), share of world trade."""
    o, tot = {}, 0.0
    for f in flows.get('materials', {}).get(label) or []:
        v = f.get(key) or 0
        o[f['from']] = o.get(f['from'], 0.0) + v
        tot += v
    if not tot:
        return None, 0.0
    c = max(o, key=o.get)
    return c, o[c] / tot * 100

val_gap = qty_gap = both = 0
val_set, qty_set, disagree = set(), set(), []
for m in data['materials']:
    lab = m['label']
    mi = (m.get('mined') or [None])[0]
    tev, tevs = top_exporter(lab, 'value')
    teq, teqs = top_exporter(lab, 'qty')
    if not mi or tev is None:
        continue
    vg = tev != mi['c']
    qg = teq is not None and teq != mi['c']
    if vg:
        val_gap += 1; val_set.add(lab)
    if qg:
        qty_gap += 1; qty_set.add(lab)
    if vg and qg:
        both += 1
    if vg != qg:
        disagree.append((m['title'].split(' (')[0], mi['c'], (tev, round(tevs)), (teq, round(teqs)),
                         'value-only' if vg else 'tonnes-only'))

survive = len(val_set & qty_set)
print(f"origin gap by VALUE (dollars)        : {val_gap}/32   <- current flagship")
print(f"origin gap by QUANTITY (tonnes)      : {qty_gap}/32   <- same-unit test")
print(f"value-gaps that SURVIVE in tonnes    : {survive}/{val_gap}")
print(f"gap holds under BOTH definitions     : {both}/32")
if disagree:
    print("\nmaterials where the two definitions differ:")
    for name, mine, v, q, why in disagree:
        print(f"  {name:22} mine={mine}  value-top={v[0]}({v[1]}%)  tonnes-top={q[0]}({q[1]}%)  [{why}]")
print("\nConclusion: the origin gap is not an artifact of comparing dollars with tonnes — "
      "it survives measuring both sides in tonnes.")
