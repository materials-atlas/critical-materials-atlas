"""Evidence JSON for the heat-pump chain pilot. Uniform schema. Public sources.
Ported onto the shared chainview renderer with per-figure confidence tags. Run: python record_heat_pump.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "heat_pump_chain.json")

SRC = {
    "iea_monitor": {"title": "IEA, Heat Pump Monitor 2026 — Key findings", "year": 2026, "url": "https://www.iea.org/reports/heat-pump-monitor-2026/key-findings"},
    "iea_future": {"title": "IEA, The Future of Heat Pumps — Executive summary", "year": 2022, "url": "https://www.iea.org/reports/the-future-of-heat-pumps/executive-summary"},
    "ehpa_2025": {"title": "EHPA Market Report 2025 — Executive summary", "year": 2025, "url": "https://www.ehpa.org/wp-content/uploads/2025/07/EHPA-Market-Report-2025-executive-summary.pdf"},
    "unep_kigali": {"title": "UNEP OzonAction, HFC phase-down (Kigali Amendment) timeline", "year": 2026, "url": "https://www.unep.org/ozonaction/resources/toolkits-manuals-and-guides/path-kigali-hfc-phase-down-timeline"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Heat-pump chain",
    "related": [{"href": "../magnet-chain/magnet-chain.html", "label": "Rare-earth magnet chain"}, {"href": "../aluminium-chain/aluminium-chain.html", "label": "Aluminium chain"}],
    "accent": "#5a8a6a",
    "eyebrow": "Product-chain pilot · the box that heats the house",
    "h1": "No scarce metal gates the heat pump — people and factories do",
    "deck": "A heat pump is copper, aluminium and steel wrapped around a compressor and a refrigerant. There is no "
            "critical-mineral chokepoint. What limits it is different in kind: factory capacity, refrigerant "
            "regulation and — above all — enough trained installers to put the units in.",
    "byline": "copper & aluminium ≠ compressor ≠ refrigerant (regulated) ≠ the factory ≠ the installer",
    "correction": "Heat pumps are a rare case in this atlas with no upstream mineral chokepoint. Their constraints are "
                  "industrial and human: manufacturing capacity is distributed (China ~35%, US ~25%), the refrigerant "
                  "is being reshaped by the Kigali HFC phase-down rather than by metal supply, and the binding limit on "
                  "deployment is the installer workforce. The bottleneck is a labour market, not a mine.",
    "stats": [
        {"v": "35 / 25%", "l": "China / US share of heat-pump manufacturing capacity", "conf": "measured"},
        {"v": "installers", "l": "the binding constraint on deployment is skilled labour, not materials", "conf": "estimate"},
        {"v": "refrigerant", "l": "the Kigali HFC phase-down reshapes the chemistry — not the supply of a metal", "conf": "measured"},
        {"v": "~12%", "l": "of building space-heating met by heat pumps today — the runway is long", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Materials", "t": "copper, aluminium, steels, polymers and a refrigerant — commodity inputs"},
        {"n": "2 · Components", "t": "compressor, heat exchangers, expansion valve, fans/pumps, motor and controls"},
        {"n": "3 · Factory", "t": "units integrated to local voltage, climate and building codes — distributed capacity"},
        {"n": "4 · Install & operate", "t": "sizing, emitters, pipework, commissioning — efficiency set on site"},
    ],
    "sections": [
        {"h2": "1 · What a heat pump is made of", "panels": [
            {"kind": "text", "h3": "Commodity metals plus a compressor", "conf": "measured",
             "text": "The bulk of a heat pump is copper (windings and heat-exchanger tubing), aluminium (fins and "
                     "casing) and steel, around a compressor and a refrigerant loop. Some compressor motors use "
                     "permanent magnets — a minor link to the magnet chain — but no input is a scarcity chokepoint. It "
                     "is, materially, a fridge run in reverse.",
             "note": "IEA / EHPA component data.", "flag": "no critical-mineral gate"},
            {"kind": "text", "h3": "The refrigerant is the regulated input",
             "text": "The one input under real pressure is the refrigerant. The Kigali Amendment's HFC phase-down is "
                     "pushing the industry toward lower-warming refrigerants (propane, CO2, new blends), which changes "
                     "designs and safety rules. It is a regulatory transition, not a supply shortage — the chemistry is "
                     "being legislated, not rationed.",
             "note": "UNEP, Kigali Amendment.", "flag": "legislated, not rationed"},
        ]},
        {"h2": "2 · Manufacturing is unusually distributed", "panels": [
            {"kind": "bars", "h3": "Heat-pump manufacturing capacity by region", "conf": "measured", "max": 1.0, "note":
                "IEA. Unlike solar or batteries, heat-pump factory capacity is spread — China ~35%, the US ~25%, with "
                "Europe, Japan and Korea holding much of the rest. There is no single-country choke on making the "
                "units; the technology is mature and widely held.", "bars": [
                {"label": "China", "value": 0.35},
                {"label": "United States", "value": 0.25},
                {"label": "Rest of world", "value": 0.40},
            ]},
            {"kind": "text", "h3": "So the limit is capacity and demand, not control",
             "text": "Because no one controls a scarce input, scaling heat pumps is about building more, fairly ordinary, "
                     "factory lines and matching them to demand that swings with energy prices and subsidies. That makes "
                     "the risk a market-and-policy risk rather than a geopolitical chokepoint — a different problem from "
                     "most chains here.",
             "flag": "a market risk, not a chokepoint"},
        ]},
        {"h2": "3 · The real bottleneck is people", "panels": [
            {"kind": "text", "h3": "Installers are the scarce resource",
             "text": "With space-heating only ~12% electrified by heat pumps, the runway is enormous — and the binding "
                     "constraint on how fast it fills is the trained-installer workforce. Sizing, refrigerant handling "
                     "and hydronic integration are skilled trades, and shortages of them, not of any metal, are what "
                     "cap deployment in most markets. The chokepoint is a labour market.",
             "note": "IEA, The Future of Heat Pumps; EHPA.", "flag": "the scarce input is skilled labour"},
        ]},
    ],
    "trade_intro": "BACI carries heat pumps and air-conditioning equipment (HS 8415 / 8418 headings), but installation "
                   "— the binding constraint — is a domestic service that no trade statistic captures. Read the shares "
                   "below as equipment-trade positions, not a measure of who can actually deploy heat pumps at scale.",
    "method": [
        {"stage": "Materials", "lens": "IEA/EHPA bill of materials", "why": "commodity metals + refrigerant — no scarcity gate"},
        {"stage": "Refrigerant", "lens": "Kigali HFC phase-down", "why": "a regulatory transition, not a supply shortage"},
        {"stage": "Factory", "lens": "IEA manufacturing-capacity share", "why": "distributed (China ~35%, US ~25%) — no single choke"},
        {"stage": "Install", "lens": "installer-workforce constraint", "why": "the actual bottleneck; not visible in trade — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- heat pump, no mineral gate; bottleneck = factories + installers")
