"""Generate the four phosphate exhibits from the checked-in evidence tables."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter


OUT = Path(__file__).resolve().parent / "out"
GREEN, BLUE, INK = "#0e7c74", "#15323a", "#203744"   # atlas teal and navy


def chart(title, xlabel, labels):
    fig, ax = plt.subplots(figsize=(7.7, 4.6))
    fig.subplots_adjust(left=.25, right=.92, top=.84, bottom=.16)
    ax.set_title(title, loc="left", fontsize=15, color=INK, weight="bold", pad=14)
    ax.set_xlabel(xlabel, color=INK)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=.22)
    ax.set_axisbelow(True)
    ax.spines[["left", "right", "top"]].set_visible(False)
    ax.spines["bottom"].set_color("#87969c")
    ax.tick_params(length=0, pad=6, colors=INK)
    return fig, ax


def save(fig, filename):
    fig.savefig(OUT / filename, dpi=140, metadata={"Software": "Matplotlib"})
    plt.close(fig)


def paired(ax, left, right, labels):
    y = range(len(left))
    ax.barh([i - .19 for i in y], left, .35, color=GREEN, label=labels[0])
    ax.barh([i + .19 for i in y], right, .35, color=BLUE, label=labels[1])
    ax.legend(loc="upper right", frameon=False, fontsize=9)


def plot_reserves(data):
    labels = ["Morocco", "China", "United States", "Russia", "Jordan"]
    rows = {r["country"]: r for r in data["upstream"]["rows"]}
    fig, ax = chart("Reserve and mine shares differ", "Share of world phosphate rock", labels)
    paired(ax, [rows[k]["reserves_share"] for k in labels], [rows[k]["production_2025_share"] for k in labels],
           ("Reported reserves", "2025 mine output"))
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlim(0, .8)
    save(fig, "phosphate_reserves.png")


def plot_origins(data):
    years = data["eu_imports"]
    groups = list(years["2024"])
    fig, ax = chart("EU import concentration by product", "Origin HHI by net product mass", groups)
    before, after = ([years[year][g]["hhi_points"][0] for g in groups] for year in ("2023", "2024"))
    paired(ax, before, after, ("2023", "2024"))
    for year, offset in (("2023", -.19), ("2024", .19)):
        for row, group in enumerate(groups):
            lower, upper = years[year][group]["hhi_points"]
            if upper > lower:
                ax.hlines(row + offset, lower, upper, color=INK, lw=1)
    ax.set_xlim(0, max(years[year][g]["hhi_points"][1] for year in years for g in groups) * 1.26)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    save(fig, "phosphate_origins.png")


def plot_balance(data):
    years = data["faostat_balance"]
    fig, ax = chart("EU apparent supply and agricultural use", "Million tonnes P₂O₅", list(years))
    paired(ax, [row["apparent_supply_t"] / 1e6 for row in years.values()],
           [row["agricultural_use_t"] / 1e6 for row in years.values()], ("Apparent supply", "Agricultural use"))
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    ax.set_xlim(0, 3.2)
    save(fig, "phosphate_balance.png")


def plot_stress(data):
    rows = data["stress_test"]["rows"]
    fig, ax = chart("DAP import gap under a modelled shock", "Share of baseline external DAP imports",
                    [f"{r['replacement_fraction']:.0%} replaced" for r in rows])
    gaps = [r["gap_share_of_baseline_imports"] for r in rows]
    ax.barh(range(len(rows)), gaps, color=BLUE, height=.46)
    for i, gap in enumerate(gaps):
        ax.text(gap + .009, i, f"{gap:.1%}", va="center", color=INK)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlim(0, .37)
    save(fig, "phosphate_dap_scenario.png")


def main():
    data = json.loads((OUT / "phosphate_chain.json").read_text(encoding="utf-8"))
    for draw in (plot_reserves, plot_origins, plot_balance, plot_stress):
        draw(data)


if __name__ == "__main__":
    main()
