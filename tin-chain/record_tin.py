"""Evidence JSON for the tin / solder chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_tin.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "tin_chain.json")

SRC = {
    "usgs_tin": {"title": "USGS Mineral Commodity Summaries 2026 — Tin", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-tin.pdf"},
    "ita": {"title": "International Tin Association — use and supply data", "year": 2025, "url": "https://www.internationaltin.org/tin-use-survey/"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — tin mine production", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Tin / solder chain",
    "published": True,
    "related": [{"href": "../tantalum-chain/tantalum-chain.html", "label": "Tantalum chain"}, {"href": "../silicon-chip/silicon-chain.html", "label": "Silicon-chip chain"}],
    "accent": "#5a6a7a",
    "eyebrow": "Product-chain pilot · the metal that joins everything",
    "h1": "Nothing electronic works without the metal almost no one thinks about",
    "deck": "Tin is the quiet keystone of electronics: about half of it becomes solder, the alloy that joins every "
            "component to every circuit board. Its supply is concentrated and, at the mine, entangled with conflict — "
            "Indonesia, Myanmar's Wa State and the DR Congo — while refining sits mostly in China and Indonesia.",
    "byline": "cassiterite (concentrated, conflict-linked) ≠ refined tin (China/Indonesia) ≠ solder ≠ every circuit board",
    "correction": "Tin never makes the headline critical-materials lists, yet no phone, server or car computer works "
                  "without it — roughly half of tin is solder, the joint in every electronic assembly. The exposure is "
                  "twofold: supply is concentrated in China and Indonesia, and a large swing feed comes from Myanmar's "
                  "Wa State, which suspended mining in 2023 — plus tin is a '3TG' conflict mineral tied to the DR "
                  "Congo. A humble metal gates all electronics.",
    "stats": [
        {"v": "~half", "l": "of world tin demand is solder — the joint in every circuit board", "conf": "measured"},
        {"v": "CN + ID", "l": "China and Indonesia lead both mining and refining", "conf": "measured"},
        {"v": "Wa 2023", "l": "Myanmar's Wa State — a major feed to China — suspended tin mining in 2023", "conf": "measured"},
        {"v": "3TG", "l": "a conflict mineral (tin, tantalum, tungsten, gold) tied to the DR Congo", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Mine", "t": "cassiterite (tin oxide) — China, Indonesia, Myanmar (Wa), Peru, Bolivia, DR Congo"},
        {"n": "2 · Smelt & refine", "t": "concentrate → refined tin metal — mostly China and Indonesia"},
        {"n": "3 · Solder & tinplate", "t": "solder alloys (~half of use), tinplate for cans, chemicals, brass/bronze"},
        {"n": "4 · Electronics", "t": "solder joins chips, boards and components — the invisible glue of every device"},
    ],
    "sections": [
        {"h2": "1 · The metal inside every device", "panels": [
            {"kind": "big", "h3": "The dominant use", "big": "~half is solder", "conf": "measured",
             "text": "About half of all tin becomes solder — the fusible alloy that electrically and mechanically "
                     "joins components to printed circuit boards. Lead-free solder (still tin-based) made tin's role "
                     "bigger, not smaller. Whatever else a supply-chain analysis of electronics covers — chips, "
                     "magnets, copper — none of it functions until tin joins it together.",
             "note": "International Tin Association: solder is the largest end use."},
            {"kind": "text", "h3": "And the other uses keep it strategic",
             "text": "Beyond solder, tin coats steel as tinplate for food cans, alloys into bronze and brass, and goes "
                     "into chemicals and (increasingly) lithium-ion battery materials. It is one of the few metals used "
                     "across food packaging, construction and every branch of electronics at once — which is why a "
                     "supply shock propagates widely.",
             "flag": "electronics, cans and alloys at once"},
        ]},
        {"h2": "2 · Concentrated — and conflict-linked", "panels": [
            {"kind": "text", "h3": "China, Indonesia, and the Wa swing", "conf": "measured",
             "text": "China and Indonesia dominate both mining and refining, but China leans on imported concentrate — "
                     "much of it from the Wa State, a semi-autonomous region of Myanmar that abruptly suspended tin "
                     "mining in August 2023, tightening the market. A large share of world tin thus flows through "
                     "politically fragile channels that a customs map does not show.",
             "note": "USGS MCS 2026; BGS.", "flag": "a swing supplier outside normal governance"},
            {"kind": "text", "h3": "A 3TG conflict mineral",
             "text": "Tin is one of the '3TG' minerals (with tantalum, tungsten and gold) covered by conflict-mineral "
                     "due-diligence rules because artisanal mining in the DR Congo and neighbours has funded armed "
                     "groups. So tin carries a compliance and ethical dimension on top of its concentration risk — the "
                     "same conflict-mineral frame as tantalum in the electronics it ultimately serves.",
             "flag": "due-diligence, not just supply"},
        ]},
        {"h2": "3 · Why there's no easy substitute", "panels": [
            {"kind": "text", "h3": "Solder is hard to replace, recycling only partial",
             "text": "Conductive adhesives and other joining methods exist but have not displaced solder for mainstream "
                     "electronics assembly, so the tin dependence persists. Recovery from electronic scrap helps and is "
                     "growing, but the dispersed, tiny quantities of tin in each device make recycling only a partial "
                     "relief. The keystone stays a keystone.",
             "flag": "substitutes researched, not adopted"},
        ]},
    ],
    "trade_intro": "BACI carries tin ores/concentrates and unwrought tin metal, but not solder or the tin inside "
                   "finished electronics, and customs origin for refined tin is the smelter, not the (sometimes "
                   "conflict-linked) mine behind it. Read the shares below as the traded raw and refined forms, not "
                   "the true origin of the ore.",
    "method": [
        {"stage": "Mine", "lens": "USGS/BGS mine share", "why": "concentrated; Wa/Myanmar feed is a governance risk"},
        {"stage": "Refine", "lens": "USGS refined-tin share", "why": "mostly China and Indonesia"},
        {"stage": "Use", "lens": "ITA end-use survey", "why": "~half solder — the electronics chokepoint"},
        {"stage": "Trade", "lens": "BACI 2609 ores + 800110 unwrought tin", "why": "smelter origin, not the mine — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- tin, ~half solder; concentrated + conflict-linked (Wa/3TG)")
