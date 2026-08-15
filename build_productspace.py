"""Economic-complexity product space from the FULL CEPII BACI matrix (all HS6 x all countries), the
backbone for the mine->refine relatedness work. Computes Balassa RCA, the binary M-matrix (with a world-
share floor + min-value threshold to kill small-exporter noise, per the council critique), country ECI /
product PCI via the eigenvector (reflections) method, and proximity phi for the atlas's material codes to
every product. Outputs out/productspace.json + prints validation (ECI/PCI extremes must look sane before
any material claim is trusted). Reads the committed BACI HS17 zip; no API key.

Run:  python build_productspace.py [year]   (default 2022 — recent complete)
"""
import os, sys, io, zipfile, json
import numpy as np, pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2022
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
MIN_VALUE = 500.0        # thousand USD: drop micro flows
MIN_WORLD_SHARE = 0.001  # a country needs >=0.1% of world exports of a product before M can be 1

# atlas material HS6 codes (the traded form), from data.json titles
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
def hs6(t):
    c = ''.join(ch for ch in t[t.find('(') + 1:t.find(')')] if ch.isdigit()); return c[:6]
MAT = {m['label']: hs6(m['title']) for m in d['materials']}
mat_codes = sorted(set(MAT.values()))

print(f'reading BACI HS17 {YEAR} …', flush=True)
with zipfile.ZipFile(BACI_ZIP) as z:
    raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{YEAR}_V202601.csv'), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'j', 'k', 'v'])
raw['v'] = pd.to_numeric(raw['v'], errors='coerce')
X = raw.groupby(['i', 'k'], as_index=False).v.sum()          # exporter i, product k -> value
X = X[X.v >= MIN_VALUE]
M = X.pivot(index='i', columns='k', values='v').fillna(0.0)  # country x product value matrix
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso2 = dict(zip(cc.country_code, cc.country_iso2))
M.index = [str(num2iso2.get(int(c), c)) for c in M.index]     # BACI numeric code -> ISO2
print(f'matrix: {M.shape[0]} countries x {M.shape[1]} products', flush=True)

# --- Balassa RCA + binary M with a world-share floor ---
tot_c = M.sum(1).values[:, None]          # each country's total exports
tot_p = M.sum(0).values[None, :]          # each product's world exports
tot = M.values.sum()
share_cp = np.divide(M.values, tot_p, where=tot_p > 0)          # country's share of the product
rca = np.divide(M.values / tot_c, tot_p / tot, where=(tot_c > 0) & (tot_p > 0))
Mb = ((rca >= 1) & (share_cp >= MIN_WORLD_SHARE)).astype(float)  # binary competitiveness
countries = list(M.index); products = list(M.columns)
pidx = {p: i for i, p in enumerate(products)}

# --- ECI / PCI via the eigenvector method (Hidalgo-Hausmann 2009) ---
kc = Mb.sum(1); kp = Mb.sum(0)                                  # diversity, ubiquity
ok_c = kc > 0; ok_p = kp > 0
Mb2 = Mb[np.ix_(ok_c, ok_p)]
kc2 = Mb2.sum(1); kp2 = Mb2.sum(0)
Mcc = (Mb2 / kc2[:, None]) @ (Mb2 / kp2[None, :]).T             # country-country (row-stochastic)
w, V = np.linalg.eig(Mcc)
order = np.argsort(-w.real)
eci_vec = V[:, order[1]].real                                   # 2nd eigenvector
if np.corrcoef(eci_vec, kc2)[0, 1] < 0:
    eci_vec = -eci_vec
eci_std = (eci_vec - eci_vec.mean()) / eci_vec.std()
ECI = {str(c): float(v) for c, v in zip(np.array(countries)[ok_c], eci_std)}
# PCI: same on the product side
Mpp = (Mb2 / kp2[None, :]).T @ (Mb2 / kc2[:, None])
wp, Vp = np.linalg.eig(Mpp)
op = np.argsort(-wp.real)
pci_vec = Vp[:, op[1]].real
if np.corrcoef(pci_vec, kp2)[0, 1] > 0:
    pci_vec = -pci_vec
pci_std = (pci_vec - pci_vec.mean()) / pci_vec.std()
PCI = {str(p): float(v) for p, v in zip(np.array(products)[ok_p], pci_std)}

