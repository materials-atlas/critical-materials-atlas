# Re-export theatre & mirror gaps — a second finding

**Headline:** raw customs statistics are a poor guide to critical-materials supply for two structural,
*measurable* reasons. **(1) Re-export theatre:** for many materials the majority of trade flows pass through
a handful of entrepôt hubs, so the country a ledger names as "exporter" is a trans-shipment point, not a
source. **(2) Mirror gaps:** where a flow is reported by *both* sides, the exporter's and importer's figures
disagree by more than 2× **51% of the time** — so half the numbers don't even agree with their own mirror.

This is the companion to [the origin gap](FINDINGS.md): that finding needs *reconciled* trade to work, and
this one shows *why raw trade cannot be taken at face value* in the first place.

Reproduce live in the [query page](pipeline/query.html) (presets ★ *Coverage & quality scorecard*,
★ *Reconciliation*, ★ *Why do the two sides disagree?*) or against the published Parquet files — SQL at the
bottom. Corridor-by-corridor evidence: the [validation dossier](pipeline/dossier.html).

## 1 · Re-export theatre — most flows never touch the source

For each material we flag every flow whose exporter *or* importer is a known trans-shipment hub
(Netherlands, Belgium, Switzerland, UK, Luxembourg, Singapore, Hong Kong, UAE, Panama, Malaysia), then take
the share of trade that routes through one.

| Material | flows via a hub | value via a hub | dominant hubs |
|---|--:|--:|---|
| **Platinum, unwrought** | 67% | **64%** | London, Hong Kong, Zurich, Belgium |
| **Palladium, unwrought** | 67% | **57%** | London, Zurich, Belgium, Hong Kong |
| Nickel, unwrought | 53% | — | |
| Cobalt oxides | 51% | — | |
| Lithium carbonate | 50% | — | |
| Titanium, unwrought | 48% | — | |

For platinum and palladium, **roughly two of every three trade flows — and ~60% of the traded value —**
pass through London (the LPPM market), Zurich (the world's platinum-group refining hub), Belgium or Hong
Kong. Reading a raw export table, you would "discover" that the UK and Switzerland are major sources of
platinum-group metals. Neither mines any. The metal is South African and Russian; the ledger shows the
*market*, not the mine.

## 2 · Mirror gaps — half the numbers don't agree with themselves

Every bilateral flow can be reported twice: the exporter declares it FOB, the importer declares its mirror
CIF (freight + insurance included). Put both on a common basis and they *should* line up. For monthly
critical-materials flows where we have both sides (n = 1,052), they disagree by more than 2×
**in 536 cases — 51% by flow count.** Two things make that number trustworthy rather than an artefact.
**(i) It replicates, it doesn't just span.** The two-sided sample is concentrated in two well-covered months
— December 2024 (n = 907) and June 2026 (n = 130), reported by *different* sets of countries — and each lands
independently at a similar rate (**50%** and **58%**). So read this as a replication across two independent
months, not a figure spread thinly over 2024–2026. **(ii) It is not thin-cell noise.** Value-weighted, the
rate is lower — roughly a quarter, though the exact figure depends on how the *ranged* (disagreeing) flows
are valued — but disagreement stays high at every flow size: even the **largest flows, running into the
billions of dollars, disagree about 42% of the time** (versus ~53% for the smallest). Big trades disagree
nearly as often as small ones, which is the opposite of what a thin-cell artefact would show. The engine
refuses to invent a single number for the conflicting flows; it publishes the range and, where it can, the
likely cause:

| Likely cause of the disagreement | share of the 536 |
|---|--:|
| Exporter reports ≫ importer (importer under-reporting / confidentiality) | 34% |
| An entrepôt / re-export leg (the two "sides" aren't the same physical trade) | 30% |
| Importer reports ≫ exporter (exporter under-invoicing / re-export inflation) | 18% |
| Unexplained (HS-code ambiguity or monthly timing) | 18% |

**82% of the conflicts get a named, structural cause** — they are not random noise, and only ~1 in 5 is
genuinely unexplained. The single largest bucket is one side simply reporting far more than the other; the
second is trade that physically passes through a hub, so the "exporter's" and "importer's" flows are not the
same shipment at all — finding #1 and finding #2 are the same phenomenon seen from two angles.

## Why there is no price cross-check here

A tempting external check is price: does the reconciled data recover a known move, such as germanium's spike
after China's 2023 export controls? We deliberately do **not** offer that check, and the reason is itself a
finding. The germanium HS6 code (**811292**) bundles **gallium, germanium and hafnium** — as
[FINDINGS.md](FINDINGS.md) states, they cannot be separated at this code — so an "implied germanium unit
value" is not actually germanium. And the monthly implied unit values are wildly unstable on 1–7
observations: the median swings from **~$768/kg (Dec 2024) to ~$8,872 (Jan 2026) to ~$248 (Jun 2026)**, so
almost any pair of endpoints can be picked to tell almost any story. The honest move is to flag that this
code cannot carry a price series, not to dress a noisy ratio as corroboration.

## What this is and isn't

- **It is** a measurement over public bilateral trade: the hub share is computed on de-duplicated flows
  (`flows_best`); the 51% is over flows where both customs sides exist in the same month; the price check is
  a median of value ÷ quantity.
- **It isn't** a fraud claim. A hub leg is often legitimate (metal genuinely is refined in Zurich and traded
  in London); a mirror gap is often freight, confidentiality suppression, or an HS-code that bundles
  products — not misreporting. The point is that **taken at face value, the raw tables mislead**, and the
  direction of the error is systematic, not random.
- **It isn't** value-weighted for every row of the first table (the "% of value" column is shown where it
  matters most, PGMs; the flow-share is the primary measure). UK coverage is strong in this dataset, which
  reinforces London's #1 position — but Zurich, Belgium and Hong Kong appear independently.

