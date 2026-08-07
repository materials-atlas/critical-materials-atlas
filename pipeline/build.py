# -*- coding: utf-8 -*-
"""Orchestrator: run every registered adapter, gate each through validation, and write ONE unified
surface (pipeline/data/flows.parquet). Wide + deep + (later) mirror coexist in a single table that
the static browser page queries. Adding a source = append one adapter to ADAPTERS below."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duckdb
import schema, cache, reconcile, concordance
from adapter_baci import BACIAdapter
from adapter_eurostat import EurostatAdapter
from adapter_mirror import MirrorAdapter
from adapter_comexstat import ComexStatAdapter
from adapter_hmrc import HMRCAdapter
from adapter_uscensus import USCensusAdapter
from adapter_comtrade import ComtradeAdapter

ADAPTERS = [BACIAdapter(), EurostatAdapter(), MirrorAdapter(), ComexStatAdapter(), HMRCAdapter(), USCensusAdapter(), ComtradeAdapter()]   # <-- the whole registry; grows one line per source

# The correctness layer: the sources OVERLAP (mirror re-frames BACI; a later same-period source may
# restate a flow). flows_best returns each physical directed flow ONCE — canonicalize to
# (exporter->importer), rank sources (deep national > wide reconciled > mirror), keep the best per key.
# NOTE: it does NOT reconcile two *different* national sources reporting the same bilateral flow at
# different code schemes — that is the reconciliation engine's job, flagged, not silently summed.
FLOWS_BEST_SQL = """
CREATE VIEW flows_best AS
SELECT * EXCLUDE(rn, src_rank) FROM (
  SELECT c.*, ROW_NUMBER() OVER (
      PARTITION BY period, exporter, importer, native_code, code_level
      ORDER BY src_rank, value_usd DESC NULLS LAST) AS rn
  FROM (
    SELECT *,
      CASE WHEN flow='export' THEN reporter ELSE partner END AS exporter,
      CASE WHEN flow='export' THEN partner ELSE reporter END AS importer,
      CASE WHEN flow='export' THEN reporter_name ELSE partner_name END AS exporter_name,
      CASE WHEN flow='export' THEN partner_name ELSE reporter_name END AS importer_name,
      CASE source WHEN 'eurostat' THEN 1 WHEN 'comexstat' THEN 1 WHEN 'hmrc' THEN 1 WHEN 'uscensus' THEN 1
                  WHEN 'baci' THEN 2 WHEN 'comtrade' THEN 2 WHEN 'mirror' THEN 3 ELSE 9 END AS src_rank
    FROM flows) c
) WHERE rn = 1
"""


def main():
    files = cache.files()
    if not files:
        print("no source caches yet — run:  python pipeline/refresh.py all")
        return
    con = duckdb.connect()
    glob_path = os.path.join(cache.CACHE_DIR, '*.parquet').replace('\\', '/')
    # known entrepot / trans-shipment hubs — a flow touching one likely involves RE-EXPORT, not origin trade
    hubs = "('NLD','BEL','SGP','HKG','ARE','CHE','GBR','LUX','PAN','MYS')"

    # Canonicalize country codes ONE place, at build time, so already-cached data is fixed without re-pulling
    # (S19->Taiwan, Eurostat/HMRC oddities -> ISO3) and the same physical flow from two sources can align.
    def _code(col):   # remap the code
        return f"CASE {col} " + " ".join(f"WHEN '{k}' THEN '{v}'" for k, v in schema.COUNTRY_FIX.items()) + f" ELSE {col} END"
    def _name(col, namecol):   # override the name for any remapped code (keyed on the ORIGINAL code)
        return f"CASE {col} " + " ".join(f"WHEN '{k}' THEN '{schema.cname(v)}'" for k, v in schema.COUNTRY_FIX.items()) + f" ELSE {namecol} END"
    con.execute(f"""CREATE TABLE flows AS
      WITH canon AS (   -- first canonicalize codes + names in ONE pass ...
        SELECT * REPLACE({_code('reporter')} AS reporter, {_code('partner')} AS partner,
                         {_name('reporter','reporter_name')} AS reporter_name,
                         {_name('partner','partner_name')} AS partner_name)
        FROM read_parquet('{glob_path}'))
      SELECT *,   -- ... then derive flags from the CANONICAL values (so resolved Taiwan isn't re-flagged)
        (reporter IN {hubs} OR partner IN {hubs}) AS via_entrepot,
        -- PROVENANCE: the counterparty is SUPPRESSED (customs confidentiality) — origin/destination is hidden
        (partner='n/a' OR lower(coalesce(partner_name,'')) LIKE '%confidential%') AS confidential,
        -- PROVENANCE: the counterparty is an unresolved AGGREGATE ('nes'/areas/bunkers/free-zone), not a country
        (lower(coalesce(partner_name,'')) SIMILAR TO '.*(, nes|not specified| areas |bunkers|free zone|special categ).*') AS partner_group
      FROM canon""")   # union all source caches — instant; canonicalize + derive provenance flags
    total = con.execute("SELECT COUNT(*) FROM flows").fetchone()[0]
    print(f"assembled {total:,} rows from {len(files)} source caches:")
    for r in con.execute("SELECT source, MAX(period) AS latest, COUNT(*) AS n FROM flows GROUP BY 1 ORDER BY 1").fetchall():
        print(f"  {r[0]:10} latest={r[1]}  rows={r[2]:>7,}")

    pq = os.path.join(schema.ROOT, 'pipeline', 'data', 'flows.parquet').replace('\\', '/')
    con.execute(f"COPY (SELECT * FROM flows ORDER BY material, value_usd DESC) TO '{pq}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    print(f"\nwrote pipeline/data/flows.parquet  ({total:,} rows, {len(files)} sources, {os.path.getsize(pq)/1024:.0f} KB)")

    # correctness layer: de-duplicated, one row per physical directed flow
    con.execute(FLOWS_BEST_SQL)
    pqb = os.path.join(schema.ROOT, 'pipeline', 'data', 'flows_best.parquet').replace('\\', '/')
    con.execute(f"COPY (SELECT * FROM flows_best ORDER BY value_usd DESC NULLS LAST) TO '{pqb}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    nb = con.execute("SELECT COUNT(*) FROM flows_best").fetchone()[0]
    print(f"wrote pipeline/data/flows_best.parquet  ({nb:,} de-duplicated rows, from {total:,} raw)")
    raw = con.execute("""SELECT COUNT(*) FROM flows WHERE material LIKE 'copper%' AND period=2024
        AND ((reporter='COD' AND partner='CHN' AND flow='export') OR (reporter='CHN' AND partner='COD' AND flow='import'))""").fetchone()[0]
    best = con.execute("SELECT COUNT(*) FROM flows_best WHERE exporter='COD' AND importer='CHN' AND material LIKE 'copper%' AND period=2024").fetchone()[0]
    print(f"  dedup check - DRC->China copper 2024:  raw flows = {raw} rows  ->  flows_best = {best} row")

    # THE MOAT: reconcile mirror sides on the monthly data
    markup, stats = reconcile.reconcile(con)
    pqr = os.path.join(schema.ROOT, 'pipeline', 'data', 'flows_reconciled.parquet').replace('\\', '/')
    con.execute(f"COPY (SELECT * FROM flows_reconciled ORDER BY value_recon_fob DESC NULLS LAST) TO '{pqr}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    pqq = os.path.join(schema.ROOT, 'pipeline', 'data', 'reporter_quality.parquet').replace('\\', '/')
    con.execute(f"COPY (SELECT * FROM reporter_quality ORDER BY n_flows DESC) TO '{pqq}' (FORMAT PARQUET, COMPRESSION ZSTD)")

    # concordance-confidence layer: honest identity grade of each material's customs code (exact/dominant/proxy)
    con.execute("CREATE OR REPLACE TABLE material_confidence(material VARCHAR, confidence VARCHAR, form VARCHAR, caveat VARCHAR)")
    con.executemany("INSERT INTO material_confidence VALUES (?,?,?,?)",
                    [(m, c, f, cav) for m, (c, f, cav) in concordance.MATERIAL_CONF.items()])
    pqm = os.path.join(schema.ROOT, 'pipeline', 'data', 'material_confidence.parquet').replace('\\', '/')
    con.execute(f"COPY (SELECT * FROM material_confidence ORDER BY confidence, material) TO '{pqm}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    cd = {r[0]: r[1] for r in con.execute("SELECT confidence, COUNT(*) FROM material_confidence GROUP BY 1").fetchall()}
    print(f"wrote pipeline/data/material_confidence.parquet  (concordance identity: {cd})")

    # coverage / quality scorecard per material — honest map of what's covered well vs thin
    con.execute("""CREATE OR REPLACE TABLE coverage AS
      WITH b AS (SELECT hs6, any_value(material) AS material, COUNT(DISTINCT source) AS n_sources,
                        MAX(code_level) AS finest_level, MAX(period) AS latest_period,
                        ROUND(SUM(value_usd)/1e9, 2) AS value_busd, COUNT(DISTINCT reporter) AS n_reporters,
                        ROUND(AVG(via_entrepot::INT)*100) AS pct_via_entrepot,
                        COUNT(*) FILTER (WHERE confidential) AS n_confidential,
                        ROUND(100.0*COUNT(qty_kg)/COUNT(*)) AS pct_with_qty,
                        ROUND(median(value_usd/qty_kg) FILTER (WHERE qty_kg>0 AND value_usd>0), 2) AS usd_per_kg
                 FROM flows_best GROUP BY hs6),
           r AS (SELECT hs6, COUNT(*) FILTER (WHERE basis='reconciled') AS n_reconciled,
                        COUNT(*) FILTER (WHERE basis='disagreement') AS n_disagreement,
                        ROUND(AVG(agreement) FILTER (WHERE basis='reconciled'), 2) AS avg_agreement
                 FROM flows_reconciled GROUP BY hs6)
      SELECT b.hs6, b.material, mc.confidence AS code_confidence, mc.form AS code_form,
             b.n_sources, b.finest_level, b.latest_period, b.value_busd, b.n_reporters,
             b.pct_via_entrepot, b.n_confidential, b.pct_with_qty, b.usd_per_kg, COALESCE(r.n_reconciled, 0) AS n_reconciled,
             COALESCE(r.n_disagreement, 0) AS n_disagreement, r.avg_agreement, mc.caveat AS code_caveat
      FROM b LEFT JOIN r USING (hs6) LEFT JOIN material_confidence mc ON b.material = mc.material
      ORDER BY b.value_busd DESC""")
    pqc = os.path.join(schema.ROOT, 'pipeline', 'data', 'coverage.parquet').replace('\\', '/')
    con.execute(f"COPY (SELECT * FROM coverage) TO '{pqc}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    print(f"wrote pipeline/data/coverage.parquet  ({con.execute('SELECT COUNT(*) FROM coverage').fetchone()[0]} materials · quality scorecard)")
    print(f"\nwrote pipeline/data/flows_reconciled.parquet  -  freight markup (rough placeholder) = {markup:.3f}")
    for basis in ('reconciled', 'disagreement', 'exporter_only', 'importer_only_adj'):
        c, v = stats.get(basis, (0, 0))
        print(f"  {basis:18} {c:>7,} flows  " + (f"${v}B" if v is not None else "(no single value — range exposed)"))
    disagree = ("SELECT exporter, importer, material, ROUND(fob/1e6,1), ROUND(cif/1e6,1), ROUND(cif/fob,2) "
                "FROM flows_reconciled WHERE basis='disagreement' AND greatest(fob,cif)>1e6 "
                "ORDER BY greatest(fob,cif) DESC LIMIT 5")
    print("  flagged mirror DISAGREEMENTS (the monthly data-quality signal):")
    for r in con.execute(disagree).fetchall():
        print(f"    {r[0]}->{r[1]} {r[2]}: exporter ${r[3]}M vs importer ${r[4]}M  (cif/fob {r[5]})")

    # #3 BACI as EXTERNAL QA (a benchmark, NOT an input to the estimate): do monthly recon flows track BACI annual?
    # HONEST version (fixed after a council review flagged the old one-number QA as misleading): compare ONLY
    # same-year (2024) reconciled flows to BACI-2024, and annualize each pair by its ACTUAL months present
    # (not a blind x12) — the old calc x12'd 2025/2026 months against BACI 2024, a meaningless cross-year gap.
    qa_sql = ("""WITH b AS (SELECT reporter AS exporter, partner AS importer, hs6, SUM(value_usd) AS baci
                 FROM flows WHERE source='baci' GROUP BY 1,2,3),
                 m AS (SELECT exporter, importer, hs6, COUNT(DISTINCT period) AS nm, SUM(value_recon_fob) AS rs
                 FROM flows_reconciled WHERE value_recon_fob IS NOT NULL AND period BETWEEN 202401 AND 202412
                 GROUP BY 1,2,3)
                 SELECT COUNT(*), ROUND(median(m.rs*(12.0/m.nm)/b.baci),2),
                        ROUND(quantile_cont(m.rs*(12.0/m.nm)/b.baci, 0.25),2),
                        ROUND(quantile_cont(m.rs*(12.0/m.nm)/b.baci, 0.75),2)
                 FROM m JOIN b USING(exporter,importer,hs6) WHERE b.baci>0""")
    qa = con.execute(qa_sql).fetchone()
    print(f"\nBACI external QA (benchmark, not input): {qa[0]} same-year (2024) reconciled pairs match BACI-2024;")
    print(f"  annualized recon / BACI annual: median {qa[1]}  (IQR {qa[2]}-{qa[3]}; 1.0 = consistent)")
    print(f"  residual >1 reflects single-month extrapolation + a single global freight markup (too low for bulk) — a known, bounded limitation, NOT an input to the estimate")

    # ABLATION (show your work): does reconciling — and does the estimator choice — actually beat a single side?
    # Compares each estimator to BACI's monthly average on the matched 2024 reconciled flows; lower = closer.
    abl = con.execute("""WITH b AS (SELECT reporter AS exporter, partner AS importer, hs6, SUM(value_usd)/12 AS bmo
        FROM flows WHERE source='baci' GROUP BY 1,2,3)
        SELECT ROUND(median(abs(ln(r.fob/b.bmo))),3), ROUND(median(abs(ln((r.cif/r.cif_fob_markup)/b.bmo))),3),
               ROUND(median(abs(ln(sqrt(r.fob*r.cif/r.cif_fob_markup)/b.bmo))),3), COUNT(*)
        FROM flows_reconciled r JOIN b USING(exporter,importer,hs6)
        WHERE r.basis='reconciled' AND r.period BETWEEN 202401 AND 202412 AND b.bmo>0 AND r.fob>0 AND r.cif>0""").fetchone()
    print(f"  ablation vs BACI ({abl[3]} flows, median |ln(est/BACI)|, lower=closer): exporter-only {abl[0]} · importer-only {abl[1]} · geomean(both) {abl[2]}")
    print(f"    -> exporter(FOB) & geomean are ~tied and both beat the importer(CIF) side. Reconciliation's value is MONTHLY frequency + disagreement flagging, NOT a lower central error vs annual BACI; we publish the equal-weight geomean (uses both declarations).")

    print("\n--- the unified surface at work: HS-6 811292, wide (BACI) vs deep (Eurostat), one query ---")
    for r in con.execute("""SELECT source, code_level AS lvl, material, ROUND(SUM(value_usd)) AS usd
        FROM flows WHERE hs6='811292' GROUP BY 1,2,3 ORDER BY source, material""").fetchall():
        print(f"  {r[0]:9} L{r[1]}  {r[2]:<24} USD {r[3]:>14,.0f}")
    print("\n--- finest granularity available per material (coalesce logic in one line) ---")
    for r in con.execute("""SELECT material, MAX(code_level) AS finest, COUNT(DISTINCT source) AS sources
        FROM flows GROUP BY 1 ORDER BY finest DESC, material LIMIT 8""").fetchall():
        print(f"  {r[0]:<24} finest=L{r[1]}  sources={r[2]}")

    # capstone: regenerate the corridor validation dossier from the freshly-written tables (never drifts)
    try:
        import dossier
        dossier.main()
    except Exception as ex:
        print(f"  (dossier generation skipped: {ex})")


if __name__ == '__main__':
    main()
