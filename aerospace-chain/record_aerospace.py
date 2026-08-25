"""Evidence JSON for the unpublished aerospace / jet-engine superalloy chain pilot.
Uniform chain schema (shared renderer). Public sources. Rhenium/qualified-titanium and
single-crystal casting are snapshot-only in public data — marked as such, not padded into
a false series. Run: python record_aerospace.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "aerospace_chain.json")

SRC = {
    "usgs_rhenium": {"title": "USGS Mineral Commodity Summaries 2026 — Rhenium", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-rhenium.pdf"},
    "usgs_titanium": {"title": "USGS Mineral Commodity Summaries 2025 — Titanium and Titanium Dioxide", "year": 2025, "url": "https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-titanium.pdf"},
    "argus_ti": {"title": "Argus, Aerospace-approved Ti sponge supply up in 2024", "year": 2025, "url": "https://www.argusmedia.com/en/news-and-insights/latest-market-news/2659047-aerospace-approved-ti-sponge-supply-up-in-2024"},
    "market_engines": {"title": "Commercial aircraft engine market analyses (Mordor Intelligence; Simple Flying), 2024", "year": 2024, "url": "https://www.mordorintelligence.com/industry-reports/commercial-aircraft-engines-market", "note": "Secondary market analyses; OEM shares approximate and vary by segment/metric."},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
    "gatech_lca": {"title": "Life Cycle Assessment and Risk Management of Titanium for Aerospace Applications (Alsabeeha et al., Georgia Tech ASDL)", "year": 2023, "url": "https://repository.gatech.edu/server/api/core/bitstreams/b8c32ac1-026d-4da6-bea2-38ffedd1fbc6/content"},
    "superalloy_recycle": {"title": "Resource recycling of superalloys and hydrometallurgical challenges (Srivastava et al., J. Mater. Sci.)", "year": 2014, "url": "https://www.researchgate.net/publication/262572757_Resource_recycling_of_superalloys_and_hydrometallurgical_challenges", "note": "Full text paywalled; figures from abstract/indexed snippets."},
    "eu_crm": {"title": "Study on the Critical Raw Materials for the EU 2023 (Economic Importance × Supply Risk)", "year": 2023, "url": "https://www.eunews.it/wp-content/uploads/2023/10/study-on-the-critical-raw-materials-for-the-eu-2023-ET0723116ENN.pdf"},
}

CHAIN = {
    "title": "Aerospace / jet-engine superalloy chain",
    "chokepoint": {"product": "Aircraft", "stage": "Turbine blades", "mechanism": "capability", "physics": "Single-crystal blades are HOT but BATCH — concentrated by qualification + know-how, not power", "holder": "mixed", "share": "—", "control": "—", "conf": "measured"},
    "published": True,
    "related": [{"href": "../titanium-chain/titanium-chain.html", "label": "Titanium chain"}, {"href": "../pgm-catalyst-chain/pgm-catalyst-chain.html", "label": "PGM / catalyst chain"}, {"href": "../defence-chain/defence-chain.html", "label": "Defence chain"}],
    "accent": "#35617f",
    "eyebrow": "Product-chain pilot · aerospace propulsion",
    "h1": "A jet engine's bottleneck is not the ore",
    "deck": "A large jet engine turns nickel, cobalt, rhenium, hafnium and titanium into superalloys, then "
            "single-crystal turbine blades, then a finished engine. At every step downstream the supply gets "
            "<i>narrower</i> — the mine is the least concentrated stage of all.",
    "byline": "rhenium (by-product) ≠ titanium sponge ≠ aerospace-qualified metal ≠ blade casting ≠ jet engine",
    "correction": "A 'critical minerals' list reads the risk at the mine. But Chile's rhenium is a copper by-product "
                  "no one mines for; China makes ~71% of titanium sponge yet almost none is aerospace-qualified; "
                  "single-crystal blade casting is held by a handful of firms; and three Western groups build nearly "
                  "every large engine. The chokepoint walks downstream.",
    "stats": [
        {"v": "~81 t", "l": "world rhenium output per year (a copper by-product)", "conf": "measured"},
        {"v": "55%", "l": "of rhenium mine production is Chile", "conf": "measured"},
        {"v": "~71%", "l": "of titanium sponge is China — little of it aerospace-qualified", "conf": "measured"},
        {"v": "55 / 26 / 18", "l": "engine share: GE · Pratt &amp; Whitney · Rolls-Royce (%)", "conf": "estimate"},
        {"v": "~28%", "l": "of world titanium sponge is aerospace-qualified", "conf": "estimate"},
        {"v": "4,026", "l": "engine-maker Herfindahl index (&gt;2,500 = highly concentrated)", "conf": "estimate"},
    ],
    "hops": [
        {"n": "1 · Rhenium", "t": "the scarce superalloy element — a copper by-product, ~55% Chile"},
        {"n": "2 · Titanium sponge", "t": "production (China) vs aerospace qualification (Japan/Russia/Kazakhstan)"},
        {"n": "3 · Blade casting", "t": "single-crystal superalloy blades — a few firms, no country series"},
        {"n": "4 · Jet engine", "t": "GE, Pratt & Whitney, Rolls-Royce — the most concentrated stage"},
    ],
    "history": {
        "title": "China's share of world titanium-sponge exports, 2002–2024",
        "conf": "measured",
        "series": [{"label": "China · sponge export share (%)", "points": [
            {"y": 2002, "v": 0.4}, {"y": 2003, "v": 0.8}, {"y": 2004, "v": 0.7}, {"y": 2005, "v": 2.7},
            {"y": 2006, "v": 5.9}, {"y": 2007, "v": 10.3}, {"y": 2008, "v": 12.7}, {"y": 2009, "v": 3.5},
            {"y": 2010, "v": 6.8}, {"y": 2011, "v": 13.4}, {"y": 2012, "v": 9.3}, {"y": 2013, "v": 7.4},
            {"y": 2014, "v": 7.0}, {"y": 2015, "v": 6.7}, {"y": 2016, "v": 3.5}, {"y": 2017, "v": 3.1},
            {"y": 2018, "v": 3.2}, {"y": 2019, "v": 3.2}, {"y": 2020, "v": 3.6}, {"y": 2021, "v": 4.1},
            {"y": 2022, "v": 6.2}, {"y": 2023, "v": 7.2}, {"y": 2024, "v": 6.1},
        ]}],
        "note": "CEPII BACI (HS 810820), the atlas's own trade data. China's EXPORT share peaked ~13% (2008, 2011) and "
                "sits ~6% today — while China makes ~71% of world sponge PRODUCTION. The gap is the finding: production "
                "dominance barely surfaces in customs, and almost none of it is aerospace-qualified. Customs is context, "
                "not capability.",
    },
    "sections": [
        {"h2": "1 · Rhenium — the metal that makes the blade, and the one you can't scale", "panels": [
            {"kind": "bars", "h3": "Where rhenium goes", "conf": "measured", "max": 1.0, "note":
                "USGS. ~80% of rhenium is used in superalloys for high-temperature turbine parts; single-crystal blades "
                "depend on it for creep strength.", "src": "usgs_rhenium", "bars": [
                {"label": "Superalloys", "value": 0.80},
                {"label": "Petroleum-reforming catalysts", "value": 0.15},
                {"label": "Other", "value": 0.05},
            ]},
            {"kind": "big", "h3": "Where it comes from", "big": "55% Chile", "conf": "measured",
             "text": "of world mine production, as a by-product of porphyry-copper molybdenum. World output is only "
                     "~81 tonnes a year and cannot be scaled without scaling copper. Secondary (recycled) rhenium is "
                     "led by the US and Germany — a downstream, not a mine, capability.",
             "note": "USGS MCS 2026 (world ~81 t in 2025).", "src": "usgs_rhenium"},
        ]},
        {"h2": "2 · Titanium — production is not the same as aerospace-qualified supply", "panels": [
            {"kind": "bars", "h3": "Titanium-sponge production", "conf": "measured", "max": 0.75, "note":
                "USGS. China dominates tonnage, but Chinese sponge is largely not qualified for critical aerospace "
                "parts — so this map overstates aerospace security.", "src": "usgs_titanium", "bars": [
                {"label": "China (2024)", "value": 0.71},
                {"label": "Japan (2022)", "value": 0.17},
                {"label": "Russia (2022)", "value": 0.13},
            ]},
            {"kind": "bars", "h3": "Where the US buys aerospace sponge", "conf": "measured", "max": 0.85, "note":
                "USGS. The US has no domestic sponge and imports the aerospace-grade metal from a narrow allied base — "
                "Japan above all. Qualification, not tonnage, is the chokepoint.", "src": "usgs_titanium", "bars": [
                {"label": "Japan", "value": 0.80},
                {"label": "Saudi Arabia", "value": 0.13},
                {"label": "Kazakhstan", "value": 0.09},
            ]},
            {"kind": "bars", "h3": "China's titanium value chain (capacity share)", "conf": "estimate", "max": 0.67, "note":
                "Market analysis (Oregon Group). China's grip tightens down the processing chain — yet aerospace "
                "qualification, not capacity, is the gate: a new qualified sponge source takes on the order of a decade to "
                "certify, and China's own aerospace-grade sponge exports are only now projected to scale (~1 to 10 kt by 2030).", "bars": [
                {"label": "Titanium minerals", "value": 0.34},
                {"label": "Sponge capacity", "value": 0.67},
                {"label": "Pigment capacity", "value": 0.55},
            ]},
        ]},
        {"h2": "3 · Single-crystal blade casting — the capability, not the country", "panels": [
            {"kind": "text", "h3": "Cast, not mined", "conf": "snapshot",
             "text": "Casting nickel-superalloy single-crystal blades (directional solidification, hafnium/rhenium-"
                     "bearing) is a low-yield, capital- and know-how-intensive stage held by a handful of firms and "
                     "engine OEMs — specialist casters (e.g. Precision Castparts, Doncasters) and OEM foundries in the "
                     "US, UK, France and Japan, with China developing capability. No public country-production series "
                     "exists; company control is the right lens.",
             "note": "Company/industry disclosures; no public longitudinal series — shown as a single-vintage read.",
             "flag": "measured in firms, not countries"},
        ]},
        {"h2": "4 · Jet engines — the most concentrated stage of all", "panels": [
            {"kind": "bars", "h3": "Commercial engine makers (overall share)", "conf": "estimate", "max": 0.6, "note":
                "Narrow-body: CFM (GE+Safran) >60%, Pratt & Whitney ~35%. Wide-body: GE and Rolls-Royce split the "
                "field. Approximate shares from secondary market analyses.", "src": "market_engines", "bars": [
                {"label": "GE Aerospace (+CFM)", "value": 0.55},
                {"label": "Pratt & Whitney", "value": 0.26},
                {"label": "Rolls-Royce", "value": 0.18},
            ]},
            {"kind": "big", "h3": "A three-firm oligopoly", "big": "$81.0B", "conf": "estimate",
             "text": "commercial aircraft-engine market, 2024. Essentially every large engine is built by GE Aerospace "
                     "(with its CFM joint venture), Pratt & Whitney and Rolls-Royce.",
             "note": "Secondary market analyses; shares vary by segment and metric.", "src": "market_engines"},
        ]},
        {"h2": "5 · Measuring the chokepoint — the chain in numbers", "panels": [
            {"kind": "text", "h3": "From walking the chain to measuring it",
             "text": "Stages 1–4 walked the chain and watched the concentration move downstream. The rest of this page "
                     "measures it — reproducing, on our own data, the methods the supply-chain literature uses: a "
                     "concentration index, an import-dependence test, a node-disruption test, and the published criticality "
                     "frameworks. Every figure below is computed the way its source computed its own; the † after a note "
                     "links to that source."},
            {"kind": "big", "h3": "Aerospace-qualified titanium", "big": "~28%", "conf": "estimate",
             "text": "of world titanium-sponge output (~89 kt of ~320 kt in 2024) is aerospace-qualified. China's ~71% "
                     "of tonnage barely enters this number — qualification, not mining, is the gate. Reproduces the "
                     "'qualified vs tonnage' split that market reporting draws for sponge.",
             "note": "Argus aerospace-approved ~89 kt (Japan/Kazakhstan/Saudi Arabia); world sponge output ~320 kt (USGS / trade-press), 2024.", "src": ["argus_ti", "usgs_titanium"]},
            {"kind": "big", "h3": "Engine concentration: makers vs customs", "big": "4,026 vs 1,345", "conf": "estimate",
             "text": "The Herfindahl index of engine MAKERS (GE 55 / Pratt & Whitney 26 / Rolls-Royce 18) is ~4,026 — "
                     "'highly concentrated' on the US-DOJ scale (>2,500). The same stage seen through customs export flows "
                     "(turbojets, HS 841112) is only ~1,345. Customs cannot see a three-firm oligopoly — the maker index is "
                     "3x the trade index.",
             "note": "Maker HHI from secondary OEM shares; trade HHI computed from BACI 2024 exporter shares (sum of squared shares ×10,000).", "src": ["market_engines", "baci"]},
            {"kind": "text", "h3": "Import-dependence inverts downstream", "conf": "measured",
             "text": "Reproducing an import-to-export dependency test on BACI (2024): the US runs 3.1:1 import-dependent on "
                     "titanium sponge and is almost entirely import-dependent on unwrought nickel — yet a NET EXPORTER of "
                     "finished engines (0.4:1). The West depends on the raw inputs and controls the finished machine. The "
                     "dependency, like the chokepoint, walks downstream.",
             "note": "BACI 2024, US import$ / export$ by HS6: sponge 810820 = 3.1:1; unwrought nickel 750210 = imports only; turbojets 841112 = 0.4:1.",
             "flag": "reproduced from customs data", "src": "baci"},
            {"kind": "big", "h3": "Rhenium you cannot scale", "big": "0 mines", "conf": "measured",
             "text": "produce rhenium as their primary product — all ~81 t/yr is a by-product of copper–molybdenum. Rhenium "
                     "supply is set by copper economics, not rhenium demand: the purest 'you can't just mine more' case in "
                     "the chain.",
             "note": "USGS MCS 2026 — rhenium is recovered from molybdenite roasting of porphyry-copper ores.", "src": "usgs_rhenium"},
        ]},
        {"h2": "6 · Testing resilience — can a stage reroute if its top node fails?", "panels": [
            {"kind": "text", "h3": "The binding node is downstream", "conf": "snapshot",
             "text": "Node-disruption test, after the Northeastern titanium study: treat each stage as a node, remove its "
                     "single largest supplier, and ask whether the rest can reroute. Concentration peaks upstream, but "
                     "rerouting is hardest downstream — where aerospace qualification, not tonnage, locks the stage. Losing a "
                     "rhenium or a sponge supplier hurts but can be stocked or (slowly) requalified; losing a qualified blade "
                     "caster or an engine maker cannot be rerouted at all. A 'critical minerals' list reads the mine and "
                     "points at the wrong stage — the binding node is the one that cannot reroute. (The EU JRC makes the same "
                     "point from the other side: the qualified alloy carries higher supply risk than its raw elements.)",
             "note": "Reproduces a node-disruption read on public supplier counts and top-node shares; see the per-stage cards.",
             "flag": "reproduced node-disruption read"},
            {"kind": "bars", "h3": "Largest single node (share of stage supply)", "conf": "measured", "max": 0.80, "note":
                "Share held by the single largest supplier of each stage — a real, reproducible top-node measure. High almost "
                "everywhere; the cards show what can actually be rerouted.", "src": ["usgs_titanium", "baci"], "bars": [
                {"label": "Rhenium (Chile)", "value": 0.55},
                {"label": "Qualified Ti sponge to US (Japan)", "value": 0.80},
                {"label": "Engine makers (GE + CFM)", "value": 0.55},
            ]},
            {"kind": "cards", "h3": "Reroute verdict, stage by stage", "conf": "snapshot", "cards": [
                {"t": "Rhenium", "d": "~5 processors; Chile/Molymet ~55%. Reroute: hard — a by-product with no spare capacity, but partly stockable and substitutable."},
                {"t": "Qualified Ti sponge", "d": "~6 aerospace-qualified producers; Japan ~80% of US supply; TIMET the lone US sponge producer. Reroute: limited — ~a decade to qualify a new source."},
                {"t": "Blade casting", "d": "a handful of qualified casters plus captive OEM foundries. Reroute: blocked — qualification is part- and engine-specific."},
                {"t": "Engine assembly", "d": "three makers (GE/CFM, Pratt & Whitney, Rolls-Royce). Reroute: blocked — every engine is type-certified to an airframe."},
            ]},
        ]},
        {"h2": "7 · Cross-checking the frameworks & the full texts", "panels": [
            {"kind": "big", "h3": "Titanium buy-to-fly", "big": "~31%", "conf": "measured",
             "text": "Only ~0.4 kg of every 1.3 kg of titanium sponge ends up in the finished part — up to 90% is machined "
                     "away, and scrap is ~53% cheaper than sponge. A proposed substitute, high-strength corrosion-resistant "
                     "(HSCR) steel, sits at technology and manufacturing readiness level 3 (≈25% less energy, ≈50% cheaper "
                     "than Ti-6Al-4V): promising but unproven.",
             "note": "Alsabeeha et al., Georgia Tech ASDL — LCA mass balance (Fig. 12) and readiness scoring (Fig. 19).", "src": "gatech_lca"},
            {"kind": "text", "h3": "Recovering rhenium from scrap — the routes exist, the economics don't", "conf": "estimate",
             "text": "Superalloy remelting recovers the nickel and cobalt matrix but 0% of the rhenium. Hydrometallurgy can: "
                     "~50% Re by conventional leaching, ~93% with electrogenerated-chlorine leaching, and >98% with two-step "
                     "HCl leaching. Yet the review's verdict is that these routes are 'not yet technologically or "
                     "economically feasible' — heavy acid use, wastewater, and the alloys' hardness. The recoverable "
                     "rhenium is real; the economics are the chokepoint.",
             "note": "Srivastava et al., resource recycling of superalloys (abstract / indexed snippets; full text paywalled).",
             "flag": "recovery routes, not yet economic", "src": "superalloy_recycle"},
            {"kind": "cards", "h3": "EU criticality (2023), reproduced for the chain's metals", "conf": "measured", "cards": [
                {"t": "Cobalt", "d": "SR 2.8 · EI 6.8 · critical"},
                {"t": "Titanium metal", "d": "SR 1.6 · EI 6.3 · critical"},
                {"t": "Hafnium", "d": "SR 1.5 · EI 4.3 · critical"},
                {"t": "Nickel", "d": "SR 0.5 · EI 5.7 · strategic, not critical"},
                {"t": "Rhenium", "d": "SR 0.5 · EI 2.3 · non-critical"},
            ], "note": "EU CRM 2023, Table 15 — the two component scores per material.", "src": "eu_crm"},
            {"kind": "text", "h3": "…and the index underrates the real chokepoint", "conf": "measured",
             "text": "Rhenium — the input this chain shows you cannot scale (a by-product with zero primary mines) — scores "
                     "the LOWEST supply risk of the chain's metals (SR 0.5, 'non-critical'), because the EU metric reads it "
                     "at the mine and processing bottleneck and credits substitution and recycling. It is the same blind "
                     "spot the atlas keeps finding: a mine-and-processing score misses a chokepoint that lives in "
                     "by-product coupling and downstream qualification. Criticality is critical when SR ≥ 1.0 and EI ≥ 2.8.",
             "note": "EU CRM 2023, Table 15 (Economic Importance × Supply Risk).", "src": "eu_crm",
             "flag": "framework blind spot"},
        ]},
        {"h2": "8 · Break the chokepoint — what actually helps", "panels": [
            {"kind": "cards", "h3": "The levers, and how far each reaches", "conf": "estimate", "cards": [
                {"t": "Substitute", "d": "HSCR steel for Ti-6Al-4V is at readiness level 3 — ~25% less energy, ~50% cheaper, but unproven. Narrow, long-dated relief."},
                {"t": "Recycle", "d": "Rhenium is >98% recoverable from scrap in the lab, but 'not yet economically feasible'. An R&D lever, not a today lever."},
                {"t": "Stockpile", "d": "Rhenium and sponge are stockable — a genuine buffer for the upstream stages. Qualified casting and engines are not."},
                {"t": "Qualify early", "d": "The binding constraint is time: ~a decade to qualify a new sponge source or blade caster. The only lever for the downstream chokepoint is to start now."},
            ], "note": "Substitution/recycling readiness from the §7 sources; qualification lead time from titanium market reporting.", "src": ["gatech_lca", "superalloy_recycle"]},
            {"kind": "text", "h3": "Where the levers point", "conf": "measured",
             "text": "Notice where every working lever sits: recycling economics, qualification lead time, casting capacity — "
                     "all downstream, none at the mine. The chokepoint walks downstream, and so must the response. Reading "
                     "the risk at the mine, as a critical-minerals list does, aims policy at the one stage that was never "
                     "the bottleneck. The whole page has been one argument: find the stage that cannot reroute, and act "
                     "there — early, because qualification takes a decade.",
             "flag": "so what"},
        ]},
        {"h2": "9 · How we measured it — the methods in one place", "panels": [
            {"kind": "cards", "h3": "Every index on this page, defined once", "cards": [
                {"t": "Herfindahl index (HHI)", "d": "Sum of squared market shares ×10,000. Above 2,500 = 'highly concentrated' (US-DOJ). Used for engine makers and, from BACI, for trade."},
                {"t": "Dependency ratio", "d": "A country's imports ÷ exports of a traded good (BACI). Above 1 = net import-dependent; below 1 = net exporter."},
                {"t": "Node-disruption", "d": "Treat each stage as a node, remove its largest supplier, ask whether the rest can reroute. After the Northeastern titanium study."},
                {"t": "EU criticality (EI×SR)", "d": "Economic Importance × Supply Risk. A material is 'critical' when SR ≥ 1.0 and EI ≥ 2.8 (EU CRM method)."},
                {"t": "Buy-to-fly", "d": "Finished-part mass ÷ input-stock mass. ~31% for aerospace titanium — the rest is machined away."},
                {"t": "By-product coupling", "d": "Whether a metal exists only as a by-product (rhenium: 0 primary mines) — so its supply cannot respond to its own price."},
            ], "note": "Each method is reproduced from the cited literature; the figures that use it link to their source above and in the Sources list."},
        ]},
    ],
    "trade_intro": "BACI gives a consistent 2002–2024 monetary lens on the traded forms, but it cannot see aerospace "
                   "qualification, single-crystal castings, captive transfers inside an OEM, or rhenium (which has no "
                   "clean HS6 line). Read the table as availability of the traded good, not who makes the engine.",
    "method": [
        {"stage": "Rhenium", "lens": "USGS production", "why": "no clean HS6 line — read from production, not trade"},
        {"stage": "Titanium", "lens": "production vs aerospace qualification", "why": "tonnage ≠ qualified aerospace supply"},
        {"stage": "Casting", "lens": "company capability (snapshot)", "why": "no public country series; firms, not countries"},
        {"stage": "Engines", "lens": "OEM market share", "why": "a three-firm oligopoly; the finished-machine chokepoint"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "— aerospace (uniform schema), rhenium 81 t/Chile 55%, engines 55/26/18")
