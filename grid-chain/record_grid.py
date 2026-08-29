"""Evidence JSON for the electricity-grid chain pilot. Uniform schema. Public sources.
Ported onto the shared chainview renderer with per-figure confidence tags. Run: python record_grid.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "grid_chain.json")

SRC = {
    "iea_grids_2023": {"title": "IEA, Electricity Grids and Secure Energy Transitions", "year": 2023, "url": "https://www.iea.org/reports/electricity-grids-and-secure-energy-transitions/executive-summary"},
    "iea_transmission_2025": {"title": "IEA, Building the Future Transmission Grid", "year": 2025, "url": "https://www.iea.org/reports/building-the-future-transmission-grid"},
    "doe_lpt_2024": {"title": "US DOE, Large Power Transformer Resilience Report", "year": 2024, "url": "https://www.energy.gov/sites/default/files/2024-10/EXEC-2022-001242%20-%20Large%20Power%20Transformer%20Resilience%20Report%20signed%20by%20Secretary%20Granholm%20on%207-10-24.pdf"},
    "doe_conductors_2023": {"title": "US DOE, Advanced Conductor Report", "year": 2023, "url": "https://www.energy.gov/sites/default/files/2024-08/Advanced%20Conductor%20Report%20December%202023.pdf"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Electricity-grid chain",
    "chokepoint": {"product": "Electricity grid", "stage": "Transformers", "mechanism": "diffuse", "physics": "Batch-built equipment; the limit is factory lead-time (years), spread across suppliers", "holder": "—", "share": "—", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../copper-chain/copper-chain", "label": "Copper chain"}, {"href": "../aluminium-chain/aluminium-chain", "label": "Aluminium chain"}, {"href": "../data-centre-chain/data-centre-chain", "label": "Data-centre / AI chain"}],
    "accent": "#8a6a3a",
    "eyebrow": "Product-chain pilot · the wires that carry it all",
    "h1": "The ore is fine — the transformer is the bottleneck",
    "deck": "The grid is copper, aluminium and electrical steel — abundant, diversified metals. Yet grids are the "
            "quiet constraint on the whole energy transition, because the chokepoint is not the material but the "
            "equipment: a large power transformer can take up to four years to procure, and the world must roughly "
            "double its grid by 2040.",
    "byline": "copper & aluminium (abundant) ≠ electrical steel ≠ transformers & cables (years-long queues) ≠ the network",
    "correction": "You cannot mine your way to a working grid. Copper and aluminium are not the binding constraint — "
                  "the equipment is. Large power transformers can take up to four years to order, HVDC cables more than "
                  "five, and grain-oriented electrical steel and skilled winding are the real scarcities. Meanwhile "
                  "~1,500 GW of renewables sit waiting in connection queues.",
    "stats": [
        {"v": "up to 4 yr", "l": "to procure a large power transformer", "conf": "measured"},
        {"v": "2–3 yr", "l": "cable procurement lead time (HVDC cables more than 5)", "conf": "measured"},
        {"v": "80M km", "l": "of grid to add or refurbish by 2040 — about as much as exists today", "conf": "measured"},
        {"v": "~1,500 GW", "l": "of renewables queued waiting for grid connection", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Metals & steel", "t": "copper, aluminium and grain-oriented electrical steel — abundant, diversified"},
        {"n": "2 · Conductors & cores", "t": "wire rod, stranded conductor, cable and transformer steel cores"},
        {"n": "3 · Equipment", "t": "transformers, switchgear, converters — years-long procurement queues"},
        {"n": "4 · Network", "t": "substations plus overhead, underground and submarine lines — the power system"},
    ],
    "sections": [
        {"h2": "1 · The chokepoint is the equipment, not the ore", "panels": [
            {"kind": "big", "h3": "The transformer queue", "big": "up to 4 years", "conf": "measured",
             "text": "A large power transformer — the workhorse that steps voltage up and down across the grid — can now "
                     "take up to four years to procure, with prices sharply higher. HVDC cables run even longer, more "
                     "than five years. These lead times, not any raw material, are what actually delay connecting new "
                     "generation and reinforcing the network.",
             "note": "IEA, Building the Future Transmission Grid; US DOE."},
            {"kind": "text", "h3": "Why: electrical steel and skilled winding",
             "text": "Transformer cores need grain-oriented electrical steel, made by a small number of mills, and "
                     "building a transformer takes skilled winding and testing that cannot be rushed. The bottleneck is "
                     "specialised manufacturing capacity and order backlogs — a factory-and-workforce problem, the same "
                     "shape as the grid-connection queue, not a mine problem.",
             "flag": "grain-oriented steel + skilled labour"},
        ]},
        {"h2": "2 · The metal is genuinely abundant", "panels": [
            {"kind": "text", "h3": "Copper and aluminium are not the wall here", "conf": "measured",
             "text": "Grids run on copper and aluminium, both diversified and recyclable. Aluminium even substitutes for "
                     "copper in many overhead lines. Copper has its own longer-term tightness — a demand-versus-mine-"
                     "timeline story told in the copper chain — but for building the grid this decade, the metal is not "
                     "the binding constraint. The equipment lead time is.",
             "note": "US DOE, Advanced Conductor Report.", "flag": "see the copper chain for the metal's own clock"},
        ]},
        {"h2": "3 · The scale of what's needed", "panels": [
            {"kind": "cards", "h3": "A grid that has to double", "cards": [
                {"t": "80 million km", "d": "The IEA estimates the world must add or refurbish ~80 million km of grid by 2040 — roughly the length of the entire existing network, built again."},
                {"t": "1,500 GW queued", "d": "Around 1,500 GW of renewable projects — many times a year's additions — sit in interconnection queues, waiting on grid capacity that isn't there."},
                {"t": "The silent gate", "d": "Grids rarely make headlines, but they gate solar, wind, EV charging and data centres alike — the chokepoint downstream of every clean-energy chain."},
            ]},
        ]},
    ],
    "trade_intro": "BACI carries copper wire, aluminium conductor, transformers and switchgear, but a transformer's "
                   "customs origin is its assembly plant, not the electrical-steel mill or the order backlog behind it. "
                   "Read the shares below as equipment-trade positions; the binding constraint — manufacturing lead "
                   "time — is not visible in trade data.",
    "method": [
        {"stage": "Metals", "lens": "USGS/DOE copper & aluminium", "why": "abundant and diversified — not the grid's chokepoint"},
        {"stage": "Equipment", "lens": "IEA/DOE transformer & cable lead times", "why": "up to 4+ years — the real bottleneck"},
        {"stage": "Network", "lens": "IEA grid-length & queue estimates", "why": "must roughly double by 2040; ~1,500 GW queued"},
        {"stage": "Trade", "lens": "BACI wire/conductor/transformers", "why": "assembly-point origin, not lead times — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- grid, metal abundant; bottleneck = transformer/cable lead times")
