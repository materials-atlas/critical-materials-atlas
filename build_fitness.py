"""Fitness-Criticality algorithm (Valverde-Carbonell, Pietrobelli & Menendez, Resources Policy 2024) --
an adaptation of the non-linear Economic Fitness-Complexity method (Tacchella et al. 2012) to critical
minerals. Country competitiveness and mineral criticality are two faces of the same coin, co-determined
on the bipartite country x material network:

    MFI_c  (Mining Fitness Index)   = sum_m  M_cm * CMI_m           -- fitness = extensive sum over the
                                                                       minerals you competitively export
    CMI_m  (Criticality Min. Index) = 1 / ( sum_c M_cm * (1/MFI_c) ) -- criticality is dominated by the
                                                                       LEAST-fit country that can supply it
(normalise by the mean each iteration; iterate to convergence). The 1/MFI term is the non-linearity that
makes a mineral 'critical' when only low-fitness countries can competitively export it -- the opposite of
ECI's linear averaging, and better on nested miner/refiner structures.

M is the binary RCA>=1 matrix over the atlas's 32 critical materials (RCA computed within the critical-
materials basket, as on the complexity page). Reads the committed BACI zip; writes out/fitness.json.
Run:  python build_fitness.py [year]
"""
import os, sys, io, zipfile, json
import numpy as np, pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2022
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
ITERS = 60

d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
def hs6(t):
    c = ''.join(ch for ch in t[t.find('(') + 1:t.find(')')] if ch.isdigit()); return c[:6]
code_labels = {}
for m in d['materials']:
    code_labels.setdefault(hs6(m['title']), []).append(m['label'])
codes = sorted(code_labels)

with zipfile.ZipFile(BACI_ZIP) as z:
    raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{YEAR}_V202601.csv'), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'k', 'v'])
raw = raw[raw.k.isin(codes)].copy(); raw['v'] = pd.to_numeric(raw['v'], errors='coerce').fillna(0.0)
X = raw.groupby(['i', 'k']).v.sum().reset_index()
M = X.pivot(index='i', columns='k', values='v').reindex(columns=codes).fillna(0.0)
# RCA within the critical-materials basket (matches the atlas complexity page). NB: on this small 31-
# material basket the non-linear country FITNESS (MFI) is ill-conditioned/unstable -- the reliable,
# validated output here is the mineral CRITICALITY index (CMI); MFI is reported as experimental only.
Xc = M.values.sum(1, keepdims=True); Xm = M.values.sum(0, keepdims=True); Xt = M.values.sum()
rca = np.divide(M.values / Xc, Xm / Xt, where=(Xc > 0) & (Xm > 0))
Mb = (rca >= 1).astype(float)
ok = Mb.sum(1) > 0
Mb = Mb[ok]
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso = dict(zip(cc.country_code, cc.country_iso2)); num2name = dict(zip(cc.country_code, cc.country_name))
countries = [int(c) for c in np.array(M.index)[ok]]

# --- Fitness-Criticality iteration ---
F = np.ones(Mb.shape[0]); Q = np.ones(Mb.shape[1])
for _ in range(ITERS):
    F_new = Mb @ Q
    F_new /= F_new.mean() + 1e-12
    with np.errstate(divide='ignore'):
        inv = np.where(F > 1e-12, 1.0 / F, 0.0)
    denom = Mb.T @ inv
    Q_new = np.where(denom > 1e-12, 1.0 / denom, 0.0)
    Q_new /= Q_new.mean() + 1e-12
    F, Q = F_new, Q_new

MFI = {num2iso.get(c, str(c)): float(f) for c, f in zip(countries, F) if isinstance(num2iso.get(c), str)}
CMI = {}
for j, code in enumerate(codes):
    CMI[code] = {'crit': float(Q[j]), 'labels': code_labels[code], 'ubiquity': int(Mb[:, j].sum())}

top_c = sorted(MFI, key=lambda c: -MFI[c])[:12]
top_m = sorted(CMI, key=lambda c: -CMI[c]['crit'])[:10]
print(f'=== Fitness-Criticality {YEAR} ({Mb.shape[0]} countries x {Mb.shape[1]} materials) ===')
print('\nMining Fitness Index (most competitive across critical materials):')
for c in top_c:
    print(f"  {c} {num2name.get({v:k for k,v in num2iso.items()}.get(c,-1),c)[:22]:22} {MFI[c]:.2f}")
print('\nCriticality Minerals Index (exported competitively by the fewest / least-fit):')
for code in top_m:
    print(f"  {'/'.join(CMI[code]['labels'])[:34]:34} crit {CMI[code]['crit']:6.2f}  ubiquity {CMI[code]['ubiquity']}")

json.dump({'year': YEAR, 'MFI': MFI,
           'CMI': {code: v for code, v in CMI.items()}},
          open(os.path.join(ROOT, 'out', 'fitness.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('\nWROTE out/fitness.json')
