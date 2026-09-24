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

**2026-09-24 — deviation 2: the headline claim turns out not to be testable, and the subset that is
testable is not a sample of it.** Logged immediately on seeing the coverage, before any verdict was
written up.

The concentration study covers 23 critical materials. Only 10 have a counterpart in the
fifteen-commodity revision panel, so only 10 have a measured revision pool to resample from. The other
13 - fluorspar, lead, vanadium, phosphate rock, magnesite, bismuth, feldspar, chromium, zinc,
molybdenum, titanium, barytes and the platinum-group metals - are untestable here.

The selection is not neutral. The median change across the 10 testable materials is **-0.003**; across
the 13 untestable ones it is **+0.060**; across all 23 it is the published **+0.046**. The materials we
can test are almost exactly the ones that did not concentrate. Any statement of the form "the headline
is fragile under revision noise" computed on those 10 would therefore be a statement about a different
population, and the filing's own rule 2 - counts are reported as N of M with M defined - exists to stop
precisely that.

**So the headline is reported as UNTESTED, not as passed or failed**, and the per-material verdicts
stand on their own. Two consequences, decided now rather than after seeing what they do to the result:

1. The per-material table is published as it is, with the selection printed beside it.
2. The panel is widened to cover the missing 13 where the USGS publishes a chapter for them, and the
   headline is retested once it is. That widening is a change to the revision study's panel, so it is
   logged there as well, and the retest uses this same filed design with no changes to it. If the
   widened test then fails the headline, it is published as a failure - that commitment is made here,
   before the wider panel exists.

**2026-09-24 — deviation 3: the panel was widened, and the retest is run with the design unchanged.**
Logged before the widened test was run, as deviation 2 promised.

Ten of the thirteen missing materials now have a measured revision record: lead, chromium, molybdenum,
fluorspar, phosphate rock, barite, feldspar, titanium, vanadium and zinc. Getting them there cost four
parser repairs, all found by the store guard rather than by reading output, and all logged in the
revision study's own amendment. **No figure for the six filed commodities moves**, which was checked
against the published output before this was written.

Three remain untestable and are named rather than quietly dropped:

- **the platinum-group metals**, because that chapter prints two metals side by side (platinum and
  palladium, each with its own pair of years), so a naive read doubles the world total. It needs its
  own handling and gets none here.
- **magnesite** and **bismuth**, whose older editions put the reserve column headers in a place the
  parser reads as a year, so reserve values would enter the panel carrying years. Rather than publish a
  store with known column errors, both are left out.

With ten of thirteen added, the headline becomes testable, on 20 of 23 materials. The design is
**unchanged**: same draws, same seed, same bands, same proxy caveat. The commitment from deviation 2
stands - if the widened test fails the headline, it is published as a failure.

One comparability note, stated before the result: the USGS chapter behind titanium is *titanium
mineral concentrates*, and the atlas has already found that titanium splits three ways on the
ilmenite-versus-slag definition. Its row is therefore the weakest of the twenty and is flagged.

**2026-09-24 — deviation 4: the pool is not exchangeable across producer size, and the filed
asymmetry claim does not survive it.** Raised by both review engines independently; the design below is
written before it is run, and the filed test is kept and published beside it rather than replaced.

The filed test draws each country-year's revision from one pool covering every country and year of that
commodity. Both reviewers objected that small producers revise proportionally more than large ones,
while an HHI is driven by the large ones, so the test puts too much noise where it matters most.
Measured on the panel, pooling all commodities, the median absolute revision by producer size is:
smallest quartile **9.1%**, 25-50% **7.7%**, 50-75% **5.6%**, 75-90% **6.0%**, largest decile **5.5%**.
The gradient is real and about 1.7x from the smallest quartile to the largest decile; within tungsten it
is 10.8% against 5.1%, within antimony 21.5% against 10.4%, within copper 3.5% against 1.9%.

**Consequence for what was filed.** Deviation 1 argued that independent draws understate uncertainty,
so a pass is weak and a failure is strong. That asymmetry is now withdrawn. Two biases run in opposite
directions: revisions are persistent and correlated in reality, which this design ignores and which
makes the test too easy; and the unweighted pool puts small-producer revision magnitudes on dominant
producers, which makes it too hard. Their net direction is unknown, so **neither a pass nor a failure
here is a bound**, and the page must not claim one. The fragile verdicts in particular are no longer
described as failures "even under a noise model that flatters the finding".

**The sensitivity that is added, specified now.** The same test, with the draw stratified by producer
size: each country-year is assigned to a share quantile bucket (0-25, 25-50, 50-75, 75-90, 90-100,
the same cuts as the diagnostic above), and its revision is drawn only from revisions observed in that
commodity at that bucket - falling back to the commodity's whole pool where a bucket holds fewer than
30 revisions, which is recorded per material. Same 2,000 draws, same seed, same bands.

**How both are reported.** The filed, unstratified test remains the headline number, because it is what
was pre-registered. The stratified run is published beside it and labelled post-hoc. If the two
disagree on any verdict, both are printed and the disagreement is the finding for that material.

**2026-09-24 — deviation 5: audit the claims the concentration study actually stands behind, not the
number a reader quotes.** Filed before these are computed. Raised by the fact-checking pass, and it is
the most important correction to this study.

The concentration study's own note says the full-set median (+0.046 across 23) "is substantially an
artifact of materials ADDED to lists during the window", that frozen to the EU CRM 2011 list - the
seven of our materials that were critical BEFORE the window - the median is **-0.095** and the
pre-window criticals mostly diversified, and that "the honest, robust, control-free finding is the
DIVERGENCE WITHIN criticals". The first version of this page took +0.046, the number the study
qualifies, and reported that it survives noise. That is validating a claim the atlas does not make.

Three things are therefore tested, with the design unchanged (same draws, seed, bands, pools):

1. **The ex-ante 2011 subset.** Median change across the seven materials critical before the window;
   six are testable (the platinum-group metals are not, for the reason already logged). Its published
   value is -0.095, so the question is whether the DIVERSIFICATION of pre-window criticals survives
   revision noise.
2. **The divergence within criticals.** The study's stated honest finding: cobalt concentrated while
   the older export-controlled materials came off monopoly highs. Tested jointly, in the same draw: the
   share of draws in which cobalt's change stays positive AND the median change across antimony,
   graphite and rare earths stays negative. A joint test is the right one, because the claim is about
   the two moving in opposite directions, not about either alone.
3. **The full-set median**, kept, but reported as what it is: a number its own study says is
   substantially a selection artifact. Whatever this audit says about it, the page repeats that caveat
   in the same breath rather than in a footnote.

If the ex-ante result is fragile and the full-set result robust, that is published plainly: it would
mean revision noise cannot erase a number the atlas does not lean on, and can erase one it does.
