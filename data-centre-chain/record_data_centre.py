"""Build the static data-centre study and its downloadable evidence."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from string import Template

from project_readiness import ASSUMPTIONS, evaluate

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EVIDENCE = HERE / "out" / "data_centre_chain.json"
TRADE = HERE / "out" / "data_centre_trade.json"
ARTICLE = HERE / "data-centre-chain.html"
TEMPLATE = HERE / "article.html.in"
STUDY = ROOT / "out" / "buildout_study.json"
TITLE = "What delays AI data-centre deployment?"
DECK = (
    "An operating data centre needs compatible servers, electrical equipment, firm power "
    "and a completed facility. Which dependency sets the commissioning date varies by project."
)

SOURCES = {
    "iea_update": {"title": "IEA, Key Questions on Energy and AI", "year": 2026,
                   "url": "https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary"},
    "iea_demand": {"title": "IEA, Energy and AI, energy demand", "year": 2025,
                   "url": "https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai"},
    "iea_grid": {"title": "IEA, Energy and AI, grid connection risks", "year": 2025,
                 "url": "https://www.iea.org/reports/energy-and-ai/ai-and-energy-security"},
    "doe_lbnl": {"title": "Berkeley Lab, US Data Center Energy Usage Report", "year": 2024,
                 "url": "https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report"},
    "doe_transformers": {"title": "US DOE, Large Power Transformer Resilience", "year": 2024,
                         "url": "https://www.energy.gov/sites/default/files/2024-10/EXEC-2022-001242%20-%20Large%20Power%20Transformer%20Resilience%20Report%207-10-24.pdf"},
    "grid_trade": {"title": "Atlas research note on transformers and electrical steel", "year": 2026,
                   "url": "../grid-trade"},
    "buildout": {"title": "Atlas AI build-out in customs data", "year": 2026,
                 "url": "../ai-buildout"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026,
             "url": "https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html"},
    "tva": {"title": "TVA board minutes, additional firm power for a Memphis load", "year": 2026,
            "url": "https://tva-azr-eastus-cdn-ep-tvawcm-prd.azureedge.net/cdn-tvawcma/docs/default-source/about-tva/board-of-directors/february-11--2026/february-11-2026-board-meeting-minutes.pdf?sfvrsn=1658d52d_1#page=8"},
    "planning": {"title": "Woodlands Park appeal decision and inspector report", "year": 2025,
                 "url": "https://acp.planninginspectorate.gov.uk/ViewDocument.aspx?fileid=63029892"},
}

ENERGY = [
    {"scope": "United States", "period": "2014", "twh": 58, "kind": "Historical estimate",
     "source": "doe_lbnl"},
    {"scope": "United States", "period": "2023", "twh": 176, "kind": "Historical estimate",
     "source": "doe_lbnl"},
    {"scope": "United States", "period": "2028", "twh": [325, 580], "kind": "Scenario range",
     "source": "doe_lbnl"},
    {"scope": "World", "period": "2025", "twh": 485, "kind": "Estimated base year",
     "source": "iea_update"},
    {"scope": "World", "period": "2030", "twh": 950, "kind": "Central projection",
     "source": "iea_update"},
]
IEA_2035 = [
    {"case": "Headwinds", "twh": 700, "qualifier": "About"},
    {"case": "High Efficiency", "twh": 970, "qualifier": "About"},
    {"case": "Base", "twh": 1200, "qualifier": "About"},
    {"case": "Lift-Off", "twh": 1700, "qualifier": "Above"},
]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def transformer_evidence(study):
    designs = [
        ("Filed comparison: heavy machinery", study["designs"]["B_transformers"]),
        ("Electrical equipment: motors, pumps and compressors", study["checks"]["contaminated_controls"]),
    ]
    comparisons = []
    for label, design in designs:
        for key, measure in (("price", "Unit value"), ("volume", "Tonnes")):
            estimate = design[key]["coefs"]["TxP2"]
            comparisons.append({
                "comparison": label, "measure": measure, "gap_percent": estimate["pct"],
                "interval_log_points": estimate["ci95_wild_line"],
                "p": estimate["p_wild_line"],
            })
    goes = study["checks"]["suppliers_goes_combined"]
    return {
        "source": "grid_trade", "baseline": "2012–2020", "comparison_period": "2023–2024",
        "world_data_end": 2024, "eu_us_data_end": "2026-07",
        "flow_years": study["sample"]["flow_years"],
        "filed_pretrend_passed": all(
            study["checks"]["pretrend_rule"][key]["did_language_allowed"]
            for key in ("B_price", "B_volume")
        ),
        "comparisons": comparisons,
        "goes_export_share_china": {year: goes[year]["china_share"] for year in ("2019", "2024")},
    }


def evidence(assumptions, study, trade):
    return {
        "title": "Data-centre / AI chain", "h1": TITLE, "deck": DECK,
        "published": True, "evidence_review": assumptions["version"],
        "chokepoint": {
            "product": "AI compute", "stage": "Project commissioning", "mechanism": "diffuse",
            "physics": "Firm power, compatible hardware and the finished facility set different local limits",
            "holder": "—", "share": "—", "control": "—", "conf": "assessment", "research": True,
        },
        "sources": SOURCES,
        "energy": {"unit": "TWh per year", "grade": "B", "rows": ENERGY,
                   "global_share_2030_projection": 0.03,
                   "global_scenarios_2035": {"source": "iea_demand", "cases": IEA_2035}},
        "grid_connection_risk": {
            "source": "iea_grid", "grade": "B", "planned_capacity_at_risk_share": 0.20,
            "horizon": 2030, "measure": "share of global capacity planned for construction",
        },
        "transformers": transformer_evidence(study),
        "trade": {"source": "baci", "years": trade["years"], "nomenclature": trade["vintage"],
                  "codes": trade["codes"]},
        "readiness": evaluate(assumptions),
    }


def rows(values, row_headers=False):
    body = []
    for cells in values:
        tag = 'th scope="row"' if row_headers else "td"
        first_tag = "th" if row_headers else "td"
        first, *rest = cells
        body.append(
            f"<tr><{tag}>{escape(str(first))}</{first_tag}>"
            + "".join(f"<td>{escape(str(cell))}</td>" for cell in rest)
            + "</tr>"
        )
    return "\n".join(body)


def source_link(key, label=None):
    source = SOURCES[key]
    label = label or f'{source["title"]} ({source["year"]})'
    return f'<a href="{escape(source["url"], quote=True)}">{escape(label)}</a>'


def display_twh(value):
    if isinstance(value, list):
        return "–".join(f"{endpoint:,}" for endpoint in value)
    return f"{value:,}"


def timing_change(months_earlier):
    if months_earlier == 0:
        return "On the same date"
    magnitude = abs(months_earlier)
    unit = "month" if magnitude == 1 else "months"
    direction = "earlier" if months_earlier > 0 else "later"
    return f"{magnitude} {unit} {direction}"


def render(data, trade, assumptions):
    last_year = trade["years"][-1]
    currency = trade["years_data"][str(last_year)]
    trade_rows = []
    for code, info in trade["codes"].items():
        item = currency[code]
        top = next(iter(item["exporters"]), None)
        lead = f'{top["name"]} · {top["share"]:.0%}' if top else "—"
        value = f'${item["world_usd"] / 1e9:,.1f} billion' if item["world_usd"] else "—"
        trade_rows.append((f'{info["title"]} ({code})', value, lead, info["boundary"]))

    energy_rows = []
    for item in data["energy"]["rows"]:
        fields = (item["scope"], item["period"], display_twh(item["twh"]), item["kind"])
        cells = "".join(f"<td>{escape(value)}</td>" for value in fields)
        energy_rows.append(f'<tr>{cells}<td>{source_link(item["source"])}</td></tr>')

    summary = data["readiness"]
    cases = summary["scenarios"]
    labels = {activity["id"]: activity["label"] for activity in assumptions["activities"]}
    key_gates = ("utility_upgrades", "transformer", "electrical_install", "rack_install", "hbm", "shell")
    case_rows = []
    for result in cases.values():
        change = timing_change(result["months_earlier"]) if "compare_to" in result else "—"
        critical = [labels[key] for key in key_gates if key in result["critical_activities"]]
        case_rows.append((result["label"], result["calendar_month"], result["commissioning_month"],
                          ", ".join(critical), f'{result["usable_it_mw"]:g}', change))

    info = data["transformers"]
    comparisons = info["comparisons"]
    estimate_rows = [
        (item["comparison"], item["measure"], f'{item["gap_percent"]:+.0f}%',
         f'{item["interval_log_points"][0]:+.3f} to {item["interval_log_points"][1]:+.3f}',
         f'{item["p"]:.3f}')
        for item in comparisons
    ]
    scenarios_2035 = [(item["case"], f'{item["qualifier"]} {item["twh"]:,}')
                      for item in data["energy"]["global_scenarios_2035"]["cases"]]
    model_finding = (
        f'With faster utility work, commissioning falls {timing_change(cases["faster_grid"]["months_earlier"]).lower()} '
        "relative to the baseline. "
        f'With faster transformer delivery, commissioning falls {timing_change(cases["faster_transformer"]["months_earlier"]).lower()} '
        "relative to the baseline. "
        f'With faster delivery in the late-transformer case, commissioning falls {timing_change(cases["recover_transformer"]["months_earlier"]).lower()} '
        "relative to the late-transformer case."
    )
    power_rows = [(f'{item["pue"]:.2f}', f'{item["facility_mw"]:g}', f'{item["usable_it_mw"]:g}')
                  for item in summary["pue_sensitivity"]]
    substitutions = {
        "title": escape(data["h1"]), "deck": escape(data["deck"]),
        "version": escape(data["evidence_review"]),
        "energy_rows": "\n".join(energy_rows), "iea_scenarios": rows(scenarios_2035, True),
        "iea_grid": source_link("iea_grid", "IEA (2025), Figure 2.27"),
        "iea_demand": source_link("iea_demand", "IEA (2025), 2035 scenarios"),
        "iea_hardware": source_link("iea_update", "IEA (2026), executive summary"),
        "doe_transformers": source_link("doe_transformers", "US DOE (2024), p. 2"),
        "grid_study": source_link("grid_trade", "September 2026 Atlas transformer study, §4.2"),
        "buildout": source_link("buildout", "Atlas AI build-out analysis"),
        "trade_rows": rows(trade_rows, True), "trade_year": last_year, "estimate_rows": rows(estimate_rows),
        "tva": source_link("tva", "TVA board minutes, 11 February 2026, pp. 8–9"),
        "planning": source_link("planning", "Planning decision and inspector report, ¶5.3"),
        "firm_mw": f'{assumptions["project"]["firm_power_mw"]:g}',
        "design_pue": f'{assumptions["project"]["design_pue"]:.2f}',
        "required_mw": f'{summary["required_facility_mw"]:g}',
        "target_mw": f'{assumptions["project"]["it_load_mw"]:g}',
        "assumed_start": assumptions["project"]["start_month"],
        "scenario_rows": rows(case_rows, True), "model_finding": escape(model_finding),
        "power_rows": rows(power_rows, True),
        "sensitivity_count": summary["sensitivity"]["combinations"],
        "first_month": summary["sensitivity"]["earliest_month"],
        "last_month": summary["sensitivity"]["latest_month"],
        "source_items": "\n".join(f"<li>{source_link(key)}</li>" for key in SOURCES),
    }
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(substitutions)


def build():
    assumptions = load(ASSUMPTIONS)
    trade = load(TRADE)
    data = evidence(assumptions, load(STUDY), trade)
    article = render(data, trade, assumptions)
    EVIDENCE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    ARTICLE.write_text(article, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build()
