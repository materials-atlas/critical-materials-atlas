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
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'), encoding='utf-8')
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

# Harvard Growth Lab (Bustos-Yildirim) — a 2nd, independent reconciliation (cached by build_harvard.py)
_hv_path = os.path.join(ROOT, 'out', 'harvard.json')
HV = json.load(open(_hv_path, encoding='utf-8'))['materials'] if os.path.exists(_hv_path) else {}

rows = []
for c in CODES:
    if not bac.get(c):
        continue
    bi, bs, bh = conc(bac[c])
    row = {'code': c, 'baci_top': bi, 'baci_share': bs, 'baci_hhi': bh}
    if com.get(c):
        ci, cs, chh = conc(com[c])
        row.update({'comtrade_top': ci, 'comtrade_share': cs, 'comtrade_hhi': chh, 'comtrade_match': ci == bi})
    hv = HV.get(c)
    if hv:
        row.update({'harvard_top': hv['top'], 'harvard_share': hv['top_share'], 'harvard_hhi': hv['hhi'],
                    'recon_match': hv['top'] == bi})       # two independent reconciliations agree?
    rows.append(row)

com_rows = [r for r in rows if 'comtrade_match' in r]
recon_rows = [r for r in rows if 'recon_match' in r]
com_match = sum(r['comtrade_match'] for r in com_rows)
recon_match = sum(r['recon_match'] for r in recon_rows)
print(f'Trade robustness {YEAR} — BACI vs raw Comtrade vs Harvard (Bustos-Yildirim):')
print(f"{'code':8}{'BACI':14}{'Comtrade':14}{'Harvard':14}")
for r in rows:
    print(f"  {r['code']:8}{str(r['baci_top'])+' '+str(r['baci_share'])+'%':14}"
          f"{(str(r.get('comtrade_top',''))+' '+str(r.get('comtrade_share',''))+'%') if 'comtrade_top' in r else '—':14}"
          f"{(str(r.get('harvard_top',''))+' '+str(r.get('harvard_share',''))+'%') if 'harvard_top' in r else '—':14}")
print(f"\nBACI vs raw Comtrade leader agreement: {com_match}/{len(com_rows)}")
print(f"BACI vs Harvard (two independent reconciliations) leader agreement: {recon_match}/{len(recon_rows)}")
json.dump({'year': YEAR, 'rows': rows,
           'comtrade_match': com_match, 'comtrade_n': len(com_rows),
           'recon_match': recon_match, 'recon_n': len(recon_rows),
           'harvard_year': HV and json.load(open(_hv_path, encoding='utf-8')).get('year')},
          open(os.path.join(ROOT, 'out', 'robustness.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('WROTE out/robustness.json')
