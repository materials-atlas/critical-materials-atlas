"""Evidence JSON for the beryllium chain pilot. Uniform schema. Public sources.
The reversal: the rare critical mineral where the US, not China, is the chokepoint.
Shared chainview renderer, per-figure confidence tags. Run: python record_beryllium.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "beryllium_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_beryllium": {"title": "USGS Mineral Commodity Summaries 2026 — Beryllium", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-beryllium.pdf"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — beryllium", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "usgs_history": {"title": "USGS, Historical Statistics for Mineral and Material Commodities", "year": 2024, "url": "https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Beryllium chain",
    "chokepoint": {"product": "Aerospace · defence", "stage": "Extraction (US)", "mechanism": "capability", "secondary": "geological", "research": True, "physics": "Hard-won hydrometallurgy + alloying, guarded by toxicity — concentrated in the US, the non-China chokepoint", "holder": "United States", "share": "~53%", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../aerospace-chain/aerospace-chain", "label": "Aerospace chain"}, {"href": "../defence-chain/defence-chain", "label": "Defence chain"}, {"href": "../copper-chain/copper-chain", "label": "Copper chain"}],
    "accent": "#4a6a4a",
    "eyebrow": "Product-chain pilot · the reversal",
    "h1": "The one critical metal the West controls — for now",
    "deck": "Almost every chain in this atlas points at China. Beryllium is the exception: the United States mines and "
            "processes most of the world's supply, from a single Utah deposit through essentially one company. A "
            "stiff, ultralight, transparent-to-X-rays metal, it goes into satellites, missiles, gyroscopes, nuclear "
            "reactors and the copper alloys in high-reliability connectors — and it is so toxic that few will handle it.",
    "byline": "bertrandite (US, Utah) ≠ hard-won extraction & alloying (US) ≠ Be metal / Cu-Be alloy ≠ aerospace · defence · nuclear",
    "correction": "Beryllium reverses the atlas's usual map. The chokepoint is American, not Chinese: the US mines "
                  "about 53% of world beryllium from one Utah bertrandite deposit and dominates the extraction and "
                  "alloying, largely through a single firm. The concentration is a built capability guarded by a "
                  "serious barrier — beryllium dust causes chronic, sometimes fatal lung disease, so few producers "
                  "will touch it. China's share is rising (from ~9% to ~18% since 2000), which is exactly why the West "
                  "watches this one chokepoint it actually holds.",
    "stats": [
        {"v": "~53% US", "l": "the rare critical mineral where the US — not China — is the chokepoint", "conf": "measured"},
        {"v": "83 → 53%", "l": "US share fell as China (~18%) and Mozambique rose", "conf": "measured"},
        {"v": "aero + defence", "l": "satellites, missiles, gyroscopes, X-ray windows, nuclear reflectors", "conf": "measured"},
        {"v": "toxic", "l": "beryllium dust causes berylliosis — a capability barrier few will cross", "conf": "measured"},
    ],
    "history": {
        "title": "The West's one chokepoint, slowly eroding: US beryllium share, 2000 → 2024",
        "conf": "measured",
        "note": "BGS/USGS mine production, from the atlas's own data. The US share fell from ~83% to ~53% as China "
                "rose to ~18% and Mozambique emerged, but the US still leads mining and dominates downstream "
                "extraction and alloying. It is the clearest example in the layer of a chokepoint held by the West — "
                "and of that lead gradually narrowing.",
        "series": [
            {"label": "United States", "points": hist_points("beryllium", "US")},
            {"label": "China", "points": hist_points("beryllium", "CN")},
            {"label": "Mozambique", "points": hist_points("beryllium", "MZ")},
        ],
    },
    "hops": [
        {"n": "1 · Bertrandite", "t": "beryllium ore — chiefly one deposit in Utah, USA (plus imported beryl)"},
        {"n": "2 · Extract", "t": "hydrometallurgy to beryllium hydroxide — hazardous, capability-gated"},
        {"n": "3 · Metal & alloy", "t": "beryllium metal, oxide, and copper-beryllium master alloy"},
        {"n": "4 · End use", "t": "aerospace/defence structures, connectors, nuclear, X-ray windows, instruments"},
    ],
    "sections": [
        {"h2": "1 · The map, reversed", "panels": [
            {"kind": "big", "h3": "Who holds beryllium", "big": "~53% US", "conf": "measured",
             "text": "The United States mines most of the world's beryllium from the Spor Mountain bertrandite deposit "
                     "in Utah and processes it largely through one company (Materion), giving the West a chokepoint it "
                     "rarely enjoys elsewhere in this atlas. China is second and growing, and Kazakhstan and Mozambique "
                     "contribute, but the capability — mine plus extraction plus alloying — remains concentrated in the "
                     "US.",
             "note": "USGS Beryllium 2026."},
            {"kind": "text", "h3": "A capability guarded by toxicity",
             "text": "Beryllium is not especially rare in the crust, but working it is genuinely dangerous: inhaling "
                     "beryllium dust causes chronic beryllium disease, an incurable lung condition. That hazard, plus "
                     "the specialised hydrometallurgy and decades of alloying know-how, is a real barrier to entry — a "
                     "built capability that few will replicate, which is what keeps the chain concentrated even though "
                     "the element itself is not scarce.",
             "flag": "toxicity is the moat"},
        ]},
        {"h2": "2 · Why it's irreplaceable where it's used", "panels": [
            {"kind": "text", "h3": "Stiff, light, and X-ray transparent", "conf": "measured",
             "text": "Beryllium is exceptionally stiff for its weight, dimensionally stable across temperature, and "
                     "transparent to X-rays — a combination no other material offers. That makes it essential in "
                     "satellite and telescope structures, inertial-guidance gyroscopes, missile and aircraft parts, "
                     "nuclear reactor reflectors and neutron sources, and the X-ray windows in medical and analytical "
                     "instruments. In these roles there is no substitute.",
             "note": "USGS: aerospace, defence and instruments dominate use.", "flag": "no substitute in its niche"},
            {"kind": "text", "h3": "And the everyday alloy",
             "text": "Most beryllium is actually used as a small addition to copper: copper-beryllium alloy is strong, "
                     "springy, conductive and non-sparking, so it makes the connectors, springs, and safety tools that "
                     "high-reliability electronics and industry depend on. A tiny percentage of beryllium transforms "
                     "copper — a quiet, widespread dependency on top of the strategic one.",
             "flag": "the invisible copper additive"},
        ]},
        {"h2": "3 · The chokepoint the West is trying to keep", "panels": [
            {"kind": "text", "h3": "A narrowing lead",
             "text": "Because beryllium is defence-critical and Western-held, it is stockpiled and closely tracked — "
                     "the reverse of the anxiety China's dominance causes elsewhere. But the US share has slid from "
                     "~83% to ~53% as China expands, so the story here is a Western chokepoint gradually eroding, not a "
                     "Chinese one being built. It is the useful mirror-image case in the layer.",
             "flag": "the mirror-image of the usual worry"},
        ]},
    ],
    "trade_intro": "BACI carries unwrought beryllium and powder (811212) and other beryllium (811219), a very small, "
                   "specialised trade dominated by US material, with copper-beryllium alloy sitting in copper-alloy "
                   "lines. Read the shares below as that thin traded metal, not the full US processing dominance.",
    "method": [
        {"stage": "Mine", "lens": "USGS/BGS mine share + history", "why": "~53% US (from ~83%) — the non-China chokepoint"},
        {"stage": "Capability", "lens": "US extraction + alloying", "why": "a built capability guarded by toxicity"},
        {"stage": "Use", "lens": "aerospace/defence + Cu-Be alloy", "why": "irreplaceable in its niche; a tiny everyday additive"},
        {"stage": "Trade", "lens": "BACI 811212/811219 beryllium", "why": "a thin, specialised US-led trade — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- beryllium, the reversal: US ~53pct (from 83); aero/defence; toxicity moat")
