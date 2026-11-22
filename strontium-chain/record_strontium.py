"""Evidence JSON for the strontium chain pilot. Uniform schema. Public sources.
Ferrite magnets and the red in fireworks. Run: python record_strontium.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "strontium_chain.json")
ROOT = os.path.dirname(HERE)
MINED = os.path.join(ROOT, "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


# 2024 mine shares: the atlas's one table (out/mined_shares.json), never typed here. For strontium
# it is BGS World Mineral Statistics, tonnes of strontium minerals, share of reporting countries -
# the same source and unit as the history series, and the build stops if the two disagree.
_CORE = json.load(open(os.path.join(ROOT, "out", "mined_shares.json"), encoding="utf-8"))["materials"]["strontium"]
if not _CORE["source"].startswith("BGS"):
    raise SystemExit("strontium: the core table changed source; the history series (BGS) no longer matches it")
M = {x["c"]: x["v"] for x in _CORE["mined"]}
IR, CN, ES, MX = M["IR"], M["CN"], M["ES"], M["MX"]
for _c in ("IR", "CN", "ES", "MX"):
    _h = hist_points("strontium", _c)[-1]
    if _h["y"] != 2024 or _h["v"] != M[_c]:
        raise SystemExit(f"strontium {_c}: history says {_h}, out/mined_shares.json says {M[_c]}% for 2024")


SRC = {
    "usgs_strontium": {"title": "USGS Mineral Commodity Summaries 2026 — Strontium", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-strontium.pdf"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — strontium (celestine)", "year": 2024, "url": "https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-data-download/"},
    "iea_magnets": {"title": "IEA / industry — ferrite vs rare-earth permanent magnets", "year": 2024, "url": "https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Strontium chain",
    "chokepoint": {"product": "Ferrite magnets · pyrotechnics", "stage": "Mine (celestite)", "mechanism": "geological", "physics": f"Iran mines {IR}% of world celestite from its own deposits (2024). The mine is the most concentrated stage, though the lead has changed hands since 2000", "holder": "Iran", "share": f"{IR}%", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../magnet-chain/magnet-chain", "label": "Rare-earth magnet chain"}, {"href": "../boron-chain/boron-chain", "label": "Boron chain"}, {"href": "../rare-earths-chain/rare-earths-chain", "label": "Rare earths (full basket)"}],
    "accent": "#8a5a5a",
    "eyebrow": "Product-chain pilot · the cheap magnet's metal",
    "h1": "The cheap magnet's metal — and the red in every firework",
    "deck": "Strontium, mined as the mineral celestite, does two very different jobs. It makes ferrite (ceramic) "
            "magnets — the cheap, rare-earth-free magnets in fridge doors, small motors and loudspeakers — and it "
            "burns bright crimson, which is why it colours fireworks, flares and signal rockets. A small mineral "
            "market, now led by Iran.",
    "byline": "celestite (SrSO4) ≠ strontium carbonate ≠ ferrite magnets · pyrotechnics · specialty glass",
    "correction": "Strontium is a minor mineral with one strategically interesting use: it is the basis of ferrite "
                  "permanent magnets, the non-rare-earth alternative that fills the vast low-performance magnet market "
                  "NdFeB is too expensive for. Mined as celestite, its supply is small and concentrated at the mine: "
                  f"Iran accounted for {IR}% of 2024 production, in a market led by Mexico and Spain around 2000. "
                  "The leverage that gives is low, because the market is small and most uses have substitutes. Its "
                  "quiet importance is as the everyday magnet material and the crimson in pyrotechnics.",
    "stats": [
        {"v": "ferrite magnets", "l": "strontium makes the cheap, rare-earth-free ceramic magnets", "conf": "measured"},
        {"v": f"{IR}% Iran", "l": f"Iran leads celestite mining in 2024 (China {CN}%, Spain {ES}%, Mexico {MX}%), BGS", "conf": "measured"},
        {"v": "crimson flame", "l": "the red in fireworks, flares and signal rockets — plus specialty glass", "conf": "measured"},
        {"v": "the magnet hedge", "l": "ferrite is the fallback where rare-earth magnets are too costly", "conf": "estimate"},
    ],
    "history": {
        "title": "The mine moved to Iran, 2000 → 2024",
        "conf": "measured",
        "note": "BGS World Mineral Statistics: tonnes of strontium minerals, as a share of the countries that "
                "report. Mexico and Spain led around 2000 and China around 2010. Spain and Iran traded the lead "
                f"between 2015 and 2022, and Iran has led since 2023 ({IR}% in 2024). The lead has changed hands "
                "several times in a small market.",
        "series": [
            {"label": "Iran", "points": hist_points("strontium", "IR")},
            {"label": "China", "points": hist_points("strontium", "CN")},
            {"label": "Spain", "points": hist_points("strontium", "ES")},
            {"label": "Mexico", "points": hist_points("strontium", "MX")},
        ],
    },
    "hops": [
        {"n": "1 · Celestite", "t": f"strontium sulfate ore: Iran {IR}%, then China, Spain and Mexico"},
        {"n": "2 · Carbonate", "t": "converted to strontium carbonate, the main traded compound"},
        {"n": "3 · Ferrite / compounds", "t": "strontium ferrite for magnets; strontium salts for flame and glass"},
        {"n": "4 · End use", "t": "ceramic magnets, pyrotechnics, specialty glass and ceramics"},
    ],
    "sections": [
        {"h2": "1 · The everyday magnet material", "panels": [
            {"kind": "big", "h3": "Why ferrite matters", "big": "ferrite magnets", "conf": "measured",
             "text": "Strontium ferrite is the workhorse of the magnet world by volume: cheap, corrosion-resistant and "
                     "using no rare earths, it goes into fridge magnets, loudspeakers, small motors, sensors and toys — "
                     "everywhere a strong magnet is unnecessary. When rare-earth magnet prices or export controls bite "
                     "(see the magnet chain), ferrite is the fallback for lower-performance uses, which gives this "
                     "humble mineral a strategic edge as a substitution hedge.",
             "note": "IEA / industry; USGS."},
            {"kind": "text", "h3": "But it can't replace NdFeB everywhere",
             "text": "Ferrite magnets are far weaker than neodymium ones, so they cannot substitute in the power-dense "
                     "motors of EVs, wind turbines or defence systems that actually drive rare-earth demand. The hedge "
                     "is real but partial: ferrite covers the low end, rare earths the high end. Knowing the split is "
                     "what makes the strontium and magnet chains complementary.",
             "flag": "the low end only"},
        ]},
        {"h2": "2 · The colour of celebration", "panels": [
            {"kind": "text", "h3": "Strontium burns red", "conf": "measured",
             "text": "Heated, strontium salts emit a pure crimson light, making strontium the standard red colourant in "
                     "fireworks, marine flares, railway signal rockets and tracer compositions. It is a small use by "
                     "tonnage but a near-monopoly on the colour — there is no equally good red. A rare case where a "
                     "critical-materials atlas touches something purely festive.",
             "note": "USGS.", "flag": "no equal for red"},
        ]},
        {"h2": "3 · A small, quiet market", "panels": [
            {"kind": "text", "h3": "Concentrated at the mine, low leverage",
             "text": f"The mine is the most concentrated stage: Iran produced {IR}% of the world's celestite in 2024. "
                     "The leverage that gives is low. The market is small, the lead has passed between Mexico, Spain, "
                     "China and Iran since 2000, and most uses have substitutes. The chain is worth mapping because "
                     "ferrite magnets are a real hedge against rare-earth magnet supply, not because a supply "
                     "emergency is waiting.",
             "flag": "worth knowing, not worrying"},
        ]},
    ],
    "trade_intro": "Two customs lines are shown. Strontium carbonate (283692) is the main traded strontium "
                   "chemical and has a line of its own. It shows who processes and sells strontium, which is not "
                   "who mines it. The second line, 281640, lumps strontium oxides with barium oxides, so it does "
                   "not measure strontium alone. Celestite, the ore, has no line of its own: it travels inside a "
                   "catch-all for other minerals, which is not shown because it says nothing about strontium. "
                   "For who mines the ore, read the mine history above.",
    "method": [
        {"stage": "Mine", "lens": "BGS celestite share and history", "why": f"Iran {IR}% in 2024; the most concentrated stage"},
        {"stage": "Use", "lens": "ferrite magnets vs pyrotechnics", "why": "the rare-earth-free magnet hedge + red flame"},
        {"stage": "Character", "lens": "concentrated, low leverage", "why": "small market, the lead has changed hands, most uses have substitutes"},
        {"stage": "Trade", "lens": "BACI 283692 carbonate, 281640 oxides", "why": "the carbonate is strontium alone; the oxides line is lumped with barium"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), f"- strontium, ferrite magnets + red flame; Iran {IR}pct of 2024 celestite (BGS)")
