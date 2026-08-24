"""Evidence JSON for the primary / green-steel chain pilot. Uniform schema. Public sources.
Distinct from the steel-alloys chain (ferroalloys); this is iron ore -> crude steel + the green shift.
Shared chainview renderer, per-figure confidence tags. Run: python record_steel.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "steel_chain.json")

SRC = {
    "usgs_iron_ore": {"title": "USGS Mineral Commodity Summaries 2026 — Iron Ore", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-iron-ore.pdf"},
    "usgs_steel": {"title": "USGS Mineral Commodity Summaries 2026 — Iron and Steel", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-iron-steel.pdf"},
    "iea_steel": {"title": "IEA, Iron and Steel Technology Roadmap", "year": 2020, "url": "https://www.iea.org/reports/iron-and-steel-technology-roadmap"},
    "worldsteel": {"title": "worldsteel, World Steel in Figures 2025", "year": 2025, "url": "https://worldsteel.org/data/world-steel-in-figures/"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Primary / green-steel chain",
    "published": True,
    "related": [{"href": "../steel-alloys-chain/steel-alloys-chain.html", "label": "Steel-alloys chain"}, {"href": "../aluminium-chain/aluminium-chain.html", "label": "Aluminium chain"}, {"href": "../copper-chain/copper-chain.html", "label": "Copper chain"}],
    "accent": "#7a6a5a",
    "eyebrow": "Product-chain pilot · the material civilisation is built from",
    "h1": "The iron ore is abundant — the chokepoints are coal and the green transition",
    "deck": "Steel is the most-produced metal on Earth, and its ore is genuinely plentiful — Australia and Brazil "
            "ship most of the world's iron ore. The real constraints sit elsewhere: metallurgical coking coal to "
            "reduce the ore, and, for low-carbon 'green steel', a scarce grade of ore plus clean hydrogen.",
    "byline": "iron ore (abundant, AU/BR) ≠ coking coal (the carbon chokepoint) ≠ crude steel (~54% CN) ≠ green steel (ore + H2)",
    "correction": "Steel breaks the 'scarce mineral' frame — iron is the fourth-most-abundant element in the crust and "
                  "the ore trade is diversified. The bottlenecks are a fuel and a transition: metallurgical coking "
                  "coal reduces most of the world's ore (China smelts ~54% of crude steel), and decarbonising it needs "
                  "hydrogen-based direct reduction — which in turn needs high-grade DRI-suitable ore that is itself in "
                  "short supply.",
    "stats": [
        {"v": "~54%", "l": "China's share of world crude-steel production", "conf": "measured"},
        {"v": "AU + BR", "l": "Australia and Brazil ship most of the world's seaborne iron ore", "conf": "measured"},
        {"v": "coking coal", "l": "the carbon chokepoint — most steel is still made via coke-fired blast furnaces", "conf": "measured"},
        {"v": "DRI-grade", "l": "green steel needs scarce high-grade ore plus clean hydrogen", "conf": "estimate"},
    ],
    "hops": [
        {"n": "1 · Iron ore", "t": "haematite/magnetite — abundant; Australia and Brazil dominate seaborne supply"},
        {"n": "2 · Reduce", "t": "coke-fired blast furnace (most steel) or direct reduction (gas/hydrogen DRI)"},
        {"n": "3 · Crude steel", "t": "basic-oxygen or electric-arc furnace — China makes ~54% of it"},
        {"n": "4 · Rolled & finished", "t": "flat and long products for construction, cars, machinery, packaging"},
    ],
    "sections": [
        {"h2": "1 · The ore is not the problem", "panels": [
            {"kind": "text", "h3": "Abundant and diversified at the mine", "conf": "measured",
             "text": "Iron ore is one of the least scarce inputs in this atlas: Australia and Brazil supply the bulk of "
                     "seaborne trade, with more from India, Russia, South Africa and Canada, and reserves are huge. "
                     "Unlike gallium or rare earths, there is no single-country geological chokepoint at the iron mine. "
                     "The concentration in steel is downstream, in who smelts it.",
             "note": "USGS Iron Ore 2026.", "flag": "no chokepoint at the mine"},
            {"kind": "big", "h3": "Where it concentrates", "big": "~54% China", "conf": "measured",
             "text": "China makes roughly 54% of the world's crude steel, importing ore (much of it Australian and "
                     "Brazilian) and turning it into metal in the world's largest blast-furnace fleet. So steel's "
                     "concentration is an industrial one — smelting capacity — not a mined-resource one, the same "
                     "pattern as aluminium.",
             "note": "worldsteel; USGS Iron and Steel 2026."},
        ]},
        {"h2": "2 · The carbon chokepoint: coking coal", "panels": [
            {"kind": "text", "h3": "Most steel is still made with coke", "conf": "measured",
             "text": "Around 70% of world steel comes from the blast-furnace route, which reduces iron ore with coke "
                     "made from metallurgical (coking) coal — a distinct, higher-quality coal from the thermal coal "
                     "burned in power stations, and a more concentrated trade led by Australia. This is both the "
                     "binding input for conventional steel and the reason steel is ~7-8% of global CO2 emissions.",
             "note": "IEA Iron and Steel Roadmap.", "flag": "coking coal ≠ thermal coal"},
        ]},
        {"h2": "3 · Green steel moves the chokepoint again", "panels": [
            {"kind": "cards", "h3": "What decarbonising steel actually needs", "cards": [
                {"t": "Clean hydrogen", "d": "Hydrogen direct reduction (H2-DRI) replaces coke with hydrogen — tying green steel to the electrolyser and clean-power chains."},
                {"t": "DRI-grade ore", "d": "Direct reduction needs high-iron, low-gangue pellet feed; most of the world's ore is NOT DRI-grade, making that specific ore the new bottleneck."},
                {"t": "Scrap + power", "d": "Electric-arc furnaces run on scrap and clean electricity — the fastest lever, but limited by scrap availability and grid capacity."},
            ]},
        ]},
    ],
    "trade_intro": "BACI carries iron ore, coal and semi-finished and finished steel, but not the distinction between "
                   "coking and thermal coal, nor DRI-grade versus ordinary ore. Read the shares below as the traded "
                   "bulk commodities; the transition-relevant grades and the coke quality are not separable in customs "
                   "data.",
    "method": [
        {"stage": "Iron ore", "lens": "USGS mine/trade share", "why": "abundant and diversified — not the chokepoint"},
        {"stage": "Reduce", "lens": "blast furnace vs DRI; coking coal", "why": "the carbon chokepoint; ~70% via coke"},
        {"stage": "Crude steel", "lens": "worldsteel production share", "why": "~54% China — an industrial concentration"},
        {"stage": "Green shift", "lens": "IEA H2-DRI / DRI-grade ore", "why": "the transition's bottleneck — marked as forward-looking"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- steel, ore abundant; chokepoint = coking coal + green (DRI+H2)")
