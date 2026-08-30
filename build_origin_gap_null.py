#!/usr/bin/env python3
"""Null test for the origin-gap headline (author-run adversarial check; logged in the changelog).
A hostile reviewer asked: is '17 of 32 materials have top exporter != top miner' more than chance?
Permutation test: draw each material's top exporter INDEPENDENTLY of its miner, weighted by that
material's own export shares, and count mismatches over 10,000 draws.

Result: under independence you'd expect ~24/32 mismatches (with dozens of exporters, a random top
exporter rarely equals the top miner). We observe 17 — 3.3 sd BELOW that, p~=0.001. So the honest
reading is not 'mismatch is surprisingly common' but the opposite: mining and exporting are
significantly CORRELATED (a miner usually exports its own material), and the 17 gaps are the real,
non-random minority where processing relocated.

Run: python build_origin_gap_null.py
"""
import os, json, random, statistics

ROOT = os.path.dirname(os.path.abspath(__file__))
random.seed(1)
flows = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf8'))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))

def top_and_shares(lab):
    o, t = {}, 0.0
    for f in flows.get('materials', {}).get(lab) or []:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; t += f['value']
    if not t:
        return None, {}
    return max(o, key=o.get), {c: v / t for c, v in o.items()}

mats = []
for m in data['materials']:
    mi = (m.get('mined') or [None])[0]
    te, sh = top_and_shares(m['label'])
    if mi and te:
        mats.append((mi['c'], te, sh))

N = len(mats)
observed = sum(1 for mine, te, _ in mats if te != mine)

def draw():
    mm = 0
    for mine, te, sh in mats:
        r, cum, pick = random.random(), 0.0, te
        for c, s in sh.items():
            cum += s
            if r <= cum:
                pick = c; break
        if pick != mine:
            mm += 1
    return mm

null = [draw() for _ in range(10000)]
mean, sd = statistics.mean(null), statistics.pstdev(null)
p = sum(1 for x in null if x <= observed) / len(null)
print(f"observed mismatches (top exporter != top miner) : {observed}/{N}")
print(f"expected under independence                      : {mean:.1f} (sd {sd:.1f})")
print(f"observed is {(observed - mean) / sd:+.1f} sd from the independence null | P(chance <= {observed}) = {p:.4f}")
print("\nConclusion: significant (p~=0.001), but in the direction of FEWER mismatches than chance — "
      "mining and exporting are correlated; the gap is a real, identifiable minority, not an inflated count.")
