# Adversarially review the scrap-price study

Repo: `materials-atlas/critical-materials-atlas` (public, self-contained).

The study lives in `scrap-response/` and publishes at `/scrap`. Its filed claim: in the US, secondary
recovery shows no response at the filed 0.20 price threshold for aluminium and lead - the two metals
where scrap is 40-59% of consumption - while scrap TRADE moves within the year (+0.58) and not at one
or two years. It went live after two council rounds, an 11-reference verified bibliography, and three
filed-but-unrun checks that were then run.

Attack in particular:

- **The threshold.** 0.20 was filed, but is the result an artefact of it? Report the response at other
  thresholds as a sensitivity, clearly labelled post-hoc.
- **"No response" is a null.** Is the test powered to detect a response large enough to matter? If
  not, the honest statement is "cannot detect", not "does not respond", and the page must say which.
- **The Turkiye unit-value check** the study ran but did not read out ("both later terms positive but
  endogenous"). Either it is readable with an instrument or it is not. Say which, and if not, confirm
  the page is right to leave it unread.
- **The consumption shares (40-59%) and every price series**: recompute from the World Bank Pink Sheet
  and the BACI scrap codes held in the repo.
- **Reach.** No open non-US secondary-production panel exists (ICSG/ILZSG sell theirs). Is that stated
  as a limit on what the finding can claim, or only as a data note?

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
