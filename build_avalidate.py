"""A -- the observable-downstream VALIDATION of B (the estimated next-rung climb).

B guesses next rungs from product-space proximity (density). A tests that guess against reality on the
downstream products with clean HS codes: does a country's density to a downstream product in year t
actually predict that it ACQUIRES that product (RCA crosses 1) by year t+k? This is the Hidalgo-Hausmann
predictive test -- out-of-sample capability EMERGENCE, not a snapshot.

PANEL: run on the CEPII BACI HS2002 vintage, which reports ALL years 2002-2024 in one consistent
nomenclature -- so the long panel needs NO vintage join. Two windows are reported:
  LONG   2002 -> 2024  (22 years -- maximum capability-emergence, the most entries)
  RECENT 2016 -> 2024  (8 years  -- a moderate-horizon robustness check)
(Li-ion batteries use the HS2012 code 850760, absent from the HS2002-consistent panel, so they are
dropped here; they validated at AUC 0.93 in the 2017->2024 HS2017 run -- noted, not re-run.)

Products split into two TIERS:
  CAPABILITY-driven (density SHOULD predict): magnets, solar, copper wire, Al sheets, TiO2 pigment,
    Ti articles, ferro-vanadium, ferro-tungsten, ferro-titanium, nickel powders.
  COMMODITY / energy-sited (located by cheap power & ore, NOT capability -> density should NOT predict):
    copper bars, aluminium unwrought, ferro-silicon, ferro-silico-Mn, ferro-manganese.

Method per window: binary RCA matrix Mb (RCA>=1, world-share>=0.1%, value>=$500k) for t0 and t1; proximity
phi0 = co-occurrence/max(ubiquity) on Mb0; density0(C,P)=sum_p Mb0[C,p]*phi0[p,P]/sum_p phi0[p,P]. Among
countries NOT making P at t0, ROC-AUC of density0 ranking those that DID acquire it by t1. Pooled overall
and per tier. Still exploratory (few entrants per product) -- it BOUNDS trust in B, does not certify it.

Writes out/avalidate.json.  Run: python build_avalidate.py
"""
import os, io, zipfile, json
import numpy as np, pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS02_V202601.zip')   # HS2002 vintage: 2002-2024 consistent
FILE = 'BACI_HS02_Y{}_V202601.csv'
MIN_VALUE, MIN_WS = 500.0, 0.001
WINDOWS = {'long': (2002, 2024), 'recent': (2016, 2024)}
BATTERY_NOTE = 'Li-ion batteries (HS2012 code 850760) validated at AUC 0.93 in the 2017-2024 HS2017 run; absent from this HS2002 panel.'
TARGETS = {
    '850511': ('NdFeB / permanent magnets', 'rare earths', 'cap'),
    '854140': ('Photovoltaic / solar cells', 'silicon', 'cap'),
    '740811': ('Copper wire, refined', 'copper', 'cap'),
    '760612': ('Aluminium plates/sheets, alloyed', 'bauxite', 'cap'),
    '320611': ('Pigments based on TiO2', 'titanium', 'cap'),
    '810890': ('Titanium articles', 'titanium', 'cap'),
    '720292': ('Ferro-vanadium', 'vanadium', 'cap'),
    '720280': ('Ferro-tungsten', 'tungsten', 'cap'),
    '720291': ('Ferro-titanium', 'titanium', 'cap'),
    '750400': ('Nickel powders / flakes', 'nickel', 'cap'),
    '740710': ('Copper bars / rods', 'copper', 'com'),
    '760120': ('Aluminium, unwrought', 'bauxite', 'com'),
    '720221': ('Ferro-silicon', 'silicon', 'com'),
    '720230': ('Ferro-silico-manganese', 'manganese · silicon', 'com'),
    '720219': ('Ferro-manganese', 'manganese', 'com')}
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
NUM2ISO = dict(zip(cc.country_code, cc.country_iso2))
NAMES = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf-8'))['names']

_MB_CACHE = {}
def binary_matrix(year):
    if year in _MB_CACHE:
        return _MB_CACHE[year]
    with zipfile.ZipFile(BACI_ZIP) as z:
        raw = pd.read_csv(io.TextIOWrapper(z.open(FILE.format(year)), encoding='utf-8'),
                          dtype={'k': str}, usecols=['i', 'k', 'v'])
    raw['v'] = pd.to_numeric(raw['v'], errors='coerce')
    X = raw.groupby(['i', 'k'], as_index=False).v.sum()
    X = X[X.v >= MIN_VALUE]
    M = X.pivot(index='i', columns='k', values='v').fillna(0.0)
    M.index = [str(NUM2ISO.get(int(c), c)) for c in M.index]
    M = M.groupby(level=0).sum()
    M = M[~M.index.isin(['nan', 'None', ''])]
    tot_c = M.values.sum(1)[:, None]; tot_p = M.values.sum(0)[None, :]; tot = M.values.sum()
    rca = np.divide(M.values / tot_c, tot_p / tot, where=(tot_c > 0) & (tot_p > 0))
    share = np.divide(M.values, tot_p, where=tot_p > 0)
    Mb = pd.DataFrame(((rca >= 1) & (share >= MIN_WS)).astype(float), index=M.index, columns=M.columns)
    _MB_CACHE[year] = Mb
    return Mb

