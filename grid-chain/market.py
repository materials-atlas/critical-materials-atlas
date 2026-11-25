"""Order books, prices and output: calculations on the official series in market_inputs.json.

Imported by record_grid.py. Every figure here is arithmetic on a published series; nothing is modelled.
"""
from __future__ import annotations


def _last(series):
    key = max(series)
    return key, series[key]


def _year_average(series, year):
    values = [v for k, v in series.items() if k.startswith(str(year))]
    if len(values) != 12:
        raise SystemExit(f"expected twelve months of {year}, found {len(values)}")
    return sum(values) / 12


def _months_of_shipments(block, month):
    """Unfilled orders at the end of a month divided by average monthly shipments over the twelve months to it."""
    months = sorted(k for k in block["shipments"] if k <= month)[-12:]
    if len(months) != 12:
        raise SystemExit("fewer than twelve months of shipments before " + month)
    return block["unfilled_orders"][month] / (sum(block["shipments"][m] for m in months) / 12)


def evaluate(inputs):
    de = inputs["germany_order_backlog"]
    rng = de["range_months"]
    de_latest = max(rng["WZ08-271"])
    de_points = ["2015-12", "2019-12", "2021-12", "2022-12", "2023-12", "2024-12", "2025-12", de_latest]
    germany = {
        "latest_month": de_latest,
        "range_months": {wz: {m: rng[wz].get(m) for m in de_points} for wz in rng},
        "volume_index_start": {wz: s[min(s)] for wz, s in de["volume_index_2021_100_original_values_total_market"].items()},
        "volume_index_latest": {wz: s[de_latest] for wz, s in de["volume_index_2021_100_original_values_total_market"].items()},
    }

    us = inputs["us_unfilled_orders"]["series"]
    us_latest = max(us["35C"]["unfilled_orders"])
    us_points = ["2015-12", "2019-12", "2021-12", "2022-12", "2023-12", "2024-12", "2025-12", us_latest]
    united_states = {"latest_month": us_latest,
                     "months_of_shipments": {cat: {m: _months_of_shipments(us[cat], m) for m in us_points} for cat in us}}

    ppi = inputs["us_producer_prices"]["series"]
    ppi_latest = max(ppi["PCU335311335311"])
    prices = {"latest_month": ppi_latest, "index_2019_100": {}}
    for sid, s in ppi.items():
        base = _year_average(s, 2019)
        prices["index_2019_100"][sid] = {m: 100 * s[m] / base for m in ("2021-12", "2022-12", "2023-12", "2024-12", "2025-12", ppi_latest)}
    t, m = prices["index_2019_100"]["PCU335311335311"][ppi_latest], prices["index_2019_100"]["PCUOMFG--OMFG--"][ppi_latest]
    prices["transformers_relative_to_manufacturing"] = t / m - 1

    jp = inputs["japan"]
    orders, value, large = jp["transformer_orders"], jp["transformer_production_value"], jp["large_units"]
    japan = {
        "orders_change_fy2020_fy2025": orders["FY2025"] / orders["FY2020"] - 1,
        "production_value_change_fy2020_fy2025": value["FY2025"] / value["FY2020"] - 1,
        "large_units": {y: large["units"][y] for y in sorted(large["units"])},
        "large_gva": {y: large["kva"][y] / 1e6 for y in sorted(large["kva"])},
        "large_units_average_fy2015_fy2018": sum(large["units"][f"FY{y}"] for y in range(2015, 2019)) / 4,
        "large_units_average_fy2022_fy2025": sum(large["units"][f"FY{y}"] for y in range(2022, 2026)) / 4,
    }

    eu = inputs["eu_production_large_transformers"]["by_year"]
    europe = {
        "value_change_2021_2025": eu["2025"]["value_eur"] / eu["2021"]["value_eur"] - 1,
        "units_change_2021_2025": eu["2025"]["units"] / eu["2021"]["units"] - 1,
        "value_per_unit_eur": {y: eu[y]["value_eur"] / eu[y]["units"] for y in ("2021", "2022", "2023", "2024", "2025")},
    }

    sv = inputs["eu_business_survey"]["series"]
    sv_latest = max(sv["capacity_utilisation_pct"])
    material = sv["limited_by_material_or_equipment_pct"]
    peak_q = max(material, key=material.get)
    survey = {"latest_quarter": sv_latest, "first_quarter": min(material),
              "first": {k: s[min(s)] for k, s in sv.items()}, "latest": {k: s[sv_latest] for k, s in sv.items()},
              "material_peak_quarter": peak_q, "material_peak": material[peak_q]}

    fed = inputs["us_capacity"]["series"]
    fed_latest = max(fed["capacity_utilisation_naics335_pct"])
    us_capacity = {"latest_month": fed_latest,
                   "utilisation": {m: fed["capacity_utilisation_naics335_pct"][m] for m in ("2015-01", "2019-12", fed_latest)},
                   "production_index": {m: fed["production_index_naics3353"][m] for m in ("2015-01", "2019-12", fed_latest)}}

    # Sentences on the page state these in words. Stop if the numbers no longer support them.
    g = germany["range_months"]
    checks = [
        (g["WZ08-271"][de_latest] > 2 * g["WZ08-271"]["2019-12"], "the German range for branch 27.1 is no longer more than double its 2019 level"),
        (g["WZ08-271"][de_latest] > g["WZ08-C"][de_latest] + 3, "the German range for branch 27.1 is no longer well above all manufacturing"),
        (united_states["months_of_shipments"]["35C"][us_latest] > 1.3 * united_states["months_of_shipments"]["35C"]["2019-12"]
         and united_states["months_of_shipments"]["MTU"][us_latest] < 1.2 * united_states["months_of_shipments"]["MTU"]["2019-12"]
         and united_states["months_of_shipments"]["35C"]["2022-12"] > united_states["months_of_shipments"]["35C"][us_latest],
         "the US backlog comparison has changed"),
        (0.15 < prices["transformers_relative_to_manufacturing"] < 0.45, "the relative price of US transformers has left the stated range"),
        (japan["orders_change_fy2020_fy2025"] > 1.0 and japan["large_units_average_fy2022_fy2025"] < japan["large_units_average_fy2015_fy2018"],
         "Japanese orders no longer doubled, or large-unit output is no longer below its earlier level"),
        (europe["value_change_2021_2025"] > 1.0 and abs(europe["units_change_2021_2025"]) < 0.05, "EU large-transformer value no longer doubled with units flat"),
        (survey["latest"]["limited_by_material_or_equipment_pct"] > 3 * survey["first"]["limited_by_material_or_equipment_pct"],
         "the survey share naming material shortages has changed"),
    ]
    for ok, message in checks:
        if not ok:
            raise SystemExit("grid market text no longer matches the data: " + message)
    return {"germany": germany, "united_states": united_states, "us_producer_prices": prices, "japan": japan,
            "eu_large_transformers": europe, "eu_survey": survey, "us_capacity": us_capacity}


