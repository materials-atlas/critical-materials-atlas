# The cube's data structure, rebuilt on BPM6

**Proposal, 2 October 2026.** Replace the atlas's home-grown 9-dimension DSD with one modelled on
the **IMF BPM6 global DSD** — the structure behind the ECB Data Portal's BPS dataflow (Balance of
Payments and International Investment Position), which the portal labels `[BOP agency: IMF]`.

Why this and not a design of our own: the problems the cube has hit — bilateral pairs, a bloc that
is not a country, stocks sitting in a table of flows, FOB against CIF, two compilers reporting the
same fact — are the problems balance-of-payments statistics solved decades ago. Every one has a
standard coded dimension already. Adopting them means anyone who reads ECB, IMF or national BoP
data can read ours without a glossary, and it stops us inventing a private vocabulary for solved
problems.

> A note on provenance. The 17 dimensions below are from the ECB Data Portal's published structure
> page for BPS. An earlier draft of this document used `ECB_BOP1`, the **legacy ECB-agency DSD**,
> which has only 9 dimensions and is not what BPS runs on. The owner caught it.

---

## The 17 dimensions, and what each means for a materials cube

`•` = adopt · `○` = carry as a constant for conformance · `—` = not applicable, code `_Z`

| # | BPM6 concept | | What it becomes here |
|---|---|---|---|
| 1 | `FREQ` | • | Already have it. `A` annual, `M` monthly. |
| 2 | `ADJUSTMENT` | ○ | `N`, not seasonally adjusted. Constant today, but a seasonally adjusted monthly series is a plausible future and the slot costs nothing. |
| 3 | `REF_AREA` | • | The reporting country. Already have it as `country_iso3`. |
| 4 | **`COUNTERPART_AREA`** | • | **The partner.** The dimension the cube lacks — see below, it solves two problems at once. |
| 5 | `REF_SECTOR` | — | No institutional sectors in mineral statistics. `_Z`. |
| 6 | `COUNTERPART_SECTOR` | — | `_Z`. |
| 7 | **`FLOW_STOCK_ENTRY`** | • | **Separates stocks from flows.** Production, imports and exports are transactions (`T`); reserves, government and industry stockpiles are positions (`LE`). Today both sit in `measure` undifferentiated, so nothing stops a query differencing a reserve against a production figure. |
| 8 | `ACCOUNTING_ENTRY` | • | Direction. Our `flow_direction` in/out maps to the credit/debit pair. |
| 9 | `INT_ACC_ITEM` | • | What is being measured — our `measure_family` (trade / production / stocks / consumption). |
| 10 | `FUNCTIONAL_CAT` | — | Direct vs portfolio investment. `_Z`. |
| 11 | `INSTR_ASSET` | • | The thing itself — our `MATERIAL`, with `STAGE` (mine / smelter / refinery / compound) as its sub-classification. This is the cube's own extension and the one place our vocabulary has to be ours. |
| 12 | `MATURITY` | — | `_Z`. |
| 13 | `UNIT_MEASURE` | • | tonnes / EUR / USD. Already an attribute; BPM6 makes it a **dimension**, which is stricter and right — a tonnage row and a value row are different observations, not one observation with two units. |
| 14 | **`CURRENCY_DENOM`** | • | **Money and tonnes stop being confusable.** `EUR`, `USD`, or `_T` where the observation is physical. This is the atlas's existing "money and tonnes are separate measures" rule, expressed as a standard code instead of a convention nobody can enforce. |
| 15 | **`VALUATION`** | • | **FOB against CIF.** Today this lives inside `reconcile.py` and a `basis` column that also carries gross/content. BPM6 gives valuation its own dimension, so a CIF import and an FOB import are different observations and can never be silently averaged. |
| 16 | **`COMP_METHOD`** | • | **Which compilation produced this.** Our `SOURCE` dimension already exists and already does this job — it simply has a standard name and a standard home. |
| 17 | `TYPE_ENTITY` | — | `_Z`. |

Positions 18–20 in the Banque de France extension (variant, decomposition, status) are a national
addition on top of the same 17; worth knowing the pattern exists, not worth copying yet.

---

## The two things this settles that we had no answer for

### 1. `COUNTERPART_AREA` makes the bilateral cube *and* the universe problem one problem

