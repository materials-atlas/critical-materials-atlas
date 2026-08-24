"""Evidence JSON for the titanium chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_titanium.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "titanium_chain.json")

SRC = {
    "usgs_ti_sponge": {"title": "USGS Mineral Commodity Summaries 2026 — Titanium Sponge", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-titanium-sponge.pdf"},
    "usgs_ti_mineral": {"title": "USGS Mineral Commodity Summaries 2026 — Titanium Mineral Concentrates", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-titanium-mineral.pdf"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — titanium minerals", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Titanium chain",
    "chokepoint": {"product": "Aerospace metal", "stage": "Sponge + mill", "mechanism": "capability", "physics": "Kroll sponge + qualified aerospace mill — batch, certification-gated (VSMPO etc.)", "holder": "CN · JP · RU · KZ", "share": "—", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../aerospace-chain/aerospace-chain.html", "label": "Aerospace chain"}, {"href": "../defence-chain/defence-chain.html", "label": "Defence chain"}],
    "accent": "#6a6a7a",
    "eyebrow": "Product-chain pilot · pigment, and the metal that flies",
    "h1": "Ninety percent of titanium is white paint — the other tenth flies and fights",
    "deck": "Titanium is two industries wearing one name. About 90% of it becomes titanium dioxide, the white pigment "
            "in paint, plastic and paper — a large, diversified market. The strategic sliver is titanium metal, made as "
            "'sponge' by the Kroll process, for jet engines, airframes, armour and implants — and that sponge is "
            "concentrated in China, Japan, Russia and Kazakhstan.",
    "byline": "ilmenite/rutile ore ≠ TiO2 pigment (~90%, diversified) ≠ titanium sponge (Kroll) ≠ aerospace & defence metal",
    "correction": "Talking about 'titanium supply' hides a split. The bulk — ~90% — is TiO2 pigment, whose ore "
                  "(ilmenite, rutile) is mined widely (Australia, South Africa, China, Mozambique) and is not a "
                  "geopolitical chokepoint. The exposure is the ~10% that becomes aerospace-grade metal: titanium "
                  "sponge production sits in China, Japan, Russia and Kazakhstan, and Russia's VSMPO-Avisma is a "
                  "critical supplier to Boeing and Airbus — a strategic dependency the pigment tonnage masks.",
    "stats": [
        {"v": "~90%", "l": "of titanium is TiO2 pigment, not metal — a diversified market", "conf": "measured"},
        {"v": "sponge", "l": "aerospace-grade metal via the Kroll process — China, Japan, Russia, Kazakhstan", "conf": "measured"},
        {"v": "VSMPO", "l": "Russia's VSMPO-Avisma is a top aerospace titanium-sponge supplier", "conf": "measured"},
        {"v": "aero + defence", "l": "jet engines, airframes, armour and medical implants — no easy substitute", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Ore", "t": "ilmenite and rutile — mined widely (Australia, South Africa, China, Mozambique)"},
        {"n": "2a · TiO2 pigment", "t": "~90% of titanium — white pigment for paint, plastic, paper (diversified)"},
        {"n": "2b · Sponge (Kroll)", "t": "the metal route: ore → TiCl4 → titanium sponge — few producers"},
        {"n": "3 · Mill & alloy", "t": "sponge melted into ingot, forged into aerospace and medical mill products"},
    ],
    "sections": [
        {"h2": "1 · The bulk is pigment, and it's diversified", "panels": [
            {"kind": "big", "h3": "What most titanium becomes", "big": "~90% pigment", "conf": "measured",
             "text": "Titanium dioxide is the brightest white known and the standard pigment in paints, coatings, "
                     "plastics and paper. Its feedstock — ilmenite and rutile sands — is mined in Australia, South "
                     "Africa, China, Mozambique, Canada and elsewhere, and pigment is made by several large producers. "
                     "This dominant use is not a chokepoint; it is a broad, competitive commodity market.",
             "note": "USGS Titanium Mineral Concentrates 2026."},
            {"kind": "text", "h3": "So 'titanium is critical' needs a qualifier",
             "text": "Because the tonnage is dominated by pigment, aggregate 'titanium' statistics look reassuringly "
                     "diversified. The strategic risk is invisible at that level — it lives entirely in the small metal "
                     "fraction, which is a different supply chain with different geography. Averaging the two together "
                     "hides the very thing that matters.",
             "flag": "the average hides the risk"},
        ]},
        {"h2": "2 · The strategic sliver: aerospace metal", "panels": [
            {"kind": "text", "h3": "Sponge, the Kroll bottleneck", "conf": "measured",
             "text": "Titanium metal starts as 'sponge', made by the energy-intensive Kroll process (ore → titanium "
                     "tetrachloride → magnesium reduction). Sponge production is concentrated in China, Japan, Russia "
                     "and Kazakhstan. Russia's VSMPO-Avisma is one of the world's largest aerospace-sponge and "
                     "mill-product suppliers, deeply embedded in Boeing and Airbus supply chains — which made titanium "
                     "a live sanctions dilemma after 2022.",
             "note": "USGS Titanium Sponge 2026.", "flag": "aerospace depends on a few sponge makers"},
        ]},
        {"h2": "3 · Why aerospace can't easily switch", "panels": [
            {"kind": "text", "h3": "Strength, lightness, and years of qualification",
             "text": "Titanium alloys combine high strength, low weight, heat resistance and corrosion resistance — "
                     "ideal for jet-engine parts, airframes, armour and, being biocompatible, for medical implants. "
                     "There is no drop-in substitute for these roles, and aerospace parts must be qualified over years, "
                     "so a sponge supplier cannot be swapped quickly. The chokepoint is narrow, deep and slow to "
                     "diversify — the opposite of the pigment market beside it.",
             "flag": "narrow, deep, slow to replace"},
        ]},
    ],
    "trade_intro": "BACI carries titanium ores (261400) and unwrought titanium and powder incl. sponge (810820), but "
                   "not the split between pigment-grade and aerospace-grade, nor finished mill products. Read the "
                   "shares below as raw ore and unwrought metal; the strategic aerospace-sponge concentration is only "
                   "partly visible.",
    "method": [
        {"stage": "Ore", "lens": "USGS mineral-concentrate share", "why": "ilmenite/rutile mined widely — not a chokepoint"},
        {"stage": "Pigment", "lens": "USGS TiO2 end-use", "why": "~90% of titanium; diversified commodity"},
        {"stage": "Sponge", "lens": "USGS titanium-sponge share", "why": "the strategic ~10% — China/Japan/Russia/Kazakhstan"},
        {"stage": "Trade", "lens": "BACI 261400 ore + 810820 titanium", "why": "pigment vs aerospace grade not separable — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- titanium, ~90pct pigment (diversified) vs aerospace sponge (China/JP/RU/KZ)")
