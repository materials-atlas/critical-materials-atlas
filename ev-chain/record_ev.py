"""Build the installed EV study and its evidence from pinned public inputs."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template


HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
BEV = "87038010"
PHEV = "87036010"
NEW = (BEV, PHEV)

IEA = "https://www.iea.org/reports/global-ev-outlook-2026"
SOURCES = {
    "iea_trade": {"title": "IEA, Global EV Outlook 2026 — Manufacturing and trade", "url": f"{IEA}/manufacturing-and-trade"},
    "iea_batteries": {"title": "IEA, Global EV Outlook 2026 — Electric vehicle batteries", "url": f"{IEA}/electric-vehicle-batteries"},
    "comext": {"title": "Eurostat Comext, DS-045409", "url": "https://ec.europa.eu/eurostat/databrowser/view/ds-045409/default/table?lang=en"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
    "renault": {"title": "Renault, Mégane E-Tech production motor", "url": "https://www.renaultgroup.com/en/magazine/energy-and-motorization/all-about-electric-motors-with-no-rare-earths/"},
    "volkswagen": {"title": "Volkswagen, ID.4 Pro 4MOTION specifications (archived 28 March 2025)", "url": "https://web.archive.org/web/20250328031332/https://www.volkswagen-newsroom.com/en/volkswagen-id4-pro-4motion-15130/specifications-of-the-id4-pro-4motion-15140"},
    "doe": {"title": "US Department of Energy, Advanced Motors and Electric Drives", "url": "https://www.energy.gov/cmei/vehicles/research-and-development-advanced-motors-and-electric-drives"},
}
TRADE_BOUNDARIES = {
    "870380": "Finished cars powered solely by an electric motor. Excludes plug-in hybrids. No origin for the parts inside the car is recorded here.",
    "850760": "Lithium-ion accumulators across end uses. Includes cells, modules and packs. EV end use and the origin of upstream inputs cannot be isolated.",
}


def read_json(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def calculate(snapshot):
    annual = []
    for year, products in snapshot["annual"]["rows"].items():
        for code in NEW:
            china = products[code]["CN"]
            extra = products[code]["EXT_EU27_2020"]
            cn_units = china["SUPPLEMENTARY_QUANTITY"]["value"]
            all_units = extra["SUPPLEMENTARY_QUANTITY"]["value"]
            cn_eur = china["VALUE_IN_EUROS"]["value"]
            all_eur = extra["VALUE_IN_EUROS"]["value"]
            annual.append({
                "year": int(year), "code": code, "from_china": cn_units, "extra_eu": all_units,
                "from_china_eur": cn_eur, "extra_eu_eur": all_eur,
            })
    quarters = []
    months = snapshot["monthly"]["rows"]
    for quarter in range(1, 5):
        base = {
            code: sum(months[f"2025-{month:02d}"][code]["value"]
                      for month in range(3 * quarter - 2, 3 * quarter + 1))
            for code in NEW
        }
        quarters.append({
            "quarter": quarter, "observed_from_china": base,
            "gross_gap": {code: (base[code] + 1) // 2 for code in NEW},
        })
    for record in annual:
        total = sum(q["observed_from_china"][record["code"]] for q in quarters)
        if record["year"] == 2025 and total != record["from_china"]:
            raise ValueError(f"Monthly and annual counts differ for {record['code']}")
    return annual, quarters


def table_row(label, *cols, attrs=""):
    heading = f'<th scope="row">{escape(str(label))}</th>'
    values = "".join(f"<td>{escape(str(value))}</td>" for value in cols)
    return f"<tr{attrs}>{heading}{values}</tr>"


def percent(part, total):
    return f"{part / total:.1%}"


def trade_followup(context, annual, quarters):
    """Add historical, market-scale and gross interruption comparisons."""
    labels = {BEV: "New BEVs", PHEV: "New petrol PHEVs"}
    customs = context["customs"]
    history = {}
    for year, products in customs["annual"]["rows"].items():
        history[year] = {}
        for code, partners in products.items():
            china = partners["CN"]["value"]
            total = partners["EXT_EU27_2020"]["value"]
            if not 0 <= china <= total or total <= 0:
                raise ValueError(f"Invalid import count in {year}, {code}")
            history[year][code] = {
                "china_origin_units": china, "extra_eu_units": total,
                "other_origin_units": total - china, "china_import_share": china / total,
            }
    for row in annual:
        year, code = str(row["year"]), row["code"]
        check = history[year][code]
        for partner, field in (("CN", "china_origin_units"), ("EXT_EU27_2020", "extra_eu_units")):
            total = sum(month[code][partner]["value"] for period, month in customs["monthly"]["rows"].items()
                        if period.startswith(year + "-"))
            expected = row["from_china"] if partner == "CN" else row["extra_eu"]
            if total != expected or check[field] != expected:
                raise ValueError(f"Original, monthly and historical counts disagree in {year}, {code}, {partner}")

    changes = {}
    for code in labels:
        first, last = history["2024"][code], history["2025"][code]
        changes[code] = {}
        for origin in ("china_origin_units", "other_origin_units"):
            initial, final = first[origin], last[origin]
            changes[code][origin] = {
                "2024": initial, "2025": final, "unit_change": final - initial,
                "growth_fraction": (final - initial) / initial,
            }

    registrations = {}
    for year, products in context["registrations"]["rows"].items():
        registrations[year] = {}
        for code, cell in products.items():
            arrivals = history[year][code]["china_origin_units"]
            registrations[year][code] = {
                "china_origin_customs_arrivals": arrivals, "reported_new_registrations": cell["value"],
                "arrivals_per_100_registrations": 100 * arrivals / cell["value"],
            }

    grid = []
    for code in labels:
        for shock in (10, 25, 50, 75, 100):
            gaps = [(q["observed_from_china"][code] * shock + 50) // 100 for q in quarters]
            if shock == 50 and gaps != [q["gross_gap"][code] for q in quarters]:
                raise ValueError(f"Original 50% case differs for {code}")
            grid.append({
                "code": code, "shock_percent": shock, "quarterly_gross_gaps": gaps,
                "sum_of_separately_rounded_quarters": sum(gaps), "largest_quarter": max(gaps),
            })
    return {
        "date": "2026-11-24",
        "source_snapshot": "ev_import_context.json",
        "product_labels": labels,
        "import_history": history,
        "import_changes_2024_2025": changes,
        "registration_scale": registrations,
        "gross_interruption_sensitivity": grid,
        "interruption_basis": "Independent quarterly baselines for 2025",
        "compatible_inventory": None,
        "qualified_incremental_replacement": None,
        "residual_gap": None,
    }


def followup_tables(followup):
    labels = followup["product_labels"]
    changes, registrations, history, sensitivity = [], [], [], []
    for code, origins in followup["import_changes_2024_2025"].items():
        for key, description in (("china_origin_units", "China origin"), ("other_origin_units", "Other origins")):
            row = origins[key]
            changes.append(table_row(
                f"{labels[code]} · {description}", f'{row["2024"]:,}', f'{row["2025"]:,}',
                f'{row["unit_change"]:+,}', f'{row["growth_fraction"]:+.2%}',
            ))
    for year, products in followup["registration_scale"].items():
        for code, row in products.items():
            registrations.append(table_row(
                labels[code], year, f'{row["china_origin_customs_arrivals"]:,}',
                f'{row["reported_new_registrations"]:,}', f'{row["arrivals_per_100_registrations"]:.1f}',
            ))
    for year, products in followup["import_history"].items():
        fields = []
        for code in labels:
            row = products[code]
            fields.extend((f'{row["china_origin_units"]:,}', f'{row["extra_eu_units"]:,}',
                           f'{row["china_import_share"]:.1%}'))
        history.append(table_row(year, *fields))
    for row in followup["gross_interruption_sensitivity"]:
        sensitivity.append(table_row(
            f'{labels[row["code"]]} · {row["shock_percent"]}%',
            *(f"{gap:,}" for gap in row["quarterly_gross_gaps"]),
            f'{row["sum_of_separately_rounded_quarters"]:,}', f'{row["largest_quarter"]:,}',
        ))
    return {
        "followup_changes": "\n".join(changes), "followup_history": "\n".join(history),
        "followup_registrations": "\n".join(registrations), "followup_sensitivity": "\n".join(sensitivity),
    }


def render_study(snapshot, annual, quarters, trade, followup):
    annual_rows = [
        table_row(snapshot["products"][r["code"]], r["year"], f"{r['from_china']:,}",
                  f"{r['extra_eu']:,}", percent(r["from_china"], r["extra_eu"]),
                  percent(r["from_china_eur"], r["extra_eu_eur"]))
        for r in annual
    ]
    scenario_rows = [
        table_row(f"Q{q['quarter']}", *(f"{q[key][code]:,}" for code in NEW
                                        for key in ("observed_from_china", "gross_gap")))
        for q in quarters
    ]
    trade_year = str(trade["years"][-1])
    trade_rows = []
    for code, item in trade["codes"].items():
        metrics = trade["years_data"][trade_year][code]
        leader = metrics["exporters"][0]
        trade_rows.append(table_row(f"{item['title']} (HS {code})",
                                    f"${metrics['world_usd'] / 1e9:.1f}B",
                                    f"{leader['name']} · {leader['share']:.0%}",
                                    TRADE_BOUNDARIES[code], attrs=f' data-trade-code="{code}"'))
    template = Template((HERE / "study.template").read_text(encoding="utf-8"))
    page = template.substitute(
        **followup_tables(followup),
        annual_rows="\n".join(annual_rows),
        scenario_rows="\n".join(scenario_rows),
        trade_rows="\n".join(trade_rows),
        trade_year=trade_year,
        comext_vintage=snapshot["annual"]["updated"][:10],
        **{key: escape(value["url"], quote=True) for key, value in SOURCES.items()},
    )
    return page


def main():
    snapshot = read_json("comext_audit.json")
    annual, quarters = calculate(snapshot)
    trade = read_json("ev_trade.json")
    record = {
        "title": "Electric-vehicle supply depends on where cars and parts are made",
        "revision": "2026-11-24",
        "published": True,
        "chokepoint": {
            "product": "Electric vehicles",
            "stage": "Potential assembly and component constraints",
            "mechanism": "capability",
            "physics": "Assembly and key components are concentrated. A binding stage depends on usable capacity, the vehicle design and the disruption.",
            "holder": "China (output)",
            "share": "Roughly 70% of electric-car output (2025)",
            "control": "—",
            "conf": "estimate",
            "research": True,
        },
        "sources": SOURCES,
        "annual_customs": {
            "evidence": "calculated from reported Eurostat imports",
            "scope": "EU-27 extra-EU imports of new BEVs and new petrol PHEVs by declared origin",
            "snapshot": "comext_audit.json",
            "rows": annual,
        },
        "disruption": {
            "evidence": "modelled",
            "baseline": "Each calendar quarter of 2025 replayed separately",
            "scope": "New cars of matching product code entering the EU from China",
            "shock_share": 0.5,
            "stock_or_replacement_credited": 0,
            "rounding": "half a vehicle rounds up",
            "rows": quarters,
        },
        "baci_trade": {"boundary": TRADE_BOUNDARIES, "snapshot": "ev_trade.json"},
    }
    followup = trade_followup(read_json("ev_import_context.json"), annual, quarters)
    record["trade_followup"] = followup
    page = render_study(snapshot, annual, quarters, trade, followup)
    (OUT / "ev_chain.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / "ev-chain.html").write_text(page, encoding="utf-8")
    print("Wrote EV study and evidence")


if __name__ == "__main__":
    main()