The cube holds country totals and has no partner, so System A's whole content — who Europe buys
from — cannot be represented. Separately, A's rows are extra-EU imports only, and nothing in the key
says so, which is why the Comext adapter currently carries a non-standard `universe` tag.

BPM6 solves both with one dimension, because **a counterpart area need not be a country**. The ECB
publishes `W1` for world, `I9`/`J9` for inside/outside the euro area, `B5`, `D5` and so on. So:

| Observation | `REF_AREA` | `COUNTERPART_AREA` |
|---|---|---|
| Germany's imports of magnets from China | `DEU` | `CHN` |
| Germany's imports of magnets, all partners | `DEU` | `W1` |
| Comext flows with no usable partner code | `DEU` | `_Z` |
| World mine production of cobalt in the DRC | `COD` | `W1` |

Both area columns are **ISO3**, and the codelist `CL_AREA` is shared between them. An earlier draft
of this table wrote `DE` and `CN`; the cube writes `DEU` and `CHN`, and Comext's own ISO2 codes are
converted on the way in through `schema.iso3()`. Caught by an engine review.

There is deliberately **no extra-EU aggregate row**. Scope is expressed by filtering the counterpart
column, not by storing a second total — see the open question below.

**So the `universe` column I proposed is unnecessary and should be dropped before it ships.** Scope
is a counterpart-area code, which is what BoP has always done. That is a better design than the one
I proposed, and it comes directly from the BPM6 suggestion.

### The open question this leaves: should we store the aggregates?

Right now the cube stores only COMPONENTS for Comext — one row per partner — and an EU total is got
by filtering out intra-EU partners and summing. That is safe against double counting and unsafe
against forgetting: an EU aggregate computed without the filter is inflated, and measured on 2024
the inflation is **12.8x for strontium**, 6.6x for cobalt, 3.5x for vanadium.

BPM6 practice is the opposite: the ECB and the IMF **publish the aggregate as its own observation**,
under its own counterpart code, so a user never sums partners at all — they select the code they
want. That removes the forgetting failure entirely, and replaces it with the coexistence failure
(`check_counterpart` would have to permit declared aggregates while still refusing accidental ones).

The honest trade: storing aggregates protects the careless reader and needs a smarter guard; storing
only components protects the guard and needs a careful reader. BPM6 chose the first. We have not
chosen yet.

One rule follows and must be guarded: a total and its own components are both legitimate
observations, and summing them double counts. This is the exact fault already found twice in this
repo — Comtrade returning an all-modes total beside its components, and Comext returning the `EU`
aggregate beside its 27 member states (which inflated the first Comext ingest 4.6×). With `W1` and
bloc aggregates in the same column, the guard becomes mandatory, not optional.

### 2. `COMP_METHOD` + `VALUATION` + `CURRENCY_DENOM` make the multi-source problem expressible

11.9% of the cube's fact-keys already carry more than one source. Today that is legible but not
safe: `SUM(value)` counts China's 2024 copper production three times. With these three dimensions
in the key, the *reason* two rows differ is machine-readable — different compiler, different
valuation, different currency — which is what a `cube_best` view needs in order to pick one row per
fact by declared precedence, the way `flows_best` already does for trade.

---

## What this does not fix

A richer DSD describes observations better. It does **not** make two sources independent. Comext and
the EU slice of BACI still share an origin — EU member states report to Eurostat, Eurostat transmits
to UN Comtrade — so giving them distinct `COMP_METHOD` codes will make them *look* like two
witnesses in the key while remaining one witness recorded twice. That has to stay written down in
the source ledger, because no dimension can encode it.

---

## Order of work

1. Write the DSD v2 (17 dimensions, our codelists) and publish it beside the current one.
2. Add `COUNTERPART_AREA` to the cube, defaulting every existing row to `W1`, and drop the
   `universe` tag from the Comext adapter. Nothing breaks: today's queries are `W1` queries.
3. Re-emit Comext bilaterally — the adapter already reads partner, it aggregates it away.
4. Ingest System B bilaterally from `out/flows_*.json` (≈372k rows).
5. `FLOW_STOCK_ENTRY`, `VALUATION`, `CURRENCY_DENOM` as real dimensions; retire the overloaded
   `basis` column.
6. `cube_best`, and a guard that fails any published page summing across `COMP_METHOD` or across a
   total and its components.

Steps 1–2 are the ones with blast radius: 10 builders read the cube, plus the DuckDB query page,
the SDMX export and several guards.
