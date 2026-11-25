"""Build the static aluminium study and its evidence JSON.

Inputs: evidence_inputs.json (source tables transcribed and checked 25 Nov 2026), article.html.in,
out/aluminium_tonnage.json (trade by weight, written by extract_tonnage.py) and out/aluminium_trade.json
(trade by value, written by extract_baci.py). No network access. Run from the repository root:
    python aluminium-chain/record_aluminium.py
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from string import Template

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "evidence_inputs.json"
TEMPLATE = HERE / "article.html.in"
TONNAGE = HERE / "out" / "aluminium_tonnage.json"
TRADE = HERE / "out" / "aluminium_trade.json"
FLOWS = HERE / "out" / "aluminium_flows.json"
OUT = HERE / "out" / "aluminium_chain.json"
ARTICLE = HERE / "aluminium-chain.html"

TITLE = "Aluminium production is concentrated in China, and bauxite trade in Guinea"
DECK = ("China made 60% of the world's alumina and primary aluminium in 2024 and exported little of either. "
        "Guinea supplied 67% of traded bauxite, and nine-tenths of it went to China.")
STAGES = ("bauxite", "alumina", "aluminium")
TRADE_KEY = {"bauxite": "bauxite", "alumina": "alumina", "aluminium": "unwrought"}
STAGE_LABEL = {"bauxite": "Bauxite", "alumina": "Alumina", "aluminium": "Aluminium (primary metal; trade is unwrought metal)"}
TABLE_COUNTRIES = ("China", "Guinea", "Australia", "Brazil", "India", "Russia", "Canada", "United Arab Emirates", "Indonesia")
SERIES_YEARS = (2005, 2010, 2015, 2020, 2022, 2024)
DEFECT_YEAR = 2023

NUMBER_WORDS = {5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
RATIO_BAND = 0.10          # a row "fits" when its alumina per tonne of metal is within a tenth of the survey ratio
CHEMICAL_MINIMUM = 101.96 / 53.96   # tonnes of alumina (Al2O3) that contain one tonne of aluminium, from atomic weights
EXTRA_SMELTERS = ("South Africa", "Mozambique", "New Zealand", "Qatar", "Argentina", "Oman")
NAVY, TEAL, AMBER, GREY, INK, MUT, RULE = "#15323a", "#0e7c74", "#b7791f", "#aab5ba", "#1a1f24", "#667179", "#e6e9e8"
FONT = "font-family:Inter,system-ui,Segoe UI,Arial,sans-serif"


def the(name):
    return "the " + name if name.startswith("United") else name


def listing(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _bar(x, y, w, h, fill, tip, r=3):
    """A horizontal bar with a square start on the baseline and a rounded data end."""
    w = max(w, 1.0)
    r = min(r, w / 2, h / 2)
    d = f"M{x:.1f} {y:.1f}h{w - r:.1f}a{r} {r} 0 0 1 {r} {r}v{h - 2 * r:.1f}a{r} {r} 0 0 1 -{r} {r}h-{w - r:.1f}z"
    return f'<path d="{d}" fill="{fill}"><title>{escape(tip)}</title></path>'


def chart_concentration(prod, trade):
    """Production and export concentration at each stage: two bars per stage, values printed at the bar ends."""
    left, plot, bar, top, step = 84, 300, 16, 40, 56
    scale = plot / 6000
    out = [f'<svg viewBox="0 0 520 {top + 3 * step + 22}" role="img" aria-label="Concentration of production and of exports at each stage, 2024" style="{FONT};font-size:12.5px">',
           f'<rect x="{left}" y="8" width="12" height="12" fill="{NAVY}"/><text x="{left + 18}" y="18" fill="{INK}">Production</text>',
           f'<rect x="{left + 104}" y="8" width="12" height="12" fill="{TEAL}"/><text x="{left + 122}" y="18" fill="{INK}">Exports, by weight</text>']
    for tick in (0, 2000, 4000, 6000):
        x = left + tick * scale
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top - 8}" y2="{top + 3 * step - 14}" stroke="{RULE}"/>'
                   f'<text x="{x:.1f}" y="{top + 3 * step + 4}" fill="{MUT}" text-anchor="middle" font-size="11">{tick:,}</text>')
    for i, s in enumerate(STAGES):
        y = top + i * step
        name = STAGE_LABEL[s].split(" (")[0]
        mid = sum(prod[s]["hhi"]) / 2
        low, high = prod[s]["hhi"]
        out.append(f'<text x="{left - 8}" y="{y + bar + 5}" fill="{INK}" text-anchor="end">{name}</text>')
        out.append(_bar(left, y, mid * scale, bar, NAVY, f"{name}, production: {low:,} to {high:,}"))
        out.append(f'<text x="{left + mid * scale + 6:.1f}" y="{y + 12}" fill="{INK}">{low:,} to {high:,}</text>')
        ex = trade[s]["export_hhi"]
        out.append(_bar(left, y + bar + 2, ex * scale, bar, TEAL, f"{name}, exports: {ex:,}"))
        out.append(f'<text x="{left + ex * scale + 6:.1f}" y="{y + bar + 14}" fill="{INK}">{ex:,}</text>')
    out.append("</svg>")
    return "".join(out)


def chart_stages(markets):
    """Concentration of origins at each stage, for the metal each market uses: three bars per market."""
    keys = (("smelted_in", "Where the metal was smelted", NAVY), ("alumina_refined_in", "Where its alumina was refined", TEAL),
            ("bauxite_mined_in", "Where the bauxite was mined", AMBER))
    left, plot, bar, top, step = 112, 320, 11, 48, 50
    scale = plot / 10000
    out = [f'<svg viewBox="0 0 520 {top + len(markets) * step + 18}" role="img" aria-label="Concentration of origins at three stages, by market, 2022" style="{FONT};font-size:12.5px">']
    for i, (_, label, fill) in enumerate(keys):
        out.append(f'<rect x="4" y="{4 + i * 14}" width="11" height="11" fill="{fill}"/><text x="21" y="{13.5 + i * 14}" fill="{INK}">{label}</text>')
    for tick in (0, 2500, 5000, 7500, 10000):
        x = left + tick * scale
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top - 2}" y2="{top + len(markets) * step - 12}" stroke="{RULE}"/>'
                   f'<text x="{x:.1f}" y="{top + len(markets) * step + 4}" fill="{MUT}" text-anchor="middle" font-size="11">{tick:,}</text>')
    for i, (market, m) in enumerate(markets.items()):
        y = top + i * step
        out.append(f'<text x="{left - 8}" y="{y + 22}" fill="{INK}" text-anchor="end">{escape(market)}</text>')
        for k, (key, label, fill) in enumerate(keys):
            v = m[key]["hhi"]
            out.append(_bar(left, y + k * (bar + 2), v * scale, bar, fill, f"{market}: {label.lower()}, index {v:,}"))
            out.append(f'<text x="{left + v * scale + 5:.1f}" y="{y + k * (bar + 2) + 10}" fill="{INK}" font-size="11.5">{v:,}</text>')
    out.append("</svg>")
    return "".join(out)


def chart_origin(rows):
    """Where each smelting country's alumina comes from: one stacked bar per country, shares of home output plus imports."""
    keys = (("home", "Refined at home", NAVY, "#fff"), ("Australia", "From Australia", TEAL, "#fff"),
            ("Brazil", "From Brazil", AMBER, "#fff"), ("other", "Other imports", GREY, INK))
    left, plot, bar, top, step = 132, 372, 17, 34, 25
    rows = sorted(rows, key=lambda r: (-r["origin"]["home"], -r["origin"]["Australia"]))
    out = [f'<svg viewBox="0 0 520 {top + len(rows) * step + 6}" role="img" aria-label="Sources of alumina for the twelve named smelting countries, 2024" style="{FONT};font-size:12.5px">']
    x = 4
    for _, label, fill, _ in keys:
        out.append(f'<rect x="{x}" y="6" width="12" height="12" fill="{fill}"/><text x="{x + 17}" y="16" fill="{INK}">{label}</text>')
        x += 17 + 7.2 * len(label) + 16
    for i, r in enumerate(rows):
        y = top + i * step
        out.append(f'<text x="{left - 8}" y="{y + 13}" fill="{INK}" text-anchor="end">{escape(r["country"])}</text>')
        at = left
        for key, label, fill, ink in keys:
            w = r["origin"][key] * plot
            if w < 0.5:
                continue
            tip = f'{r["country"]}: {label.lower()}, {r["origin"][key]:.0%}'
            out.append(f'<rect x="{at:.1f}" y="{y}" width="{max(w - 2, 0.5):.1f}" height="{bar}" fill="{fill}"><title>{escape(tip)}</title></rect>')
            if w >= 34:
                out.append(f'<text x="{at + (w - 2) / 2:.1f}" y="{y + 13}" fill="{ink}" text-anchor="middle" font-size="11.5">{r["origin"][key]:.0%}</text>')
            at += w
    out.append("</svg>")
    return "".join(out)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pct(x, places=0):
    return f"{100 * x:.{places}f}%"


def mt(kt, places=1):
    return f"{kt / 1000:,.{places}f}"