# --- proximity phi for our material codes to every product ---
co = Mb.T @ Mb                                                  # product co-occurrence counts
phi_targets = {}
for code in mat_codes:
    if code not in pidx:
        continue
    j = pidx[code]
    denom = np.maximum(kp, kp[j])                               # min-symmetrised: co / max(kp_i,kp_j)
    phi_targets[code] = {products[i]: float(co[i, j] / denom[i]) for i in range(len(products)) if denom[i] > 0 and co[i, j] > 0}

json.dump({'year': YEAR, 'ECI': ECI, 'PCI': PCI, 'mat_codes': MAT,
           'phi_targets': phi_targets},
          open(os.path.join(ROOT, 'out', 'productspace.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)

# ===================== mine -> refine layer (council-reshaped estimand) =====================
# only CLEAN ore-HS6 -> refined-HS6 pairs (single, distinct, non-shared, non-byproduct). Per the
# council: drop chains without a clean pair rather than invent one across HS vintages.
CROSSWALK = {
    'copper':   ('260300', '740311'),   # copper ores -> refined cathode
    'nickel':   ('260400', '750210'),   # nickel ores -> unwrought nickel
    'cobalt':   ('260500', '282200'),   # cobalt ores -> cobalt oxides
    'tungsten': ('261100', '810194'),   # tungsten ores -> unwrought tungsten
    'titanium': ('261400', '810820'),   # titanium ores -> unwrought titanium
    'antimony': ('261710', '811010'),   # antimony ores -> unwrought antimony
    'bauxite':  ('260600', '281820'),   # bauxite -> alumina
}
cur_mine = {m['label']: {x['c']: x['v'] for x in (m.get('mined') or [])} for m in d['materials']}
cur_ref = {m['label']: {x['c']: x['v'] for x in (m.get('refined') or [])} for m in d['materials']}
idx_iso = list(M.index)
eci_arr = np.array([ECI.get(c, np.nan) for c in idx_iso])
cn_mask = np.array([c != 'CN' for c in idx_iso])
MbX = Mb[cn_mask]; kpX = MbX.sum(0); coX = MbX.T @ MbX
isoX = list(np.array(idx_iso)[cn_mask]); idxX = {c: i for i, c in enumerate(isoX)}

mine_refine, report = {}, []
for lab, (ore, ref) in CROSSWALK.items():
    if ore not in pidx or ref not in pidx:
        report.append(f"  {lab}: code missing ({ore}/{ref})"); continue
    jo, jr = pidx[ore], pidx[ref]
    phi_or = float(co[jo, jr] / max(kp[jo], kp[jr])) if max(kp[jo], kp[jr]) else 0.0
    pci_gain = (PCI.get(ref) - PCI.get(ore)) if (ref in PCI and ore in PCI) else None
    phi_r = co[:, jr] / np.maximum(kp, kp[jr]); phi_r[jr] = 0.0
    dens = (Mb @ phi_r) / phi_r.sum()
    good = np.isfinite(eci_arr)
    b = np.polyfit(eci_arr[good], dens[good], 1)                 # density ~ ECI
    resid = dens - np.polyval(b, np.nan_to_num(eci_arr))         # "closer than its complexity predicts"
    phi_rX = coX[:, jr] / np.maximum(kpX, kpX[jr]); phi_rX[jr] = 0.0
    densX = (MbX @ phi_rX) / phi_rX.sum()                        # density with China removed from the space
    miners, refiners = cur_mine.get(lab, {}), cur_ref.get(lab, {})
    rows = []
    for i, c in enumerate(idx_iso):
        if miners.get(c, 0) >= 2:                                # actual miners (>=2% of world mine output)
            rows.append({'c': c, 'mines': miners[c], 'refines': refiners.get(c, 0),
                         'density': round(float(dens[i]), 3), 'resid': round(float(resid[i]), 3),
                         'density_exCN': round(float(densX[idxX[c]]), 3) if c in idxX else None,
                         'eci': round(float(ECI.get(c, 0.0)), 2)})
    rows.sort(key=lambda r: -r['resid'])
    mine_refine[lab] = {'ore': ore, 'refined': ref, 'phi_distance': round(phi_or, 3),
                        'pci_gain': round(pci_gain, 2) if pci_gain is not None else None, 'miners': rows}
    report.append(f"  {lab:9} phi(ore,ref)={phi_or:.3f}  PCI gain={pci_gain:+.2f}  miners={len(rows)}"
                  if pci_gain is not None else f"  {lab:9} phi={phi_or:.3f}")
json.dump(mine_refine, open(os.path.join(ROOT, 'out', 'mine_refine.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('\n=== mine->refine distance (low phi = big product-space jump) ===')
print('\n'.join(report))

# ===================== OPPORTUNITY GAIN / complexity outlook (who is CLOSEST to entering a stage) =====
# For each refined / magnet product: per-country DENSITY (feasibility = share of its capabilities that
# already surround the target) and the product's OUTLOOK (avg PCI of its proximity neighbourhood = how
# much complexity sits around entering it). Candidates = high density but not yet a competitive refiner
# -> the realistic diversification bets. This is the density/opportunity-gain leg of the product space.
TARGETS = {lab: ref for lab, (ore, ref) in CROSSWALK.items()}
TARGETS['magnet (NdFeB)'] = '850511'
opportunity = {}
for lab, code in TARGETS.items():
    if code not in pidx:
        continue
    j = pidx[code]
    phi_j = co[:, j] / np.maximum(kp, kp[j]); phi_j[j] = 0.0
    denom = phi_j.sum()
    if denom <= 0:
        continue
    dens = (Mb @ phi_j) / denom                                     # per country (idx_iso order)
    pci_vec = np.array([PCI.get(products[i], 0.0) for i in range(len(products))])
    outlook = float((phi_j * pci_vec).sum() / denom)                # neighbourhood complexity
    # RESIDUAL density: regress density on DIVERSITY (kc = # competitive products) and ECI, keep the residual.
    # Raw density is mechanically dominated by kc ("a country that makes many things is close to everything")
    # -- the control-test discipline from the product-space review. The residual = proximity to THIS product
    # BEYOND what breadth alone buys, so it surfaces genuinely material-adjacent countries, not just big ones.
    kc_arr = Mb.sum(1).astype(float)                                 # country diversity (count), Mb row order
    eci_arr = np.array([ECI.get(c, np.nan) for c in idx_iso])
    m = ~np.isnan(eci_arr)
    resid = np.full_like(dens, np.nan)
    if m.sum() > 3:
        A = np.vstack([kc_arr[m], eci_arr[m], np.ones(int(m.sum()))]).T
        b, _, _, _ = np.linalg.lstsq(A, dens[m], rcond=None)
        resid[m] = dens[m] - A @ b
    dens_eci_corr = float(np.corrcoef(dens, kc_arr)[0, 1])           # corr with diversity (the artifact driver)
    refiners = cur_ref.get(lab, {})
    already = Mb[:, j] > 0
    cand = []
    for i, c in enumerate(idx_iso):
        if already[i] or refiners.get(c, 0) >= 3:                   # skip current competitive refiners
            continue
        if not isinstance(c, str) or c in ('nan', 'None', '') or np.isnan(resid[i]):
            continue                                                # drop bad ISO / no-ECI countries
        cand.append({'c': c, 'density': round(float(dens[i]), 3),
                     'resid': round(float(resid[i]), 3), 'eci': round(float(ECI.get(c, 0.0)), 2)})
    # rank by RESIDUAL (material-specific proximity beyond breadth), not raw density (diversity artifact)
    cand.sort(key=lambda r: -r['resid'])
    opportunity[lab] = {'code': code, 'pci': round(float(PCI.get(code, 0.0)), 2),
                        'outlook': round(outlook, 2),
                        'density_eci_corr': round(dens_eci_corr, 2) if dens_eci_corr is not None else None,
                        'candidates': cand[:8]}
json.dump(opportunity, open(os.path.join(ROOT, 'out', 'opportunity.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('\n=== opportunity gain: closest NON-refiners to entering each stage (density) ===')
for lab, o in opportunity.items():
    tops = ', '.join(f"{r['c']} {r['density']:.2f}" for r in o['candidates'][:5])
    print(f"  {lab:16} PCI {o['pci']:+.2f} outlook {o['outlook']:+.2f} | candidates: {tops}")

# --- validation: extremes must look sane ---
top_c = sorted(ECI, key=lambda c: -ECI[c])[:8]; bot_c = sorted(ECI, key=lambda c: ECI[c])[:8]
top_p = sorted(PCI, key=lambda p: -PCI[p])[:6]; bot_p = sorted(PCI, key=lambda p: PCI[p])[:6]
print(f'\nECI highest: {top_c}\nECI lowest : {bot_c}')
print(f'PCI highest (complex): {top_p}\nPCI lowest (simple): {bot_p}')
print(f'\nWROTE productspace.json · {len(ECI)} countries scored, phi for {len(phi_targets)} material codes')
