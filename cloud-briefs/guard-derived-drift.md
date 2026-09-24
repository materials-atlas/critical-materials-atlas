# Widen the guards against derived-output drift

Repo: `materials-atlas/critical-materials-atlas` (public, self-contained).

The failure mode, in the author's words: a corrected source does NOT correct its copies. `risk.json`
scored germanium 94 for three weeks after `data.json` said otherwise. The rule learned from it: guard
by comparing the COPY to its source, never by comparing modification times, and verify a guard by
INJECTION.

`check.py` already holds guards of this kind (`stale`, `register`, `ledger`, `basis`, `usgs_mcs`,
`head`, `weights`). The job is to find where a derived figure can still drift from what it was derived
from, and close those paths.

1. **Build the map.** For every `out/*.json` and every page, what reads what? A builder that copies a
   figure out of another builder's output is the risk; one that recomputes from a store is not.
   `runner.py` and `_runner_state.json` know the dependency order - use them, and say where they are
   wrong.
2. **Rank the unguarded copies** by how badly a stale one would mislead a reader. A score or rank on a
   published page is the worst case; an internal intermediate the least.
3. **Guard the worst by VALUE comparison**: recompute from the source and compare, with a tolerance
   that is stated and justified, never tuned until it passes.
4. **Injection-test every guard**, one at a time, and report each result.
5. **Say what cannot be guarded** - a figure whose source is gone, a hand-entered number. A listed
   known-unguarded figure is better than a false sense of coverage.

If you find a figure that is already stale, do not silently rebuild it. Report it, fix it, and log it
in the relevant study's deviations log.

## House rules (non-negotiable)

- `check.py` must pass. Any guard you add must be verified by INJECTION: break the thing it guards,
  confirm the guard fails, restore it, confirm it passes. Report that you did this.
- Never run `runner.py --force`. If you rebuild a page, the runner reruns the post-passes
  (`add_canonicals.py`, `add_head.py`, `clean_links.py`, `build_search_index.py`).
- Determinism: no `hash()`, no set/dict iteration order, no unseeded randomness.
- Deliver a PULL REQUEST, never a push to `main`. The PR description must carry the numbers, the
  verdict, and what you did not do.
- Money and tonnes are separate measures: chain JSONs are value-based, `out/cube.parquet` is
  tonnage-based. State the basis in every figure.
- Never sum sources for one flow. Never treat a zero declaration as a declaration.
- A negative result is a result. If the page's claim survives, say so plainly and change only the
  wording that needed it. Do not manufacture findings to justify the run.
- Do not touch anything relating to `BOP_extraction` or `rbop-archive`.
- Every source you cite, you open first. Never cite from memory.
