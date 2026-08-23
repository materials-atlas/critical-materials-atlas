"""Evidence JSON for the fluorine (fluorspar -> HF) chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_fluorine.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "fluorine_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_fluorspar": {"title": "USGS Mineral Commodity Summaries 2026 — Fluorspar", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-fluorspar.pdf"},
    "iea_minerals_2025": {"title": "IEA, Global Critical Minerals Outlook 2025", "year": 2025, "url": "https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — fluorspar mine production", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Fluorine (fluorspar → HF) chain",
    "accent": "#3a7d6a",
    "eyebrow": "Product-chain pilot · one mineral, three technologies",
    "h1": "One obscure mineral quietly gates chips, batteries and cooling at once",
    "deck": "Fluorspar is a mineral almost nobody names, yet its acid — hydrogen fluoride — is the gateway to three "
            "unrelated critical products: the etching gases that make semiconductors, the electrolyte and binder in "
            "every lithium-ion cell, and the refrigerants in every air conditioner and heat pump. China mines about "
            "two-thirds of it.",
    "byline": "fluorspar (~65% CN) → hydrogen fluoride → { chip gases · LiPF6 electrolyte · refrigerants }",
    "correction": "Supply-risk lists rarely mention fluorine, yet it is a hidden common node. Fluorspar → HF feeds "
                  "semiconductor etchants, the LiPF6 electrolyte and PVDF binder in Li-ion cells, and HFC/HFO "
                  "refrigerants — three chains that look independent but share one upstream mineral. China mines ~65% "
                  "of fluorspar (up from ~37% in 2000) and makes most of the world's HF, so a single quiet chokepoint "
                  "sits under chips, batteries and heat pumps together.",
    "stats": [
        {"v": "~65%", "l": "China's share of world fluorspar mine output (2024)", "conf": "measured"},
        {"v": "37 → 65%", "l": "China's fluorspar share climbed steadily, 2000 → 2024", "conf": "measured"},
        {"v": "HF", "l": "hydrogen fluoride — the one chemical gateway to all three end uses", "conf": "measured"},
        {"v": "3 chains", "l": "chips, Li-ion cells and refrigerants all depend on this mineral", "conf": "measured"},
    ],
    "history": {
        "title": "A chokepoint that was built: China's fluorspar share, 2000 → 2024",
        "conf": "measured",
        "note": "BGS/USGS mine production, from the atlas's own data. China's share roughly doubled from ~37% to a "
                "peak near 70% before easing to ~65%, while Mexico held second place. Unlike a geological monopoly, "
                "this concentration was built over two decades — which is exactly the atlas's distinction: a built "
                "chokepoint can, in principle, be rebuilt elsewhere.",
        "series": [
            {"label": "China", "points": hist_points("fluorspar", "CN")},
            {"label": "Mexico", "points": hist_points("fluorspar", "MX")},
            {"label": "Mongolia", "points": hist_points("fluorspar", "MN")},
        ],
    },
    "hops": [
        {"n": "1 · Fluorspar", "t": "calcium fluoride ore (CaF2), acid-grade — China ~65% of the mine"},
        {"n": "2 · Hydrogen fluoride", "t": "fluorspar + sulphuric acid → HF, the reactive gateway chemical"},
        {"n": "3 · Fluorochemicals", "t": "etch gases (NF3, WF6), LiPF6 electrolyte + PVDF binder, HFC/HFO refrigerants"},
        {"n": "4 · The products", "t": "semiconductors, lithium-ion cells, air conditioners and heat pumps"},
    ],
    "sections": [
        {"h2": "1 · The mineral splits into three critical roads", "panels": [
            {"kind": "cards", "h3": "What HF turns into", "cards": [
                {"t": "Semiconductor gases", "d": "Fluorinated gases (NF3, WF6, etch chemistries) clean and pattern silicon wafers — no chip fab runs without them (see the silicon-chip chain)."},
                {"t": "Battery electrolyte", "d": "LiPF6 salt and the PVDF binder in every lithium-ion cell are fluorochemicals — fluorine is quietly inside the battery chain."},
                {"t": "Refrigerants", "d": "HFC and next-gen HFO refrigerants in air conditioners and heat pumps are fluorine-based — the cooling chain rests on it too."},
            ]},
            {"kind": "text", "h3": "Also the flux under aluminium and steel",
             "text": "Beyond the three headline roads, fluorspar is the flux (as synthetic cryolite) in aluminium "
                     "smelting and a flux in steelmaking. So the same mineral touches five chains in this atlas at "
                     "once — a genuinely cross-cutting node hiding in plain sight.",
             "flag": "a shared node under five chains"},
        ]},
        {"h2": "2 · The concentration was built, not born", "panels": [
            {"kind": "big", "h3": "China's climb", "big": "37 → 65%", "conf": "measured",
             "text": "China's share of fluorspar mining roughly doubled over two decades as other producers (South "
                     "Africa, Mongolia, Mexico) held or shrank and Chinese output grew. It also dominates the HF and "
                     "downstream fluorochemical steps. Because this was built with capital and policy rather than "
                     "handed by geology, it is the kind of chokepoint that can be diversified — slowly.",
             "note": "USGS / BGS mine-production history."},
            {"kind": "text", "h3": "The reserves picture is less lopsided",
             "text": "Unlike a true geological monopoly, fluorspar reserves are spread — Mexico, South Africa, "
                     "Mongolia and others hold sizeable deposits, and by-product fluorine can be recovered from "
                     "phosphate processing. The bottleneck is where acid-grade fluorspar and HF are actually made, not "
                     "where the calcium fluoride sits in the ground.",
             "flag": "reserves spread; processing concentrated"},
        ]},
        {"h2": "3 · Why it matters for resilience", "panels": [
            {"kind": "text", "h3": "A single point under three transitions",
             "text": "The digital build-out (chips), electrification (batteries) and efficient heating (heat pumps) "
                     "are usually analysed as separate supply stories. Fluorine is a reminder that they can share a "
                     "hidden dependency: constrain one obscure mineral and its acid, and you touch all three at once. "
                     "It is the clearest 'so-what' in this layer — diversify the node, not just the visible products.",
             "flag": "one node, three transitions"},
        ]},
    ],
    "trade_intro": "BACI carries fluorspar (acid- and metallurgical-grade) and hydrogen fluoride, but not the "
                   "downstream fluorochemicals (LiPF6, electronic gases, refrigerants), which sit in broad chemical "
                   "headings. Read the shares below as the raw mineral and its first acid; the three end-use branches "
                   "are not separable in customs data.",
    "method": [
        {"stage": "Fluorspar", "lens": "USGS/BGS mine share + history", "why": "~65% China, built from ~37% since 2000"},
        {"stage": "HF", "lens": "USGS/IEA HF production", "why": "the single chemical gateway; most of it in China"},
        {"stage": "End uses", "lens": "chips / battery / refrigerant literature", "why": "three chains share the node — qualitative"},
        {"stage": "Trade", "lens": "BACI 252921/252922 fluorspar + 281111 HF", "why": "raw mineral + acid only; fluorochemicals not separable — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- fluorine, fluorspar 37->65pct China; gates chips+battery+refrigerants")
