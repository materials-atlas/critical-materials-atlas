# Grid equipment in world trade, 2012–2024: did prices or volumes carry the build-out?

Filed 2026-09-18, before any estimate. It replaces `DESIGN.md` (committed first, in the repository's
history) after two independent language models reviewed that draft as journal referees, and after a
verified literature review (`literature.md`, every source opened on 2026-09-18). What the review
changed is listed at the end.

## The question, and what it is not

Transformers, the grain-oriented electrical steel (GOES) in their cores and the copper in their
windings are bought by every part of the electricity build-out: grid replacement, renewables,
electric vehicles, heat pumps and data centres. Public sources record long transformer lead times
after 2021 (under a year before COVID, up to 36 months quoted in 2024: DOE 2024, pp. 2, 12) and a
producer price rise that was steep in 2021–22 and nearly flat in 2023–24 (BLS series WPU117409).

This paper asks what world **trade** in those goods shows: **after 2021, did the value of grid-equipment
trade rise through prices or through volumes, relative to comparable goods, and how much of any price
rise is left once the cost of the steel and copper inside a transformer is taken out?**

Prices and volumes rising together is a demand shift along a supply curve; the ratio of the price
response to the volume response says how steep that curve was (the sign logic of Shapiro 2022 and
Kilian and Murphy 2012). The paper therefore measures **how elastic traded supply was**. It does not
test for a "bottleneck", it does not attribute anything to data centres or AI, and it measures trade,
not production or installation.

## Data

- **Trade.** CEPII BACI, **HS 2002 nomenclature for every year** (pinned: the atlas reader otherwise
  switches nomenclature by year), 2012–2024, through the atlas's single BACI reader. A **flow** is one
  exporter–importer pair in one six-digit line.
- **Copper price.** World Bank Pink Sheet, monthly copper, annual mean.
- **External benchmark.** US producer price index for power and distribution transformers, BLS
  WPU117409, annual mean.
- **Cost shares.** GOES about 25% and copper conductor about 25% of a large power transformer's
  production cost (DOE 2024, citing the 2020 Commerce survey; the Commerce report itself gives GOES only.
  Attribution corrected 2026-09-18 after the fact-check; the shares are unchanged). Used as filed below and varied from 20% to 30% each.

## Sample rules, fixed now

A flow-year enters if value is at least USD 100,000 and tonnes are positive. Unit value (UV) is value
over tonnes. Flow-years whose UV is under a tenth or over ten times the median of their line in that
year are dropped as unit errors; the count is reported, and the headline is re-run with the band at
0.2–5 times and with no band. The main panel is unbalanced (flows enter and leave); flow effects absorb
each flow's level.

## Three designs, reported separately and never pooled

**A. The inputs.** GOES (7225.11, 7226.11) against other flat-rolled alloy steel (7225.30, 7225.40,
7225.50, 7225.99; non-oriented electrical steel 7225.19 is excluded because it goes into motors).
Copper wire (7408.11) against copper cathode (7403.11), which isolates the wire-drawing premium from
the copper price itself.

**B. Finished transformers.** Each of 8504.21, 8504.22 and 8504.23 separately, then together, against
heavy capital goods with steel and copper content but no grid, motor or vehicle function: lifts
(8428.10), cranes (8426.49), crushing machines (8474.20), concrete mixers (8474.31), electric welding
machines (8515.31, 8515.39). Electric motors, pumps and compressors are **not** controls — they share
the electrification demand — and appear only as a labelled contaminated robustness line.

**C. Transformers net of their materials.** For each transformer flow, the UV change minus 0.25 × the
change in the world UV of GOES (7225.11) and 0.25 × the change in the copper price, against the same
controls as B. What is left is the price movement that the cost of the steel and copper does not
explain. Re-run with shares of 0.20 and 0.30 each.

## The estimating equation

For flow *f* in line *l*, year *t*, in levels:

    y_ft = β₁ · (T_l × P1_t) + β₂ · (T_l × P2_t) + α_f + γ_t + ε_ft