def row(label, cells, numeric=True):
    cls = ' class="n"' if numeric else ""
    return (f'<tr><th scope="row">{escape(str(label))}</th>'
            + "".join(f"<td{cls}>{escape(str(c))}</td>" for c in cells) + "</tr>")


def evaluate(inputs):
    usgs = inputs["usgs_mcs2026"]
    tonnage = load(TONNAGE)
    series = {k: {r["year"]: r for r in v} for k, v in tonnage["series"].items()}
    latest = tonnage["latest"]
    year = latest["bauxite"]["year"]

    production = {}
    for stage in STAGES:
        table = usgs[stage]
        world = table["World"]["y2024"]
        listed = {k: v["y2024"] for k, v in table.items() if k != "World"}
        if abs(sum(listed.values()) - world) > 0.005 * world:
            raise SystemExit(f"{stage}: the country rows do not add to the published world total")
        named = {k: v / world for k, v in listed.items() if k != "Other countries"}
        other = listed["Other countries"] / world
        base = sum((100 * s) ** 2 for s in named.values())
        leader = max(named, key=named.get)
        production[stage] = {"world_kt": world, "shares": {**named, "Other countries": other}, "leader": leader,
                             "leader_share": named[leader], "hhi": [round(base), round(base + (100 * other) ** 2)]}

    trade = {}
    for stage in STAGES:
        key = TRADE_KEY[stage]
        rec, top = series[key][year], latest[key]
        world_t = rec["world_tonnes"]
        trade[stage] = {
            "world_kt": world_t / 1000, "traded_over_produced": world_t / 1000 / production[stage]["world_kt"],
            "leading_exporter": top["exporters"][0]["name"], "leading_exporter_share": top["exporters"][0]["share"],
            "leading_importer": top["importers"][0]["name"], "leading_importer_share": top["importers"][0]["share"],
            "export_hhi": rec["export_hhi"], "import_hhi": rec["import_hhi"],
            "exporters": top["exporters"], "importers": top["importers"],
            "china_export_share": rec["china_exports"] / world_t, "china_import_share": rec["china_imports"] / world_t,
            "china_exports_over_own_output": rec["china_exports"] / 1000 / usgs[stage]["China"]["y2024"],
        }
    semis_rec, semis_top = series["semis"][year], latest["semis"]
    semis = {"world_kt": semis_rec["world_tonnes"] / 1000, "export_hhi": semis_rec["export_hhi"],
             "china_exports_kt": semis_rec["china_exports"] / 1000,
             "china_export_share": semis_rec["china_exports"] / semis_rec["world_tonnes"],
             "china_import_share": semis_rec["china_imports"] / semis_rec["world_tonnes"],
             "china_exports_over_primary_output": semis_rec["china_exports"] / 1000 / usgs["aluminium"]["China"]["y2024"],
             "leading_importer": semis_top["importers"][0]["name"], "leading_importer_share": semis_top["importers"][0]["share"]}

    b = series["bauxite"][year]
    china_domestic = usgs["bauxite"]["China"]["y2024"]
    china_supply = china_domestic + b["china_imports"] / 1000
    china_bauxite = {
        "domestic_kt": china_domestic, "imports_kt": b["china_imports"] / 1000, "supply_kt": china_supply,
        "import_share_of_supply": b["china_imports"] / 1000 / china_supply,
        "guinea_kt": b["guinea_to_china"] / 1000, "guinea_share_of_supply": b["guinea_to_china"] / 1000 / china_supply,
        "guinea_share_of_china_imports": b["guinea_to_china"] / b["china_imports"],
        "china_share_of_guinea_exports": b["guinea_to_china"] / b["guinea_exports"],
        "guinea_exports_over_guinea_output": b["guinea_exports"] / 1000 / usgs["bauxite"]["Guinea"]["y2024"],
    }

    bx_series = []
    for y in SERIES_YEARS:
        r, a = series["bauxite"][y], series["alumina"][y]
        bx_series.append({"year": y, "world_kt": r["world_tonnes"] / 1000, "guinea_kt": r["guinea_exports"] / 1000,
                          "guinea_share": r["guinea_exports"] / r["world_tonnes"], "china_imports_kt": r["china_imports"] / 1000,
                          "china_import_share": r["china_imports"] / r["world_tonnes"],
                          "indonesia_bauxite_kt": r["indonesia_exports"] / 1000, "indonesia_alumina_kt": a["indonesia_exports"] / 1000})

    world_bx, world_al2o3, world_al = (usgs[s]["World"]["y2024"] for s in STAGES)
    cn = {s: series[TRADE_KEY[s]][year] for s in STAGES}
    china_alumina_available = usgs["alumina"]["China"]["y2024"] + (cn["alumina"]["china_imports"] - cn["alumina"]["china_exports"]) / 1000
    china_bauxite_available = china_supply - cn["bauxite"]["china_exports"] / 1000
    iai = inputs["iai"]
    ratios = {
        "bauxite_per_alumina_world": world_bx / world_al2o3,
        "bauxite_per_alumina_china": china_bauxite_available / usgs["alumina"]["China"]["y2024"],
        "alumina_per_aluminium_world_usgs": world_al2o3 / world_al,
        "alumina_per_aluminium_world_iai": iai["alumina_kt"]["2024"]["metallurgical_world"] / iai["primary_aluminium_kt"]["2024"]["World"],
        "alumina_per_aluminium_china": china_alumina_available / usgs["aluminium"]["China"]["y2024"],
        "bauxite_at_usgs_rule_kt": usgs["rule_of_thumb"]["bauxite_per_alumina"] * world_al2o3,
    }
    ratios["bauxite_above_usgs_rule"] = world_bx / ratios["bauxite_at_usgs_rule_kt"] - 1

    screen = []
    for f in inputs["scenarios"]["guinea_to_china_cut_fractions"]:
        lost = f * china_bauxite["guinea_kt"]
        alumina = lost / ratios["bauxite_per_alumina_china"]
        metal = alumina / iai["lci_2019"]["alumina_per_aluminium"]
        screen.append({"fraction": f, "bauxite_kt": lost, "share_of_china_bauxite": lost / china_supply,
                       "alumina_kt": alumina, "share_of_world_alumina": alumina / world_al2o3,
                       "aluminium_kt": metal, "share_of_world_aluminium": metal / world_al})

    power = iai["smelting_power_gwh_2025"]
    for region, mix in power.items():
        if abs(sum(v for k, v in mix.items() if k != "Total") - mix["Total"]) > 5:      # published rows are rounded
            raise SystemExit(f"{region}: the power sources do not add to the published total")
    energy = {
        "mix": {region: {k: v / mix["Total"] for k, v in mix.items() if k != "Total"} for region, mix in power.items()},
        "china_share_of_smelting_power": power["China"]["Total"] / power["World"]["Total"],
        "china_share_of_coal_power": power["China"]["Coal"] / power["World"]["Coal"],
        "coverage": iai["smelting_power_coverage_2025_mt"]["reported"] / iai["smelting_power_coverage_2025_mt"]["world"],
        "world_twh": power["World"]["Total"] / 1000,
    }
    al = usgs["aluminium"]
    utilisation = {k: al[k]["y2024"] / al[k]["capacity_2024"] for k in ("China", "World", "United States", "Other countries")}

    survey = iai["lci_2019"]["alumina_per_aluminium"]
    partners = tonnage["partners"]
    now, then = partners[str(year)]["alumina"], partners["2019"]["alumina"]
    smelters = []
    for country, v in al.items():
        if country in ("World", "Other countries"):
            continue
        home = usgs["alumina"].get(country, {}).get("y2024")
        rec, old = now[country], then[country]
        imports, exports = rec["imports"] / 1000, rec["exports"] / 1000
        gross = (home or 0) + imports
        by = {s["name"]: s["tonnes"] / 1000 for s in rec["suppliers"]}
        origin = {"home": (home or 0) / gross, "Australia": by.get("Australia", 0) / gross, "Brazil": by.get("Brazil", 0) / gross}
        origin["other"] = 1 - sum(origin.values())
        smelters.append({
            "country": country, "metal_kt": v["y2024"], "home_alumina_kt": home, "imports_kt": imports, "exports_kt": exports,
            "available_per_tonne": (gross - exports) / v["y2024"], "import_share": imports / gross, "origin": origin,
            "suppliers": [(s["name"], s["share"]) for s in rec["suppliers"]],
            "suppliers_2019": [(s["name"], s["share"]) for s in old["suppliers"]]})
    outside = [s for s in smelters if s["country"] != "China"]
    major = [s for s in outside if s["import_share"] > 0.5]
    outside_china_kt = al["World"]["y2024"] - al["China"]["y2024"]
    alumina_supply = {
        "rows": smelters, "survey_ratio": survey,
        "import_majority": [s["country"] for s in major], "import_majority_metal_kt": sum(s["metal_kt"] for s in major),
        "import_majority_share_of_output_outside_china": sum(s["metal_kt"] for s in major) / outside_china_kt,
        "no_alumina_output_listed": [s["country"] for s in outside if s["home_alumina_kt"] is None],
        "single_supplier": [(s["country"], s["suppliers"][0][0], s["suppliers"][0][1]) for s in major if s["suppliers"][0][1] >= 0.7],
        "ratio_out_of_line": sorted(s["country"] for s in smelters if abs(s["available_per_tonne"] / survey - 1) > RATIO_BAND),
        "below_chemical_minimum": [(s["country"], s["available_per_tonne"]) for s in smelters if s["available_per_tonne"] < CHEMICAL_MINIMUM],
        "chemical_minimum": CHEMICAL_MINIMUM,
        "australia_share_of_imports": {c: next((x["share"] for x in now[c]["suppliers"] if x["name"] == "Australia"), 0.0) for c in EXTRA_SMELTERS},
    }
    emirates = {"guinea_to_emirates_mt": {str(y): series["bauxite"][y]["guinea_to_emirates"] / 1e6 for y in (2022, 2023, year)},
                "bauxite_imports_mt": partners[str(year)]["bauxite"]["United Arab Emirates"]["imports"] / 1e6,
                "bauxite_needed_at_usgs_rule_mt": usgs["rule_of_thumb"]["bauxite_per_alumina"] * usgs["alumina"]["United Arab Emirates"]["y2024"] / 1000}

    ev, p17, p18 = inputs["brazil_2018"], partners["2017"]["alumina"], partners["2018"]["alumina"]

    def brazil(block, country):
        return next((x["tonnes"] for x in block[country]["suppliers"] if x["name"] == "Brazil"), 0) / 1e6

    def importer(country):
        a, b_, c, d = p17[country]["imports"] / 1e6, p18[country]["imports"] / 1e6, brazil(p17, country), brazil(p18, country)
        return {"imports_2017_mt": a, "imports_2018_mt": b_, "from_brazil_2017_mt": c, "from_brazil_2018_mt": d,
                "from_others_2017_mt": a - c, "from_others_2018_mt": b_ - d}

    bx_al = ev["usgs_alumina_kt"]
    interruption = {"brazil_exports_mt": {str(y): series["alumina"][y]["brazil_exports"] / 1e6 for y in (2017, 2018, 2019, 2020)},
                    "output_fall_kt": bx_al["brazil_2017"] - bx_al["brazil_2018"],
                    "output_fall_share_of_world": (bx_al["brazil_2017"] - bx_al["brazil_2018"]) / bx_al["world_2017"],
                    "norway": importer("Norway"), "canada": importer("Canada"),
                    "brazil_metal_fall": 1 - ev["usgs_primary_aluminium_kt"]["brazil_2018"] / ev["usgs_primary_aluminium_kt"]["brazil_2017"]}
    interruption["export_fall_share"] = 1 - interruption["brazil_exports_mt"]["2018"] / interruption["brazil_exports_mt"]["2017"]

    st, gr = inputs["stocks"], inputs["grades"]
    stocks = {
        "china_bauxite_ports_months_of_2024_imports": st["china_bauxite_ports"]["mt"] / (b["china_imports"] / 1e6) * 12,
        "china_bauxite_ports_over_quarter_cut": st["china_bauxite_ports"]["mt"] * 1000 / screen[0]["bauxite_kt"],
        "china_alumina_days_of_2024_output": st["china_alumina_total"]["mt"] * 1000 / usgs["alumina"]["China"]["y2024"] * 365,
        "exchange_aluminium_t": st["shfe_aluminium"]["t"] + st["lme_aluminium"]["t"],
        "exchange_aluminium_days_of_2024_world_output": (st["shfe_aluminium"]["t"] + st["lme_aluminium"]["t"]) / 1000 / al["World"]["y2024"] * 365,
    }
    available = [g for g in gr["rows"] if g["basis"] == "available" and g["source"] == "alcoa_10k_2025"]   # one company, one basis
    grades = {"lowest": min(gr["rows"], key=lambda g: g["al2o3_pct"]), "highest": max(gr["rows"], key=lambda g: g["al2o3_pct"]),
              "available_low": min(available, key=lambda g: g["al2o3_pct"]), "available_high": max(available, key=lambda g: g["al2o3_pct"])}
    grades["available_low_over_high"] = grades["available_low"]["al2o3_pct"] / grades["available_high"]["al2o3_pct"]
    gq = gr["guinea_exports_q1_2025"]
    if abs(sum(gq["moisture_pct"].values()) / len(gq["moisture_pct"]) - gq["moisture_average_printed_pct"]) > 0.02:
        raise SystemExit("the Guinean moisture rows do not reproduce the printed average")
    grades["guinea_exports"] = {"alumina_low": min(gq["alumina_pct"].values()), "alumina_high": max(gq["alumina_pct"].values()),
                                "companies_with_alumina": len(gq["alumina_pct"]), "moisture_low": min(gq["moisture_pct"].values()),
                                "moisture_high": max(gq["moisture_pct"].values()), "moisture_average": gq["moisture_average_printed_pct"],
                                "usgs_wet_dry_gap": 1 - inputs["guinea"]["usgs_yearbook_2024_dry_tonnes"] / 1000 / inputs["guinea"]["usgs_yearbook_2024_wet_kt"]}
    gq1 = st["guinea_exports_q1_t"]
    stocks["guinea_q1_2025_exports_mt"] = gq1["2025"] / 1e6
    stocks["guinea_q1_2024_exports_mt"] = gq1["2024"] / 1e6
    china_room = {"ceiling_mt": inputs["restarts"]["china_ceiling_mt"], "capacity_2025_kt": al["China"]["capacity_2025"], "output_2025_kt": al["China"]["y2025"]}
    capacity = [{"country": k, "output_kt": v["y2024"], "capacity_kt": v["capacity_2024"],
                 "unused_kt": max(v["capacity_2024"] - v["y2024"], 0), "use": v["y2024"] / v["capacity_2024"]} for k, v in al.items()]
    unused = {c["country"]: c["unused_kt"] for c in capacity}
    spare = {"rows": capacity, "world_kt": unused["World"], "china_kt": unused["China"], "outside_china_kt": unused["World"] - unused["China"],
             "outside_china_share_of_output": (unused["World"] - unused["China"]) / outside_china_kt,
             "unnamed_countries_kt": unused["Other countries"], "united_states_kt": unused["United States"]}

    old = inputs["usgs_mcs2025_estimates_for_2024"]["bauxite"]
    revision = {"guinea_share_2025_edition": old["Guinea"] / old["World"],
                "guinea_share_2026_edition": production["bauxite"]["shares"]["Guinea"],
                "china_share_usgs": production["aluminium"]["shares"]["China"],
                "china_share_iai": iai["primary_aluminium_kt"]["2024"]["China"] / iai["primary_aluminium_kt"]["2024"]["World"],
                "china_share_iai_2025": iai["primary_aluminium_kt"]["2025"]["China"] / iai["primary_aluminium_kt"]["2025"]["World"]}
    cyc = iai["cycle_model_2024_kt"]
    recycled_share = cyc["recycled"] / (cyc["primary"] + cyc["recycled"])
    customs = inputs["smm_china_imports_2024"]
    cross = {"baci_china_imports_mt": b["china_imports"] / 1e6, "customs_china_imports_mt": customs["imports_mt"],
             "baci_guinea_to_china_mt": b["guinea_to_china"] / 1e6, "customs_guinea_to_china_mt": customs["from_guinea_mt"],
             "baci_guinea_exports_mt": b["guinea_exports"] / 1e6, "ins_guinea_exports_mt": inputs["guinea"]["ins_exports_mt"]["2024"],
             "guinea_ins_minus_baci_mt": {y: round(v - series["bauxite"][int(y)]["guinea_exports"] / 1e6, 1)
                                          for y, v in inputs["guinea"]["ins_exports_mt"].items()}}
    defect = {"year": DEFECT_YEAR, "guinea_share": series["bauxite"][DEFECT_YEAR]["guinea_exports"] / series["bauxite"][DEFECT_YEAR]["world_tonnes"],
              "world_mt": series["bauxite"][DEFECT_YEAR]["world_tonnes"] / 1e6}

    # The page states these in words. Stop if the numbers no longer support the sentences.
    checks = [
        (0.59 < production["alumina"]["shares"]["China"] < 0.615 and 0.59 < production["aluminium"]["shares"]["China"] < 0.615,
         "China's share of alumina or aluminium is no longer 60%"),
        (0.665 <= trade["bauxite"]["leading_exporter_share"] < 0.675 and trade["bauxite"]["leading_exporter"] == "Guinea",
         "Guinea's share of traded bauxite is no longer 67%"),
        (china_bauxite["china_share_of_guinea_exports"] > 0.85, "less than nine-tenths of Guinea's bauxite goes to China"),
        (trade["alumina"]["china_export_share"] < 0.1 and trade["aluminium"]["china_export_share"] < 0.02,
         "China's export shares of alumina or unwrought aluminium are no longer small"),
        (0.6 < china_bauxite["import_share_of_supply"] < 0.7, "imports are no longer about two-thirds of China's bauxite supply"),
        (1.85 < ratios["alumina_per_aluminium_world_iai"] < 2.0 and 1.85 < ratios["alumina_per_aluminium_china"] < 2.0,
         "the alumina-to-aluminium ratios no longer sit near the reference values"),
        (ratios["bauxite_per_alumina_world"] > 2.8, "the bauxite-to-alumina ratio is no longer well above the USGS rule"),
        (defect["guinea_share"] > 0.75, "the 2023 bauxite record has changed: review the note on that year"),
        (abs(cross["baci_china_imports_mt"] - cross["customs_china_imports_mt"]) < 2, "BACI and the trade publication no longer agree on 2024 imports"),
        (series["bauxite"][year]["indonesia_exports"] < 1000, "Indonesia exported bauxite in the latest year"),
        (series["alumina"][year]["indonesia_exports"] / 1000 > 3 * usgs["alumina"]["Indonesia"]["y2024"],
         "Indonesian alumina exports are no longer more than three times the USGS output estimate"),
        (cross["guinea_ins_minus_baci_mt"]["2022"] < 0 and cross["guinea_ins_minus_baci_mt"]["2023"] < 0
         and cross["guinea_ins_minus_baci_mt"]["2024"] > 0, "the gap between the two Guinea export figures no longer changes sign"),
        (latest["unwrought"]["importers"][1]["name"] == "China", "China is no longer the second-largest importer of unwrought aluminium"),
        (max(v for k, v in production["alumina"]["shares"].items() if k not in ("China", "Other countries")) < 0.13
         and max(v for k, v in production["aluminium"]["shares"].items() if k not in ("China", "Other countries")) < 0.06,
         "another country now reaches 13% of alumina or 6% of primary aluminium"),
        (len(major) in NUMBER_WORDS and len(outside) == 11, "the count of import-dependent smelting countries has no word, or the list is no longer eleven"),
        ([n for n, _ in next(s for s in smelters if s["country"] == "Russia")["suppliers_2019"][:2]] == ["Ukraine", "Australia"]
         and not {"Ukraine", "Australia"} & {n for n, _ in next(s for s in smelters if s["country"] == "Russia")["suppliers"]}
         and [n for n, _ in next(s for s in smelters if s["country"] == "Russia")["suppliers"][:2]] == ["China", "Indonesia"],
         "Russia's alumina suppliers no longer read as the page states"),
        (all(next(s for s in smelters if s["country"] == c)["suppliers_2019"][0][0] == "Australia"
             and next(s for s in smelters if s["country"] == c)["suppliers"][0][0] == "Indonesia" for c in ("India", "Malaysia")),
         "India's or Malaysia's largest alumina supplier no longer changed from Australia to Indonesia"),
        (alumina_supply["ratio_out_of_line"] == ["Brazil", "Iceland", "United States"], "the list of rows that do not fit the survey ratio has changed"),
        (("Bahrain", "Australia") in [(a, b_) for a, b_, _ in alumina_supply["single_supplier"]]
         and ("Norway", "Brazil") in [(a, b_) for a, b_, _ in alumina_supply["single_supplier"]],
         "Bahrain or Norway no longer takes at least 70% of its alumina imports from one country"),
        (emirates["guinea_to_emirates_mt"][str(year)] == 0 and emirates["guinea_to_emirates_mt"]["2023"] > 5
         and emirates["bauxite_imports_mt"] < 0.2 * emirates["bauxite_needed_at_usgs_rule_mt"],
         "the bauxite record for the United Arab Emirates has changed: review the note on it"),
        (abs(interruption["norway"]["imports_2018_mt"] / interruption["norway"]["imports_2017_mt"] - 1) < 0.03
         and interruption["norway"]["from_brazil_2017_mt"] - interruption["norway"]["from_brazil_2018_mt"] > 0.3
         and interruption["brazil_exports_mt"]["2020"] > 0.9 * interruption["brazil_exports_mt"]["2017"],
         "the 2018 Brazilian interruption no longer reads as the page states"),
        (spare["unnamed_countries_kt"] > 0.5 * spare["outside_china_kt"], "most unused capacity outside China is no longer in the unnamed countries"),
        (0.8 < stocks["china_bauxite_ports_over_quarter_cut"] < 1.5 and screen[0]["fraction"] == 0.25,
         "Chinese port stocks of bauxite are no longer of the same order as the ore removed in the first row of the screen"),
        ([c for c, _ in alumina_supply["below_chemical_minimum"]] == ["Bahrain", "Malaysia"], "the rows below the chemical minimum have changed"),
        (grades["available_low"]["deposit"] == "Darling Range" and grades["available_high"]["deposit"] == "Juruti", "the two grades compared are no longer the same pair"),
        (abs(china_room["capacity_2025_kt"] / 1000 - china_room["ceiling_mt"]) < 0.5 and china_room["output_2025_kt"] >= 0.98 * china_room["capacity_2025_kt"],
         "China's capacity or output is no longer at the reported ceiling"),
        (grades["available_low"]["country"] == "Australia" and grades["available_high"]["country"] == "Brazil" and 0.5 < grades["available_low_over_high"] < 0.7,
         "the ore grades no longer read as the page states"),
    ]
    for ok, message in checks:
        if not ok:
            raise SystemExit("aluminium page text no longer matches the data: " + message)

    flows = load(FLOWS)
    fm = flows["markets"]
    us, eu, cn = fm["United States"], fm["European Union"], fm["China"]
    rising = [m for m, v in fm.items() if v["bauxite_mined_in"]["hhi"] > v["smelted_in"]["hhi"]]
    alt = flows["sensitivity"]["unalloyed_metal_only"]["markets"]
    rising_alt = [m for m, v in alt.items() if v["index_mining"] > v["index_smelting"]]
    flow_checks = [
        (rising == ["United States", "European Union", "Japan", "South Korea"] and rising_alt == ["United States", "European Union", "Japan"],
         "the markets whose concentration rises upstream, with and without traded alloy, have changed"),
        (fm["India"]["smelted_in"]["hhi"] > fm["India"]["bauxite_mined_in"]["hhi"], "India no longer runs the same way as China"),
        (fm["China"]["customs_share_of"]["Guinea"] < 0.001 and all(v["customs_share_of"]["Guinea"] == 0 for m, v in fm.items() if m != "China"),
         "Guinea's place in metal imports has changed"),
        (us["smelted_in"]["top_foreign"][0]["name"] == "Canada" and us["bauxite_mined_in"]["top_foreign"][0]["name"] == "Brazil"
         and us["customs_share_of"]["Brazil"] < 0.02, "the United States reading of the flow model has changed"),
        (eu["bauxite_mined_in"]["top_foreign"][0]["name"] == "Australia" and eu["customs_share_of"]["Australia"] < 0.02
         and eu["smelted_in"]["top_foreign"][0]["name"] == "Norway" and eu["smelted_in"]["top_foreign"][0]["share"] < eu["smelted_in"]["home"] < 0.2,
         "the EU reading of the flow model has changed"),
        (all(v["customs_share_of"]["Guinea"] < 0.001 for v in fm.values()), "Guinea now appears in a market's metal imports"),
        (cn["smelted_in"]["hhi"] > 9000 and cn["bauxite_mined_in"]["hhi"] < 3000, "the China reading of the flow model has changed"),
        (flows["stages"]["alumina"]["largest_gap_country"] == "Indonesia", "the largest inconsistency in the flow model is no longer Indonesian alumina"),
    ]
    for ok, message in flow_checks:
        if not ok:
            raise SystemExit("aluminium page text no longer matches the flow model: " + message)
    return {"trade_year": year, "production_2024": production, "trade_2024": trade, "semis_2024": semis, "china_bauxite_2024": china_bauxite,
            "bauxite_series": bx_series, "ratios_2024": ratios, "guinea_screen": screen, "energy_2025": energy,
            "capacity_utilisation_2024": utilisation, "revisions": revision, "recycled_share_of_metal_2024": recycled_share,
            "cross_checks_2024": cross, "bauxite_2023_record": defect, "alumina_supply": alumina_supply, "emirates_bauxite": emirates,
            "brazil_2018": interruption, "unused_capacity_2024": spare, "stocks": stocks, "ore_grades": grades, "china_capacity_limit": china_room}


