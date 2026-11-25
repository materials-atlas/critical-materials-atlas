"""Trace the aluminium a market uses back to where it was smelted, where its alumina was refined and where
the bauxite was mined.

Method (Kastner, Kastner and Nonhebel, 2011, Ecological Economics 70, 1032-1040). For one stage, every country's
supply is its own production plus its imports. A country's exports are assumed to have the same mix of origins as
its supply. With p the production vector, Z the matrix of bilateral trade (exporter in rows) and x = p + imports,
the share of country j's supply that was produced in country i is

    C = diag(p / x) (I - Z diag(1 / x))^-1

The three stages are then chained: the metal a market uses is traced to its smelting countries, each smelting
country's alumina supply to its refining countries, and each refining country's bauxite supply to its mines.

Inputs: production_2022.json (USGS Minerals Yearbook 2022) and the local BACI extract, through baci.py.
No network access. Run from the repository root:
    python aluminium-chain/flow_model.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import baci  # noqa: E402  the one door for BACI

HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCTION = os.path.join(HERE, "production_2022.json")
OUT = os.path.join(HERE, "out", "aluminium_flows.json")
STAGES = {"bauxite": ["260600"], "alumina": ["281820"], "aluminium": ["760110", "760120"]}
PLAIN = {"Russian Federation": "Russia", "USA": "United States", "Rep. of Korea": "South Korea", "Türkiye": "Turkey", "Viet Nam": "Vietnam",
         "Lao People's Dem. Rep.": "Laos", "Bosnia Herzegovina": "Bosnia and Herzegovina", "Dominican Rep.": "Dominican Republic",
         "United Rep. of Tanzania": "Tanzania", "Solomon Isds": "Solomon Islands", "China, Hong Kong SAR": "Hong Kong",
         "Dem. Rep. of the Congo": "Congo (Kinshasa)"}
EU27 = ("Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia", "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
        "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
        "Spain", "Sweden")
MARKETS = {"United States": ("United States",), "European Union": EU27, "Japan": ("Japan",), "South Korea": ("South Korea",),
           "India": ("India",), "China": ("China",)}
TOP = 6


def origin_shares(names, production, trade):
    """C[i, j] = share of country j's supply (production plus imports) that was produced in country i."""
    n = len(names)
    index = {name: k for k, name in enumerate(names)}
    p = np.zeros(n)
    for name, value in production.items():
        p[index[name]] = value
    z = np.zeros((n, n))
    for exporter, importer, tonnes in trade:
        if exporter != importer:
            z[index[exporter], index[importer]] += tonnes
    x = p + z.sum(axis=0)
    inverse = np.divide(1.0, x, out=np.zeros(n), where=x > 0)
    c = np.diag(p * inverse) @ np.linalg.inv(np.eye(n) - z @ np.diag(inverse))
    use = np.clip(x - z.sum(axis=1), 0, None)          # supply less exports: what stays in the country
    return c, x, use, p, z


