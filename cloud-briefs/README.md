# Cloud-session briefs

> **Audited 2026-10-03.** The briefs below were written before the cube went bilateral. The
> instruction "`out/cube.parquet` is tonnage-based" appeared in all seven and is now false — it has
> been replaced everywhere, because an agent acting on it would read euros as tonnes. Per-brief
> status is at the bottom of this file.

Each file here is one self-contained job for a hosted coding session, written to be pasted in as the
opening prompt against `materials-atlas/critical-materials-atlas`. They are briefs, not runnable code,
and nothing here is imported by the site build.

Why they exist: a hosted session runs against the GitHub repo rather than on the author's PC, which
suits long self-contained jobs. A job started from a local terminal does **not** draw on hosted credit
even when it is given an isolated worktree, so these have to be launched from the web interface.

House rules every brief inherits, and repeats so it stands alone:

- **`check.py` must pass**, and a new guard is verified by injection: break the thing it guards,
  confirm the guard fails, restore, confirm it passes. Say in the report that this was done.
- **Never `runner.py --force`.** After any page rebuild the runner reruns the post-passes
  (`add_canonicals.py`, `add_head.py`, `clean_links.py`, `build_search_index.py`).
- **Determinism**: no reliance on `hash()`, set/dict iteration order or unseeded randomness.
- **A pull request, never a push to `main`**, and the PR description carries the numbers a reviewer
  needs, including what was not done.
- **Money and tonnes are separate measures, and the cube now carries both.** Read `currency_denom`
  (USD / EUR / `_T` for physical). The chain JSONs are value-based. State the basis in every figure.
- **The cube is bilateral since 2026-10-02**, on the IMF BPM6 structure (`DSD_BPM6.md`): 13
  dimensions, 3.52M rows private, 1.30M published. `counterpart_area` and `country_iso3` each hold
  totals beside their own components, so summing across either double counts. Aggregate only
  through `cube_query.totals()`, which requires both scopes for exactly that reason.
- **Never sum sources for one flow**; never treat a zero declaration as a declaration.
- **A negative result is a result.** A refinement that does not beat what it replaces is reported as
  such and not adopted. Reconciliation v2 (PR #2) is the worked example.
- Off limits: anything under `BOP_extraction` or `rbop-archive` (Banque de France material), and any
  raw non-open-licence holding. Publish what is derived; a refusal ships a retrieval recipe.

| brief | job |
|---|---|
| `review-scrap.md` | adversarial review of the scrap-price study |
| `review-export-controls.md` | adversarial review of the export-controls study |
| `review-grid-trade.md` | adversarial review of the build-out / grid-trade note |
| `review-revisions.md` | adversarial review of the USGS revision study and its amendment |
| `guard-derived-drift.md` | widen the guards against derived-output drift |
| `clean-routes.md` | the clean-route restructure |
| `reconcile-monthly-benchmark.md` | a benchmark that could actually separate reconciliation v1 from v2 |


## Status of each brief, audited 2026-10-03

Checked against what changed on 2 and 3 October, so no credit is spent on a settled question.

| Brief | Status | Why |
|---|---|---|
| `reconcile-monthly-benchmark` | **more worth doing than when written** | It asks for a benchmark able to separate reconciliation v1 from v2, because annual BACI carries ~1.166 log points of its own noise and cannot. The ingredient it needs has since appeared: genuinely cross-compiler matched pairs went from ~105 to **~9,060 across 20 months**. The question is still open — v1 remains the published estimator — and it is now answerable. |
| `review-revisions` | **still valid, with a wider target** | The USGS revision study has since widened to 27 commodities and gained the PGM split. Nothing in it has been adversarially reviewed by an outside reader. |
| `review-scrap` | **still valid** | Three filings share `/scrap` and none has had an outside review. |
| `review-export-controls` | **still valid** | Unchanged since filing; the antimony/bismuth signals are still exploratory and unreviewed. |
| `review-grid-trade` | **still valid** | Two filings share `/grid-trade`. Note it already survived three reviewers before publication, so expect a thinner return than the others. |
| `guard-derived-drift` | **partly overtaken — narrow it before running** | Four guards have been added since (`refresh`, `search`, `counterpart`, `aggregation`) and several drift instances closed by hand: stale figures on `data.html`, the manifest disagreeing with `cube_query.IDENTITY`, and `check.py` duplicating a constant it was meant to check. The remaining surface is smaller than the brief assumes. |
| `clean-routes` | **still valid, and now cheaper** | The sitemap is 214 entries (three dead URLs removed) and the search index finally matches it, so the route inventory the job starts from is already correct. |

**Not covered by any brief:** the self-audit study (`/self-audit`, filed 24 September) has never had
an outside review, and it is the one that audits the atlas's own published claims. If a single
credit-funded review is worth most, it is probably that one.