def link(sources, key, label=None):
    s = sources[key]
    return f'<a href="{escape(s["url"], quote=True)}">{escape(label or s["title"])}</a>.'


def render(inputs, r):
    src = inputs["sources"]
    usgs = inputs["usgs_mcs2026"]
    prod, trade, semis, cb = r["production_2024"], r["trade_2024"], r["semis_2024"], r["china_bauxite_2024"]
    ratios, energy, iai = r["ratios_2024"], r["energy_2025"], inputs["iai"]

    def cell(stage, country):
        v = usgs[stage].get(country)
        return (mt(v["y2024"]), pct(v["y2024"] / usgs[stage]["World"]["y2024"], 1)) if v else ("—", "")

    prod_rows = [row(c, [x for s in STAGES for x in cell(s, c)]) for c in TABLE_COUNTRIES]
    rest = []
    for s in STAGES:
        world = usgs[s]["World"]["y2024"]
        left = world - sum(usgs[s][c]["y2024"] for c in TABLE_COUNTRIES if c in usgs[s])
        rest += [mt(left), pct(left / world, 1)]
    prod_rows.append(row("All other countries", rest))
    prod_rows.append(row("World", [x for s in STAGES for x in (mt(usgs[s]["World"]["y2024"]), "")]))

    stage_rows = []
    for s in STAGES:
        p, t = prod[s], trade[s]
        stage_rows.append(row(STAGE_LABEL[s], [
            mt(p["world_kt"]), f'{p["leader"]} {pct(p["leader_share"])}', "{:,} to {:,}".format(*p["hhi"]),
            mt(t["world_kt"]), pct(t["traded_over_produced"]), f'{t["leading_exporter"]} {pct(t["leading_exporter_share"])}',
            f'{t["export_hhi"]:,}', f'{t["leading_importer"]} {pct(t["leading_importer_share"])}']))
    stage_rows.append(row("Semi-finished aluminium (bars, wire, plate, foil, tubes)", [
        "not published", "", "", mt(semis["world_kt"]), "", f'China {pct(semis["china_export_share"])}',
        f'{semis["export_hhi"]:,}', f'{semis["leading_importer"]} {pct(semis["leading_importer_share"])}']))

    china_rows = [row(STAGE_LABEL[s].split(" (")[0], [pct(prod[s]["shares"]["China"], 1), pct(trade[s]["china_export_share"], 1),
                                                    pct(trade[s]["china_import_share"], 1), pct(trade[s]["china_exports_over_own_output"], 1)])
                  for s in STAGES]
    china_rows.append(row("Semi-finished aluminium", ["not published", pct(semis["china_export_share"], 1),
                                                     pct(semis["china_import_share"], 1), ""]))

    series_rows = [row(x["year"], [mt(x["world_kt"]), mt(x["guinea_kt"]), pct(x["guinea_share"]), mt(x["china_imports_kt"]),
                                   pct(x["china_import_share"]), mt(x["indonesia_bauxite_kt"]), mt(x["indonesia_alumina_kt"])])
                   for x in r["bauxite_series"]]
    first, last = r["bauxite_series"][0], r["bauxite_series"][-1]

    words = {0.25: "A quarter", 0.5: "Half"}
    screen_rows = [row(f'{words[x["fraction"]]} of Guinea’s shipments to China', [
        mt(x["bauxite_kt"]), pct(x["share_of_china_bauxite"]), mt(x["alumina_kt"]), pct(x["share_of_world_alumina"]),
        mt(x["aluminium_kt"]), pct(x["share_of_world_aluminium"])]) for x in r["guinea_screen"]]
    half = next(x for x in r["guinea_screen"] if x["fraction"] == 0.5)

    lci, rule, oecd = iai["lci_2019"], usgs["rule_of_thumb"], inputs["oecd2019"]
    ratio_rows = [
        row("Bauxite per tonne of alumina, world", [f'{ratios["bauxite_per_alumina_world"]:.2f}',
            f'USGS rule {rule["bauxite_per_alumina"]:.0f}; industry survey {lci["bauxite_per_alumina_wet"]:.2f} including moisture; OECD {oecd["bauxite_per_alumina_range"][0]} to {oecd["bauxite_per_alumina_range"][1]}'], numeric=False),
        row("Bauxite per tonne of alumina, China", [f'{ratios["bauxite_per_alumina_china"]:.2f}', "Domestic output plus imports less exports, over alumina output"], numeric=False),
        row("Alumina per tonne of aluminium, world", [f'{ratios["alumina_per_aluminium_world_iai"]:.2f}',
            f'USGS rule {rule["alumina_per_aluminium"]:.0f}; industry survey {lci["alumina_per_aluminium"]:.2f}'], numeric=False),
        row("Alumina per tonne of aluminium, China", [f'{ratios["alumina_per_aluminium_china"]:.2f}', "Output plus imports less exports, over primary metal output"], numeric=False),
    ]

    intensity = iai["smelting_energy_kwh_per_tonne_ac_2025"]
    energy_rows = [row(k, [f"{v:,}"]) for k, v in sorted(intensity.items(), key=lambda kv: kv[1])]
    mix_rows = [row(k, [pct(energy["mix"]["World"][k], 1), pct(energy["mix"]["China"][k], 1)])
                for k in ("Coal", "Hydro", "Natural gas", "Other renewable", "Nuclear")]

    tr = load(TRADE)
    tyear = tr["years"][-1]
    trade_rows = []
    for code, info in tr["codes"].items():
        item = tr["years_data"][str(tyear)][code]
        top = next(iter(item["exporters"]), None)
        lead = f'{top["name"]} · {top["share"]:.0%}' if top else "not available"
        cells = (f'{info["title"]} ({code})', f'USD {item["world_usd"] / 1e9:,.1f} billion', lead, inputs["trade_boundaries"][code])
        trade_rows.append(f'<tr data-trade-code="{escape(code)}">' + "".join(f"<td>{escape(c)}</td>" for c in cells) + "</tr>")

    old = inputs["usgs_mcs2025_estimates_for_2024"]["bauxite"]
    bx = usgs["bauxite"]
    util = r["capacity_utilisation_2024"]
    rev, cross, defect = r["revisions"], r["cross_checks_2024"], r["bauxite_2023_record"]
    chk = inputs["trade_checks"]["australia_to_china"]
    g, indo = inputs["guinea"], inputs["indonesia"]
    ex = {s: {e["name"]: e["share"] for e in trade[s]["exporters"]} for s in STAGES}
    al_t = usgs["aluminium"]

    supply, emi, cut, spare = r["alumina_supply"], r["emirates_bauxite"], r["brazil_2018"], r["unused_capacity_2024"]
    ev = inputs["brazil_2018"]

    def lead(pairs, share):
        return f"{pairs[0][0]} {pct(pairs[0][1])}" if share >= 0.1 else "—"

    smelter_rows = [row(s["country"], [
        f'{s["metal_kt"] / 1000:.2f}', "not listed" if s["home_alumina_kt"] is None else f'{s["home_alumina_kt"] / 1000:.2f}',
        f'{s["imports_kt"] / 1000:.2f}', f'{s["exports_kt"] / 1000:.2f}', f'{s["available_per_tonne"]:.2f}', pct(s["import_share"]),
        lead(s["suppliers"], s["import_share"]), lead(s["suppliers_2019"], s["import_share"])]) for s in supply["rows"]]
    russia = next(s for s in supply["rows"] if s["country"] == "Russia")
    united_states = next(s for s in supply["rows"] if s["country"] == "United States")
    extra = sorted(supply["australia_share_of_imports"].items(), key=lambda kv: -kv[1])
    capacity_rows = [row({"Other countries": "Countries not listed by name"}.get(c["country"], c["country"]), [
        f'{c["output_kt"] / 1000:.2f}', f'{c["capacity_kt"] / 1000:.2f}', f'{c["unused_kt"] / 1000:.2f}', pct(c["use"])]) for c in spare["rows"]]
    no, ca, kt = cut["norway"], cut["canada"], ev["usgs_primary_aluminium_kt"]
    more = {
        "chart_hhi": chart_concentration(prod, trade), "chart_origin": chart_origin(supply["rows"]),
        "q_bx_prod": "{:,} to {:,}".format(*prod["bauxite"]["hhi"]), "q_al_prod": "{:,} to {:,}".format(*prod["aluminium"]["hhi"]),
        "q_bx_ex": f'{trade["bauxite"]["export_hhi"]:,}', "q_al_ex": f'{trade["aluminium"]["export_hhi"]:,}',
        "n_major": NUMBER_WORDS[len(supply["import_majority"])], "n_major_cap": NUMBER_WORDS[len(supply["import_majority"])].capitalize(),
        "major_list": listing(the(c) for c in supply["import_majority"]),
        "major_mt": mt(supply["import_majority_metal_kt"]), "major_share": pct(supply["import_majority_share_of_output_outside_china"]),
        "no_home_list": listing(supply["no_alumina_output_listed"]),
        "single_list": listing(f"{the(c)} ({s} {pct(v)})" for c, s, v in supply["single_supplier"]),
        "extra_list": ("at least 99% of the alumina imported by " + listing(the(c) for c, v in extra if v >= 0.99) + ", "
                       + listing(f"{pct(v)} of that imported by {the(c)}" for c, v in extra if v < 0.99)),
        "survey_ratio": f'{supply["survey_ratio"]:.2f}', "smelter_rows": "\n".join(smelter_rows),
        "ru_a": pct(russia["suppliers_2019"][0][1]), "ru_b": pct(russia["suppliers_2019"][1][1]),
        "ru_c": pct(russia["suppliers"][0][1]), "ru_d": pct(russia["suppliers"][1][1]),
        "off_list": listing(the(c) for c in supply["ratio_out_of_line"]), "us_ratio": f'{united_states["available_per_tonne"]:.1f}',
        "us_to_smelters": pct(usgs["us_2025"]["alumina_share_to_smelters"]),
        "ae_bx": f'{emi["bauxite_imports_mt"]:.1f}', "ae_gn_2023": f'{emi["guinea_to_emirates_mt"]["2023"]:.1f}',
        "ae_gn_2022": f'{emi["guinea_to_emirates_mt"]["2022"]:.1f}', "ae_al2o3": mt(usgs["alumina"]["United Arab Emirates"]["y2024"]),
        "ae_need": f'{emi["bauxite_needed_at_usgs_rule_mt"]:.1f}',
        "br_cap": ev["refinery_capacity_mt"], "br_out17": mt(ev["usgs_alumina_kt"]["brazil_2017"]), "br_out18": mt(ev["usgs_alumina_kt"]["brazil_2018"]),
        "br_fall_world": pct(cut["output_fall_share_of_world"]), "br_x17": f'{cut["brazil_exports_mt"]["2017"]:.1f}',
        "br_x18": f'{cut["brazil_exports_mt"]["2018"]:.1f}', "br_x20": f'{cut["brazil_exports_mt"]["2020"]:.1f}', "br_x_fall": pct(cut["export_fall_share"]),
        "no_m17": f'{no["imports_2017_mt"]:.2f}', "no_m18": f'{no["imports_2018_mt"]:.2f}',
        "no_br_fall": f'{no["from_brazil_2017_mt"] - no["from_brazil_2018_mt"]:.2f}', "no_other_rise": f'{no["from_others_2018_mt"] - no["from_others_2017_mt"]:.2f}',
        "no_al17": f'{kt["norway_2017"] / 1000:.2f}', "no_al18": f'{kt["norway_2018"] / 1000:.2f}',
        "br_al17": f'{kt["brazil_2017"] / 1000:.2f}', "br_al18": f'{kt["brazil_2018"] / 1000:.2f}', "br_al_fall": pct(cut["brazil_metal_fall"]),
        "low_list": listing(f"{c} ({v:.2f})" for c, v in supply["below_chemical_minimum"]), "chem_min": f'{supply["chemical_minimum"]:.2f}',
        "us_usgs_imports": mt(usgs["us_2025"]["alumina_imports_2024_kt"], 2),
        "us_baci_imports": f'{united_states["imports_kt"] / 1000:.2f}',
        "ca_br_fall": f'{ca["from_brazil_2017_mt"] - ca["from_brazil_2018_mt"]:.2f}', "ca_fall": f'{ca["imports_2017_mt"] - ca["imports_2018_mt"]:.2f}',
        "ca_al17": f'{kt["canada_2017"] / 1000:.2f}', "ca_al18": f'{kt["canada_2018"] / 1000:.2f}',
        "capacity_rows": "\n".join(capacity_rows), "w_out": mt(al_t["World"]["y2024"]), "w_cap": mt(al_t["World"]["capacity_2024"]),
        "w_unused": mt(spare["world_kt"]), "cn_unused": mt(spare["china_kt"]), "out_unused": mt(spare["outside_china_kt"]),
        "out_unused_share": pct(spare["outside_china_share_of_output"]), "other_unused": mt(spare["unnamed_countries_kt"]),
        "us_unused": mt(spare["united_states_kt"]),
        "mcs19_bx": link(src, "mcs2019_bauxite", "USGS, bauxite and alumina, 2019 edition"),
        "mcs20_bx": link(src, "mcs2020_bauxite", "USGS, bauxite and alumina, 2020 edition"),
        "mcs19_al": link(src, "mcs2019_aluminum", "USGS, aluminum, 2019 edition"),
        "mcs20_al": link(src, "mcs2020_aluminum", "USGS, aluminum, 2020 edition"),
    }
    im = {s: {e["name"]: e["share"] for e in trade[s]["importers"]} for s in STAGES}

    values = {
        "title": escape(TITLE), "deck": escape(DECK), "date": inputs["version"], "trade_year": r["trade_year"],
        "cn_bx": pct(prod["bauxite"]["shares"]["China"]), "cn_al2o3": pct(prod["alumina"]["shares"]["China"]),
        "cn_al": pct(prod["aluminium"]["shares"]["China"]),
        "gn_bx": pct(prod["bauxite"]["shares"]["Guinea"]), "au_bx": pct(prod["bauxite"]["shares"]["Australia"]),
        "gn_ex": pct(ex["bauxite"]["Guinea"]), "au_ex": pct(ex["bauxite"]["Australia"]),
        "cn_bx_im": pct(im["bauxite"]["China"]),
        "cn_al2o3_ex": pct(trade["alumina"]["china_export_share"]), "cn_al_ex": pct(trade["aluminium"]["china_export_share"]),
        "cn_al2o3_own": pct(trade["alumina"]["china_exports_over_own_output"]), "cn_al_own": pct(trade["aluminium"]["china_exports_over_own_output"], 1),
        "cn_al_im": pct(trade["aluminium"]["china_import_share"]),
        "au_al2o3_ex": pct(ex["alumina"]["Australia"]), "br_al2o3_ex": pct(ex["alumina"]["Brazil"]), "id_al2o3_ex": pct(ex["alumina"]["Indonesia"]),
        "al_lead": trade["aluminium"]["leading_exporter"], "al_lead_share": pct(trade["aluminium"]["leading_exporter_share"]),
        "bx_traded": pct(trade["bauxite"]["traded_over_produced"]), "al2o3_traded": pct(trade["alumina"]["traded_over_produced"]),
        "semis_cn_mt": mt(semis["china_exports_kt"]), "semis_cn_share": pct(semis["china_export_share"]),
        "semis_over_primary": pct(semis["china_exports_over_primary_output"]),
        "prod_rows": "\n".join(prod_rows), "stage_rows": "\n".join(stage_rows), "china_rows": "\n".join(china_rows),
        "gn_reserves": mt(bx["Guinea"]["reserves"] / 1000, 1), "gn_reserve_share": pct(bx["Guinea"]["reserves"] / bx["World"]["reserves"]),
        "gn_2025": mt(bx["Guinea"]["y2025"], 0), "gn_2025_share": pct(bx["Guinea"]["y2025"] / bx["World"]["y2025"]),
        "cn_dom": mt(cb["domestic_kt"]), "cn_imp": mt(cb["imports_kt"]), "cn_imp_share": pct(cb["import_share_of_supply"]),
        "gn_cn": mt(cb["guinea_kt"]), "gn_cn_supply": pct(cb["guinea_share_of_supply"]),
        "gn_of_cn_imports": pct(cb["guinea_share_of_china_imports"]), "cn_of_gn_exports": pct(cb["china_share_of_guinea_exports"]),
        "series_rows": "\n".join(series_rows),
        "gn_first_mt": mt(first["guinea_kt"]), "gn_first_year": first["year"], "gn_last_mt": mt(last["guinea_kt"]),
        "cn_first_share": pct(first["china_import_share"]), "cn_last_share": pct(last["china_import_share"]),
        "x_baci_cn": f'{cross["baci_china_imports_mt"]:.1f}', "x_cust_cn": f'{cross["customs_china_imports_mt"]:.1f}',
        "x_baci_gn_cn": f'{cross["baci_guinea_to_china_mt"]:.1f}', "x_cust_gn_cn": f'{cross["customs_guinea_to_china_mt"]:.1f}',
        "x_baci_gn": f'{cross["baci_guinea_exports_mt"]:.1f}', "x_ins_gn": f'{cross["ins_guinea_exports_mt"]:.1f}',
        "ins_cn_share": pct(g["ins_share_to_china_2024"], 1), "gn_wet": f'{g["usgs_yearbook_2024_wet_kt"] / 1000:,.0f}',
        "gn_dry": f'{g["usgs_yearbook_2024_dry_tonnes"] / 1e6:,.1f}',
        "screen_rows": "\n".join(screen_rows), "half_al": mt(half["aluminium_kt"]), "half_al_share": pct(half["share_of_world_aluminium"]),
        "half_cn_share": pct(half["share_of_china_bauxite"]),
        "id_ban": indo["ban_month"], "id_prod_2022": f'{indo["usgs_production_mt"]["2022"]:.1f}', "id_prod_2023": f'{indo["usgs_production_mt"]["2023"]:.1f}',
        "id_prod_2024": indo["usgs_production_mt"]["2024"], "id_al2o3_usgs": mt(usgs["alumina"]["Indonesia"]["y2024"]),
        "gap_2022": f'{-cross["guinea_ins_minus_baci_mt"]["2022"]:.0f}', "gap_2023": f'{-cross["guinea_ins_minus_baci_mt"]["2023"]:.0f}',
        "gap_2024": f'{cross["guinea_ins_minus_baci_mt"]["2024"]:.0f}',
        "id_ex_2022": indo["usgs_exports_mt"]["2022"], "id_ex_2023": indo["usgs_exports_mt"]["2023"],
        "id_al2o3_mt": mt(last["indonesia_alumina_kt"]),
        "ratio_rows": "\n".join(ratio_rows), "bx_ratio": f'{ratios["bauxite_per_alumina_world"]:.1f}',
        "bx_rule_mt": mt(ratios["bauxite_at_usgs_rule_kt"], 0), "bx_world_mt": mt(usgs["bauxite"]["World"]["y2024"], 0),
        "bx_above": pct(ratios["bauxite_above_usgs_rule"]),
        "energy_rows": "\n".join(energy_rows), "mix_rows": "\n".join(mix_rows),
        "kwh_world": f'{intensity["World"]:,}', "kwh_china": f'{intensity["China"]:,}',
        "kwh_top": f'{max(intensity.values()):,}', "kwh_top_region": max(intensity, key=intensity.get),
        "power_coverage": pct(energy["coverage"]),
        "twh_world": f'{energy["world_twh"]:,.0f}', "cn_power_share": pct(energy["china_share_of_smelting_power"]),
        "cn_coal_share": pct(energy["china_share_of_coal_power"]),
        "coal_world": pct(energy["mix"]["World"]["Coal"]), "coal_china": pct(energy["mix"]["China"]["Coal"]),
        "hydro_world": pct(energy["mix"]["World"]["Hydro"]),
        "cost_share": pct(oecd["energy_share_of_cost_up_to"]), "support_low": oecd["support_usd_billion_2013_2017"][0],
        "support_high": oecd["support_usd_billion_2013_2017"][1], "firms": oecd["firms_studied"],
        "util_cn": pct(util["China"]), "util_world": pct(util["World"]), "util_us": pct(util["United States"]),
        "recycled_share": pct(r["recycled_share_of_metal_2024"]), "us_old_scrap": pct(usgs["us_2025"]["old_scrap_share_of_apparent_consumption"]),
        "recycling_saving": pct(oecd["recycling_energy_saving_up_to"]),
        "rev_id_old": mt(old["Indonesia"], 0), "rev_id_new": mt(bx["Indonesia"]["y2024"]), "rev_cn_old": mt(old["China"], 0),
        "rev_cn_new": mt(bx["China"]["y2024"]), "rev_gn_old": mt(old["Guinea"], 0), "rev_gn_new": mt(bx["Guinea"]["y2024"], 0),
        "rev_w_old": mt(old["World"], 0), "rev_w_new": mt(bx["World"]["y2024"], 0),
        "rev_gn_share_old": pct(rev["guinea_share_2025_edition"]), "rev_gn_share_new": pct(rev["guinea_share_2026_edition"]),
        "cn_usgs": pct(rev["china_share_usgs"], 1), "cn_iai": pct(rev["china_share_iai"], 1), "cn_iai_2025": pct(rev["china_share_iai_2025"], 1),
        "trade_rows": "\n".join(trade_rows), "value_year": tyear,
        "d_year": defect["year"], "d_share": pct(defect["guinea_share"]),
        "d_2022": f'{chk["2022"]["tonnes"] / 1e6:.1f}', "d_2023": f'{chk["2023"]["tonnes"] / 1e6:.1f}', "d_2024": f'{chk["2024"]["tonnes"] / 1e6:.1f}',
        "d_p2022": f'{chk["2022"]["usd_per_tonne"]:.0f}', "d_p2023": f'{chk["2023"]["usd_per_tonne"]:.0f}', "d_p2024": f'{chk["2024"]["usd_per_tonne"]:.0f}',
        "mcs_bx": link(src, "mcs2026_bauxite", "USGS, bauxite and alumina, 2026 edition"),
        "mcs_al": link(src, "mcs2026_aluminum", "USGS, aluminum, 2026 edition"),
        "mcs25_bx": link(src, "mcs2025_bauxite", "USGS, bauxite and alumina, 2025 edition"),
        "myb_gn": link(src, "myb_guinea", "USGS 2024 Minerals Yearbook, Guinea"),
        "myb_id23": link(src, "myb_indonesia_2023", "USGS 2023 Minerals Yearbook, Indonesia"),
        "myb_id24": link(src, "myb_indonesia_2024", "USGS 2024 Minerals Yearbook, Indonesia"),
        "ins": link(src, "ins_guinea", "Guinea, national statistics institute, external trade 2024"),
        "smm": link(src, "smm", "Shanghai Metals Market, 20 January 2025"),
        "iai_primary": link(src, "iai_primary", "International Aluminium Institute, primary aluminium production"),
        "iai_alumina": link(src, "iai_alumina", "International Aluminium Institute, alumina production"),
        "iai_energy": link(src, "iai_energy", "International Aluminium Institute, smelting energy intensity"),
        "iai_power": link(src, "iai_power", "International Aluminium Institute, smelting power consumption"),
        "iai_lci": link(src, "iai_lci", "International Aluminium Institute, 2019 life cycle inventory"),
        "iai_cycle": link(src, "iai_cycle", "International Aluminium Institute, Global Aluminium Cycle"),
        "oecd": link(src, "oecd2019", "OECD (2019), The aluminium value chain"),
        "wco26": link(src, "wco_ch26", "WCO, HS 2017, Chapter 26"), "wco28": link(src, "wco_ch28", "WCO, HS 2017, Chapter 28"),
        "wco76": link(src, "wco_ch76", "WCO, HS 2017, Chapter 76"), "baci": link(src, "baci", "CEPII BACI V202601"),
        "references": "\n".join(f'    <li><a href="{escape(s["url"], quote=True)}">{escape(s["title"])}</a> · {escape(s["vintage"])}</li>'
                                for s in src.values()),
    }
    rs, st, gr, sk, gd = inputs["restarts"], inputs["stocks"], inputs["grades"], r["stocks"], r["ore_grades"]

    def src_links(keys):
        return " ".join(f'<a href="{escape(src[k]["url"], quote=True)}">{escape(src[k]["title"])}</a>.' for k in keys)

    restart_rows = ["<tr>" + f'<th scope="row">{escape(x["plant"])}, {escape(x["country"])}</th>'
                    + f'<td class="n">{escape(x.get("capacity_note") or format(x["capacity_t"], ","))}</td>'
                    + "".join(f"<td>{escape(x[k])}</td>" for k in ("announced", "planned", "cost", "later"))
                    + f"<td>{src_links(x['sources'])}</td></tr>" for x in rs["rows"]]
    stock_rows = [
        ("Bauxite at major Chinese ports", f'{st["china_bauxite_ports"]["mt"]:.1f} million tonnes', st["china_bauxite_ports"]["date"], "Trade-press survey",
         f'About {sk["china_bauxite_ports_months_of_2024_imports"]:.1f} months of China’s 2024 bauxite imports', "mysteel_bauxite"),
        ("Alumina in China: ports, refiners, smelters and in transit", f'{st["china_alumina_total"]["mt"]:.2f} million tonnes', st["china_alumina_total"]["date"], "Trade-press survey",
         f'About {sk["china_alumina_days_of_2024_output"]:.0f} days of China’s 2024 alumina output', "mysteel_alumina"),
        ("Aluminium in Shanghai Futures Exchange warehouses", f'{st["shfe_aluminium"]["t"]:,} tonnes', st["shfe_aluminium"]["date"], "Exchange report", "", "shfe"),
        ("Aluminium in London Metal Exchange warehouses", f'{st["lme_aluminium"]["t"]:,} tonnes', st["lme_aluminium"]["date"], "Exchange figure as republished by a metal trader",
         f'The two exchanges together: about {sk["exchange_aluminium_days_of_2024_world_output"]:.1f} days of 2024 world primary output', "westmetall"),
        ("Aluminium held by producers in the United States and Canada: ingot, mill products and scrap", f'{st["us_industry_aluminium"]["kt"] / 1000:.1f} million tonnes', st["us_industry_aluminium"]["date"], "USGS, from an industry association", "", "mcs2026_aluminum"),
    ]
    stock_html = ["<tr>" + f'<th scope="row">{escape(a)}</th><td class="n">{escape(q)}</td><td>{escape(d)}</td><td>{escape(k)}</td><td>{escape(c)}</td><td>{src_links([s])}</td></tr>'
                  for a, q, d, k, c, s in stock_rows]
    grade_rows = ["<tr>" + f'<th scope="row">{escape(g["deposit"])}, {escape(g["country"])}</th><td class="n">{g["reserves_mt"]:,.0f}</td>'
                  + f'<td class="n">{g["al2o3_pct"]:.1f}%</td><td>{escape(g["basis"].capitalize())} alumina</td><td>{src_links([g["source"]])}</td></tr>' for g in gr["rows"]]
    more.update({
        "restart_rows": "\n".join(restart_rows), "stock_rows": "\n".join(stock_html), "grade_rows": "\n".join(grade_rows),
        "us_shutdowns": escape(rs["us_shutdowns"], quote=False), "eu_curtailed": escape(rs["eu_curtailed"], quote=False),
        "cn_plan_translation": escape(rs["china_plan_translation"]), "cn_ceiling": rs["china_ceiling_mt"],
        "cn_cap_2025": mt(al_t["China"]["capacity_2025"]), "cn_out_2025": mt(al_t["China"]["y2025"], 0),
        "st_bx": f'{st["china_bauxite_ports"]["mt"]:.0f}', "st_cut": mt(r["guinea_screen"][0]["bauxite_kt"]),
        "st_ended": st["producer_series_ended"]["date"],
        "gn_q1_25": f'{sk["guinea_q1_2025_exports_mt"]:.1f}', "gn_q1_24": f'{sk["guinea_q1_2024_exports_mt"]:.1f}',
        "lista_line": f'{rs["lista"]["potline_t"]:,}', "lista_share": pct(rs["lista"]["site_share_end_2025"]),
        "src_10k": link(src, "alcoa_10k_2025", "Alcoa, 2025 annual report"), "src_century": link(src, "century_q3_2026", "Century Aluminum, third-quarter 2026 results"),
        "src_myb_al": link(src, "myb2022_aluminum", "USGS Minerals Yearbook 2022, aluminum"),
        "src_myb_bx": link(src, "myb2022_bauxite", "USGS Minerals Yearbook 2022, bauxite and alumina"),
        "gr_low": f'{gd["lowest"]["al2o3_pct"]:.0f}%', "gr_high": f'{gd["highest"]["al2o3_pct"]:.0f}%',
        "gr_av_low": f'{gd["available_low"]["al2o3_pct"]:.1f}%', "gr_av_low_name": escape(gd["available_low"]["deposit"]),
        "gr_av_high": f'{gd["available_high"]["al2o3_pct"]:.1f}%', "gr_av_high_name": escape(gd["available_high"]["deposit"]),
        "gr_ratio": pct(gd["available_low_over_high"]), "gr_india": escape(gr["india"]["quote"], quote=False),
        "src_ec": link(src, "ec_metals_plan", "European Commission, Steel and Metals Action Plan, March 2025"),
        "src_miit": link(src, "miit_plan", "China, aluminium industry plan for 2025 to 2027"),
        "src_xinhua": link(src, "xinhua_2026", "Xinhua, 9 May 2026"),
        "src_reuters15": link(src, "reuters_2015", "Reuters column, 3 February 2015"),
        "src_ibm": link(src, "ibm_2022", "Indian Minerals Yearbook 2022, Bauxite"),
        "src_gn": link(src, "gn_bulletin", "Guinea, Ministry of Mines and Geology, statistics bulletin no. 27"),
        "gn_al_low": f'{gd["guinea_exports"]["alumina_low"]:.2f}%', "gn_al_high": f'{gd["guinea_exports"]["alumina_high"]:.2f}%',
        "gn_n": NUMBER_WORDS.get(gd["guinea_exports"]["companies_with_alumina"], gd["guinea_exports"]["companies_with_alumina"]),
        "gn_m_low": f'{gd["guinea_exports"]["moisture_low"]:.2f}%', "gn_m_high": f'{gd["guinea_exports"]["moisture_high"]:.2f}%',
        "gn_m_avg": f'{gd["guinea_exports"]["moisture_average"]:.2f}%', "gn_gap": f'{gd["guinea_exports"]["usgs_wet_dry_gap"]:.1%}',
    })
    flows = load(FLOWS)
    fm = flows["markets"]

    def origins(block, n=3):
        items = [("home", block["home"])] + [(t["name"], t["share"]) for t in block["top_foreign"]]
        items = sorted((i for i in items if i[1] >= 0.005), key=lambda kv: -kv[1])[:n]
        return ", ".join(f"{name} {pct(share)}" for name, share in items)

    flow_rows = [row(market, [f'{m["apparent_use_kt"] / 1000:.1f}', origins(m["smelted_in"]), origins(m["alumina_refined_in"]), origins(m["bauxite_mined_in"]),
                              pct(m["selected"]["guinea_bauxite"])], numeric=False) for market, m in fm.items()]
    us_f, eu_f, cn_f, jp_f = fm["United States"], fm["European Union"], fm["China"], fm["Japan"]
    more.update({
        "flow_year": flows["year"], "flow_rows": "\n".join(flow_rows), "chart_stages": chart_stages(fm),
        "fl_us_ca": pct(us_f["smelted_in"]["top_foreign"][0]["share"]), "fl_us_br_bx": pct(us_f["selected"]["brazil_bauxite"]),
        "fl_us_br_customs": pct(us_f["customs_share_of"]["Brazil"], 1), "fl_us_gn": pct(us_f["selected"]["guinea_bauxite"]),
        "fl_eu_home": pct(eu_f["smelted_in"]["home"]), "fl_eu_au_bx": pct(eu_f["selected"]["australia_bauxite"]),
        "fl_eu_au_customs": pct(eu_f["customs_share_of"]["Australia"], 0), "fl_eu_gn": pct(eu_f["selected"]["guinea_bauxite"]),
        "fl_eu_h1": f'{eu_f["smelted_in"]["hhi"]:,}', "fl_eu_h3": f'{eu_f["bauxite_mined_in"]["hhi"]:,}',
        "fl_jp_h1": f'{jp_f["smelted_in"]["hhi"]:,}', "fl_jp_h3": f'{jp_f["bauxite_mined_in"]["hhi"]:,}',
        "fl_cn_h1": f'{cn_f["smelted_in"]["hhi"]:,}', "fl_cn_h3": f'{cn_f["bauxite_mined_in"]["hhi"]:,}',
        "fl_cn_home_bx": pct(cn_f["bauxite_mined_in"]["home"]), "fl_cn_gn": pct(cn_f["selected"]["guinea_bauxite"]),
        "fl_gap": f'{flows["stages"]["alumina"]["exports_above_supply_kt"] / 1000:.1f}',
        "fl_eu_no": pct(eu_f["selected"]["norway_smelting"]), "fl_us_ca_customs": pct(us_f["customs_share_of"]["Canada"]),
        "fl_in_h1": f'{fm["India"]["smelted_in"]["hhi"]:,}', "fl_in_h3": f'{fm["India"]["bauxite_mined_in"]["hhi"]:,}',
        "fl_cn_gn_customs": pct(cn_f["customs_share_of"]["Guinea"], 2),
        "fl_alt_low": pct(min(v["guinea_bauxite"] for v in flows["sensitivity"]["unalloyed_metal_only"]["markets"].values()), 1),
        "fl_alt_high": pct(max(v["guinea_bauxite"] for v in flows["sensitivity"]["unalloyed_metal_only"]["markets"].values())),
        "fl_alt_eu_home": pct(flows["sensitivity"]["unalloyed_metal_only"]["markets"]["European Union"]["home_smelting"]),
        "fl_noprod": f'{flows["stages"]["aluminium"]["trade_shipped_by_countries_without_production_kt"] / 1000:.1f}',
        "fl_metal_trade": f'{flows["stages"]["aluminium"]["world_trade_kt"] / 1000:.1f}',
        "fl_cn_home_dry": pct(flows["sensitivity"]["traded_bauxite_less_10_per_cent_moisture"]["markets"]["China"]["home_bauxite"], 1),
        "fl_cn_home_bx1": pct(cn_f["bauxite_mined_in"]["home"], 1),
        "fl_gn_low": pct(min(v["selected"]["guinea_bauxite"] for v in fm.values())), "fl_gn_high": pct(max(v["selected"]["guinea_bauxite"] for v in fm.values())),
        "src_myb_al": link(src, "myb2022_aluminum", "USGS Minerals Yearbook 2022, aluminum"),
        "src_myb_bx": link(src, "myb2022_bauxite", "USGS Minerals Yearbook 2022, bauxite and alumina"),
        "src_kastner": link(src, "kastner", "Kastner, Kastner and Nonhebel (2011)"),
    })
    values.update(more)
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(values)


