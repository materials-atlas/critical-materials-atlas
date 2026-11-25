"""Build the defence materials evidence note from pinned inputs and Atlas aggregates."""
from __future__ import annotations

from calendar import month_abbr
import csv
from html import escape
import json
from pathlib import Path
from statistics import mean
from string import Template

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = HERE / "out"
DATE = "2026-11-25"
TITLE = "Materials and trade in defence supply chains"
DECK = "Production shares and trade records show where materials come from. Antimony imports show how origins and unit values changed around export controls."

SOURCES = {
    "china_usgs": ("USGS Open-File Report 2026-1018, Table 3", "https://pubs.usgs.gov/of/2026/1018/ofr20261018_pamphlet.pdf"),
    "mcs_2024": ("USGS Mineral Commodity Summaries 2024, Antimony", "https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-antimony.pdf?v=101202"),
    "mcs_earlier": ("USGS Mineral Commodity Summaries 2025, Antimony", "https://pubs.usgs.gov/periodicals/mcs2025/mcs2025.pdf"),
    "mcs_antimony": ("USGS Mineral Commodity Summaries 2026, Antimony", "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-antimony.pdf"),
    "outlook": ("USGS World Minerals Outlook, November 2026, Antimony", "https://pubs.usgs.gov/publication/sir20265081/full"),
    "magnets": ("IEA Rare Earth Elements, executive summary", "https://www.iea.org/reports/rare-earth-elements/executive-summary"),
    "iea_controls": ("IEA Global Critical Minerals Outlook 2026, p. 39", "https://www.iea.org/reports/global-critical-minerals-outlook-2026"),
    "comext": ("Eurostat Comext DS-045409", "https://ec.europa.eu/eurostat/databrowser/view/DS-045409/default/table?lang=en"),
    "gao": ("US GAO report on industrial supplier visibility, July 2025", "https://www.gao.gov/products/gao-25-107283"),
    "licenses": ("MOFCOM and Customs announcement 23 of 2023", "https://www.mofcom.gov.cn/zcfb/dwmygl/art/2023/art_52b9a321087f402bb3d310d18b07967e.html"),
    "antimony_licensing": ("MOFCOM and Customs announcement 33 of 2024", "https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2024/art_3840ffc4bd104de2aa673ccd74a646cc.html"),
    "ban": ("MOFCOM announcement 46 of 2024", "https://www.mofcom.gov.cn/zfxxgk/gkml/art/2024/art_99f5d51bbe6a412ca309d5818c4dee52.html"),
    "tungsten": ("MOFCOM and Customs announcement 10 of 2025", "https://exportcontrol.mofcom.gov.cn/article/hgfw/lywxcx/gzqd/202502/1102.html"),
    "rare_earths": ("MOFCOM and Customs announcement 18 of 2025", "https://english.mofcom.gov.cn/Policies/AnnouncementsOrders/art/2025/art_0dd87cbee7b045bf93fabe6ab2faceee.html/"),
    "suspension": ("MOFCOM announcement 72 of 2025", "https://www.mofcom.gov.cn/zfxxgk/gkml/art/2025/art_43489ca6f2094b70954c25249702b4cc.html"),
    "extension": ("MOFCOM announcement 59 of 2026", "https://aqygzj.mofcom.gov.cn/qdml/art/2026/art_98ae61c2a60f43638304f2e6a43f952f.html"),
    "hs_minor": ("UN Statistics Division, HS 2017 code 811292", "https://unstats.un.org/unsd/classifications/Econ/Detail/EN/2089/811292"),
    "baci": ("CEPII BACI V202601", "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"),
}
POLICIES = (
    ("1 August 2023", "Licensing took effect for specified gallium and germanium items.", "licenses"),
    ("15 September 2024", "Licensing took effect for specified antimony and superhard-material items.", "antimony_licensing"),
    ("3 December 2024", "The second paragraph generally ruled out approval for certain US-bound gallium, germanium, antimony and superhard-material items. It tightened scrutiny for certain graphite exports.", "ban"),
    ("4 February 2025", "Licensing was introduced for specified tungsten and other items.", "tungsten"),
    ("4 April 2025", "Licensing was introduced for selected medium and heavy rare-earth items.", "rare_earths"),
    ("9 November 2025", "China suspended the second paragraph of announcement 46 through 27 November 2026.", "suspension"),
    ("24 November 2026", "China published an extension covering 28 November 2026 through 27 January 2027.", "extension"),
)
MINE = {"2024": {"china_t": 40000, "world_t": 119000}, "2025": {"china_t": 40000, "world_t": 110000}}
PRICES = {"mcs_2024": 10.24, "mcs_2025": 25, "outlook_2024": 10, "outlook_2025": 24, "april_2026_spot": 12}
TRADE_BOUNDARIES = {
    "811292": "Mixed minor metals and forms. Individual metal values are unavailable.",
    "811010": "Unwrought antimony and powders. Oxide is a separate heading.",
    "810194": "Unwrought tungsten and powders. The heading gives no final end use.",
    "850511": "Metal permanent magnets, including more categories than the CN8 series above.",
    "810320": "Unwrought tantalum and powders. The heading gives no final end use.",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def month_number(month):
    return int(month[:4]) * 12 + int(month[4:])


def month_label(month):
    return f"{month_abbr[int(month[4:])]} {month[:4]}"


def summarise_months(rows):
    total = sum(row["total_t"] for row in rows)
    return {
        "start": rows[0]["ym"], "end": rows[-1]["ym"], "months": len(rows),
        "china_t_per_month": mean(row["china_t"] for row in rows),
        "total_t_per_month": total / len(rows),
        "unit_value_per_kg": sum(row["uv"] * row["total_t"] for row in rows if row["uv"] is not None) / total,
    }


def antimony_episode():
    aggregate = load(ROOT / "out/export_controls.json")
    cases = {}
    for result in aggregate["results"]:
        if result["control"] != "C5" or result["importer"] not in ("EU", "US"):
            continue
        rows = result["monthly"]
        effective_month = month_number(result["in_force"])
        earlier = [row for row in rows if row["ym"] < result["announced"]]
        later = [row for row in rows if 7 <= month_number(row["ym"]) - effective_month <= 12]
        if any(row["uv"] is None and row["total_t"] > 0 for row in earlier + later):
            raise ValueError("Reported import mass has no corresponding customs unit value")
        cases[result["importer"]] = {
            "effective_month": result["in_force"], "announcement_month": result["announced"],
            "basket_codes": (
                ["81101000", "81102000", "81109000", "26171000"] if result["importer"] == "EU"
                else ["8110100000", "8110200000", "8110900000"]
            ),
            "earlier": summarise_months(earlier), "later": summarise_months(later),
            "monthly": [{key: row[key] for key in ("ym", "china_t", "total_t", "uv")} for row in rows],
        }
    return cases


def benchmark_magnets():
    comext = load(ROOT / "magnet-chain/out/comext_audit.json")
    benchmark = comext["annual"]["rows"]["2024"]
    china, total = benchmark["CN"], benchmark["EXT_EU27_2020"]
    return {
        "year": 2024, "source": comext["dataset"], "query": comext["annual"]["query"], "code": comext["product"],
        "china_kg": round(china["QUANTITY_IN_100KG"]["value"] * 100),
        "total_kg": round(total["QUANTITY_IN_100KG"]["value"] * 100),
        "china_eur": china["VALUE_IN_EUROS"]["value"], "total_eur": total["VALUE_IN_EUROS"]["value"],
    }


def mine_history():
    data = load(ROOT / "out/mined_years.json")
    return {
        material: {year: next((item["v"] for item in countries if item["c"] == "CN"), None)
                   for year, countries in data[material].items()}
        for material in ("antimony", "tungsten")
    }


def build_evidence():
    share = MINE["2025"]["china_t"] / MINE["2025"]["world_t"]
    materials = (
        ("Gallium", "Primary refined production", 2023, 0.98, "Semiconductor material across applications.", "china_usgs"),
        ("Germanium", "Refined production", 2023, 0.77, "Refined material for optics and electronics.", "china_usgs"),
        ("Antimony", "Mine production", 2025, share, "40,000 of 110,000 tonnes in the published estimate.", "mcs_antimony"),
        ("Tungsten", "Mine production", 2023, 0.83, "Mine output upstream of industrial tooling and other products.", "china_usgs"),
        ("Rare-earth magnets", "Sintered permanent magnet production", 2024, 0.94,
         "Sintered magnet output across markets. The estimate has a separate scope from bonded magnets.", "magnets"),
    )
    keys = ("material", "stage", "year", "china_share", "scope", "source")
    return {
        "title": TITLE, "h1": TITLE, "deck": DECK, "published": True, "version": DATE,
        "chokepoint": {
            "product": "Defence supply chains", "stage": "Selected materials", "mechanism": "capability",
            "physics": "Concentration varies by material and stage. Public trade does not identify defence procurement.",
            "holder": "Varies by material", "share": "—", "control": "multiple", "conf": "snapshot", "research": True,
        },
        "materials": [dict(zip(keys, row, strict=True)) for row in materials],
        "mine_history_bgs": mine_history(), "antimony_mine_usgs": MINE,
        "us_antimony_net_import_reliance": {"year": 2025, "share": 0.91, "source": "mcs_antimony"},
        "magnet_imports": benchmark_magnets(),
        "policy_timeline": [dict(date=date, measure=measure, source=source) for date, measure, source in POLICIES],
        "antimony_episode": antimony_episode(), "antimony_prices_usgs": PRICES,
        "sources": {key: {"title": title, "url": url} for key, (title, url) in SOURCES.items()},
    }


def display_rows(items):
    return "\n".join(
        f'<tr><th scope="row">{escape(str(head))}</th>'
        + "".join(f"<td>{escape(str(value))}</td>" for value in cells) + "</tr>"
        for head, *cells in items
    )


def source_link(key):
    title, url = SOURCES[key]
    return f'<a href="{escape(url, quote=True)}">{escape(title)}</a>.'


def trade_rows(trade, year):
    for code, category in trade["codes"].items():
        row = trade["years_data"][str(year)][code]
        exporter = next(iter(row["exporters"]), None)
        lead = f'{exporter["name"]} · {exporter["share"]:.0%}' if exporter else "Unavailable"
        cells = (f'{category["title"]} ({code})', f'USD {row["world_usd"] / 1e6:,.1f} million',
                 lead, TRADE_BOUNDARIES[code])
        yield f'<tr data-trade-code="{escape(code)}">' + "".join(f"<td>{escape(cell)}</td>" for cell in cells) + "</tr>"


def render(data, trade):
    material_rows = []
    for row in data["materials"]:
        head = (row["material"], row["stage"], row["year"], f'{row["china_share"]:.0%}')
        material_rows.append(display_rows([head]).removesuffix("</tr>")
                             + f'<td>{escape(row["scope"])} {source_link(row["source"])}</td></tr>')
    policy_rows = [display_rows([(date, measure)]).removesuffix("</tr>")
                   + f"<td>{source_link(key)}</td></tr>" for date, measure, key in POLICIES]
    episode_rows = []
    for market, currency in (("EU", "EUR"), ("US", "USD")):
        case = data["antimony_episode"][market]
        metrics = (("china_t_per_month", "China origin, tonnes/month"), ("total_t_per_month", "Total, tonnes/month"),
                   ("unit_value_per_kg", f"Unit value, {currency}/kg"))
        for key, label in metrics:
            a, b = (case[window][key] for window in ("earlier", "later"))
            episode_rows.append((f"{market} · {label}", f"{a:,.2f}", f"{b:,.2f}", f"{b/a-1:+.1%}"))
    eu = data["antimony_episode"]["EU"]
    history = data["mine_history_bgs"]
    years = sorted(set(history["antimony"]) | set(history["tungsten"]))
    magnet = data["magnet_imports"]
    last = trade["years"][-1]
    values = {
        "title": TITLE, "deck": DECK, "date": DATE,
        "material_rows": "\n".join(material_rows), "policy_rows": "\n".join(policy_rows),
        "bgs_antimony_2024": f'{history["antimony"]["2024"]:g}%',
        "antimony_2024": f'{MINE["2024"]["china_t"] / MINE["2024"]["world_t"]:.1%}',
        "antimony_2025": f'{MINE["2025"]["china_t"] / MINE["2025"]["world_t"]:.1%}',
        "history_rows": display_rows((year, *(f"{v:g}%" if v is not None else "Unavailable" for v in (
            history["antimony"].get(year), history["tungsten"].get(year)))) for year in years),
        "magnet_china_kg": f'{magnet["china_kg"]:,}', "magnet_total_kg": f'{magnet["total_kg"]:,}',
        "magnet_mass": f'{magnet["china_kg"] / magnet["total_kg"]:.1%}',
        "magnet_value": f'{magnet["china_eur"] / magnet["total_eur"]:.1%}',
        "import_reliance": f'{data["us_antimony_net_import_reliance"]["share"]:.0%}',
        "early_window": f'{month_label(eu["earlier"]["start"])} to {month_label(eu["earlier"]["end"])}',
        "late_window": f'{month_label(eu["later"]["start"])} to {month_label(eu["later"]["end"])}',
        "episode_rows": display_rows(episode_rows),
        "price_2024": f'USD {PRICES["mcs_2024"]:g}', "price_2025": f'USD {PRICES["mcs_2025"]:g}',
        "outlook_2024": f'USD {PRICES["outlook_2024"]:g}', "outlook_2025": f'USD {PRICES["outlook_2025"]:g}',
        "april_spot": f'USD {PRICES["april_2026_spot"]:g}',
        "trade_year": last, "trade_rows": "\n".join(trade_rows(trade, last)),
        **{key: source_link(key) for key in SOURCES},
    }
    return Template((HERE / "article.html.in").read_text(encoding="utf-8")).substitute(values)


def build():
    data = build_evidence()
    trade = load(OUT / "defence_trade.json")
    article = render(data, trade)
    (OUT / "defence_chain.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n",
    )
    (HERE / "defence-chain.html").write_text(article, encoding="utf-8", newline="\n")
    with (OUT / "defence_antimony_monthly.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("market", "month", "china_t", "total_t", "customs_unit_value_per_kg", "currency"))
        for market, case in data["antimony_episode"].items():
            for row in case["monthly"]:
                writer.writerow((market, row["ym"], row["china_t"], row["total_t"], row["uv"],
                                 "EUR" if market == "EU" else "USD"))


if __name__ == "__main__":
    build()
