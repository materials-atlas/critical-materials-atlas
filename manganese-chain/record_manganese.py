"""Evidence JSON for the manganese chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_manganese.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "manganese_chain.json")
MINED = os.path.join(os.path.dirname(HERE), "out", "mined_years.json")


def hist_points(material, country):
    node = json.load(open(MINED, encoding="utf-8")).get(material, {})
    return [{"y": int(y), "v": next((x["v"] for x in node[y] if x["c"] == country), 0)} for y in sorted(node, key=int)]


SRC = {
    "usgs_manganese": {"title": "USGS Mineral Commodity Summaries 2026 — Manganese", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-manganese.pdf"},
    "iea_minerals_2025": {"title": "IEA, Global Critical Minerals Outlook 2025", "year": 2025, "url": "https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — manganese mine production", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Manganese chain",
    "accent": "#7a4a4a",
    "eyebrow": "Product-chain pilot · the metal steel can't do without",
    "h1": "The manganese mine is spread across Africa — the battery-grade refining is China",
    "deck": "Almost every tonne of steel contains manganese — there is no substitute for what it does in steelmaking, "
            "and it is quietly essential to civilisation's most-used metal. Its ore is mined across South Africa, "
            "Gabon and Australia, a genuinely diversified map. But the high-purity manganese that batteries need is "
            "refined overwhelmingly in China.",
    "byline": "ore (South Africa, Gabon, Australia) ≠ ferro-manganese / EMM / sulphate (China) ≠ steel alloy or battery cathode",
    "correction": "Manganese is two stories. As a steel additive — ~90% of demand, and irreplaceable for removing "
                  "sulphur and adding hardness — its ore is reassuringly diversified: South Africa, Gabon and Australia "
                  "lead the mine. But the refined forms that matter for batteries — electrolytic manganese metal (EMM) "
                  "and high-purity manganese sulphate — are made overwhelmingly in China. So the same metal is "
                  "low-risk for steel and a concentrated chokepoint for the battery chain.",
    "stats": [
        {"v": "~90%", "l": "of manganese goes into steel — with no substitute in steelmaking", "conf": "measured"},
        {"v": "ZA · GA · AU", "l": "the mine is diversified: South Africa, Gabon, Australia lead", "conf": "measured"},
        {"v": "~90% China", "l": "electrolytic manganese metal and battery-grade sulphate refining", "conf": "estimate"},
        {"v": "batteries", "l": "high-purity manganese sulphate for NMC and rising LMFP cathodes", "conf": "estimate"},
    ],
    "history": {
        "title": "The mine stayed diversified, 2000 → 2024",
        "conf": "measured",
        "note": "BGS/USGS mine production, from the atlas's own data. South Africa rose to lead (~37%), with Gabon and "
                "Australia strong and China's mine share falling — no single-country ore chokepoint. That is precisely "
                "why the battery risk is downstream: the refining of battery-grade manganese, not the mining of the "
                "ore, is where the concentration sits (in China), and no mine-share chart shows it.",
        "series": [
            {"label": "South Africa", "points": hist_points("manganese", "ZA")},
            {"label": "Gabon", "points": hist_points("manganese", "GA")},
            {"label": "China", "points": hist_points("manganese", "CN")},
        ],
    },
    "hops": [
        {"n": "1 · Mine", "t": "manganese ore — South Africa, Gabon, Australia, Ghana (diversified)"},
        {"n": "2 · Alloy or refine", "t": "ferro-manganese/silico-manganese for steel; EMM and sulphate for batteries"},
        {"n": "3 · Grade split", "t": "steel-grade alloy (bulk) vs high-purity manganese sulphate (battery)"},
        {"n": "4 · End use", "t": "~90% steel; a growing slice into NMC and LMFP battery cathodes"},
    ],
    "sections": [
        {"h2": "1 · For steel, the mine is genuinely diversified", "panels": [
            {"kind": "text", "h3": "No single-country ore chokepoint", "conf": "measured",
             "text": "South Africa holds the largest reserves and leads mining, with Gabon, Australia, Ghana and others "
                     "supplying the rest. Manganese is essential and irreplaceable in steel — it removes sulphur and "
                     "oxygen and adds strength — but because the ore is spread and abundant, the steel industry's "
                     "manganese supply is one of the lower-risk links in this atlas.",
             "note": "USGS MCS 2026.", "flag": "diversified at the mine"},
            {"kind": "text", "h3": "Irreplaceable, but not scarce",
             "text": "There is no substitute for manganese in mainstream steelmaking, so 'essential' it certainly is — "
                     "but essential is not the same as scarce or concentrated. For its dominant use, manganese is a "
                     "reminder that criticality has two axes: importance and supply risk. Here importance is high and "
                     "mine-supply risk is low.",
             "flag": "essential ≠ concentrated"},
        ]},
        {"h2": "2 · For batteries, the refining is China", "panels": [
            {"kind": "big", "h3": "The battery-grade chokepoint", "big": "~90% China", "conf": "estimate",
             "text": "Batteries do not use ore or steel-grade ferroalloy; they need high-purity manganese sulphate, and "
                     "electrolytic manganese metal (EMM) is the usual route to it. Both are made overwhelmingly in "
                     "China. So as manganese-rich cathodes (NMC, and cheaper high-manganese LMFP) grow, the battery "
                     "world inherits a concentrated refining dependency that the diversified ore map completely hides.",
             "note": "IEA; USGS: EMM and high-purity sulphate are China-dominated."},
            {"kind": "text", "h3": "The same mine-versus-refine split, once more",
             "text": "Manganese joins lithium, cobalt, nickel and graphite in the atlas's recurring pattern: a "
                     "reasonable mine map, a concentrated refining step. Securing battery manganese is not about the "
                     "South African or Gabonese mine; it is about building high-purity sulphate capacity outside China "
                     "— a processing problem, not a mining one.",
             "flag": "the refinery, not the mine"},
        ]},
        {"h2": "3 · A rising battery role", "panels": [
            {"kind": "text", "h3": "Cheap, abundant, and increasingly wanted",
             "text": "Manganese is attractive to battery makers precisely because it is cheap and abundant relative to "
                     "cobalt and nickel — high-manganese and LMFP chemistries lean on it to cut cost. That makes the "
                     "battery-grade refining chokepoint more important over time, even as the ore stays comfortable: a "
                     "growing dependency hiding behind a reassuring mine map.",
             "flag": "demand rising where the chokepoint is"},
        ]},
    ],
    "trade_intro": "BACI carries manganese ores (260200) and ferro-manganese (720211), but not electrolytic manganese "
                   "metal or battery-grade manganese sulphate cleanly, which is where China's concentration sits. Read "
                   "the shares below as the ore and the steel-grade alloy — the diversified part — not the battery-grade "
                   "refining, which trade data does not isolate.",
    "method": [
        {"stage": "Mine", "lens": "USGS/BGS mine share + history", "why": "diversified (South Africa, Gabon, Australia) — low risk"},
        {"stage": "Refine", "lens": "EMM + high-purity sulphate", "why": "~90% China — the battery-grade chokepoint"},
        {"stage": "Use", "lens": "steel vs battery grade", "why": "~90% steel (irreplaceable); rising battery slice"},
        {"stage": "Trade", "lens": "BACI 260200 ore + 720211 ferro-manganese", "why": "ore/alloy only; battery grade not separable — flagged"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- manganese, mine diversified (ZA/GA/AU) but battery-grade ~90pct China")
