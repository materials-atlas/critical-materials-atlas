"""Evidence JSON for the data-centre / AI-infrastructure chain pilot. Uniform schema. Public sources.
Ported onto the shared chainview renderer with per-figure confidence tags. Run: python record_data_centre.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "data_centre_chain.json")

SRC = {
    "iea_demand": {"title": "IEA, Energy and AI — Energy demand from AI", "year": 2025, "url": "https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai"},
    "iea_summary": {"title": "IEA, Energy and AI — Executive summary", "year": 2025, "url": "https://www.iea.org/reports/energy-and-ai/executive-summary"},
    "iea_update": {"title": "IEA, Key Questions on Energy and AI — Executive summary", "year": 2026, "url": "https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary"},
    "doe_lbnl": {"title": "US DOE / LBNL, 2024 Report on U.S. Data Center Energy Use", "year": 2024, "url": "https://www.energy.gov/articles/doe-releases-new-report-evaluating-increase-electricity-demand-data-centers"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Data-centre / AI chain",
    "accent": "#5a5a9c",
    "eyebrow": "Product-chain pilot · the compute behind AI",
    "h1": "The chip is ready — the power isn't",
    "deck": "The story of AI infrastructure is told as a chip story, and the chip is a real chokepoint (see the "
            "silicon-chip chain). But the constraint that now bites is electricity: data-centre power demand is set to "
            "roughly double by 2030, and connecting that load to the grid — transformers, substations, capacity — is "
            "the binding limit.",
    "byline": "chips (a chokepoint of their own) ≠ servers ≠ power & cooling ≠ grid connection ≠ operating electricity",
    "correction": "Once the accelerators are secured, the next wall is not another material — it is megawatts. "
                  "US data-centre electricity roughly tripled from 2014 to 2023, and global demand is projected to "
                  "roughly double to ~950 TWh by 2030. The bottleneck moves to the same place the grid chain flags: "
                  "transformers, substations and grid-connection queues, not the chip.",
    "stats": [
        {"v": "485→950 TWh", "l": "world data-centre electricity, 2025 → 2030 (projection)", "conf": "estimate"},
        {"v": "~3×", "l": "US data-centre electricity growth, 2014 → 2023 (58 → 176 TWh)", "conf": "measured"},
        {"v": "the grid", "l": "the binding constraint is power and connection, not the semiconductors", "conf": "estimate"},
        {"v": "~3%", "l": "of world electricity used by data centres by 2030", "conf": "estimate"},
    ],
    "history": {
        "title": "The load that tripled: US data-centre electricity, 2014 → 2023",
        "conf": "measured",
        "unit": "TWh per year (US)",
        "note": "US DOE / LBNL. US data-centre electricity rose from about 58 TWh in 2014 to about 176 TWh in 2023 — "
                "roughly a tripling, and accelerating with AI. These are two measured national endpoints, not an annual "
                "series; the DOE's own 2028 forecast (325–580 TWh) sits well above the line. The observed history alone "
                "already shows why grid connection, not the chip, is the emerging wall.",
        "series": [
            {"label": "US data-centre electricity", "points": [{"y": 2014, "v": 58}, {"y": 2023, "v": 176}]},
        ],
    },
    "hops": [
        {"n": "1 · Chips", "t": "accelerators, CPUs, memory and substrates — a chokepoint of their own (silicon-chip chain)"},
        {"n": "2 · Servers & network", "t": "chips integrated into boards, servers, storage and switches"},
        {"n": "3 · Facility & power", "t": "UPS, batteries, switchgear, transformers, cooling and water systems"},
        {"n": "4 · Grid & site", "t": "land, fibre, substations and transmission capacity — the binding connection"},
    ],
    "sections": [
        {"h2": "1 · The demand curve that changed the problem", "panels": [
            {"kind": "big", "h3": "US data centres", "big": "58 → 176 TWh", "conf": "measured",
             "text": "US data-centre electricity roughly tripled between 2014 and 2023, and AI is bending the curve "
                     "further up — DOE's forecast has US data centres at 325–580 TWh by 2028, or up to ~12% of national "
                     "electricity. Globally the IEA projects a rough doubling to ~950 TWh by 2030. The compute exists; "
                     "the question is where the power comes from.",
             "note": "US DOE / LBNL; IEA Energy and AI."},
            {"kind": "text", "h3": "The bottleneck moved downstream to the grid",
             "text": "Chips remain a genuine chokepoint upstream (advanced logic, HBM memory, packaging). But for the "
                     "operators building now, the gating item is a grid connection: transformers with multi-year lead "
                     "times, substation capacity and interconnection queues — exactly the constraints the grid chain "
                     "documents. AI's physical limit is increasingly the power system.",
             "flag": "see the grid and silicon-chip chains"},
        ]},
        {"h2": "2 · How wide the uncertainty really is", "panels": [
            {"kind": "cards", "h3": "2035 is a set of scenarios, not a number", "cards": [
                {"t": "Headwinds ~700 TWh", "d": "Slower AI uptake, strong efficiency gains and supply-chain friction hold data-centre electricity down."},
                {"t": "Base ~1,200 TWh", "d": "The IEA's central case for data-centre electricity in 2035 — a large but not explosive rise."},
                {"t": "Lift-off ~1,700 TWh", "d": "Rapid AI adoption with weaker efficiency pushes demand far higher. These are scenarios, not a confidence interval."},
            ]},
        ]},
        {"h2": "3 · The material layer, kept in proportion", "panels": [
            {"kind": "text", "h3": "Copper, and the chip chain behind it",
             "text": "A data centre is copper busbars and cabling, steel, aluminium, batteries for backup, and a great "
                     "deal of water for cooling — plus the semiconductors themselves. None of the bulk materials is a "
                     "unique chokepoint; the concentrated risk lives in the chip chain it sits on and in the power it "
                     "draws. The honest framing is energy-and-chips, not a new critical mineral.",
             "note": "IEA Energy and AI.", "flag": "energy + chips, not a new mineral"},
        ]},
    ],
    "trade_intro": "BACI carries servers, networking gear and processors under broad electronics headings, but a data "
                   "centre is built and operated in place — its defining input, electricity, and its binding "
                   "constraint, grid connection, are not traded goods. Read any hardware trade below as context; the "
                   "chain's real limits are power and the chip chain, not customs flows.",
    "method": [
        {"stage": "Chips", "lens": "silicon-chip chain", "why": "a real upstream chokepoint — analysed separately"},
        {"stage": "Electricity", "lens": "DOE/IEA demand history & outlook", "why": "roughly doubling by 2030 — the emerging wall"},
        {"stage": "Grid", "lens": "connection & transformer constraints", "why": "the binding limit; shared with the grid chain"},
        {"stage": "Trade", "lens": "BACI electronics headings", "why": "hardware only; power isn't a traded good — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- data centre, chip ready but power/grid is the wall; US 58->176 TWh")
