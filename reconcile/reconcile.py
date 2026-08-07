"""Heavy BACI-style reconciliation of raw UN Comtrade into a single bilateral value per flow.
Faithful to Gaulier & Zignago (2010):
  1. match the two mirror reports of each flow (exporter FOB, importer CIF);
  2. deflate every CIF import to an FOB basis by a robust per-product median markup (a gravity
     regression is unidentified on this ~31-product slice — see the inline note in step 2);
  3. estimate each reporter's reliability from a variance-components decomposition of the mirror
     discrepancy (E[d^2] = var_i + var_j), giving inverse-variance weights;
  4. reconcile two-sided flows by inverse-variance averaging on logs; keep one-sided flows
     (FOB-adjusting lone importer reports with the predicted markup).
Output: reconcile/recon_<year>.csv  (i_iso3, j_iso3, cmd, value)  + diagnostics to stdout.
Usage:  python reconcile.py 2024
"""
import os, sys
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

ROOT = os.environ.get('ATLAS_ROOT', '.')
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2024

# ---- country crosswalk: Comtrade M49 -> ISO3 (BACI table) ----
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
m49_iso3 = dict(zip(cc.country_code, cc.country_iso3))

# ---- geography (CEPII dist_cepii) — OPTIONAL: kept for diagnostics only; the CIF/FOB markup below uses
# a per-product median, so dist/contig are not consumed. Skipped if the file is absent (e.g. in CI). ----
geo_path = os.path.join(ROOT, 'raw', 'geodist', 'dist_cepii.xls')
if os.path.exists(geo_path):
    geo = pd.read_excel(geo_path)[['iso_o', 'iso_d', 'dist', 'distw', 'contig']]
    geo['distw'] = geo['distw'].fillna(geo['dist'])
else:
    geo = pd.DataFrame(columns=['iso_o', 'iso_d', 'dist', 'distw', 'contig'])
LANDLOCKED = set(('AFG ARM AZE BDI BFA BOL BWA CAF TCD ETH KAZ KGZ LAO LSO MWI MLI MDA MNG NPL NER PRY '
                  'RWA SSD SWZ TJK MKD TKM UGA UZB ZMB ZWE AND AUT BLR BTN HUN LIE LUX SMR SRB SVK CHE XKX').split())

# ---- raw Comtrade (accepts a gzipped fixture: comtrade_<year>.csv or .csv.gz) ----
cpath = os.path.join(ROOT, 'raw', 'comtrade', f'comtrade_{YEAR}.csv')
if not os.path.exists(cpath) and os.path.exists(cpath + '.gz'):
    cpath += '.gz'
df = pd.read_csv(cpath)
df = df[(df.value > 0) & (df.reporter != 0) & (df.partner != 0)]
df = df[df.reporter.isin(m49_iso3) & df.partner.isin(m49_iso3)]
df['r3'] = df.reporter.map(m49_iso3); df['p3'] = df.partner.map(m49_iso3)
df = df[df.r3 != df.p3]
df['cmd'] = df.cmd.astype(str).str.zfill(6)
print(f'raw rows {len(df)}  reporters {df.reporter.nunique()}  codes {df.cmd.nunique()}', flush=True)

# ---- directed flow i->j from both sides ----
exp = (df[df.flow == 'X'][['r3', 'p3', 'cmd', 'value', 'netwgt']]
       .rename(columns={'r3': 'i', 'p3': 'j', 'value': 'x_fob', 'netwgt': 'x_wgt'})
       .groupby(['i', 'j', 'cmd'], as_index=False).agg(x_fob=('x_fob', 'sum'), x_wgt=('x_wgt', 'sum')))
imp = (df[df.flow == 'M'][['r3', 'p3', 'cmd', 'value', 'netwgt']]
       .rename(columns={'r3': 'j', 'p3': 'i', 'value': 'm_cif', 'netwgt': 'm_wgt'})
       .groupby(['i', 'j', 'cmd'], as_index=False).agg(m_cif=('m_cif', 'sum'), m_wgt=('m_wgt', 'sum')))
