"""Evidence JSON for the cement chain pilot. Uniform schema. Public sources.
The deliberate counter-example: a material with no chokepoint, only carbon.
Shared chainview renderer, per-figure confidence tags. Run: python record_cement.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "cement_chain.json")

SRC = {
    "usgs_cement": {"title": "USGS Mineral Commodity Summaries 2026 — Cement", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-cement.pdf"},
    "iea_cement": {"title": "IEA, Cement — tracking & net-zero roadmap", "year": 2023, "url": "https://www.iea.org/energy-system/industry/cement"},
    "gcca": {"title": "Global Cement and Concrete Association — Concrete Future roadmap", "year": 2024, "url": "https://gccassociation.org/concretefuture/"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Cement chain",
    "chokepoint": {"product": "Concrete", "stage": "Kiln (local)", "mechanism": "diffuse", "physics": "Limestone + kilns are everywhere and cement is cheap + heavy → made locally; no chokepoint, only CO₂", "holder": "local, everywhere", "share": "—", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../steel-chain/steel-chain", "label": "Primary / green-steel chain"}, {"href": "../aluminium-chain/aluminium-chain", "label": "Aluminium chain"}, {"href": "../ammonia-chain/ammonia-chain", "label": "Ammonia / nitrogen chain"}],
    "accent": "#8a8a8a",
    "eyebrow": "Product-chain pilot · the counter-example",
    "h1": "The most-used material on Earth has no chokepoint — only a carbon problem",
    "deck": "Concrete is the second-most-consumed substance after water, and cement is what binds it. Yet it is the "
            "atlas's clean counter-example: limestone is everywhere, kilns are everywhere, and cement is too cheap and "
            "heavy to ship far — so there is no geographic chokepoint to find. The only binding constraint is carbon: "
            "cement alone is about 8% of global CO₂.",
    "byline": "limestone (everywhere) ≠ clinker (kiln, ~1450°C) ≠ cement ≠ concrete — no chokepoint, only emissions",
    "correction": "Every other chain in this atlas asks where the bottleneck is. Cement is the case that proves the "
                  "rule by having none: its raw material (limestone) is one of the most abundant rocks on Earth, kilns "
                  "are built wherever there is demand, and because cement is cheap and heavy it is made locally almost "
                  "everywhere. China makes about half of it, but not as a chokepoint — everyone makes their own. The "
                  "real problem is not supply security; it is that making it emits ~8% of the world's CO₂, most of it "
                  "unavoidable chemistry.",
    "stats": [
        {"v": "~8%", "l": "of global CO₂ emissions come from cement", "conf": "measured"},
        {"v": "no chokepoint", "l": "limestone and kilns are everywhere; cement is made locally — supply is diffuse", "conf": "measured"},
        {"v": "#2 substance", "l": "concrete is the most-used material on Earth after water", "conf": "measured"},
        {"v": "~60% chemistry", "l": "most cement CO₂ is calcination (limestone → lime), not fuel — hard to abate", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Limestone", "t": "quarried almost everywhere — one of Earth's most abundant rocks"},
        {"n": "2 · Kiln → clinker", "t": "heated to ~1450 °C; limestone calcines to lime, releasing CO₂"},
        {"n": "3 · Cement", "t": "clinker ground with gypsum and supplementary materials into cement"},
        {"n": "4 · Concrete", "t": "cement + aggregate + water — poured locally, near the site"},
    ],
    "sections": [
        {"h2": "1 · Why there is nothing to concentrate", "panels": [
            {"kind": "big", "h3": "The diffuse case", "big": "no chokepoint", "conf": "measured",
             "text": "Limestone, clay and aggregate are abundant and mined near demand; a cement kiln is mature, "
                     "unglamorous technology built wherever there is construction; and cement is so cheap per tonne and "
                     "so heavy that shipping it far makes no economic sense. Every condition that concentrates other "
                     "chains — a scarce deposit, a hard-won capability, a by-product coupling — is simply absent. Cement "
                     "spreads because nothing forces it to gather.",
             "note": "USGS Cement 2026."},
            {"kind": "text", "h3": "China makes half — but not as a lever",
             "text": "China produces roughly half the world's cement, but that reflects the scale of its construction, "
                     "not control of anyone else's supply: the United States, India, Europe and every other region make "
                     "their own. There is no export chokepoint to weaponise, because the material is intrinsically "
                     "local. It is the mirror image of gallium or rare earths.",
             "flag": "big producer, not a chokepoint"},
        ]},
        {"h2": "2 · The real constraint is carbon", "panels": [
            {"kind": "big", "h3": "Cement's climate weight", "big": "~8% of CO₂", "conf": "measured",
             "text": "Making cement emits about 8% of global CO₂ — more than aviation and shipping combined. Crucially, "
                     "roughly 60% of that is not from burning fuel but from the chemistry itself: heating limestone "
                     "(calcium carbonate) to make lime releases CO₂ that was locked in the rock. That process emission "
                     "cannot be removed by switching fuels, which is what makes cement one of the hardest sectors to "
                     "decarbonize.",
             "note": "IEA Cement; GCCA."},
            {"kind": "text", "h3": "So the 'so what' is climate, not supply",
             "text": "For cement, the decision layer is not diversification or stockpiles — it is emissions: clinker "
                     "substitution (using less clinker per tonne), supplementary cementitious materials, carbon capture "
                     "on kilns, and novel low-carbon binders. The chain matters enormously, but for a completely "
                     "different reason than the rest of the atlas — which is exactly why it is worth including.",
             "flag": "decarbonize, don't secure"},
        ]},
        {"h2": "3 · What it teaches the layer", "panels": [
            {"kind": "text", "h3": "The rule, working in reverse",
             "text": "Cement is the purest 'diffuse' chain in the Chokepoint Map: a cool-enough, switchable, "
                     "everywhere-available process with no concentrating force, so it never gathered into a chokepoint. "
                     "Setting it beside aluminium or ammonia — bulk materials that DO concentrate, because their key "
                     "step is continuous-hot and power-bound — sharpens the mechanism: concentration is not about "
                     "importance or tonnage, but about whether the binding process can be small and local. Cement can, "
                     "so it is.",
             "flag": "importance ≠ concentration"},
        ]},
    ],
    "trade_intro": "BACI carries cement clinker (252310) and portland cement (252329), but only a small share of cement "
                   "is traded — it moves regionally at most, because it is cheap and heavy. Read the shares below as "
                   "that thin traded margin, not the overwhelmingly local production that defines the chain.",
    "method": [
        {"stage": "Limestone", "lens": "USGS reserves/production", "why": "ubiquitous — no scarcity, no chokepoint"},
        {"stage": "Kiln", "lens": "local clinker capacity", "why": "built near demand; cheap, heavy, local"},
        {"stage": "Carbon", "lens": "IEA/GCCA emissions", "why": "~8% of CO₂, ~60% process chemistry — the real constraint"},
        {"stage": "Trade", "lens": "BACI 252310 clinker + 252329 cement", "why": "a thin traded margin; production is local — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- cement, no chokepoint (limestone+kilns everywhere); only ~8pct CO2")