def trace(names, prod, df, stages, bauxite_factor=1.0):
    """Run the three stages and chain them. Returns (stage diagnostics, markets, smelting countries)."""
    index = {name: k for k, name in enumerate(names)}
    result, kept = {}, {}
    for stage, hs in stages.items():
        d = df[df["k"].isin(hs)].groupby(["exporter", "importer"])["q"].sum().reset_index()
        factor = bauxite_factor if stage == "bauxite" else 1.0
        trade = [(r.exporter, r.importer, r.q / 1000.0 * factor) for r in d.itertuples()]          # thousand tonnes
        c, x, use, p, z = origin_shares(names, prod["stages"][stage]["production"], trade)
        kept[stage] = (c, x, use, p, z)
        sums = c.sum(axis=0)[x > 0]
        if c.min() < -1e-9 or sums.max() > 1 + 1e-6:
            raise SystemExit(f"{stage}: origin shares are negative or add to more than one ({c.min():.3g}, {sums.max():.6f})")
        # What every country keeps, traced to origin i, adds up to what i produced, except where a country's
        # recorded exports exceed its supply: its use is set to zero and the excess shows up as a gap.
        back = c @ use
        excess = np.clip(z.sum(axis=1) - x, 0, None)                     # exports larger than supply
        no_output = p <= 0
        result[stage] = {"world_production_kt": float(p.sum()), "world_trade_kt": float(z.sum()),
                         "largest_tracing_gap_kt": round(float(np.abs(back - p).max()), 1), "largest_gap_country": names[int(np.abs(back - p).argmax())],
                         "exports_above_supply_kt": round(float(excess.sum()), 1),
                         "largest_export_excess": {"country": names[int(excess.argmax())], "kt": round(float(excess.max()), 1)},
                         "trade_shipped_by_countries_without_production_kt": round(float(z[no_output].sum()), 1),
                         # supply that reaches a country from one with no recorded production or imports cannot be traced
                         "untraced_share_of_world_use": round(float(((1 - c.sum(axis=0)) * use).sum() / use.sum()), 5)}

    c_bx, c_al, c_me = kept["bauxite"][0], kept["alumina"][0], kept["aluminium"][0]
    x_me, use_me, z_me = kept["aluminium"][1], kept["aluminium"][2], kept["aluminium"][4]

    def top(vector, exclude=()):
        order = [k for k in np.argsort(-vector) if names[k] not in exclude and vector[k] > 0.0005][:TOP]
        return [{"name": names[k], "share": round(float(vector[k]), 4)} for k in order]

    def hhi(vector):
        return round(float((vector ** 2).sum()) * 10000)

    markets = {}
    for market, members in MARKETS.items():
        cols = [index[m] for m in members]
        weight = use_me[cols]
        if weight.sum() <= 0:
            raise SystemExit(f"{market}: no apparent use of unwrought aluminium")
        smelted = (c_me[:, cols] * weight).sum(axis=1) / weight.sum()
        refined = c_al @ smelted
        mined = c_bx @ refined
        # the customs view: imports of unwrought aluminium from outside the market, by shipping country
        imports = z_me[:, cols].sum(axis=1)
        for m in cols:
            imports[m] = 0.0
        own = set(members)
        customs = imports / imports.sum() if imports.sum() else imports
        net_use = float((x_me[cols] - z_me[cols].sum(axis=1)).sum())      # supply less exports, summed over members without clipping

        def grouped(vector):
            """Fold the market's own members into one line, keep the rest by country."""
            home = float(sum(vector[index[m]] for m in members))
            rest = top(vector, exclude=own)
            folded = np.append(np.array([vector[k] for k in range(len(names)) if names[k] not in own]), home)   # the market counts as one origin
            return {"home": round(home, 4), "top_foreign": rest, "untraced": round(float(1 - vector.sum()), 4), "hhi": hhi(folded)}

        markets[market] = {
            "apparent_use_kt": round(net_use, 1),
            "customs_view": {"imports_kt": round(float(imports.sum()), 1),
                             "top_suppliers": top(customs) if imports.sum() else [], "hhi": hhi(customs) if imports.sum() else None},
            "smelted_in": grouped(smelted), "alumina_refined_in": grouped(refined), "bauxite_mined_in": grouped(mined),
            "customs_share_of": {n: round(float(customs[index[n]]), 4) for n in ("Guinea", "Brazil", "Australia", "Jamaica", "Canada", "Norway")},
            "selected": {"guinea_bauxite": round(float(mined[index["Guinea"]]), 4), "australia_bauxite": round(float(mined[index["Australia"]]), 4),
                         "china_bauxite": round(float(mined[index["China"]]), 4), "brazil_bauxite": round(float(mined[index["Brazil"]]), 4),
                         "china_alumina": round(float(refined[index["China"]]), 4), "australia_alumina": round(float(refined[index["Australia"]]), 4),
                         "brazil_alumina": round(float(refined[index["Brazil"]]), 4), "china_smelting": round(float(smelted[index["China"]]), 4),
                         "russia_smelting": round(float(smelted[index["Russia"]]), 4), "canada_smelting": round(float(smelted[index["Canada"]]), 4),
                         "norway_smelting": round(float(smelted[index["Norway"]]), 4)},
        }

    # the same tracing for each large smelting country's own metal: where the bauxite behind it was mined
    smelters = {}
    order = sorted(prod["stages"]["aluminium"]["production"].items(), key=lambda kv: -kv[1])[:14]
    for country, kt in order:
        refined = c_al[:, index[country]]
        mined = c_bx @ refined
        smelters[country] = {"metal_kt": kt, "alumina_refined_in": top(refined), "bauxite_mined_in": top(mined),
                             "alumina_untraced": round(float(1 - refined.sum()), 4), "bauxite_untraced": round(float(1 - mined.sum()), 4)}
    return result, markets, smelters


