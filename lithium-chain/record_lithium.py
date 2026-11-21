"""Evidence JSON for the lithium chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_lithium.py
"""
from __future__ import annotations
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out", "lithium_chain.json")
sys.path.insert(0, ROOT)
import usgs_mcs_cube as U  # noqa: E402

# THE UNIT. Every mine share on this page is tonnes of LITHIUM CONTENT, from the USGS tables, as a
# share of the world total USGS prints (which leaves out US output, withheld). The atlas's other
# yearly file, out/mined_years.json, counts gross tonnes of ore and concentrate: on that basis a
# hard-rock producer looks far bigger than it is, because spodumene concentrate is a few percent
# lithium. This page used it until 21 Nov 2026 and showed Australia at 62% for 2024; by lithium
# content the figure is 37%.
YEARS = range(2000, 2025)
_BY_YEAR = {}
for _y in YEARS:
    _t = U.shares("lithium", "mine", _y)
    _BY_YEAR[_y] = {r.iso3: float(r.share) * 100 for r in _t.itertuples() if r.share == r.share}  # stored as a fraction


def hist_points(iso3):
    return [{"y": y, "v": round(_BY_YEAR[y].get(iso3, 0.0), 1)} for y in YEARS]


def pct(iso3, year=2024):
    return int(round(_BY_YEAR[year][iso3]))


# the 2024 headline must be the figure every other page of the atlas shows
_CORE = {x["c"]: x["v"] for x in json.load(open(os.path.join(ROOT, "out", "mined_shares.json"),
                                                 encoding="utf-8"))["materials"]["lithium"]["mined"]}
for _i3, _i2 in (("AUS", "AU"), ("CHL", "CL"), ("CHN", "CN"), ("ZWE", "ZW")):
    if pct(_i3) != _CORE.get(_i2):
        raise SystemExit(f"lithium {_i3} 2024: this page computes {pct(_i3)}%, out/mined_shares.json "
                         f"says {_CORE.get(_i2)}% - same source and year, so they must agree")
AU = pct("AUS")
PEAK_Y = max(YEARS, key=lambda y: _BY_YEAR[y].get("AUS", 0))
PEAK = pct("AUS", PEAK_Y)


