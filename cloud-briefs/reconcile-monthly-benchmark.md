# A monthly benchmark that can actually separate reconciliation v1 from v2

Repo: `materials-atlas/critical-materials-atlas` (public, self-contained).

## Why this job exists

Reconciliation v2 (reliability-variance weights, merged as PR #2) was measured against annual CEPII
BACI and **not adopted**: the headline median favoured it by 0.03% of an error of 1.166 with a
bootstrap interval straddling zero sevenfold, while the paired test favoured the equal-weight geomean
(12,064 flows to 11,389). The reason that benchmark cannot settle the question is stated in the PR:
annual BACI over twelve months carries about 1.166 log points of its own noise - a factor of 3.2 -
which is three orders of magnitude above the effect being tested. It can refuse a refinement; it
cannot certify one.

So the open question is not "is v2 better" but "what could tell us". This job answers that.

## The trap to avoid

The obvious move is to benchmark against monthly customs data. It is circular: `pipeline/reconcile.py`
takes its declarations from exactly five monthly sources - `eurostat`, `comexstat`, `hmrc`,
`uscensus`, `comtrade` - so scoring the reconciliation against any of them scores it against its own
input. Annual BACI is the only current benchmark that is independent, and being annual is precisely
its limitation.

## The design worth trying first: leave-one-source-out, at monthly frequency

This is independent AND monthly, and needs no new data.

1. Drop one source (say `hmrc`) from the reconciliation entirely and rebuild the reconciled series
   from the remaining four.
2. Score that series against the held-out source's own monthly declarations, on the flows where the
   held-out source is one of the two declarants.
3. Repeat for each source in turn.
4. Run it for v1 and v2 under the same protocol, paired on the same flows, and report both the median
   and the paired test - as PR #2 does, because the two readings pointed opposite ways there and may
   again.

What this measures is a real question and not a proxy: can the weighting predict a declaration it was
not shown? State clearly what it does NOT settle - the held-out source is not ground truth either, and
a corridor where the held-out reporter is the loud one is not the same test as one where it is quiet.

Report the result **by held-out source**, not pooled. If v2 wins on the corridors of one reporter and
loses on another's, that is the finding, and it is more useful than a single number.

## The second route, if the first is inconclusive

Find a monthly series that is genuinely outside the five. Named in the code as candidates: OECD ITIC,
and national offices not in the panel (Japan Customs, Korea KITA, India DGCI&S). For each, establish
before ingesting anything: is it monthly, is it HS6, what licence does it carry, and does it already
feed any of the five (if it does, it is circular again). Report what you find even if you ingest
nothing - a written answer to "what monthly data exists that we do not already use" is the deliverable
if the ingestion is too large for one session.

## Non-negotiable, from the existing work

- **A zero weight is not a weight.** `reconcile.py` lines 77-78: treating US Census zeros as
  declarations mis-scored 43,067 flows (11.6%). The guard in `check.py` asserts this; do not weaken it.
- **Never sum sources for one flow.** That bug hit `ac_reconcile` once already.
- **Do not tune on the benchmark and then report the benchmark as validation.** Fix constants before
  the scoring run. Anything decided afterwards is labelled post-hoc, as PR #2 labels its three probes.
- **v1 stays the published default** unless the evidence is clear enough to change it, and changing it
  means rewriting the verdict block in `reconcile.py` to the new numbers - the guard fails on a flag
  flip alone, deliberately.
- Money and tonnes are separate measures: every figure states its basis. The existing benchmark is
  value (USD); the tonnage reconciliation (`qty_recon_kg`) is still unweighted and untested, which is
  itself a gap worth reporting on.

## House rules (non-negotiable)

- `check.py` must pass. Any guard you add is verified by INJECTION: break the thing it guards, confirm
  the guard fails, restore, confirm it passes. Report that you did this.
- Never run `runner.py --force`. If you rebuild a page, the runner reruns the post-passes.
- Determinism: no `hash()`, no set/dict iteration order, no unseeded randomness. Verify by rerunning
  under two hash seeds and comparing output.
- Deliver a PULL REQUEST, never a push to `main`, with the numbers, the verdict and what you did not
  do.
- A negative result is a result. "This design cannot separate them either, and here is why" is a
  perfectly good outcome, and more useful than a thin win.
- Do not touch anything relating to `BOP_extraction` or `rbop-archive`.
