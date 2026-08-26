"""Evidence JSON for the wind-turbine chain pilot. Uniform schema. Public sources.
Ported onto the shared chainview renderer with per-figure confidence tags. Run: python record_wind.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "wind_chain.json")

SRC = {
    "gwec_2026": {"title": "GWEC, Wind turbine installations and suppliers in 2025", "year": 2026, "url": "https://www.gwec.net/news/gwec-records-sharp-rise-in-wind-turbine-installations-as-five-oems-exceed-100-gw"},
    "jrc_materials": {"title": "European Commission JRC, Material requirements for wind (JRC139701)", "year": 2024, "url": "https://publications.jrc.ec.europa.eu/repository/handle/JRC139701"},
    "iea_manufacturing": {"title": "IEA, The State of Clean Technology Manufacturing", "year": 2023, "url": "https://www.iea.org/reports/the-state-of-clean-technology-manufacturing/analysis"},
    "doe_recycling": {"title": "US DOE, Wind Turbine Recycling", "year": 2023, "url": "https://www.energy.gov/cmei/systems/wind-turbine-recycling"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Wind-turbine chain",
    "chokepoint": {"product": "Wind turbines", "stage": "OEM + logistics", "mechanism": "diffuse", "physics": "A steel-and-concrete machine; the limit is scale/logistics + OEM share, and it localises", "holder": "China OEM", "share": "~67%", "control": "—", "conf": "estimate"},
    "published": True,
    "related": [{"href": "../magnet-chain/magnet-chain.html", "label": "Rare-earth magnet chain"}, {"href": "../steel-alloys-chain/steel-alloys-chain.html", "label": "Steel-alloys chain"}, {"href": "../grid-chain/grid-chain.html", "label": "Electricity-grid chain"}],
    "accent": "#4a8090",
    "eyebrow": "Product-chain pilot · the machine in the wind",
    "h1": "The wind-turbine bottleneck is scale, not scarcity",
    "deck": "A turbine is mostly steel and concrete, with copper windings and composite blades. No rare mineral gates "
            "it — magnet rare earths appear only in some drivetrain designs. The binding constraints are physical "
            "size, logistics and a manufacturing base that is now dominated by a handful of, increasingly Chinese, OEMs.",
    "byline": "steel & concrete (bulk) ≠ copper ≠ magnets (some designs only) ≠ the OEM ≠ installed on site",
    "correction": "Unlike magnets or solar wafers, a wind turbine has no single scarce input — it is ~85–90% "
                  "commodity materials by mass. Its chokepoints are elsewhere: the sheer scale of blades and towers "
                  "(a logistics problem), and OEM concentration — Chinese manufacturers supplied about two-thirds of "
                  "new turbines in 2025 and hold ~93% of their vast home market.",
    "stats": [
        {"v": "~67%", "l": "of new turbine units supplied by China-HQ OEMs (2025)", "conf": "measured"},
        {"v": "178 GW", "l": "wind capacity mechanically installed worldwide (2025)", "conf": "measured"},
        {"v": "steel + concrete", "l": "the bulk of a turbine — commodity materials, not critical minerals", "conf": "measured"},
        {"v": "some only", "l": "magnet rare earths are used only in direct-drive (PMSG) designs", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Materials", "t": "steel, concrete, copper, composites — and, in some designs, magnet rare earths"},
        {"n": "2 · Components", "t": "blades, tower, bearings, gearbox or direct-drive generator, power electronics"},
        {"n": "3 · Turbine (OEM)", "t": "the OEM integrates the nacelle, rotor and controls into a generating system"},
        {"n": "4 · Wind farm", "t": "transport, foundations, cabling, installation and grid connection on site"},
    ],
    "sections": [
        {"h2": "1 · What a turbine is actually made of", "panels": [
            {"kind": "text", "h3": "Bulk commodities, not critical minerals", "conf": "measured",
             "text": "By mass a wind turbine is dominated by steel (tower, nacelle, foundation reinforcement) and "
                     "concrete, with copper in the generator and cabling and glass- or carbon-fibre composites in the "
                     "blades. None of these is a scarcity chokepoint. That is why wind sits apart from most chains in "
                     "this atlas: its supply risk is industrial and logistical, not geological.",
             "note": "JRC material requirements for wind.", "flag": "a steel-and-concrete machine"},
            {"kind": "text", "h3": "The one critical-mineral hedge: drivetrain choice",
             "text": "Some turbines use direct-drive permanent-magnet generators, which need neodymium and dysprosium "
                     "— linking them to the magnet chain. But geared drivetrains, which use little or no magnet rare "
                     "earth, remain widespread, so the rare-earth exposure is a design choice, not an inescapable "
                     "feature of wind. The chokepoint can be engineered around.",
             "flag": "rare earths are optional here"},
        ]},
        {"h2": "2 · The real chokepoint is the machine's size", "panels": [
            {"kind": "big", "h3": "Bigger every year", "big": "logistics", "conf": "estimate",
             "text": "Modern blades exceed 100 metres and towers reach ever higher, so the binding constraints become "
                     "physical: roads and ports that can move the pieces, cranes that can lift them, specialised vessels "
                     "for offshore, and factories sited near the coast. You cannot ship a chokepoint like this in a "
                     "container — it is built and moved locally, which shapes where wind can scale.",
             "note": "IEA / industry: turbine scale and transport constraints."},
            {"kind": "text", "h3": "End-of-life: the blade problem",
             "text": "The composite blades that make wind cheap are hard to recycle, and a wave of first-generation "
                     "turbines is now retiring. It is a genuine materials issue for wind — but a waste-and-recycling "
                     "one, not a supply chokepoint, and the industry is actively developing recyclable resins.",
             "note": "US DOE, Wind Turbine Recycling.", "flag": "a waste problem, not a supply one"},
        ]},
        {"h2": "3 · Where the concentration actually is: the OEM", "panels": [
            {"kind": "cards", "h3": "A market tilting toward China", "cards": [
                {"t": "~67% of units", "d": "China-headquartered OEMs (Goldwind, Envision, Windey and peers) supplied about two-thirds of the turbines installed worldwide in 2025."},
                {"t": "~93% at home", "d": "Chinese OEMs hold roughly 93% of China's own market — the world's largest — which is where most of that global share is built."},
                {"t": "Western squeeze", "d": "Vestas, Siemens Gamesa and GE Vernova compete in a tighter field; the concentration risk in wind is corporate and industrial, not mineral."},
            ]},
        ]},
    ],
    "trade_intro": "BACI carries wind-powered generating sets and parts, but a turbine is largely assembled and "
                   "installed near where it operates, so cross-border trade captures only a slice of the chain "
                   "(nacelles, blades, castings). Read the shares below as component-trade positions, not a map of who "
                   "can build a turbine.",
    "method": [
        {"stage": "Materials", "lens": "JRC bill of materials", "why": "~85–90% steel/concrete/copper — no scarcity chokepoint"},
        {"stage": "Drivetrain", "lens": "geared vs direct-drive", "why": "rare-earth exposure is a design choice, not inherent"},
        {"stage": "OEM", "lens": "GWEC supplier shares", "why": "the real concentration — ~67% China-HQ OEMs"},
        {"stage": "Trade", "lens": "BACI generating sets & parts", "why": "components only; turbines are built locally — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- wind, no scarce mineral; bottleneck = scale + OEM concentration (~67% China)")