- `y` is log UV (price equation) or log tonnes (volume equation); `T_l` marks the treated lines of the
  design; `P1` is 2021–2022 and `P2` is 2023–2024; the pre-period is 2012–2020.
- **No line-year effects** (they would absorb the treatment). Flow effects and year effects only.
- Coefficients are log-point gaps over the average pre-period gap; each is also reported as a percent.
- **Inference.** Treatment is a shock to a product market, so the conservative unit is the line. The
  headline p-values come from a **wild cluster bootstrap by line** (Webb six-point weights, 9,999
  draws). Standard errors clustered by exporter are reported beside them and never used alone.
- Every estimate is printed with its standard error, its 95% interval, and the smallest effect the
  design could detect at 80% power. **No estimate is suppressed for being insignificant.**
- **Splitting P1 and P2 is the point**: 2021–22 carries the energy and freight shock and the recorded
  price rise; 2023–24 is when lead times were still lengthening but the producer price index had
  stopped rising.

## What each outcome means, decided now

There is no single threshold. Each design is read as a pair — the price gap and the volume gap:

| Price gap | Volume gap | Reading |
|---|---|---|
| positive | not above controls | Supply of traded equipment was steep: the build-out showed up in prices, not in more units shipped. |
| positive | also positive | Both moved: demand rose along an upward-sloping supply; the ratio of the two gaps is reported as a rough inverse elasticity. |
| not different | positive | Supply expanded to meet demand; no price signature. |
| not different | not different | No build-out signature in trade relative to these controls. |

**Design C decides how much of any price gap is materials.** If C's gap is less than half of B's, the
page says the transformer price rise in trade is mostly the cost of steel and copper. If C keeps more
than half, the page says it is not explained by those two materials alone.

## Checks, all filed now

1. **Pre-trends.** Year-by-year coefficients for 2012–2024 with 2019 as the base. If any pre-period
   year from 2014 to 2018 lies outside ±0.05 log points of the base, difference-in-differences language
   is dropped and the result is described as a relative pattern.
2. **Placebo period.** The same design on 2012–2016 alone, with 2015–2016 as a fake post period.
3. **Validation of the unit values.** The annual change in the UV of US transformer imports against
   the change in the BLS transformer producer price index, 2012–2024: the correlation is reported. A
   weak correlation weakens every price result and the page must say so.
4. **Who supplied the change.** For each treated line: number of exporters above 1% of world exports,
   China's share, and the share of the top three, in 2019, 2022 and 2024 (unbalanced, all flows).
5. **Importers.** Designs B and C re-run for flows into the United States, the EU27 and the rest,
   because US tariff regimes raise US import unit values.
6. **Exporters.** China versus all other exporters.
7. **Leave one line out** for designs A and B.
8. **Freight.** 2021–22 freight costs fall hardest on heavy, low-value goods; the design B price gap is
   re-run on flows above and below the median UV.
9. **Contaminated controls.** Design B against electric motors (8501.52, 8501.53), pumps (8413.70)
   and compressors (8414.80), labelled as contaminated by shared demand.

**Chip-making equipment (8486.20, 8486.10) is not tested.** Its per-tonne values measure which machines
were shipped, not prices. It is described only by value and supplier concentration.

## What this cannot say, printed on the page

- Nothing about AI or data centres specifically: every buyer of grid equipment is in these flows.
- Nothing about domestic production or installation. A country that makes its own transformers
  never appears here, and US plants raised utilisation from 40% to 78% over 2011–2023 (as reported by
  NLR 2026) - the domestic supply response is outside these data.
- Unit values are not prices: product mix within a six-digit line remains (8504.23 spans roughly 10 to
  several hundred MVA), and BACI converts some quantities reported in units into tonnes. The price
  gaps are upper bounds on price change.
- Nothing about why supply was steep; nothing about permitting, which the IEA names as the main cause
  of transmission delays in advanced economies (IEA 2025).
- Not causal.

## Design review, 2026-09-18 (before any estimate)

The draft was reviewed by two independent language models acting as referees, and by a verified
literature review. Changes:

