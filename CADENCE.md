# Cadence — keeping the atlas fresh

A portfolio project updates when you feel like it; a *data product* updates on a schedule people can rely
on. This is the runbook for that promise. Everything here is public-data only.

## The refresh pipeline (one pass)

```powershell
# 0. secrets in env (never commit)
$env:COMTRADE_KEY = '<key>'
$env:ATLAS_ROOT   = $PSScriptRoot

# 1. trade — pull raw Comtrade, reconcile, build the year's flows
python reconcile\pull_comtrade.py 2025         # or the latest year with data
python reconcile\reconcile.py 2025
python reconcile\build_recon_flows.py 2025     # -> out/flows_2025.json  (provisional)
python reconcile\build_2026_nowcast.py         # -> out/flows_2026.json  (directional scenario)

# 2. reference layers (mine / refine / reserves / EU lens) when USGS/IEA update
Rscript build_static.R                         # -> out/data.json

# 3. regenerate the derived site artefacts (order matters: risk + wgi before criticality; insights last)
python fetch_wgi.py                            # -> out/wgi.json (World Bank governance; only when WGI updates ~yearly)
python build_risk.py                           # -> out/risk.json + risk.html (supply-risk index)
python build_network.py                        # -> out/network.json + network.html (trade-network chokepoints)
python build_complexity.py                     # -> out/complexity.json + complexity.html (RCA / economic complexity)
python build_criticality.py                    # -> out/criticality.json + criticality.html (governance-weighted; reads risk.json + wgi.json)
python build_origin.py                         # -> out/origin_trace.json + origin.html (hybrid origin trace)
python build_scenarios.py                      # -> scenarios.html (supply-shock stress tests)
python build_profiles.py                       # -> profile-*.html (material+country) + profiles.html + countries.html
python build_insights.py                       # -> insights.html (the synthesis / state-of-supply page)

# 4. sanity-check, then commit + push (Pages redeploys automatically)
python reconcile\validate.py 2024              # must stay green (top-1 ~25/30)
```

**Before publishing, check the numbers — not just that it ran.** Comtrade's latest year is provisional and
revised upward for months; the slider tiers (measured / provisional* / directional**) must stay honest.

## When to run it

| Trigger | Action |
|---|---|
| New **quarterly** Comtrade lands | refresh `flows_2025`/`flows_2026`, post a short **Update** entry |
| New **annual** Comtrade for a year | rebuild that year; if it's the newest, it becomes the measured default |
| **CEPII BACI** releases a new year | rebuild from BACI (authoritative), drop the provisional tier for that year |
| **USGS / IEA** publish new editions | rerun `build_static.R`, note the vintage bump |
| **Export-control / policy event** | add it to `POLICY_EVENTS` (the year-slider timeline) + an Update entry |

## The pre-registered moment

When **BACI for 2025** is released, run `ATLAS_ROOT=… python reconcile/validate.py 2025` and publish the
result against the thresholds locked in [`reconcile/PREREGISTRATION.md`](reconcile/PREREGISTRATION.md) —
**pass or fail**. That is the credibility event; do not let it slip silently.

## Automation in place

- **CI** (`comtrade-reconcile`) reconciles the committed raw fixture → validates vs BACI on every push
  **and monthly** (scheduled), so the green badge keeps proving the pipeline reproduces and catches
  dependency drift even when nothing is committed.
- `build_profiles.py` is deterministic — the 32 profile pages regenerate exactly from the data, so a
  refresh never means hand-editing pages.

Log every refresh on the [Updates](updates.html) page — that dated trail *is* the freshness promise.
