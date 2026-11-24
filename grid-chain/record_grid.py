"""Build the electricity-grid working paper from the dated research inputs."""

from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path
from runpy import run_path
from string import Template

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VERSION = "2026-11-24"
TITLE = "When does transformer procurement delay the grid?"
DECK = ("Procurement is slow and trade in transformer core steel is concentrated. "
        "Which constraint delays a project depends on the equipment it needs and when the site is ready.")

SOURCES = {
    "iea": ("IEA, Building the Future Transmission Grid, 2025, executive summary and ch. 2",
            "https://www.iea.org/reports/building-the-future-transmission-grid/executive-summary"),
    "entso": ("ENTSO-E, Transmission Grid Investment and Supply Chain Assessment, 2026, pp. 15–16",
              "https://eepublicdownloads.blob.core.windows.net/public-cdn-container/clean-documents/Publications/Position%20papers%20and%20reports/2026/entso-e_report_investment_supply_chain_assessment_2026_261030.pdf"),
    "doe": ("US Department of Energy, Large Power Transformer Resilience, 2024, pp. 2 and 12",
            "https://www.energy.gov/sites/default/files/2024-10/EXEC-2022-001242%20-%20Large%20Power%20Transformer%20Resilience%20Report%207-10-24.pdf"),
    "nlr": ("National Laboratory of the Rockies, Large Power Transformer Supply Chain Gap Analysis, 2026, Tables 3–4 and section 1.8",
            "https://docs.nlr.gov/docs/fy26osti/96742.pdf#page=24"),
    "prodcom": ("Eurostat, sold production, DS-059358, October 2026 snapshot",
                "https://ec.europa.eu/eurostat/databrowser/view/ds-059358/default/table?lang=en"),
    "comext": ("Eurostat, EU trade by HS and CN, DS-045409, November 2026 snapshot",
               "https://ec.europa.eu/eurostat/databrowser/view/ds-045409/default/table?lang=en"),
    "crosswalk": ("Eurostat, Prodcom List 2024 with CN correspondence, published by Statistics Netherlands",
                  "https://www.cbs.nl/-/media/_pdf/2025/21/prodcom-list_en_2024.pdf"),
    "prodcom_flags": ("Eurostat, DS-059358 quick guide, flag and rounding-base definitions, p. 2",
                      "https://ec.europa.eu/eurostat/documents/120432/19597181/Quick%2Bguide%2Bon%2Baccessing%2BPRODCOM%2Bdata%2BDS-059358.pdf/30ad2839-31cd-32b0-c0f2-d43f200be35e?t=1762360585715"),
    "baci": ("CEPII BACI, V202601, HS17 exporter series and HS02 transformer models",
             "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"),
    "trade": ("Critical Materials Atlas, September 2026 transformer trade study", "../grid-trade"),
}

MARKET = [
    {
        "basis": "Survey benchmark", "market": "International",
        "scope": "IEA 2024 industry survey, large power transformers",
        "months": 48, "measure": "Up to four years",
        "context": "Reported procurement lead time. The IEA puts the rise in power transformer prices since 2019 at around 75%.",
        "source": "iea",
    },
    {
        "basis": "Operator plans", "market": "Europe",
        "scope": "ENTSO-E 2026, 245–420 kV power transformers (its Figure 4a uses a 145–420 kV band)",
        "months": 36, "measure": "Typically at least 36 months",
        "context": "Operators report plans for 113–243 additions annually in this voltage band. Operators report a limited view of manufacturing capacity, which manufacturers do not publish.",
        "source": "entso",
    },
    {
        "basis": "Industry evidence", "market": "United States",
        "scope": "US DOE 2024, transformers rated at least 100 MVA",
        "months": 36, "measure": "Commonly quoted at 36 months",
        "context": "Reported maximum up to 60 months. MVA is a power rating and kV is a voltage rating.",
        "source": "doe",
    },
    {
        "basis": "Reported average", "market": "United States",
        "scope": "National Laboratory of the Rockies 2026 (a hydropower-focused supplement), citing Wood Mackenzie estimates",
        "months": 30, "measure": "30 months on average",
        "context": "First half of 2025. Manufacturer interviews also report long waits for bushings and tap changers.",
        "source": "nlr",
    },
]