def headline(markets):
    """The figures the page states in words, for comparing variants."""
    return {m: {"guinea_bauxite": v["selected"]["guinea_bauxite"], "home_smelting": v["smelted_in"]["home"], "home_bauxite": v["bauxite_mined_in"]["home"],
                "index_smelting": v["smelted_in"]["hhi"], "index_refining": v["alumina_refined_in"]["hhi"], "index_mining": v["bauxite_mined_in"]["hhi"]}
            for m, v in markets.items()}


def main():
    prod = json.load(open(PRODUCTION, encoding="utf-8"))
    year = prod["year"]
    frame = baci.countries()
    current = {}
    for r in frame.itertuples():
        if "(..." not in r.name:                          # former entities share ISO codes with their successors
            current[int(r.code)] = PLAIN.get(r.name, r.name)
    names = sorted(set(current.values()))
    for stage in STAGES:
        missing = [c for c in prod["stages"][stage]["production"] if c not in names]
        if missing:
            raise SystemExit(f"{stage}: production countries not found in the trade database: {missing}")
    codes = [c for v in STAGES.values() for c in v]
    df = baci.year(year, codes=codes)
    df = df[df["i"].isin(current) & df["j"].isin(current) & df["q"].notna()]
    df = df.assign(exporter=df["i"].map(current), importer=df["j"].map(current))

    result, markets, smelters = trace(names, prod, df, STAGES)
    # Two variants, to show how far the stated results depend on choices made here.
    unalloyed = dict(STAGES, aluminium=["760110"])
    _, no_alloy, _ = trace(names, prod, df, unalloyed)
    _, dry, _ = trace(names, prod, df, STAGES, bauxite_factor=0.9)

    out = {"year": year,
           "method": ("Origin tracing with proportional mixing (Kastner, Kastner and Nonhebel, 2011) for each stage. "
                      "Chaining the three stages is this study's own step."),
           "inputs": {"production": "production_2022.json (USGS Minerals Yearbook 2022)", "trade": "CEPII BACI V202601, customs net weight",
                      "codes": STAGES},
           "assumptions": ["A country's exports have the same mix of origins as its supply (production plus imports) in that year.",
                           "A smelting country uses the national mix of alumina, and a refining country the national mix of bauxite.",
                           "Stocks do not change.",
                           "Unwrought aluminium in trade includes alloys and remelted metal; production is primary metal only.",
                           "The alumina code covers all grades, not only smelter grade. Bauxite production is in dry tonnes and trade in customs weight."],
           "stages": result, "markets": markets, "smelting_countries": smelters,
           "sensitivity": {"base": headline(markets),
                           "unalloyed_metal_only": {"note": "Unwrought alloy (HS 760120) left out of metal trade. A stress test: some smelting countries ship most of their metal as alloy.",
                                                    "markets": headline(no_alloy)},
                           "traded_bauxite_less_10_per_cent_moisture": {"note": "Bauxite trade tonnage multiplied by 0.9, against production in dry tonnes.",
                                                                       "markets": headline(dry)}}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    print("wrote aluminium_flows.json:", "; ".join(
        "%s Guinea %.0f%% of bauxite" % (m, 100 * v["selected"]["guinea_bauxite"]) for m, v in markets.items()))


if __name__ == "__main__":
    main()
