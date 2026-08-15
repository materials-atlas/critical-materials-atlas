"""A -- the observable-downstream VALIDATION of B (the estimated next-rung climb).

B guesses next rungs from product-space proximity (density). A tests that guess against reality on the
few downstream products with clean HS codes: does a country's density to a downstream product in year t
actually predict that it ACQUIRES that product (RCA crosses 1) by year t+k? This is the Hidalgo-Hausmann
predictive test -- out-of-sample capability EMERGENCE, not a snapshot -- run on the 2017->2024 panel.

Observable downstream set (clean HS6, material -> end product):
  850511  NdFeB / permanent magnets      <- rare earths (the mine->refine->magnet climb, already the anchor)
  850760  Lithium-ion accumulators       <- lithium / cobalt / nickel / graphite
  854140  Photovoltaic / solar cells     <- silicon

Method: build the binary RCA matrix Mb (same floors as build_productspace: RCA>=1, world-share>=0.1%,
value>=$500k) for year0=2017 and year1=2024. Proximity phi0 = co-occurrence / max(ubiquity) on Mb0.
Density0(C,P) = sum_p Mb0[C,p]*phi0[p,P] / sum_p phi0[p,P]. Among countries that did NOT make P in 2017,
test whether density0 ranks the ones that DID acquire it by 2024 above those that did not (ROC-AUC, rank
based), plus the lift (entry rate in the top-quartile density vs the base rate). Pools across the 3 products.
A small, exploratory ground-truth set (3 products) -- enough to BOUND trust in B, not to certify it.

Writes out/avalidate.json.  Run: python build_avalidate.py
"""
import os, io, zipfile, json
import numpy as np, pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
MIN_VALUE, MIN_WS = 500.0, 0.001
Y0, Y1 = 2017, 2024
TARGETS = {'850511': ('NdFeB / permanent magnets', 'rare earths'),
           '850760': ('Lithium-ion batteries', 'lithium · cobalt · nickel · graphite'),
           '854140': ('Photovoltaic / solar cells', 'silicon')}
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
NUM2ISO = dict(zip(cc.country_code, cc.country_iso2))
NAMES = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf-8'))['names']

def binary_matrix(year):
    with zipfile.ZipFile(BACI_ZIP) as z:
        raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{year}_V202601.csv'), encoding='utf-8'),
                          dtype={'k': str}, usecols=['i', 'k', 'v'])
    raw['v'] = pd.to_numeric(raw['v'], errors='coerce')
    X = raw.groupby(['i', 'k'], as_index=False).v.sum()
    X = X[X.v >= MIN_VALUE]
    M = X.pivot(index='i', columns='k', values='v').fillna(0.0)
    M.index = [str(NUM2ISO.get(int(c), c)) for c in M.index]
    M = M.groupby(level=0).sum()                                   # collapse duplicate ISO rows
    M = M[~M.index.isin(['nan', 'None', ''])]
    tot_c = M.sum(1).values[:, None]; tot_p = M.sum(0).values[None, :]; tot = M.values.sum()
    rca = np.divide(M.values / tot_c, tot_p / tot, where=(tot_c > 0) & (tot_p > 0))
    share = np.divide(M.values, tot_p, where=tot_p > 0)
    Mb = ((rca >= 1) & (share >= MIN_WS)).astype(float)
    return pd.DataFrame(Mb, index=M.index, columns=M.columns)

print(f'building binary RCA matrices {Y0} and {Y1} ...', flush=True)
B0, B1 = binary_matrix(Y0), binary_matrix(Y1)
# proximity phi on year-0 space
kp0 = B0.values.sum(0)
co0 = B0.values.T @ B0.values
denom = np.maximum(kp0[:, None], kp0[None, :])
phi0 = np.divide(co0, denom, out=np.zeros_like(co0, float), where=denom > 0)
prod0 = list(B0.columns); pidx0 = {p: i for i, p in enumerate(prod0)}
phi_colsum = phi0.sum(0)   # per product P: sum_p phi0[p,P]

