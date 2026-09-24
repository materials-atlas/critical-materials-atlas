# Adversarially review the build-out and grid-trade notes

Repo: `materials-atlas/critical-materials-atlas` (public, self-contained).

The note lives in `buildout/` and publishes at `/grid-trade`, with the AI build-out page at
`/ai-buildout`. It began as a pre-registered transformer/GOES study and became a DESCRIPTIVE note
after three reviewers. Headline figures: GOES exports concentrated (China 12->32%); China 9->57% of EU
GOES import value to July 2026; Amendment D adds a world panel (China 36->39% of GOES imports 2025)
and EU transformer origins (China 4->46%); "heavier transformers" was withdrawn. The companion page
reports transformer trade growing about 3x faster than chip trade 2019-24.

Attack in particular:

- **Every share**: recompute from the stores and state the basis for each. A share of import VALUE and
  a share of TONNES are different claims and have been confused in this project before.
- **The 4->46% and 9->57% jumps.** Base effect, reporter-panel change, code change, or real? Confirm
  the reporter panel is FIXED across the window - a drifting panel manufactures trends.
- **The "3x faster than chips" comparison**: which codes stand for chips and which for transformers,
  and does the comparison survive a different defensible code choice? Report the alternative.
- **Causal language.** A descriptive note must not make causal-sounding statements about the AI
  build-out.
- **The withdrawal of "heavier transformers"**: confirm nothing downstream still depends on it.

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
