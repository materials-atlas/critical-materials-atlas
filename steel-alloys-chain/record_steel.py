"""Build the static steel-alloying-metals study and its evidence JSON.

Inputs: evidence_inputs.json (source tables and quotations transcribed and checked 25 Nov 2026), article.html.in,
out/steel_exposure.json (trade by weight and each market's suppliers, written by extract_exposure.py) and
out/steel_trade.json (trade by value, written by extract_baci.py). No network access. Run from the repository root:
    python steel-alloys-chain/record_steel.py
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from string import Template

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "evidence_inputs.json"
TEMPLATE = HERE / "article.html.in"
EXPOSURE = HERE / "out" / "steel_exposure.json"
TRADE = HERE / "out" / "steel_trade.json"
CONTENT = HERE / "content_inputs.json"
OUT = HERE / "out" / "steel_chain.json"
ARTICLE = HERE / "steel-alloys-chain.html"

TITLE = "Niobium has one main source; for steel's other alloying metals, exposure depends on the buyer"
DECK = ("Brazil mined 93% of the world's niobium in 2024 and supplied most of every large importer's ferroniobium. "
        "Indonesia shipped 93% of traded ferronickel, almost all of it to China, and none of what the United States imported.")
METALS = ("niobium", "vanadium", "chromium", "manganese", "nickel", "molybdenum")
PRODUCTS = ("ferroniobium", "ferrovanadium", "ferrochromium", "ferromanganese", "ferronickel", "ferromolybdenum", "chromium_ore", "manganese_ore")
MARKETS = ("United States", "European Union", "Japan", "South Korea", "India", "China")
CHARTED = ("ferroniobium", "ferrochromium", "ferronickel")
HUBS = ("Netherlands", "China", "Malaysia", "Singapore")     # countries that export ferroniobium and mine little or none
EU_MEMBERS = ("Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia", "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
              "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland", "Portugal", "Romania",
              "Slovakia", "Slovenia", "Spain", "Sweden")
NAVY, TEAL, INK, MUT, RULE = "#15323a", "#0e7c74", "#1a1f24", "#667179", "#e6e9e8"
FONT = "font-family:Inter,system-ui,Segoe UI,Arial,sans-serif"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pct(x, places=0):
    return f"{100 * x:.{places}f}%"


def row(label, cells, numeric=True):
    cls = ' class="n"' if numeric else ""
    return (f'<tr><th scope="row">{escape(str(label))}</th>'
            + "".join(f"<td{cls}>{escape(str(c))}</td>" for c in cells) + "</tr>")


def contained_metal(exposure, content, mine):
    """Restate 2024 trade in contained metal, with a low and a high figure where an origin's content is not measured."""
    by_code = exposure["exporters_by_code"]["codes"]
    groups = {"ferroniobium": ("niobium", ["720293"]), "ferrovanadium": ("vanadium", ["720292"]), "ferrochromium": ("chromium", ["720241", "720249"]),
              "ferromanganese": ("manganese", ["720211", "720219", "720230"]), "ferronickel": ("nickel", ["720260"]),
              "ferromolybdenum": ("molybdenum", ["720270"]), "manganese_ore": ("manganese", ["260200"])}
    ore = content["manganese_ore_grade_2023"]
    out = {}
    for key, (metal, codes) in groups.items():
        gross, low, high, measured = {}, {}, {}, 0.0
        for code in codes:
            for exporter, tonnes in by_code[code].items():
                if key == "manganese_ore":
                    known = exporter in ore["origins"]
                    lo = hi = ore["origins"].get(exporter, ore["world"])
                else:
                    spec = content["codes"][code]
                    rec = spec["origins"].get(exporter)
                    known = rec is not None
                    lo, hi = (rec.get("range", [rec["content"], rec["content"]]) if known else spec["other_origins"])
                gross[exporter] = gross.get(exporter, 0.0) + tonnes
                low[exporter] = low.get(exporter, 0.0) + tonnes * lo
                high[exporter] = high.get(exporter, 0.0) + tonnes * hi
                measured += tonnes if known else 0.0
        total_gross, total_low, total_high = sum(gross.values()), sum(low.values()), sum(high.values())

        def share(exporter):
            """Lowest and highest share of contained metal the exporter can have, given the ranges of the others."""
            others_low, others_high = total_low - low[exporter], total_high - high[exporter]
            return [low[exporter] / (low[exporter] + others_high), high[exporter] / (high[exporter] + others_low)]

        ranked = sorted(gross, key=gross.get, reverse=True)[:4]
        unit = mine[metal]["unit"] if metal in mine else None
        world = mine[metal]["world"] * (1000 if unit and unit.startswith("thousand") else 1) if metal in mine and "content" in unit else None
        out[key] = {"metal": metal, "gross_t": total_gross, "contained_t": [total_low, total_high],
                    "share_of_tonnage_with_measured_content": measured / total_gross,
                    "exporters": [{"name": e, "gross_share": gross[e] / total_gross, "contained_share": share(e),
                                   "content": [low[e] / gross[e], high[e] / gross[e]]} for e in ranked],
                    "mine_output_t": world,
                    "contained_over_mine_output": [total_low / world, total_high / world] if world else None}
    return out


