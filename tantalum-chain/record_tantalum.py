"""Evidence JSON for the tantalum / capacitor chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_tantalum.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "tantalum_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_tantalum": {"title": "USGS Mineral Commodity Summaries 2026 — Tantalum", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-tantalum.pdf"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — tantalum mine production", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "oecd_3tg": {"title": "OECD Due Diligence Guidance for Responsible Mineral Supply Chains", "year": 2016, "url": "https://www.oecd.org/corporate/mne/mining.htm"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Tantalum / capacitor chain",
    "chokepoint": {"product": "Capacitors", "stage": "Mine (3TG)", "mechanism": "governance", "physics": "~70% from DRC/Rwanda artisanal mining — a conflict-mineral supply, not a unique deposit", "holder": "DRC · Rwanda", "share": "~70%", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../tin-chain/tin-chain.html", "label": "Tin / solder chain"}, {"href": "../silicon-chip/silicon-chain.html", "label": "Silicon-chip chain"}],
    "accent": "#6a5a4a",
    "eyebrow": "Product-chain pilot · the capacitor in every device",
    "h1": "The capacitor metal comes mostly from a conflict zone",
    "deck": "Tantalum makes the tiny, ultra-reliable capacitors inside phones, cars, aircraft, medical implants and "
            "weapons. About two-thirds of it is mined in Central Africa — the Democratic Republic of the Congo and "
            "Rwanda — which makes it a '3TG' conflict mineral, while the powder and capacitor processing concentrate "
            "elsewhere.",
    "byline": "coltan (~70% DRC + Rwanda) ≠ tantalum powder (processing) ≠ the capacitor ≠ the device",
    "correction": "Tantalum is a small-volume metal with an outsized reach: its capacitors sit in almost every "
                  "high-reliability electronic device, and there is no clean substitute for their size-to-performance. "
                  "The exposure is twofold — the mine is ~70% in the DR Congo and Rwanda, so tantalum carries "
                  "conflict-mineral due-diligence obligations, and the downstream powder and capacitor making are "
                  "concentrated in a few processors, led by China.",
    "stats": [
        {"v": "~70%", "l": "of tantalum mined in the DR Congo and Rwanda (Central Africa)", "conf": "measured"},
        {"v": "capacitors", "l": "the dominant use — tantalum capacitors in high-reliability electronics", "conf": "measured"},
        {"v": "3TG", "l": "a conflict mineral (tin, tantalum, tungsten, gold) with due-diligence rules", "conf": "measured"},
        {"v": "no easy sub", "l": "unmatched volumetric efficiency in a tiny, stable capacitor", "conf": "estimate"},
    ],
    "history": {
        "title": "The mine sits in Central Africa, 2019 → 2023",
        "conf": "measured",
        "note": "BGS/USGS mine production, from the atlas's own data (the reliable public series is short, 2019–2023). "
                "The DR Congo and Rwanda together mine roughly 70% of the world's tantalum, with Brazil the main "
                "outside source. This is one of the atlas's mine-side chokepoints — but a governance one (artisanal, "
                "conflict-linked), not a pure geological monopoly.",
        "series": [
            {"label": "DR Congo", "points": hist_points("tantalum", "CD")},
            {"label": "Rwanda", "points": hist_points("tantalum", "RW")},
            {"label": "Brazil", "points": hist_points("tantalum", "BR")},
        ],
    },
    "hops": [
        {"n": "1 · Coltan / mine", "t": "columbite-tantalite ore — ~70% DR Congo and Rwanda, much of it artisanal"},
        {"n": "2 · Process", "t": "concentrate refined to tantalum oxide, then metal — a few processors, China-led"},
        {"n": "3 · Powder & wire", "t": "high-purity tantalum powder and wire — the capacitor feedstock"},
        {"n": "4 · Capacitor / device", "t": "tantalum capacitors in phones, cars, aircraft, implants and defence"},
    ],
    "sections": [
        {"h2": "1 · The mine is a conflict-mineral chokepoint", "panels": [
            {"kind": "big", "h3": "Where it comes out of the ground", "big": "~70% Central Africa", "conf": "measured",
             "text": "The DR Congo and Rwanda together supply roughly 70% of mined tantalum, much of it from artisanal "
                     "and small-scale mining. Because that mining has funded armed groups in the Great Lakes region, "
                     "tantalum is one of the four '3TG' minerals subject to conflict-mineral due-diligence laws — the "
                     "same regime that governs the tin in the solder next to it (see the tin chain).",
             "note": "USGS MCS 2026; OECD due-diligence guidance."},
            {"kind": "text", "h3": "Traceability, not just tonnage",
             "text": "The response to this chokepoint is unusual: bag-and-tag traceability schemes (iTSCi and others) "
                     "certify ore from validated mines. It is a governance fix rather than a geological one — the metal "
                     "exists in many countries, but responsible, documented supply is the scarce thing, and it shapes "
                     "who Western manufacturers can legally buy from.",
             "flag": "responsible supply is the scarce part"},
        ]},
        {"h2": "2 · Why tantalum, and why it is hard to replace", "panels": [
            {"kind": "text", "h3": "The capacitor's volumetric efficiency", "conf": "measured",
             "text": "Tantalum capacitors pack a large capacitance into a tiny, stable, reliable package — ideal where "
                     "space is tight and failure is unacceptable: smartphones, automotive electronics, hearing aids and "
                     "pacemakers, avionics and missiles. Multilayer ceramic capacitors substitute in some roles, but "
                     "for high-reliability, high-density uses tantalum holds, so the dependence persists.",
             "note": "USGS: capacitors are the leading tantalum use.", "flag": "reliability where failure isn't allowed"},
        ]},
        {"h2": "3 · The processing sits downstream", "panels": [
            {"kind": "text", "h3": "Powder and capacitors concentrate elsewhere",
             "text": "As with rare earths and graphite, the ore's origin and the processing geography are two different "
                     "maps: turning concentrate into high-purity tantalum powder and finished capacitors is "
                     "concentrated among a few processors (in China and a handful of specialists), and recycling from "
                     "electronic scrap supplies a meaningful share. The mine is a governance chokepoint; the powder is "
                     "an industrial one.",
             "flag": "ore map ≠ processing map"},
        ]},
    ],
    "trade_intro": "BACI carries tantalum ore only inside the shared niobium/tantalum/vanadium ore line (261590), and "
                   "unwrought tantalum and powder under 810320, but it cannot isolate capacitor-grade material or the "
                   "tantalum inside finished electronics. Read the shares below as the raw and semi-processed forms, "
                   "not the conflict-mineral origin, which traceability schemes — not customs — track.",
    "method": [
        {"stage": "Mine", "lens": "USGS/BGS mine share + history", "why": "~70% DR Congo + Rwanda — a governance chokepoint"},
        {"stage": "Process", "lens": "powder/capacitor processing", "why": "concentrated downstream, China-led"},
        {"stage": "Due diligence", "lens": "3TG / OECD guidance", "why": "responsible supply is the binding constraint"},
        {"stage": "Trade", "lens": "BACI 261590 ore + 810320 tantalum", "why": "shared ore line; capacitor grade not separable — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- tantalum, ~70pct DRC+Rwanda (3TG); capacitors; China processing")
