# -*- coding: utf-8 -*-
"""THE VALIDATION DOSSIER (capstone, per council review): for a curated set of critical-material corridors,
show the FULL chain of evidence and reach an EXPLICIT, data-driven call — raw sides -> flows_best choice ->
reconciliation decision -> external anchors (BACI, unit value, concordance grade) -> verdict. It regenerates
from the live Parquet tables every build, so it can never drift from the data. This is what turns the project
from 'clever ETL + stats' into 'a research instrument that shows its judgment'.

Run:  python pipeline/dossier.py   ->  writes pipeline/dossier.html
(build.py calls it automatically at the end of a build.)"""
import os, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duckdb, schema

D = os.path.join(schema.ROOT, 'pipeline', 'data')


def _con():
    con = duckdb.connect()
    for v, f in [('fb', 'flows_best'), ('fr', 'flows_reconciled'), ('fl', 'flows'), ('mc', 'material_confidence')]:
        con.execute(f"CREATE VIEW {v} AS SELECT * FROM '{os.path.join(D, f + '.parquet').replace(chr(92), '/')}'")
    return con


def pick_corridors(con):
    """Data-driven selection: the biggest corridors in each of the three adjudication archetypes."""
    stat = """WITH fb2 AS (
        SELECT exporter, importer, material, any_value(exporter_name) en, any_value(importer_name) inn,
               SUM(value_usd) v, MAX(period) latest, AVG(via_entrepot::INT) ent, list(DISTINCT source) srcs
        FROM fb GROUP BY 1,2,3),
      fr2 AS (SELECT exporter, importer, material,
               COUNT(*) FILTER (WHERE basis='reconciled') rec, COUNT(*) FILTER (WHERE basis='disagreement') dis
        FROM fr GROUP BY 1,2,3)
      SELECT f.exporter, f.importer, f.material, f.v, COALESCE(r.rec,0) rec, COALESCE(r.dis,0) dis, f.ent, f.srcs
      FROM fb2 f LEFT JOIN fr2 r USING (exporter, importer, material) WHERE f.v > 3e7"""
    rows = con.execute(stat).fetchall()

    def cap_per_material(cands, n, per_mat=3):
        """Rank by value but keep at most `per_mat` corridors of any one material, for a diverse dossier."""
        seen, out = {}, []
        for r in sorted(cands, key=lambda r: -r[3]):
            if seen.get(r[2], 0) >= per_mat:
                continue
            seen[r[2]] = seen.get(r[2], 0) + 1
            out.append(r)
            if len(out) >= n:
                break
        return out

    # rank each archetype by VALUE (strategic importance), requiring the relevant two-sided evidence to exist
    recon = cap_per_material([r for r in rows if r[4] >= 1 and r[4] >= r[5]], 7)
    disag = cap_per_material([r for r in rows if r[5] >= 1 and r[5] > r[4]], 7)
    # one-sided "dark exporter" corridors: big value but NO two-sided data (mirror / single declaration)
    oneside = cap_per_material([r for r in rows if r[4] == 0 and r[5] == 0 and ('mirror' in r[7] or r[3] > 2e9)], 8)
    seen, out = set(), []
    for tag, grp in [('recon', recon), ('disagree', disag), ('oneside', oneside)]:
        for r in grp:
            k = (r[0], r[1], r[2])
            if k in seen:
                continue
            seen.add(k)
            out.append((tag,) + r)
    return out


def evidence(con, ex, im, mat):
    e = {}
    e['sides'] = con.execute("""SELECT source, flow, ROUND(SUM(value_usd)/1e6,1)
        FROM fl WHERE ((flow='export' AND reporter=? AND partner=?) OR (flow='import' AND reporter=? AND partner=?))
        AND material=? GROUP BY 1,2 ORDER BY 3 DESC""", [ex, im, im, ex, mat]).fetchall()
    e['best'] = con.execute("""SELECT source, ROUND(SUM(value_usd)/1e6,1), MAX(period), ROUND(AVG(via_entrepot::INT)*100)
        FROM fb WHERE exporter=? AND importer=? AND material=? GROUP BY 1 ORDER BY 2 DESC LIMIT 1""",
        [ex, im, mat]).fetchone()
    e['recon'] = con.execute("""SELECT COUNT(*) FILTER (WHERE basis='reconciled'), COUNT(*) FILTER (WHERE basis='disagreement'),
        COUNT(*) FILTER (WHERE basis LIKE '%only%'), ROUND(AVG(agreement) FILTER (WHERE basis='reconciled'),2),
        ROUND(SUM(value_recon_fob)/1e6,1), mode(disagree_reason),
        ROUND(MIN(value_lo_fob)/1e6,1), ROUND(MAX(value_hi_fob)/1e6,1)
        FROM fr WHERE exporter=? AND importer=? AND material=?""", [ex, im, mat]).fetchone()
    e['baci'] = con.execute("""SELECT ROUND(SUM(value_usd)/1e6,1) FROM fl
        WHERE source='baci' AND reporter=? AND partner=? AND material=?""", [ex, im, mat]).fetchone()[0]
    e['uv'] = con.execute("""WITH m AS (SELECT median(value_usd/qty_kg) med FROM fb WHERE material=? AND qty_kg>0 AND value_usd>0)
        SELECT ROUND(median(f.value_usd/f.qty_kg),2), ROUND(any_value(m.med),2)
        FROM fb f, m WHERE f.material=? AND f.exporter=? AND f.importer=? AND f.qty_kg>0 AND f.value_usd>0""",
        [mat, mat, ex, im]).fetchone()
    e['conf'] = con.execute("SELECT confidence, form, caveat FROM mc WHERE material=?", [mat]).fetchone()
    return e


