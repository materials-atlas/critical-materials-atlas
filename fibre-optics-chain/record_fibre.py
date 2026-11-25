"""Build the static optical-fibre study and its evidence JSON.

Inputs: evidence_inputs.json (source figures transcribed and checked 25 Nov 2026), article.html.in and
out/fibre_trade.json (the frozen BACI extract). No network access. Run from the repository root:
    python fibre-optics-chain/record_fibre.py
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from string import Template

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "evidence_inputs.json"
TEMPLATE = HERE / "article.html.in"
TRADE = HERE / "out" / "fibre_trade.json"
OUT = HERE / "out" / "fibre_chain.json"
ARTICLE = HERE / "fibre-optics-chain.html"

TITLE = "Germanium in optical fibre and the suppliers of submarine cables"
DECK = ("Standard optical fibre has a germanium-doped core. The quantity is small and known only from estimates. "
        "Fibre for the longest submarine cables is offered with a pure silica core. "
        "Four suppliers built 83% of submarine cable length between 2020 and 2024.")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pct(x, places=0):
    return f"{100 * x:.{places}f}%"


def row(label, cells, numeric=True):
    cls = ' class="n"' if numeric else ""
    return (f'<tr><th scope="row">{escape(str(label))}</th>'
            + "".join(f"<td{cls}>{escape(str(c))}</td>" for c in cells) + "</tr>")


def evaluate(inputs):
    m = inputs["usgs_fibre_model"]
    sm, mm = m["single_mode"], m["multimode"]
    if abs(sm["germanium_tonnes"] + mm["germanium_tonnes"] - m["total_contained_tonnes"]) > 0.005:
        raise SystemExit("the two fibre types do not add to the USGS total")
    if abs(m["total_contained_tonnes"] * m["primary_to_incorporated_ratio"] - m["primary_tonnes"]) > 0.05:
        raise SystemExit("contained germanium times the USGS ratio does not give the USGS primary figure")
    for f in (sm, mm):      # the per-kilometre figures are rounded in the source, so allow 5%
        implied = f["us_million_fibre_km"] * f["germanium_g_per_km"]
        if abs(implied - f["germanium_tonnes"]) > 0.05 * max(implied, f["germanium_tonnes"]) + 0.005:
            raise SystemExit("length times grams per kilometre does not reproduce the USGS tonnage")
    ratio = m["primary_to_incorporated_ratio"]
    per_km = lambda s: s * mm["germanium_g_per_km"] + (1 - s) * sm["germanium_g_per_km"]      # noqa: E731
    us_split = mm["us_market_share"] / (mm["us_market_share"] + sm["us_market_share"])
    world_km = inputs["scenarios"]["world_million_fibre_km"]
    implied_world = [m["us_million_fibre_km"] / m["us_fibre_share_of_world"],
                     m["north_america_demand_2021"]["million_fibre_km"] / m["north_america_demand_2021"]["share_of_world"]]
    if not (min(implied_world) * 0.95 <= world_km <= max(implied_world) * 1.05):
        raise SystemExit("the assumed world fibre length is outside the range implied by the USGS figures")
    screen = []
    for s in inputs["scenarios"]["multimode_shares_of_length"] + [us_split]:
        contained = world_km * per_km(s)          # million km times grams per km = tonnes
        screen.append({"multimode_share": s, "us_split": s == us_split, "grams_per_km": per_km(s),
                       "contained_tonnes": contained, "primary_tonnes": contained * ratio})
    supply = inputs["germanium_supply"]
    use = inputs["germanium_use_shares"]
    w22 = supply["usgs_world_2022"]
    if sum(w22["primary_tonnes"].values()) != w22["total_tonnes"] or w22["total_tonnes"] - w22["primary_tonnes"]["China"] != w22["outside_china_tonnes"]:
        raise SystemExit("the USGS 2022 country estimates do not add to its world total")
    benchmark = use["world_2020_2022_fibre"] * w22["total_tonnes"]
    g_needed = benchmark / ratio / world_km
    matching_share = (g_needed - sm["germanium_g_per_km"]) / (mm["germanium_g_per_km"] - sm["germanium_g_per_km"])
    model = {"multimode_share_of_us_glass_fibre": us_split, "multimode_over_single_mode_per_km": mm["germanium_g_per_km"] / sm["germanium_g_per_km"],
             "multimode_share_of_contained": mm["germanium_tonnes"] / m["total_contained_tonnes"],
             "implied_world_million_fibre_km_2021": implied_world, "screen": screen,
             "benchmark_tonnes": benchmark, "multimode_share_matching_benchmark": matching_share,
             "china_share_of_usgs_2022_estimate": w22["primary_tonnes"]["China"] / w22["total_tonnes"]}

    mk = inputs["germanium_market"]
    ex, price, imp = mk["china_metal_exports_jan_sep_kg"], mk["price_metal_usd_per_kg"], mk["us_imports_metal_kg"]
    market = {"china_exports_change_2023_2025": ex["2025"] / ex["2023"] - 1, "price_multiple_2023_2025": price["2025"] / price["2023"],
              "us_metal_imports_change_2024_2025": imp["2025"] / imp["2024"] - 1}
    if abs(supply["usgs_china_2023"]["refined_tonnes"] / supply["usgs_china_2023"]["assumed_world_tonnes"] - supply["usgs_china_2023"]["share"]) > 0.005:
        raise SystemExit("the USGS China share does not follow from its own tonnages")

    sup = inputs["submarine_suppliers_2020_2024"]
    total_km = sum(s["thousand_km"] for s in sup["suppliers"])
    shares = {}
    for s in sup["suppliers"]:
        shares[s["name"]] = s["thousand_km"] / total_km
        if abs(shares[s["name"]] - s["printed_share"]) > 0.0006:
            raise SystemExit(f'{s["name"]}: the cable length does not reproduce the printed share')
    tier = sup["tier_one"]
    suppliers = {"total_thousand_km": total_km, "shares": shares, "tier_one_share": sum(shares[n] for n in tier),
                 "hhi_lower_bound": round(sum((100 * shares[n]) ** 2 for n in tier + ["Xtera"]))}
    ves = inputs["vessels_2025"]
    laying = sum(o["laying"] for o in ves["owners"])
    maint = sum(o["maintenance"] for o in ves["owners"])
    if (laying, maint, laying + maint) != (ves["printed_totals"]["laying"], ves["printed_totals"]["maintenance"], ves["printed_totals"]["all"]):
        raise SystemExit("the vessel rows do not add to the printed totals")
    own = {o["owner"]: o for o in ves["owners"]}
    vessels = {"laying": laying, "maintenance": maint, "all": laying + maint,
               "subcom_asn_share_of_laying": (own["SubCom"]["laying"] + own["ASN"]["laying"]) / laying}

    checks = [
        (0.825 <= suppliers["tier_one_share"] < 0.835, "the four suppliers no longer hold 83% of cable length"),
        (model["multimode_share_of_contained"] > 0.95, "multimode fibre no longer holds nearly all the germanium in the USGS model"),
        (45 < model["multimode_over_single_mode_per_km"] < 52, "the per-kilometre ratio is no longer about 49"),
        (0.84 < model["china_share_of_usgs_2022_estimate"] < 0.87, "China is no longer 86% of the USGS 2022 estimate"),
        (0.18 < matching_share < 0.26, "the multimode share that matches the comparison figure is no longer about a fifth"),
        (-0.82 < market["china_exports_change_2023_2025"] < -0.77, "China's export fall is no longer about four-fifths"),
        (2.8 < market["price_multiple_2023_2025"] < 3.1, "the price is no longer about three times its 2023 level"),
        (29 < screen[-1]["primary_tonnes"] / screen[0]["primary_tonnes"] < 31, "the screen no longer ranges thirty-fold"),
        (vessels["subcom_asn_share_of_laying"] == 0.5, "SubCom and ASN no longer own half of the cable-laying vessels"),
    ]
    for ok, message in checks:
        if not ok:
            raise SystemExit("fibre page text no longer matches the data: " + message)
    return {"germanium_model": model, "germanium_market": market, "submarine_suppliers": suppliers, "vessels": vessels}


def link(sources, key, label=None):
    s = sources[key]
    return f'<a href="{escape(s["url"], quote=True)}">{escape(label or s["title"])}</a>.'


def render(inputs, r):
    src = inputs["sources"]
    m = inputs["usgs_fibre_model"]
    sm, mm = m["single_mode"], m["multimode"]
    model, market, sup_r, ves = r["germanium_model"], r["germanium_market"], r["submarine_suppliers"], r["vessels"]
    supply, use, mk = inputs["germanium_supply"], inputs["germanium_use_shares"], inputs["germanium_market"]
    proc = m["process"]

    model_rows = [
        row("Core diameter, micrometres", [sm["core_diameter_um"], mm["core_diameter_um"]]),
        row("Mass of the core, grams per kilometre of fibre", [sm["core_g_per_km"], mm["core_g_per_km"]]),
        row("Germanium, grams per kilometre of fibre", [sm["germanium_g_per_km"], mm["germanium_g_per_km"]]),
        row("Share of the US market", [pct(sm["us_market_share"], 1), pct(mm["us_market_share"], 1)]),
        row("Length made in the United States in 2021, million kilometres", [sm["us_million_fibre_km"], mm["us_million_fibre_km"]]),
        row("Germanium contained, tonnes", [sm["germanium_tonnes"], mm["germanium_tonnes"]]),
    ]
    screen_rows = []
    for x in model["screen"]:
        label = (f'{pct(x["multimode_share"], 1)} (the split USGS uses for the United States)' if x["us_split"]
                 else ("None" if x["multimode_share"] == 0 else pct(x["multimode_share"])))
        screen_rows.append(row(label, [f'{x["grams_per_km"]:.3f}', f'{x["contained_tonnes"] + 1e-9:,.1f}', f'{x["primary_tonnes"] + 1e-9:,.0f}']))

    sup = inputs["submarine_suppliers_2020_2024"]
    supplier_rows = []
    for s in sup["suppliers"]:
        vessels = "" if s["laying_vessels"] is None else (str(s["laying_vessels"]) if s["laying_vessels"] else "none")
        supplier_rows.append(row(s["name"], [s["country"], f'{s["thousand_km"]:,.1f}', pct(sup_r["shares"][s["name"]], 1), vessels]))
    supplier_rows.append(row("Total", ["", f'{sup_r["total_thousand_km"]:,.1f}', "", ""]))

    years = ("2021", "2022", "2023", "2024", "2025")
    market_rows = [
        row("Germanium metal price, US dollars per kilogram", [f'{mk["price_metal_usd_per_kg"][y]:,}' for y in years]),
        row("US imports of germanium metal, kilograms", [f'{mk["us_imports_metal_kg"][y]:,}' for y in years]),
        row("US imports of germanium dioxide, kilograms of germanium", [f'{mk["us_imports_dioxide_kg"][y]:,}' for y in years]),
        row("China's exports of germanium metal, January to September, kilograms",
            [f'{mk["china_metal_exports_jan_sep_kg"][y]:,}' if y in mk["china_metal_exports_jan_sep_kg"] else "" for y in years]),
    ]

    tr = load(TRADE)
    tyear = tr["years"][-1]
    trade_rows = []
    for code, info in tr["codes"].items():
        item = tr["years_data"][str(tyear)][code]
        top = next(iter(item["exporters"]), None)
        lead = f'{top["name"]} · {top["share"]:.0%}' if top else "not available"
        cells = (f'{info["title"]} ({code})', f'USD {item["world_usd"] / 1e9:,.1f} billion', lead, inputs["trade_boundaries"][code])
        trade_rows.append(f'<tr data-trade-code="{escape(code)}">' + "".join(f"<td>{escape(c)}</td>" for c in cells) + "</tr>")

    gecl4 = m["us_gecl4_for_fibre_kg"]
    cn = inputs["world_fibre"]["china_2025_brokerage_estimate"]
    dest = mk["china_export_destinations_2025"]
    ds = mk["us_dioxide_sources_2021_2024"]
    lo, hi = model["implied_world_million_fibre_km_2021"]
    three = sup_r["shares"]["ASN"] + sup_r["shares"]["SubCom"] + sup_r["shares"]["NEC"]
    values = {
        "title": escape(TITLE), "deck": escape(DECK), "date": inputs["version"],
        "sm_g": sm["germanium_g_per_km"], "mm_g": mm["germanium_g_per_km"], "per_km_ratio": f'{model["multimode_over_single_mode_per_km"]:.0f}',
        "contained": m["total_contained_tonnes"], "mm_contained": mm["germanium_tonnes"], "sm_contained": sm["germanium_tonnes"],
        "primary": m["primary_tonnes"], "ratio": m["primary_to_incorporated_ratio"], "geo2": pct(0.04), "ge_frac": pct(m["assumed_germanium_fraction_of_core"], 1),
        "inc_lo": pct(proc["incorporated_share"][0]), "inc_hi": pct(proc["incorporated_share"][1]),
        "rec_lo": pct(proc["waste_recovered_share"][0]), "rec_hi": pct(proc["waste_recovered_share"][1]),
        "recycled_input": pct(proc["recycled_share_of_input"]),
        "us_2016": pct(use["us_2016_fibre"]), "us_model": pct(use["us_model_input_fibre"], 1), "world_use": pct(use["world_2020_2022_fibre"]),
        "model_rows": "\n".join(model_rows), "screen_rows": "\n".join(screen_rows),
        "world_km": inputs["scenarios"]["world_million_fibre_km"], "world_lo": f"{min(lo, hi) + 1e-9:.0f}", "world_hi": f"{max(lo, hi) + 1e-9:.0f}",
        "us_km": m["us_million_fibre_km"], "us_km_share": pct(m["us_fibre_share_of_world"], 1),
        "na_km": m["north_america_demand_2021"]["million_fibre_km"], "na_share": pct(m["north_america_demand_2021"]["share_of_world"]),
        "benchmark": f'{model["benchmark_tonnes"]:.0f}', "matching": pct(model["multimode_share_matching_benchmark"]),
        "assumed_world": supply["usgs_china_2023"]["assumed_world_tonnes"],
        "w22": supply["usgs_world_2022"]["total_tonnes"], "w22_cn": supply["usgs_world_2022"]["primary_tonnes"]["China"],
        "w22_cn_share": pct(model["china_share_of_usgs_2022_estimate"]), "w22_out": supply["usgs_world_2022"]["outside_china_tonnes"],
        "w22_ca": supply["usgs_world_2022"]["primary_tonnes"]["Canada"], "w22_ru": supply["usgs_world_2022"]["primary_tonnes"]["Russia"],
        "w22_be": supply["usgs_world_2022"]["primary_tonnes"]["Belgium"],
        "cn_t": supply["usgs_china_2023"]["refined_tonnes"], "cn_share": pct(supply["usgs_china_2023"]["share"]),
        "cn_cap": supply["usgs_china_2023"]["china_capacity_tonnes"], "iea_share": pct(supply["iea_2025_table_share"]),
        "kz": supply["iea_korea_zinc_planned_tonnes"], "old_share": pct(supply["previous_page_share"]),
        "market_rows": "\n".join(market_rows),
        "ex_2023": f'{mk["china_metal_exports_jan_sep_kg"]["2023"]:,}', "ex_2025": f'{mk["china_metal_exports_jan_sep_kg"]["2025"]:,}',
        "ex_change": pct(-market["china_exports_change_2023_2025"]),
        "dest": ", ".join(f"{k} ({pct(v)})" for k, v in list(dest.items())[:-1]) + " and " + " ".join(f"{k} ({pct(v)})" for k, v in list(dest.items())[-1:]),
        "price_2023": f'{mk["price_metal_usd_per_kg"]["2023"]:,}', "price_2025": f'{mk["price_metal_usd_per_kg"]["2025"]:,}',
        "us_imp_change": pct(-market["us_metal_imports_change_2024_2025"]),
        "ds_be": pct(ds["Belgium"]), "ds_ca": pct(ds["Canada"]),
        "ms_cn": pct(mk["us_metal_sources_2021_2024"]["China"]), "ms_be": pct(mk["us_metal_sources_2021_2024"]["Belgium"]),
        "ms_de": pct(mk["us_metal_sources_2021_2024"]["Germany"]),
        "gecl4_lo": f"{min(gecl4.values()) / 1000:.1f}", "gecl4_hi": f"{max(gecl4.values()) / 1000:.1f}",
        "sei_km": inputs["world_fibre"]["sumitomo_2018_million_km"],
        "cn_preform": pct(cn["preform"]), "cn_fibre": pct(cn["fibre"]), "cn_cable": pct(cn["cable"]),
        "supplier_rows": "\n".join(supplier_rows), "tier_share": pct(sup_r["tier_one_share"]), "three_share": pct(three),
        "asn": pct(sup_r["shares"]["ASN"], 1), "subcom": pct(sup_r["shares"]["SubCom"], 1), "nec": pct(sup_r["shares"]["NEC"], 1),
        "hmn": pct(sup_r["shares"]["HMN Tech"], 1), "other": pct(sup_r["shares"]["Other suppliers (systems without repeaters)"], 1),
        "xtera": pct(sup_r["shares"]["Xtera"], 1),
        "hhi": f'{sup_r["hhi_lower_bound"]:,}',
        "v_all": ves["all"], "v_lay": ves["laying"], "v_maint": ves["maintenance"],
        "trade_rows": "\n".join(trade_rows), "trade_year": tyear,
        "ofr2024": link(src, "ofr2024", "USGS Open-File Report 2024-1057"), "mcs2026": link(src, "mcs2026", "USGS, germanium, 2026 edition"),
        "mcs2025": link(src, "mcs2025", "USGS, germanium, 2025 edition"), "ofr2026": link(src, "ofr2026", "USGS Open-File Report 2026-1018"),
        "iea": link(src, "iea2026", "IEA, Global Critical Minerals Outlook 2026"),
        "itu_manual": link(src, "itu_manual", "ITU, Optical fibres, cables and systems"), "itu_g654": link(src, "itu_g654", "ITU-T Recommendation G.654"),
        "sei": link(src, "sei_tr86", "Sumitomo Electric, SEI Technical Review No. 86"), "sumitomo_z": link(src, "sumitomo_z", "Sumitomo Electric, Z Fiber data sheets"),
        "corning": link(src, "corning_ex3000", "Corning, Vascade EX3000 product sheet"), "morana": link(src, "morana2020", "Morana and others (2020)"),
        "lightera": link(src, "lightera", "Lightera, TeraWave SCUBA 125"),
        "eu": link(src, "eu_annex", "European Commission expert group, Annex, October 2025"),
        "abels": link(src, "abels_babic", "Abels and Babić (2026)"), "scmp": link(src, "scmp", "South China Morning Post, 8 May 2026"),
        "wco81": link(src, "wco_ch81", "WCO, HS 2017, Chapter 81"), "wco28": link(src, "wco_ch28", "WCO, HS 2017, Chapter 28"),
        "wco85": link(src, "wco_ch85", "WCO, HS 2017, Chapter 85"), "wco90": link(src, "wco_ch90", "WCO, HS 2017, Chapter 90"),
        "baci": link(src, "baci", "CEPII BACI V202601"),
        "references": "\n".join(f'    <li><a href="{escape(s["url"], quote=True)}">{escape(s["title"])}</a> · {escape(s["vintage"])}</li>'
                                for s in src.values()),
    }
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(values)


def build():
    inputs = load(INPUTS)
    results = evaluate(inputs)
    tier = pct(results["submarine_suppliers"]["tier_one_share"])
    makers = len(inputs["submarine_suppliers_2020_2024"]["repeatered_fibre_makers"])
    data = {
        "title": "Fibre-optics / telecom chain", "h1": TITLE, "deck": DECK, "published": True, "version": inputs["version"],
        "chokepoint": {
            "product": "Optical fibre and submarine cable systems", "stage": "Fibre for long submarine systems; cable system supply",
            "mechanism": "capability",
            "physics": "Ultra-low-loss fibre and cable systems with repeaters are each made by a few firms",
            "holder": "US · JP (fibre); FR · US · JP · CN (systems)",
            "share": f"{makers} firms make fibre for submarine systems with repeaters; 4 suppliers built {tier} of cable length (2020–2024)",
            "control": "—", "conf": "estimate",
        },
        "sources": inputs["sources"],
        "inputs": {k: inputs[k] for k in ("usgs_fibre_model", "germanium_use_shares", "germanium_supply", "germanium_market", "world_fibre",
                                         "submarine_suppliers_2020_2024", "vessels_2025", "scenarios")},
        "results": results,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    ARTICLE.write_text(render(inputs, results), encoding="utf-8", newline="\n")
    print("wrote fibre_chain.json and fibre-optics-chain.html: four suppliers %s of submarine cable length; %s t of germanium in US fibre (2021 model)"
          % (tier, inputs["usgs_fibre_model"]["total_contained_tonnes"]))


if __name__ == "__main__":
    build()
