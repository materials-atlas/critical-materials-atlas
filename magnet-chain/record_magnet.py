"""Build the magnet study and its evidence from pinned public inputs."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template


HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
TITLE = "Where rare-earth magnet supply can run short"
REVISION = "2026-11-24"
BASELINE_YEAR = 2024
STRESS_MONTHS = (4, 5, 6, 7, 8, 9)

SOURCES = {
    "iea": ("IEA, Rare Earth Elements (April 2026)", "https://www.iea.org/reports/rare-earth-elements/executive-summary"),
    "outlook": ("IEA, Global Critical Minerals Outlook 2026 release", "https://www.iea.org/news/supply-concentration-export-restrictions-and-declining-investment-put-critical-mineral-security-at-risk"),
    "doe": ("US Department of Energy, Rare Earth Permanent Magnets Supply Chain Assessment", "https://www.energy.gov/sites/default/files/2024-12/Neodymium%2520Magnets%2520Supply%2520Chain%2520Report%2520-%2520Final%5B1%5D.pdf"),
    "comext": ("Eurostat Comext DS-045409", "https://ec.europa.eu/eurostat/databrowser/view/ds-045409/default/table?lang=en"),
    "usgs": ("USGS Mineral Commodity Summaries 2026, World Mine Production and Reserves", "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-rare-earths_ver.1.2.pdf"),
    "history": ("USGS Data Series 140, rare earths, World production column", "https://www.usgs.gov/media/files/rare-earths-historical-statistics-data-series-140"),
    "bgs": ("BGS World Mineral Statistics, rare earth oxides", "https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-data-download/"),
    "baci": ("CEPII BACI V202601, based on UN Comtrade", "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"),
    "licensing": ("MOFCOM and customs, Announcement No. 18 of 2025", "https://english.mofcom.gov.cn/Policies/AnnouncementsOrders/art/2025/art_0dd87cbee7b045bf93fabe6ab2faceee.html"),
    "narva": ("Neo, first commercial automotive shipments from Narva, 14 September 2026", "https://www.neomaterials.com/neo-advances-commercial-production-magnet-facility/"),
    "expansion": ("Neo, European Integrated Magnet Project, 19 October 2026", "https://www.neomaterials.com/neos-european-integrated-magnet-project-selected-for-e126-million-grant-under-eu-innovation-fund/"),
    "blocks": ("Neo, Q3 2026 earnings transcript, project scope and block capacity", "https://www.neomaterials.com/wp-content/uploads/2026/11/NPM-Q3-2026-Earnings-Transcript.pdf"),
    "silmet": ("Neo, small-scale separation commissioning, 10 April 2026", "https://www.neomaterials.com/neo-successfully-commissions-heavy-rare-earth-separation-small-scale-production-line-in-europe/"),
    "solvay": ("Solvay, Q3 2025 earnings transcript, La Rochelle", "https://www.solvay.com/sites/solvay_solvay/files/2025-11/2025Q3%20Transcript%20with%20Q%26A%20for%20Webpage.pdf"),
    "lcm": ("Less Common Metals, strategic report for 2024", "https://find-and-update.company-information.service.gov.uk/company/02690088/filing-history/MzQ4MjgzMjE0NWFkaXF6a2N4/document"),
}

STAGES = (
    ("Mine and concentrate", "Magnet rare earths in mined output", 0.60,
     "Develop or source concentrate with suitable Nd, Pr, Dy or Tb content and a compatible processing route."),
    ("Separate and refine", "Refined magnet rare earths", 0.91,
     "Turn mixed feed into separated products of the required purity. Track light Nd/Pr and heavy Dy/Tb independently."),
    ("Make metal", "Rare-earth metals or metal intermediates", None,
     "Convert separated oxides or other precursors into usable metals. Availability depends on feedstock, purity and plant capability."),
    ("Make alloy", "Magnet-grade alloy", None,
     "Combine metals into a repeatable NdFeB alloy that meets the maker’s composition and process specifications."),
    ("Make and finish magnets", "Sintered permanent magnets", 0.94,
     "Sinter, machine, coat and qualify the magnet for the intended application. Blocks and finished customer parts have different capacity bases."),
)
TRADE_BOUNDARIES = {
    "850511": "Metal permanent magnets and articles for magnetisation, including products that contain no rare earths. Embedded magnets are in other customs lines.",
    "280530": "Rare-earth metals, scandium and yttrium, whether or not intermixed or interalloyed. The code cannot isolate NdPr or Dy/Tb supply or identify where material was separated.",
}
FACILITIES = (
    {"place": "La Rochelle, France", "stage": "Separate and refine", "operator": "Solvay",
     "date": "2025-04", "status": "Operator-reported NdPr oxide production",
     "product": "NdPr oxides for magnet applications",
     "nameplate_tonnes_per_year": None, "qualified_available_tonnes": None, "source": "solvay"},
    {"place": "Sillamäe, Estonia", "stage": "Separate and refine", "operator": "Neo Performance Materials",
     "date": "2026-04-10", "status": "Small-scale commissioning and first separated process solutions",
     "product": "Dy and Tb process solutions",
     "nameplate_tonnes_per_year": None, "qualified_available_tonnes": None, "source": "silmet"},
    {"place": "Ellesmere Port, United Kingdom", "stage": "Make metal and alloy", "operator": "Less Common Metals",
     "date": "2024", "status": "Operator reported manufacturing and alloy sales during 2024",
     "product": "Light rare-earth metals and NdFeB alloys",
     "nameplate_tonnes_per_year": None, "qualified_available_tonnes": None, "source": "lcm"},
    {"place": "Narva, Estonia", "stage": "Make and finish magnets", "operator": "Neo Performance Materials",
     "date": "2026-09-14", "status": "Commercial production and first deliveries for an automotive programme",
     "product": "Sintered NdFeB magnets",
     "nameplate_tonnes_per_year": 2000, "qualified_available_tonnes": None, "source": "narva"},
    {"place": "Narva, Estonia (Phase 1B)", "stage": "Make and finish magnets", "operator": "Neo Performance Materials",
     "date": "2026-10-19", "status": "Announced expansion subject to investment and grant conditions",
     "product": "Incremental sintered magnet block capacity across end uses",
     "nameplate_tonnes_per_year": 3000, "qualified_available_tonnes": None, "source": "expansion"},
)


def read_json(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def split_origins(row):
    """Convert reported net mass from 100 kg to tonnes, retaining nominal euro values."""
    result = {}
    for key, partner in (("china", "CN"), ("extra_eu", "EXT_EU27_2020")):
        result[key] = {
            "tonnes": row[partner]["QUANTITY_IN_100KG"]["value"] / 10,
            "euros": row[partner]["VALUE_IN_EUROS"]["value"],
        }
    return result


def trade_summary(rows):
    total = {origin: {unit: sum(row[origin][unit] for row in rows) for unit in ("tonnes", "euros")}
             for origin in ("china", "extra_eu")}
    china, extra_eu = total["china"], total["extra_eu"]
    mass_share = china["tonnes"] / extra_eu["tonnes"]
    return {
        **total, "other_origin_tonnes": extra_eu["tonnes"] - china["tonnes"],
        "china_mass_share": mass_share, "china_value_share": china["euros"] / extra_eu["euros"],
        "mass_hhi_bounds": [mass_share ** 2, mass_share ** 2 + (1 - mass_share) ** 2],
    }


def screen_trade(snapshot):
    annual = {period: trade_summary([split_origins(row)])
              for period, row in snapshot["annual"]["rows"].items()}
    monthly = {period: split_origins(row) for period, row in snapshot["monthly"]["rows"].items()}
    windows = {str(year): trade_summary([monthly[f"{year}-{month:02d}"] for month in STRESS_MONTHS])
               for year in (2024, 2025)}
    for year in windows:
        total = trade_summary([row for period, row in monthly.items() if period.startswith(year)])
        if abs(total["extra_eu"]["tonnes"] - annual[year]["extra_eu"]["tonnes"]) > 0.1:
            raise ValueError(f"Annual and monthly extra-EU mass disagree in {year}")
        if abs(total["china"]["tonnes"] - annual[year]["china"]["tonnes"]) > 0.1:
            raise ValueError(f"Annual and monthly China-origin mass disagree in {year}")
    return annual, monthly, windows


def calculate_bound(baseline):
    """Screen direct import mass and the additional blocks available under stated assumptions."""
    target = baseline["extra_eu"]["tonnes"]
    retained = baseline["other_origin_tonnes"]
    gap = baseline["china"]["tonnes"]
    phase_1b_annual = FACILITIES[-1]["nameplate_tonnes_per_year"]
    wind_share = 1 / 3
    duration = len(STRESS_MONTHS)
    non_wind_annual = phase_1b_annual - phase_1b_annual * wind_share
    block_ceiling = non_wind_annual * duration / 12
    cases = [{"case": "Reference imports", "mass_tonnes": target, "gross_unreplaced_tonnes": 0}]
    cases.append({"case": "Complete interruption", "mass_tonnes": retained, "gross_unreplaced_tonnes": gap})
    for factor in (0.5, 1.0):
        extra = min(gap, block_ceiling * factor)
        cases.append({
            "case": f"Interruption plus expansion at {factor:.0%} effective availability",
            "availability": factor,
            "credited_tonnes": extra, "mass_tonnes": retained + extra,
            "gross_unreplaced_tonnes": gap - extra,
        })
    return {
        "evidence": "modelled direct import mass bound",
        "reference": "April–September 2024 gross direct extra-EU imports of CN 85051110",
        "duration_months": duration,
        "china_direct_import_cut_fraction": 1,
        "direct_import_reference_tonnes": target,
        "stocks_existing_eu_output_and_new_imports_credited_tonnes": 0,
        "retained_other_origin_tonnes": retained,
        "announced_incremental_blocks_tonnes_per_year": phase_1b_annual,
        "offshore_wind_allocation_fraction": wind_share,
        "allocation_timing": "Annual nameplate and wind allocation prorated evenly across the year",
        "other_applications_block_ceiling_tonnes": block_ceiling,
        "effective_availability": "Joint fraction of ceiling convertible to compatible, qualified, timely, uncommitted magnet deliveries",
        "cases": [{**case, "share_of_reference_import_mass": case["mass_tonnes"] / target} for case in cases],
    }


def cells(label, *values, attrs=""):
    data = "".join(f"<td>{escape(str(value))}</td>" for value in values)
    return f'<tr{attrs}><th scope="row">{escape(str(label))}</th>{data}</tr>'


def tonnes(value):
    return f"{value:,.0f}"


def pct(value):
    return f"{value:.1%}"


def money(value):
    return f"${value / 1e9:.1f}B" if value >= 1e9 else f"${value / 1e6:.1f}M"


def render(record, trade, snapshot):
    annual = record["annual_imports"]
    windows = record["historical_windows"]
    model = record["six_month_bound"]
    trade_year = str(trade["years"][-1])
    trade_rows = []
    for code, item in trade["codes"].items():
        stats = trade["years_data"][trade_year][code]
        leader = stats["exporters"][0]
        trade_rows.append(cells(f"{item['title']} (HS {code})", money(stats["world_usd"]),
                                f"{leader['name']} · {leader['share']:.0%}", TRADE_BOUNDARIES[code],
                                attrs=f' data-trade-code="{code}"'))
    stage_map, stage_rows = [], []
    for stage, product, share, detail in STAGES:
        display = f"China {share:.0%}" if share is not None else "Comparable output share unavailable"
        stage_map.append(f'<li class="hop"><b>{escape(stage)}</b><span>{escape(product)}</span><strong>{display}</strong></li>')
        stage_rows.append(cells(stage, detail))
    annual_rows = [cells(year, tonnes(row["china"]["tonnes"]), tonnes(row["extra_eu"]["tonnes"]),
                         pct(row["china_mass_share"]), pct(row["china_value_share"]),
                         "–".join(f"{v:.3f}" for v in row["mass_hhi_bounds"]))
                   for year, row in annual.items()]
    window_rows = [cells(year, tonnes(row["china"]["tonnes"]), tonnes(row["other_origin_tonnes"]),
                         tonnes(row["extra_eu"]["tonnes"])) for year, row in windows.items()]
    monthly = record["monthly_imports"]
    pairs = [(monthly[f"2024-{month:02d}"]["china"]["tonnes"],
              monthly[f"2025-{month:02d}"]["china"]["tonnes"]) for month in STRESS_MONTHS]
    maximum = max(map(max, pairs))
    month_rows = [
        cells(name, tonnes(first), tonnes(second), f"{(second / first - 1) * 100:+.1f}%")
        for name, (first, second) in zip(("Apr", "May", "Jun", "Jul", "Aug", "Sep"), pairs)
    ]
    history_chart = "".join(
        f'<div class="comparison"><span>{name}</span><div>'
        f'<span class="bar baseline" style="width:{first / maximum:.1%}"></span>'
        f'<span class="bar event" style="width:{second / maximum:.1%}"></span></div></div>'
        for name, (first, second) in zip(("Apr", "May", "Jun", "Jul", "Aug", "Sep"), pairs)
    )
    model_rows = [
        cells(row["case"], tonnes(row["mass_tonnes"]),
              f'{100 * row["share_of_reference_import_mass"]:.1f}%',
              tonnes(row["gross_unreplaced_tonnes"])) for row in model["cases"]
    ]
    scenario_chart = "".join(
        f'<div class="scenario-line"><span>{label}</span><div class="scenario-track">'
        f'<span class="bar event" style="width:{row["share_of_reference_import_mass"]:.1%}"></span></div></div>'
        for label, row in zip(("Reference", "Interruption", "Half available", "Full ceiling"), model["cases"])
    )
    facility_rows = [
        cells(row["place"], row["date"], row["product"], row["status"],
              tonnes(row["nameplate_tonnes_per_year"]) if row["nameplate_tonnes_per_year"] is not None else "—")
        for row in FACILITIES
    ]
    first, event = windows["2024"], windows["2025"]
    template = Template((HERE / "study.template").read_text(encoding="utf-8"))
    return template.substitute(
        title=escape(TITLE), stage_map="\n".join(stage_map), stage_rows="\n".join(stage_rows),
        annual_rows="\n".join(annual_rows), window_rows="\n".join(window_rows),
        month_rows="\n".join(month_rows), model_rows="\n".join(model_rows),
        facility_rows="\n".join(facility_rows), history_chart=history_chart, scenario_chart=scenario_chart,
        china_decline=pct(1 - event["china"]["tonnes"] / first["china"]["tonnes"]),
        other_decline=pct(1 - event["other_origin_tonnes"] / first["other_origin_tonnes"]),
        annual_gain=pct(annual["2025"]["china"]["tonnes"] / annual["2024"]["china"]["tonnes"] - 1),
        gross_gap=tonnes(first["china"]["tonnes"]),
        block_ceiling=tonnes(model["other_applications_block_ceiling_tonnes"]),
        gap_offset=pct(model["other_applications_block_ceiling_tonnes"] / first["china"]["tonnes"]),
        comext_vintage=snapshot["annual"]["updated"][:10],
        trade_year=trade_year, trade_rows="\n".join(trade_rows),
        **{key: escape(value[1], quote=True) for key, value in SOURCES.items()},
    )


def main():
    snapshot = read_json("comext_audit.json")
    annual, monthly, windows = screen_trade(snapshot)
    pilot = read_json("magnet_pilot_evidence.json")
    trade = read_json("magnet_trade.json")
    record = {
        "title": TITLE, "revision": REVISION, "published": True,
        "chokepoint": {
            "product": "Rare-earth permanent magnets",
            "stage": "Separation, metals and sintered magnets",
            "mechanism": "capability",
            "physics": "Separated products, metals, alloys and magnets each need industrial capability. The binding stage depends on the grade, available routes and the shock.",
            "holder": "China (output)", "share": "91% of magnet rare-earth refining, 94% of sintered magnets (2024)", "control": "Apr 2025",
            "conf": "estimate", "research": True,
        },
        "sources": {key: {"title": label, "url": url} for key, (label, url) in SOURCES.items()},
        "physical_stages": [
            {"stage": stage, "denominator": scope, "china_share": share,
             "measure": "World physical output", "year": 2024, "source": "iea",
             "status": "IEA estimate" if share is not None else "Comparable share unavailable"}
            for stage, scope, share, _ in STAGES
        ],
        "other_production_measures": {
            "usgs_all_rare_earth_mine_reo_tonnes": {
                "2024": {"china": 270000, "world_rounded": 380000},
                "2025": {"china": 270000, "world_rounded": 390000},
                "source": "usgs",
            },
            "bgs_all_rare_earth_mine_reo_tonnes_2024": {
                **{key: pilot["bgs_mine_production"]["series"][-1][key]
                   for key in ("china_tonnes_reo", "world_tonnes_reo", "china_share")},
                "source": "bgs",
            },
            "iea_refining_china_2025": {"share": 0.85, "source": "outlook",
                                       "measure": "Top-country share of rare-earth refinery output"},
            "usgs_historical_world_reo_tonnes": {"1900": 1040, "2020": 243000, "source": "history"},
            "iea_sintered_magnet_share_anchors": {"2005": 0.50, "2024": 0.94, "source": "iea"},
        },
        "facilities": FACILITIES,
        "expansion_package": {
            "status": "Operator estimate, conditional on investment and grant agreement",
            "scope": "Separation, metallisation, Phase 1B magnet expansion and digital infrastructure",
            "estimated_package_eur": 400000000, "estimated_completion_years": [2, 3],
            "source": "expansion",
        },
        "imports": {"scope": "EU-27 gross extra-EU imports of CN 85051110 by declared origin",
                    "units": {"tonnes": "net mass", "euros": "nominal customs value"},
                    "snapshot": "comext_audit.json"},
        "annual_imports": annual, "monthly_imports": monthly, "historical_windows": windows,
        "six_month_bound": calculate_bound(windows[str(BASELINE_YEAR)]),
        "global_customs": {"snapshot": "magnet_trade.json", "boundaries": TRADE_BOUNDARIES},
    }
    page = render(record, trade, snapshot)
    (OUT / "magnet_chain.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (HERE / "magnet-chain.html").write_text(page, encoding="utf-8")
    print("Wrote magnet study and evidence")


if __name__ == "__main__":
    main()