def auc(scores, labels):
    """ROC-AUC via the Mann-Whitney U rank statistic."""
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    npos, nneg = int(y.sum()), int((1 - y).sum())
    if npos == 0 or nneg == 0:
        return None
    order = np.argsort(s, kind='mergesort'); ranks = np.empty(len(s)); ranks[order] = np.arange(1, len(s) + 1)
    # average ranks for ties
    _, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    csum = np.cumsum(cnt); start = csum - cnt
    avg = {i: (start[i] + 1 + csum[i]) / 2.0 for i in range(len(cnt))}
    ranks = np.array([avg[i] for i in inv])
    return float((ranks[y == 1].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))

results = []
pooled_scores, pooled_labels = [], []
for code, (lab, upstream) in TARGETS.items():
    if code not in pidx0 or code not in B1.columns:
        results.append({'code': code, 'label': lab, 'skip': 'not in matrix'}); continue
    P = pidx0[code]
    dens = (B0.values @ phi0[:, P]) / (phi_colsum[P] + 1e-12)          # density of each 2017 country to P
    dens = pd.Series(dens, index=B0.index)
    made0 = B0[code]                                                   # made it in 2017?
    # align to countries present in 2017; their 2024 status (missing -> 0)
    made1 = B1[code].reindex(B0.index).fillna(0.0)
    test = made0 == 0                                                  # candidates: did NOT make it in 2017
    d = dens[test]; y = made1[test].astype(int)
    a = auc(d.values, y.values); base = float(y.mean())
    # lift: entry rate in the top density quartile vs the base rate
    q = d.quantile(0.75); top = y[d >= q]; toprate = float(top.mean()) if len(top) else None
    ent = [i for i in d.index if y[i] == 1]
    ranked = d.sort_values(ascending=False)
    confirms = [{'iso': i, 'name': NAMES.get(i, i), 'd': round(float(d[i]), 3)} for i in ranked.index if y[i] == 1][:6]
    misses = [{'iso': i, 'name': NAMES.get(i, i), 'd': round(float(d[i]), 3)} for i in ranked.index if y[i] == 0][:5]
    pooled_scores += list(d.values); pooled_labels += list(y.values)
    results.append({'code': code, 'label': lab, 'upstream': upstream, 'auc': round(a, 3) if a is not None else None,
                    'base_rate': round(base, 3), 'top_quartile_rate': round(toprate, 3) if toprate is not None else None,
                    'lift': round(toprate / base, 2) if (toprate and base) else None,
                    'n_candidates': int(test.sum()), 'n_entrants': int(y.sum()),
                    'confirms': confirms, 'top_opportunities': misses})

pooled_auc = auc(pooled_scores, pooled_labels)
payload = {'y0': Y0, 'y1': Y1, 'pooled_auc': round(pooled_auc, 3) if pooled_auc else None,
           'n_products': sum(1 for r in results if r.get('auc') is not None), 'products': results,
           'note': ('Predictive test of B: does product-space density in ' + str(Y0) + ' rank the countries that '
                    'ACQUIRED each downstream product (RCA crossed 1) by ' + str(Y1) + ' above those that did not? '
                    'ROC-AUC 0.5 = no skill, 1.0 = perfect. A small, exploratory ground-truth set (3 clean HS codes) '
                    '-- it bounds trust in the estimated climb, it does not certify it.')}
json.dump(payload, open(os.path.join(ROOT, 'out', 'avalidate.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)

print(f'=== A-validation (density {Y0} -> RCA emergence by {Y1}) ===')
for r in results:
    if r.get('auc') is None:
        print(f"  {r['code']} {r['label'][:26]:26} skip"); continue
    print(f"  {r['label'][:26]:26} AUC {r['auc']}  base {r['base_rate']}  top-quartile {r['top_quartile_rate']} (lift {r['lift']}x)  "
          f"entrants {r['n_entrants']}/{r['n_candidates']}")
    print(f"     entered & density-nearest: {', '.join(c['iso'] for c in r['confirms'][:6])}")
print(f'\nPOOLED AUC = {payload["pooled_auc"]}  across {payload["n_products"]} products')
print('WROTE out/avalidate.json')
