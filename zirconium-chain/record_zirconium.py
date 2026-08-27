"""Evidence JSON for the zirconium / hafnium chain pilot. Uniform schema. Public sources.
Nuclear-grade cladding + the chemical-twin separation. Run: python record_zirconium.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "zirconium_chain.json")

SRC = {
    "usgs_zirconium": {"title": "USGS Mineral Commodity Summaries 2026 — Zirconium and Hafnium", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-zirconium.pdf"},
    "iaea_cladding": {"title": "IAEA — zirconium alloys for nuclear fuel cladding", "year": 2024, "url": "https://www.iaea.org/topics/nuclear-fuel-cycle"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — zircon", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Zirconium / hafnium chain",
    "chokepoint": {"product": "Nuclear fuel cladding", "stage": "Nuclear-grade sponge", "mechanism": "capability", "physics": "Nuclear-grade (hafnium-free) zirconium sponge + cladding is a qualified capability held by a few; Zr and Hf are chemical twins, hard to separate", "holder": "FR · US · RU · CN", "share": "few", "control": "—", "conf": "estimate"},
    "published": True,
    "related": [{"href": "../nuclear-chain/nuclear-chain.html", "label": "Nuclear fuel chain"}, {"href": "../titanium-chain/titanium-chain.html", "label": "Titanium chain"}, {"href": "../silicon-chip/silicon-chain.html", "label": "Silicon → chips chain"}],
    "accent": "#5a7a7a",
    "eyebrow": "Product-chain pilot · the metal that clads the fuel",
    "h1": "The metal that clads nuclear fuel — and its twin that must not be there",
    "deck": "Every fuel rod in a water-cooled reactor is sheathed in zirconium alloy: it resists corrosion at "
            "temperature and is nearly transparent to neutrons. But it must be hafnium-free, because hafnium — "
            "zirconium's chemical twin, always found with it — absorbs neutrons and would poison the reaction. "
            "Separating the two identical-acting elements is a hard, qualified capability held by a few.",
    "byline": "zircon sand (by-product of Ti mining) ≠ Zr/Hf separation ≠ nuclear-grade sponge & cladding (a few) ≠ fuel rods",
    "correction": "Zirconium's chokepoint is not the ore — zircon sand is abundant, mostly a by-product of "
                  "titanium-mineral (and tin) mining, used in vast quantities for ceramics and refractories. The "
                  "chokepoint is nuclear-grade zirconium: cladding must have the hafnium removed, and because zirconium "
                  "and hafnium are near-identical chemical twins, separating them and making qualified reactor-grade "
                  "sponge is done by only a handful of producers (in France, the US, Russia and China). The removed "
                  "hafnium is itself a valuable metal.",
    "stats": [
        {"v": "cladding", "l": "zirconium-alloy tubes hold the fuel — corrosion-resistant, neutron-transparent", "conf": "measured"},
        {"v": "hafnium-free", "l": "cladding needs the neutron-absorbing hafnium twin removed", "conf": "measured"},
        {"v": "chemical twins", "l": "Zr and Hf act almost identically — separation is a hard, qualified capability", "conf": "measured"},
        {"v": "zircon abundant", "l": "the ore is a by-product of titanium sands — the chokepoint is the processing", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Zircon sand", "t": "a by-product of titanium-mineral (and tin) mining — abundant; Australia, South Africa"},
        {"n": "2 · Separate Zr/Hf", "t": "the hard step: remove hafnium from zirconium — chemical twins"},
        {"n": "3 · Nuclear sponge", "t": "reactor-grade zirconium sponge and alloy (Zircaloy) — a few qualified producers"},
        {"n": "4 · Cladding / end use", "t": "fuel-rod cladding; plus ceramics/refractories (bulk zircon) and hafnium uses"},
    ],
    "sections": [
        {"h2": "1 · The ore is easy; the grade is hard", "panels": [
            {"kind": "text", "h3": "Zircon is a by-product, and abundant", "conf": "measured",
             "text": "Most zirconium is used, as zircon, in ceramics, foundry sand and refractories — a large, "
                     "unremarkable market supplied as a by-product of mining titanium-mineral sands (ilmenite, rutile) "
                     "and tin, chiefly in Australia and South Africa. At this level there is no chokepoint. The "
                     "strategic sliver is the small fraction turned into nuclear-grade metal.",
             "note": "USGS Zirconium and Hafnium 2026.", "flag": "the bulk is not the issue"},
            {"kind": "big", "h3": "Why the grade is the chokepoint", "big": "hafnium-free", "conf": "measured",
             "text": "Reactor cladding must be zirconium with the hafnium taken out, because hafnium soaks up neutrons "
                     "and would choke the chain reaction. But zirconium and hafnium are chemical twins — they behave "
                     "almost identically — so separating them is genuinely difficult, and turning the result into "
                     "qualified reactor-grade Zircaloy is done by only a handful of plants worldwide.",
             "note": "IAEA; USGS."},
        ]},
        {"h2": "2 · A capability held by a few", "panels": [
            {"kind": "text", "h3": "France, the US, Russia, China",
             "text": "Nuclear-grade zirconium sponge and cladding production is concentrated among a few qualified "
                     "producers — in France, the United States, Russia and China — because it demands both the Zr/Hf "
                     "separation and years of nuclear qualification. It is the same shape as uranium enrichment (see "
                     "the nuclear chain): the mine is not the constraint; the licensed, capital- and know-how-heavy "
                     "processing step is.",
             "flag": "a qualification chokepoint, like enrichment"},
        ]},
        {"h2": "3 · The valuable twin", "panels": [
            {"kind": "text", "h3": "Hafnium, once removed, is a metal in demand",
             "text": "The hafnium separated out of reactor-grade zirconium is not waste: it goes into superalloys for "
                     "jet engines, into control rods (where its neutron appetite is a feature), and — as hafnium oxide "
                     "— into the high-k gate dielectrics of advanced chips (see the silicon-chip chain). So the same "
                     "difficult separation yields two strategic materials at once, tying the nuclear and semiconductor "
                     "chains to one processing step.",
             "flag": "one separation, two strategic metals"},
        ]},
    ],
    "trade_intro": "BACI carries zircon ore (261510) and unwrought zirconium (810920), but not the split between bulk "
                   "ceramic-grade zircon and nuclear-grade metal, and hafnium hides in the shared minor-metals basket. "
                   "Read the shares below as the raw and semi-processed zirconium; the nuclear-grade chokepoint is not "
                   "separable in customs data.",
    "method": [
        {"stage": "Zircon", "lens": "USGS zircon share", "why": "abundant, a titanium-sands by-product — not the chokepoint"},
        {"stage": "Separate", "lens": "Zr/Hf separation", "why": "chemical twins — the hard step"},
        {"stage": "Nuclear grade", "lens": "reactor-sponge producers", "why": "a few qualified plants (FR/US/RU/CN)"},
        {"stage": "Trade", "lens": "BACI 261510 zircon + 810920 zirconium", "why": "raw/semi forms; nuclear grade + hafnium not separable — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- zirconium, nuclear cladding needs Hf-free Zr; twin-separation capability (few)")