## Why it matters

Supply-risk policy is written off import-origin tables. This finding says those tables are wrong in two
compounding ways for critical materials: they credit hubs as sources, and half of them don't even agree with
their mirror. Reconciling the two sides — and flagging, not smoothing, the half that conflict — is the only
way to see the real structure underneath. That reconciliation *is* the engine behind this atlas.

## Reproduce

Against the published Parquet files (DuckDB), or live in the [query page](pipeline/query.html):

```sql
-- 1 · re-export share per material
SELECT material, ROUND(100*avg(via_entrepot::INT)) AS pct_flows_via_hub,
       ROUND(100*sum(CASE WHEN via_entrepot THEN value_usd ELSE 0 END)/sum(value_usd)) AS pct_value_via_hub
FROM 'pipeline/data/flows_best.parquet' GROUP BY 1 ORDER BY 2 DESC;

-- 2 · mirror disagreement rate + taxonomy
SELECT disagree_reason, COUNT(*) FROM 'pipeline/data/flows_reconciled.parquet'
WHERE basis='disagreement' GROUP BY 1 ORDER BY 2 DESC;

-- 3 · the two-sided sample is concentrated in two months (the replication, not a span)
SELECT period, COUNT(*) AS two_sided,
       ROUND(100.0*AVG((basis='disagreement')::INT)) AS pct_disagree
FROM 'pipeline/data/flows_reconciled.parquet'
WHERE basis IN ('disagreement','reconciled') GROUP BY 1 ORDER BY 2 DESC;
```

*Independent work, public data only (UN Comtrade, Eurostat, UK HMRC, Brazil ComexStat, US Census, CEPII
BACI). Two-sided monthly reconciliation is currently concentrated in two well-covered months (Dec 2024,
Jun 2026) as coverage accrues — read the 51% as a two-month replication, not a continuous 2024–2026 series;
figures rounded. Read the hub share as "trade that touches a hub," not "trade that is fraudulent."*
