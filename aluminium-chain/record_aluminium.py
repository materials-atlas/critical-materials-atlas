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
    ]
    for ok, message in checks:
        if not ok:
            raise SystemExit("aluminium page text no longer matches the data: " + message)

    return {"trade_year": year, "production_2024": production, "trade_2024": trade, "semis_2024": semis, "china_bauxite_2024": china_bauxite,
            "bauxite_series": bx_series, "ratios_2024": ratios, "guinea_screen": screen, "energy_2025": energy,
            "capacity_utilisation_2024": utilisation, "revisions": revision, "recycled_share_of_metal_2024": recycled_share,
            "cross_checks_2024": cross, "bauxite_2023_record": defect}


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
                                         "smm_china_imports_2024", "trade_checks", "scenarios")},
        "results": results,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    ARTICLE.write_text(render(inputs, results), encoding="utf-8", newline="\n")
    print("wrote aluminium_chain.json and aluminium-chain.html: China %s of primary aluminium, Guinea %s of traded bauxite (2024)"
          % (pct(p["aluminium"]["shares"]["China"]), pct(t["bauxite"]["leading_exporter_share"])))


if __name__ == "__main__":
    build()
