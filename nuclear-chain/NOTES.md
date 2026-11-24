# Methods and uncertainty

This release follows the front end of civilian reactor fuel supply. The
reference year, source vintage and unit are recorded alongside the rows.
Mine output measures observed production, including source estimates.
Conversion uses licensed primary capacity. Enrichment uses separative
work capacity. The fabrication table uses tonnes of heavy metal for
listed plant capacity, with separate reactor families where the source
allows. Its light-water table includes some capacity for other reactors.
The four measures cannot be added. Capacity, realised production and
uncommitted supply are distinct.

## Industrial concentration

For each operator table, divide each row by the sum of the included
rows. The Herfindahl–Hirschman Index (HHI) is the sum of the squared
percentage shares on a zero to 10,000 scale. The top-three share adds
the three largest rows. The two smallest enrichment operators are grouped
as in the source. For the historical comparison, normalize the rounded
NEA percentages first. For the CNNC sensitivity, multiply only the CNNC
row by each specified factor, then recalculate the denominator. These are
scenario points. The source does not give a sampling error or a
probability distribution.

The analysis compares the same operator grouping within each source
series. Country of capacity and operator ownership answer different
questions. Urenco is counted once as an operator, even though it operates
across countries. WNA and ESA use some common underlying references.
The company disclosures partly reconcile their inputs. The underlying
plant-level basis for the CNNC and Rosatom differences remains unresolved.
The cited evidence cannot establish unrestricted commercial access to
their capacity.

## Service replacement

Baseline procurement is a proxy for annual service need. Each
counterfactual removes one observed sourcing flow while maintaining the
other baseline deliveries. Treat the exposed flow as constant at `L` per
year throughout the assumed interruption of `T` months. The gross loss
is `L * T / 12`. If replacements start after `d` months, opening usable
stock must cover `L * min(T, d) / 12` before then. Annual replacement is
zero if the stock covers the entire horizon. If the stock covers the
initial wait and still leaves a gap over the horizon, the minimum
constant annual rate after the wait is `(L * T / 12 - stock) * 12 / (T - d)`.
A stock draw is counted once. If stock falls short before replacements
begin, the model records an early service gap and no feasible rate to
avoid that gap within the specified timing.

Stock quantities in the scenario are assumed usable equivalents of the
lost flow. Evidence for region-wide stocks spans several material forms.
Converting those reported bins to usable service equivalents would
require utility-level stage, ownership, eligibility, quality and timing
data. Opening stock is assumed usable from the first month. Buyers must
qualify alternative deliveries and have enough contracted transport and
processing. The simulation varies the start month and usable stock and
repeats the cases with 2024 observed deliveries and purchases. The 2024–25
spread is descriptive variability, not a statistical uncertainty interval.

The EU enrichment rows use ESA deliveries. US rows use the EIA purchases
by delivery year. A joint immediate replacement requirement adds the
lost flows in the same physical unit. Shared suppliers must allocate
separate incremental capacity to each market. The conversion case
isolates the EU procurement lane. It does not extrapolate EU exposure to
the United States or other buyers. Additional rates remain conditional
on actual access, commissioning and contracts.

## Validation limits

The same-year NEA comparison, the 2025 ESA and WNA denominators, and the
estimated CNNC capacity sensitivity test the operator concentration
ordering. The IEA supplier-removal screen uses capacity and demand
outside the same supplying countries. The two new scenarios preserve
demand in the affected markets. Flat stocks and no replacement preserve
the HHI ordering for the EU examples. A reversal is feasible in the
model when accessibility differs by stage. That establishes sensitivity
to assumptions. It provides no estimate of the frequency of reversals.

The ESA reports a realised alternate fuel load at Loviisa plus contractual
diversification across EU VVER utilities. This is evidence that substitution
can occur and that contracting and qualification are different steps. It
does not validate the disruption scenarios. Validation against actual
outages would require verified delivery and uncommitted-capacity schedules,
contract and waiver eligibility, stage-specific usable stocks, qualified
fuel supply by design, and delivery dates relative to planned reloads.
