"""Trade robustness cross-check: does our BACI-derived refining concentration survive an INDEPENDENT
trade source? BACI is CEPII's reconciliation of UN Comtrade mirror flows; here we recompute the same
refined-code exporter concentration straight from RAW UN Comtrade (reporter-declared exports, partner=World)
and compare leaders + HHI. If they agree, the chokepoint figures are not an artifact of BACI's reconciliation.

Reads the committed raw Comtrade + BACI (2022); writes out/robustness.json.  Run: python build_robustness.py
"""
import os, io, csv, zipfile, json
import pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = 2022
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
COMTRADE = os.path.join(ROOT, 'raw', 'comtrade', f'comtrade_{YEAR}.csv')
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso = dict(zip(cc.country_code, cc.country_iso2))

# refined codes we report concentration on (present in both sources)
CODES = ['740311', '750210', '282200', '810194', '810820', '811010', '281820', '810320', '720293', '850511']

def conc(shares):
    tot = sum(shares.values()) + 1e-9
    s = sorted(((k, v / tot) for k, v in shares.items()), key=lambda kv: -kv[1])
    top_iso = num2iso.get(int(s[0][0])) if str(s[0][0]).lstrip('-').isdigit() else s[0][0]
    hhi = sum(v * v for _, v in s)
    return top_iso, round(s[0][1] * 100, 1), round(hhi, 3)

# --- raw Comtrade: reporter-declared exports to World (partner=0) ---
com = {c: {} for c in CODES}
with open(COMTRADE, encoding='utf-8-sig') as f:
    r = csv.reader(f); next(r)
    for row in r:
        if row[4] == 'X' and row[2] == '0' and row[3] in com:      # export, partner=World
            try:
                com[row[3]][row[1]] = com[row[3]].get(row[1], 0.0) + float(row[5])
            except ValueError:
                pass

# --- BACI: exporter totals over all partners ---
with zipfile.ZipFile(BACI_ZIP) as z:
    baci = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{YEAR}_V202601.csv'), encoding='utf-8'),
                       dtype={'k': str}, usecols=['i', 'k', 'v'])
baci = baci[baci.k.isin(CODES)]
baci['v'] = pd.to_numeric(baci['v'], errors='coerce').fillna(0.0)
bac = {c: dict(g.groupby('i').v.sum()) for c, g in baci.groupby('k')}

rows = []
for c in CODES:
    if not com.get(c) or not bac.get(c):
        continue
    ci, cs, ch = conc(com[c]); bi, bs, bh = conc(bac[c])
    rows.append({'code': c, 'comtrade_top': ci, 'comtrade_share': cs, 'comtrade_hhi': ch,
                 'baci_top': bi, 'baci_share': bs, 'baci_hhi': bh,
                 'leader_match': ci == bi, 'hhi_gap': round(abs(ch - bh), 3), 'share_gap': round(abs(cs - bs), 1)})

match = sum(r['leader_match'] for r in rows)
mean_hhi_gap = round(sum(r['hhi_gap'] for r in rows) / max(len(rows), 1), 3)
mean_share_gap = round(sum(r['share_gap'] for r in rows) / max(len(rows), 1), 1)
print(f'Trade robustness: BACI (reconciled) vs raw UN Comtrade (reporter-declared), {YEAR}')
print(f"{'code':8}{'Comtrade':16}{'BACI':16}{'match':7}{'HHIgap':7}")
for r in rows:
    print(f"  {r['code']:8}{str(r['comtrade_top'])+' '+str(r['comtrade_share'])+'%':16}"
          f"{str(r['baci_top'])+' '+str(r['baci_share'])+'%':16}{'yes' if r['leader_match'] else 'NO':7}{r['hhi_gap']}")
print(f"\nleader agreement: {match}/{len(rows)} · mean HHI gap {mean_hhi_gap} · mean top-share gap {mean_share_gap}pp")
json.dump({'year': YEAR, 'rows': rows, 'leader_match': match, 'n': len(rows),
           'mean_hhi_gap': mean_hhi_gap, 'mean_share_gap': mean_share_gap},
          open(os.path.join(ROOT, 'out', 'robustness.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('WROTE out/robustness.json')
