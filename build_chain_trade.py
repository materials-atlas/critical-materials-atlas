"""Master BACI extractor for the 10 ported value-chain pilots.

Reads the local BACI HS02 (2002-2016) and HS17 (2017-2024) archives ONCE and emits one
<base>_trade.json per chain in the same schema the shared renderer (chainview.js tradeRow)
expects: {source, years, vintage, codes, years_data, series}. Trade is context, not capability —
every code carries a boundary flag. Run from repo root: python extract_all_chains.py
"""
from __future__ import annotations
import csv, io, json, os, zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
COUNTRIES = os.path.join(ROOT, "raw", "baci", "country_codes_V202601.csv")
BATCHES = [
    ("HS02", range(2002, 2017), "BACI_HS02_V202601.zip", "BACI_HS02_Y{year}_V202601.csv"),
    ("HS17", range(2017, 2025), "BACI_HS17_V202601.zip", "BACI_HS17_Y{year}_V202601.csv"),
]
FORCE_ISO = {"490": "TW", "516": "NA"}
FORCE_NAME = {"TW": "Taiwan", "NA": "Namibia"}

# chain -> (out_dir, out_base, CODES{hs6: {title, boundary}})
CHAINS = {
    "solar": ("solar-chain", "solar", {
        "280461": {"title": "Silicon, >= 99.99% pure", "boundary": "Polysilicon feedstock (PV + semiconductor); the pure-silicon input, not the panel."},
        "854140": {"title": "Photosensitive / PV semiconductor devices", "boundary": "Cells and modules; the PV heading was reclassified in 2022, so later years shift codes."},
    }),
    "wind": ("wind-chain", "wind", {
        "850231": {"title": "Wind-powered generating sets", "boundary": "Complete turbines only; blades, nacelles and towers trade under generic parts and are mostly built locally."},
    }),
    "ev": ("ev-chain", "ev", {
        "870380": {"title": "Motor cars, only electric motor", "boundary": "HS2017 code; a finished EV's origin is its assembly plant, not the battery or magnet chain behind it."},
        "850760": {"title": "Lithium-ion accumulators", "boundary": "The pack/cells; origin is the cell plant, not the mine or refinery. HS2017 code, sparse before 2017."},
    }),
    "battery": ("battery-chain", "battery", {
        "850760": {"title": "Lithium-ion accumulators", "boundary": "Cells; customs origin is the assembly plant, not the refining midstream. HS2017 code, sparse before 2017."},
        "283691": {"title": "Lithium carbonate", "boundary": "A refined battery chemical; a trading/refining position, not the mine."},
    }),
    "magnet": ("magnet-chain", "magnet", {
        "850511": {"title": "Permanent magnets, of metal", "boundary": "NdFeB and other metal magnets; origin is the last shipment point, not where the ore was separated."},
        "280530": {"title": "Rare-earth metals, scandium and yttrium", "boundary": "Rare-earth metals; the concentrated separation stage is upstream and not visible in this line."},
    }),
    "nuclear": ("nuclear-chain", "nuclear", {
        "261210": {"title": "Uranium ores and concentrates", "boundary": "Mined concentrate only; conversion and enrichment are traded as services, invisible in customs data."},
        "284410": {"title": "Natural uranium and its compounds", "boundary": "Front-end uranium material; the enrichment chokepoint is a service, not a traded good."},
    }),
    "grid": ("grid-chain", "grid", {
        "850422": {"title": "Liquid-dielectric transformers, 650-10,000 kVA", "boundary": "Power transformers; origin is the assembly plant, and the years-long lead time is not visible in trade."},
        "740811": {"title": "Copper wire, cross-section > 6 mm", "boundary": "A conductor form; the metal is abundant, so this is availability of the traded form, not a chokepoint."},
    }),
    "heat_pump": ("heat-pump-chain", "heat_pump", {
        "841861": {"title": "Heat pumps (other than air conditioners)", "boundary": "HS2017 code; the binding constraint (skilled installation) is a domestic service, not a traded good."},
    }),
    "electrolyser": ("electrolyser-chain", "electrolyser", {
        "854330": {"title": "Machines for electrolysis / electroplating", "boundary": "Electrolysers scatter across machinery headings; PEM and alkaline are not separable here."},
        "711049": {"title": "Platinum-group metals, semi-manufactured", "boundary": "A PGM basket that includes iridium; the specific iridium line cannot be isolated."},
    }),
    "data_centre": ("data-centre-chain", "data_centre", {
        "847150": {"title": "Automatic data-processing units (servers)", "boundary": "Server hardware only; the binding inputs (electricity, grid connection) are not traded goods."},
        "854231": {"title": "Electronic integrated circuits, processors", "boundary": "Processors; a chip chokepoint of their own (see the silicon-chip chain), shown as context."},
    }),
    "graphite": ("graphite-chain", "graphite", {
        "250410": {"title": "Natural graphite, powder or flakes", "boundary": "Raw flake; battery-anode-grade spherical graphite is not a separate customs line."},
        "250490": {"title": "Natural graphite, other", "boundary": "Lump/other natural graphite; grade and end use not distinguished."},
        "380110": {"title": "Artificial graphite", "boundary": "Synthetic graphite (all grades); anode-grade not separable from electrode/other uses."},
    }),
    "fluorine": ("fluorine-chain", "fluorine", {
        "252922": {"title": "Fluorspar, > 97% CaF2 (acid-grade)", "boundary": "The chemical-grade feed to HF; the downstream fluorochemicals are not traded under this line."},
        "252921": {"title": "Fluorspar, <= 97% CaF2 (met-grade)", "boundary": "Metallurgical-grade fluorspar; a flux, distinct from the acid-grade chemical feed."},
        "281111": {"title": "Hydrogen fluoride (hydrofluoric acid)", "boundary": "The gateway acid; chip gases, LiPF6 and refrigerants made from it sit in broad chemical headings."},
    }),
    "steel": ("steel-chain", "steel", {
        "260111": {"title": "Iron ores, non-agglomerated", "boundary": "The abundant, diversified raw ore; DRI-grade vs ordinary ore is not distinguished."},
        "270112": {"title": "Bituminous coal", "boundary": "Includes metallurgical coking coal, but customs does not separate it from thermal coal here."},
        "720712": {"title": "Semi-finished iron/steel, rectangular", "boundary": "Semi-finished steel; a trading/processing position, not the smelting map."},
    }),
    "tin": ("tin-chain", "tin", {
        "260900": {"title": "Tin ores and concentrates", "boundary": "Cassiterite; some feed (e.g. Myanmar Wa) routes through China and is not visible as origin."},
        "800110": {"title": "Unwrought tin, not alloyed", "boundary": "Refined tin metal; origin is the smelter, not the (sometimes conflict-linked) mine."},
    }),
    "tantalum": ("tantalum-chain", "tantalum", {
        "261590": {"title": "Niobium/tantalum/vanadium ores", "boundary": "Tantalum ore shares this line with niobium and vanadium; it cannot be isolated. Conflict origin is tracked by traceability schemes, not customs."},
        "810320": {"title": "Tantalum, unwrought / powder", "boundary": "Semi-processed tantalum; capacitor-grade powder and the tantalum inside finished electronics are not separable."},
    }),
    "helium": ("helium-chain", "helium", {
        "280429": {"title": "Rare gases (helium, neon, krypton, xenon)", "boundary": "Customs lumps all rare gases together, so helium cannot be isolated — the dependency is literally invisible in trade data."},
    }),
    "neon": ("neon-chain", "neon", {
        "280429": {"title": "Rare gases (neon, helium, krypton, xenon)", "boundary": "Semiconductor-grade neon cannot be separated from the shared rare-gas line — the chokepoint that matters is invisible in customs data."},
    }),
    "ammonia": ("ammonia-chain", "ammonia", {
        "281410": {"title": "Anhydrous ammonia", "boundary": "The fertilizer intermediate; its binding input — natural gas — is a separate energy market, not visible here."},
        "310210": {"title": "Urea", "boundary": "The most-traded nitrogen fertilizer; a downstream form, gas-cost-driven upstream."},
    }),
    "gallium": ("gallium-chain", "gallium", {
        "811292": {"title": "Gallium/indium/germanium (unwrought minor metals)", "boundary": "Gallium shares this basket with indium and germanium and cannot be isolated — the dependency is invisible in customs data."},
    }),
    "cobalt": ("cobalt-chain", "cobalt", {
        "260500": {"title": "Cobalt ores and concentrates", "boundary": "Mined concentrate; largely a copper by-product, and refined-origin differs from mined-origin."},
        "810520": {"title": "Cobalt mattes, unwrought cobalt, powder", "boundary": "Semi-refined cobalt; battery-grade sulphate and the China refining share are not separable here."},
    }),
    "nickel": ("nickel-chain", "nickel", {
        "260400": {"title": "Nickel ores and concentrates", "boundary": "Little ore now trades — Indonesia's export ban moved the value into smelted products this line misses."},
        "750210": {"title": "Unwrought nickel, not alloyed", "boundary": "Refined nickel metal; class-1 vs class-2 and Indonesian intermediates are not distinguished."},
    }),
    "tungsten": ("tungsten-chain", "tungsten", {
        "261100": {"title": "Tungsten ores and concentrates", "boundary": "Mined scheelite/wolframite; China's processing dominance shows more in the APT line than in the ore."},
        "284180": {"title": "Tungstates (incl. ammonium paratungstate, APT)", "boundary": "The traded chemical intermediate; where China's midstream dominance is most visible."},
        "810194": {"title": "Tungsten, unwrought / powder", "boundary": "Metal powder; finished carbide tools and munitions are not captured."},
    }),
    "lithium": ("lithium-chain", "lithium", {
        "283691": {"title": "Lithium carbonate", "boundary": "Refined battery/technical chemical; customs origin is the refinery, not the mine."},
        "282520": {"title": "Lithium oxide and hydroxide", "boundary": "The other battery-grade chemical; spodumene concentrate is not shown here."},
    }),
    "titanium": ("titanium-chain", "titanium", {
        "261400": {"title": "Titanium ores and concentrates", "boundary": "Ilmenite/rutile sands; pigment-grade vs metal-grade is not distinguished."},
        "810820": {"title": "Titanium, unwrought / powder (incl. sponge)", "boundary": "Includes aerospace sponge, but pigment vs metal grade and mill products are not separable."},
    }),
    "magnesium": ("magnesium-chain", "magnesium", {
        "810411": {"title": "Unwrought magnesium, >= 99.8% pure", "boundary": "Primary magnesium metal; exporter shares track China's output; embedded magnesium in aluminium alloys is invisible."},
        "810419": {"title": "Unwrought magnesium, other", "boundary": "Lower-purity/alloyed unwrought magnesium."},
    }),
    "manganese": ("manganese-chain", "manganese", {
        "260200": {"title": "Manganese ores and concentrates", "boundary": "The diversified ore (South Africa, Gabon, Australia) - not the China-concentrated battery-grade refining."},
        "720211": {"title": "Ferro-manganese", "boundary": "Steel-grade alloy; electrolytic manganese metal and battery-grade sulphate are not captured."},
    }),
    "antimony": ("antimony-chain", "antimony", {
        "811010": {"title": "Unwrought antimony, powder", "boundary": "Refined antimony metal; China's refining dominance shows here more than in the diversifying mine."},
        "282580": {"title": "Antimony oxides (incl. trioxide)", "boundary": "The flame-retardant form (ATO); the stage the Sept-2024 export controls targeted."},
    }),
    "germanium": ("germanium-chain", "germanium", {
        "811292": {"title": "Germanium/gallium/indium (unwrought minor metals)", "boundary": "Germanium shares this basket with gallium and indium and cannot be isolated — invisible in customs data."},
    }),
    "chromium": ("chromium-chain", "chromium", {
        "261000": {"title": "Chromium ores and concentrates (chromite)", "boundary": "South-Africa-led ore; increasingly shipped to Kazakh and Chinese ferrochrome capacity."},
        "720241": {"title": "Ferro-chromium, > 4% carbon", "boundary": "The energy-intensive alloy step; where the smelter geography (KZ/CN) shows, not the ore map."},
    }),
    "vanadium": ("vanadium-chain", "vanadium", {
        "720292": {"title": "Ferro-vanadium", "boundary": "The steel-alloying form; China's processing dominance shows here, not in the shared V ore line."},
        "282530": {"title": "Vanadium oxides and hydroxides", "boundary": "Vanadium pentoxide — feeds both ferro-vanadium and flow-battery electrolyte; grade not distinguished."},
    }),
    "sulfur": ("sulfur-chain", "sulfur", {
        "250300": {"title": "Sulfur of all kinds (excl. sublimed/precipitated)", "boundary": "A by-product of oil/gas/smelting moved regionally; most is used on-site and never enters trade."},
        "280700": {"title": "Sulfuric acid; oleum", "boundary": "The workhorse acid; largely made and consumed at fertilizer and metal plants, so trade is a thin surplus."},
    }),
    "cement": ("cement-chain", "cement", {
        "252310": {"title": "Cement clinkers", "boundary": "The tradable intermediate; moves regionally at most because it is cheap and heavy."},
        "252329": {"title": "Portland cement (other)", "boundary": "Only a small share of cement is traded — production is overwhelmingly local."},
    }),
    "silver": ("silver-chain", "silver", {
        "261610": {"title": "Silver ores and concentrates", "boundary": "Silver is mostly a by-product credit in base-metal concentrates, not a standalone ore trade."},
        "710691": {"title": "Silver, unwrought", "boundary": "Refined silver, incl. bullion moved for investment — trading, not consumption."},
    }),
    "beryllium": ("beryllium-chain", "beryllium", {
        "811212": {"title": "Beryllium, unwrought; powder", "boundary": "A very small, specialised US-led trade; copper-beryllium alloy sits in copper-alloy lines, not here."},
        "811219": {"title": "Beryllium, other (articles)", "boundary": "Wrought beryllium articles; the US processing dominance is only partly visible."},
    }),
}