def quarter_label(key):
    year, q = key.split("-Q")
    return f'the {["first", "second", "third", "fourth"][int(q) - 1]} quarter of {year}'


def month_label(key):
    names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    year, month = key.split("-")
    return f"{names[int(month) - 1]} {year}"


def evaluate_firms(inputs):
    """Order backlog set against revenue for the reporting segments that contain power transformers."""
    firms = []
    for f in inputs["manufacturers"]:
        first, last = f["years"][0], f["years"][-1]
        rec = {"company": f["company"], "segment": f["segment"], "unit": f["unit"], "first_year": first["year"], "last_year": last["year"],
               "backlog_first": first["backlog"], "backlog_last": last["backlog"], "backlog_multiple": last["backlog"] / first["backlog"],
               "ratio_comparable": f["ratio_comparable"]}
        if f["ratio_comparable"]:
            rec["years_of_revenue"] = {y["year"]: y["backlog"] / y["revenue"] for y in f["years"]}
        elif first.get("revenue"):
            rec["revenue_multiple"] = last["revenue"] / first["revenue"]
        firms.append(rec)
    es = inputs["eu_electrical_steel"]
    years = es["years"]
    steel = {"years": years,
             "utilisation": [p / c for p, c in zip(es["union_production_t"], es["union_capacity_t"])],
             "union_market_share": [s / c for s, c in zip(es["union_sales_to_unrelated_customers_t"], es["consumption_steel_and_cores_t"])],
             "imports_multiple_2021_2025": es["imports_steel_t"][-1] / es["imports_steel_t"][0],
             "production_change_2021_2025": es["union_production_t"][-1] / es["union_production_t"][0] - 1,
             "overcapacity_over_union_consumption_2024": es["global_overcapacity_t"] / es["consumption_steel_and_cores_t"][3]}
    for computed, printed in zip(steel["utilisation"] + steel["union_market_share"], es["capacity_utilisation_printed"] + es["union_market_share_printed"]):
        if abs(computed - printed) > 0.006:
            raise SystemExit("the Commission's printed percentages do not follow from its tonnages")
    for a, b, c in zip(es["imports_steel_and_cores_t"], es["union_sales_to_unrelated_customers_t"], es["consumption_steel_and_cores_t"]):
        if abs(a + b - c) > 2:      # the 2024 row is one tonne off in the source
            raise SystemExit("Union sales plus imports do not add to the Commission's consumption figure")
    ratios = [r["years_of_revenue"][r["last_year"]] for r in firms if r["ratio_comparable"]]
    early = [r["years_of_revenue"][r["first_year"]] for r in firms if r["ratio_comparable"] and r["first_year"].endswith("2021")]
    checks = [
        (len(ratios) == 4 and 2.8 < min(ratios) and max(ratios) < 3.8, "the latest backlog ratios are no longer about three to four years of revenue"),
        (len(early) == 2 and all(1.3 < x < 1.6 for x in early), "the 2021 backlog ratios are no longer about one and a half years"),
        (all(r["backlog_multiple"] > 2 for r in firms if r["company"] != "Hyosung Heavy Industries"), "a maker's backlog no longer at least doubled"),
        (0.70 < steel["utilisation"][-1] < 0.72 and steel["imports_multiple_2021_2025"] > 2, "the EU electrical-steel figures have changed"),
    ]
    for ok, message in checks:
        if not ok:
            raise SystemExit("grid manufacturer text no longer matches the data: " + message)
    return {"manufacturers": firms, "eu_electrical_steel": steel, "latest_ratio_range": [min(ratios), max(ratios)]}


