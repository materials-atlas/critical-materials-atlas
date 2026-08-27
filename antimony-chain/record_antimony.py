"""Evidence JSON for the antimony chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_antimony.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "antimony_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_antimony": {"title": "USGS Mineral Commodity Summaries 2026 — Antimony", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-antimony.pdf"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — antimony mine production", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "usgs_sb_mcs": {"title": "USGS Mineral Commodity Summaries 2026 — Antimony", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-antimony.pdf"},
    "reuters_sb": {"title": "Reuters, China to limit antimony exports in latest critical mineral curbs", "year": 2024, "url": "https://www.reuters.com/markets/commodities/china-limit-antimony-exports-latest-critical-mineral-curbs-2024-08-15/"},
    "csis_antimony": {"title": "CSIS, China's antimony export controls", "year": 2024, "url": "https://www.csis.org/analysis/critical-minerals-gambit"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Antimony chain",
    "chokepoint": {"product": "Flame retardant · munitions", "stage": "Refining", "mechanism": "capability", "physics": "Trioxide + metal refining — China built the capacity; the mine diversified but refining didn't", "holder": "China refine", "share": "refine", "control": "Sep 2024", "conf": "estimate"},
    "published": True,
    "related": [{"href": "../defence-chain/defence-chain.html", "label": "Defence chain"}, {"href": "../tungsten-chain/tungsten-chain.html", "label": "Tungsten chain"}, {"href": "../gallium-chain/gallium-chain.html", "label": "Gallium chain"}],
    "accent": "#7a5a5a",
    "eyebrow": "Product-chain pilot · flame retardant and munitions metal",
    "h1": "The metal in flame retardants and ammunition — and China just made it a lever",
    "deck": "Antimony is a dual-use metal hiding in plain sight: about half of it makes the flame retardants in plastics, "
            "textiles and electronics, and the rest runs through strategic military uses — ammunition primers, tracer "
            "rounds, night-vision and nuclear applications. Its mining has actually spread, but refining and control "
            "stayed with China, which placed antimony under export licensing in September 2024.",
    "byline": "stibnite (China↓, Tajikistan/Russia↑) ≠ refined antimony / trioxide (China) ≠ flame retardant + munitions",
    "correction": "Antimony's mine map is diversifying — China's share of mining fell from ~84% in 2000 to ~43% as "
                  "Tajikistan and Russia grew — yet it is more of a chokepoint than ever, because China dominates "
                  "refining and the trade in antimony trioxide, and in September 2024 it placed antimony under export "
                  "controls, sending prices sharply higher. A metal that is both a mass-market flame retardant and a "
                  "munitions input turned into a strategic lever.",
    "stats": [
        {"v": "Sep 2024", "l": "China placed antimony under export licensing; prices spiked", "conf": "measured"},
        {"v": "~half", "l": "of antimony use is flame retardants (as antimony trioxide)", "conf": "measured"},
        {"v": "military", "l": "ammunition primers, tracer rounds, night-vision, nuclear — a defence metal", "conf": "measured"},
        {"v": "84 → 43%", "l": "China's mine share fell as Tajikistan and Russia rose — but refining stayed China", "conf": "measured"},
    ],
    "history": {
        "title": "The mine diversified, the control didn't: antimony mine share, 2000 → 2024",
        "conf": "measured",
        "note": "BGS/USGS mine production, from the atlas's own data. China's share of antimony mining fell from ~84% to "
                "~43% as Tajikistan (now ~26%) and Russia (~14%) grew. But mine share is the misleading number here: "
                "China still dominates antimony refining and trioxide production, and its September 2024 export "
                "controls showed the lever sits downstream of the mine, not at it.",
        "series": [
            {"label": "China", "points": hist_points("antimony", "CN")},
            {"label": "Tajikistan", "points": hist_points("antimony", "TJ")},
            {"label": "Russia", "points": hist_points("antimony", "RU")},
        ],
    },
    "hops": [
        {"n": "1 · Mine", "t": "stibnite ore — China, Tajikistan, Russia, Bolivia, Myanmar"},
        {"n": "2 · Refine", "t": "antimony metal and antimony trioxide (ATO) — China-dominated"},
        {"n": "3a · Flame retardant", "t": "ATO synergist with brominated retardants in plastics, textiles, electronics"},
        {"n": "3b · Military & other", "t": "ammunition, tracer rounds, night-vision, lead-acid batteries, glass"},
    ],
    "sections": [
        {"h2": "1 · The mine spread — the chokepoint moved downstream", "panels": [
            {"kind": "big", "h3": "Where the lever actually is", "big": "refining, not the mine", "conf": "measured",
             "text": "China's declining mine share (84% to 43%) looks like diversification, but it hides where the power "
                     "sits: China refines most of the world's antimony and makes most antimony trioxide, and it imports "
                     "ore (from Tajikistan, Russia, Myanmar) to feed that capacity. The September 2024 export controls "
                     "target refined antimony and trioxide — the concentrated stage — not the increasingly spread mine.",
             "note": "USGS MCS 2026; CSIS."},
            {"kind": "text", "h3": "A small market, a big shock",
             "text": "Antimony is a small market by tonnage, which makes it easy to move: when China restricted exports "
                     "in late 2024, prices roughly doubled and Western buyers of flame retardants and defence primes "
                     "scrambled. It is the same playbook as gallium, germanium and graphite — a niche, refining-"
                     "concentrated metal turned into an instrument (see the defence chain).",
             "flag": "the export-control playbook again"},
        ]},
        {"h2": "2 · Half of it is fire safety", "panels": [
            {"kind": "text", "h3": "Antimony trioxide, the flame-retardant synergist", "conf": "measured",
             "text": "The largest use of antimony is antimony trioxide, which works synergistically with brominated and "
                     "chlorinated flame retardants to stop plastics, textiles, wiring and electronics from burning. It "
                     "is embedded in building materials, cars, furniture and consumer electronics — a quiet, "
                     "safety-critical dependency most people never notice until the supply is squeezed.",
             "note": "USGS: flame retardants are the leading antimony use.", "flag": "a hidden safety input"},
        ]},
        {"h2": "3 · The strategic half: munitions and optics", "panels": [
            {"kind": "text", "h3": "A genuine defence metal",
             "text": "Antimony hardens lead in ammunition and shot, primes and tracer rounds, and goes into "
                     "night-vision devices, infrared sensors, and some nuclear applications. That dual-use character — "
                     "mass-market fire safety plus military essentiality — is exactly why its concentration and the "
                     "2024 export controls drew defence-supply alarm in the US and Europe, which have little domestic "
                     "mine or refining capacity.",
             "note": "USGS; defence-industrial reporting.", "flag": "fire safety and firepower, one metal"},
        ]},
    ],
    "trade_intro": "BACI carries unwrought antimony (811010) and antimony oxides (282580), where China's refining and "
                   "trioxide dominance shows more than in the increasingly spread mine. Read the shares below as the "
                   "traded refined forms — the stage the 2024 export controls actually targeted — not the mine map.",
    "method": [
        {"stage": "Mine", "lens": "USGS/BGS mine share + history", "why": "diversifying (China 84->43%) — the misleading number"},
        {"stage": "Refine", "lens": "antimony metal + trioxide", "why": "China-dominated — where the 2024 lever sits"},
        {"stage": "Use", "lens": "flame retardant vs military", "why": "dual-use: fire safety and munitions"},
        {"stage": "Trade", "lens": "BACI 811010 antimony + 282580 oxide", "why": "refined forms show the real concentration — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- antimony, mine diversified but refining+Sep-2024 control China; FR+munitions")
