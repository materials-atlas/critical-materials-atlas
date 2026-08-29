"""Evidence JSON for the arsenic chain pilot. Uniform schema. Public sources.
A toxic by-product that is also a semiconductor. Run: python record_arsenic.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "arsenic_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_arsenic": {"title": "USGS Mineral Commodity Summaries 2026 — Arsenic", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-arsenic.pdf"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — arsenic", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "usgs_gallium": {"title": "USGS — gallium arsenide (GaAs) semiconductor context", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-gallium.pdf"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Arsenic chain",
    "chokepoint": {"product": "GaAs chips · alloys", "stage": "Recovery (by-product)", "mechanism": "byproduct", "physics": "A by-product of copper/gold smelting — recovered from toxic flue dust, not mined; supply bounded by the host and by nobody wanting to make it", "holder": "Peru · China", "share": "—", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../gallium-chain/gallium-chain", "label": "Gallium chain"}, {"href": "../copper-chain/copper-chain", "label": "Copper chain"}, {"href": "../silicon-chip/silicon-chain", "label": "Silicon → chips chain"}],
    "accent": "#5a6a4a",
    "eyebrow": "Product-chain pilot · the poison in the chip",
    "h1": "The poison that's also a semiconductor — and nobody wants to make it",
    "deck": "Arsenic is notorious as a poison, yet high-purity arsenic is half of gallium arsenide, the compound "
            "semiconductor behind radar, satellite links, high-speed and RF chips and many LEDs. It is not mined for "
            "itself — it is a toxic by-product of copper and gold smelting that producers would rather not make at "
            "all, which is exactly what makes its supply awkward.",
    "byline": "copper/gold ore ≠ by-product arsenic (toxic flue dust) ≠ high-purity As ≠ GaAs chips · alloys · (legacy wood preservative)",
    "correction": "Arsenic is a reluctant by-product. It occurs with copper and gold and is captured, as arsenic "
                  "trioxide, from smelter flue dust — producers minimise it because it is toxic and hard to dispose of, "
                  "so supply is driven by base-metal output and pollution rules, not by arsenic demand. Yet the small "
                  "high-purity fraction is essential: it makes gallium arsenide (GaAs) chips for radar, RF and "
                  "communications (pairing with the gallium chain). China's share of production has fallen sharply as "
                  "Peru's has risen.",
    "stats": [
        {"v": "GaAs", "l": "high-purity arsenic makes gallium-arsenide chips — radar, RF, satellites, LEDs", "conf": "measured"},
        {"v": "by-product", "l": "recovered from copper and gold smelting flue dust — not mined", "conf": "measured"},
        {"v": "reluctant supply", "l": "toxicity means producers minimise output — supply is unwanted, not scaled", "conf": "measured"},
        {"v": "China 72→40%", "l": "China's share of production fell as Peru's rose to the lead", "conf": "measured"},
    ],
    "history": {
        "title": "China fell, Peru rose, 2019 → 2023",
        "conf": "measured",
        "note": "BGS/USGS mine/production, from the atlas's own data (the reliable public series is short). China's "
                "share of arsenic production dropped from ~72% toward ~40% as tighter pollution controls curbed output, "
                "while Peru — where arsenic is a by-product of large copper smelters — rose to the lead. It is a rare "
                "case where a share fell because a country wanted to make less of a toxic material.",
        "series": [
            {"label": "China", "points": hist_points("arsenic", "CN")},
            {"label": "Peru", "points": hist_points("arsenic", "PE")},
            {"label": "Morocco", "points": hist_points("arsenic", "MA")},
        ],
    },
    "hops": [
        {"n": "1 · Host ore", "t": "copper and gold ores containing arsenic — Peru, China, Morocco"},
        {"n": "2 · Capture", "t": "arsenic trioxide recovered from smelter flue dust — a toxic by-product"},
        {"n": "3 · High-purity As", "t": "refined to semiconductor-grade arsenic for compound chips"},
        {"n": "4 · End use", "t": "gallium-arsenide chips, lead/copper alloys; legacy wood preservatives (declining)"},
    ],
    "sections": [
        {"h2": "1 · A by-product no one is trying to grow", "panels": [
            {"kind": "big", "h3": "Why supply is awkward", "big": "reluctant", "conf": "measured",
             "text": "Arsenic is captured as arsenic trioxide from the flue dust of copper and gold smelters, because "
                     "letting it escape would be an environmental disaster. Producers therefore make arsenic they do "
                     "not especially want, and tighter pollution rules — as in China — push them to make less. Supply "
                     "is set by base-metal smelting and regulation, not by demand: a by-product coupling with a toxic "
                     "twist.",
             "note": "USGS Arsenic 2026."},
            {"kind": "text", "h3": "The map shifted for an unusual reason",
             "text": "China long dominated arsenic, but its share fell from around 72% toward 40% as environmental "
                     "controls tightened, while Peru rose to the lead on the back of its large copper smelters. It is "
                     "one of the few chains where a country's production share dropped because it chose to handle less "
                     "of a hazardous material — the opposite of a scramble for control.",
             "flag": "share fell by choice, not loss"},
        ]},
        {"h2": "2 · The semiconductor half", "panels": [
            {"kind": "text", "h3": "Half of gallium arsenide", "conf": "measured",
             "text": "For all its toxicity, high-purity arsenic is essential: combined with gallium it forms gallium "
                     "arsenide (GaAs), a compound semiconductor that handles high frequencies and power better than "
                     "silicon. GaAs is in radar and electronic-warfare systems, satellite and 5G radio front-ends, and "
                     "many LEDs and laser diodes — so arsenic pairs directly with the gallium chain as an input to the "
                     "same strategic chips.",
             "note": "USGS gallium/arsenic.", "flag": "pairs with the gallium chain"},
        ]},
        {"h2": "3 · The uses it is losing", "panels": [
            {"kind": "text", "h3": "Out of wood, into electronics",
             "text": "Historically most arsenic went into chromated-copper-arsenate wood preservative, now banned or "
                     "phased out for residential use in many countries on health grounds. As that bulk use disappears, "
                     "arsenic's remaining demand tilts toward the high-value electronic and alloy uses — a smaller, "
                     "more strategic footprint for a material the world is otherwise trying to use less of.",
             "flag": "a shrinking, more strategic use"},
        ]},
    ],
    "trade_intro": "BACI carries arsenic (280480), but the strategically important part — semiconductor-grade high-"
                   "purity arsenic and the GaAs it makes — is not separable from the bulk toxic material, and much "
                   "arsenic trioxide is handled under hazardous-material rules that trade data reflects poorly. Read the "
                   "shares below as the coarse arsenic trade only.",
    "method": [
        {"stage": "Source", "lens": "USGS/BGS production + history", "why": "a copper/gold by-product; China 72->40%, Peru rose"},
        {"stage": "Character", "lens": "toxicity + regulation", "why": "reluctant supply — made less by choice"},
        {"stage": "Use", "lens": "GaAs vs legacy wood preservative", "why": "tilting from bulk toxic use to strategic chips"},
        {"stage": "Trade", "lens": "BACI 280480 arsenic", "why": "high-purity/GaAs grade not separable — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- arsenic, toxic by-product of copper/gold; GaAs chips; China 72->40pct")
