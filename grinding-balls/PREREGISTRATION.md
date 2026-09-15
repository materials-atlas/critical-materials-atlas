# Pre-registration — grinding balls as a public proxy for ore milled

**Filed 2026-09-13, before any regression has been run.** Only size, scope and data-hygiene facts
were measured before this was written (listed below). Everything that decides pass or fail is fixed
here first, so the result cannot be tuned to the data.

The design was drafted with two independent language models acting as advisors, run separately on
the same brief, and reconciled by hand. Where they disagreed, the stricter choice was kept.

## The question

Grinding balls are the steel media that wear away inside SAG and ball mills. Consumption should scale
with **tonnes of rock milled**, not with tonnes of metal produced. If customs data sees them, two things
follow:

1. **Throughput.** A country's ball consumption tracks its ore milled.
2. **Grade.** Balls per tonne of contained metal rise as ore grade falls (more rock per tonne of copper).

This is a *contemporaneous* proxy test. It is not a leading-indicator test.

## What was measured before filing (and only this)

- Two customs codes: **732611** forged or stamped balls, **732591** cast balls.
- 732611 world trade (CEPII BACI HS02, quantity): 422 kt (2002) → 1,547 kt (2024). China supplies 72%.
  Largest 2024 importers: Chile 227, Brazil 148, Peru 140, Kazakhstan 124, Australia 71 kt.
- 732591 world trade: ~300–600 kt a year, with a 2012 outlier of 1,372 kt. The outlier is one flow,
  Bahrain → Qatar, 783 kt at **$174/t** against a world unit value of $1,100–1,450/t in adjacent
  years. It is not grinding balls. Smaller flows of the same kind exist (Ghana → India 2011, $110/t).
- Chile imports 227 kt and exports 83 kt of forged balls. It, like Peru, Australia, South Africa, the
  United States and Canada, makes balls domestically, and no public series gives that output.

## Data rules (fixed)

- **Primary code: 732611, quantity only.** Values follow Chinese export prices and are not used.
  732591 is contaminated by cement mills and enters robustness checks only.
- **Unit-value screen.** A bilateral flow is dropped when its unit value lies outside **0.4×–3×** the
  quantity-weighted world median unit value of that code and year. The tonnes dropped are reported.
- **Apparent consumption** AC = screened imports − screened exports, floored at zero.
- **Ore milled, Q.** Q = Σ contained metal ÷ (head grade × recovery), over copper, gold, and lead + zinc,
  from BGS World Mineral Statistics mine production. Where no country grade series exists, fixed
  global constants are used, declared now: copper 0.60% at 85% recovery; gold 1.5 g/t at 88%; lead + zinc
  6% combined at 85%. Iron ore is **excluded**: most of it is direct-shipping ore that is never milled.
- **Intensity band** (kg of media per tonne of ore milled): copper 0.4–1.4, gold 0.8–2.5, lead-zinc
  0.4–1.2. Both advisors gave overlapping ranges from the comminution literature (Wills; SME handbook;
  Napier-Munn et al.). **These ranges are to be verified against a primary source before publication;
  if the verified band differs, the gate is re-run with it and the change is logged below.**

## Sample (fixed before seeing any AC-Q relationship)

Countries whose estimated Q exceeds **20 Mt of ore in 2024**, years 2002–2024.

## Step 1 — the coverage gate

For each country, the 2022–24 mean AC divided by the mid-band ball demand (Q × band midpoint):

| Ratio | Tier | Use |
|---|---|---|
| ≥ 0.5 | **A — import-dependent** | enters the tests |
| 0.1 – 0.5 | **B — domestic supply dominates** | reported, never decides a test |
| < 0.1 | excluded | imports are not the input |
| > 2 × upper band | flagged | re-export or misclassification; excluded |

If fewer than **6** countries reach tier A, the study stops at the gate and publishes the gate. That is
a finding in its own right (as it was for explosives).

## Step 2 — throughput test (tier A)

`Δlog AC_it = β · Δlog Q_it + α_i + γ_t + ε_it`, standard errors clustered by country, Driscoll–Kraay
as robustness.

