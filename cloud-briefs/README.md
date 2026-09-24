# Cloud-session briefs

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
- **Money and tonnes are separate measures.** The chain JSONs are value-based, `out/cube.parquet` is
  tonnage-based. State the basis in every figure.
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
