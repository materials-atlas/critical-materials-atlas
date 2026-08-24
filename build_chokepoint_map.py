"""Derive chokepoint_map.json from the chain records — single source of truth.

Every chain record carries a `chokepoint` object (its binding stage, mechanism, physics, holder,
share, export-control, conf). This script reads all of them and writes one chokepoint_map.json that
the Chokepoint Map page renders from — so the classification and every tally live in the records, in
one place, and can never drift from the per-chain pages. Run from repo root: python build_chokepoint_map.py
"""
from __future__ import annotations
import json, os, glob

ROOT = os.path.dirname(os.path.abspath(__file__))

# silicon-chip is a bespoke page (not on the shared chainview schema), so its row is defined here —
# the one documented exception. Everything else is read from the chain records.
BESPOKE = [
    {"chain": "silicon-chip", "href": "silicon-chip/silicon-chain.html", "product": "Logic chips",
     "stage": "Fab / EUV", "mechanism": "capability",
     "physics": "Batch lithography; barrier is decades of process know-how + a single EUV supplier",
     "holder": "TW · US · JP · NL", "share": "—", "control": "US↔China", "conf": "measured"},
]


def derive():
    """Read every chain record's chokepoint field (+ the bespoke silicon-chip row) and return the map
    structure. This is the single source of truth; both build() and check.py's guard call it."""
    rows = list(BESPOKE)
    for d in sorted(glob.glob(os.path.join(ROOT, "*-chain"))):
        slug = os.path.basename(d)[:-6]  # strip trailing "-chain"
        js = glob.glob(os.path.join(d, "out", "*_chain.json"))
        if not js:
            continue
        data = json.load(open(js[0], encoding="utf-8"))
        ck = data.get("chokepoint")
        if not ck:
            print("  WARNING: no chokepoint in", slug)
            continue
        row = {"chain": slug, "href": "%s-chain/%s-chain.html" % (slug, slug)}
        row.update({k: ck.get(k, "—") for k in ("product", "stage", "mechanism", "physics", "holder", "share", "control", "conf")})
        rows.append(row)
    rows.sort(key=lambda r: r["chain"])
    return {"source": "derived from the chain records' chokepoint fields", "count": len(rows), "rows": rows}


def build():
    out = derive()
    path = os.path.join(ROOT, "chokepoint_map.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    # tallies, for the log
    from collections import Counter
    c = Counter(r["mechanism"] for r in out["rows"])
    geo = c.get("geological", 0)
    print("wrote chokepoint_map.json —", out["count"], "chains |", dict(c), "| geological", geo, "/ made", out["count"] - geo)


if __name__ == "__main__":
    build()