both = exp.merge(imp, on=['i', 'j', 'cmd'], how='outer')
g = geo.rename(columns={'iso_o': 'i', 'iso_d': 'j'})
both = both.merge(g, on=['i', 'j'], how='left')
both['ll'] = both.i.isin(LANDLOCKED).astype(int) + both.j.isin(LANDLOCKED).astype(int)
print(f'flows: total {len(both)}  two-sided {both.x_fob.notna().__and__(both.m_cif.notna()).sum()}  '
      f'exp-only {(both.x_fob.notna() & both.m_cif.isna()).sum()}  imp-only {(both.m_cif.notna() & both.x_fob.isna()).sum()}', flush=True)

# ---- (2) CIF/FOB markup: robust per-product MEDIAN of M_cif/X_fob ----
# A gravity regression for CIF rates (BACI's approach) needs the full ~5000-product universe and
# millions of flows; on a 31-code slice the product-level M/X ratio is dominated by valuation /
# misreporting noise (we measured R^2=0.01, i.e. distance is unidentified). The median ratio per
# product is robust to that noise; we bound it to plausible freight (2%-30%). This deflates every
# CIF (import-reported) value to an FOB basis without the garbage swings of the noisy regression.
mt = both.dropna(subset=['x_fob', 'm_cif']).copy()
mt = mt[(mt.x_fob > 0) & (mt.m_cif > 0)]
mt['ratio'] = (mt.m_cif / mt.x_fob).clip(0.3, 3.0)             # winsorise wild misreports before the median
cif_by_cmd = mt.groupby('cmd').ratio.median().clip(1.02, 1.30)
gmed = float(np.clip(mt.ratio.median(), 1.02, 1.30)) if len(mt) else 1.08
both['cif'] = both.cmd.map(cif_by_cmd).fillna(gmed)
print(f'CIF/FOB markup (per-product median): median={cif_by_cmd.median():.3f} '
      f'range=[{cif_by_cmd.min():.3f}, {cif_by_cmd.max():.3f}] global={gmed:.3f}', flush=True)
both['m_fob'] = both.m_cif / both.cif                           # importer report on an FOB basis

# ---- (3) reliability weights via variance components: E[d^2] = var_i + var_j ----
tw = both.dropna(subset=['x_fob', 'm_fob']).copy()
tw = tw[(tw.x_fob > 0) & (tw.m_fob > 0)]
tw['d2'] = (np.log(tw.x_fob) - np.log(tw.m_fob)) ** 2
vc = smf.ols('d2 ~ C(i) + C(j) + 0', data=tw).fit()            # coefficients ~ reporter variances
# recover per-country variance (average of its i-role and j-role coefficients), clip positive
var = {}
for role in ('i', 'j'):
    d = vc.params.filter(like=f'C({role})')
    for k, v in d.items():
        iso = k.split('[')[-1].rstrip(']').replace('T.', '')
        var.setdefault(iso, []).append(v)
varc = {k: max(np.mean(v), 1e-3) for k, v in var.items()}
medvar = float(np.median(list(varc.values())))
def vget(iso): return varc.get(iso, medvar)
print(f'reliability: {len(varc)} reporters, median var={medvar:.3f}', flush=True)

# ---- (4) reconcile ----
def recon(r):
    x, mf = r.x_fob, r.m_fob
    if pd.notna(x) and pd.notna(mf) and x > 0 and mf > 0:
        wi, wj = 1.0 / vget(r.i), 1.0 / vget(r.j)              # inverse-variance on logs
        return float(np.exp((wi * np.log(x) + wj * np.log(mf)) / (wi + wj)))
    if pd.notna(x) and x > 0:   return float(x)                # exporter only
    if pd.notna(mf) and mf > 0: return float(mf)               # importer only (already FOB-adjusted)
    return np.nan
both['value'] = both.apply(recon, axis=1)
out = both.dropna(subset=['value'])[['i', 'j', 'cmd', 'value']].copy()
out = out[out.value > 0]
out.to_csv(os.path.join(ROOT, 'reconcile', f'recon_{YEAR}.csv'), index=False)
print(f'RECONCILED {YEAR}: {len(out)} flows, total ${out.value.sum()/1e9:.1f}B -> reconcile/recon_{YEAR}.csv', flush=True)
