"""Evidence JSON for the unpublished steel / structural-alloys chain pilot. Uniform schema.
Public sources. Run: python record_steel.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "steel_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")

def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]

SRC = {
    "usgs_niobium": {"title": "USGS Mineral Commodity Summaries 2026 — Niobium (Columbium)", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-niobium.pdf"},
    "usgs_vanadium": {"title": "USGS Mineral Commodity Summaries 2025 — Vanadium", "year": 2025, "url": "https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-vanadium.pdf"},
    "usgs_chromium": {"title": "USGS Mineral Commodity Summaries 2025 — Chromium", "year": 2025, "url": "https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-chromium.pdf"},
    "usgs_manganese": {"title": "USGS Mineral Commodity Summaries 2025 — Manganese", "year": 2025, "url": "https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-manganese.pdf"},
    "usgs_moly": {"title": "USGS Mineral Commodity Summaries 2025 — Molybdenum", "year": 2025, "url": "https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-molybdenum.pdf"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Steel / structural-alloys chain",
    "related": [{"href": "../steel-chain/steel-chain.html", "label": "Primary / green-steel chain"}, {"href": "../tungsten-chain/tungsten-chain.html", "label": "Tungsten chain"}, {"href": "../wind-chain/wind-chain.html", "label": "Wind-turbine chain"}],
    "accent": "#4e5a66",
    "eyebrow": "Product-chain pilot · the built world",
    "h1": "Steel is abundant; the metals that make it strong are not",
    "deck": "Almost everything built — buildings, rail, ships, cars, pipelines — is steel. Iron ore and coking coal "
            "are everywhere, so steel itself is not a chokepoint. But the small alloying additions that give steel "
            "its strength, hardness and corrosion resistance come from a handful of concentrated sources.",
    "byline": "iron ore (abundant) ≠ alloying metals (concentrated) ≠ steel grade ≠ what fails first",
    "correction": "A steel-supply map looks reassuring — iron is one of the commonest elements. The risk hides in the "
                  "additives: a few hundred grams of niobium per tonne, from essentially one Brazilian mine, decide "
                  "whether a pipeline or a car body can be made light and strong.",
    "stats": [
        {"v": "~92%", "l": "of world niobium is Brazil (one company, CBMM)", "conf": "measured"},
        {"v": "~64%", "l": "of world vanadium is China — tied to its steel industry", "conf": "measured"},
        {"v": "SA → CN", "l": "chromium: South Africa mines the ore, China makes the ferrochrome", "conf": "measured"},
        {"v": "77%", "l": "of niobium goes into steel (21% into superalloys)", "conf": "measured"},
    ],
    "history": {
        "title": "The alloying metals stay concentrated (top-producer share)",
        "conf": "measured",
        "note": "BGS/USGS mine production, from the atlas's own data. Niobium (Brazil) sits near 90% and vanadium "
                "(China) near two-thirds for years — durable concentration, not a passing snapshot. Niobium's series "
                "is shorter (2019–2023) because that is the comparable window in the local data.",
        "series": [
            {"label": "Niobium (Brazil)", "points": hist_points("niobium", "BR")},
            {"label": "Vanadium (China)", "points": hist_points("vanadium", "CN")},
        ],
    },
    "hops": [
        {"n": "1 · Base", "t": "iron ore + coking coal → steel — abundant, not a chokepoint"},
        {"n": "2 · Alloying metals", "t": "niobium, chromium, vanadium, manganese, molybdenum — concentrated"},
        {"n": "3 · Steel grades", "t": "microalloyed (Nb/V) · stainless (Cr) · tool/heat (Mo/W)"},
        {"n": "4 · What fails first", "t": "not the steel — the additive that gives it its property"},
    ],
    "sections": [
        {"h2": "1 · The base is abundant; the additives are not", "panels": [
            {"kind": "bars", "h3": "Concentration of the key steel-alloying metals", "conf": "measured", "max": 1.0, "note":
                "USGS. Niobium and vanadium are mine shares; chromium and manganese are more concentrated at the "
                "ferroalloy/processing stage (China) than at the mine. Read each by the stage that binds it.", "bars": [
                {"label": "Niobium (Brazil, mine)", "value": 0.92},
                {"label": "Vanadium (China, mine)", "value": 0.64},
                {"label": "Chromium (China, ferrochrome)", "value": 0.60},
                {"label": "Molybdenum (China, mine)", "value": 0.40},
            ]},
            {"kind": "text", "h3": "A few hundred grams decide the grade",
             "text": "Microalloyed (HSLA) steel gets its strength-to-weight from tiny niobium and vanadium additions — "
                     "often well under a kilogram per tonne of steel. That is why a trace-metal chokepoint can gate an "
                     "entire category of light, strong steel used in cars, pipelines and structures.",
             "flag": "trace additive, whole-grade leverage"},
        ]},
        {"h2": "2 · Niobium — one mine for the world", "panels": [
            {"kind": "big", "h3": "Niobium mine share", "big": "~92% Brazil", "conf": "measured",
             "text": "one country — and largely one company, CBMM at Araxá — supplies most of the world's niobium, with "
                     "Canada a distant second. About 77% goes into steel as ferro-niobium; Brazil's exports run ~49% to "
                     "China. It is one of the most geographically concentrated critical materials there is.",
             "note": "USGS MCS 2026 (Niobium)."},
            {"kind": "text", "h3": "The partial hedge: interchangeability",
             "text": "USGS notes that manganese, molybdenum, niobium, titanium and tungsten are to some degree "
                     "interchangeable with vanadium as steel alloying elements. So no single one is irreplaceable — but "
                     "substitution changes the recipe, the cost and the properties, and cannot happen overnight.",
             "flag": "substitutable, but not instantly"},
        ]},
        {"h2": "3 · Chromium & vanadium — the ore is not the ferroalloy", "panels": [
            {"kind": "text", "h3": "Chromium: mined in South Africa, alloyed in China", "conf": "measured",
             "text": "South Africa leads chromite-ore mining, but China is the leading producer of ferrochromium and "
                     "stainless steel — and the largest chromium consumer. As with the atlas's other materials, the "
                     "chokepoint sits at the ferroalloy/processing stage, not the mine. Stainless steel cannot be made "
                     "without it.",
             "note": "USGS (Chromium)."},
            {"kind": "text", "h3": "Vanadium: a Chinese-steel by-product",
             "text": "China is the top vanadium producer, much of it recovered from steelmaking slag, so vanadium "
                     "supply is coupled to the Chinese steel industry itself. Vanadium adds strength to rebar and "
                     "aerospace alloys, and is the basis of vanadium-flow grid batteries — a second, growing demand.",
             "note": "USGS (Vanadium).", "flag": "coupled to Chinese steel"},
        ]},
        {"h2": "4 · What this means for the built world", "panels": [
            {"kind": "text", "h3": "The risk is the recipe, not the metal",
             "text": "Steel will not run out. But the properties a modern economy depends on — high strength-to-weight, "
                     "corrosion resistance, heat tolerance — come from alloying metals concentrated in Brazil (niobium), "
                     "China (vanadium, ferrochrome, ferromanganese) and South Africa (chromite). A disruption would not "
                     "stop steelmaking; it would degrade what grades of steel the world can make, and at what cost.",
             "flag": "grade risk, not tonnage risk"},
        ]},
    ],
    "trade_intro": "BACI shows the traded ferroalloys — ferro-niobium, ferro-vanadium, ferro-chromium, ferro-manganese "
                   "— which are closer to the alloying stage than to crude steel. Read exporter shares as availability "
                   "of the alloy addition, not of steel itself (steel is a much larger, separate trade).",
    "method": [
        {"stage": "Base", "lens": "context (steel is abundant)", "why": "iron/coking coal are not the chokepoint"},
        {"stage": "Alloying metals", "lens": "USGS mine or ferroalloy share", "why": "concentration by the binding stage per metal"},
        {"stage": "History", "lens": "BGS/USGS 2000–2024 mine series", "why": "concentration is durable, not a snapshot"},
        {"stage": "Trade", "lens": "BACI ferroalloys", "why": "the alloy addition as traded, not steel"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "— steel/alloys, niobium ~92% Brazil, vanadium ~64% China")
