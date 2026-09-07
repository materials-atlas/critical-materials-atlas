# Data architecture

How data moves through this project, what is enforced, and what is deliberately not built.

Written 7 Sep 2026 after two adversarial reviews. Every number here was measured, not estimated;
the commands that produce them are in `check.py`.

---

## 1. The system as it actually is

Not as it should be. An earlier draft of this document drew `raw → extract → cube → out → release`
and called the cube the spine. That diagram was aspiration. Measured:

| | |
|---|---|
| builders | 286 |
| builders that open `cube.parquet` | **11** |
| analysis families that read the cube | **1 of 13** |
| builders that open raw BACI archives themselves | **53** |
| ...that separately re-implement the country-code mapping | **52** |
| builders that read another builder's JSON | **85** |
| `out/` paths with more than one writer | 0 |
| raw datasets on disk / read by something | 35 / 29 |
| held datasets in the register / undocumented | 64 / 0 |
| published outputs carrying a version | **0** |

So the real shape is:

```
raw/  ──────────────┬──────────────────────────► builder ──► out/*.json ──┐
  (35 datasets)     │                             (78 of them)            │
                    │                                                     ├──► pages
                    └──► cube.parquet ──► builder ──────────────────────► │
                          (11 readers)    (1 family)                      │
                                                                          │
                    out/*.json ──────────────────────────────────────────►┘
                     (85 edges, builder to builder)
```

The cube is **a product with 11 readers**, not a hub. Drawing it as the spine is how this becomes a
platform nobody uses. It is the right home for the 32 tracked materials and the wrong home for a
country's whole export basket — and both statements stay true after this plan.

## 2. Two proven failures, one latent

