"""Evidence JSON for the lithium chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_lithium.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "lithium_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_lithium": {"title": "USGS Mineral Commodity Summaries 2026 — Lithium", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-lithium.pdf"},
    "iea_minerals_2025": {"title": "IEA, Global Critical Minerals Outlook 2025", "year": 2025, "url": "https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — lithium mine production", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Lithium chain",
    "related": [{"href": "../battery-chain/battery-chain.html", "label": "Battery chain"}, {"href": "../cobalt-chain/cobalt-chain.html", "label": "Cobalt chain"}, {"href": "../nickel-chain/nickel-chain.html", "label": "Nickel chain"}],
    "accent": "#7a7a3a",
    "eyebrow": "Product-chain pilot · the battery's headline metal",
    "h1": "The lithium mine moved to Australia — the refinery stayed in China",
    "deck": "Lithium is the metal everyone names in the battery story, and its mining actually diversified: Australia's "
            "hard-rock spodumene now leads, with Chile's brine, and fast-rising output from Zimbabwe and Brazil. But "
            "raw lithium is not battery lithium — turning spodumene or brine into battery-grade chemical is "
            "concentrated in China. The chokepoint is the conversion step, not the deposit.",
    "byline": "spodumene (AU) / brine (Chile) ≠ battery-grade chemical (China) ≠ cathode ≠ the cell",
    "correction": "The lithium mine is not the chokepoint — the refinery is. Australia mines the most lithium (hard-rock "
                  "spodumene), the 'Lithium Triangle' of Chile, Argentina and Bolivia holds vast brine reserves, and "
                  "Zimbabwe and Brazil are scaling fast, so ore supply is genuinely multi-country. But most spodumene is "
                  "shipped to China to be converted into battery-grade lithium carbonate and hydroxide — the same "
                  "mine-versus-refine split the atlas finds for cobalt, nickel and graphite.",
    "stats": [
        {"v": "~62%", "l": "Australia's share of lithium mine output (hard-rock spodumene)", "conf": "measured"},
        {"v": "China", "l": "converts most spodumene into battery-grade chemical — the real chokepoint", "conf": "measured"},
        {"v": "brine vs rock", "l": "two production routes: fast hard-rock, slow high-reserve brine", "conf": "measured"},
        {"v": "reserves ≠ output", "l": "Chile and Argentina hold huge brine reserves but mine far less", "conf": "estimate"},
    ],
    "history": {
        "title": "The mine diversified toward hard rock, 2000 → 2024",
        "conf": "measured",
        "note": "BGS/USGS mine production, from the atlas's own data. Australia's fast-scaling hard-rock spodumene took "
                "the lead (to ~62%), while Chile's slower brine fell in relative MINE share (though it still holds vast "
                "reserves) and Zimbabwe rose. The raw-material map is genuinely multi-country — which is exactly why the "
                "chokepoint is the conversion step in China, not the mine, and no country mine-share chart shows it.",
        "series": [
            {"label": "Australia", "points": hist_points("lithium", "AU")},
            {"label": "Chile", "points": hist_points("lithium", "CL")},
            {"label": "Zimbabwe", "points": hist_points("lithium", "ZW")},
        ],
    },
    "hops": [
        {"n": "1 · Mine", "t": "hard-rock spodumene (Australia) or brine (Chile, Argentina) — multi-country"},
        {"n": "2 · Refine", "t": "spodumene/brine → battery-grade carbonate or hydroxide — mostly China"},
        {"n": "3 · Cathode", "t": "lithium chemical into NMC, LFP and other cathode powders"},
        {"n": "4 · Cell", "t": "the battery — lithium is the charge carrier in every lithium-ion cell"},
    ],
    "sections": [
        {"h2": "1 · Two ways to make lithium, one refiner", "panels": [
            {"kind": "big", "h3": "Where lithium is mined", "big": "~62% Australia", "conf": "measured",
             "text": "Australia leads because hard-rock spodumene mines can be built and expanded quickly, and it ships "
                     "the concentrate to converters. Brine operations in Chile and Argentina hold far larger reserves "
                     "but evaporate slowly over months, so their share of annual output is smaller than their share of "
                     "the ground. Two very different clocks feed the same battery.",
             "note": "USGS MCS 2026."},
            {"kind": "text", "h3": "The conversion step is the chokepoint",
             "text": "Neither spodumene nor raw brine is usable in a cell — both must be refined to high-purity "
                     "carbonate or hydroxide. That conversion is concentrated in China, which processes most of the "
                     "world's spodumene (much of it Australian) into battery-grade chemical. So even Australian lithium "
                     "typically becomes a battery only after a Chinese refinery, as with cobalt and graphite.",
             "flag": "the refinery, not the rock"},
        ]},
        {"h2": "2 · Reserves are not the same as supply", "panels": [
            {"kind": "text", "h3": "The Lithium Triangle holds it; Australia ships it", "conf": "estimate",
             "text": "Chile, Argentina and Bolivia sit on the world's largest lithium resources in their salt flats, but "
                     "turning brine reserves into flowing supply is slow, water-intensive and politically contested "
                     "(Bolivia has barely started). Direct-lithium-extraction (DLE) promises to speed brine up, but is "
                     "not yet at scale. So the reserve map and the production map point at different countries.",
             "note": "USGS; IEA.", "flag": "reserves in one place, output in another"},
        ]},
        {"h2": "3 · Why the price whipsaws", "panels": [
            {"kind": "text", "h3": "A young market that overshoots",
             "text": "Lithium demand is dominated by batteries and has grown explosively, but new mines and refineries "
                     "take years, so price has swung violently — a boom to 2022, then a sharp crash as supply caught up. "
                     "The metal is not geologically scarce; the difficulty is matching a fast-moving demand curve to "
                     "slow-building supply and a concentrated refining step. Chemistry shifts (LFP vs NMC) move the "
                     "demand target too (see the battery chain).",
             "flag": "not scarce, just slow to build"},
        ]},
    ],
    "trade_intro": "BACI carries lithium carbonate (283691) and lithium oxide/hydroxide (282520), but not spodumene "
                   "concentrate cleanly, and a chemical's customs origin is the refinery, not the mine. Read the shares "
                   "below as the traded battery chemicals — where China's conversion role shows more than in any mine "
                   "figure.",
    "method": [
        {"stage": "Mine", "lens": "USGS/BGS mine share + history", "why": "multi-country (Australia hard-rock leads) — not the chokepoint"},
        {"stage": "Refine", "lens": "IEA conversion share", "why": "battery-grade chemical, mostly China — the real chokepoint"},
        {"stage": "Reserves", "lens": "USGS reserves vs output", "why": "Lithium Triangle holds it; production sits elsewhere"},
        {"stage": "Trade", "lens": "BACI 283691 carbonate + 282520 hydroxide", "why": "refinery-origin chemicals — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- lithium, AU ~62pct mine but China refines; brine vs rock")