# code -> list of chains that use it
CODE_TO_CHAINS = defaultdict(list)
for ch, (_, _, codes) in CHAINS.items():
    for code in codes:
        CODE_TO_CHAINS[code].append(ch)
ALL_CODES = set(CODE_TO_CHAINS)


def country_maps():
    iso, names = {}, {}
    with open(COUNTRIES, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key, code = row["country_code"].strip(), (row.get("country_iso2") or "").strip()
            if code and code != "NA":
                iso[key] = code
                names[code] = (row.get("country_name") or code).strip()
    iso.update(FORCE_ISO); names.update(FORCE_NAME)
    return iso, names


def empty():
    return {"exp": defaultdict(float), "imp": defaultdict(float), "usd": 0.0, "tonnes": 0.0, "flows": 0}


def top(values, total, names, n=8):
    return [{"iso": iso, "name": names.get(iso, iso), "value_usd": round(value), "share": round(value / total, 4)}
            for iso, value in sorted(values.items(), key=lambda item: -item[1])[:n]] if total else []


def extract():
    iso_map, names = country_maps()
    # bag[chain][year][code]
    bag, vintage = {}, {}
    for ch, (_, _, codes) in CHAINS.items():
        bag[ch] = {}
        for _, years, _, _ in BATCHES:
            for year in years:
                bag[ch][year] = {code: empty() for code in codes}
                vintage[year] = None
    for hs, years, archive, member in BATCHES:
        for year in years:
            vintage[year] = hs
        with zipfile.ZipFile(os.path.join(ROOT, "raw", "baci", archive)) as zipped:
            for year in years:
                print("reading", year, hs, flush=True)
                with zipped.open(member.format(year=year)) as raw:
                    handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
                    next(handle)
                    for line in handle:
                        p = line.split(",")
                        if len(p) < 6:
                            continue
                        code = p[3]
                        if code not in ALL_CODES:
                            continue
                        exporter, importer = iso_map.get(p[1]), iso_map.get(p[2])
                        if not exporter or not importer or exporter == importer:
                            continue
                        try:
                            usd = float(p[4]) * 1000
                        except ValueError:
                            continue
                        if usd <= 0:
                            continue
                        try:
                            tonnes = float(p[5]) if p[5].strip() not in ("", "NA", "nan") else 0.0
                        except ValueError:
                            tonnes = 0.0
                        for ch in CODE_TO_CHAINS[code]:
                            row = bag[ch][year][code]
                            row["exp"][exporter] += usd; row["imp"][importer] += usd
                            row["usd"] += usd; row["tonnes"] += max(0, tonnes); row["flows"] += 1
    for ch, (out_dir, out_base, codes) in CHAINS.items():
        years = sorted(bag[ch])
        out = {"source": "CEPII BACI V202601, based on UN Comtrade", "years": years,
               "vintage": {str(y): vintage[y] for y in years}, "codes": codes, "years_data": {}, "series": {}}
        for year in years:
            out["years_data"][str(year)] = {}
            for code in codes:
                row, total = bag[ch][year][code], bag[ch][year][code]["usd"]
                shares = [v / total for v in row["exp"].values()] if total else []
                out["years_data"][str(year)][code] = {
                    "hs": vintage[year], "world_usd": round(total), "world_tonnes": round(row["tonnes"], 1), "n_flows": row["flows"],
                    "china_export_share": round(row["exp"].get("CN", 0) / total, 4) if total else None,
                    "export_hhi": round(sum(s * s for s in shares), 4) if total else None,
                    "exporters": top(row["exp"], total, names), "importers": top(row["imp"], total, names),
                }
        for code in codes:
            out["series"][code] = [{"year": year, **{k: out["years_data"][str(year)][code][k]
                                    for k in ("hs", "world_usd", "world_tonnes", "china_export_share", "export_hhi")}} for year in years]
        path = os.path.join(ROOT, out_dir, "out", out_base + "_trade.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(out, handle, ensure_ascii=False, indent=2); handle.write("\n")
        latest = out["years_data"][str(years[-1])]
        tot = sum(latest[c]["world_usd"] for c in codes)
        print("WROTE", os.path.relpath(path, ROOT), f"| {years[-1]} world ~${tot/1e9:.1f}B across {len(codes)} code(s)")


if __name__ == "__main__":
    extract()
