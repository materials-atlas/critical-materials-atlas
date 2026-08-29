"""Evidence JSON for the bismuth chain pilot. Uniform schema. Public sources.
The non-toxic heavy metal replacing lead. Run: python record_bismuth.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "bismuth_chain.json")

SRC = {
    "usgs_bismuth": {"title": "USGS Mineral Commodity Summaries 2026 — Bismuth", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-bismuth.pdf"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — bismuth", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "ec_crm": {"title": "European Commission, Critical Raw Materials 2023 — bismuth", "year": 2023, "url": "https://single-market-economy.ec.europa.eu/sectors/raw-materials/areas-specific-interest/critical-raw-materials_en"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Bismuth chain",
    "chokepoint": {"product": "Non-toxic lead replacement · pharma", "stage": "Recovery (lead/tungsten)", "mechanism": "byproduct", "physics": "A by-product of lead and tungsten smelting; China ~88% of production and refining — coupled to hosts, and China dominates the refining", "holder": "China", "share": "~88%", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../lead-chain/lead-chain", "label": "Lead chain"}, {"href": "../tungsten-chain/tungsten-chain", "label": "Tungsten chain"}, {"href": "../tin-chain/tin-chain", "label": "Tin / solder chain"}],
    "accent": "#5a7a6a",
    "eyebrow": "Product-chain pilot · the safe heavy metal",
    "h1": "The non-toxic heavy metal that replaces lead — and China makes most of it",
    "deck": "Bismuth is the oddity of the heavy metals: dense like lead, but remarkably non-toxic — so it is the go-to "
            "replacement as lead is regulated out of plumbing, alloys, ammunition and fishing weights. It is also the "
            "'bismol' in stomach remedies and the shimmer in cosmetics. It comes as a by-product of lead and tungsten "
            "smelting, and China produces around 88% of it.",
    "byline": "lead / tungsten smelting ≠ by-product bismuth (China ~88%) ≠ fusible alloys · free-machining · pharma · pigment",
    "correction": "Bismuth's appeal is exactly that it is a safe heavy metal, which makes it the standard non-toxic "
                  "substitute for lead in drinking-water brass, free-machining steel and brass, shot and sinkers. It is "
                  "recovered as a by-product of lead and tungsten smelting, and China dominates both production and "
                  "refining at roughly 88%. So the metal the world reaches for to get away from toxic lead is itself "
                  "concentrated in one supplier — and its demand rises precisely as lead is phased out.",
    "stats": [
        {"v": "lead replacement", "l": "non-toxic bismuth replaces lead in plumbing, alloys, shot and sinkers", "conf": "measured"},
        {"v": "~88% China", "l": "of world bismuth production and refining", "conf": "measured"},
        {"v": "by-product", "l": "recovered from lead and tungsten smelting — can't scale on its own", "conf": "measured"},
        {"v": "pharma + pigment", "l": "bismuth subsalicylate (stomach remedies) and pearlescent cosmetics", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Host smelting", "t": "lead and tungsten smelting carry bismuth as a by-product — China-led"},
        {"n": "2 · Refine", "t": "bismuth separated and refined to metal and compounds — ~88% China"},
        {"n": "3 · Alloys & compounds", "t": "fusible/free-machining alloys, bismuth subsalicylate, bismuth oxide/pigment"},
        {"n": "4 · End use", "t": "lead-free plumbing & alloys, ammunition, pharma, cosmetics, fire-sprinkler links"},
    ],
    "sections": [
        {"h2": "1 · A safe substitute — with a catch", "panels": [
            {"kind": "big", "h3": "Why bismuth replaces lead", "big": "non-toxic", "conf": "measured",
             "text": "Bismuth is nearly as dense as lead but is not a cumulative poison, so as regulations push lead out "
                     "of anything that touches water, food or people, bismuth steps in: lead-free brass for potable-"
                     "water fittings, free-machining steel and brass (bismuth improves machinability like lead did), "
                     "non-toxic shot and fishing sinkers, and low-melting 'fusible' alloys for fire-sprinkler links and "
                     "safety devices. Its whole value proposition is being the harmless heavy metal.",
             "note": "USGS Bismuth 2026; EC CRM 2023."},
            {"kind": "text", "h3": "The catch: it's ~88% China",
             "text": "The awkwardness is that the metal chosen to escape toxic lead is itself a concentrated dependency: "
                     "China produces and refines roughly 88% of world bismuth, as a by-product of its lead and tungsten "
                     "industries. So a health-and-safety substitution creates a supply-concentration exposure, and "
                     "bismuth demand grows exactly as lead phase-outs advance.",
             "flag": "swap toxicity for concentration"},
        ]},
        {"h2": "2 · The medicine-cabinet metal", "panels": [
            {"kind": "text", "h3": "From upset stomachs to eyeshadow", "conf": "measured",
             "text": "Bismuth subsalicylate is the active ingredient in familiar stomach remedies, and bismuth "
                     "oxychloride gives the pearlescent shimmer in cosmetics. Bismuth compounds also appear in some "
                     "pharmaceuticals and pigments. These are small, high-value uses that, with the alloys, make "
                     "bismuth quietly ubiquitous in daily life — another everyday dependency the atlas surfaces.",
             "note": "USGS.", "flag": "quietly everywhere"},
        ]},
        {"h2": "3 · A by-product, so hard to secure", "panels": [
            {"kind": "text", "h3": "You can't just make more",
             "text": "As a by-product of lead and tungsten, bismuth output is set by those metals' economics and by "
                     "China's dominant smelting, not by bismuth demand — the same coupling as gallium or tellurium. "
                     "Diversifying means recovering bismuth at non-Chinese lead and tungsten operations, a slow, "
                     "incentive-driven change, while recycling from alloys is limited by how dispersed the uses are. "
                     "The safe metal has an unsafe supply structure.",
             "flag": "coupled supply, one dominant refiner"},
        ]},
    ],
    "trade_intro": "BACI carries bismuth and its articles (810600), where China's production and refining dominance "
                   "shows, though much bismuth also moves embedded in alloys and finished goods. Read the shares below "
                   "as the traded metal — the by-product origin (lead/tungsten) is not visible in this line.",
    "method": [
        {"stage": "Source", "lens": "USGS by-product recovery", "why": "a lead/tungsten by-product — can't scale alone"},
        {"stage": "Refine", "lens": "USGS/EC production share", "why": "~88% China — the concentration"},
        {"stage": "Use", "lens": "lead-replacement + pharma", "why": "demand grows as lead is phased out"},
        {"stage": "Trade", "lens": "BACI 810600 bismuth", "why": "traded metal; by-product origin not visible — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- bismuth, non-toxic lead replacement; ~88pct China by-product of lead/tungsten")
