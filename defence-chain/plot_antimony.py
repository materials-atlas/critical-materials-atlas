"""Plot the published monthly antimony trade series with Matplotlib."""
import csv
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
from matplotlib import pyplot as plt

OUT = Path(__file__).resolve().parent / "out"
START = date(2022, 8, 1)
END = date(2025, 9, 30)
LICENSING = date(2024, 9, 1)
US_MEASURE = date(2024, 12, 1)
MARKETS = {"EU": ("EU import basket", "EUR"), "US": ("US import basket", "USD")}
METRICS = (
    ("total_t", "All origins", "Tonnes", 2500),
    ("china_t", "Declared China origin", "Tonnes", 600),
    ("customs_unit_value_per_kg", "Customs unit value", "{currency}/kg", None),
)
COLORS = ("#15323a", "#0e7c74", "#5a6b68")   # atlas navy, teal, grey


def main():
    with (OUT / "defence_antimony_monthly.csv").open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    fig, axes = plt.subplots(3, 2, figsize=(10, 7.5), sharex=True)
    fig.subplots_adjust(left=.11, right=.96, top=.86, bottom=.11, hspace=.48, wspace=.31)
    fig.suptitle("Monthly imports of selected antimony products", x=.11, y=.96, ha="left", fontsize=18, weight="bold")
    fig.text(.11, .905, "The EU and US series cover different product baskets.", fontsize=10, color="#344d5d")

    for col, (market, (name, currency)) in enumerate(MARKETS.items()):
        rows = [row for row in data if row["market"] == market]
        dates = [date(int(row["month"][:4]), int(row["month"][4:]), 1) for row in rows]
        for i, (field, label, unit, ymax) in enumerate(METRICS):
            axis = axes[i][col]
            values = [float(row[field]) if row[field] else float("nan") for row in rows]
            axis.set_title(f"{name} · {label}" if i == 0 else label, loc="left", fontsize=11, weight="medium")
            axis.plot(dates, values, color=COLORS[i], lw=2)
            axis.axvline(LICENSING, color="#465463", ls=":", lw=1.5)
            if market == "US":
                axis.axvline(US_MEASURE, color="#465463", ls="--", lw=1.5)
            axis.set_ylabel(unit.format(currency=currency), fontsize=9)
            axis.set_ylim(bottom=0, top=ymax)
            axis.set_xlim(START, END)
            axis.grid(axis="y", alpha=.25)
            axis.set_axisbelow(True)
            axis.spines[["top", "right", "left"]].set_visible(False)
            axis.spines["bottom"].set_color("#76818a")
            axis.tick_params(length=0, pad=5, labelsize=9)
            axis.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
            axis.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

    fig.text(.11, .034, "The dotted line marks September 2024 licensing. The dashed line marks the December 2024 US measure.",
             fontsize=9, color="#344d5d")
    fig.savefig(OUT / "defence_antimony_monthly.png", dpi=150, metadata={"Software": "Matplotlib"})
    plt.close(fig)


if __name__ == "__main__":
    main()