# negative-control placebos: if density "predicts" these food/textile products as well as the
# critical-material downstream, the signal is a diversity artifact, not product-space capability.
PLACEBOS = {'220830': 'whisky', '030212': 'fresh salmon', '220421': 'wine', '520100': 'cotton'}

def auc(scores, labels):
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    npos, nneg = int(y.sum()), int((1 - y).sum())
    if npos == 0 or nneg == 0:
        return None
    _, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    csum = np.cumsum(cnt); start = csum - cnt
    avg = {i: (start[i] + 1 + csum[i]) / 2.0 for i in range(len(cnt))}
    ranks = np.array([avg[i] for i in inv])
    return float((ranks[y == 1].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))

def pr_auc(scores, labels):
    """Average precision (area under precision-recall) -- honest under extreme class imbalance."""
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    if y.sum() == 0:
        return None
    o = np.argsort(-s, kind='mergesort'); y = y[o]
    tp = np.cumsum(y); prec = tp / np.arange(1, len(y) + 1)
    rec = tp / y.sum(); ap = 0.0; prev = 0.0
    for i in range(len(y)):
        if y[i]:
            ap += prec[i] * (rec[i] - prev); prev = rec[i]
    return float(ap)

def residual_auc(dens, div, y):
    """AUC of density after regressing out diversity (kc) -- does the product space add anything?"""
    d = np.asarray(dens, float); k = np.asarray(div, float)
    A = np.vstack([k, np.ones(len(k))]).T
    b, _, _, _ = np.linalg.lstsq(A, d, rcond=None)
    return auc(d - A @ b, y)

