# Critical-materials trade pipeline

A reconciled, harmonized, de-duplicated, **monthly** critical-materials trade database — assembled from
public sources into one canonical table, queryable client-side with zero backend. This is the private
build side; the browser demo is `query.html`.

> **Design in one line:** slow *pull* jobs write per-source caches → `build.py` unions the caches into
> `flows.parquet` in seconds. Adding a country = writing **one adapter file**.

---

## Run it

```bash
# 1. refresh source caches — SLOW (network pulls + rate limits); run occasionally / on a schedule
python pipeline/refresh.py all            # or: refresh.py comexstat hmrc   (just some)
python pipeline/pull_comtrade.py 3        # Comtrade is extra rate-limited: grow its raw cache separately
python pipeline/refresh.py comtrade       # then fold the grown Comtrade cache into its canonical cache

# 2. assemble — INSTANT (no network); writes flows.parquet + flows_best.parquet
python pipeline/build.py

# 3. view — DuckDB-WASM over the parquet, all client-side
python -m http.server 8777                # open http://127.0.0.1:8777/pipeline/query.html
```

---

## Architecture

```
 pull jobs (slow, rate-limited)         build (instant)              view (static)
 ─────────────────────────────         ───────────────             ──────────────
 refresh.py <source>  ─► cache/<source>.parquet ─┐
 pull_comtrade.py ─► comtrade_cache.jsonl ─►      ├─► build.py ─► flows.parquet ─► query.html
                       refresh.py comtrade ─►     │              flows_best.parquet   (DuckDB-WASM)
                                        cache/*.parquet ─────────┘
```

| File | Role |
|------|------|
| `schema.py` | canonical `flows` record + `validate()` gate + country lookups. **Every source normalizes into this.** |
| `concordance.py` | native code → material harmonization; splits HS-6 bundles at 8-digit (the thing TDM doesn't do) |
| `fx.py` | monthly currency→USD from ECB reference rates (`to_usd(value, period, ccy)`) |
| `adapter_base.py` | the contract: `discover() → pull() → normalize() → validate()` via `run()`; a flaky source FAILs gracefully |
| `adapter_*.py` | one per source (see below) |
| `cache.py` | per-source canonical-row cache (`cache/<source>.parquet`) |
| `refresh.py` | runs adapters, writes caches (the slow part) |
| `build.py` | unions caches → `flows.parquet` + `flows_best.parquet` (the fast part); holds the `ADAPTERS` registry |
| `query.html` | static DuckDB-WASM query page |

### Sources (7)

| adapter | source | layer | granularity | notes |
|---------|--------|-------|-------------|-------|
| `adapter_baci` | CEPII BACI | wide | HS-6 · annual | world, mirror-reconciled — the comparable base |
| `adapter_eurostat` | Eurostat Comext | deep | CN-8 · monthly | EU-27, splits bundles |
| `adapter_comexstat` | Brazil Comex Stat | deep | NCM-8 · monthly | keyless POST, USD FOB |
| `adapter_hmrc` | UK HMRC | deep | CN-8 · monthly | keyless OData, GBP→USD |
| `adapter_uscensus` | US Census | deep | HS-6 · monthly | needs free key in `.census_key` |
| `adapter_comtrade` | UN Comtrade | wide | HS-6 · monthly | keyless preview, rate-limited → rotating calendar |
| `adapter_mirror` | (from BACI) | mirror | HS-6 | China/Russia/DRC reconstructed from partner reports |

### Two views
- **`flows`** — the raw layers (every source, may overlap).
- **`flows_best`** — each physical flow **once**: canonicalized to exporter→importer, source overlap removed
  by precedence (deep national > wide reconciled > mirror). Use this for `SUM(value_usd)`.

---

## Add a source (the AI-parallel task)

1. Create `adapter_<name>.py` — subclass `Adapter`, implement three methods:
   ```python
   class FooAdapter(Adapter):
       key = 'foo'; freq = 'M'; note = '...'
       def discover(self):  return [latest_period_int]          # YYYY or YYYYMM
       def pull(self, period):  return raw                       # network / file — source quirks live here
       def normalize(self, raw, period):                        # yield canonical rows
           yield schema.row(source=self.key, freq=self.freq, period=..., reporter=<ISO3>, partner=<ISO3>,
                            flow='import'|'export', hs6=<6>, native_code=<native>, code_level=6|8|10,
                            material=concordance.material_for(code, level),
                            value_usd=<USD, via fx.to_usd if not USD>, qty_kg=<kg or None>, is_mirror=False)
   ```
2. Register it: add `FooAdapter()` to `ADAPTERS` in `build.py` (one line).
3. `python pipeline/refresh.py foo` → validates and caches. `python pipeline/build.py` → folds it in.

**Rules:** normalize to the canonical schema; map countries to **ISO3**; convert value to **USD** (use
`fx`); assign material via **`concordance`** (add native-code entries there to split a new scheme's
bundles). The `validate()` gate rejects a broken source, so a bad adapter can't corrupt the DB.

**Guardrail:** public data only. If a source needs a key, read it from a **gitignored** file (see
`.census_key`) — never commit keys.

---

## What makes this not just a data feed
Reconciliation (BACI + mirror), harmonization (`concordance` splits HS-6 bundles national-line-deep),
de-duplication (`flows_best`), real FX — all things a raw commercial feed (e.g. Trade Data Monitor)
does **not** do. All free, static, reproducible, and extensible one adapter at a time.