def evaluate(inputs):
    mine = {}
    for metal in METALS:
        table = inputs["mine_production_2024"][metal]
        rows, world = table["rows"], table["world"]
        if abs(sum(rows.values()) / world - 1) > 0.01:
            raise SystemExit(f"{metal}: the country rows do not add to the published world total")
        ranked = sorted((k for k in rows if k != "Other countries"), key=rows.get, reverse=True)
        mine[metal] = {"unit": table["unit"], "world": world, "leader": ranked[0], "leader_share": rows[ranked[0]] / world,
                       "second": ranked[1], "second_share": rows[ranked[1]] / world}

    exposure = load(EXPOSURE)
    year, base = str(exposure["years"][-1]), str(exposure["years"][0])
    trade = {}
    for key in PRODUCTS:
        now, then = exposure["by_year"][year][key], exposure["by_year"][base][key]
        world = now["world"]
        markets = {}
        for market in MARKETS:
            rec = now["markets"][market]
            top = rec["top"][0]
            # a market that is, or contains, the leading exporter cannot import from it in this table
            own = market == now["world_leader"] or (market == "European Union" and now["world_leader"] in EU_MEMBERS)
            markets[market] = {"tonnes": rec["tonnes"], "share_of_world_trade": rec["tonnes"] / world["tonnes"],
                               "from_world_leader": None if own else rec["share_from_world_leader"], "largest_supplier": top["name"],
                               "largest_supplier_share": top["share"]}
        shares = [m["from_world_leader"] for m in markets.values() if m["from_world_leader"] is not None]
        trade[key] = {"label": exposure["products"][key]["label"], "codes": exposure["products"][key]["codes"],
                      "world_tonnes": world["tonnes"], "export_hhi": world["hhi"], "leader": now["world_leader"],
                      "leader_share": world["top"][0]["share"], "leader_share_base_year": then["world"]["top"][0]["share"],
                      "leader_base_year": then["world_leader"], "markets": markets,
                      "top_exporters": [(t["name"], t["share"]) for t in world["top"]],
                      "markets_led_by_leader": sum(1 for m in markets.values() if m["largest_supplier"] == now["world_leader"]),
                      "lowest_market_share": min(shares), "highest_market_share": max(shares)}

    india_now, india_then = (exposure["by_year"][y]["ferroniobium"]["markets"]["India"] for y in (year, base))
    nb_detail = {"india_tonnes": india_now["tonnes"], "india_via_hubs": sum(t["share"] for t in india_now["top"] if t["name"] in HUBS),
                 "india_largest_base_year": india_then["top"][0]["name"], "india_largest_share_base_year": india_then["top"][0]["share"],
                 "hub_share_of_world_exports": sum(s for n, s in trade["ferroniobium"]["top_exporters"] if n in HUBS),
                 "hubs_listed": [n for n, _ in trade["ferroniobium"]["top_exporters"] if n in HUBS]}
    cr = inputs["chromium"]
    fe = cr["ferrochrome_2023_t"]
    icda_total = sum(cr["icda_2025_kt"].values())
    chromium = {"china_ferrochrome_share_2023": fe["China"] / fe["World"], "south_africa_ferrochrome_share_2023": fe["South Africa"] / fe["World"],
                "china_ferrochrome_share_2025_icda": cr["icda_2025_kt"]["China"] / icda_total, "icda_total_2025_kt": icda_total,
                "south_africa_ore_share_of_mining": mine["chromium"]["leader_share"],
                "south_africa_ore_share_of_trade": trade["chromium_ore"]["leader_share"],
                "china_share_of_ore_imports": trade["chromium_ore"]["markets"]["China"]["share_of_world_trade"],
                "china_ferrochrome_imports_t": trade["ferrochromium"]["markets"]["China"]["tonnes"],
                "south_africa_ore_exports_t": trade["chromium_ore"]["leader_share"] * trade["chromium_ore"]["world_tonnes"],
                "south_africa_ore_output_kt": inputs["mine_production_2024"]["chromium"]["rows"]["South Africa"],
                "icda_south_africa_ore_share_2025": cr["icda_ore_2025_kt"]["South Africa"] / sum(cr["icda_ore_2025_kt"].values()),
                "icda_ore_total_2025_kt": sum(cr["icda_ore_2025_kt"].values())}
    nickel = {"indonesia_mine_share": mine["nickel"]["leader_share"], "indonesia_ferronickel_trade_share": trade["ferronickel"]["leader_share"],
              "indonesia_ferronickel_trade_share_base_year": trade["ferronickel"]["leader_share_base_year"],
              "china_share_of_ferronickel_imports": trade["ferronickel"]["markets"]["China"]["share_of_world_trade"],
              "world_ferronickel_tonnes": trade["ferronickel"]["world_tonnes"],
              "world_ferronickel_tonnes_base_year": exposure["by_year"][base]["ferronickel"]["world"]["tonnes"]}
    bi = inputs["base_inputs"]
    ore, coal = bi["iron_ore_usable_2024_kt"], bi["met_coal_exports_2024_mt"]
    base_inputs = {"australia_share_of_iron_ore_output": ore["Australia"] / ore["World"], "brazil_share_of_iron_ore_output": ore["Brazil"] / ore["World"],
                   "australia_share_of_met_coal_exports": coal["Australia"] / coal["Total"],
                   "top_two_share_of_iron_ore_exports": bi["iron_ore_trade_2025"]["exporter_shares"]["Australia"] + bi["iron_ore_trade_2025"]["exporter_shares"]["Brazil"]}
    rv = inputs["revisions_of_2024"]
    revisions = {"vanadium_china_share_mcs2025": rv["vanadium_china"]["mcs2025"] / rv["vanadium_china"]["world_mcs2025"],
                 "vanadium_china_share_mcs2026": rv["vanadium_china"]["mcs2026"] / rv["vanadium_china"]["world_mcs2026"],
                 "chromium_south_africa_share_mcs2025": rv["chromium_south_africa"]["mcs2025"] / rv["chromium_south_africa"]["world_mcs2025"],
                 "chromium_south_africa_share_mcs2026": rv["chromium_south_africa"]["mcs2026"] / rv["chromium_south_africa"]["world_mcs2026"]}

    nb, ni, fc = trade["ferroniobium"], trade["ferronickel"], trade["ferrochromium"]
    checks = [
        (mine["niobium"]["leader"] == "Brazil" and 0.92 < mine["niobium"]["leader_share"] < 0.94, "Brazil's share of niobium mining is no longer 93%"),
        (nb["leader"] == "Brazil" and all(m["largest_supplier"] == "Brazil" for m in nb["markets"].values()) and nb["lowest_market_share"] > 0.5,
         "Brazil is no longer the largest ferroniobium supplier of every market, with more than half of each"),
        (ni["leader"] == "Indonesia" and 0.925 <= ni["leader_share"] < 0.935 and ni["markets"]["United States"]["from_world_leader"] == 0
         and ni["markets"]["China"]["from_world_leader"] > 0.95 and ni["markets"]["China"]["share_of_world_trade"] > 0.9,
         "the ferronickel sentences in the deck no longer match the data"),
        (fc["leader"] == "South Africa" and fc["markets"]["Japan"]["largest_supplier"] == "Kazakhstan", "the ferrochromium reading has changed"),
        (0.48 < chromium["china_ferrochrome_share_2023"] < 0.5, "China's 2023 ferrochromium share no longer reproduces the published 49%"),
        (chromium["south_africa_ore_share_of_trade"] > 0.8 > 0.5 > chromium["south_africa_ore_share_of_mining"] > 0.44,
         "South Africa's shares of chromium ore mining and trade no longer read as the page states"),
        ([n for n, _ in trade["ferrovanadium"]["top_exporters"][:3]] == ["Austria", "China", "Czechia"] and mine["vanadium"]["leader"] == "China"
         and mine["vanadium"]["leader_share"] > 0.7, "the vanadium contrast between mining and ferrovanadium trade has changed"),
        (nb["markets_led_by_leader"] == 6 and fc["markets_led_by_leader"] == 5 and trade["manganese_ore"]["markets_led_by_leader"] == 5,
         "the counts of markets whose largest supplier is the world leader have changed"),
        (nb_detail["india_largest_base_year"] == "Singapore" and nb_detail["hubs_listed"] == list(HUBS) and 0.3 < nb_detail["india_via_hubs"] < 0.4,
         "the re-export reading for ferroniobium has changed"),
        (chromium["south_africa_ore_exports_t"] / 1000 > chromium["south_africa_ore_output_kt"], "South Africa's recorded ore exports no longer exceed the USGS output figure"),
        (mine["nickel"]["leader"] == "Indonesia" and 0.6 < mine["nickel"]["leader_share"] < 0.65, "Indonesia's share of nickel mining is no longer 62%"),
        (ni["markets"]["Japan"]["from_world_leader"] < 0.01 and ni["markets"]["India"]["largest_supplier"] == "Indonesia"
         and ni["markets"]["South Korea"]["largest_supplier"] == "Indonesia", "the ferronickel reading for Japan, India or South Korea has changed"),
        (mine["molybdenum"]["leader_share"] < mine["manganese"]["leader_share"] < mine["chromium"]["leader_share"] < 0.5,
         "the order of the chromium, manganese and molybdenum mine shares has changed"),
        (abs(sum(inputs["nickel"]["first_use_2024"].values()) - 1) < 0.005, "the nickel first-use shares do not add to 100%"),
    ]
    for ok, message in checks:
        if not ok:
            raise SystemExit("steel-alloys page text no longer matches the data: " + message)
    content_in = load(CONTENT)
    contained = contained_metal(exposure, content_in, mine)
    by_code = exposure["exporters_by_code"]["codes"]
    # manganese ore: at these grades the trade record for South Africa carries more manganese than USGS has it mining
    mo = contained["manganese_ore"]
    sa_ore = by_code["260200"]["South Africa"] * content_in["manganese_ore_grade_2023"]["origins"]["South Africa"]
    sa_mine = inputs["mine_production_2024"]["manganese"]["rows"]["South Africa"] * 1000
    mo["south_africa_contained_over_its_mine_output"] = sa_ore / sa_mine
    mo["contained_over_mine_output"] = [(mo["contained_t"][0] - max(sa_ore - sa_mine, 0)) / mo["mine_output_t"], mo["contained_t"][1] / mo["mine_output_t"]]
    # how large the US sample is beside what each origin exports, for the two origins the ferrochromium result rests on
    us41 = content_in["codes"]["720241"]["origins"]
    sample = {c: us41[c]["gross_t"] / by_code["720241"][c] for c in ("South Africa", "Kazakhstan")}
    # ferronickel with Indonesian nickel pig iron at 10% nickel, the lowest grade the customs definition admits
    idt = by_code["720260"]["Indonesia"]
    fn_c = contained["ferronickel"]
    others_mid = (fn_c["contained_t"][0] + fn_c["contained_t"][1]) / 2 - idt * sum(content_in["codes"]["720260"]["origins"]["Indonesia"]["range"]) / 2
    extras = {"us_sample_share_of_exports_720241": sample, "indonesia_share_of_nickel_at_10_per_cent": idt * 0.10 / (idt * 0.10 + others_mid),
              "ferroniobium_at_documented_range_t": [contained["ferroniobium"]["gross_t"] * v for v in content_in["codes"]["720293"]["documented_range"]]}
    fcc, fnc = contained["ferrochromium"], contained["ferronickel"]
    content_checks = [
        ([e["name"] for e in fcc["exporters"][:2]] == ["South Africa", "Kazakhstan"]
         and fcc["exporters"][0]["contained_share"][1] < fcc["exporters"][0]["gross_share"]
         and fcc["exporters"][1]["contained_share"][0] > fcc["exporters"][1]["gross_share"],
         "ferrochromium: South Africa's share no longer falls, or Kazakhstan's no longer rises, in contained chromium"),
        (fnc["exporters"][0]["name"] == "Indonesia" and 0.8 < fnc["exporters"][0]["contained_share"][0]
         and fnc["exporters"][0]["contained_share"][1] < fnc["exporters"][0]["gross_share"],
         "ferronickel: Indonesia's share in contained nickel has left the range the page describes"),
        (all(abs(v["exporters"][0]["contained_share"][0] - v["exporters"][0]["gross_share"]) < 0.03 and
             abs(v["exporters"][0]["contained_share"][1] - v["exporters"][0]["gross_share"]) < 0.03
             for k, v in contained.items() if k in ("ferroniobium", "ferromanganese", "ferromolybdenum")),
         "an alloy described as little changed by the conversion now changes by more than three points"),
    ]
    for ok, message in content_checks:
        if not ok:
            raise SystemExit("steel-alloys page text no longer matches the data: " + message)
    return {"trade_year": int(year), "base_year": int(base), "mine_2024": mine, "trade_by_weight": trade, "ferroniobium_detail": nb_detail,
            "contained_metal_2024": contained, "contained_metal_notes": extras,
            "chromium": chromium, "nickel": nickel,
            "base_inputs": base_inputs, "revisions_of_2024": revisions}