def build():
    inputs = load(INPUTS)
    results = evaluate(inputs)
    p, t = results["production_2024"], results["trade_2024"]
    kwh = inputs["iai"]["smelting_energy_kwh_per_tonne_ac_2025"]["World"]
    data = {
        "title": "Aluminium chain", "h1": TITLE, "deck": DECK, "published": True, "version": inputs["version"],
        "chokepoint": {
            "product": "Aluminium metal", "stage": "Smelting", "mechanism": "thermodynamic",
            "physics": f"Smelting is continuous electrolysis. It used {kwh / 1000:.1f} MWh of electricity per tonne of metal on average in 2025",
            "holder": "China",
            "share": (f'{pct(p["aluminium"]["shares"]["China"])} of primary aluminium and {pct(p["alumina"]["shares"]["China"])} of alumina (2024); '
                      f'Guinea ships {pct(t["bauxite"]["leading_exporter_share"])} of traded bauxite'),
            # "estimate" until the source ledger carries the quoted USGS rows; the basis note gives them
            "control": "—", "conf": "estimate",
        },
        "sources": inputs["sources"],
        "inputs": {k: inputs[k] for k in ("usgs_mcs2026", "usgs_mcs2025_estimates_for_2024", "iai", "oecd2019", "guinea", "indonesia",
                                         "smm_china_imports_2024", "trade_checks", "scenarios", "brazil_2018", "emirates", "restarts", "stocks", "grades")},
        "results": results,
        "flow_model": load(FLOWS),
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    ARTICLE.write_text(render(inputs, results), encoding="utf-8", newline="\n")
    print("wrote aluminium_chain.json and aluminium-chain.html: China %s of primary aluminium, Guinea %s of traded bauxite (2024)"
          % (pct(p["aluminium"]["shares"]["China"]), pct(t["bauxite"]["leading_exporter_share"])))


if __name__ == "__main__":
    build()