def _row(label, cells):
    from html import escape
    return (f'<tr><th scope="row">{escape(str(label))}</th>' + "".join(f"<td>{escape(str(c))}</td>" for c in cells) + "</tr>")


def _a(url, label):
    from html import escape
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def template_values(market_inputs, firm_inputs):
    """Everything the page prints from the two evidence files, as template variables."""
    from html import escape
    r, f = evaluate(market_inputs), evaluate_firms(firm_inputs)
    g, us, pr, jp, eu, sv, cap = (r["germany"], r["united_states"], r["us_producer_prices"], r["japan"], r["eu_large_transformers"],
                                   r["eu_survey"], r["us_capacity"])
    de_l, us_l, pp_l = g["latest_month"], us["latest_month"], pr["latest_month"]
    rng, mos, idx = g["range_months"], us["months_of_shipments"], pr["index_2019_100"]
    backlog_rows = [
        _row("Germany: order backlog, in months of sales", ["Electric motors, generators and transformers (branch 27.11)", f'{rng["WZ08-2711"]["2019-12"]:.1f}',
                                                           f'{rng["WZ08-2711"][de_l]:.1f} ({month_label(de_l)})', f'All manufacturing: {rng["WZ08-C"]["2019-12"]:.1f} to {rng["WZ08-C"][de_l]:.1f}']),
        _row("Germany: order backlog, in months of sales", ["The same with switchgear and controls (branch 27.1)", f'{rng["WZ08-271"]["2019-12"]:.1f}',
                                                           f'{rng["WZ08-271"][de_l]:.1f} ({month_label(de_l)})', f'Electrical equipment as a whole: {rng["WZ08-27"]["2019-12"]:.1f} to {rng["WZ08-27"][de_l]:.1f}']),
        _row("United States: unfilled orders, in months of shipments", ["Electrical equipment: transformers, motors and generators, switchgear, controls", f'{mos["35C"]["2019-12"]:.1f}',
                                                                       f'{mos["35C"][us_l]:.1f} ({month_label(us_l)}); {mos["35C"]["2022-12"]:.1f} at the end of 2022',
                                                                       f'Manufacturing industries that report unfilled orders: {mos["MTU"]["2019-12"]:.1f} to {mos["MTU"][us_l]:.1f}']),
        _row("United States: producer prices, 2019 = 100", ["Power and specialty transformer manufacturing", "100 (2019 average)", f'{idx["PCU335311335311"][pp_l]:.0f} ({month_label(pp_l)})',
                                                           f'Total manufacturing: {idx["PCUOMFG--OMFG--"][pp_l]:.0f}; machinery: {idx["PCU333---333---"][pp_l]:.0f}']),
    ]
    j_in, e_in = market_inputs["japan"], market_inputs["eu_production_large_transformers"]["by_year"]
    fedp = cap["production_index"]
    output_rows = [
        _row("Japan: transformer orders, billion yen", ["Fiscal 2020", f'{j_in["transformer_orders"]["FY2020"] / 1000:,.1f}', "Fiscal 2025", f'{j_in["transformer_orders"]["FY2025"] / 1000:,.1f}', f'{jp["orders_change_fy2020_fy2025"]:+.0%}']),
        _row("Japan: transformer production, billion yen", ["Fiscal 2020", f'{j_in["transformer_production_value"]["FY2020"] / 1000:,.1f}', "Fiscal 2025", f'{j_in["transformer_production_value"]["FY2025"] / 1000:,.1f}', f'{jp["production_value_change_fy2020_fy2025"]:+.0%}']),
        _row("Japan: units of 100 MVA and above produced, yearly average", ["Fiscal 2015 to 2018", f'{jp["large_units_average_fy2015_fy2018"]:.1f}', "Fiscal 2022 to 2025", f'{jp["large_units_average_fy2022_fy2025"] + 1e-9:.1f}',
                                                                         f'{jp["large_units_average_fy2022_fy2025"] / jp["large_units_average_fy2015_fy2018"] - 1:+.0%}']),
        _row("EU: sold production of transformers above 10 MVA, billion euro", ["2021", f'{e_in["2021"]["value_eur"] / 1e9:.2f}', "2025", f'{e_in["2025"]["value_eur"] / 1e9:.2f}', f'{eu["value_change_2021_2025"]:+.0%}']),
        _row("EU: units of transformers above 10 MVA sold", ["2021", f'{e_in["2021"]["units"]:,.0f}', "2025", f'{e_in["2025"]["units"]:,.0f}', f'{eu["units_change_2021_2025"]:+.1%}']),
        _row("United States: production index, electrical equipment", ["December 2019", f'{fedp["2019-12"]:.1f}', month_label(cap["latest_month"]), f'{fedp[cap["latest_month"]]:.1f}',
                                                                      f'{fedp[cap["latest_month"]] / fedp["2019-12"] - 1:+.0%}']),
    ]
    firm_rows = []
    lookup = {m["company"]: m for m in firm_inputs["manufacturers"]}
    for rec in f["manufacturers"]:
        src = lookup[rec["company"]]
        unit = src["unit"]
        years = {y["year"]: y for y in src["years"]}
        fmt = (lambda y: ("about " if years[y].get("backlog_rounded") else "") + f'{years[y]["backlog"]:,.0f}')
        if rec["ratio_comparable"]:
            a, b = f'{rec["years_of_revenue"][rec["first_year"]]:.1f}', f'{rec["years_of_revenue"][rec["last_year"]]:.1f}'
        else:
            a = b = "not formed"
        firm_rows.append(_row(f'{rec["company"]}, {rec["segment"]}', [unit, f'{rec["first_year"]}: {fmt(rec["first_year"])}', a,
                                                                       f'{rec["last_year"]}: {fmt(rec["last_year"])}', b, f'{rec["backlog_multiple"]:.1f} times', src["scope"]]))
    es_in, es = firm_inputs["eu_electrical_steel"], f["eu_electrical_steel"]
    steel_rows = [_row(y, [f'{es_in["union_production_t"][i]:,}', f'{es_in["union_capacity_t"][i]:,}', f'{es["utilisation"][i]:.0%}', f'{es_in["imports_steel_t"][i]:,}',
                           f'{es["union_market_share"][i]:.0%}']) for i, y in enumerate(es["years"])]
    st = {s["company"] + s["date"]: s for s in firm_inputs["statements"]}
    statements = " ".join(f'{escape(s["company"])}, {escape(s["date"])}: “{escape(s["quote"])}” ({_a(s["url"], s["document"])}).' for s in firm_inputs["statements"][:3])
    announcements = "\n".join(f'  <li>{escape(a["company"])}, {escape(a["date"])}. {escape(a["stated"].rstrip("."))}. {_a(a["url"], a["document"])}.</li>' for a in firm_inputs["capacity_announcements"])
    pc = firm_inputs["plant_count_study"]
    hd = lookup["HD Hyundai Electric"]
    lo, hi = f["latest_ratio_range"]
    sources = []
    for key in ("germany_order_backlog", "us_unfilled_orders", "us_producer_prices", "eu_production_large_transformers", "eu_business_survey", "us_capacity"):
        b = market_inputs[key]
        sources.append(f'<li id="source-{key}">{_a(b["url"], b["source"])}</li>')
    sources.append(f'<li id="source-japan_orders">{_a(j_in["orders_url"], j_in["orders_source"])}</li>')
    sources.append(f'<li id="source-japan_production">{_a(j_in["production_url"], j_in["production_source"])}</li>')
    sources.append(f'<li id="source-eu_steel">{_a(es_in["url"], es_in["source"])}</li>')
    sources.append(f'<li id="source-plant_count">{_a(pc["url"], pc["source"])}</li>')
    return {
        "backlog_rows": "\n".join(backlog_rows), "output_rows": "\n".join(output_rows), "firm_rows": "\n".join(firm_rows), "steel_rows": "\n".join(steel_rows),
        "de_2711_2019": f'{rng["WZ08-2711"]["2019-12"]:.1f}', "de_2711_latest": f'{rng["WZ08-2711"][de_l]:.1f}', "de_latest_label": month_label(de_l),
        "de_c_latest": f'{rng["WZ08-C"][de_l]:.1f}', "de_vol_271": f'{g["volume_index_latest"]["WZ08-271"] / g["volume_index_start"]["WZ08-271"]:.1f}',
        "us_2019": f'{mos["35C"]["2019-12"]:.1f}', "us_latest": f'{mos["35C"][us_l]:.1f}', "us_peak": f'{mos["35C"]["2022-12"]:.1f}', "us_latest_label": month_label(us_l),
        "us_change": f'{mos["35C"][us_l] / mos["35C"]["2019-12"] - 1:.0%}', "us_mfg_change": f'{mos["MTU"][us_l] / mos["MTU"]["2019-12"] - 1:.0%}',
        "us_mfg_2019": f'{mos["MTU"]["2019-12"]:.1f}', "us_mfg_latest": f'{mos["MTU"][us_l]:.1f}',
        "jp_large_2020": f'{jp["large_units"]["FY2020"]:.0f}', "jp_large_2024": f'{jp["large_units"]["FY2024"]:.0f}',
        "sv_demand": f'{sv["latest"]["limited_by_demand_pct"]:.1f}%', "sv_none": f'{sv["latest"]["no_limit_pct"]:.1f}%',
        "ppi_latest": f'{idx["PCU335311335311"][pp_l]:.0f}', "ppi_mfg": f'{idx["PCUOMFG--OMFG--"][pp_l]:.0f}', "ppi_relative": f'{pr["transformers_relative_to_manufacturing"]:.0%}',
        "ppi_latest_label": month_label(pp_l),
        "jp_orders_change": f'{jp["orders_change_fy2020_fy2025"]:.0%}', "jp_large_2025": f'{jp["large_units"]["FY2025"]:.0f}',
        "jp_large_early": f'{jp["large_units_average_fy2015_fy2018"]:.0f}', "jp_large_late": f'{jp["large_units_average_fy2022_fy2025"]:.0f}',
        "eu_value_change": f'{eu["value_change_2021_2025"]:.0%}', "eu_units_2021": f'{e_in["2021"]["units"]:,.0f}', "eu_units_2025": f'{e_in["2025"]["units"]:,.0f}',
        "eu_value_per_unit_2021": f'{eu["value_per_unit_eur"]["2021"] / 1e6:.2f}', "eu_value_per_unit_2025": f'{eu["value_per_unit_eur"]["2025"] / 1e6:.2f}',
        "sv_first": f'{sv["first"]["limited_by_material_or_equipment_pct"]:.1f}%', "sv_peak": f'{sv["material_peak"]:.1f}%', "sv_peak_q": quarter_label(sv["material_peak_quarter"]),
        "sv_latest": f'{sv["latest"]["limited_by_material_or_equipment_pct"]:.1f}%', "sv_labour": f'{sv["latest"]["limited_by_labour_pct"]:.1f}%',
        "sv_util": f'{sv["latest"]["capacity_utilisation_pct"]:.1f}%', "sv_latest_q": quarter_label(sv["latest_quarter"]),
        "ratio_lo": f"{lo:.1f}", "ratio_hi": f"{hi:.1f}",
        "hd_backlog_latest": f'{hd["latest_backlog"]["backlog"]:,.0f}', "hd_backlog_latest_date": hd["latest_backlog"]["period"],
        "statements": statements, "announcements": announcements,
        "pc_facilities": pc["facilities"], "pc_countries": pc["countries"], "pc_demand": f'{pc["demand_growth_since_2019"]:.0%}', "pc_capacity": f'{pc["nameplate_capacity_growth_upper"]:.0%}',
        "pc_additions": pc["identified_additions_2024_2027_gva"], "pc_link": _a(pc["url"], "Christoffersen, Transformers Magazine, 2025") + ".",
        "steel_in_force": es_in["in_force"], "steel_q49": escape(es_in["grades"]["recital_49"]),
        "steel_util_2021": f'{es["utilisation"][0]:.0%}', "steel_util_2025": f'{es["utilisation"][-1]:.0%}', "steel_imports_multiple": f'{es["imports_multiple_2021_2025"]:.1f}',
        "steel_share_2021": f'{es["union_market_share"][0]:.0%}', "steel_share_2025": f'{es["union_market_share"][-1]:.0%}',
        "steel_overcapacity": f'{es_in["global_overcapacity_t"]:,}', "steel_cn_2021": f'{es_in["china_share_of_imports_2021"]:.0%}', "steel_cn_2025": f'{es_in["china_share_of_imports_2025"]:.0%}',
        "steel_link": _a(es_in["url"], "Commission Implementing Regulation (EU) 2026/2133") + ".",
        "steel_shutdown_link": _a(es_in["plant_shutdowns"]["url"], "thyssenkrupp Steel, 26 March 2026") + ".",
        "market_sources": "\n".join(sources),
        "src_de": _a(market_inputs["germany_order_backlog"]["url"], "Destatis, tables 42113 and 42155") + ".",
        "src_us": _a(market_inputs["us_unfilled_orders"]["url"], "US Census Bureau, M3 survey") + ".",
        "src_ppi": _a(market_inputs["us_producer_prices"]["url"], "US Bureau of Labor Statistics, producer prices") + ".",
        "src_jp": _a(j_in["orders_url"], "Japan Electrical Manufacturers' Association, orders") + ". " + _a(j_in["production_url"], "METI production survey, as republished") + ".",
        "src_eu": _a(market_inputs["eu_production_large_transformers"]["url"], "Eurostat Prodcom, code 27114180") + ".",
        "src_sv": _a(market_inputs["eu_business_survey"]["url"], "European Commission business survey, electrical equipment") + ".",
        "src_fed": _a(market_inputs["us_capacity"]["url"], "Federal Reserve, G.17") + ".",
    }
