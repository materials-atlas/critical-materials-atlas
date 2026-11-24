# Methods and uncertainty

## Concentration

BACI V202601 HS17 records cross-border flows by product. The GOES basket
uses both widths, HS 722511 and 722611. For value HHI, sum export values
by exporter, divide by world export value and sum squared shares. For
the pooled 2022–24 result, add each country's annual export values before
forming shares. For mass HHI, sum positive reported quantities by
exporter and divide by the total of those quantities. The builder reports
what share of export value has a positive quantity. BACI can reconcile
and estimate quantities. This check is sensitive to data quality and
the product mix. Split results show the consequence of using one width.

Exporter shares describe goods crossing borders. Domestic sales,
re-exports and differences in prices and quantities can shift the
relationship to output in either direction. GOES grade, source mill and
technical end use are not present in these customs headings. Neither
concentration measure ranks available production.

## Regional exposure

The 2024 EU point measure uses gross imports from China divided by EU27
sold production plus extra-EU imports minus extra-EU exports. It uses the
value of the same customs numerator with different denominators for
import exposure and apparent-supply exposure. The UK is excluded from
both trade sides and `EU27_2020` specifies production. Reproduce the
published formula from the checked-in amounts to the displayed
precision. The independent current Eurostat pull subtracts published
GB and XI flows from the extra-EU aggregate where supplied separately.
It confirms the historical point shares to their published whole-percent
precision, with small source-vintage and rounding differences. The
cross-check stores production flags and the exact code lists.

Sold production, customs values and inventory movements represent
different objects. Imports from China may be re-exported. Public annual
tables do not link each export with its preceding import origin, and
goods origin does not identify embedded inputs. The reported measure
does not quantify retained imports or final absorption. Avoid summing
adjacent products with overlapping physical content.

The 2024 official crosswalk matches the headline codes for GOES,
liquid-dielectric transformers and large inverters. This establishes a
statistical link. Transformers include distribution and other
applications. The highest product bin is above 10 MVA and still broader
than the US 100 MVA threshold or Europe's transmission-voltage bands.
GOES grades remain pooled. Inverter classification uses power in the
2024 basket and the 2026 customs split uses function.

The GOES mass check uses Prodcom kilograms and Comext quantities in
100 kg units converted to kilograms. The narrow strip production
quantity carries a rounding flag. The US customs comparisons use the
September paper's Census Bureau extracts with no independent US
apparent-supply denominator. EU and US neither share the same immediate
buyers nor the same product specification constraints.

## Sensitivity

Keep Eurostat flags separate from analyst-selected perturbations. The
source's rounding-base diagnostic applies the published base on either
side of the reported production value while holding customs values
fixed. Production below zero is physically impossible. When the supply
denominator can reach zero, no useful upper share follows from that
formula.

The modelled EU values vary production ±10%, customs values together
±5%, gross exports ±10%, or the retained portion of gross Chinese
imports from 75% to 100%. The scope case excludes 10% of reported
apparent supply and assigns the excluded amount to Chinese or other
supply as far as total amounts allow. This shows the influence of
misalignment without pretending to know the actual product split.
The combined case checks all endpoint combinations except product scope.
The display reports numerical exposure bands using the original cutoffs
of 10%, 25% and 50%. The scenarios do not define probability,
confidence intervals or shortage severity.

## Transformer trade regressions

The replication uses BACI HS02 V202601 and the original 2012–2024
transformer and control baskets. It reuses the minimum-value and unit-value
filters, flow and year effects, tariff-line bootstrap and seeds. The
2023–2024 differences are relative to 2012–2020. Convert a log point
estimate or interval endpoint to percent with `100 × (exp(b) − 1)`.
For the heavy-machinery comparison, the filed pre-trend fails when an
absolute pre-period gap exceeds 0.05 log points in 2014–2018. The
replication matches the published violations. Neither a positive
estimate nor the zero-crossing interval establishes a causal transformer
supply shock. Unit values can shift with the type or rating of
equipment, in addition to prices.

## Project timing

Site readiness equals permit duration plus construction duration.
Procurement and network readiness run independently from project start
in the illustration. Completion equals the latest of equipment
arrival, site readiness and network readiness, plus installation and
commissioning. Reduce equipment arrival by six months and recompute
completion while holding other paths fixed. The result is conditional on
receiving a qualified unit at the earlier date. It does not estimate how
many projects are equipment-led or how much factory expansion is needed
to change a delivery date.

For a capacity finding, define the specification, region and period,
obtain incremental qualified output and comparable orders, and measure
positive unmet demand divided by demand. Account for existing contracts,
grades, rated equipment, staffing, component supplies, downtime, test
slots, vendor approval and delivery. Independent review should check
the product correspondence, the separate value and mass results, and a
utility procurement or construction schedule used to calibrate the
critical-path assumptions.
