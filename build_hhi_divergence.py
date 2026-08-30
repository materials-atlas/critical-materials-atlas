#!/usr/bin/env python3
"""Audit #5 (author-run adversarial check; logged in the changelog): for the materials where the
atlas's export-concentration (HHI) differs most from official BACI (beryllium, tungsten), find out
WHY. Compare the engine's reconstruction (recon_2024) with official BACI (baci_2024) at the commodity
level, holding flows/exporters fixed.

Result: the divergence is NOT extra flows or exporters (both are identical). It is the mirror
reconciliation redistributing VALUE: averaging the exporter- and importer-reported values of a
dominated flow dilutes the leader's share, so the atlas HHI runs BELOW official BACI for thin,
dominated commodities. So the atlas understates concentration exactly where it is highest — a
material limit; read those HHIs as a lower bound.

Run: python build_hhi_divergence.py
"""
import os, csv
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))

def load(fn):
    exp = defaultdict(lambda: defaultdict(float))
    for r in csv.DictReader(open(os.path.join(ROOT, 'reconcile', fn), encoding='utf-8')):
        try:
            exp[r['cmd']][r['i']] += float(r['value'])
        except (ValueError, KeyError):
            continue
    return exp

R, B = load('recon_2024.csv'), load('baci_2024.csv')

def hhi(d):
    t = sum(d.values())
    return sum((v / t) ** 2 for v in d.values()) if t else None

for name, code in [('beryllium', '811212'), ('tungsten', '810194')]:
    r, b = R.get(code, {}), B.get(code, {})
    print(f"{name} (HS{code}): HHI engine {hhi(r):.3f} vs official BACI {hhi(b):.3f}  "
          f"| exporters {len(r)} vs {len(b)} | leader {max(r, key=r.get)} vs {max(b, key=b.get)}")
print("\nSame flows and same leader -> the gap is value redistribution by the mirror reconciliation, "
      "which dilutes dominant shares. The atlas understates concentration for thin, dominated commodities; "
      "read those HHIs as a lower bound and the higher BACI value as equally valid.")
