"""Evidence JSON for the semiconductor-inputs (photoresist / gases / CMP) chain pilot. Uniform schema.
The chemicals that gate the fab, upstream of silicon-chip. Run: python record_semiconductor_inputs.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "semiconductor_inputs_chain.json")

SRC = {
    "semi_materials": {"title": "SEMI — semiconductor materials market (wafer + fab chemicals)", "year": 2024, "url": "https://www.semi.org/en/products-services/market-data/materials"},
    "csis_resist": {"title": "CSIS — Japan's photoresist and the 2019 Japan-Korea dispute", "year": 2019, "url": "https://www.csis.org/analysis/japan-korea-trade-dispute"},
    "iea_neon": {"title": "IEA / industry — specialty gases in semiconductor manufacturing", "year": 2023, "url": "https://www.iea.org/reports/the-state-of-clean-technology-manufacturing"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Semiconductor-inputs chain",
    "chokepoint": {"product": "Chip fabrication", "stage": "Photoresist + process chemicals", "mechanism": "capability", "physics": "Advanced photoresist is ~90% Japan; process gases, CMP slurries and EUV pellicles are each held by a few qualified suppliers", "holder": "Japan (resist)", "share": "~90%", "control": "2019 JP↔KR", "conf": "measured"},
    "published": True,
    "related": [{"href": "../silicon-chip/silicon-chain.html", "label": "Silicon → chips chain"}, {"href": "../neon-chain/neon-chain.html", "label": "Neon / specialty-gas chain"}, {"href": "../fluorine-chain/fluorine-chain.html", "label": "Fluorine chain"}],
    "accent": "#4a5a8a",
    "eyebrow": "Product-chain pilot · before the chip",
    "h1": "Before the chip, the chemicals — and Japan makes most of the critical one",
    "deck": "A chip fab is famous for its machines, but it runs on a stream of ultra-pure specialty chemicals: the "
            "photoresist that patterns every layer, the process gases that etch and deposit, the slurries that polish "
            "wafers flat, the pellicles that protect masks. Each is a thin, qualified-supplier chokepoint upstream of "
            "the fab — and advanced photoresist is roughly 90% Japanese.",
    "byline": "photoresist (~90% Japan) · process gases (few) · CMP slurries · EUV pellicles ≠ the fab ≠ the chip",
    "correction": "The silicon-chip chain covers the fab and its EUV machines; this one is the layer beneath — the "
                  "consumable chemicals every fab depends on. The sharpest is photoresist, the light-sensitive coating "
                  "that transfers circuit patterns: a few Japanese firms (JSR, Tokyo Ohka, Shin-Etsu, Fujifilm) make "
                  "around 90% of the advanced grades. Add the specialty gases (neon, fluorinated etchants), the "
                  "chemical-mechanical polishing slurries and the EUV pellicles, and the fab sits on a stack of narrow, "
                  "qualification-gated chemical chokepoints.",
    "stats": [
        {"v": "~90% Japan", "l": "advanced photoresist — a near-monopoly of a few firms", "conf": "measured"},
        {"v": "the fab's chemicals", "l": "resist, process gases, CMP slurries and pellicles — each few suppliers", "conf": "measured"},
        {"v": "2019 shock", "l": "Japan's photoresist export curbs on Korea showed the leverage", "conf": "measured"},
        {"v": "upstream of the fab", "l": "these gate the chip before an EUV machine even runs", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Chemicals", "t": "photoresist, process gases, CMP slurries, pellicles, high-purity solvents"},
        {"n": "2 · Qualification", "t": "each grade is qualified into specific processes over years — hard to swap"},
        {"n": "3 · Fab", "t": "the chemicals feed lithography, etch, deposition and planarisation (silicon-chip chain)"},
        {"n": "4 · The chip", "t": "the finished logic/memory device — sitting on the whole chemical stack"},
    ],
    "sections": [
        {"h2": "1 · Photoresist: the sharpest chokepoint", "panels": [
            {"kind": "big", "h3": "Who makes the resist", "big": "~90% Japan", "conf": "measured",
             "text": "Photoresist is the light-sensitive polymer that records the circuit pattern on each layer of a "
                     "chip — and the advanced grades (KrF, ArF, and especially EUV resist) are made overwhelmingly by a "
                     "few Japanese companies. It is a decades-deep formulation and purity capability that cannot be "
                     "cloned quickly, which is why it is one of the most concentrated inputs in all of electronics.",
             "note": "SEMI; CSIS."},
            {"kind": "text", "h3": "The 2019 warning shot",
             "text": "In 2019 Japan tightened export controls on photoresist and two other fab chemicals to South "
                     "Korea, briefly threatening Samsung and SK Hynix — a reminder that a fab full of the world's most "
                     "advanced machines can still be halted by a consumable it does not make. Korea scrambled to "
                     "localise, but the episode showed how narrow and leverageable these chemical chokepoints are.",
             "note": "CSIS.", "flag": "a consumable can halt a fab"},
        ]},
        {"h2": "2 · The rest of the chemical stack", "panels": [
            {"kind": "cards", "h3": "The other narrow inputs", "cards": [
                {"t": "Process gases", "d": "Neon for lithography lasers, plus fluorinated etch and deposition gases — thin, concentrated (see the neon and fluorine chains)."},
                {"t": "CMP slurries", "d": "Chemical-mechanical polishing slurries (ceria, silica, additives) flatten each layer — a few qualified suppliers."},
                {"t": "EUV pellicles", "d": "The ultra-thin membranes that protect EUV masks are a niche, single-digit-supplier item essential to leading-edge chips."},
            ]},
        ]},
        {"h2": "3 · Why it stays concentrated", "panels": [
            {"kind": "text", "h3": "Qualification is the moat",
             "text": "These chemicals are cheap relative to the machines, but switching a supplier means re-qualifying "
                     "the process — months to years of testing on production lines where a defect costs a fortune. That "
                     "qualification barrier, not cost or scarcity, is what keeps each input in a few hands. It is the "
                     "same capability mechanism as chip fabs and turbine blades, applied to the consumables that feed "
                     "them.",
             "flag": "qualification, not scarcity"},
        ]},
    ],
    "trade_intro": "BACI carries photographic chemical preparations (370790, where photoresist sits) but cannot isolate "
                   "semiconductor-grade resist, and the gases, slurries and pellicles scatter across many chemical and "
                   "machinery headings. Read the shares below as a coarse proxy only — the concentration that matters "
                   "is a qualified-supplier fact, not a customs one.",
    "method": [
        {"stage": "Photoresist", "lens": "SEMI / industry share", "why": "~90% Japan — the sharpest input chokepoint"},
        {"stage": "Gases & slurries", "lens": "specialty-gas / CMP analyses", "why": "each a few qualified suppliers"},
        {"stage": "Barrier", "lens": "process qualification", "why": "re-qualifying takes years — the moat"},
        {"stage": "Trade", "lens": "BACI 370790 photo-chemicals", "why": "resist not separable; inputs scattered — flagged proxy"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- semiconductor inputs, photoresist ~90pct Japan + gases/CMP; qualification moat")
