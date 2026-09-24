# Adversarially review the USGS revision study and Amendment A

Repo: `materials-atlas/critical-materials-atlas` (public, self-contained).

The study lives in `usgs-revisions/` and publishes at `/revisions` (built by `build_revisions.py` from
`out/usgs_revisions.json`, computed by `usgs-revisions/analysis.py` from
`pipeline/data/usgs_mcs_history.parquet`). Section 1 covers the six filed commodities; `AMENDMENT_A.md`
widens the same measure to all fifteen in the panel. The filing carries 15 dated deviations and the
amendment 10. Read both before anything else.

This study has been reviewed three times and every round found something real. Assume there is a
fourth. Attack in particular:

- **The 15-way ranking mixes stages** (mine, refinery, plain production). The page discloses this and
  prints a mine-only ranking beside it. Is the disclosure enough, or does the headline still lean on
  the mixed order?
- **The direction rule.** The filing says "the share of REVISIONS that are upward", at 60%. Both
  denominators are now reported and gallium and indium clear it on the filing's own. Check the
  arithmetic, and whether the wording could still mislead.
- **The magnesium merge** (`merge_renamed`): two measures are merged when they share a printed caption
  and no edition prints both. Enumerate every commodity and say whether that test could merge two
  genuinely different tables. The join year is 2019; check what it does to the median.
- **Coverage.** Four retrieval faults have already been found (a `_0` filename suffix; 403s from
  duplicated path segments; chapters uncut from the yearly volumes; tin's pre-2008 chapters). Count
  cached against parsed for all fifteen, check what each commodity's USGS page publishes that the repo
  does not hold, and check whether the 1997-1999 scanned volumes are genuinely unusable or merely
  hard.
- **The `NO_TABLE` exceptions in `check.py`** (gallium before 2019, germanium from 2024): open those
  PDFs and confirm each really prints no country table.
- **Comparability.** Is any median over few years presented as comparable with one over twenty-five?

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

## How to review (this project has a method; follow it)

1. Read the pre-registration filing and its dated deviations log FIRST
   (`<study-dir>/PREREGISTRATION.md`, plus any `AMENDMENT_*.md`). The filing is the contract: a
   reading it does not license is not licensed, and a change made after it belongs in the log.
2. RECOMPUTE the page's numbers with your own script, from the stores. Checking a JSON against the
   page verifies nothing: both come from the same computation. Stores: `out/cube.parquet` (tonnage),
   `pipeline/data/*.parquet`, and the `out/*.json` each builder reads.
3. Open the sources the page cites - the PDFs under `raw/`, the agency pages - and check the page
   says what they say. Read USGS chapters GEOMETRICALLY with PyMuPDF: a footnote marker is smaller
   type set against its value, so in plain text "7100,000" cannot be told from a number.
4. Check the denominators. Most errors found in this project were a share computed over one
   population and described as another.
5. Check COVERAGE before believing any claim about a source's silence. A file that was never fetched
   leaves no symptom: count what is cached against what is parsed, and look for what the source
   publishes that the repo does not hold. Four faults of this kind have been found here; one changed
   a published figure.
6. Ask what a hostile expert reader would say. Overstatement is the failure mode that matters.

## What to deliver

A PR that (a) fixes what is wrong, (b) adds a dated entry to the study's deviations log for every
change, in that log's existing voice, and (c) leaves a short review note in the study directory
recording what you checked and found CORRECT - a clean check is worth recording. If a fix changes a
published figure, say so in the PR title.
