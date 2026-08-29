"""Evidence JSON for the lead chain pilot. Uniform schema. Public sources.
The circular counter-story: the most-recycled metal runs in a loop. Run: python record_lead.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "lead_chain.json")

SRC = {
    "usgs_lead": {"title": "USGS Mineral Commodity Summaries 2026 — Lead", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-lead.pdf"},
    "ilzsg": {"title": "International Lead and Zinc Study Group — supply & use", "year": 2025, "url": "https://www.ilzsg.org/"},
    "who_lead": {"title": "WHO — lead poisoning and informal battery recycling", "year": 2023, "url": "https://www.who.int/news-room/fact-sheets/detail/lead-poisoning-and-health"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Lead chain",
    "chokepoint": {"product": "Lead-acid batteries", "stage": "Recycling loop", "mechanism": "diffuse", "physics": "~60% of lead is recycled from spent batteries, locally — a closed loop, not a geographic chokepoint", "holder": "—", "share": "—", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../battery-chain/battery-chain", "label": "Lithium-ion battery chain"}, {"href": "../zinc-chain/zinc-chain", "label": "Zinc chain"}, {"href": "../sulfur-chain/sulfur-chain", "label": "Sulfur / sulfuric-acid chain"}],
    "accent": "#6a6a6a",
    "eyebrow": "Product-chain pilot · the circular metal",
    "h1": "The most-recycled metal runs in a loop, not a chokepoint",
    "deck": "Lead is toxic, unglamorous and everywhere — and it is the atlas's clearest circular story. More than half "
            "of the world's lead supply is secondary, recycled almost entirely from spent lead-acid batteries, close "
            "to where they are used. The lead-acid battery still starts nearly every vehicle and backs up telecoms and "
            "power. There is no geographic chokepoint; the constraint is the loop and its safety.",
    "byline": "primary ore ≠ smelting ≠ lead-acid battery ≠ spent battery → recycled lead (the loop closes locally)",
    "correction": "Lead breaks the atlas's usual pattern by not having a chokepoint at all — for the opposite reason to "
                  "cement. Cement is too cheap to concentrate; lead is too recyclable. Around 60% of lead supply is "
                  "recycled, overwhelmingly from lead-acid batteries, and that recycling happens locally because spent "
                  "batteries are heavy and hazardous to ship. Lead's real problem is not supply security but toxicity: "
                  "informal, unregulated recycling poisons communities, which is where the risk actually lies.",
    "stats": [
        {"v": "~60% recycled", "l": "lead is the most-recycled metal — a largely closed loop", "conf": "measured"},
        {"v": "~85% batteries", "l": "of lead goes into lead-acid batteries — cars, backup, industrial storage", "conf": "measured"},
        {"v": "local loop", "l": "spent batteries are recycled near where used — no geographic chokepoint", "conf": "measured"},
        {"v": "toxicity", "l": "the real risk is informal recycling and lead poisoning, not scarcity", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Primary", "t": "lead ore (galena), often with zinc/silver — China, Australia, Peru"},
        {"n": "2 · Battery", "t": "refined lead into lead-acid batteries — starter, backup, industrial"},
        {"n": "3 · Collect", "t": "spent batteries collected — heavy, hazardous, so handled locally"},
        {"n": "4 · Secondary", "t": "smelted back to lead and returned to new batteries — the loop closes"},
    ],
    "sections": [
        {"h2": "1 · A metal that mostly recycles itself", "panels": [
            {"kind": "big", "h3": "How lead is supplied", "big": "~60% recycled", "conf": "measured",
             "text": "More than half of the world's lead comes from recycling, not mining — the highest recycled "
                     "content of any major metal. The reason is the lead-acid battery: it is a standardised, easily "
                     "collected product whose lead is fully recoverable, and the economics of recovery are strong. So "
                     "lead supply is dominated by a circular flow, with primary mining topping up demand growth rather "
                     "than carrying it.",
             "note": "USGS Lead 2026; ILZSG."},
            {"kind": "text", "h3": "And the loop is local",
             "text": "Spent batteries are heavy, and shipping hazardous waste across borders is restricted, so lead "
                     "recycling happens close to where batteries are used. That locality is exactly why there is no "
                     "chokepoint: no single country controls the supply, because most of it circulates within regions. "
                     "It is the mirror image of a concentrated chain.",
             "flag": "the loop closes near demand"},
        ]},
        {"h2": "2 · Still the workhorse battery", "panels": [
            {"kind": "text", "h3": "Lead-acid isn't going away", "conf": "measured",
             "text": "Roughly 85% of lead goes into lead-acid batteries. Even as lithium-ion takes over traction and "
                     "storage, nearly every vehicle — including electric ones — keeps a lead-acid battery for starting "
                     "and low-voltage systems, and lead-acid still dominates backup power for telecoms, data centres "
                     "and grids. Cheap, safe, recyclable and reliable, it persists alongside the newer chemistry (see "
                     "the battery chain), not against it.",
             "note": "ILZSG; USGS.", "flag": "the quiet, durable battery"},
        ]},
        {"h2": "3 · The real risk: toxicity, not supply", "panels": [
            {"kind": "text", "h3": "Where lead actually hurts",
             "text": "Lead's danger is health, not scarcity. Formal recycling is clean and closed, but a large share of "
                     "used batteries in lower-income countries is broken down in informal, unregulated operations that "
                     "expose workers and whole communities — the WHO links used lead-acid battery recycling to "
                     "widespread lead poisoning. The 'so what' for lead is regulation and safe collection, a public-"
                     "health decision layer rather than a supply-security one.",
             "note": "WHO.", "flag": "a health chokepoint, not a supply one"},
        ]},
    ],
    "trade_intro": "BACI carries lead ores (260700) and unwrought lead including secondary (780110, 780199), but the "
                   "dominant flow — spent batteries recycled locally — barely crosses borders, so trade captures only "
                   "the primary and refined margin. Read the shares below as that margin, not the circular loop that "
                   "defines lead.",
    "method": [
        {"stage": "Primary", "lens": "USGS mine share", "why": "tops up demand; not the main supply or a chokepoint"},
        {"stage": "Recycling", "lens": "secondary share (~60%)", "why": "the dominant, local, closed loop"},
        {"stage": "Use", "lens": "lead-acid battery share", "why": "~85% batteries — the durable workhorse"},
        {"stage": "Trade", "lens": "BACI 260700 ore + 780110/780199 lead", "why": "primary/refined margin; the loop is local — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- lead, ~60pct recycled (local loop, no chokepoint); toxicity is the risk")