1. **The claim.** "Does the grid bind before the chip?" and "the signature of a supply constraint"
   promised more than trade data can deliver. Retitled; the question is now how elastic traded supply
   was, following the sign logic in the literature.
2. **Input costs.** Both referees: a transformer price rise may be mostly steel and copper. Design C
   nets them out with verified cost shares; design A tests the inputs themselves.
3. **Controls.** Motors, pumps and compressors share the electrification demand; hot-rolled plate
   follows a commodity cycle. Replaced by heavy capital goods, with the old set kept as a labelled
   contaminated check, and three designs instead of one pooled treatment.
4. **The equation.** The draft wrote line-year effects, which absorb the treatment. Now flow and year
   effects only, in levels.
5. **Inference.** Exporter clustering would overstate precision for a product-market shock. Headline
   inference is now a wild cluster bootstrap by line.
6. **Pre-period.** Three years (2018–2020, including tariffs and COVID) could not establish trends.
   The panel now runs from 2012, in one nomenclature, with a pre-trend rule and a placebo period.
7. **Timing.** 2021–22 and 2023–24 are separate, because the energy shock and the producer price rise
   sit in the first and the lengthening lead times in the second.
8. **Chip equipment.** Dropped from the tests: its unit values measure machine mix.
9. **Unit values.** An external benchmark (the BLS producer price index) is now filed as a check, and
   transformer size classes are estimated separately.
10. **No suppression.** The draft's "not significant, not shown" became: every estimate is printed.

## Result - run 2026-09-18

Run by `analysis.py` (committed before its first run on real data); every number is in
`out/buildout_study.json`, and the full exposition is the paper built from it. Sample: 283,029
flow-years; 4,425 dropped by the unit-value band.

| Design | Price gap 2021-22 | Price gap 2023-24 | Volume gap 2021-22 | Volume gap 2023-24 |
|---|---|---|---|---|
| B. Transformers vs heavy capital goods | +0.028 (+3%, p = 0.105) | +0.178 (+19%, p = 0.011) | +0.025 (+3%, p = 0.497) | +0.160 (+17%, p = 0.011) |
| C. Transformers net of GOES and copper | -0.070 (-7%, p = 0.015) | +0.116 (+12%, p = 0.019) | - | - |
| A. GOES vs other alloy flat steel | +0.027 (+3%, p = 0.520) | +0.109 (+12%, p = 0.073) | -0.068 (-7%, p = 0.180) | -0.035 (-3%, p = 0.639) |
| A. Copper wire vs cathode (exporter-clustered, deviation 1) | -0.041 (-4%, p = 0.023) | -0.015 (-1%, p = 0.414) | +0.032 (+3%, p = 0.752) | +0.153 (+17%, p = 0.267) |

**Reading, by the filed table.** For transformers in 2023-24, price and volume both rose relative to the
controls: demand rose along an upward-sloping traded supply, with the price gap about
1.1 times the volume gap. In 2021-22 neither moved. Net of steel and copper, the 2023-24
gap keeps 65% of its size, so by the filed rule it is **not explained by those two materials
alone**; in 2021-22 the net gap is negative, so over that period materials more than account for it.

**The filed pre-trend rule failed for all five designs it was applied to** (years outside ±0.05 log points: see
`checks.pretrend_rule`), so difference-in-differences language is withdrawn. The transformer result is
described as a relative pattern: transformer unit values relative to the controls fell from
+0.15 in 2012 to 0 in 2019 and then rose to +0.26 in 2024; relative volumes were
-0.16 in 2012, flat from 2018, and +0.17 in 2024. That is a reversal of a decline, and the
average-gap coefficients above understate the size of the turn and overstate how clean it is.

The GOES placebo fails (+0.221, p = 0.024 in the fake 2015-16 period), so the GOES price
series moves this much in ordinary years and its 2023-24 gap is not read as a signature. The unit
values of US transformer imports track the BLS producer price index only moderately (correlation of
annual changes 0.43); every price result carries that weakness.

## Deviations log

Every change made after this filing goes here, dated, with its reason.