**Pass only if all hold:**
1. β ∈ **[0.4, 1.5]** and p < 0.05.
2. Leave-one-country-out: every β stays within **[0.3, 1.7]**.
3. **Horse race.** Adding cement production growth does not push β out of band, and Q stays the
   stronger regressor. If no cement series can be obtained for tier A, the pass is labelled
   *incomplete*, not a pass.
4. **Placebo code.** The same regression on **731815** (threaded screws and bolts of iron or steel: a
   general industrial steel import) gives a β outside the band or insignificant.
5. **Negative control.** In Australia, direct-shipping iron ore tonnage does not predict ball
   consumption: its coefficient's 95% interval includes zero.

**Automatic fail:** β identified only in levels, only in values, or only when 732591 is pooled in.

## Step 3 — grade test (conditional)

`log(AC_it / contained Cu_it) = δ · log(1 / (grade_it × recovery)) + α_i + γ_t + u_it`

Run only for tier-A countries with a public **mill head grade** series (COCHILCO for Chile, MINEM for
Peru, or equivalent). Pass if δ ∈ **[0.5, 1.5]** and the same ratio does not rise equally in
countries with no grade decline. Tier-B countries (Chile is expected to be one) are shown descriptively
and cannot pass the test. **If no tier-A country has a grade series, the page says the grade question
is not testable from public data.** No proxy grade will be substituted.

## Commitments

1. No edits to this file's rules after this commit; any deviation is appended below with its date and
   reason.
2. The result is published whatever it is: gate only, pass, or fail.
3. Every figure, including flows dropped by the screen, is written to `out/grinding_balls.json`.

## Deviations log

**2026-09-14 — intensity band replaced by verified figures (the rule above required it).**
Made before the coverage gate or any AC–Q comparison was computed. Twelve operations with a
published media rate were read off the primary documents (mine technical reports and feasibility
studies); every figure, page and verbatim line is in `intensity_sources.csv`. The advisors' ranges
were too high:

| Commodity | Filed band (kg/t) | Verified points | Verified band (kg/t) | Midpoint |
|---|---|---|---|---|
| Copper | 0.4–1.4 | 7 (Constancia 0.88, Mantos Blancos 0.66, Vizcachitas 0.60, Cobre Panamá 0.57, Chapada 0.54, Kamoa-Kakula 0.37, Aranzazu 0.33) | **0.33–0.88** | 0.605 |
| Gold | 0.8–2.5 | 3 (Fekola 1.01, Lafigué 0.66, Springpole 0.46) | **0.46–1.01** | 0.735 |
| Lead-zinc | 0.4–1.2 | 2 (Kipushi 0.74, Zinkgruvan 0.36) | **0.36–0.74** | 0.55 |

Consequences, stated before seeing them: lower intensity means lower implied ball demand, so every
coverage ratio rises and tier A can only grow. That makes the gate *easier* to pass, which is the
direction that needs guarding against. Nothing else changes: the tier thresholds, the tests and the
pass bands stay as filed. The gold and lead-zinc bands rest on 3 and 2 operations and are reported
as thin. HPGR and autogenous circuits sit at the low end, so a country dominated by them will look
better covered than it is.

Two facts found in the same search, recorded for the tier-B discussion: Molycop states a nominal
capacity above 472 kt of balls a year in Chile (exhibitor news item, company-supplied, Expomin,
6 Sep 2021), three times Chile's 2024 apparent imports. ME Elecmetal's grinding-media plants are in
China, Zambia and Indonesia; its Chilean and Peruvian plants make liners, not balls (company plants
page).

**2026-09-15 — three details the filing left open, fixed before the gate was computed.**
1. The gate ratio compares 2022–24 mean AC with ball demand from ore milled averaged over the
   *same* 2022–24 years (the filing named years only for AC). Sample membership stays on 2024 ore.
2. BACI flows with no reported quantity carry no tonnes, so they cannot enter AC; they are dropped
   and their value share is reported.