PROJECTS = [
    {"label": "Permits and site work finish last", "permit": 28, "site": 20, "transformer": 36, "network": 40},
    {"label": "The transformer arrives last", "permit": 18, "site": 12, "transformer": 42, "network": 34},
    {"label": "The site and transformer finish together", "permit": 22, "site": 14, "transformer": 36, "network": 32},
]

EXPOSURE_LABELS = {
    "transformers": "Liquid-dielectric transformers",
    "goes": "Grain-oriented electrical steel",
    "cables": "Insulated conductors above 1,000 V",
    "switchgear": "Switchgear above 1,000 V",
    "switchboards": "Switchboards above 1,000 V",
    "inverters": "Inverters above 7.5 kVA",
    "meters": "Electricity meters",
}


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def project_results(projects, acceleration=6, installation=4):
    results = []
    for case in projects:
        site_ready = case["permit"] + case["site"]
        other = max(site_ready, case["network"])
        base = max(case["transformer"], other) + installation
        earlier = max(0, case["transformer"] - acceleration)
        improved = max(earlier, other) + installation
        results.append({
            **case, "site_ready": site_ready, "installation": installation,
            "delivered_earlier_by": acceleration, "transformer_after": earlier,
            "completion_before": base, "completion_after": improved, "months_saved": base - improved,
        })
    return results


def relative(coefficient):
    return math.expm1(coefficient)


def combine():
    published = read("out/eu_grid_supply.json")
    audit = read("eu-grid-supply/eurostat_audit.json")
    exposure = run_path(str(ROOT / "eu-grid-supply/exposure.py"))["analyze"](published, audit)

    concentration = read("grid-chain/out/goes.json")
    groups = concentration["groups"]
    goes = groups["goes"]
    series = {}
    for y, eu in audit["goes_imports"].items():
        val = goes["by_year"].get(y)
        mass = goes["mass_by_year"].get(y)

        def china(record):
            return next((entry["pct"] / 100 for entry in record["top"] if entry["iso3"] == "CHN"), None) if record else None

        series[y] = {
            "global_china_value": china(val),
            "global_china_mass": china(mass),
            "global_value_hhi": val["hhi"] if val else None,
            "global_mass_hhi": mass["hhi"] if mass else None,
            "value_share_with_mass": mass["share_of_value_with_positive_mass"] if mass else None,
            "eu_china_value": eu["eur"]["china"] / eu["eur"]["all"],
            "eu_china_mass": eu["hundred_kg"]["china"] / eu["hundred_kg"]["all"],
        }

    filed = read("out/buildout_study.json")
    replication = read("grid-chain/out/transformer_replication.json")
    regressions = {
        "heavy_machinery": filed["designs"]["B_transformers"]["price"]["coefs"]["TxP2"],
        "electrical_machinery": filed["checks"]["contaminated_controls"]["price"]["coefs"]["TxP2"],
    }
    us_imports = read("out/buildout_us.json")["checks"]
    model_table = {
        k: {"estimate": relative(v["beta"]), "interval": [relative(i) for i in v["ci95_wild_line"]],
            "p": v["p_wild_line"]}
        for k, v in regressions.items()
    }
    return {
        "title": "Electricity-grid chain", "published": True, "version": VERSION, "h1": TITLE, "deck": DECK,
        "sources": {k: {"title": title, "url": url} for k, (title, url) in SOURCES.items()},
        "chokepoint": {
            "product": "Electricity grid", "stage": "Transformer core steel",
            "mechanism": "capability", "conf": "measured", "research": True,
            "physics": ("Specialised core steel has more concentrated gross exports than the transformer basket. "
                        "Qualified capacity and project-level constraints remain unresolved."),
            "holder": "China · Japan", "share": "53% of pooled export value, 2022–24", "control": "—",
        },
        "goes_series": series,
        "pooled_export_value_hhi": {k: v["window"]["hhi"] for k, v in groups.items()},
        "goes_widths_2024": goes["value_and_mass_by_code"]["2024"],
        "eurostat_source_dates": {k: audit[k]["updated"] for k in ("trade", "sold_production")},
        "exposure": exposure,
        "us_imports_2024": {
            "goes": us_imports["goes_us_imports"]["2024"],
            "transformers": us_imports["transformer_import_origins"]["2024"],
            "source": "US Census Bureau, as extracted for the September trade note, section 4.7",
        },
        "filed_models": model_table,
        "replication": replication,
        "filed_pretrend": filed["checks"]["pretrend_rule"]["B_price"],
        "market_evidence": MARKET, "modelled_projects": project_results(PROJECTS),
    }