def link(sources, key, label=None):
    s = sources[key]
    return f'<a href="{escape(s["url"], quote=True)}">{escape(label or s["title"])}</a>.'


def chart_exposure(trade):
    """Share of each market's imports that comes from the world's leading exporter, for three alloys."""
    left, plot, bar, step, head = 118, 300, 14, 19, 26
    out, y = [], 4
    body = []
    for key in CHARTED:
        t = trade[key]
        body.append(f'<text x="4" y="{y + 14}" fill="{INK}" font-weight="600">{escape(t["label"].split(",")[0])}: share bought from {escape(t["leader"])}</text>')
        y += head
        for market in MARKETS:
            v = t["markets"][market]["from_world_leader"]
            w = max(v * plot, 1.0)
            r = min(3, w / 2)
            d = f"M{left} {y}h{w - r:.1f}a{r} {r} 0 0 1 {r} {r}v{bar - 2 * r:.1f}a{r} {r} 0 0 1 -{r} {r}h-{w - r:.1f}z"
            body.append(f'<text x="{left - 8}" y="{y + 11}" fill="{INK}" text-anchor="end">{escape(market)}</text>'
                        f'<path d="{d}" fill="{TEAL}"><title>{escape(market)}: {v:.0%} of {escape(t["label"].lower())} imports from {escape(t["leader"])}</title></path>'
                        f'<text x="{left + w + 6:.1f}" y="{y + 11}" fill="{INK}">{v:.0%}</text>')
            y += step
        y += 10
    out.append(f'<svg viewBox="0 0 520 {y}" role="img" aria-label="Share of imports from the world\'s leading exporter, by market, 2024" style="{FONT};font-size:12.5px">')
    out.append(f'<line x1="{left}" x2="{left}" y1="24" y2="{y - 8}" stroke="{RULE}"/>')
    out += body
    out.append("</svg>")
    return "".join(out)


