# Electric-vehicle supply study

Research and publication handoff · 24 November 2026

## Publication assessment

The revised page can serve as a descriptive research briefing after editorial and independent source review. The original’s stage-by-stage structure was useful. It separated batteries, motors and final assembly, and linked to the specialist studies. The methodological weakness was the jump from a concentrated production stage or a globally available engineering alternative to a claim about what would limit actual deliveries. The public data establish location, product mix and trade exposure. A causal research claim requires evidence on which suppliers can deliver to which platforms within a defined disruption window.

The main empirical contribution is a comparison of China-origin EU imports across two tightly defined powertrain categories. From 2024 to 2025, China's share of extra-EU new BEV units fell from 66.8% to 59.2% as China-origin volumes stayed near 440,000. Its corresponding share of new petrol PHEVs rose from 21.3% to 45.3%, with volume growing from 42,587 to 171,431. Combining those categories would show a small fall in share from 56.2% to 54.5% and conceal the difference in direction. The differences are descriptive and do not identify the effect of a tariff, subsidy or change in preferences. [Eurostat Comext DS-045409](https://ec.europa.eu/eurostat/databrowser/view/ds-045409/default/table?lang=en).

## Claims checked

| Earlier claim | Finding and disposition |
| --- | --- |
| China assembled roughly seven in ten electric cars in 2025 | Supported as approximate. The IEA reports about 16 million China-built electric cars and nearly 22 million worldwide. Its manufacturing overview says nearly 75%, and the outlook discussion says 70%. The rounded totals imply roughly 73%. The denominator covers BEVs and PHEVs by factory location. |
| China accounted for around 40% of electric-car exports and about one-quarter of cars crossed major regions | Supported as IEA estimates with different denominators. The export share uses worldwide electric-car exports. The one-quarter uses global output traded among major production and demand centres. Neither measures supplier exposure. |
| Batteries account for around 40% of EV value | The original evidence did not supply a matched cost or price denominator. Withdrew the blanket percentage. A future component-cost comparison needs vehicle class, year, pack size and chemistry, a consistent cost basis and a vehicle-level denominator on the same basis. |
| Battery inputs and components are around 80–90% Chinese | Replaced the combined number with reported estimates for cells, cathode active materials and anode active materials. The output figures do not measure mineral refining as a single stage or identify sourcing for a specific vehicle plant. |
| A rare-earth magnet motor can be swapped out | Series-production examples verify alternatives and show why exposure is platform-specific. The evidence establishes engineering feasibility. It leaves the time, investment and qualification needed to change an existing vehicle open. |
| Finished-car exports understate dependence and prove fast assembly substitution | Finished-car trade captures a different exposure from upstream inputs. The direction and scale of the difference need a matched platform and supplier dataset. Removed the implied speed of switching and the causal explanation for production locations. |
| Silicon carbide is gaining share in vehicle inverters | The original did not supply a penetration series with a defined market denominator. The revision identifies power electronics as a separate component and specifies the evidence needed to quantify exposure. |

Primary references for this audit are the [IEA manufacturing chapter](https://www.iea.org/reports/global-ev-outlook-2026/manufacturing-and-trade), the [IEA battery chapter](https://www.iea.org/reports/global-ev-outlook-2026/electric-vehicle-batteries), the [Renault production motor](https://www.renaultgroup.com/en/magazine/energy-and-motorization/all-about-electric-motors-with-no-rare-earths/), the [Volkswagen motor specifications](https://www.volkswagen-newsroom.com/en/volkswagen-id4-pro-4motion-15130/specifications-of-the-id4-pro-4motion-15140) and [US Department of Energy motor research](https://www.energy.gov/cmei/vehicles/research-and-development-advanced-motors-and-electric-drives).

## Data and reproduction

`out/comext_audit.json` preserves public Eurostat annual and monthly cells, observation flags, queries and update dates. Each annual share is the China-origin cell divided by the EU-27 extra-EU total for the same code, year and unit. Vehicle counts use supplementary quantities, and customs values use nominal euros. The annual snapshot also keeps used-vehicle cells for sensitivity checks. Adding used vehicles would reduce the 2025 China share for the BEV basket to 54.9% and the petrol PHEV basket to 26.7%. The used petrol PHEV aggregate contains a large recorded increase in supplementary units relative to declared value and needs a reporting-quality check before any substantive interpretation. The main comparison uses new vehicles with separate CN codes. The diesel plug-in hybrid code 87037000 pools new and used vehicles. [Eurostat Comext](https://ec.europa.eu/eurostat/databrowser/view/ds-045409/default/table?lang=en).

`out/ev_trade.json` is the existing frozen BACI V202601 extract. The article uses its 2024 snapshot and year controls for global gross exports. The Eurostat analysis is separate from the main Atlas customs pipeline. A change in the source’s coverage or vintages should be reviewed before recomputing the tables and updating the dated interpretation.

```text
python ev-chain/record_ev.py
python build_chokepoint_map.py
python check.py datasets
python check.py links
python check.py js
python check.py chokepoint
python -m http.server 8765
```

The first command generates `ev-chain.html` and `out/ev_chain.json` from the committed snapshots and `study.template`. Open `http://localhost:8765/ev-chain/ev-chain.html`. To fetch a new Comext revision, run `python ev-chain/audit_comext.py` first. Compare the returned flags and values with the pinned snapshot. Confirm that the four quarterly counts sum to the annual count for each new-car basket. A data revision that changes a finding needs a dated note.

## Research needed for a production-loss paper

1. **Define the outcome before collecting new data.** For a fixed disruption window, estimate the change in EU-27 deliveries of new BEVs and PHEVs, by segment, relative to a stated baseline. Keep production losses, displaced imports, stock drawdowns and unmet demand as separate intermediate quantities. Use completed vehicles as the outcome. Record battery and motor requirements in the relevant native units.
2. **Build a small linked sample.** Start with the highest-volume EU platforms with public production, registration or homologation records. For each model and plant, record powertrain, cell chemistry and form factor, kWh per car, qualified pack and motor suppliers, country of each production stage, committed quantities, available inventories and the earliest interchangeable supply. Record evidence dates, source coverage by vehicle volume and unknowns. Company headquarters and plant location require separate fields. Use OEM disclosures and independent regulatory or plant-level records where available. Represent unknown supplier allocations and inventory with explicit ranges.
3. **Run comparable shocks.** Compare a time-limited interruption to finished imports with a cut to qualified cell or motor supply, using the same date, geography and time window. Allocate the same stock or substitute capacity only once across models. Compare estimated deliveries with and without each constraint relaxed. Test which ranking survives low and high inventory, compatibility, qualification time and spare-capacity assumptions. Credit reserves, supplier diversification or local capacity only when the affected platform can receive usable supply in time.
4. **Validate before claiming industrial effects.** Freeze the baseline and scenario rules, compare against a documented supply interruption, and compare with a simple import-share-only benchmark. Report coverage, ranges and out-of-sample errors. Treat an effect of policy as a separate question requiring a comparison design, evidence on concurrent demand and supply changes, and pre-trend checks. Publish the dataset, calculations and major amendments together.