def number(value, decimals=0):
    return f"{value:,.{decimals}f}"


def pct(value, decimals=1):
    return "—" if value is None else f"{value:.{decimals}%}"


def table_rows(values):
    return "\n".join(
        f'<tr><th scope="row">{escape(str(title))}</th>'
        + "".join(f"<td>{escape(str(value))}</td>" for value in items)
        + "</tr>"
        for title, *items in values
    )


def trade_rows(trade):
    annual = trade["years_data"][str(trade["years"][-1])]
    for code, item in trade["codes"].items():
        row = annual[code]
        top = next(iter(row["exporters"]), None)
        usd = "$" + number(row["world_usd"] / 1e9, 1) + " billion" if row["world_usd"] else "—"
        label = "Customs origin describes the traded product. Upstream component origins and lead times are unavailable."
        yield f'{item["title"]} ({code})', usd, f'{top["name"]} · {top["share"]:.0%}' if top else "—", label


def pair_bars(exposure):
    return "\n".join(
        f'<div class="pair"><b>{escape(EXPOSURE_LABELS[key])}</b>'
        f'<div class="paired-value"><span>Imports</span><span class="track" aria-hidden="true">'
        f'<span class="fill imported" style="width:{row["share_of_imports"]:.1%}"></span></span>'
        f'<strong>{pct(row["share_of_imports"])}</strong></div>'
        f'<div class="paired-value"><span>Supply</span><span class="track" aria-hidden="true">'
        f'<span class="fill" style="width:{row["published_share"]:.1%}"></span></span>'
        f'<strong>{pct(row["published_share"])}</strong></div></div>'
        for key, row in exposure.items()
    )


def forest_rows(models):
    axis_min, axis_max = -0.10, 0.50
    def position(value):
        return (value - axis_min) / (axis_max - axis_min)
    labels = {"heavy_machinery": "Filed heavy machinery", "electrical_machinery": "Motors, pumps and compressors"}
    rows = []
    for key, model in models.items():
        lo, hi = model["interval"]
        val = model["estimate"]
        rows.append(
            f'<div class="forest-line"><b>{labels[key]}</b><div class="forest-track" aria-hidden="true">'
            f'<span class="zero" style="left:{position(0):.2%}"></span>'
            f'<span class="interval" style="left:{position(lo):.2%};width:{position(hi)-position(lo):.2%}"></span>'
            f'<span class="point" style="left:{position(val):.2%}"></span></div>'
            f'<p class="note">Estimate {val:+.1%} · 95% interval {lo:+.1%} to {hi:+.1%}</p></div>'
        )
    return "\n".join(rows)


