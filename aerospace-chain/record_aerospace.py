"""Evidence JSON for the unpublished aerospace / jet-engine superalloy chain pilot.
Uniform chain schema (shared renderer). Public sources. Rhenium/qualified-titanium and
single-crystal casting are snapshot-only in public data — marked as such, not padded into
a false series. Run: python record_aerospace.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "aerospace_chain.json")

SRC = {
    "usgs_rhenium": {"title": "USGS Mineral Commodity Summaries 2026 — Rhenium", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-rhenium.pdf"},
    "usgs_titanium": {"title": "USGS Mineral Commodity Summaries 2025 — Titanium and Titanium Dioxide", "year": 2025, "url": "https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-titanium.pdf"},
    "argus_ti": {"title": "Argus, Aerospace-approved Ti sponge supply up in 2024", "year": 2025, "url": "https://www.argusmedia.com/en/news-and-insights/latest-market-news/2659047-aerospace-approved-ti-sponge-supply-up-in-2024"},
    "market_engines": {"title": "Commercial aircraft engine market analyses (Mordor Intelligence; Simple Flying), 2024", "year": 2024, "url": "https://www.mordorintelligence.com/industry-reports/commercial-aircraft-engines-market", "note": "Secondary market analyses; OEM shares approximate and vary by segment/metric."},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Aerospace / jet-engine superalloy chain",
    "related": [{"href": "../titanium-chain/titanium-chain.html", "label": "Titanium chain"}, {"href": "../pgm-catalyst-chain/pgm-catalyst-chain.html", "label": "PGM / catalyst chain"}, {"href": "../defence-chain/defence-chain.html", "label": "Defence chain"}],
    "accent": "#35617f",
    "eyebrow": "Product-chain pilot · aerospace propulsion",
    "h1": "A jet engine's bottleneck is not the ore",
    "deck": "A large jet engine turns nickel, cobalt, rhenium, hafnium and titanium into superalloys, then "
            "single-crystal turbine blades, then a finished engine. At every step downstream the supply gets "
            "<i>narrower</i> — the mine is the least concentrated stage of all.",
    "byline": "rhenium (by-product) ≠ titanium sponge ≠ aerospace-qualified metal ≠ blade casting ≠ jet engine",
    "correction": "A 'critical minerals' list reads the risk at the mine. But Chile's rhenium is a copper by-product "
                  "no one mines for; China makes ~71% of titanium sponge yet almost none is aerospace-qualified; "
                  "single-crystal blade casting is held by a handful of firms; and three Western groups build nearly "
                  "every large engine. The chokepoint walks downstream.",
    "stats": [
        {"v": "~81 t", "l": "world rhenium output per year (a copper by-product)", "conf": "measured"},
        {"v": "55%", "l": "of rhenium mine production is Chile", "conf": "measured"},
        {"v": "~71%", "l": "of titanium sponge is China — little of it aerospace-qualified", "conf": "measured"},
        {"v": "55 / 26 / 18", "l": "engine share: GE · Pratt &amp; Whitney · Rolls-Royce (%)", "conf": "estimate"},
    ],
    "hops": [
        {"n": "1 · Rhenium", "t": "the scarce superalloy element — a copper by-product, ~55% Chile"},
        {"n": "2 · Titanium sponge", "t": "production (China) vs aerospace qualification (Japan/Russia/Kazakhstan)"},
        {"n": "3 · Blade casting", "t": "single-crystal superalloy blades — a few firms, no country series"},
        {"n": "4 · Jet engine", "t": "GE, Pratt & Whitney, Rolls-Royce — the most concentrated stage"},
    ],
    "sections": [
        {"h2": "1 · Rhenium — the metal that makes the blade, and the one you can't scale", "panels": [
            {"kind": "bars", "h3": "Where rhenium goes", "conf": "measured", "max": 1.0, "note":
                "USGS. ~80% of rhenium is used in superalloys for high-temperature turbine parts; single-crystal blades "
                "depend on it for creep strength.", "bars": [
                {"label": "Superalloys", "value": 0.80},
                {"label": "Petroleum-reforming catalysts", "value": 0.15},
                {"label": "Other", "value": 0.05},
            ]},
            {"kind": "big", "h3": "Where it comes from", "big": "55% Chile", "conf": "measured",
             "text": "of world mine production, as a by-product of porphyry-copper molybdenum. World output is only "
                     "~81 tonnes a year and cannot be scaled without scaling copper. Secondary (recycled) rhenium is "
                     "led by the US and Germany — a downstream, not a mine, capability.",
             "note": "USGS MCS 2026 (world ~81 t in 2025)."},
        ]},
        {"h2": "2 · Titanium — production is not the same as aerospace-qualified supply", "panels": [
            {"kind": "bars", "h3": "Titanium-sponge production", "conf": "measured", "max": 0.75, "note":
                "USGS. China dominates tonnage, but Chinese sponge is largely not qualified for critical aerospace "
                "parts — so this map overstates aerospace security.", "bars": [
                {"label": "China (2024)", "value": 0.71},
                {"label": "Japan (2022)", "value": 0.17},
                {"label": "Russia (2022)", "value": 0.13},
            ]},
            {"kind": "bars", "h3": "Where the US buys aerospace sponge", "conf": "measured", "max": 0.85, "note":
                "USGS. The US has no domestic sponge and imports the aerospace-grade metal from a narrow allied base — "
                "Japan above all. Qualification, not tonnage, is the chokepoint.", "bars": [
                {"label": "Japan", "value": 0.80},
                {"label": "Saudi Arabia", "value": 0.13},
                {"label": "Kazakhstan", "value": 0.09},
            ]},
        ]},
        {"h2": "3 · Single-crystal blade casting — the capability, not the country", "panels": [
            {"kind": "text", "h3": "Cast, not mined", "conf": "snapshot",
             "text": "Casting nickel-superalloy single-crystal blades (directional solidification, hafnium/rhenium-"
                     "bearing) is a low-yield, capital- and know-how-intensive stage held by a handful of firms and "
                     "engine OEMs — specialist casters (e.g. Precision Castparts, Doncasters) and OEM foundries in the "
                     "US, UK, France and Japan, with China developing capability. No public country-production series "
                     "exists; company control is the right lens.",
             "note": "Company/industry disclosures; no public longitudinal series — shown as a single-vintage read.",
             "flag": "measured in firms, not countries"},
        ]},
        {"h2": "4 · Jet engines — the most concentrated stage of all", "panels": [
            {"kind": "bars", "h3": "Commercial engine makers (overall share)", "conf": "estimate", "max": 0.6, "note":
                "Narrow-body: CFM (GE+Safran) >60%, Pratt & Whitney ~35%. Wide-body: GE and Rolls-Royce split the "
                "field. Approximate shares from secondary market analyses.", "bars": [
                {"label": "GE Aerospace (+CFM)", "value": 0.55},
                {"label": "Pratt & Whitney", "value": 0.26},
                {"label": "Rolls-Royce", "value": 0.18},
            ]},
            {"kind": "big", "h3": "A three-firm oligopoly", "big": "$81.0B", "conf": "estimate",
             "text": "commercial aircraft-engine market, 2024. Essentially every large engine is built by GE Aerospace "
                     "(with its CFM joint venture), Pratt & Whitney and Rolls-Royce.",
             "note": "Secondary market analyses; shares vary by segment and metric."},
        ]},
    ],
    "trade_intro": "BACI gives a consistent 2002–2024 monetary lens on the traded forms, but it cannot see aerospace "
                   "qualification, single-crystal castings, captive transfers inside an OEM, or rhenium (which has no "
                   "clean HS6 line). Read the table as availability of the traded good, not who makes the engine.",
    "method": [
        {"stage": "Rhenium", "lens": "USGS production", "why": "no clean HS6 line — read from production, not trade"},
        {"stage": "Titanium", "lens": "production vs aerospace qualification", "why": "tonnage ≠ qualified aerospace supply"},
        {"stage": "Casting", "lens": "company capability (snapshot)", "why": "no public country series; firms, not countries"},
        {"stage": "Engines", "lens": "OEM market share", "why": "a three-firm oligopoly; the finished-machine chokepoint"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "— aerospace (uniform schema), rhenium 81 t/Chile 55%, engines 55/26/18")