def verdict(tag, e):
    """The explicit CALL — derived from the evidence, not asserted."""
    rec, dis, one, agr = e['recon'][0], e['recon'][1], e['recon'][2], e['recon'][3]
    ent = (e['best'][3] or 0) if e['best'] else 0
    flags = []
    if ent >= 50:
        flags.append('RE-EXPORT hub leg — origin/destination may be trans-shipment, not true production/consumption')
    if e['conf'] and e['conf'][0] == 'proxy':
        flags.append(f"code is a PROXY ({e['conf'][2]})")
    if tag == 'oneside' or (rec == 0 and dis == 0):
        v, cls = ('ONE-SIDED — value rests on a single declaration / mirror reconstruction (the exporter does not '
                  'report); origin not independently confirmed by a second customs authority.'), 'v-oneside'
    elif dis > rec:
        v, cls = (f'UNRESOLVED — sides disagree on {dis} of {rec+dis} two-sided month(s); we publish the [lo,hi] range, '
                  f'not a point. Likely cause: {e["recon"][5]}.'), 'v-bad'
    elif rec >= 1 and dis == 0 and (agr or 0) >= 0.75:
        thin = ' — thin (single two-sided month so far; firms up as coverage grows)' if rec == 1 else ''
        v, cls = (f'RECON USABLE — all {rec} two-sided month(s) reconcile (agreement {agr}); the two customs sides '
                  f'independently corroborate this flow{thin}.'), 'v-good'
    else:
        v, cls = (f'MIXED — {rec} month(s) reconcile, {dis} flagged; usable per-month with the exposed flags '
                  f'(agreement {agr}).'), 'v-mix'
    return v, cls, flags


def esc(x):
    return html.escape(str(x)) if x is not None else '—'


def render(con, corridors):
    cards = []
    for row in corridors:
        tag, ex, im, mat, v, rec, dis, ent, srcs = row
        e = evidence(con, ex, im, mat)
        en = con.execute("SELECT any_value(exporter_name), any_value(importer_name) FROM fb WHERE exporter=? AND importer=? LIMIT 1", [ex, im]).fetchone()
        vtxt, vcls, flags = verdict(tag, e)
        sides = ''.join(f"<tr><td>{esc(s)}</td><td>{esc(fl)}</td><td class=num>${esc(mm)}M</td></tr>" for s, fl, mm in e['sides'])
        rc = e['recon']
        baci = f"${esc(e['baci'])}M" if e['baci'] else 'no BACI match'
        uv = (f"${e['uv'][0]:,.2f}/kg vs material median ${e['uv'][1]:,.2f}/kg" if e['uv'] and e['uv'][0] else 'n/a')
        conf = e['conf'] or ('—', '—', '')
        recline = (f"{rc[0]} reconciled · {rc[1]} disagreement · {rc[2]} one-sided months; "
                   f"agreement {esc(rc[3])}; recon Σ ${esc(rc[4])}M; range [${esc(rc[6])}M, ${esc(rc[7])}M]") if rc else '—'
        flagshtml = ''.join(f"<li class=flag>⚑ {esc(f)}</li>" for f in flags)
        cards.append(f"""<div class="card {vcls}">
  <h3>{esc(en[0])} → {esc(en[1])} · <span class="mat">{esc(mat)}</span>
      <span class="badge b-{esc(conf[0])}">{esc(conf[0])}: {esc(conf[1])}</span></h3>
  <div class="verdict {vcls}">{esc(vtxt)}</div>
  <ul class="flags">{flagshtml}</ul>
  <div class="grid">
    <div><b>1 · Raw sides reported</b><table><tr><th>source</th><th>flow</th><th>value</th></tr>{sides}</table></div>
    <div><b>2 · flows_best pick</b><p>{esc(e['best'][0]) if e['best'] else '—'} · ${esc(e['best'][1]) if e['best'] else '—'}M · latest {esc(e['best'][2]) if e['best'] else '—'} · {esc(ent) if e['best'] else '—'}% via entrepôt<br><span class=dim>(source-ranked: deep national &gt; wide reconciled &gt; mirror)</span></p>
      <b>3 · Reconciliation</b><p>{esc(recline)}</p></div>
    <div><b>4 · External anchors</b><p>BACI 2024 annual: {esc(baci)}<br>Unit value: {esc(uv)}<br>Concordance: <i>{esc(conf[2])}</i></p></div>
  </div>
</div>""")
    counts = {}
    for row in corridors:
        counts[row[0]] = counts.get(row[0], 0) + 1
    body = '\n'.join(cards)
    return TEMPLATE.replace('{{CARDS}}', body).replace('{{N}}', str(len(corridors))).replace(
        '{{SUMMARY}}', f"{counts.get('recon',0)} reconciled · {counts.get('disagree',0)} unresolved · {counts.get('oneside',0)} one-sided")