**2026-09-18, before any estimate - two details the filing left open, fixed now.**
1. **Design C uses real input prices.** Year effects absorb general inflation for every flow, so
   subtracting nominal steel and copper prices from treated flows alone would also subtract a quarter
   of general inflation from them twice over. The GOES world unit value and the copper price are
   therefore deflated by the US consumer price index (World Bank FP.CPI.TOTL, saved in
   `buildout-study/inputs/us_cpi_worldbank.csv`) before the adjustment, so it removes only input-cost movement
   relative to prices in general.
2. **The bootstrap statistic.** The wild cluster bootstrap by line imposes the null (restricted
   residuals, Webb six-point weights) and compares the absolute estimated coefficient with the
   distribution of bootstrap coefficients; the reported interval inverts the same distribution. The
   smallest detectable effect is 2.8 times the bootstrap standard error.

1. **2026-09-18 - copper wire could not take the line bootstrap.** Design A's copper comparison is one
   treated line against one control line; a wild cluster bootstrap by line needs more than two
   clusters. It is estimated with the same equation and exporter-clustered errors only, labelled as
   such everywhere it appears. Found on the first real run, when the estimator returned nothing.
2. **2026-09-18 - exporter-clustered errors with one exporter.** The China-only exporter split has one
   exporter, so exporter clustering is undefined; those errors are reported as unavailable and the
   line bootstrap stands alone there. A crash fix, found on the first real run.
3. **2026-09-18 - the pre-trend rule was tested on synthetic data before the real run** and shown to be
   crossed by noise alone at realistic line-year shocks. It was kept as filed rather than loosened,
   and it failed on the real data; see the result above.
4. **2026-09-18 - percents were rounded twice.** The analysis stored each percent to one decimal and
   the reports rounded again, so +19.46% printed as +20% and -3.49% as -4%. Percents are now stored to
   two decimals; no coefficient, p-value or reading changed. The two affected figures above are
   corrected.
5. **2026-09-18 - event-study intervals.** The first version drew the year-by-year intervals from
   unrestricted residuals with 2,999 draws, while the headline estimates impose the null with 9,999; the
   chart looked far more certain than the test. Both now use the headline procedure. No coefficient changed.
6. **2026-09-18 - chip equipment.** HS 8486 was created in HS 2007 and does not exist in the HS 2002
   panel, so the filed description returned zeros. It is described in HS 2017 for 2017 and 2024 only.
7. **2026-09-18 - GOES supplier structure.** The first report gave 7225.11 alone as "GOES"; the filing
   defines GOES as 7225.11 and 7226.11. Supplier shares are now reported for both together (China 12% to
   32%, top three 48% to 67%, 2019 to 2024), which is less concentrated than the single line suggested.
8. **2026-09-18 - design C sensitivity.** Both referees showed that netting copper and GOES from the
   treated lines only can mechanically move the gaps, because the controls contain copper and ordinary
   steel. A variant netting GOES alone, the input the controls do not use, is reported beside the filed one.
   Design C is now a sensitivity, not a headline.
9. **2026-09-18 - exploratory, unfiled: electrical equipment against construction machinery.** Asked by
   both referees, run after the result, in `exploratory_electrical_boom.json`: motors, pumps and
   compressors (the filed contaminated set) against the filed capital-goods controls rose too (unit value
   +9%, tonnes +8%, 2023-24), and transformers against construction-only controls (welding machines
   removed) give +22% unit value and +15% tonnes. Labelled exploratory wherever used.

**Consequence for the publication (2026-09-18).** With the pre-trend rule failed and the filed
contaminated-control check showing the transformer gap is not clearly separate from a broad rise in
electrical equipment (+0.095, p = 0.055), the study is published as a descriptive research note, not as
a test result. The note says so in its first section.

10. **2026-09-18 - order-independent bootstrap streams.** Every estimate drew from one random stream,
    so adding an estimate earlier in the run moved later p-values in the third decimal (one went from
    0.051 to 0.057). Each estimate is now seeded from the study seed and its own label. Coefficients are
    unchanged; p-values above are from this run.
