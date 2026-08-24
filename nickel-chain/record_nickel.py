"""Evidence JSON for the nickel chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_nickel.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "nickel_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_nickel": {"title": "USGS Mineral Commodity Summaries 2026 — Nickel", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-nickel.pdf"},
    "iea_minerals_2025": {"title": "IEA, Global Critical Minerals Outlook 2025", "year": 2025, "url": "https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — nickel mine production", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Nickel chain",
    "published": True,
    "related": [{"href": "../battery-chain/battery-chain.html", "label": "Battery chain"}, {"href": "../cobalt-chain/cobalt-chain.html", "label": "Cobalt chain"}, {"href": "../steel-chain/steel-chain.html", "label": "Primary / green-steel chain"}],
    "accent": "#4a7a5a",
    "eyebrow": "Product-chain pilot · stainless steel and the battery",
    "h1": "Indonesia rewrote the nickel map with a single policy",
    "deck": "Nickel makes stainless steel and, increasingly, high-energy battery cathodes. Its geography was "
            "transformed not by geology but by policy: Indonesia banned exports of raw nickel ore to force smelting at "
            "home, and — with heavy Chinese investment — went from a bit player to roughly 60% of world mine output in "
            "little over a decade.",
    "byline": "laterite ore (Indonesia) ≠ smelting (RKEF / HPAL, China-financed) ≠ class 1 vs class 2 ≠ stainless or battery",
    "correction": "Nickel is the atlas's clearest case of a chokepoint built by industrial policy. Indonesia holds "
                  "large low-grade laterite reserves; by banning raw-ore exports (fully from 2020) it forced miners to "
                  "build smelters at home, largely financed and operated by Chinese firms. The result: Indonesia's mine "
                  "share leapt to ~60%, and it now dominates both stainless-grade (class 2) and, via HPAL, battery-grade "
                  "(class 1) nickel — a concentration created by a rule, not a deposit.",
    "stats": [
        {"v": "8 → 61%", "l": "Indonesia's share of world nickel mine output, 2000 → 2024", "conf": "measured"},
        {"v": "export ban", "l": "Indonesia's 2020 raw-ore export ban forced domestic smelting", "conf": "measured"},
        {"v": "class 1 vs 2", "l": "battery-grade (class 1) vs stainless-grade (class 2) — different products", "conf": "measured"},
        {"v": "China-financed", "l": "the new Indonesian smelters are largely Chinese-built and -owned", "conf": "measured"},
    ],
    "history": {
        "title": "A chokepoint built by policy: Indonesia's nickel share, 2000 → 2024",
        "conf": "measured",
        "note": "BGS/USGS mine production, from the atlas's own data. Indonesia went from ~8% of world nickel mining to "
                "~61%, while Russia, Canada and Australia shrank in relative terms and the Philippines held second "
                "place. The inflection follows Indonesia's ore-export restrictions — a rare, vivid example of "
                "geography being remade by a policy rather than by geology.",
        "series": [
            {"label": "Indonesia", "points": hist_points("nickel", "ID")},
            {"label": "Philippines", "points": hist_points("nickel", "PH")},
            {"label": "Russia", "points": hist_points("nickel", "RU")},
        ],
    },
    "hops": [
        {"n": "1 · Laterite ore", "t": "Indonesia's low-grade nickel laterite — abundant, near-surface"},
        {"n": "2 · Smelt", "t": "RKEF → ferronickel/NPI (class 2), or HPAL → MHP (battery-grade class 1)"},
        {"n": "3 · Class 1 / class 2", "t": "class 1 (>99.8%) for batteries; class 2 (ferronickel/NPI) for stainless"},
        {"n": "4 · End use", "t": "stainless steel (~two-thirds of demand) and EV battery cathodes (rising)"},
    ],
    "sections": [
        {"h2": "1 · A map redrawn by a rule", "panels": [
            {"kind": "big", "h3": "Indonesia's leap", "big": "8 → 61%", "conf": "measured",
             "text": "Indonesia banned exports of unprocessed nickel ore to capture more value at home. Miners and "
                     "(mostly Chinese) investors responded by building a wave of smelters, and Indonesian mine output "
                     "and processing surged. In roughly a decade the country went from marginal to dominant — a "
                     "concentration engineered by policy and capital, not handed down by a unique deposit.",
             "note": "USGS MCS 2026; IEA."},
            {"kind": "text", "h3": "The environmental bill",
             "text": "The speed came at a cost: much of the new smelting is coal-powered, and HPAL plants generate large "
                     "volumes of tailings and process residues in a biodiverse region. So the nickel map's redraw is "
                     "also a carbon-and-waste story — cheap, fast nickel with a heavy footprint, which shapes how "
                     "'clean' the batteries built on it really are.",
             "flag": "fast and cheap, but coal-powered"},
        ]},
        {"h2": "2 · Two nickels, two chains", "panels": [
            {"kind": "text", "h3": "Class 1 vs class 2 matters", "conf": "measured",
             "text": "Not all nickel is battery nickel. Class-2 nickel (ferronickel and nickel pig iron) goes into "
                     "stainless steel, still about two-thirds of demand. Battery cathodes need high-purity class-1 "
                     "nickel, historically a separate, tighter market — but Indonesia's HPAL projects now convert "
                     "laterite into battery-grade intermediate (MHP), blurring the line and extending its dominance "
                     "into the battery chain too.",
             "note": "IEA; USGS.", "flag": "stainless and batteries draw on different grades"},
        ]},
        {"h2": "3 · Who controls it now", "panels": [
            {"kind": "text", "h3": "Indonesian ground, Chinese capacity",
             "text": "The nickel sits in Indonesia, but the smelting capacity, technology and much of the ownership are "
                     "Chinese (Tsingshan and others). So control of the chain is split — resource nationalism on one "
                     "side, processing dominance on the other — and the battery world's nickel increasingly flows "
                     "through that Indonesian-Chinese partnership. It is a policy-built chokepoint with two keyholders.",
             "flag": "resource host and processor are different powers"},
        ]},
    ],
    "trade_intro": "BACI carries nickel ores (260400) and unwrought nickel (750210), but Indonesia's ore-export ban "
                   "means little ore now trades — the value moved into smelted products and intermediates that these "
                   "lines only partly capture. Read the shares below as the traded metal forms, not the mine or "
                   "smelter map, which the export ban deliberately reshaped.",
    "method": [
        {"stage": "Mine", "lens": "USGS/BGS mine share + history", "why": "Indonesia ~61%, built by the export ban"},
        {"stage": "Smelt", "lens": "RKEF vs HPAL; class 1 vs 2", "why": "the processing split that gates batteries vs stainless"},
        {"stage": "Control", "lens": "Indonesian resource + Chinese capacity", "why": "a two-keyholder chokepoint"},
        {"stage": "Trade", "lens": "BACI 260400 ore + 750210 nickel", "why": "ore barely trades post-ban — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- nickel, Indonesia 8->61pct via export ban; class1/2; China-financed")