3. "Quantity-weighted world median unit value" = the median of bilateral unit values (value ÷
   quantity) across every flow of that code and year, each flow weighted by its tonnes.
Ore milled uses BGS mine production in contained metal (gold converted from kilograms); lead and
zinc are summed before applying the lead-zinc constant.

**2026-09-15 — gate result, then the throughput test's open details fixed before running it.**
The gate (`gate.py`, `out/grinding_balls.json`) put 10 countries in tier A: Brazil, Ecuador,
Mongolia, Saudi Arabia, Kazakhstan, Bolivia, Ghana, Burkina Faso, Philippines, Côte d'Ivoire. The
threshold was 6, so the study continues. Details the filing did not pin down, fixed now:
1. **Panel.** Tier A only, annual first differences 2003–2024 (levels 2002–2024), each year's trade
   screened with that year's median. A country-year with AC = 0 has no logarithm and is dropped;
   the count is reported.
2. **Inference.** Standard errors clustered by country, p from a t distribution with G − 1 = 9
   degrees of freedom (few clusters). Driscoll–Kraay (maximum lag 2) reported alongside.
3. **Horse race.** BGS reports cement only for Europe, so the series is USGS Minerals Yearbook
   *Cement*, Table 22, seven editions, saved with URLs as `cement_usgs_kt.json`. USGS ends in 2023,
   so the horse race runs on 2003–2023. "Q stays the stronger regressor" means a larger absolute
   t-statistic than cement growth in the joint regression.
4. **Placebo.** HS 731815 apparent consumption for the same tier-A countries, same screen, same
   regression.
5. **Negative control.** Australia alone, 2003–2024: Δlog AC of forged balls on Δlog BGS iron-ore
   mine production, with Δlog Q as a second regressor; the iron-ore coefficient's 95% interval must
   include zero.

A research agent first read the Kamoa-Kakula table as 0.80 kg/t of steel. Checked against the
tonnage column on the same rows, the 0.450 kg/t line is 3 mm ceramic media; steel is 0.367 kg/t.

## Result — throughput test, run 2026-09-15: **FAIL**

Run by `throughput.py` (committed before its first run); every number is in `out/grinding_balls.json`.

| Condition | Filed rule | Result |
|---|---|---|
| 1. Main effect | β in [0.4, 1.5], p < 0.05 | β = 0.35, 95% CI [−0.10, 0.79], p = 0.11 (Driscoll–Kraay p = 0.06); 206 country-years, 10 countries. **Fail** |
| 2. Leave one country out | every β in [0.3, 1.7] | 0.19 (without Côte d'Ivoire) to 0.42; three below 0.3. **Fail** |
| 3. Cement horse race | β in band, Q the stronger regressor | β = 0.34 (out of band); Q t = 1.72 vs cement t = 0.16. **Fail** on the band |
| 4. Placebo, HS 731815 | outside band or not significant | β = −0.29, p = 0.26. **Pass** |
| 5. Australia, iron ore | iron-ore CI includes zero | Not informative: Australia was a net *exporter* of forged balls until 2017, so only 7 annual changes exist. Reported, not counted either way. |

Automatic-fail checks, as filed: the relationship **is** strong in levels with country and year
effects (β = 1.19, p = 0.003) and becomes significant only when cast balls are pooled in
(β = 0.40, p = 0.04). The filing names both as grounds for failure, not rescue: a levels
relationship says countries that mill more import more over the long run, not that imports follow
throughput year to year.

**What the result says.** Across the ten countries where imports can physically be the input,
year-to-year growth in forged-ball imports moves with ore milled only about a third as much as
the physics predicts, and the estimate cannot be told apart from zero. Imported grinding balls
are not a usable annual proxy for ore throughput.

**Step 3 (grade) is not run.** The filing allows it only for a tier-A country with a public mill
head-grade series. The two it names, COCHILCO and MINEM, cover Chile and Peru, both tier B. No such
series has been located for any of the ten tier-A countries; that search was not exhaustive, and
this line will change if one is found.
