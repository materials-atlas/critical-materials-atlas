# Which of our own published findings sit inside their sources' revision noise? — filed 2026-09-24

Filed before any comparison was computed. The revision measurement (`usgs-revisions/`, published at
`/revisions`) established how far a production figure moves between its first printing and its
revision: a median 1.5% for copper's world total, 11.6% for antimony's, and once 42.5%. That
measurement was made about other people's numbers. This one turns it on ours.

**The question.** Of the atlas's own published claims that rest on a production figure, how many state
a change no larger than what that figure has moved on its own?

## Population — fixed here, before the answer is seen

A claim enters if all three hold:

1. it concerns one of the fifteen commodities in the revision panel (antimony, cobalt, copper,
   gallium, germanium, graphite, indium, lithium, magnesium, manganese, nickel, rare earths, tellurium,
   tin, tungsten);
2. it rests on a **production** figure — mine, refinery, smelter or plain production — and not on trade
   value, trade tonnage, price, capacity or reserves;
3. it states a **change**: between two data years, between two vintages, or in a share computed from
   production across years.

Enumerated from the published outputs, not from prose, so the population cannot be curated after the
fact: `out/concentration.json`, `out/mine_refine.json`, `out/capability_years.json`,
`out/production.json`, `out/risk.json`. Every claim found in those files that meets the three tests is
in, whether or not it flatters the atlas. The count of claims examined and the count excluded, with
reasons, are both published.

**Explicitly out of scope, and listed rather than dropped:** trade-based findings (the export-controls
study, the grid-trade and AI build-out notes, the chain pages), price-based findings (the scrap study),
capacity and reserve figures, and any commodity outside the panel. Those rest on sources whose revision
behaviour this atlas has not measured, and a test needs a benchmark.

## The benchmark

From `out/usgs_revisions.json`, per commodity:

- a claim about a **world total** is measured against that commodity's world median |revision| and its
  largest observed world revision;
- a claim about a **country series** is measured against that commodity's country median |revision|,
  which the study computes separately and which is the right comparator for a country-level number.

## The verdict bands — fixed here

- **INSIDE**: |change claimed| ≤ the median |revision| of the relevant series.
- **MARGINAL**: median < |change claimed| ≤ the largest observed |revision|.
- **OUTSIDE**: |change claimed| > the largest observed |revision|.

## The proxy problem, and how it is handled

The revision record is measured on USGS editions, because the USGS prints two vintages of every year
and the atlas holds thirty editions of it. **The atlas holds no comparable vintage history for BGS or
World Mining Data**, so a claim resting on those is compared against the USGS record as a *proxy*.
Every such row is flagged `proxy`, and the measured USGS-against-BGS gap for that commodity is printed
beside it. No claim is called INSIDE on proxy grounds without that flag visible in the same row. If the
proxy rows turn out to carry the result, the result is reported as proxy-dependent and not as a
finding.

## What a verdict does and does not mean

INSIDE does **not** mean the claim is false. It means the change we published is no larger than the
movement the source itself has shown, so this test cannot distinguish the claim from source movement.
That is a statement about what our evidence can carry, not about the world. OUTSIDE does not mean the
claim is true either — only that revision noise is not a sufficient explanation for it.

## Pre-commitments

1. **The table is published whatever it says**, including the atlas's own flagship concentration
   finding landing INSIDE. A self-audit that exonerates its author is worth nothing.
2. Counts are reported as "N of M" with M defined by the population rule above, never as a universal
   about the atlas.
3. **No rescue.** If a claim lands INSIDE, the page does not then go looking for a different framing of
   the same claim that passes. Any reframing found afterwards is reported as post-hoc and kept out of
   the headline.
4. The medians used are themselves estimates over unequal windows (copper 25 years, gallium 7), and
   every row carries the year count behind its benchmark.
5. If the result is that almost everything passes, that is published too, and read as weak evidence:
   the test is one-sided and a pass is not a confirmation.

## Deviations log

Every change made after this filing goes here, dated, with its reason.

**2026-09-24 — deviation 1: the population is smaller than the filing implied, and the test changes
shape for the claims that survive it.** Filed before any comparison was run; the reasons are structural
and visible in the files themselves, not in any result.

*Exclusions, with the rule each one fails.* `out/mine_refine.json` rests on trade codes and
product-space distances, not production (rule 2). `out/risk.json` publishes scores, not changes (rule
3). `out/production.json` states differences between three sources for the same year, which is a
cross-source difference and not a change between years, vintages or a share across years (rule 3); that
question is already answered elsewhere, by the measured agency gap now printed on the page itself.
`out/capability_years.json` moves its year slider on the trade signal only - its physical share is a
single recent vintage, as the refining page's own caveat states - so it publishes no production change
either (rule 3). What remains is `out/concentration.json`.

*Why the band test cannot be applied as written.* The filing compares "the change claimed" against a
median revision expressed as a percentage of a production figure. The concentration finding is not
stated in those units: it is a change in an HHI, a number between 0 and 1 computed from country shares.
Comparing 0.046 HHI points against 11.6% is a category error, and no rescaling of one into the other is
honest.

*The test that replaces it, specified here before it is run.* Propagate the measured revisions into the
finding instead of comparing to them:

1. Rebuild each material's country-by-year production vectors from `out/cube.parquet`, exactly as
   `build_bgs_concentration.py` does (BGS production rows, dominant form, dominant unit).
2. For each country-year value, draw a signed revision at random, with replacement, from the EMPIRICAL
   pool of that commodity's measured country-series revisions in the USGS panel - the actual observed
   revisions, not a fitted distribution - and multiply the value by (1 + that revision).
3. Recompute the HHI per year, average over 1995-2004 and 2015-2024 as the study does, and take the
   change.
4. 2,000 draws, seed 20260924, so the result is reproducible and the guard can pin it.
5. Report, per material and for the headline median across materials: the share of draws in which the
   published change keeps its SIGN, and the 5th-95th percentile band of the perturbed change.

*Verdicts, fixed now.* ROBUST if the sign survives in at least 95% of draws; FRAGILE if 50-95%; NOT
SUPPORTED below 50%.

*The limitation that must travel with every verdict.* The draws are independent across countries and
years. Real revisions are not: the world total is revised together with its parts, and successive
editions share a method, so genuine revisions are correlated and persistent. Independent draws largely
cancel inside a share, so this test UNDERSTATES the uncertainty and a ROBUST verdict is a weak pass,
not a certificate. A FRAGILE or NOT SUPPORTED verdict, by contrast, is strong: it means the finding
fails even under an optimistic noise model.

*Proxy status.* The concentration finding rests on BGS production and the revision pool is measured on
USGS editions, so every row here is a proxy row in the sense the filing defines, and the result is
reported as proxy-dependent throughout. A material with no counterpart in the fifteen-commodity panel
is excluded and counted.
