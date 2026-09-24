# Adversarially review the export-controls study

Repo: `materials-atlas/critical-materials-atlas` (public, self-contained).

The study lives in `export-controls/` and publishes at `/export-controls`. As filed it finds no bite;
antimony and bismuth are exploratory, with the antimony fall PREDATING the control and Korean bismuth
redirected away from the US. It carries `AMENDMENT_A.md` with eight deviations and `WATCH_2027.md` for
a February 2027 re-read.

Attack in particular:

- **Dates against data.** The monthly Comtrade layer is EMPTY before December 2024, so it holds no
  2023-24 control dates. Confirm no claim leans on a window the data cannot cover.
- **Every MOFCOM announcement cited** (M23, M39, M33, M46, M72, M10, M18, M70, M57, M58): open each
  and check the page has its scope and date right.
- **The BGS bismuth series for China is a FLAT PLACEHOLDER** - the study knows this. Cross-check
  against World Mining Data and the USGS, and confirm no figure rests on the placeholder.
- **HS code scope.** Check each code is what the page says: 811292 is a basket, 250490 is noise, and
  compound codes (antimony trioxide 2825xx, for instance) may be absent entirely. A wrong scope claim
  silently changes what a figure means.
- **`isNetWgtEstimated` can flip mid-series**, making a tonnage series incomparable across months.
  Check the flag and the implied $/kg wherever tonnages are compared.
- **Framing.** Is "no bite as filed" stated as a finding about the FILED TEST rather than about the
  world?

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
