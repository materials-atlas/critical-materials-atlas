# Wind-turbine chain pilot (unpublished)

This workspace follows the product chain:

`materials → components → nacelle/rotor → turbine → wind farm → operation/recovery`

It is not linked from the live Atlas and does not modify the permanent-magnet profile or pilot.

## Evidence design

| Layer | Coverage | Measure |
|---|---|---|
| Deployment | 2000–2025 | IRENA cumulative operating capacity and annual net change |
| Customs context | 2002–2024 | BACI finished generating sets and broad component baskets |
| Drivetrain adoption | 2010–2012 | Direct-drive share of global turbine supply |
| Cost | 2010 / 2024 | Global weighted-average onshore-wind LCOE |
| Material design | 2024 | JRC kg/MW estimates by generator architecture |
| Manufacturing capacity | 2025 target, 2023 vintage | IEA project-announcement estimate |
| Supplier market | 2025 | GWEC mechanically installed capacity by OEM |

## Rebuild and view

```text
python wind-chain/fetch_irena.py     # refresh official IRENA raw cache
python wind-chain/record_wind.py
python wind-chain/extract_baci.py
python -m http.server 8765
```

Open `http://localhost:8765/wind-chain/wind-chain.html`.
