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
critical-materials flows where we have both sides (n = 1,040), they disagree by more than 2×
**in 535 cases — 51%.** The engine refuses to invent a single number for those; it publishes the range and,
where it can, the likely cause:

| Likely cause of the disagreement | share of the 535 |
|---|--:|
| Exporter reports ≫ importer (importer under-reporting / confidentiality) | 34% |
| An entrepôt / re-export leg (the two "sides" aren't the same physical trade) | 30% |
| Importer reports ≫ exporter (exporter under-invoicing / re-export inflation) | 18% |
| Unexplained (HS-code ambiguity or monthly timing) | 18% |

**82% of the conflicts get a named, structural cause** — they are not random noise, and only ~1 in 5 is
genuinely unexplained. The single largest bucket is one side simply reporting far more than the other; the
second is trade that physically passes through a hub, so the "exporter's" and "importer's" flows are not the
same shipment at all — finding #1 and finding #2 are the same phenomenon seen from two angles.

## The engine tracks the real market (a check, not a headline)

A fair worry: is a reconciled figure just an average of two bad numbers? One external check — **price**.
The implied unit value of germanium (value ÷ kg), aggregated across all reporters, rose from a median of
**$1,685/kg in 2024 to $3,781/kg in early 2026 — a 2.2× increase** — matching the well-documented
tightening after China's 2023 export controls on the metal. The engine was not told about the controls; it
recovered their price signature from customs data alone. (Monthly samples are small, 25–27 obs per window,
so this corroborates rather than headlines.)

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

-- 3 · germanium price signal
SELECT period, ROUND(median(value_usd/qty_kg)) AS usd_per_kg
FROM 'pipeline/data/flows_best.parquet'
WHERE material='germanium' AND qty_kg>0 AND value_usd>0 GROUP BY 1 ORDER BY 1;
```

*Independent work, public data only (UN Comtrade, Eurostat, UK HMRC, Brazil ComexStat, US Census, CEPII
BACI). Monthly reconciliation covers 2024–2026 as coverage accrues; figures rounded. Read the hub share as
"trade that touches a hub," not "trade that is fraudulent."*