SRC = {
    "usgs_lithium": {"title": "USGS Mineral Commodity Summaries 2026 — Lithium", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-lithium.pdf"},
    "iea_minerals_2025": {"title": "IEA, Global Critical Minerals Outlook 2025", "year": 2025, "url": "https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Lithium chain",
    "chokepoint": {"product": "Battery lithium", "stage": "Conversion", "mechanism": "capability", "physics": "Converting spodumene/brine to battery-grade chemical — the concentrated step, China", "holder": "China", "share": "most", "control": "—", "conf": "estimate"},
    "published": True,
    "related": [{"href": "../battery-chain/battery-chain", "label": "Battery chain"}, {"href": "../cobalt-chain/cobalt-chain", "label": "Cobalt chain"}, {"href": "../nickel-chain/nickel-chain", "label": "Nickel chain"}],
    "accent": "#7a7a3a",
    "eyebrow": "Product-chain pilot · the battery's headline metal",
    "h1": "The lithium mine moved to Australia — the refinery stayed in China",
    "deck": "Lithium is the metal everyone names in the battery story, and its mining actually diversified: Australia's "
            "hard-rock spodumene now leads, with Chile's brine, and fast-rising output from Zimbabwe and Brazil. But "
            "raw lithium is not battery lithium — turning spodumene or brine into battery-grade chemical is "
            "concentrated in China. The chokepoint is the conversion step, not the deposit.",
    "byline": "spodumene (AU) / brine (Chile) ≠ battery-grade chemical (China) ≠ cathode ≠ the cell",
    "correction": "The lithium mine is not the chokepoint — the refinery is. Australia mines the most lithium (hard-rock "
                  "spodumene), the 'Lithium Triangle' of Chile, Argentina and Bolivia holds vast brine reserves, and "
                  "Zimbabwe and Brazil are scaling fast, so ore supply is genuinely multi-country. But most spodumene is "
                  "shipped to China to be converted into battery-grade lithium carbonate and hydroxide — the same "
                  "mine-versus-refine split the atlas finds for cobalt, nickel and graphite.",
    "stats": [
        {"v": f"{AU}%", "l": "Australia's share of lithium mined in 2024, by lithium content (USGS)", "conf": "measured"},
        {"v": "China", "l": "converts most spodumene into battery-grade chemical — the real chokepoint", "conf": "measured"},
        {"v": "brine vs rock", "l": "two production routes: fast hard-rock, slow high-reserve brine", "conf": "measured"},
        {"v": "reserves ≠ output", "l": "Chile and Argentina hold huge brine reserves but mine far less", "conf": "estimate"},
    ],
    "history": {
        "title": "Who mines lithium, 2000 to 2024, by lithium content",
        "conf": "measured",
        "note": "USGS Mineral Commodity Summaries: mine production in tonnes of lithium content, as a share of the "
                "world total USGS prints, which leaves out United States output (withheld). Chile's brine led for most "
                "of the 2000s. Australia's hard-rock mines pulled clear in 2017 and peaked at "
                f"{PEAK}% in {PEAK_Y}. By 2024 Australia was at {AU}%, Chile {pct('CHL')}%, China {pct('CHN')}% and "
                f"Zimbabwe {pct('ZWE')}%. A count in gross tonnes of ore and concentrate would show Australia much "
                "higher, because spodumene concentrate is only a few percent lithium. Mining is spread over "
                "several countries. Conversion into battery chemicals is more concentrated, and a mine-share "
                "chart cannot show it.",
        "series": [
            {"label": "Australia", "points": hist_points("AUS")},
            {"label": "Chile", "points": hist_points("CHL")},
            {"label": "China", "points": hist_points("CHN")},
            {"label": "Zimbabwe", "points": hist_points("ZWE")},
        ],
    },
    "hops": [
        {"n": "1 · Mine", "t": "hard-rock spodumene (Australia) or brine (Chile, Argentina) — multi-country"},
        {"n": "2 · Refine", "t": "spodumene/brine → battery-grade carbonate or hydroxide — mostly China"},
        {"n": "3 · Cathode", "t": "lithium chemical into NMC, LFP and other cathode powders"},
        {"n": "4 · Cell", "t": "the battery — lithium is the charge carrier in every lithium-ion cell"},
    ],
    "sections": [
        {"h2": "1 · Two ways to make lithium, one refiner", "panels": [
            {"kind": "big", "h3": "Where lithium is mined", "big": f"{AU}% Australia", "conf": "measured",
             "text": "Australia leads because hard-rock spodumene mines can be built and expanded quickly, and it ships "
                     "the concentrate to converters. Brine operations in Chile and Argentina hold far larger reserves "
                     "but evaporate slowly over months, so their share of annual output is smaller than their share of "
                     "the ground. Two very different clocks feed the same battery.",
             "note": f"USGS MCS 2026, 2024 mine production by lithium content. Chile {pct('CHL')}%, China {pct('CHN')}%."},
            {"kind": "text", "h3": "The conversion step is the chokepoint",
             "text": "Neither spodumene nor raw brine is usable in a cell — both must be refined to high-purity "
                     "carbonate or hydroxide. That conversion is concentrated in China, which processes most of the "
                     "world's spodumene (much of it Australian) into battery-grade chemical. So even Australian lithium "
                     "typically becomes a battery only after a Chinese refinery, as with cobalt and graphite.",
             "flag": "the refinery, not the rock"},
        ]},
        {"h2": "2 · Reserves are not the same as supply", "panels": [
            {"kind": "text", "h3": "The Lithium Triangle holds it; Australia ships it", "conf": "estimate",
             "text": "Chile, Argentina and Bolivia sit on the world's largest lithium resources in their salt flats, but "
                     "turning brine reserves into flowing supply is slow, water-intensive and politically contested "
                     "(Bolivia has barely started). Direct-lithium-extraction (DLE) promises to speed brine up, but is "
                     "not yet at scale. So the reserve map and the production map point at different countries.",
             "note": "USGS; IEA.", "flag": "reserves in one place, output in another"},
        ]},
        {"h2": "3 · Why the price whipsaws", "panels": [
            {"kind": "text", "h3": "A young market that overshoots",
             "text": "Lithium demand is dominated by batteries and has grown explosively, but new mines and refineries "
                     "take years, so price has swung violently — a boom to 2022, then a sharp crash as supply caught up. "
                     "The metal is not geologically scarce; the difficulty is matching a fast-moving demand curve to "
                     "slow-building supply and a concentrated refining step. Chemistry shifts (LFP vs NMC) move the "
                     "demand target too (see the battery chain).",
             "flag": "not scarce, just slow to build"},
        ]},
    ],
    "trade_intro": "BACI carries lithium carbonate (283691) and lithium oxide/hydroxide (282520), but not spodumene "
                   "concentrate cleanly, and a chemical's customs origin is the refinery, not the mine. Read the shares "
                   "below as the traded battery chemicals — where China's conversion role shows more than in any mine "
                   "figure.",
    "method": [
        {"stage": "Mine", "lens": "USGS mine share and history, by lithium content", "why": "multi-country (Australia hard-rock leads) — not the chokepoint"},
        {"stage": "Refine", "lens": "IEA conversion share", "why": "battery-grade chemical, mostly China — the real chokepoint"},
        {"stage": "Reserves", "lens": "USGS reserves vs output", "why": "Lithium Triangle holds it; production sits elsewhere"},
        {"stage": "Trade", "lens": "BACI 283691 carbonate + 282520 hydroxide", "why": "refinery-origin chemicals — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), f"- lithium, AU {AU}pct of 2024 mine output by lithium content (peak {PEAK}pct in {PEAK_Y})")