def render(inputs, r):
    src = inputs["sources"]
    mine, trade, cr, ni, bi_r, rev = r["mine_2024"], r["trade_by_weight"], r["chromium"], r["nickel"], r["base_inputs"], r["revisions_of_2024"]
    nbi, vi, cri, nii, om, gr, bi = (inputs[k] for k in ("niobium", "vanadium", "chromium", "nickel", "other_metals", "grades", "base_inputs"))

    def q(text):
        return escape(text, quote=False)

    mine_rows = [row(m.capitalize(), [f'{mine[m]["leader"]} {pct(mine[m]["leader_share"])}', f'{mine[m]["second"]} {pct(mine[m]["second_share"])}',
                                      f'{mine[m]["world"]:,}', mine[m]["unit"]]) for m in METALS]

    def cell(t, market):
        m = t["markets"][market]
        text = "own exporter" if m["from_world_leader"] is None else pct(m["from_world_leader"])
        if m["largest_supplier"] != t["leader"]:
            text += f' ({m["largest_supplier"]} {pct(m["largest_supplier_share"])})'
        return text

    exposure_rows = [row(trade[k]["label"], [f'{trade[k]["world_tonnes"] / 1000:,.0f}', f'{trade[k]["leader"]} {pct(trade[k]["leader_share"])}']
                         + [cell(trade[k], m) for m in MARKETS]) for k in PRODUCTS]
    fe = cri["ferrochrome_2023_t"]
    ferrochrome_rows = [row(c, [f'{fe[c] / 1e6:.2f}', pct(fe[c] / fe["World"])]) for c in fe if c != "World"]
    use = nii["first_use_2024"]
    grade_rows = ["<tr>" + f'<th scope="row">{escape(g["grade"])}</th>'
                  + "".join(f'<td class="n">{escape(g[k]) or "—"}</td>' for k in ("chromium", "nickel", "molybdenum", "vanadium", "niobium"))
                  + f'<td>{link(src, g["source"])}</td></tr>' for g in gr["rows"]]
    coal = bi["met_coal_exports_2024_mt"]
    ore_t = bi["iron_ore_trade_2025"]

    tr = load(TRADE)
    tyear = tr["years"][-1]
    trade_rows = []
    for code, info in tr["codes"].items():
        item = tr["years_data"][str(tyear)][code]
        top = next(iter(item["exporters"]), None)
        lead = f'{top["name"]} · {top["share"]:.0%}' if top else "not available"
        cells = (f'{info["title"]} ({code})', f'USD {item["world_usd"] / 1e6:,.0f} million', lead, inputs["trade_boundaries"][code])
        trade_rows.append(f'<tr data-trade-code="{escape(code)}">' + "".join(f"<td>{escape(c)}</td>" for c in cells) + "</tr>")

    nb, fc, fn, fv, co = (trade[k] for k in ("ferroniobium", "ferrochromium", "ferronickel", "ferrovanadium", "chromium_ore"))
    nd, coal2 = r["ferroniobium_detail"], bi["met_coal_exports_2024_mt_australian_table"]
    fv_top = fv["top_exporters"]
    values = {
        "title": escape(TITLE), "deck": escape(DECK), "date": inputs["version"], "trade_year": r["trade_year"], "base_year": r["base_year"],
        "mine_rows": "\n".join(mine_rows), "exposure_rows": "\n".join(exposure_rows), "chart_exposure": chart_exposure(trade),
        "nb_mine": pct(mine["niobium"]["leader_share"]), "nb_trade": pct(nb["leader_share"]), "nb_trade_base": pct(nb["leader_share_base_year"]),
        "nb_low": pct(nb["lowest_market_share"]), "nb_high": pct(nb["highest_market_share"]),
        "nb_us": pct(nb["markets"]["United States"]["from_world_leader"]), "nb_cn": pct(nb["markets"]["China"]["from_world_leader"]),
        "nb_cn_take": pct(nb["markets"]["China"]["share_of_world_trade"]),
        "nb_capacity": f'{nbi["capacity_2025_t"]:,}', "nb_cap_br": pct(nbi["capacity_share_brazil"]), "nb_cap_ca": pct(nbi["capacity_share_canada"]),
        "nb_producers": q(nbi["producers"]), "cbmm_cap": f'{nbi["cbmm_capacity_t_ferroniobium_equivalent"]:,}',
        "cbmm_sales": f'{nbi["cbmm_sales_2025_t_ferroniobium_equivalent"]:,}', "cmoc_t": f'{nbi["cmoc_2025_t_niobium"]:,}',
        "cbmm_quote": q(nbi["cbmm_capacity_quote"]), "nb_us_use": q(nbi["us_end_use"]), "nb_world_use": q(nbi["world_steel_share_2022"]),
        "nb_recycling": q(nbi["recycling"]),
        "v_mine": pct(mine["vanadium"]["leader_share"]), "v_trade_leader": fv["leader"], "v_trade": pct(fv["leader_share"]),
        "v_coproduct": q(vi["usgs_coproduct"]), "v_slag": pct(vi["vanitec_split"]["steelmaking_slag"]), "v_primary": pct(vi["vanitec_split"]["primary_mines"]),
        "v_secondary": pct(vi["vanitec_split"]["secondary"]), "v_us_use": q(vi["us_use"]), "v_sub": q(vi["substitution"]), "v_sub_time": q(vi["substitution_time"]),
        "v_inter": q(vi["usgs_interchangeable"]),
        "cr_mine": pct(mine["chromium"]["leader_share"]), "cr_ore_trade": pct(co["leader_share"]), "cr_cn_ore": pct(cr["china_share_of_ore_imports"]),
        "cr_cn_fe": pct(cr["china_ferrochrome_share_2023"]), "cr_cn_fe_2025": pct(cr["china_ferrochrome_share_2025_icda"]),
        "cr_cn_fe_imports": f'{cr["china_ferrochrome_imports_t"] / 1e6:.1f}', "cr_fe_trade": pct(fc["leader_share"]),
        "cr_jp": pct(fc["markets"]["Japan"]["largest_supplier_share"]), "cr_sa_change": cri["icda_south_africa_change_2025"].replace("-", "").replace("%", ""),
        "ferrochrome_rows": "\n".join(ferrochrome_rows), "cr_use": q(cri["oecd_use"]), "cr_exports": q(cri["oecd_exports"]),
        "cr_sub": q(cri["usgs_substitute"]), "cr_stainless": q(cri["stainless_minimum"]), "cr_recycling": q(cri["usgs_recycling"]),
        "ni_mine": pct(ni["indonesia_mine_share"]), "ni_trade": pct(ni["indonesia_ferronickel_trade_share"]),
        "ni_trade_base": pct(ni["indonesia_ferronickel_trade_share_base_year"]), "ni_cn_take": pct(ni["china_share_of_ferronickel_imports"]),
        "ni_world": f'{ni["world_ferronickel_tonnes"] / 1e6:.1f}', "ni_world_base": f'{ni["world_ferronickel_tonnes_base_year"] / 1e6:.1f}',
        "ni_cn": pct(fn["markets"]["China"]["from_world_leader"]), "ni_in": pct(fn["markets"]["India"]["from_world_leader"]),
        "ni_eu": pct(fn["markets"]["European Union"]["from_world_leader"]),
        "ni_stainless": pct(use["Stainless steel"]), "ni_batteries": pct(use["Batteries"]), "ni_us_use": q(nii["us_use"]),
        "ni_refined": q(nii["oecd_refined"]), "ni_ban": q(nii["oecd_ban"]), "ni_recycling": q(nii["us_recycling"]),
        "mn_mine": pct(mine["manganese"]["leader_share"]), "mn_second": f'{mine["manganese"]["second"]} {pct(mine["manganese"]["second_share"])}',
        "mn_sub": q(om["manganese_substitute"]), "mo_mine": pct(mine["molybdenum"]["leader_share"]), "mo_sub": q(om["molybdenum_substitute"]),
        "mo_recycling": q(om["molybdenum_recycling"]), "nb_sub": q(om["niobium_substitute"]), "nb_sub_caveat": q(om["niobium_substitute_caveat"]),
        "grade_rows": "\n".join(grade_rows), "a572_scope": q(gr["a572_scope"]), "micro_lo": f'{gr["microalloy_range_pct"][0]:g}', "micro_hi": f'{gr["microalloy_range_pct"][1]:g}',
        "micro_g_lo": f'{gr["microalloy_range_pct"][0] * 10000:.0f}', "micro_g_hi": f'{gr["microalloy_range_pct"][1] * 10000:.0f}',
        "grades_count": q(gr["grades_count"]),
        "ore_au": pct(bi_r["australia_share_of_iron_ore_output"]), "ore_br": pct(bi_r["brazil_share_of_iron_ore_output"]),
        "ore_x_au": pct(ore_t["exporter_shares"]["Australia"]), "ore_x_br": pct(ore_t["exporter_shares"]["Brazil"]), "ore_m_cn": pct(ore_t["china_import_share"]),
        "ore_two": pct(bi_r["top_two_share_of_iron_ore_exports"]), "coal_au": pct(bi_r["australia_share_of_met_coal_exports"]),
        "coal_au_mt": coal["Australia"], "coal_total": coal["Total"], "coal_ru": coal["Russia"], "coal_us": coal["United States"], "coal_mn": coal["Mongolia"],
        "scrap": q(bi["scrap_restrictions"]),
        "rev_v_old_t": f'{inputs["revisions_of_2024"]["vanadium_china"]["mcs2025"]:,}', "rev_v_new_t": f'{inputs["revisions_of_2024"]["vanadium_china"]["mcs2026"]:,}',
        "rev_cr_old_t": f'{inputs["revisions_of_2024"]["chromium_south_africa"]["mcs2025"] / 1000:.1f}',
        "rev_cr_new_t": f'{inputs["revisions_of_2024"]["chromium_south_africa"]["mcs2026"] / 1000:.1f}',
        "trade_rows": "\n".join(trade_rows), "value_year": tyear,
        "in_t": f'{nd["india_tonnes"]:,}', "in_hubs": pct(nd["india_via_hubs"]), "in_base": pct(nd["india_largest_share_base_year"]),
        "nb_hubs": pct(nd["hub_share_of_world_exports"]), "fv_1": f"{fv_top[0][0]} ({pct(fv_top[0][1])})", "fv_2": f"{fv_top[1][0]} ({pct(fv_top[1][1])})",
        "fv_3": f"{fv_top[2][0]} ({pct(fv_top[2][1])})", "mo_trade_leader": trade["ferromolybdenum"]["leader"], "mo_trade": pct(trade["ferromolybdenum"]["leader_share"]),
        "cr_sa_x": f'{cr["south_africa_ore_exports_t"] / 1e6:.1f}', "cr_sa_out": f'{cr["south_africa_ore_output_kt"] / 1000:.1f}',
        "cr_icda_sa": pct(cr["icda_south_africa_ore_share_2025"]), "cr_icda_total": f'{cr["icda_ore_total_2025_kt"] / 1000:.0f}',
        "cr_restrictions": q(cri["oecd_restrictions"]), "cr_potential": q(cri["usgs_potential"]),
        "nb_myb_world": f'{nbi["yearbook_2022_t_niobium"]["world"]:,}', "nb_myb_brazil": f'{nbi["yearbook_2022_t_niobium"]["brazil"]:,}',
        "taboca_t": f'{nbi["third_brazilian_producer_2022_t_gross"]:,}',
        "coal2_world": coal2["World"], "coal2_mn": coal2["Mongolia"], "coal2_ru": coal2["Russia"],
        "references": "\n".join(f'    <li><a href="{escape(s["url"], quote=True)}">{escape(s["title"])}</a> · {escape(s["vintage"])}</li>' for s in src.values()),
    }
    labels = {"mcs_niobium": "USGS, niobium, 2026 edition", "mcs_vanadium": "USGS, vanadium, 2026 edition", "mcs_chromium": "USGS, chromium, 2026 edition",
              "mcs_manganese": "USGS, manganese, 2026 edition", "mcs_nickel": "USGS, nickel, 2026 edition", "mcs_molybdenum": "USGS, molybdenum, 2026 edition",
              "mcs_iron_ore": "USGS, iron ore, 2026 edition", "mcs2025_vanadium": "USGS, vanadium, 2025 edition", "mcs2025_chromium": "USGS, chromium, 2025 edition",
              "outlook": "USGS World Minerals Outlook, November 2026", "myb_niobium": "USGS Minerals Yearbook 2022, niobium",
              "myb_chromium": "USGS Minerals Yearbook 2023, chromium", "myb_vanadium": "USGS Minerals Yearbook 2023, vanadium",
              "pp1802u": "USGS Professional Paper 1802-U", "cbmm": "CBMM, 2025 Sustainability Report", "cmoc": "CMOC, 2025 Annual Report",
              "icda": "International Chromium Development Association", "vanitec": "Vanitec", "oecd_outlook": "OECD Steel Outlook 2026",
              "nickel_institute": "Nickel Institute, 2025", "req": "Australian Government, Resources and Energy Quarterly, September 2026",
              "nrcan": "Natural Resources Canada, Coal facts", "worldsteel_grades": "World Steel Association", "worldstainless": "worldstainless",
              "astm_a572": "ASTM A572/A572M", "baker": "Baker (2015)", "wco_ch72": "WCO, HS 2017, Chapter 72", "wco_ch26": "WCO, HS 2017, Chapter 26",
              "wco_ch27": "WCO, HS 2017, Chapter 27", "baci": "CEPII BACI V202601"}
    values.update({"s_" + k: link(src, k, v) for k, v in labels.items()})
    cm = r["contained_metal_2024"]

    def span(pair, f):
        a, b = f(pair[0]), f(pair[1])
        return a if a == b else f"{a} to {b}"

    content_rows = []
    for key in ("ferroniobium", "ferrovanadium", "ferrochromium", "ferromanganese", "ferronickel", "ferromolybdenum", "manganese_ore"):
        c = cm[key]
        lead = c["exporters"][0]
        content_rows.append(row(trade[key]["label"], [
            f'{c["gross_t"] / 1000:,.0f}', span(c["contained_t"], lambda v: f"{v / 1000:,.0f}") + " of " + c["metal"],
            pct(c["share_of_tonnage_with_measured_content"]), f'{lead["name"]} {pct(lead["gross_share"])}', span(lead["contained_share"], pct),
            span(c["contained_over_mine_output"], pct) if c["contained_over_mine_output"] else "—"]))
    fcc, fnc, fvc, fmc, nbc, moc = (cm[k] for k in ("ferrochromium", "ferronickel", "ferrovanadium", "manganese_ore", "ferroniobium", "ferromolybdenum"))
    cinp = load(CONTENT)
    cr41 = cinp["codes"]["720241"]["origins"]
    values.update({
        "content_rows": "\n".join(content_rows),
        "c_sa_gross": pct(fcc["exporters"][0]["gross_share"]), "c_sa_cont": span(fcc["exporters"][0]["contained_share"], pct),
        "c_kz_gross": pct(fcc["exporters"][1]["gross_share"]), "c_kz_cont": span(fcc["exporters"][1]["contained_share"], pct),
        "c_sa_grade": pct(cr41["South Africa"]["content"]), "c_kz_grade": pct(cr41["Kazakhstan"]["content"]),
        "c_id_gross": pct(fnc["exporters"][0]["gross_share"]), "c_id_cont": span(fnc["exporters"][0]["contained_share"], pct),
        "c_id_usgs": pct(cinp["codes"]["720260"]["origins"]["Indonesia"]["content"], 1), "c_id_company": pct(cinp["codes"]["720260"]["origins"]["Indonesia"]["range"][0], 1),
        "c_id_at10": pct(r["contained_metal_notes"]["indonesia_share_of_nickel_at_10_per_cent"]),
        "c_sa_sample": pct(r["contained_metal_notes"]["us_sample_share_of_exports_720241"]["South Africa"]),
        "c_kz_sample": pct(r["contained_metal_notes"]["us_sample_share_of_exports_720241"]["Kazakhstan"]),
        "c_nb_t": f'{nbc["contained_t"][0] / 1000:,.0f}', "c_nb_range": span(r["contained_metal_notes"]["ferroniobium_at_documented_range_t"], lambda v: f"{v / 1000:,.0f}"),
        "c_mn_sa": f'{fmc["south_africa_contained_over_its_mine_output"]:.1f}',
        "c_fm_lead": pct(cm["ferromanganese"]["exporters"][0]["gross_share"]), "c_fm_cont": span(cm["ferromanganese"]["exporters"][0]["contained_share"], pct),
        "c_mo_lead": pct(moc["exporters"][0]["gross_share"]), "c_mo_cont": span(moc["exporters"][0]["contained_share"], pct),
        "c_fv_cont": span(fvc["exporters"][0]["contained_share"], pct),
        "s_icda_fc": link(cinp["sources"], "icda_ferrochrome", "International Chromium Development Association, ferrochrome"),
        "s_pp1802m": link(cinp["sources"], "usgs_pp1802m", "USGS Professional Paper 1802-M"),
        "c_ni_other": span(cinp["codes"]["720260"]["other_origins"], pct),
        "c_ni_t": span(fnc["contained_t"], lambda v: f"{v / 1e6:.1f}"), "c_ni_mine": span(fnc["contained_over_mine_output"], pct),
        "c_v_t": span(fvc["contained_t"], lambda v: f"{v / 1000:,.0f}"), "c_v_mine": span(fvc["contained_over_mine_output"], pct),
        "c_mn_ore_mine": span(fmc["contained_over_mine_output"], pct), "c_nb_mine": span(nbc["contained_over_mine_output"], pct),
        "c_ga_gross": pct(next(e for e in fmc["exporters"] if e["name"] == "Gabon")["gross_share"]),
        "c_ga_cont": pct(next(e for e in fmc["exporters"] if e["name"] == "Gabon")["contained_share"][0]),
        "c_gh_gross": pct(next(e for e in fmc["exporters"] if e["name"] == "Ghana")["gross_share"]),
        "c_gh_cont": pct(next(e for e in fmc["exporters"] if e["name"] == "Ghana")["contained_share"][0]),
        "s_census": link(cinp["sources"], "census", "US Census Bureau, import records by tariff line"),
        "s_usgs_indonesia": link(cinp["sources"], "usgs_indonesia", "USGS Minerals Yearbook 2024, Indonesia"),
        "s_nickel_industries": link(cinp["sources"], "nickel_industries", "Nickel Industries, Annual Report 2024"),
        "s_usgs_manganese": link(cinp["sources"], "usgs_manganese", "USGS Minerals Yearbook 2023, manganese"),
    })
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(values)