TEMPLATE = """<!doctype html><html><head><meta charset=utf-8><title>Critical-materials corridor validation dossier</title>
<meta name=viewport content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0f1216;--card:#171b21;--fg:#e6e9ef;--dim:#8b93a1;--line:#262c36;--good:#2ea36b;--bad:#d9713c;--mix:#c9a227;--one:#5b7fb0}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;padding:28px}
h1{font-size:24px;margin:0 0 4px}.sub{color:var(--dim);max-width:900px}.sum{margin:14px 0 24px;color:var(--dim);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line);border-radius:10px;padding:16px 18px;margin:0 0 16px}
.card.v-good{border-left-color:var(--good)}.card.v-bad{border-left-color:var(--bad)}.card.v-mix{border-left-color:var(--mix)}.card.v-oneside{border-left-color:var(--one)}
h3{margin:0 0 8px;font-size:17px}.mat{color:#9fd3ff}.badge{font-size:11px;padding:2px 7px;border-radius:20px;margin-left:6px;vertical-align:middle;border:1px solid var(--line)}
.b-exact{background:#12351f;color:#7fe0a6}.b-dominant{background:#3a3411;color:#e7cf6a}.b-proxy{background:#3a1f11;color:#f0a877}
.verdict{font-weight:600;margin:6px 0 8px;font-size:13.5px}.verdict.v-good{color:#7fe0a6}.verdict.v-bad{color:#f0a877}.verdict.v-mix{color:#e7cf6a}.verdict.v-oneside{color:#a8c6ea}
.flags{margin:0 0 10px;padding:0;list-style:none}.flag{color:#f0c877;font-size:12.5px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}@media(max-width:760px){.grid{grid-template-columns:1fr}}
.grid b{font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:.04em}.grid p{margin:4px 0 12px;font-size:13px}
table{border-collapse:collapse;width:100%;margin:4px 0 12px;font-size:12.5px}th,td{border-bottom:1px solid var(--line);padding:3px 6px;text-align:left}
th{color:var(--dim);font-weight:500}.num{text-align:right;font-variant-numeric:tabular-nums}.dim{color:var(--dim)}.dim,i{font-style:normal}
i{color:var(--dim)}footer{color:var(--dim);font-size:12px;margin-top:24px;border-top:1px solid var(--line);padding-top:12px}
</style></head><body>
<h1>Critical-materials corridor validation dossier</h1>
<div class=sub>For each corridor the full evidence chain is shown — <b>raw customs sides → flows_best pick → reconciliation decision → external anchors</b> (BACI annual, unit value, concordance grade) → an <b>explicit call</b>. Generated from the live Parquet tables, so it can never drift from the numbers. Colour = verdict: <span style="color:#7fe0a6">green usable</span>, <span style="color:#f0a877">orange unresolved</span>, <span style="color:#e7cf6a">yellow mixed</span>, <span style="color:#a8c6ea">blue one-sided</span>.</div>
<div class=sum>{{N}} corridors · {{SUMMARY}}</div>
{{CARDS}}
<footer>Public data only (CEPII BACI · Eurostat · UK HMRC · Brazil ComexStat · US Census · UN Comtrade · partner-mirror). Reconciliation exposes uncertainty; it does not manufacture certainty. Disagreements are published as ranges, never smoothed to a point.</footer>
</body></html>"""


def main():
    con = _con()
    corridors = pick_corridors(con)
    out = os.path.join(schema.ROOT, 'pipeline', 'dossier.html')
    open(out, 'w', encoding='utf8').write(render(con, corridors))
    print(f"wrote pipeline/dossier.html  ({len(corridors)} corridors adjudicated with full evidence chains)")


if __name__ == '__main__':
    main()
