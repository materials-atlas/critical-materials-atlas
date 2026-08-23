"""Record public IEA solar-factory shares next to the BACI silicon-chip pull.

These are curated from published IEA / IEA-PVPS text (not scraped from a
paywalled sheet). Chip-grade production is NOT in these figures.

Run: python silicon-chip/record_iea_pv.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "iea_pv_production.json")

# IEA PVPS, Trends in Photovoltaic Applications 2024 (T1-43:2024).
# Figures 4.2–4.5 and surrounding text. Year = 2023 PRODUCTION (not capacity).
# Local copy: raw/iea/IEA-PVPS-Task-1-Trends-Report-2024.pdf
PVPS_2024 = {
    "source": "IEA PVPS (2024), Trends in Photovoltaic Applications 2024, Report T1-43:2024",
    "url": "https://iea-pvps.org/wp-content/uploads/2024/10/IEA-PVPS-Task-1-Trends-Report-2024.pdf",
    "licence": "IEA PVPS public report",
    "year": 2023,
    "metric": "production",
    "stages": {
        "polysilicon": {
            "title": "PV polysilicon (semiconductor-grade included)",
            "figure": "Figure 4.2",
            "world_tonnes": 1_608_000,
            "semiconductor_tonnes": 38_800,
            "pv_share_of_poly": 0.976,
            "china_tonnes": 1_470_000,
            "shares": [
                {"iso": "CN", "name": "China", "share": 0.92},
                {"iso": "DE", "name": "Germany", "share": 0.04},
                {"iso": "US", "name": "United States", "share": 0.02},
                {"iso": "MY", "name": "Malaysia", "share": 0.02},
                {"iso": "KR", "name": "Korea", "share": 0.00},
                {"iso": "XX", "name": "Other", "share": 0.00},
            ],
            "note": (
                "Chart label: production for semiconductors is included. "
                "Semiconductor poly is ~38.8 kt of 1 608 kt (~2%). "
                "China produced 1.47 Mt; share rose from 86% (2020) to 92% (2023)."
            ),
        },
        "wafers": {
            "title": "PV wafers",
            "figure": "Figure 4.3",
            "world_gw": 682,
            "china_gw": 668,
            "shares": [
                {"iso": "CN", "name": "China", "share": 0.98},
                {"iso": "VN", "name": "Vietnam", "share": 0.02},
                {"iso": "XX", "name": "Other", "share": 0.01},
            ],
            "note": (
                "China produced 668 GW of 682 GW. About 70 GW were exported to "
                "cell plants in Vietnam, Malaysia, Thailand, Singapore, Taiwan, India. "
                "Chart rounds China 98%, Vietnam 2%, Other 1%."
            ),
        },
        "cells": {
            "title": "PV cells",
            "figure": "Figure 4.4",
            "world_gw": 644,
            "china_gw": 591,
            "shares": [
                {"iso": "CN", "name": "China", "share": 0.918},
                {"iso": "MY", "name": "Malaysia", "share": 0.023},
                {"iso": "VN", "name": "Vietnam", "share": 0.017},
                {"iso": "KR", "name": "Korea", "share": 0.016},
                {"iso": "US", "name": "United States", "share": 0.008},
                {"iso": "TW", "name": "Taiwan", "share": 0.006},
                {"iso": "TH", "name": "Thailand", "share": 0.006},
                {"iso": "IN", "name": "India", "share": 0.005},
                {"iso": "XX", "name": "Rest of world", "share": 0.001},
            ],
            "note": "Recorded for later solar-product chain. Not used in the silicon-to-wafer hop.",
        },
        "modules": {
            "title": "PV modules",
            "figure": "Figure 4.5",
            "world_gw": 612,
            "china_gw": 510,
            "shares": [
                {"iso": "CN", "name": "China", "share": 0.846},
                {"iso": "VN", "name": "Vietnam", "share": 0.034},
                {"iso": "IN", "name": "India", "share": 0.027},
                {"iso": "TH", "name": "Thailand", "share": 0.023},
                {"iso": "US", "name": "United States", "share": 0.022},
                {"iso": "MY", "name": "Malaysia", "share": 0.021},
                {"iso": "XX", "name": "Rest of world", "share": 0.026},
            ],
            "note": "Recorded for later solar-product chain. Not used in the silicon-to-wafer hop.",
        },
    },
}

# Newer IEA vintage: manufacturing / supply of demand, not a country table.
ETP_2026 = {
    "source": "IEA (2026), Energy Technology Perspectives 2026",
    "url": "https://www.iea.org/reports/energy-technology-perspectives-2026/energy-technology-manufacturing-and-trade",
    "licence": "CC BY 4.0",
    "year": 2024,
    "metric": "share of global supply / manufacturing (IEA text, not a full country table)",
    "china": {
        "polysilicon_and_wafers": 0.90,
        "modules": 0.80,
    },
    "note": (
        "IEA: China supplies more than 80% of upstream wafer and polysilicon "
        "(90% in 2024) and 80% of modules in 2024. Complements PVPS 2023 "
        "production shares; not a replacement country table."
    ),
}

# IEA (2024) Advancing Clean Technology Manufacturing — wafers 95% capacity.
ACTM_2024 = {
    "source": "IEA (2024), Advancing Clean Technology Manufacturing",
    "url": "https://www.iea.org/reports/advancing-clean-technology-manufacturing/executive-summary",
    "licence": "CC BY 4.0",
    "year": 2024,
    "metric": "manufacturing capacity",
    "china": {"modules": 0.80, "wafers": 0.95},
    "note": "Capacity, not production. Wafers 95%; modules more than 80%.",
}

CHIP_GAP = {
    "electronic_grade_polysilicon": (
        "No public IEA/USGS country production table. Global semiconductor-grade "
        "poly is only ~39 kt (IEA-PVPS 2023) versus ~1 570 kt solar. USGS silicon "
        "chapter covers metal and ferrosilicon only."
    ),
    "semiconductor_wafers": (
        "No public IEA/USGS country production table. SEMI and firm reports exist "
        "but are not Atlas-grade. Do not invent Shin-Etsu/SUMCO shares."
    ),
}


def main():
    out = {
        "purpose": (
            "Factory layer for the solar half of HS 280461 / 381800. "
            "Sits next to BACI trade. Not added to the 32."
        ),
        "iea_pvps_trends_2024": PVPS_2024,
        "iea_etp_2026": ETP_2026,
        "iea_actm_2024": ACTM_2024,
        "chip_production_gap": CHIP_GAP,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