def run_window(t0, t1):
    B0, B1 = binary_matrix(t0), binary_matrix(t1)
    kp0 = B0.values.sum(0); co0 = B0.values.T @ B0.values
    den = np.maximum(kp0[:, None], kp0[None, :])
    phi0 = np.divide(co0, den, out=np.zeros_like(co0, float), where=den > 0)
    pidx0 = {p: i for i, p in enumerate(B0.columns)}; colsum = phi0.sum(0)
    kc = pd.Series(B0.values.sum(1), index=B0.index)   # country diversity (# competitive products)
    tier_pool = {'cap': ([], [], []), 'com': ([], [], [])}   # (density, diversity, y)
    pooled = ([], [], []); prods = []
    percountry = {}   # per-country downstream trajectory over this window (for the country-mode validation)
    for code, (lab, up, tier) in TARGETS.items():
        if code not in pidx0 or code not in B1.columns:
            prods.append({'code': code, 'label': lab, 'tier': tier, 'skip': 1}); continue
        P = pidx0[code]
        dens = pd.Series((B0.values @ phi0[:, P]) / (colsum[P] + 1e-12), index=B0.index)
        made0 = B0[code]; made1 = B1[code].reindex(B0.index).fillna(0.0)
        test = made0 == 0; d = dens[test]; y = made1[test].astype(int)
        a = auc(d.values, y.values); base = float(y.mean())
        qd = d.quantile(0.75)   # per-country trajectory: did the density-near ones climb?
        for C in d.index:
            iso = C
            if y[C] == 1:        # ACQUIRED it over the window
                percountry.setdefault(iso, {'gained': [], 'near': []})['gained'].append(
                    {'code': code, 'label': lab, 'tier': tier, 'pred': bool(d[C] >= qd)})
            elif d[C] >= qd:     # density-near in t0 but still NOT made by t1 -> open opportunity
                percountry.setdefault(iso, {'gained': [], 'near': []})['near'].append(
                    {'code': code, 'label': lab, 'tier': tier})
        kk = kc[test]
        ranked = d.sort_values(ascending=False)
        confirms = [{'iso': i, 'name': NAMES.get(i, i)} for i in ranked.index if y[i] == 1][:6]
        tier_pool[tier][0].extend(d.values); tier_pool[tier][1].extend(kk.values); tier_pool[tier][2].extend(y.values)
        pooled[0].extend(d.values); pooled[1].extend(kk.values); pooled[2].extend(y.values)
        prods.append({'code': code, 'label': lab, 'upstream': up, 'tier': tier,
                      'auc': round(a, 3) if a is not None else None,
                      'pr_auc': round(pr_auc(d.values, y.values), 3) if y.sum() else None,
                      'base_rate': round(base, 3),
                      'n_candidates': int(test.sum()), 'n_entrants': int(y.sum()), 'confirms': confirms})
    # placebos (negative controls): density AUC for food/textile products
    plac = []
    for pc_code, pc_lab in PLACEBOS.items():
        if pc_code not in pidx0 or pc_code not in B1.columns:
            continue
        P = pidx0[pc_code]
        dens = pd.Series((B0.values @ phi0[:, P]) / (colsum[P] + 1e-12), index=B0.index)
        made0 = B0[pc_code]; made1 = B1[pc_code].reindex(B0.index).fillna(0.0)
        test = made0 == 0; d = dens[test]; y = made1[test].astype(int); aa = auc(d.values, y.values)
        if aa is not None:
            plac.append({'code': pc_code, 'label': pc_lab, 'auc': round(aa, 3), 'n_entrants': int(y.sum())})
    plac_auc = auc([x for r in [] for x in r], []) if False else (
        round(np.mean([p['auc'] for p in plac]), 3) if plac else None)

    def ts(t):
        s, k, y = tier_pool[t]
        ad = auc(s, y); adiv = auc(k, y); ares = residual_auc(s, k, y)
        return {'auc': round(ad, 3) if ad is not None else None,
                'auc_diversity': round(adiv, 3) if adiv is not None else None,
                'auc_residual': round(ares, 3) if ares is not None else None,
                'n_products': sum(1 for r in prods if r.get('tier') == t and r.get('auc') is not None),
                'n_entrants': int(sum(y))}
    pa = auc(pooled[0], pooled[2])
    # trim per-country: keep countries that gained or are near >=1; cap near-list to 6
    pc = {}
    for iso, v in percountry.items():
        if v['gained'] or v['near']:
            pc[iso] = {'gained': v['gained'], 'near': v['near'][:6]}
    return {'t0': t0, 't1': t1, 'by_tier': {'cap': ts('cap'), 'com': ts('com')},
            'pooled_auc': round(pa, 3) if pa else None,
            'placebos': plac, 'placebo_auc': plac_auc,
            'n_products': sum(1 for r in prods if r.get('auc') is not None),
            'n_entrants': int(sum(pooled[2])), 'products': prods, 'per_country': pc}

print('building HS2002 panel (this reads several large years) ...', flush=True)
windows = {}
for name, (t0, t1) in WINDOWS.items():
    print(f'  window {name}: {t0} -> {t1}', flush=True)
    windows[name] = run_window(t0, t1)

payload = {'panel': 'BACI HS2002 (2002-2024, consistent nomenclature)', 'windows': windows,
           'battery_note': BATTERY_NOTE,
           'note': ('A GENERAL product-space appearance test (NOT a validation of B''s specific next-rung codes): '
                    'does density at t0 rank the countries that ACQUIRED a downstream product (RCA crossed 1) by t1 '
                    'above those that did not? The honest verdict, after controls: density barely beats a pure '
                    'DIVERSITY baseline (auc_diversity), and once diversity is regressed out the residual AUC '
                    'collapses toward chance -- and PLACEBO products (whisky, salmon) score in the same band. So '
                    'the apparent "capability climb" is mostly that already-diversified economies diversify further, '
                    'not evidence that product-space proximity forecasts critical-material capability. ROC-AUC is '
                    'also optimistic under ~0.5-5% base rates -- see pr_auc. Exploratory; reported as a NULL-ish '
                    'control result, not a confirmation.')}
json.dump(payload, open(os.path.join(ROOT, 'out', 'avalidate.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)

for name, w in windows.items():
    c = w['by_tier']['cap']
    print(f"\n=== {name.upper()} {w['t0']}->{w['t1']} ===")
    print(f"  CAPABILITY: density {c['auc']}  vs diversity {c['auc_diversity']}  residual(density perp diversity) {c['auc_residual']}  ({c['n_entrants']} entries)")
    print(f"  COMMODITY : density {w['by_tier']['com']['auc']}  residual {w['by_tier']['com']['auc_residual']}")
    print(f"  PLACEBOS  : mean density AUC {w['placebo_auc']}  ({', '.join(p['label']+' '+str(p['auc']) for p in w['placebos'])})")
print('\nHonest reading: density ~= diversity; residual collapses toward chance; placebos match. NULL-ish control.')
print('WROTE out/avalidate.json')
