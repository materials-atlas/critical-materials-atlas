"""Evidence JSON for the zinc chain pilot. Uniform schema. Public sources.
The host that explains the by-product cluster. Run: python record_zinc.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "zinc_chain.json")

SRC = {
    "usgs_zinc": {"title": "USGS Mineral Commodity Summaries 2026 — Zinc", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-zinc.pdf"},
    "usgs_gallium": {"title": "USGS Mineral Commodity Summaries 2026 — Gallium (recovery from zinc)", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-gallium.pdf"},
    "ilzsg": {"title": "International Lead and Zinc Study Group — supply & use", "year": 2025, "url": "https://www.ilzsg.org/"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Zinc chain",
    "chokepoint": {"product": "Galvanizing · by-product host", "stage": "Smelting", "mechanism": "capability", "physics": "The host: gallium, germanium, indium and cadmium are recovered at zinc smelters — refining capacity (China ~half) gates them, not just zinc", "holder": "China", "share": "~half", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../gallium-chain/gallium-chain.html", "label": "Gallium chain"}, {"href": "../germanium-chain/germanium-chain.html", "label": "Germanium chain"}, {"href": "../displays-indium-chain/displays-indium-chain.html", "label": "Displays / indium chain"}],
    "accent": "#6a7a8a",
    "eyebrow": "Product-chain pilot · the host metal",
    "h1": "Zinc is the invisible host that gates half the atlas's by-product metals",
    "deck": "Zinc's everyday job is galvanizing — the sacrificial coating that stops steel rusting. But its strategic "
            "role is quieter and bigger: gallium, germanium, indium and cadmium are all recovered from zinc ores and "
            "smelters. So zinc-refining capacity, and whether a smelter bothers to recover the trace metals, is what "
            "actually gates those by-products — not any gallium or germanium 'mine'.",
    "byline": "zinc ore (diversified) ≠ smelting (China ~half, + by-product recovery) ≠ galvanized steel / die-cast / brass",
    "correction": "Half the by-product chains in this atlas — gallium, germanium, indium, cadmium — trace back to one "
                  "host: zinc. They are recovered from the residues of zinc smelting, so their supply is bounded by how "
                  "much zinc is refined and by whether recovery circuits are installed. China refines roughly half the "
                  "world's zinc and dominates that recovery, which is the real reason it dominates gallium and "
                  "germanium. Zinc itself is abundant and mined widely; its leverage is as the host.",
    "stats": [
        {"v": "galvanizing", "l": "about half of zinc rust-proofs steel — the sacrificial coating has no cheap substitute", "conf": "measured"},
        {"v": "the host", "l": "gallium, germanium, indium and cadmium are recovered from zinc smelting", "conf": "measured"},
        {"v": "~half China", "l": "of refined zinc — where the by-product metals are actually recovered", "conf": "measured"},
        {"v": "diversified mine", "l": "zinc ore is mined across China, Peru, Australia — not a mine chokepoint", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Mine", "t": "zinc ore (sphalerite) — China, Peru, Australia, Mexico; diversified"},
        {"n": "2 · Smelt", "t": "roast-leach-electrowin to refined zinc — China ~half; by-products recovered here"},
        {"n": "3 · By-products", "t": "gallium, germanium, indium, cadmium pulled from residues — if recovery is installed"},
        {"n": "4 · End use", "t": "galvanizing (steel), die-casting, brass, chemicals — plus the trace-metal stream"},
    ],
    "sections": [
        {"h2": "1 · The everyday job: rust-proofing steel", "panels": [
            {"kind": "big", "h3": "Where most zinc goes", "big": "galvanizing", "conf": "measured",
             "text": "The largest use of zinc is galvanizing — coating steel so that the zinc corrodes sacrificially "
                     "instead of the iron beneath. It is what keeps bridges, cars, roofing and infrastructure from "
                     "rusting, and there is no cheap substitute for the electrochemistry. Zinc also die-casts and "
                     "alloys into brass. This bulk demand is diversified and unremarkable — which is why zinc rarely "
                     "makes critical-materials lists.",
             "note": "USGS Zinc 2026; ILZSG."},
            {"kind": "text", "h3": "Abundant and widely mined",
             "text": "Zinc is a common base metal, mined across China, Peru, Australia, Mexico and others, with refining "
                     "more concentrated (China refines about half). On its own it is not a severe chokepoint — supply "
                     "is broad. The reason to give it a chain is not zinc itself, but what rides on it.",
             "flag": "not a chokepoint on its own"},
        ]},
        {"h2": "2 · The strategic role: the by-product host", "panels": [
            {"kind": "text", "h3": "Half the by-product cluster is recovered here", "conf": "measured",
             "text": "Gallium, germanium, indium and cadmium do not have mines of their own — they occur in zinc ores "
                     "at trace levels and are recovered from the residues and dusts of zinc smelting. So the supply of "
                     "these technology metals is bounded by zinc-refining capacity and, crucially, by whether a given "
                     "smelter installs the recovery circuits. China's dominance of gallium (~98%) and germanium is "
                     "downstream of its dominance of zinc smelting and its choice to recover.",
             "note": "USGS: gallium/germanium/indium recovered from zinc processing.", "flag": "the host gates the by-products"},
            {"kind": "text", "h3": "Why the West lost the by-products",
             "text": "Western zinc smelters can recover gallium, germanium and indium too, but many stopped when "
                     "Chinese output made it uneconomic. Rebuilding by-product supply therefore means rebuilding "
                     "recovery at zinc (and alumina) refineries — a zinc-capacity and incentive problem, not a mining "
                     "one. The host chain is where several of the atlas's export-control stories actually begin.",
             "flag": "recovery circuits, not new mines"},
        ]},
        {"h2": "3 · Reading the cluster through zinc", "panels": [
            {"kind": "cards", "h3": "What zinc hosts", "cards": [
                {"t": "Gallium", "d": "Recovered from zinc (and alumina) — ~98% China, export-controlled 2023 (see the gallium chain)."},
                {"t": "Germanium", "d": "From zinc residues + coal ash — export-controlled with gallium (see the germanium chain)."},
                {"t": "Indium", "d": "Almost entirely a zinc by-product — the ITO metal in every screen (see the displays chain)."},
            ]},
        ]},
    ],
    "trade_intro": "BACI carries zinc ores (260800) and unwrought zinc (790111), but not the trace gallium, germanium "
                   "and indium recovered alongside — those hide in the shared minor-metal baskets the atlas flags. Read "
                   "the shares below as the base-metal trade; the strategic story is the by-product recovery it "
                   "carries, which trade data cannot show.",
    "method": [
        {"stage": "Mine", "lens": "USGS zinc mine share", "why": "diversified and abundant — not the chokepoint"},
        {"stage": "Smelt", "lens": "refined-zinc share + by-product recovery", "why": "~half China; where the by-product metals are gated"},
        {"stage": "By-products", "lens": "gallium/germanium/indium recovery", "why": "bounded by zinc capacity + recovery circuits"},
        {"stage": "Trade", "lens": "BACI 260800 ore + 790111 zinc", "why": "base-metal trade; trace by-products not visible — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- zinc, the host: gates gallium/germanium/indium via smelting (China ~half)")