def render(data, trade):
    series = data["goes_series"]
    exposure = data["exposure"]["components"]
    mass = data["exposure"]["goes_mass_check_2024"]
    inv = exposure["inverters"]
    low, high = inv["sensitivity"]["production"]["range"]
    goes_2024 = series["2024"]
    rounding = inv["published_production_rounding"]
    trends = table_rows(
        (year, pct(point["global_china_value"]), pct(point["global_china_mass"]),
         pct(point["eu_china_value"]), pct(point["eu_china_mass"]),
         number(point["global_value_hhi"], 3) if point["global_value_hhi"] is not None else "—",
         number(point["global_mass_hhi"], 3) if point["global_mass_hhi"] is not None else "—")
        for year, point in series.items()
    )
    scope = table_rows(
        (EXPOSURE_LABELS[key], ", ".join(row["prodcom"]), ", ".join(row["cn8_2024"]),
         row["exposure_band"], pct(row["crosscheck_value_share"]),
         ", ".join(sorted(set(row["production_flags"].values()))) or "—")
        for key, row in exposure.items()
    )
    cases = ("production", "trade_valuation", "exports", "product_scope", "reexport", "combined_excluding_scope")
    sensitivity = table_rows(
        (EXPOSURE_LABELS[key], *(" to ".join(pct(v) for v in row["sensitivity"][case]["range"]) for case in cases),
         ", ".join(row["sensitivity"]["combined_excluding_scope"]["exposure_bands"]))
        for key, row in exposure.items()
    )
    market = "\n".join(
        f'<tr><th scope="row">{escape(row["market"])}</th><td>{escape(row["scope"])}</td>'
        f'<td>{escape(row["measure"])}</td><td>{escape(row["context"])} '
        f'<a href="#source-{row["source"]}">Source</a></td></tr>'
        for row in data["market_evidence"]
    )
    sources = "\n".join(f'<li id="source-{key}"><a href="{escape(url, quote=True)}">{escape(label)}</a></li>'
                        for key, (label, url) in SOURCES.items())
    return Template((HERE / "article.html.in").read_text(encoding="utf-8")).substitute({
        "title": escape(TITLE), "deck": escape(DECK), "version": VERSION,
        "trends": trends, "pairs": pair_bars(exposure), "crosswalk": scope, "sensitivity": sensitivity,
        "forest_rows": forest_rows(data["filed_models"]), "market": market, "sources": sources,
        "pooled_hhi": number(data["pooled_export_value_hhi"]["goes"], 3),
        "transformer_hhi": number(data["pooled_export_value_hhi"]["transformers"], 3),
        "global_start": pct(series["2019"]["global_china_value"]),
        "global_end": pct(goes_2024["global_china_value"]),
        "global_mass_end": pct(goes_2024["global_china_mass"]),
        "mass_coverage": pct(goes_2024["value_share_with_mass"], 2),
        "us_goes_china": pct(data["us_imports_2024"]["goes"]["china_value_share"]),
        "us_transformer_china": pct(data["us_imports_2024"]["transformers"]["china_share"]),
        "eu_start": pct(series["2019"]["eu_china_value"]),
        "eu_end": pct(series["2025"]["eu_china_value"]),
        "goes_import_mass": pct(mass["china_import_share"]),
        "goes_supply_mass": pct(mass["china_apparent_supply_share"]),
        "inverter_sensitivity_low": pct(low), "inverter_sensitivity_high": pct(high),
        "inverter_rounding_base": number(rounding["base_eur"] / 1e9),
        "inverter_rounding_lower_share": pct(rounding["share_from_production_rounding_alone"][0]),
        "wide_hhi": number(data["goes_widths_2024"]["722511"]["value"]["hhi"], 3),
        "narrow_hhi": number(data["goes_widths_2024"]["722611"]["value"]["hhi"], 3),
        "project_rows": table_rows(
            (r["label"], f'{r["permit"]} + {r["site"]}', r["transformer"], r["network"],
             r["completion_before"], r["completion_after"], r["months_saved"])
            for r in data["modelled_projects"]
        ),
        "trade_year": trade["years"][-1], "trade_rows": table_rows(trade_rows(trade)),
    })


def main():
    trade = read("grid-chain/out/grid_trade.json")
    evidence = combine()
    html = render(evidence, trade)
    (HERE / "out/grid_chain.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
    (HERE / "grid-chain.html").write_text(html, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
