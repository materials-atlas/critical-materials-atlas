"""Evidence JSON for the strontium chain pilot. Uniform schema. Public sources.
Ferrite magnets and the red in fireworks. Run: python record_strontium.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "strontium_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_strontium": {"title": "USGS Mineral Commodity Summaries 2026 — Strontium", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-strontium.pdf"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — strontium (celestine)", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "iea_magnets": {"title": "IEA / industry — ferrite vs rare-earth permanent magnets", "year": 2024, "url": "https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Strontium chain",
    "chokepoint": {"product": "Ferrite magnets · pyrotechnics", "stage": "Mine (celestite)", "mechanism": "diffuse", "physics": "A small celestite-mineral market spread across Iran, China, Spain and Mexico — moderately concentrated, no severe chokepoint", "holder": "Iran", "share": "~58%", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../magnet-chain/magnet-chain.html", "label": "Rare-earth magnet chain"}, {"href": "../boron-chain/boron-chain.html", "label": "Boron chain"}, {"href": "../rare-earths-chain/rare-earths-chain.html", "label": "Rare earths (full basket)"}],
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
                  "NdFeB is too expensive for. Mined as celestite, its supply is small and moderately concentrated — "
                  "Iran now accounts for roughly 58% of production, up from a market once led by Mexico and Spain — but "
                  "it is not a severe chokepoint. Its quiet importance is as the everyday magnet material and the "
                  "crimson in pyrotechnics.",
    "stats": [
        {"v": "ferrite magnets", "l": "strontium makes the cheap, rare-earth-free ceramic magnets", "conf": "measured"},
        {"v": "~58% Iran", "l": "Iran now leads celestite mining (from a Mexico/Spain-led market)", "conf": "measured"},
        {"v": "crimson flame", "l": "the red in fireworks, flares and signal rockets — plus specialty glass", "conf": "measured"},
        {"v": "the magnet hedge", "l": "ferrite is the fallback where rare-earth magnets are too costly", "conf": "estimate"},
    ],
    "history": {
        "title": "The mine moved to Iran, 2000 → 2024",
        "conf": "measured",
        "note": "BGS/USGS mine production, from the atlas's own data. Celestite mining shifted from a market led by "
                "Mexico and Spain around 2000 to one led by Iran (~58%) today, with China holding a steady share. It is "
                "a small, moderately-concentrated mineral market — enough of a shift to notice, not enough to be a "
                "chokepoint.",
        "series": [
            {"label": "Iran", "points": hist_points("strontium", "IR")},
            {"label": "China", "points": hist_points("strontium", "CN")},
            {"label": "Spain", "points": hist_points("strontium", "ES")},
        ],
    },
    "hops": [
        {"n": "1 · Celestite", "t": "strontium sulfate ore — Iran ~58%, plus China, Spain, Mexico"},
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
            {"kind": "text", "h3": "Moderately concentrated, not weaponised",
             "text": "Strontium's market is small and its concentration modest — Iran's rise is notable but the mineral "
                     "is not a lever, and substitutes exist for most uses. It sits in the atlas as a 'diffuse' chain: "
                     "worth mapping because ferrite magnets are a genuine rare-earth hedge, but not a supply "
                     "emergency in waiting.",
             "flag": "worth knowing, not worrying"},
        ]},
    ],
    "trade_intro": "BACI carries strontium/barium oxides (281640) and celestite within broad mineral lines (253090), so "
                   "strontium cannot be cleanly isolated — the market is small and the compounds lumped. Read the "
                   "shares below as coarse context; the mine map (Iran-led) is the clearer signal, shown in the history "
                   "above.",
    "method": [
        {"stage": "Mine", "lens": "USGS/BGS celestite share + history", "why": "Iran ~58%; small, moderately concentrated"},
        {"stage": "Use", "lens": "ferrite magnets vs pyrotechnics", "why": "the rare-earth-free magnet hedge + red flame"},
        {"stage": "Character", "lens": "diffuse, not a lever", "why": "small market, substitutes exist — not a chokepoint"},
        {"stage": "Trade", "lens": "BACI 281640 oxides + 253090 minerals", "why": "strontium lumped/not separable — flagged proxy"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- strontium, ferrite magnets + red flame; Iran ~58pct celestite (diffuse)")
