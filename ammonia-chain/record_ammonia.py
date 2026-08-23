"""Evidence JSON for the ammonia / nitrogen-fertilizer chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_ammonia.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "ammonia_chain.json")

SRC = {
    "usgs_nitrogen": {"title": "USGS Mineral Commodity Summaries 2026 — Nitrogen (Fixed)–Ammonia", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-nitrogen.pdf"},
    "iea_ammonia": {"title": "IEA, Ammonia Technology Roadmap", "year": 2021, "url": "https://www.iea.org/reports/ammonia-technology-roadmap"},
    "fao": {"title": "FAO, World fertilizer trends and outlook", "year": 2022, "url": "https://www.fao.org/documents/card/en/c/cc0088en"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Ammonia / nitrogen-fertilizer chain",
    "accent": "#5a7a4a",
    "eyebrow": "Product-chain pilot · the other half of the food supply",
    "h1": "Half the world eats because we pull nitrogen from the air with natural gas",
    "deck": "Phosphate is one half of the fertilizer story (its own chain); nitrogen is the other. Synthetic nitrogen "
            "fertilizer is made by the Haber-Bosch process, which fixes inert nitrogen from the air into ammonia using "
            "hydrogen from natural gas. Roughly half of humanity is fed on the crops it enables — and its chokepoint "
            "is an energy price, not a mineral.",
    "byline": "natural gas (feedstock + energy) ≠ Haber-Bosch ≠ ammonia ≠ urea / nitrate ≠ the harvest",
    "correction": "Unlike most chains here, nitrogen has no scarce ore — its raw material is 78% of the air. The "
                  "binding input is natural gas, used both as the hydrogen feedstock and as the energy to run "
                  "Haber-Bosch, so ammonia's real chokepoint is the gas price and where cheap gas sits. When European "
                  "gas prices spiked in 2022, ammonia plants across Europe simply shut down — a food-security shock "
                  "driven by energy, not by a mine.",
    "stats": [
        {"v": "~half", "l": "of the world's food is grown with synthetic nitrogen fertilizer", "conf": "measured"},
        {"v": "natural gas", "l": "both the hydrogen feedstock and the energy — the real chokepoint", "conf": "measured"},
        {"v": "Haber-Bosch", "l": "fixes inert N2 from the air into ammonia — the raw material is free", "conf": "measured"},
        {"v": "~2%", "l": "of world energy use goes to making ammonia", "conf": "estimate"},
    ],
    "hops": [
        {"n": "1 · Natural gas", "t": "methane supplies hydrogen (via reforming) and the process energy"},
        {"n": "2 · Haber-Bosch", "t": "N2 from air + H2 → ammonia (NH3) at high temperature and pressure"},
        {"n": "3 · Fertilizer", "t": "ammonia → urea, ammonium nitrate and other nitrogen fertilizers"},
        {"n": "4 · The harvest", "t": "applied to crops — the yield that feeds roughly half the planet"},
    ],
    "sections": [
        {"h2": "1 · The raw material is free; the energy is not", "panels": [
            {"kind": "big", "h3": "What feeds the world", "big": "~half of food", "conf": "measured",
             "text": "Nitrogen is the nutrient that limits plant growth, and about half of the world's population is fed "
                     "on crops grown with synthetic nitrogen fertilizer. The nitrogen itself is inexhaustible — it is "
                     "the air — so this chain has no mine. What it has instead is a heavy dependence on natural gas, "
                     "which supplies both the hydrogen and the energy for Haber-Bosch.",
             "note": "IEA Ammonia Roadmap; FAO."},
            {"kind": "text", "h3": "So the chokepoint is the gas price",
             "text": "Because gas is ~70-90% of the cost of making ammonia, the fertilizer map is really a cheap-gas "
                     "map: production concentrates where gas is abundant and cheap (the US, the Middle East, Russia, "
                     "Trinidad), and China uses coal-based routes. Nitrogen supply is therefore an energy-and-industrial "
                     "story, the same shape as aluminium's electricity dependence.",
             "flag": "a cheap-gas map, not an ore map"},
        ]},
        {"h2": "2 · When energy breaks, food supply wobbles", "panels": [
            {"kind": "text", "h3": "The 2022 European shutdowns", "conf": "measured",
             "text": "When European natural-gas prices spiked in 2022, many ammonia plants across Europe curtailed or "
                     "closed because making fertilizer was no longer economic — and Russia and Belarus are major "
                     "fertilizer exporters, so the same shock hit supply from two sides. Fertilizer prices surged and "
                     "food-security alarms followed. It was an energy crisis transmitted straight into agriculture.",
             "note": "IEA; FAO.", "flag": "an energy shock, felt as a food shock"},
        ]},
        {"h2": "3 · The decarbonisation branch: green ammonia", "panels": [
            {"kind": "cards", "h3": "Two futures for a gas-bound chain", "cards": [
                {"t": "Green ammonia", "d": "Replace gas-derived hydrogen with electrolytic hydrogen from clean power — tying nitrogen fertilizer to the electrolyser chain."},
                {"t": "Ammonia as fuel", "d": "Ammonia is also emerging as a carbon-free shipping fuel and hydrogen carrier, adding new demand on top of fertilizer."},
                {"t": "The CO2 cost", "d": "Ammonia is ~1.3% of global CO2 emissions today; the transition matters for climate as much as for food security."},
            ]},
        ]},
    ],
    "trade_intro": "BACI carries anhydrous ammonia (281410) and urea (310210), among other nitrogen products, but not "
                   "the natural gas or the energy behind them, which is where the real cost and chokepoint sit. Read "
                   "the shares below as the traded fertilizer forms; the binding input — cheap gas — is a separate "
                   "energy market.",
    "method": [
        {"stage": "Raw material", "lens": "nitrogen from air (Haber-Bosch)", "why": "no ore — the nitrogen is free"},
        {"stage": "Energy", "lens": "natural-gas feedstock + process energy", "why": "~70-90% of cost — the real chokepoint"},
        {"stage": "Shock", "lens": "2022 EU plant shutdowns", "why": "an energy crisis transmitted to food supply"},
        {"stage": "Trade", "lens": "BACI 281410 ammonia + 310210 urea", "why": "fertilizer forms; the gas market is separate — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- ammonia, nitrogen from air; chokepoint = natural gas; 2022 EU shutdowns")
