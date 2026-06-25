# Materials crosswalk

The 32 critical raw materials this atlas tracks, with the HS6 trade code used, the stage that code represents, and the headline figure from each data layer.

- **Trade** = CEPII BACI HS22 V202501 (year 2023; primary source UN Comtrade).
- **Mine** = USGS Mineral Commodity Summaries (approximate).
- **Refine** = IEA Critical Minerals Outlook (approximate).

| Material | label | HS6 code | Stage | Top miner (USGS) | Top refiner (IEA) | Top exporter (BACI 2023) |
|---|---|---|---|---|---|---|
| Rare-earth permanent magnets | `magnets` | 85051110 | refined | CN 69% | CN 90% | CN 65% |
| Magnesium, unwrought | `magnesium` | 81041100 | refined | CN 90% | CN 90% | CN 63% |
| Germanium | `germanium` | 81129295 | refined | CN 68% | CN 60% | CN 26% |
| Natural graphite | `graphite` | 25049000 | raw ore | CN 78% | CN 95% | CN 35% |
| Gallium | `gallium` | 81129289 | refined | CN 98% | CN 98% | CN 26% |
| Tungsten, unwrought | `tungsten` | 81019400 | refined | CN 80% | CN 83% | CN 69% |
| Cobalt oxides & hydroxides | `cobalt` | 28220000 | refined | CD 76% | CN 76% | FI 26% |
| Ferro-niobium | `niobium` | 72029300 | refined | BR 88% | BR 88% | BR 75% |
| Natural borates | `boron` | 25280000 | raw ore | TR 47% | TR 60% | TR 52% |
| Lithium carbonate | `lithium` | 28369100 | refined | AU 52% | CN 65% | CL 76% |
| Antimony, unwrought | `antimony` | 81101000 | refined | CN 48% | CN 75% | TJ 23% |
| Platinum, unwrought | `platinum` | 71101100 | refined | ZA 70% | ZA 70% | ZA 33% |
| Palladium, unwrought | `palladium` | 71102100 | refined | RU 40% | RU 40% | RU 24% |
| Fluorspar, >97% CaF2 | `fluorspar` | 25292200 | raw ore | CN 60% | CN 60% | ZA 31% |
| Titanium, unwrought | `titanium` | 81082000 | refined | CN 32% | CN 50% | JP 35% |
| Silicon, < 99.99% | `silicon` | 28046900 | refined | CN 70% | CN 79% | CN 35% |
| Feldspar | `feldspar` | 25291000 | raw ore | TR 28% | TR 30% | TR 44% |
| Ferro-vanadium | `vanadium` | 72029200 | refined | CN 68% | CN 70% | AT 23% |
| Manganese ore | `manganese` | 26020000 | raw ore | ZA 36% | CN 95% | ZA 41% |
| Aluminium ores / bauxite | `bauxite` | 26060000 | raw ore | AU 27% | CN 58% | GN 76% |
| Phosphate rock | `phosphate` | 25101000 | raw ore | CN 44% | CN 40% | JO 26% |
| Baryte | `baryte` | 25111000 | raw ore | CN 30% | — | IN 26% |
| Arsenic | `arsenic` | 28048000 | refined | PE 28% | CN 70% | JP 33% |
| Beryllium, unwrought | `beryllium` | 81121200 | refined | US 65% | US 65% | KZ 80% |
| Hafnium, unwrought | `hafnium` | 81123100 | refined | AU 40% | FR 40% | DE 35% |
| Strontium carbonate | `strontium` | 28369200 | refined | ES 30% | CN 60% | DE 48% |
| Phosphorus | `phosphorus` | 28047010 | refined | CN 70% | CN 70% | KZ 40% |
| Tantalum, unwrought | `tantalum` | 81032000 | refined | CD 40% | CN 40% | CN 23% |
| Coking coal | `cokingcoal` | 27011210 | raw ore | AU 30% | — | AU 42% |
| Helium | `helium` | 28042910 | refined | US 46% | — | QA 31% |
| Refined copper cathodes | `copper` | 74031100 | refined | CL 23% | CN 45% | CL 21% |
| Nickel, unwrought | `nickel` | 75021000 | refined | ID 60% | CN 40% | NO 17% |

**Stage** = which form the HS6 code captures: *raw ore* (HS chapters 25/26/27, mined mineral traded in raw form) or *refined* (processed product). For raw-ore materials the map derives **miners** from real ore exports; for refined materials it derives **refiners** from real refined-product exports — falling back to the USGS/IEA reference shares where the relevant form is not in that trade stream. See `methodology.html` (Limitations) for the full caveats.
