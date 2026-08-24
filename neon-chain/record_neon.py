"""Evidence JSON for the neon / specialty-gas (lithography) chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_neon.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "neon_chain.json")

SRC = {
    "usgs_helium": {"title": "USGS Mineral Commodity Summaries 2026 — Helium (rare-gas context)", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-helium.pdf"},
    "csis_neon": {"title": "CSIS, Semiconductors and the Ukraine war — neon supply", "year": 2022, "url": "https://www.csis.org/analysis/semiconductor-supply-chain-and-russias-invasion-ukraine"},
    "iea_semi": {"title": "IEA / industry analyses of semiconductor specialty gases", "year": 2023, "url": "https://www.iea.org/reports/the-state-of-clean-technology-manufacturing"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Neon / specialty-gas chain",
    "chokepoint": {"product": "Chip lithography", "stage": "Air separation", "mechanism": "byproduct", "physics": "By-product of steel-plant air separation — captured, not made", "holder": "(was Ukraine)", "share": "~half", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../silicon-chip/silicon-chain.html", "label": "Silicon-chip chain"}, {"href": "../helium-chain/helium-chain.html", "label": "Helium chain"}],
    "accent": "#7a4a7a",
    "eyebrow": "Product-chain pilot · the gas inside the lithography laser",
    "h1": "Chip lithography runs on a gas that Ukraine once supplied half the world's supply of",
    "deck": "Deep-ultraviolet lithography — the step that patterns most of the world's chips — uses excimer lasers "
            "whose light comes from neon gas. Neon is a by-product of the air-separation units at large steel plants, "
            "and a strikingly large share of the semiconductor-grade supply came from Ukraine. The 2022 invasion "
            "showed how thin that link was.",
    "byline": "air-separation (steel plant) ≠ crude neon ≠ semiconductor-grade neon (Ukraine-heavy) ≠ the lithography laser",
    "correction": "Neon looks trivial — it is 'just' a noble gas in the air — yet purified, semiconductor-grade neon is "
                  "a genuine chokepoint under chipmaking. It is captured as a by-product of the air-separation plants "
                  "attached to steelworks, and before 2022 roughly half of it came from Ukraine (with Russian feedstock "
                  "links). The war spiked prices many-fold and forced a scramble to diversify — a thin, invisible "
                  "dependency the customs data cannot even see.",
    "stats": [
        {"v": "~half", "l": "Ukraine's estimated pre-2022 share of semiconductor-grade neon", "conf": "measured"},
        {"v": "lithography", "l": "neon is the medium in DUV excimer lasers that pattern chips", "conf": "measured"},
        {"v": "steel by-product", "l": "captured at air-separation units, historically ex-Soviet steelworks", "conf": "measured"},
        {"v": "2022 shock", "l": "the invasion spiked neon prices many-fold and forced diversification", "conf": "estimate"},
    ],
    "hops": [
        {"n": "1 · Air separation", "t": "neon captured as a trace by-product when steel plants separate air for oxygen"},
        {"n": "2 · Crude neon", "t": "collected and shipped; historically concentrated in Ukraine and Russia"},
        {"n": "3 · Semiconductor grade", "t": "purified to ultra-high purity for laser use — few qualified suppliers"},
        {"n": "4 · Lithography", "t": "the working gas in ArF/KrF excimer lasers that expose chip wafers"},
    ],
    "sections": [
        {"h2": "1 · A trace gas that gates chipmaking", "panels": [
            {"kind": "big", "h3": "The Ukraine concentration", "big": "~half", "conf": "measured",
             "text": "Before 2022, roughly half of the world's semiconductor-grade neon was estimated to come from "
                     "Ukraine, where companies purified the crude neon captured at steelworks (some feedstock linked to "
                     "Russian plants). A material almost no one lists as critical turned out to sit under the most "
                     "advanced step in electronics — and in an active war zone.",
             "note": "CSIS; industry estimates."},
            {"kind": "text", "h3": "Why neon, specifically",
             "text": "Deep-ultraviolet lithography uses excimer lasers — argon-fluoride (193 nm) and krypton-fluoride "
                     "(248 nm) — in which neon is the bulk buffer gas. The volumes per fab are small, but the purity "
                     "and reliability requirements are extreme and the qualified supplier list is short, which is "
                     "exactly what makes a cheap, abundant-in-air gas into a chokepoint.",
             "flag": "abundant in air, scarce at grade"},
        ]},
        {"h2": "2 · The shock, and the response", "panels": [
            {"kind": "text", "h3": "2022: prices spiked, buyers scrambled", "conf": "estimate",
             "text": "When Russia invaded Ukraine, neon output was disrupted and prices rose many-fold. Chipmakers had "
                     "stockpiled and quickly moved to diversify — US, Korean and Chinese air-separation and "
                     "purification capacity expanded, and steelmakers added neon recovery. The chokepoint is being "
                     "rebuilt away from one region, but it revealed how invisible such a dependency can be until it "
                     "breaks.",
             "note": "CSIS; industry reporting.", "flag": "diversifying after the break"},
        ]},
        {"h2": "3 · The wider specialty-gas basket", "panels": [
            {"kind": "text", "h3": "Neon is one of several thin links",
             "text": "The same story applies to other electronic specialty gases and rare gases — krypton and xenon "
                     "(also air-separation by-products), and fluorinated process gases (tied to the fluorine chain). "
                     "Each is small in volume, high in purity, and concentrated among few suppliers. Together they are "
                     "a quiet, distributed set of chokepoints under semiconductor manufacturing that rarely appear on "
                     "critical-materials lists.",
             "flag": "small volumes, outsized leverage"},
        ]},
    ],
    "trade_intro": "BACI carries neon only inside the shared 'rare gases' line (280429), together with helium, krypton "
                   "and xenon, so semiconductor-grade neon cannot be isolated in customs data — the dependency that "
                   "matters is literally invisible in trade statistics. Read the shares below as the whole rare-gas "
                   "basket, not a neon series.",
    "method": [
        {"stage": "Source", "lens": "air-separation by-product", "why": "captured at steelworks; historically Ukraine-heavy"},
        {"stage": "Grade", "lens": "semiconductor-purity supply", "why": "few qualified suppliers — the real chokepoint"},
        {"stage": "Shock", "lens": "2022 price spike & diversification", "why": "revealed and then loosened the dependency"},
        {"stage": "Trade", "lens": "BACI 280429 rare gases", "why": "neon not separable from helium/krypton/xenon — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- neon, ~half Ukraine pre-2022; DUV lithography; 2022 shock")
