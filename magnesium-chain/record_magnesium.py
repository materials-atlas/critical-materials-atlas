"""Evidence JSON for the magnesium chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_magnesium.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "magnesium_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_magnesium": {"title": "USGS Mineral Commodity Summaries 2026 — Magnesium Metal", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-magnesium-metal.pdf"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — magnesium metal production", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "ec_crm": {"title": "European Commission, Study on the Critical Raw Materials for the EU 2023", "year": 2023, "url": "https://single-market-economy.ec.europa.eu/sectors/raw-materials/areas-specific-interest/critical-raw-materials_en"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Magnesium chain",
    "chokepoint": {"product": "Aluminium alloys", "stage": "Reduction", "mechanism": "thermodynamic", "physics": "Coal-fired Pidgeon retorts, energy-sited in one Chinese province", "holder": "China", "share": "~87%", "control": "—", "conf": "estimate"},
    "published": True,
    "related": [{"href": "../aluminium-chain/aluminium-chain.html", "label": "Aluminium chain"}, {"href": "../steel-chain/steel-chain.html", "label": "Primary / green-steel chain"}],
    "accent": "#8a7a5a",
    "eyebrow": "Product-chain pilot · the metal that lightens the others",
    "h1": "One country makes almost all the magnesium — and once switched it off",
    "deck": "Magnesium is the lightest structural metal, but you rarely see it alone: its main jobs are to alloy "
            "aluminium (every drink can and much of a car body needs it) and to die-cast light parts. China makes "
            "roughly 85–90% of the world's primary magnesium — and in 2021 an energy crunch cut that output, leaving "
            "European industry weeks from running out.",
    "byline": "dolomite/magnesite ≠ Pidgeon reduction (coal, ~87% China) ≠ magnesium metal ≠ aluminium alloy & die-cast parts",
    "correction": "Magnesium is one of the most single-sourced metals in this atlas: China produces ~87% of primary "
                  "magnesium, most via the coal-fired Pidgeon process clustered in Shaanxi. It is also nearly "
                  "unsubstitutable in its main role — you cannot make most aluminium alloys (cans, autos, aerospace) "
                  "without a little magnesium. When Chinese energy curbs cut magnesium output in late 2021, European "
                  "carmakers and smelters were within weeks of a shortage, with almost no alternative supply.",
    "stats": [
        {"v": "~87%", "l": "China's share of world primary magnesium production", "conf": "estimate"},
        {"v": "aluminium alloy", "l": "magnesium's biggest job — alloying aluminium and die-casting", "conf": "measured"},
        {"v": "2021 shock", "l": "China's energy curbs cut output; Europe was weeks from a shortage", "conf": "measured"},
        {"v": "coal-fired", "l": "most magnesium is made by the energy-intensive Pidgeon process", "conf": "measured"},
    ],
    "history": {
        "title": "A near-monopoly that held: China's magnesium share, 2019 → 2023",
        "conf": "measured",
        "note": "BGS/USGS mine/metal production, from the atlas's own data (the reliable public series is short). "
                "China's share of primary magnesium sat around 85–88% across the window, with only scattered small "
                "producers (Russia, Kazakhstan, Israel, Brazil) elsewhere. It is one of the most concentrated single "
                "metals in the whole atlas — which is why a domestic Chinese energy decision became a global supply "
                "event.",
        "series": [
            {"label": "China", "points": hist_points("magnesium", "CN")},
            {"label": "Russia", "points": hist_points("magnesium", "RU")},
            {"label": "Kazakhstan", "points": hist_points("magnesium", "KZ")},
        ],
    },
    "hops": [
        {"n": "1 · Feedstock", "t": "dolomite or magnesite ore (also seawater/brine routes) — widely available"},
        {"n": "2 · Reduce", "t": "Pidgeon process: silicothermic reduction, coal-fired — ~87% China (Shaanxi)"},
        {"n": "3 · Magnesium metal", "t": "ingots and alloys of the lightest structural metal"},
        {"n": "4 · End use", "t": "alloying aluminium, die-cast auto/electronics parts, desulphurising steel"},
    ],
    "sections": [
        {"h2": "1 · Among the most single-sourced metals here", "panels": [
            {"kind": "big", "h3": "China's share", "big": "~87%", "conf": "estimate",
             "text": "Most of the world's magnesium is made in China by the Pidgeon process — reducing dolomite with "
                     "ferrosilicon in coal-fired retorts, concentrated in Shaanxi province. The feedstock (dolomite, "
                     "magnesite, even seawater) is abundant everywhere, so this is not a geological monopoly but an "
                     "industrial one: China built the cheap, if dirty, capacity and others exited.",
             "note": "USGS Magnesium Metal 2026."},
            {"kind": "text", "h3": "Built, therefore rebuildable — slowly",
             "text": "Because the concentration is industrial, not geological, magnesium is in principle rebuildable "
                     "elsewhere — and the 2021 shock spurred plans in the US, Europe and elsewhere. But magnesium "
                     "smelting is energy-intensive and low-margin against Chinese output, which is why prior Western "
                     "capacity closed and restarts are slow. A built chokepoint, but a sticky one.",
             "flag": "an industrial monopoly, not a geological one"},
        ]},
        {"h2": "2 · The 2021 near-miss", "panels": [
            {"kind": "text", "h3": "When China dialled it down", "conf": "measured",
             "text": "In autumn 2021, energy-use curbs in Shaanxi forced magnesium smelters to cut production, prices "
                     "spiked several-fold, and because magnesium cannot be stored long in ingot form without oxidising, "
                     "European aluminium and automotive supply chains warned they were within weeks of running out. It "
                     "was a vivid demonstration of how a single-country, single-region chokepoint transmits a domestic "
                     "policy straight into global industry.",
             "note": "European Commission; industry reporting.", "flag": "weeks of stock, no alternative"},
        ]},
        {"h2": "3 · Why it's nearly unavoidable", "panels": [
            {"kind": "text", "h3": "The invisible ingredient in aluminium",
             "text": "Magnesium's largest use is as an alloying element in aluminium: it gives strength to the "
                     "aluminium in drink cans, car bodies and aircraft. It also enables the lightest die-cast parts and "
                     "desulphurises steel. In these roles the quantities are small but essential — you cannot make the "
                     "alloy without it — so a magnesium shortage quietly threatens the far larger aluminium and "
                     "automotive chains (see the aluminium chain).",
             "flag": "small dose, essential function"},
        ]},
    ],
    "trade_intro": "BACI carries unwrought magnesium (810411, 810419), but a metal that is mostly consumed as an "
                   "alloying addition shows up more in downstream aluminium and parts than in its own line, and China's "
                   "dominance means exporter shares track its output. Read the shares below as the traded metal, not "
                   "the embedded magnesium in aluminium alloys.",
    "method": [
        {"stage": "Feedstock", "lens": "dolomite/magnesite availability", "why": "abundant everywhere — not the constraint"},
        {"stage": "Reduce", "lens": "USGS primary-magnesium share + history", "why": "~87% China (Pidgeon) — an industrial monopoly"},
        {"stage": "Shock", "lens": "2021 energy-curb episode", "why": "showed the fragility; no ready alternative"},
        {"stage": "Trade", "lens": "BACI 810411/810419 magnesium", "why": "metal only; embedded magnesium in alloys not captured — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- magnesium, China ~87pct (Pidgeon); Al alloy; 2021 energy shock")
