"""Evidence JSON for the silver chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_silver.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "silver_chain.json")

SRC = {
    "usgs_silver": {"title": "USGS Mineral Commodity Summaries 2026 — Silver", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-silver.pdf"},
    "silver_institute": {"title": "The Silver Institute, World Silver Survey", "year": 2025, "url": "https://www.silverinstitute.org/all-world-silver-surveys/"},
    "iea_solar": {"title": "IEA, Solar PV Global Supply Chains (silver in cells)", "year": 2022, "url": "https://www.iea.org/reports/solar-pv-global-supply-chains"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Silver chain",
    "chokepoint": {"product": "Solar paste · contacts", "stage": "Mine (by-product)", "mechanism": "byproduct", "physics": "~70% a by-product of lead/zinc/copper/gold — output bounded by the base metals, can't scale to demand", "holder": "Mexico · CN · Peru", "share": "—", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../solar-chain/solar-chain.html", "label": "Solar-PV chain"}, {"href": "../copper-chain/copper-chain.html", "label": "Copper chain"}, {"href": "../displays-indium-chain/displays-indium-chain.html", "label": "Displays / indium chain"}],
    "accent": "#7a8a9a",
    "eyebrow": "Product-chain pilot · money, mirrors and solar cells",
    "h1": "Most silver is a by-product — and solar is eating the rest",
    "deck": "Silver is the best electrical and thermal conductor there is, and no substitute matches it in high-end "
            "contacts or in the paste that carries current out of a solar cell. But most silver is not mined for "
            "itself — it comes as a by-product of lead, zinc, copper and gold mining — so its supply cannot respond to "
            "its own demand, and industrial use, led by solar, is running ahead of it.",
    "byline": "lead/zinc/copper/gold mine ≠ by-product silver ≠ refined silver ≠ solar paste · contacts · jewelry & investment",
    "correction": "Silver behaves like a by-product metal wearing a precious-metal coat. Around 70% of mined silver is "
                  "recovered as a by-product of lead, zinc, copper and gold operations, so miners cannot ramp silver "
                  "when its price rises — it rides on base-metal output. Meanwhile industrial demand, now more than "
                  "half of the total and led by solar-cell paste, is climbing. The result is a structural supply "
                  "deficit cushioned only by investment and jewelry stocks and by recycling.",
    "stats": [
        {"v": "~70%", "l": "of mined silver is a by-product of lead, zinc, copper and gold", "conf": "measured"},
        {"v": "solar", "l": "PV paste is the fastest-growing industrial use — the swing consumer", "conf": "measured"},
        {"v": "no substitute", "l": "the best conductor there is — contacts, PV paste, electronics", "conf": "measured"},
        {"v": "deficit", "l": "industrial demand is outrunning by-product supply — a structural deficit", "conf": "estimate"},
    ],
    "hops": [
        {"n": "1 · Host mine", "t": "lead, zinc, copper and gold ores — silver rides along as a by-product"},
        {"n": "2 · Recover & refine", "t": "silver separated during base-metal smelting/refining, plus primary silver mines"},
        {"n": "3a · Industrial", "t": "solar-cell paste, electrical contacts, electronics, brazing, catalysts"},
        {"n": "3b · Investment & jewelry", "t": "coins, bars, jewelry and silverware — a large, price-elastic buffer"},
    ],
    "sections": [
        {"h2": "1 · Silver rides on base metals", "panels": [
            {"kind": "big", "h3": "How most silver is produced", "big": "~70% by-product", "conf": "measured",
             "text": "Only a minority of silver comes from dedicated silver mines; most is recovered as a credit when "
                     "lead, zinc, copper and gold ores are smelted and refined. That means silver supply is set by "
                     "base-metal economics, not by silver's own price — the same by-product coupling that makes gallium "
                     "and indium hard to scale, but on a precious metal that markets treat as money.",
             "note": "USGS Silver 2026; Silver Institute."},
            {"kind": "text", "h3": "So supply can't chase demand",
             "text": "When silver demand or price rises, miners cannot simply produce more, because the silver only "
                     "appears alongside base metals the market may not want more of. New primary silver mines are few. "
                     "So the balancing has to come from above-ground stocks and recycling rather than from fresh mine "
                     "supply — a structurally tight setup.",
             "flag": "output set by lead, zinc and copper"},
        ]},
        {"h2": "2 · Solar is the new swing demand", "panels": [
            {"kind": "text", "h3": "The paste on every cell", "conf": "measured",
             "text": "Silver paste forms the fine conductive lines that collect current on a solar cell, and with "
                     "hundreds of gigawatts of panels made each year (see the solar chain), photovoltaics have become a "
                     "major and fast-growing silver consumer. The industry keeps thrifting the silver per cell, but has "
                     "not eliminated it — so as solar scales, it pulls harder on a supply that cannot easily grow.",
             "note": "IEA; Silver Institute.", "flag": "PV, the fastest-growing use"},
            {"kind": "text", "h3": "Industrial demand now leads",
             "text": "Beyond solar, silver is unmatched in electrical and thermal conductivity — it goes into contacts, "
                     "switches, electronics, EVs, brazing alloys and catalysts, with essentially no equal substitute in "
                     "the highest-performance roles. Industrial uses now make up more than half of silver demand, "
                     "shifting it from a monetary metal toward a technology input.",
             "flag": "more a tech metal than money now"},
        ]},
        {"h2": "3 · The buffer: stocks and recycling", "panels": [
            {"kind": "text", "h3": "Why the deficit hasn't broken",
             "text": "Silver has run a structural supply deficit — industrial plus investment demand above mine and "
                     "recycling supply — for several years, drawn down from large above-ground stocks of coins, bars "
                     "and jewelry that can return to market when prices rise. Recycling recovers a meaningful share too. "
                     "That buffer, plus silver's dual monetary-industrial nature, absorbs the gap the by-product mine "
                     "cannot close.",
             "flag": "above-ground stock cushions the mine"},
        ]},
    ],
    "trade_intro": "BACI carries silver ores (261610) and unwrought silver (710691), but refined-silver flows also move "
                   "through bullion and investment channels that are trading, not consumption. Read the shares below as "
                   "the traded metal, not the by-product mine origin or the industrial demand pulling on it.",
    "method": [
        {"stage": "Mine", "lens": "USGS/Silver Institute by-product share", "why": "~70% a by-product of base metals — can't scale alone"},
        {"stage": "Demand", "lens": "industrial vs investment", "why": "industrial >half, led by solar — the swing"},
        {"stage": "Balance", "lens": "deficit vs above-ground stocks", "why": "structural deficit cushioned by stocks + recycling"},
        {"stage": "Trade", "lens": "BACI 261610 ore + 710691 silver", "why": "traded metal incl. bullion — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- silver, ~70pct by-product; solar swing demand; structural deficit")
