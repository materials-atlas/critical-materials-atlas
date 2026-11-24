"""Replicate the two filed transformer unit-value models and their pre-trend check."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from runpy import run_path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).resolve().parent / "out/transformer_replication.json"


def main():
    sys.path.insert(0, str(ROOT))
    code = run_path(str(ROOT / "buildout-study/analysis.py"))
    baci = code["baci"]
    countries = baci.countries().set_index("code")["iso3"].to_dict()
    lines = code["TRANSFORMERS"]
    controls = {"heavy_machinery": code["CAPITAL_CTL"], "electrical_machinery": code["CONTAMINATED"]}
    wanted = set(lines).union(*controls.values())
    frames = []
    for year in code["YEARS"]:
        data = baci.year(year, nom=code["NOM"], columns=["i", "j", "k", "v", "q"], codes=wanted)
        data["year"] = year
        data["exp"] = data.i.astype(str).map(countries).fillna(data.i.astype(str))
        data["imp"] = data.j.astype(str).map(countries).fillna(data.j.astype(str))
        frames.append(data)
    sample, _ = code["sample"](code["pd"].concat(frames, ignore_index=True))
    rng = code["np"].random.default_rng(code["SEED"])
    filed = json.loads((ROOT / "out/buildout_study.json").read_text(encoding="utf-8"))
    prior = {
        "heavy_machinery": filed["designs"]["B_transformers"]["price"],
        "electrical_machinery": filed["checks"]["contaminated_controls"]["price"],
    }
    labels = {"heavy_machinery": "B_transformers price", "electrical_machinery": "B vs contaminated"}
    outcomes = {}
    for name, comparison in controls.items():
        spec = {"lines": lines, "controls": comparison}
        estimate = code["estimate"](sample, "luv", spec, labels[name], rng)
        outcomes[name] = {
            "flow_years": estimate["n"],
            "post_2023_24": estimate["coefs"]["TxP2"],
            "matches_filed_sample_and_coefficients": (
                estimate["n"] == prior[name]["n"] and estimate["coefs"] == prior[name]["coefs"]
            ),
        }
    spec = {"lines": lines, "controls": controls["heavy_machinery"]}
    event = code["event_study"](sample, "luv", spec, rng, label="ev B")
    violations = [year for year in range(2014, 2019) if year in event and abs(event[year]["beta"]) > 0.05]
    result = {
        "source": f'CEPII BACI {code["NOM"]} {baci.VINTAGE}',
        "filed_calculation": "buildout-study/analysis.py",
        "observed_years": [code["YEARS"][0], code["YEARS"][-1]],
        "models": outcomes,
        "pretrend_violations": violations,
        "filed_pretrend_violations": filed["checks"]["pretrend_rule"]["B_price"]["years_outside_0.05"],
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote grid-chain/out/transformer_replication.json")


if __name__ == "__main__":
    main()
