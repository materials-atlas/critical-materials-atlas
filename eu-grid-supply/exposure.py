"""Value-based supplier exposure, with independent data checks and explicit assumptions."""

from __future__ import annotations

from itertools import product

BANDS = ("Below 10%", "10% to below 25%", "25% to below 50%", "50% and above")
THRESHOLDS = (0.10, 0.25, 0.50)


def exposure_band(share):
    return BANDS[sum(share >= threshold for threshold in THRESHOLDS)]


def share(denominator, numerator):
    return numerator / denominator if denominator > 0 else None


def range_result(low, high):
    first = BANDS.index(exposure_band(low))
    last = BANDS.index(exposure_band(high))
    return {"range": [low, high], "exposure_bands": list(BANDS[first:last + 1])}


def sensitivity(row):
    p = row["production_meur"]
    m = row["imports_meur"]
    x = row["exports_meur"]
    c = row["imports_from_china_meur"]
    available = p + m - x

    def under(production=1, trade=1, exports=1, retained=1):
        return share(p * production + (m - x * exports) * trade, c * trade * retained)

    aligned_product = available * 0.90
    combined = [
        under(production, trade, exports, retained)
        for production, trade, exports, retained in product((0.90, 1.10), (0.95, 1.05), (0.90, 1.10), (0.75, 1))
    ]
    return {
        "production": range_result(under(production=1.10), under(production=0.90)),
        "trade_valuation": range_result(*sorted((under(trade=0.95), under(trade=1.05)))),
        "exports": range_result(under(exports=0.90), under(exports=1.10)),
        "product_scope": range_result(
            share(aligned_product, max(0, c - available * 0.10)),
            share(aligned_product, min(c, aligned_product)),
        ),
        "reexport": range_result(under(retained=0.75), under(retained=1)),
        "combined_excluding_scope": range_result(min(combined), max(combined)),
    }


def analyze(published, audit):
    year = str(published["headline_year"])
    results = {}
    for key, component in published["components"].items():
        row = component["years"][year]
        latest = audit["components_2024"][key]
        codes = latest["production_by_prodcom"]
        audit_production = sum(entry["PRODVAL"] for entry in codes.values())
        audit_imports = latest["extra_eu_imports_eur_excluding_uk"]
        audit_exports = latest["extra_eu_exports_eur_excluding_uk"]
        audit_cn = latest["imports_from_china_eur"]
        rounding_base = sum(entry.get("PVALBASE", 0) for entry in codes.values())
        minimum_production = max(0, audit_production - rounding_base)
        min_supply = minimum_production + audit_imports - audit_exports
        max_supply = audit_production + rounding_base + audit_imports - audit_exports
        supply = row["production_meur"] + row["imports_meur"] - row["exports_meur"]
        published_value = row["china_share_of_supply"]
        comparisons = {
            "production": audit_production / 1e6 - row["production_meur"],
            "imports": audit_imports / 1e6 - row["imports_meur"],
            "exports": audit_exports / 1e6 - row["exports_meur"],
            "imports_from_china": audit_cn / 1e6 - row["imports_from_china_meur"],
        }
        results[key] = {
            "label": component["label"],
            "recorded_2024_meur": row,
            "prodcom": component["prodcom"],
            "cn8_2024": latest["cn8"],
            "recalculated_share": share(supply, row["imports_from_china_meur"]),
            "published_share": published_value,
            "share_of_imports": row["china_share_of_imports"],
            "exposure_band": exposure_band(published_value),
            "crosscheck_value_share": share(audit_production + audit_imports - audit_exports, audit_cn),
            "crosscheck_import_share": share(audit_imports, audit_cn),
            "crosscheck_delta_meur": comparisons,
            "production_flags": {code: entry["PVALFLAG"] for code, entry in codes.items() if "PVALFLAG" in entry},
            "published_production_rounding": {
                "base_eur": rounding_base,
                "apparent_supply_eur": [min_supply, max_supply],
                "share_from_production_rounding_alone": [
                    share(max_supply, audit_cn), share(min_supply, audit_cn)
                ],
            },
            "sensitivity": sensitivity(row),
        }
    goes = audit["components_2024"]["goes"]
    codes = goes["production_by_prodcom"].values()
    if {entry.get("QNTUNIT") for entry in codes} != {"KG"}:
        raise ValueError("GOES sold production units must match the customs mass basis.")
    mass_production = sum(entry["PRODQNT"] for entry in codes)
    mass_imports = goes["extra_eu_imports_kg_excluding_uk"]
    mass_exports = goes["extra_eu_exports_kg_excluding_uk"]
    return {
        "headline_year": int(year),
        "components": results,
        "goes_mass_check_2024": {
            "production_kg": mass_production,
            "imports_kg": mass_imports,
            "exports_kg": mass_exports,
            "imports_from_china_kg": goes["imports_from_china_kg"],
            "china_import_share": share(mass_imports, goes["imports_from_china_kg"]),
            "china_apparent_supply_share": share(mass_production + mass_imports - mass_exports, goes["imports_from_china_kg"]),
            "production_flags": {
                code: entry["PQNTFLAG"] for code, entry in goes["production_by_prodcom"].items() if "PQNTFLAG" in entry
            },
        },
    }
