"""Evidence JSON for the baryte / drilling-mud chain pilot. Uniform schema. Public sources.
The invisible mineral you can't drill without. Run: python record_baryte.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "baryte_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_baryte": {"title": "USGS Mineral Commodity Summaries 2026 — Barite", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-barite.pdf"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — barytes", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "api_mud": {"title": "American Petroleum Institute — drilling-fluid (mud) specifications", "year": 2024, "url": "https://www.api.org/"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Baryte / drilling-mud chain",
    "chokepoint": {"product": "Oil & gas drilling mud", "stage": "Mine", "mechanism": "diffuse", "physics": "A cheap, heavy, abundant weighting mineral mined near demand (India/China/Morocco) — no chokepoint, but you can't drill without it", "holder": "India · China · Morocco", "share": "—", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../sulfur-chain/sulfur-chain", "label": "Sulfur / sulfuric-acid chain"}, {"href": "../copper-chain/copper-chain", "label": "Copper chain"}, {"href": "../ammonia-chain/ammonia-chain", "label": "Ammonia / nitrogen chain"}],
    "accent": "#7a7a6a",
    "eyebrow": "Product-chain pilot · the mineral in the mud",
    "h1": "You can't drill an oil or gas well without this invisible mineral",
    "deck": "Baryte — barium sulfate — is one of the most-used minerals almost no one has heard of. Ground to a "
            "powder, its exceptional density is what weights drilling mud, holding back the pressure in an oil or gas "
            "well so it does not blow out. Most baryte on Earth goes into that mud. It is cheap, heavy, mined in many "
            "countries — and utterly essential.",
    "byline": "baryte ore (India/China/Morocco) ≠ ground drilling-grade powder ≠ weighted drilling mud ≠ the well",
    "correction": "Baryte is the opposite of a glamorous critical mineral, and that is the point. It has no severe "
                  "chokepoint — it is abundant and mined across India, China, Morocco, Kazakhstan and the US — yet "
                  "without it you cannot safely drill. Its extreme density (about 4.5 times water) makes it the "
                  "weighting agent in drilling fluid, controlling downhole pressure, and there is no cheap substitute. "
                  "Demand rises and falls with drilling activity; the risk is not concentration but that an essential "
                  "input is invisible until it is short.",
    "stats": [
        {"v": "drilling mud", "l": "most baryte weights oil & gas drilling fluid — it controls well pressure", "conf": "measured"},
        {"v": "no substitute", "l": "its density (~4.5× water) has no cheap replacement in mud", "conf": "measured"},
        {"v": "diversified", "l": "India, China, Morocco, Kazakhstan and the US mine it — no single chokepoint", "conf": "measured"},
        {"v": "invisible", "l": "essential to every well, yet almost never discussed", "conf": "measured"},
    ],
    "history": {
        "title": "A diversified mine, 2019 → 2024",
        "conf": "measured",
        "note": "BGS/USGS mine production, from the atlas's own data (the reliable public series is short). India, "
                "China and Morocco lead, with Kazakhstan, the US and others contributing — no single country "
                "dominates. That spread is exactly why baryte is a 'diffuse' chain: it is essential but not "
                "concentrated, so its supply story is about drilling demand and logistics, not a chokepoint.",
        "series": [
            {"label": "India", "points": hist_points("baryte", "IN")},
            {"label": "China", "points": hist_points("baryte", "CN")},
            {"label": "Morocco", "points": hist_points("baryte", "MA")},
        ],
    },
    "hops": [
        {"n": "1 · Mine", "t": "baryte (barium sulfate) ore — India, China, Morocco, Kazakhstan, US"},
        {"n": "2 · Grind", "t": "milled to API drilling-grade powder of controlled density and purity"},
        {"n": "3 · Drilling mud", "t": "added to fluid as the weighting agent that controls downhole pressure"},
        {"n": "4 · The well", "t": "oil & gas drilling — plus barium chemicals, filler, and medical 'barium meals'"},
    ],
    "sections": [
        {"h2": "1 · Why every well needs it", "panels": [
            {"kind": "big", "h3": "The weighting agent", "big": "drilling mud", "conf": "measured",
             "text": "As a drill bit goes down, the fluid pumped through it must be heavy enough to counter the pressure "
                     "of oil, gas and water in the rock, or the well blows out. Baryte, ground fine, gives the mud that "
                     "weight without making it too thick — its density is the whole point. Roughly the vast majority of "
                     "world baryte is consumed this way, which ties its demand directly to drilling activity.",
             "note": "USGS Barite 2026; API."},
            {"kind": "text", "h3": "No substitute at the price",
             "text": "Alternatives (ilmenite, haematite) exist for special cases, but nothing matches baryte's "
                     "combination of high density, low cost, chemical inertness and abundance for routine drilling. So "
                     "even though baryte is cheap and unglamorous, it is functionally irreplaceable in the mud — a "
                     "quiet, essential dependency of the entire oil-and-gas industry (and of the sulfur and ammonia "
                     "chains that ride on it).",
             "flag": "cheap, inert, irreplaceable"},
        ]},
        {"h2": "2 · Diffuse by nature", "panels": [
            {"kind": "text", "h3": "Abundant and spread out", "conf": "measured",
             "text": "Baryte deposits are common and mined in many countries, and drilling-grade powder is produced "
                     "regionally near where wells are drilled, because the mineral is cheap and heavy to ship. There is "
                     "no single-country chokepoint and no export lever — it is the diffuse case, like cement: essential, "
                     "but nothing forces it to concentrate. The supply concern is quality and local availability, not "
                     "geopolitics.",
             "note": "BGS/USGS.", "flag": "essential, not concentrated"},
        ]},
        {"h2": "3 · The other lives of barium", "panels": [
            {"kind": "text", "h3": "Beyond the mud",
             "text": "A smaller share of baryte becomes barium chemicals (for pigments, glass, electronics and "
                     "specialty applications), a filler in paints and plastics, and — medically — the 'barium meal' "
                     "that makes the gut visible on X-rays, since barium is opaque to them. But the mineral's strategic "
                     "weight, literally and figuratively, is in the drilling mud that keeps wells under control.",
             "flag": "chemicals, filler, X-ray contrast"},
        ]},
    ],
    "trade_intro": "BACI carries natural baryte (251110) and witherite (251120), a cheap, heavy mineral traded "
                   "regionally near drilling demand. Read the shares below as that raw-mineral trade — the diversified "
                   "mine map is visible here, which is precisely the point: there is no chokepoint to find.",
    "method": [
        {"stage": "Mine", "lens": "USGS/BGS mine share + history", "why": "diversified (India/China/Morocco) — no chokepoint"},
        {"stage": "Use", "lens": "drilling-mud demand", "why": "the vast majority of baryte; irreplaceable weighting agent"},
        {"stage": "Character", "lens": "diffuse vs concentrated", "why": "essential but spread — a 'diffuse' chain"},
        {"stage": "Trade", "lens": "BACI 251110/251120 baryte", "why": "raw mineral, traded regionally — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- baryte, drilling-mud weighting agent; diversified (diffuse), no substitute")
