"""Build the static platinum-group metals study and its evidence JSON.

Inputs: evidence_inputs.json (source tables transcribed and checked 25 Nov 2026), article.html.in,
out/pgm_trade.json (the frozen BACI extract) and the atlas's out/mined_years.json (BGS series).
No network access. Run from the repository root:  python pgm-catalyst-chain/record_pgm.py
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from string import Template

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUTS = HERE / "evidence_inputs.json"
TEMPLATE = HERE / "article.html.in"
TRADE = HERE / "out" / "pgm_trade.json"
MINED = ROOT / "out" / "mined_years.json"
OUT = HERE / "out" / "pgm_chain.json"
ARTICLE = HERE / "pgm-catalyst-chain.html"

TITLE = "Platinum, palladium and rhodium have different supply maps"
DECK = ("South Africa supplies most platinum and rhodium, and Russia leads in palladium. "
        "Recycling and vehicle demand also differ by metal, so one figure for the group hides the exposure.")
TONNES_PER_KOZ = 0.0311035      # one thousand troy ounces in tonnes
METALS = ("Platinum", "Palladium", "Rhodium")
REGIONS = ("South Africa", "Russia", "North America", "Zimbabwe", "Others")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pct(x, places=0):
    return f"{100 * x:.{places}f}%"


def t(kg_or_koz, kind="kg", places=0):
    value = kg_or_koz / 1000 if kind == "kg" else kg_or_koz * TONNES_PER_KOZ
    return f"{value:,.{places}f}"


def row(label, cells, numeric=True):
    cls = ' class="n"' if numeric else ""
    return (f'<tr><th scope="row">{escape(str(label))}</th>'
            + "".join(f"<td{cls}>{escape(str(c))}</td>" for c in cells) + "</tr>")


def hhi_bounds(shares, other):
    """HHI on a 0-10,000 scale. The grouped 'other countries' row is counted as one unit (upper)
    or as fully dispersed (lower)."""
    base = sum((100 * s) ** 2 for s in shares)
    return round(base), round(base + (100 * other) ** 2)


def evaluate(inputs):
    usgs = inputs["usgs_mcs2026"]
    world = usgs["world"]
    countries = usgs["countries"]
    named = {k: v for k, v in countries.items() if k != "Other countries"}
    reserve_sum = sum(v["reserves"] for v in named.values())
    shares = {
        name: {
            "pt_2024": v["pt_2024"] / world["pt_2024"],
            "pd_2024": v["pd_2024"] / world["pd_2024"],
            "reserves": (v["reserves"] / reserve_sum) if v["reserves"] else None,
        } for name, v in countries.items()
    }
    hhi = {m: hhi_bounds([shares[c][f"{m}_2024"] for c in named], shares["Other countries"][f"{m}_2024"])
           for m in ("pt", "pd")}

    history = []
    for h in inputs["usgs_history"]:
        history.append({
            "year": h["year"], "source": h["source"],
            "pt_sa": h["pt"]["South Africa"] / h["pt"]["world"], "pt_ru": h["pt"]["Russia"] / h["pt"]["world"],
            "pd_ru": h["pd"]["Russia"] / h["pd"]["world"], "pd_sa": h["pd"]["South Africa"] / h["pd"]["world"],
        })

    jm = inputs["jm_2025"]["metals"]
    balance = {}
    for metal in METALS:
        m = jm[metal]
        primary = sum(m["primary"].values())
        secondary = sum(m["secondary"].values())
        demand = m["total_demand"]
        if sum(m["demand"].values()) != demand:
            raise SystemExit(f"{metal}: demand sectors do not add to the published total")
        if primary + secondary - demand != m["movement_in_stocks"]:
            raise SystemExit(f"{metal}: supply minus demand does not equal the published stock movement")
        balance[metal] = {
            "primary": primary, "secondary": secondary, "combined": primary + secondary, "demand": demand,
            "movement_in_stocks": m["movement_in_stocks"],
            "primary_share": {r: m["primary"][r] / primary for r in REGIONS},
            "secondary_share_of_supply": secondary / (primary + secondary),
            "automotive_share_of_secondary": m["secondary"]["Automotive"] / secondary,
            "automotive_share_of_demand": m["demand"]["Automotive"] / demand,
            "deficit_share_of_demand": -m["movement_in_stocks"] / demand,
        }

    cut = inputs["scenarios"]["supply_cut_fraction"]
    supply_screen = {country: {metal: cut * jm[metal]["primary"][country] / jm[metal]["total_demand"] for metal in METALS}
                     for country in ("South Africa", "Russia")}
    demand_screen = {str(c): {metal: jm[metal]["movement_in_stocks"] + c * jm[metal]["demand"]["Automotive"]
                              for metal in METALS}
                     for c in [0.0] + inputs["scenarios"]["automotive_demand_cuts"]}

    trade = load(TRADE)
    series = {p["year"]: p for p in trade["series"]["711021"]}
    records = inputs["trade_checks"]["records"]
    flagged_years = sorted({r["year"] for r in records})
    clean = {y: series[y]["world_tonnes"] - sum(r["tonnes"] for r in records if r["year"] == y) for y in flagged_years}
    typical = [p["world_tonnes"] for y, p in series.items() if y not in flagged_years]
    tonnage = {"reported": {str(y): series[y]["world_tonnes"] for y in flagged_years},
               "without_flagged_records": {str(y): round(v, 1) for y, v in clean.items()},
               "other_years_range": [min(typical), max(typical)]}
    for y, v in clean.items():
        if not (min(typical) * 0.8 <= v <= max(typical) * 1.2):
            raise SystemExit(f"palladium {y}: the six flagged records no longer explain the tonnage outlier")

    bgs = load(MINED).get("platinum", {})
    def bgs_share(year, code):
        return next((x["v"] for x in bgs.get(str(year), []) if x["c"] == code), None)
    bgs_all = {str(y): {"South Africa": bgs_share(y, "ZA"), "Russia": bgs_share(y, "RU")} for y in (2000, 2024)}

    return {"reserve_sum_kg": reserve_sum, "usgs_shares_2024": shares, "hhi_2024": {"platinum": hhi["pt"], "palladium": hhi["pd"]},
            "history": history, "balance_2025": balance, "supply_screen": supply_screen, "demand_screen_koz": demand_screen,
            "palladium_tonnage_check": tonnage, "bgs_all_pgm_shares": bgs_all}


def link(sources, key, label=None):
    s = sources[key]
    return f'<a href="{escape(s["url"], quote=True)}">{escape(label or s["title"])}</a>.'


def render(inputs, results):
    src = inputs["sources"]
    usgs = inputs["usgs_mcs2026"]
    world = usgs["world"]
    sh = results["usgs_shares_2024"]
    bal = results["balance_2025"]
    jm = inputs["jm_2025"]["metals"]

    usgs_rows = []
    for name, v in usgs["countries"].items():
        s = sh[name]
        usgs_rows.append(row(name, [
            t(v["pt_2024"], places=1), pct(s["pt_2024"], 1), t(v["pt_2025"], places=1),
            t(v["pd_2024"], places=1), pct(s["pd_2024"], 1), t(v["pd_2025"], places=1),
            t(v["reserves"]) if v["reserves"] else "not available", pct(s["reserves"], 1) if s["reserves"] else "",
        ]))
    usgs_rows.append(row("World", [t(world["pt_2024"]), "", t(world["pt_2025"]), t(world["pd_2024"]), "", t(world["pd_2025"]),
                                   "more than " + t(world["reserves_at_least"]), ""]))

    history_rows = [row(h["year"], [pct(h["pt_sa"], 1), pct(h["pt_ru"], 1), pct(h["pd_ru"], 1), pct(h["pd_sa"], 1)])
                    .removesuffix("</tr>") + f'<td>{escape(src[h["source"]]["vintage"])}</td></tr>'
                    for h in results["history"]]
    hist = results["history"]

    def koz_row(label, getter, places=1):
        return row(label, [t(getter(m), "koz", places) for m in METALS])

    balance_rows = [
        koz_row("Primary supply (producer sales)", lambda m: bal[m]["primary"]),
        row("of which South Africa", [pct(bal[m]["primary_share"]["South Africa"], 1) for m in METALS]),
        row("of which Russia", [pct(bal[m]["primary_share"]["Russia"], 1) for m in METALS]),
        row("of which Zimbabwe", [pct(bal[m]["primary_share"]["Zimbabwe"], 1) for m in METALS]),
        row("of which North America", [pct(bal[m]["primary_share"]["North America"], 1) for m in METALS]),
        koz_row("Recycled supply (open market)", lambda m: bal[m]["secondary"]),
        row("Recycled share of supply", [pct(bal[m]["secondary_share_of_supply"], 1) for m in METALS]),
        koz_row("Demand", lambda m: bal[m]["demand"]),
        row("Automotive share of demand", [pct(bal[m]["automotive_share_of_demand"], 1) for m in METALS]),
        koz_row("Movement in stocks (negative = deficit)", lambda m: bal[m]["movement_in_stocks"]),
    ]

    cut = inputs["scenarios"]["supply_cut_fraction"]
    adjective = {"South Africa": "South African", "Russia": "Russian"}
    cut_rows = [row(f"Half of {adjective[country]} primary sales", [pct(results["supply_screen"][country][m], 1) for m in METALS])
                for country in ("South Africa", "Russia")]
    if cut != 0.5:
        raise SystemExit("the page text says 'half': change it with the scenario")
    quarter = results["demand_screen_koz"]["0.25"]
    if not (quarter["Palladium"] > 0 and quarter["Rhodium"] > 0 and abs(quarter["Platinum"]) * TONNES_PER_KOZ < 5):
        raise SystemExit("the sentence on a quarter-lower automotive demand no longer matches the screen")
    demand_rows = []
    for key, values in results["demand_screen_koz"].items():
        label = "As in 2025" if float(key) == 0 else f"{pct(float(key))} lower"
        demand_rows.append(row(label, [f"{values[m] * TONNES_PER_KOZ:+,.1f}" for m in METALS]))

    trade = load(TRADE)
    year = trade["years"][-1]
    trade_rows = []
    for code, info in trade["codes"].items():
        item = trade["years_data"][str(year)][code]
        top = next(iter(item["exporters"]), None)
        lead = f'{top["name"]} · {top["share"]:.0%}' if top else "not available"
        cells = (f'{info["title"]} ({code})', f'USD {item["world_usd"] / 1e9:,.1f} billion', lead,
                 inputs["trade_boundaries"][code])
        trade_rows.append(f'<tr data-trade-code="{escape(code)}">' + "".join(f"<td>{escape(c)}</td>" for c in cells) + "</tr>")

    tc = results["palladium_tonnage_check"]
    bgs = results["bgs_all_pgm_shares"]
    bgs_summary = (f'South Africa {bgs["2000"]["South Africa"]}% and Russia {bgs["2000"]["Russia"]}% in 2000, '
                   f'and {bgs["2024"]["South Africa"]}% and {bgs["2024"]["Russia"]}% in 2024')
    old = inputs["usgs_mcs2025_estimates_for_2024"]["world"]

    values = {
        "title": escape(TITLE), "deck": escape(DECK), "date": inputs["version"],
        "pt_sa_share": pct(bal["Platinum"]["primary_share"]["South Africa"]),
        "rh_sa_share": pct(bal["Rhodium"]["primary_share"]["South Africa"]),
        "pd_sa_share": pct(bal["Palladium"]["primary_share"]["South Africa"]),
        "pd_ru_share": pct(bal["Palladium"]["primary_share"]["Russia"]),
        "pt_auto_share": pct(bal["Platinum"]["automotive_share_of_demand"]),
        "pd_auto_share": pct(bal["Palladium"]["automotive_share_of_demand"]),
        "rh_auto_share": pct(bal["Rhodium"]["automotive_share_of_demand"]),
        "usgs_pt_sa": pct(sh["South Africa"]["pt_2024"]), "usgs_pt_ru": pct(sh["Russia"]["pt_2024"]),
        "usgs_pd_ru": pct(sh["Russia"]["pd_2024"]), "usgs_pd_sa": pct(sh["South Africa"]["pd_2024"]),
        "usgs_rows": "\n".join(usgs_rows), "reserve_sum": t(results["reserve_sum_kg"]),
        "hhi_pt": "{:,} to {:,}".format(*results["hhi_2024"]["platinum"]),
        "hhi_pd": "{:,} to {:,}".format(*results["hhi_2024"]["palladium"]),
        "rev_pd_old": t(old["pd"]), "rev_pd_new": t(world["pd_2024"]), "rev_pt_old": t(old["pt"]), "rev_pt_new": t(world["pt_2024"]),
        "history_rows": "\n".join(history_rows),
        "pt_sa_min": pct(min(h["pt_sa"] for h in hist)), "pt_sa_max": pct(max(h["pt_sa"] for h in hist)),
        "pd_ru_first": pct(hist[0]["pd_ru"]), "pd_ru_last": pct(hist[-1]["pd_ru"]),
        "pd_sa_first": pct(hist[0]["pd_sa"]), "pd_sa_last": pct(hist[-1]["pd_sa"]),
        "pt_two": pct(hist[-1]["pt_sa"] + hist[-1]["pt_ru"]), "pd_two": pct(hist[-1]["pd_sa"] + hist[-1]["pd_ru"]),
        "history_sources": " ".join(link(src, h["source"], "USGS " + src[h["source"]]["vintage"].split()[-1]) for h in hist),
        "bgs_summary": bgs_summary,
        "balance_rows": "\n".join(balance_rows),
        "pt_sec_share": pct(bal["Platinum"]["secondary_share_of_supply"]),
        "pd_sec_share": pct(bal["Palladium"]["secondary_share_of_supply"]),
        "rh_sec_share": pct(bal["Rhodium"]["secondary_share_of_supply"]),
        "pt_sec_auto": pct(bal["Platinum"]["automotive_share_of_secondary"]),
        "pd_sec_auto": pct(bal["Palladium"]["automotive_share_of_secondary"]),
        "cut_pct": pct(cut).replace("50%", "half"), "cut_rows": "\n".join(cut_rows), "demand_rows": "\n".join(demand_rows),
        "pt_deficit_share": pct(bal["Platinum"]["deficit_share_of_demand"], 1),
        "pd_deficit_share": pct(bal["Palladium"]["deficit_share_of_demand"], 1),
        "rh_deficit_share": pct(bal["Rhodium"]["deficit_share_of_demand"], 1),
        "trade_year": year, "trade_rows": "\n".join(trade_rows),
        "anomaly_2002": f'{tc["reported"]["2002"]:,.0f}', "anomaly_2009": f'{tc["reported"]["2009"]:,.0f}',
        "typical_low": f'{tc["other_years_range"][0]:,.0f}', "typical_high": f'{tc["other_years_range"][1]:,.0f}',
        "clean_2002": f'{tc["without_flagged_records"]["2002"]:,.0f}', "clean_2009": f'{tc["without_flagged_records"]["2009"]:,.0f}',
        "jm": link(src, "jm2026", "Johnson Matthey, PGM Market Report, May 2026"),
        "mcs2026": link(src, "mcs2026", "USGS, 2026 edition"), "mcs2025": link(src, "mcs2025", "USGS, 2025 edition"),
        "bgs": link(src, "bgs", "British Geological Survey, World Mineral Statistics"),
        "ipa_recycling": link(src, "ipa_recycling", "International Platinum Group Metals Association"),
        "ipa_rhodium": link(src, "ipa_rhodium", "IPA rhodium fact sheet"),
        "usgs_pp1802": link(src, "usgs_pp1802", "USGS Professional Paper 1802-N"),
        "wco_ch71": link(src, "wco_ch71", "WCO, HS 2017, Chapter 71"), "wco_2022": link(src, "wco_2022", "WCO, HS 2022 correlation table"),
        "baci": link(src, "baci", "CEPII BACI V202601"),
        "references": "\n".join(f'    <li><a href="{escape(s["url"], quote=True)}">{escape(s["title"])}</a> · {escape(s["vintage"])}</li>'
                                for s in src.values()),
    }
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(values)


def build():
    inputs = load(INPUTS)
    results = evaluate(inputs)
    sh = results["usgs_shares_2024"]
    data = {
        "title": "PGM / catalyst chain", "h1": TITLE, "deck": DECK, "published": True, "version": inputs["version"],
        "chokepoint": {
            "product": "Autocatalysts and other PGM catalysts", "stage": "Mine supply, by metal", "mechanism": "geological",
            "physics": "The ore is concentrated in South Africa's Bushveld Complex and Russia's Norilsk deposits, and the metals are mined together",
            "holder": "South Africa; Russia for palladium",
            "share": (f'{pct(sh["South Africa"]["reserves"])} of reserves; {pct(sh["South Africa"]["pt_2024"])} of platinum and '
                      f'{pct(sh["Russia"]["pd_2024"])} (Russia) of palladium mine output (2024)'),
            "control": "—", "conf": "measured", "research": True,
        },
        "sources": inputs["sources"],
        "inputs": {k: inputs[k] for k in ("usgs_mcs2026", "usgs_mcs2025_estimates_for_2024", "usgs_history", "jm_2025",
                                         "scenarios", "trade_checks")},
        "results": results,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    ARTICLE.write_text(render(inputs, results), encoding="utf-8", newline="\n")
    b = results["balance_2025"]
    print("wrote pgm_chain.json and pgm-catalyst-chain.html: South Africa %s of primary platinum, Russia %s of primary palladium (2025)"
          % (pct(b["Platinum"]["primary_share"]["South Africa"]), pct(b["Palladium"]["primary_share"]["Russia"])))


if __name__ == "__main__":
    build()
