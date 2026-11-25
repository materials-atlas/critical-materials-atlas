"""Build the supplier-exposure working paper (grid-exposure.html) from the filed results.

Inputs: out/eu_grid_supply.json (the filed results by year), eu-grid-supply/eurostat_audit.json (the second
Eurostat extraction), eu-grid-supply/exposure.py (bands and sensitivity), out/buildout_us.json (US customs
shares from the September study) and paper.html.in. No network access. Run from the repository root:
    python eu-grid-supply/build_paper.py
Nothing here changes a filed figure. Additions made after filing are labelled on the page.
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from runpy import run_path
from string import Template

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VERSION = "2026-11-25"
TITLE = "Which parts of Europe's grid come from China, on a supply basis?"
DECK = ("In 2024 China supplied 34% of the EU's transformer imports and 9% of its transformer supply. "
        "The difference between the two measures is the part of supply that the EU imports at all.")
LABELS = {
    "transformers": "Liquid-dielectric transformers", "goes": "Grain-oriented electrical steel",
    "cables": "Insulated conductors above 1,000 V", "switchgear": "Switchgear above 1,000 V",
    "switchboards": "Switchboards above 1,000 V", "inverters": "Inverters above 7.5 kVA",
    "meters": "Electricity meters, including household smart meters",
}
SOURCES = {
    "prodcom": ("Eurostat, sold production, DS-059358, October 2026 snapshot",
                "https://ec.europa.eu/eurostat/databrowser/view/ds-059358/default/table?lang=en"),
    "comext": ("Eurostat, EU trade by HS and CN, DS-045409, November 2026 snapshot",
               "https://ec.europa.eu/eurostat/databrowser/view/ds-045409/default/table?lang=en"),
    "crosswalk": ("Eurostat, Prodcom List 2024 with CN correspondence, published by Statistics Netherlands",
                  "https://www.cbs.nl/-/media/_pdf/2025/21/prodcom-list_en_2024.pdf"),
    "prodcom_flags": ("Eurostat, DS-059358 quick guide, flag and rounding-base definitions, p. 2",
                      "https://ec.europa.eu/eurostat/documents/120432/19597181/Quick%2Bguide%2Bon%2Baccessing%2BPRODCOM%2Bdata%2BDS-059358.pdf/30ad2839-31cd-32b0-c0f2-d43f200be35e?t=1762360585715"),
    "mejean": ("Mejean and Rousseaux, Identifying European trade dependencies, version of 9 July 2025 (published as chapter 3 of CEPR Paris Report 2, 2024)",
               "https://pierrerousseaux.github.io/research/MejeanRousseaux_ITCEI.pdf"),
    "arjona": ("Arjona, Connell and Herghelegiu, An enhanced methodology to monitor the EU's strategic dependencies and vulnerabilities, Single Market Economics Papers WP2023/14",
               "https://single-market-economy.ec.europa.eu/publications/enhanced-methodology-monitor-eus-strategic-dependencies-and-vulnerabilities_en"),
    "prereg": ("Critical Materials Atlas, pre-registration of the seven-component study, filed 21 September 2026",
               "eu-grid-supply/PREREGISTRATION.md"),
    "trade": ("Critical Materials Atlas, September 2026 transformer trade study, sections 4.6b, 4.6c and 4.7", "grid-trade"),
}
YEARS = ("2019", "2020", "2021", "2022", "2023", "2024")


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def pct(x, places=1):
    return "" if x is None else f"{100 * x:.{places}f}%"


def row(label, cells, numeric=True):
    cls = ' class="n"' if numeric else ""
    return (f'<tr><th scope="row">{escape(str(label))}</th>'
            + "".join(f"<td{cls}>{escape(str(c))}</td>" for c in cells) + "</tr>")


def reading(ratio):
    """The filed two-sided reading of the ratio of the supply share to the import share."""
    if ratio < 0.5:
        return "overstates dependence"
    return "partly overstates dependence" if ratio < 0.8 else "a fair guide"


def filed_band(share):
    for limit, name in ((0.10, "low (under 10%)"), (0.25, "material (10% to 25%)"), (0.50, "high (25% to 50%)")):
        if share < limit:
            return name
    return "critical (above 50%)"


def evaluate():
    published = read("out/eu_grid_supply.json")
    audit = read("eu-grid-supply/eurostat_audit.json")
    exposure = run_path(str(HERE / "exposure.py"))["analyze"](published, audit)
    year = str(published["headline_year"])
    components = {}
    for key, comp in published["components"].items():
        r = comp["years"][year]
        m, s = r["china_share_of_imports"], r["china_share_of_supply"]
        penetration = r["imports_meur"] / r["apparent_supply_meur"]
        if abs(m * penetration - s) > 0.001:
            raise SystemExit(f"{key}: import share times import penetration does not give the published supply share")
        x = exposure["components"][key]
        context = {}
        for y in YEARS:
            ry = comp["years"][y]
            context[y] = None if ry["production_missing_codes"] else ry["china_share_of_supply"]
        components[key] = {
            "label": LABELS[key], "share_of_imports": m, "import_penetration": penetration, "share_of_supply": s,
            "supply_share_under_half_import_share": s < 0.5 * m,
            "ratio_supply_to_import_share": s / m, "filed_reading": reading(s / m), "filed_band": filed_band(s),
            "net_trade_meur": r["exports_meur"] - r["imports_meur"],
            "band": x["exposure_band"], "prodcom": x["prodcom"], "cn8_2024": x["cn8_2024"],
            "second_extraction_share": x["crosscheck_value_share"],
            "production_flags": sorted(set(x["production_flags"].values())),
            "sensitivity": x["sensitivity"], "context_supply_share": context,
        }
    us = read("out/buildout_us.json")["checks"]
    split = published["inverters_2026_by_function"]
    return {
        "headline_year": int(year), "components": components,
        "n_supply_share_under_half": sum(c["supply_share_under_half_import_share"] for c in components.values()),
        "max_second_extraction_difference": max(abs(c["second_extraction_share"] - c["share_of_supply"]) for c in components.values()),
        "bands_spanned": {k: len(c["sensitivity"]["combined_excluding_scope"]["exposure_bands"]) for k, c in components.items()},
        "goes_mass_check_2024": exposure["goes_mass_check_2024"],
        "goes_import_share_2025": audit["goes_imports"]["2025"]["eur"]["china"] / audit["goes_imports"]["2025"]["eur"]["all"],
        "inverter_rounding": exposure["components"]["inverters"]["published_production_rounding"],
        "inverters_jan_jul_2026_china_share_of_imports": {
            "solar": split["solar_mppt_85044084"]["from_china_meur"] / split["solar_mppt_85044084"]["imports_meur"],
            "other": split["other_85044087"]["from_china_meur"] / split["other_85044087"]["imports_meur"]},
        "us_2024": {"goes_china_share_of_import_value": us["goes_us_imports"]["2024"]["china_value_share"],
                    "transformer_china_share_of_import_value": us["transformer_import_origins"]["2024"]["china_share"]},
        "eurostat_source_dates": {k: audit[k]["updated"] for k in ("trade", "sold_production")},
    }


def pair_bars(components):
    return "\n".join(
        f'<div class="pair"><b>{escape(c["label"])}</b>'
        f'<div class="paired-value"><span>Imports</span><span class="track" aria-hidden="true">'
        f'<span class="fill imported" style="width:{c["share_of_imports"]:.1%}"></span></span><strong>{pct(c["share_of_imports"])}</strong></div>'
        f'<div class="paired-value"><span>Supply</span><span class="track" aria-hidden="true">'
        f'<span class="fill" style="width:{c["share_of_supply"]:.1%}"></span></span><strong>{pct(c["share_of_supply"])}</strong></div></div>'
        for c in components.values())


def render(r):
    comps = r["components"]
    tr, go, inv = comps["transformers"], comps["goes"], comps["inverters"]
    # The page states these in words. Stop if the numbers no longer support the sentences.
    exporters = {k for k, c in comps.items() if c["net_trade_meur"] > 0}
    checks = [
        (r["n_supply_share_under_half"] == 6 and not inv["supply_share_under_half_import_share"], "the half-share rule no longer holds for six components with inverters the exception"),
        (exporters == {"transformers", "cables", "switchgear", "switchboards", "inverters"}, "the list of net-exported components has changed"),
        (max(comps, key=lambda k: comps[k]["import_penetration"]) == "inverters", "inverters no longer have the highest import penetration"),
        (sorted(r["bands_spanned"].values()) == [1, 1, 1, 2, 2, 2, 2], "the number of bands spanned by the sensitivity ranges has changed"),
        (round(100 * tr["share_of_imports"]) == 34 and round(100 * tr["share_of_supply"]) == 9, "the transformer shares in the deck have changed"),
        (all(2 <= 1 / c["ratio_supply_to_import_share"] < 7.5 for k, c in comps.items() if k != "inverters"),
         "the overstatement is no longer a factor of two to seven"),
        (inv["filed_reading"] == "a fair guide" and 0.45 < go["ratio_supply_to_import_share"] < 0.5, "the inverter reading or the electrical-steel borderline has changed"),
        (all(round(1000 * c["second_extraction_share"]) == round(1000 * c["share_of_supply"]) for c in comps.values()),
         "the second extraction no longer reproduces every share to the first decimal place"),
    ]
    for ok, message in checks:
        if not ok:
            raise SystemExit("grid-exposure text no longer matches the data: " + message)

    lowest = min(comps.values(), key=lambda c: c["import_penetration"])
    result_rows = [row(c["label"], [pct(c["share_of_imports"]), f'{c["ratio_supply_to_import_share"]:.2f}', pct(c["share_of_supply"]),
                                    c["filed_reading"], f'{c["net_trade_meur"]:+,.0f}', c["filed_band"]]) for c in comps.values()]
    context_rows = [row(c["label"], [pct(c["context_supply_share"][y]) for y in YEARS]) for c in comps.values()]
    code_rows = [row(c["label"], [", ".join(c["prodcom"]), ", ".join(c["cn8_2024"]), pct(c["second_extraction_share"]),
                                  ", ".join(c["production_flags"]) or "none"], numeric=False) for c in comps.values()]
    cases = ("production", "trade_valuation", "exports", "product_scope", "reexport", "combined_excluding_scope")
    sens_rows = [row(c["label"], [" to ".join(pct(v) for v in c["sensitivity"][case]["range"]) for case in cases]
                     + [", ".join(c["sensitivity"]["combined_excluding_scope"]["exposure_bands"])]) for c in comps.values()]
    mass, rounding = r["goes_mass_check_2024"], r["inverter_rounding"]
    values = {
        "title": escape(TITLE), "deck": escape(DECK), "version": VERSION,
        "tr_m": pct(tr["share_of_imports"]), "tr_s": pct(tr["share_of_supply"]),
        "go_m": pct(go["share_of_imports"]), "go_s": pct(go["share_of_supply"]),
        "inv_m": pct(inv["share_of_imports"]), "inv_s": pct(inv["share_of_supply"]),
        "n_under_half": "six", "pairs": pair_bars(comps),
        "result_rows": "\n".join(result_rows), "context_rows": "\n".join(context_rows),
        "code_rows": "\n".join(code_rows), "sensitivity_rows": "\n".join(sens_rows),
        "pen_min": f'{lowest["ratio_supply_to_import_share"]:.2f}', "pen_min_label": lowest["label"].split(" above")[0].lower() + " above 1,000 V" if " above" in lowest["label"] else lowest["label"].lower(),
        "pen_max": f'{inv["ratio_supply_to_import_share"]:.2f}', "go_ratio": f'{go["ratio_supply_to_import_share"]:.2f}',
        "inv_solar": pct(r["inverters_jan_jul_2026_china_share_of_imports"]["solar"], 0),
        "inv_other": pct(r["inverters_jan_jul_2026_china_share_of_imports"]["other"], 0),
        "go_m_2025": pct(r["goes_import_share_2025"]),
        "go_m_mass": pct(mass["china_import_share"]), "go_s_mass": pct(mass["china_apparent_supply_share"]),
        "tr_lo": pct(tr["sensitivity"]["combined_excluding_scope"]["range"][0]), "tr_hi": pct(tr["sensitivity"]["combined_excluding_scope"]["range"][1]),
        "inv_lo": pct(inv["sensitivity"]["production"]["range"][0]), "inv_hi": pct(inv["sensitivity"]["production"]["range"][1]),
        "inv_base": f'{rounding["base_eur"] / 1e9:.0f}', "inv_round_lo": pct(rounding["share_from_production_rounding_alone"][0]),
        "us_goes": pct(r["us_2024"]["goes_china_share_of_import_value"]), "us_tr": pct(r["us_2024"]["transformer_china_share_of_import_value"]),
        "sources": "\n".join(f'  <li id="source-{k}"><a href="{escape(url, quote=True)}">{escape(label)}</a></li>' for k, (label, url) in SOURCES.items()),
    }
    return Template((HERE / "paper.html.in").read_text(encoding="utf-8")).substitute(values)


def main():
    results = evaluate()
    data = {"title": TITLE, "deck": DECK, "version": VERSION,
            "filed": "eu-grid-supply/PREREGISTRATION.md, 21 September 2026; results in grid-trade.html sections 4.6b and 4.6c",
            "added_after_filing": ["decomposition into import penetration", "product-correspondence check", "sensitivity ranges"],
            "sources": {k: {"title": t, "url": u} for k, (t, u) in SOURCES.items()}, "results": results}
    (ROOT / "out" / "grid_exposure.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (ROOT / "grid-exposure.html").write_text(render(results), encoding="utf-8", newline="\n")
    t = results["components"]["transformers"]
    print("wrote grid-exposure.html and out/grid_exposure.json: transformers %s of imports, %s of supply (2024)"
          % (pct(t["share_of_imports"]), pct(t["share_of_supply"])))


if __name__ == "__main__":
    main()