def build():
    inputs = load(INPUTS)
    results = evaluate(inputs)
    m, t = results["mine_2024"], results["trade_by_weight"]
    data = {
        "title": "Steel alloying metals", "h1": TITLE, "deck": DECK, "published": True, "version": inputs["version"],
        "chokepoint": {
            "product": "Steel alloying metals", "stage": "Niobium mining", "mechanism": "geological",
            "physics": "Two companies in Brazil and one in Canada produce nearly all niobium. Most of it goes into steel, at a few hundred grams per tonne",
            "holder": "Brazil",
            "share": (f'{pct(m["niobium"]["leader_share"])} of niobium mined (2024); Brazil supplied {pct(t["ferroniobium"]["lowest_market_share"])} to '
                      f'{pct(t["ferroniobium"]["highest_market_share"])} of ferroniobium imports in six large markets'),
            # "estimate" until the source ledger carries the quoted USGS row; the basis note gives it
            "control": "—", "conf": "estimate",
        },
        "sources": inputs["sources"],
        "inputs": {k: inputs[k] for k in inputs if k not in ("sources", "version", "note")},
        "content_inputs": load(CONTENT),
        "results": results,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    ARTICLE.write_text(render(inputs, results), encoding="utf-8", newline="\n")
    print("wrote steel_chain.json and steel-alloys-chain.html: Brazil %s of niobium mined, %s of ferroniobium trade; Indonesia %s of ferronickel trade (2024)"
          % (pct(m["niobium"]["leader_share"]), pct(t["ferroniobium"]["leader_share"]), pct(t["ferronickel"]["leader_share"])))


if __name__ == "__main__":
    build()
