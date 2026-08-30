#!/usr/bin/env python3
"""Trend robustness to the reconciliation choice (author-run; answers an adversarial-council demand).
The council objected that our claim 'the dilution shifts the level not the trend' rested on only two
years. Fair. This recomputes the engine-vs-BACI concentration GAP for EVERY year in the trend window
(2002-2024) and tests whether the trend conclusion actually survives.

For each tracked commodity we build two annual export-HHI series:
  - engine : from the atlas reconciliation, out/flows_<year>.json
  - baci   : from CEPII BACI HS02 (full 2002-2024 span), extracted here from raw/baci/BACI_HS02 zip
and run a Mann-Kendall-equivalent monotonic-trend test (Kendall's tau of HHI vs year; the MK S statistic
is monotone in tau) on each. The claim 'trend is unaffected by the reconciliation' is TRUE for a
commodity iff the two series agree on trend SIGN and on significance at 0.05. We report the agreement
rate and name every commodity where the correction would FLIP the trend sign or its significance.

Run: python build_trend_robustness.py   ->  writes out/trend_robustness.json   (needs pandas, scipy)
"""
import os, io, json, zipfile
import pandas as pd
from scipy.stats import kendalltau

ROOT = os.path.dirname(os.path.abspath(__file__))
YEARS = list(range(2002, 2025))
ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS02_V202601.zip')

DATA = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
def hs6(title):
    c = ''.join(ch for ch in title[title.find('(') + 1:title.find(')')] if ch.isdigit())
    return c[:6]
CODES = {hs6(m['title']) for m in DATA['materials']}
CODES.add('811231')
XW = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))
CODE2NAME = {e['title_code']: n for n, e in XW.items() if e.get('title_code')}

cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'), encoding='utf-8')
NUM2ISO = dict(zip(cc.country_code, cc.country_iso3))

def fold(s):
    return '811292' if s == '811231' else s

def baci_hhi_year(zf, year):
    """exporter-HHI per tracked commodity for one BACI year member."""
    member = f'BACI_HS02_Y{year}_V202601.csv'
    if member not in zf.namelist():
        return {}
    raw = pd.read_csv(io.TextIOWrapper(zf.open(member), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'k', 'v'])
    raw['k'] = raw.k.str.zfill(6)
    raw = raw[raw.k.isin(CODES)]
    if raw.empty:
        return {}
    raw['cmd'] = raw.k.map(fold)
    g = raw.groupby(['cmd', 'i'], as_index=False).v.sum()
    out = {}
    for cmd, sub in g.groupby('cmd'):
        t = sub.v.sum()
        if t > 0:
            out[cmd] = float(((sub.v / t) ** 2).sum())
    return out

# --- BACI series ---
baci_series = {}   # cmd -> {year: hhi}
with zipfile.ZipFile(ZIP) as zf:
    for y in YEARS:
        for cmd, h in baci_hhi_year(zf, y).items():
            baci_series.setdefault(cmd, {})[y] = h
    print('BACI HS02 extracted', flush=True)

# --- engine series from flows ---
def engine_hhi_year(year):
    p = os.path.join(ROOT, 'out', f'flows_{year}.json')
    if not os.path.exists(p):
        return {}
    fl = json.load(open(p, encoding='utf-8')).get('materials', {})
    out = {}
    for lab, flows in fl.items():
        tc = XW.get(lab, {}).get('title_code')
        if not tc:
            continue
        by = {}
        for f in flows:
            by[f['from']] = by.get(f['from'], 0.0) + f['value']
        t = sum(by.values())
        if t > 0:
            out[tc] = sum((v / t) ** 2 for v in by.values())
    return out

engine_series = {}
for y in YEARS:
    for cmd, h in engine_hhi_year(y).items():
        engine_series.setdefault(cmd, {})[y] = h

def mk(series):
    """Mann-Kendall-equivalent: Kendall tau of value vs year. Returns (sign, p, n)."""
    ys = sorted(series)
    if len(ys) < 5:
        return None
    tau, p = kendalltau(ys, [series[y] for y in ys])
    if tau is None or pd.isna(tau):
        return None
    sign = 0 if p >= 0.05 else (1 if tau > 0 else -1)
    return {'tau': round(float(tau), 3), 'p': round(float(p), 4),
            'dir': 'rising' if tau > 0 else 'falling', 'sig': p < 0.05, 'n': len(ys), 'sign05': sign}

rows, agree_sign, agree_sig, both, flips = [], 0, 0, 0, []
for cmd in sorted(set(engine_series) & set(baci_series)):
    e, b = mk(engine_series[cmd]), mk(baci_series[cmd])
    if not e or not b:
        continue
    both += 1
    sign_ok = (e['sign05'] == b['sign05'])          # agree incl. 'not significant' = 0
    sig_ok = (e['sig'] == b['sig'])
    agree_sign += sign_ok
    agree_sig += sig_ok
    rec = {'code': cmd, 'name': CODE2NAME.get(cmd, cmd), 'engine': e, 'baci': b,
           'trend_sign_agrees': sign_ok, 'significance_agrees': sig_ok}
    rows.append(rec)
    if not sign_ok:
        flips.append(rec)

summary = {'n_commodities': both, 'trend_sign_agrees': agree_sign,
           'significance_agrees': agree_sig,
           'trend_sign_agree_pct': round(100 * agree_sign / both, 1) if both else None,
           'n_sign_flips': len(flips)}
out = {'note': ('Mann-Kendall (Kendall-tau) monotonic-trend test on annual export-HHI 2002-2024, '
                'computed on the atlas engine series and on CEPII BACI HS02 independently. The claim '
                '"the reconciliation choice does not change the trend" holds for a commodity iff both '
                'agree on trend sign at p<0.05.'),
       'summary': summary, 'materials': rows}
json.dump(out, open(os.path.join(ROOT, 'out', 'trend_robustness.json'), 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False,
          default=lambda o: o.item() if hasattr(o, 'item') else str(o))

print(f"\ncommodities with both series testable: {both}")
print(f"trend SIGN agrees (engine vs BACI, p<0.05): {agree_sign}/{both} ({summary['trend_sign_agree_pct']}%)")
print(f"significance agrees: {agree_sig}/{both}")
if flips:
    print("sign/one-significant flips:")
    for r in flips:
        print(f"  {r['name']:12} engine {r['engine']['dir']} p={r['engine']['p']} (sig={r['engine']['sig']}) "
              f"| BACI {r['baci']['dir']} p={r['baci']['p']} (sig={r['baci']['sig']})")
print("\nwrote out/trend_robustness.json")