**Proven — duplicated source logic.** A country-code correction (Republic of Congo filed under DR
Congo's ISO code) had to be applied in two places independently. There are 52 places it could have
been needed.

**Proven — stale derived copies.** `risk.json` served a retracted germanium score for three weeks
after `data.json` was corrected. A corrected source does not correct its copies.

**Latent — nothing published can be cited.** Every rebuild replaces the last, so a chart cannot name
the table behind it.

Work is ordered by proven harm, not by what is pleasant to build. The latent problem goes last.
This document originally put it first because it was small and felt like a win; that was the same
instinct that produces a tidy diagram of a system that does not exist.

## 3. The foundation: the graph is observed, not declared

Both reviewers independently said the dependency rules could not be enforced, because a
hand-written manifest always misses an edge — a glob, a path built from a variable, a `pandas`
call that opens a file in C rather than through Python.

That objection is correct about *declared* manifests and empirically wrong about this one.
`sys.addaudithook` sees every file access, including from compiled extensions. Tested here:

| access | seen by the hook |
|---|---|
| `pandas.read_parquet` | yes |
| `json.load(open(...))` | yes |
| `zipfile.ZipFile` | yes |
| writes (`out/library.json`, `DATA_LIBRARY.md`) | yes, exactly |

So the manifest is **recorded by running the builders**, not typed by hand. Nobody declares
anything; nobody can forget to. This is the same principle as everything else that worked in this
project: measure it, do not assert it.

And once the true graph exists, it can be **topologically sorted**, which turns the checks below
from a report into an action. A checker that says "stale" without rebuilding is, correctly, a guilt
dashboard: `check.py` would have been red for the germanium score for three weeks and the number
would still have been wrong.

## 4. Layers

```
raw/            immutable. Source bytes as published, vintage in the filename
                (BACI_HS02_V202601.zip). Never edited. Opened only by an extractor.

extract/        one writer per source. Normalized parquet: canonical ISO3, declared units,
                source vintage recorded. The only legal reader of raw/.

cube.parquet    the harmonized fact table for the 32 tracked materials. One consumer of
                extracts among several. Deliberately narrow.

out/            page and view models. Terminal by intent, and 85 edges currently violate that.
                The target is not "declare the 85 and move on" - a declared copy is still a
                copy, and germanium was an out/ -> out/ edge. The graph exists to shrink them.

release/        immutable published vintages. Cut, never edited.
```

Two rules about the cube, so it is not mistaken for a warehouse:

- Two compilations reporting the same (material, country, period) are **two observations, not a
  conflict**. `source` is a dimension. There is no precedence rule because none is wanted: the
  golden rule is that facts are never joined on `material` alone.
- Vocabularies for `measure`, `stage`, `basis`, `unit`, `obs_status` are declared as SDMX code
  lists in `build_sdmx.py` and validated against the data on every run.

## 5. Invariants

Enforced by `check.py`. Each is verified by deliberately breaking it — a guard nobody has seen
fail is not a guard.

| # | invariant | mechanism | status |
|---|---|---|---|
| I1 | only an extractor may open `raw/<source>/` | observed graph + a per-source allowlist | **needs the allowlist** |
| I2 | one writer per artifact | observed graph | holds today (0 violations) |
| I3 | every builder-to-builder edge is in the recorded graph | observed graph | recording first, enforcing later |
| I4 | an output whose inputs or producer changed is stale **and gets rebuilt** | content hashes + topological rebuild | not built |
| I5 | nothing reaches a public path without a licence decision | `licences.py`, injection-tested | **live** |
| I6 | a published page names the vintage it was built from | string check over `out/*.html` | not built |

On I1: it is global, and only one source (BACI) can be extracted first. Turning it on before the
other 28 are extracted would break the repository. So I1 ships **per source**, with an explicit
allowlist naming every source not yet migrated. The allowlist is the honest form of "we know, and
here is the list" — and it shrinks. A blanket rule that must be disabled is not a rule.

On I4: hashing is over the **inputs and the producer's code**, never the output, and never mtime.
`build_cube.py` currently derives `retrieved_at` from a file's modification time, which a fresh
clone resets — the same defect class as the drift check this project has already been bitten by.
That must move to content.

On I6: you cannot mechanically make a chart *mean* its citation, but you can refuse to publish a
page that does not contain the vintage string of the data it read. That is checkable and it is
the part that decays without a machine.

## 6. What is deliberately not built

- a warehouse or database service — there is no server, and there must not be one
- Airflow, Dagster, dbt. A topological rebuild over an observed graph is ~80 lines and needs no
  daemon, no scheduler, and no vendor.
- bronze/silver/gold naming
- a widened cube. Full BACI is ~5,000 HS6 codes in tonnes *and* USD; the cube holds 45 codes in
  tonnes. A full-BACI cube is order 20M rows — roughly 30x the current artefact — and would still
  not serve product space, whose method needs the entire export basket in value terms.
- migrating all 13 analysis families onto the cube. For most, reading raw is **correct**.

The failure mode at this scale is schema drift and licence amnesia, not missing infrastructure.

## 7. Sequence

Ordered by proven harm over cost.

**Phase 1 — record the graph.** Run every builder under the audit hook; write the observed
reads/writes and content hashes. Nothing is enforced yet. This is pure measurement and it is the
prerequisite for everything else, including knowing what Phase 2 breaks.

**Phase 2 — the BACI extract.** One extractor writes `baci_crm_tonnes` (cube grain) and
`baci_full_usd` (whole basket). Migrate all 53 readers **in one sweep, not lazily** — lazy
migration keeps a proven bug class alive for months by choice. Then I1 for BACI only, with the
other 28 sources on the allowlist. The concentration finding is live and must reproduce exactly;
that test is written before the migration, not after.

**Phase 3 — the runner.** Topological rebuild from the recorded graph, then I2, I3, I4. This is
what actually prevents another germanium.

**Phase 4 — finish the register.** `read_by`, `in_cube`, `last_refreshed` are **derived from the
graph**, not typed and not stored twice. The register answers *what do we hold*; the graph answers
*what feeds what*; `licences.py` answers *what may leave*. Three questions, three files, no
overlap. `check.py` fails on a `raw/` folder with no register row.

**Phase 5 — vintages.** Cut `release/v2026-Q4` once the graph is true, and only then. A frozen bag
of undeclared edges is not a vintage; `BACI V202601` means *these source bytes plus this method*,
and until Phase 3 we cannot say either. Releases attach to GitHub Releases / Zenodo rather than
living in git, so cadence is a publishing decision and not a repository-size one.

**Phase 6 — selective cube migration.** Only where the cube serves better than raw.

## 8. Risks

1. **A green gate on a lie.** Mitigated more by observation than by policy: an undeclared read is
   the thing you cannot detect, so we stopped asking people to declare. Residual risk is a builder
   that is never run under the hook — so the recorder runs over *all* builders, and a builder with
   no recorded graph is itself a failure.
2. **A fake platform.** Rules bypassed because they are slower than not using them. The correct
   path must be shorter: `baci.load()` must be less typing than opening a zip. If it is not, it
   loses, and it deserves to.
3. **Phase 2 changes a published finding.** The concentration result is live. Exact reproduction is
   the acceptance test, written first.
4. **The plan is drawn for a system that does not exist.** After all six phases, most families still
   read `extract → builder → out`. That is fine and intended. This document should be re-measured,
   not re-remembered — the table in §1 is regenerated, and if it stops matching the prose, the
   prose is wrong.
