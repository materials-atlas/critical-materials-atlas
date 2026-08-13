"""Refining supply-shock stress test -- the DEFENSIBLE 'scenario': a counterfactual on current data, not
a forecast. For each material: if the largest refiner stopped SUPPLYING THE WORLD MARKET, how much is at
risk and who could the world buy refined from instead?

Two measures, deliberately:
  MAGNITUDE AT RISK = the leader's share of world refined OUTPUT (BGS/USGS physical, from data.json) --
    how much capacity sits behind one country.
  FALLBACK = who else EXPORTS the refined form onto the world market (BACI refined-HS6 export shares).
    This is the right fallback signal: a refiner that absorbs its output domestically is not a fallback;
    an exporter is. It also fills the gap where physical data lists only the leader (antimony, PGMs...),
    since BGS has no refined-by-country series for specialty metals.

A material is a SINGLE POINT OF FAILURE if the leader holds >=50% of output AND no other country exports
more than a third of the leader's export volume. Writes out/scenario.json. Run: python build_scenario.py
"""
import os, sys, io, zipfile, json
import pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
EPS = 1e-9
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso = dict(zip(cc.country_code, cc.country_iso2)); num2name = dict(zip(cc.country_code, cc.country_name))
iso2name = {i: num2name.get({v: k for k, v in num2iso.items()}.get(i, -1), i) for i in set(num2iso.values())}

def hs6(t):
    c = ''.join(ch for ch in t[t.find('(') + 1:t.find(')')] if ch.isdigit()); return c[:6]
def nicename(m):
    t = m['title']; return t[:t.find('(')].strip() if '(' in t else t
MATS = {m['label']: {'name': nicename(m), 'code': hs6(m['title']),
                     'phys': sorted(((x['c'], x['v']) for x in (m.get('refined') or [])), key=lambda kv: -kv[1])}
        for m in d['materials'] if m.get('refined')}
CODES = sorted({v['code'] for v in MATS.values()})

with zipfile.ZipFile(BACI_ZIP) as z:
    raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{YEAR}_V202601.csv'), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'k', 'v'])
raw = raw[raw.k.isin(CODES)].copy(); raw['v'] = pd.to_numeric(raw['v'], errors='coerce').fillna(0.0)
xpo = raw.groupby(['k', 'i']).v.sum()

def trade_shares(code):
    if code not in xpo.index.get_level_values(0):
        return []
    s = xpo.loc[code]; tot = float(s.sum()) + EPS
    out = [(num2iso.get(int(c)), float(v) / tot * 100) for c, v in s.items() if isinstance(num2iso.get(int(c)), str)]
    return sorted(out, key=lambda kv: -kv[1])

rows = []
for lab, info in MATS.items():
    phys = info['phys']; leader, lead_share = phys[0]
    trade = trade_shares(info['code'])
    lead_exp = next((v for c, v in trade if c == leader), 0.0)
    fb = [(c, v) for c, v in trade if c != leader]           # export fallbacks (exclude the leader)
    fb_top = fb[:3]
    best_fb = fb_top[0][1] if fb_top else 0.0
    # SPOF: leader dominates output AND no exporter fallback above a third of the leader's export volume
    spof = lead_share >= 50 and best_fb < max(lead_exp, EPS) / 3.0
    rows.append({'label': lab, 'name': info['name'], 'code': info['code'],
                 'leader': leader, 'leader_name': iso2name.get(leader, leader), 'lead_share': round(lead_share, 1),
                 'lead_export_share': round(lead_exp, 1),
                 'fallbacks': [{'iso': c, 'name': iso2name.get(c, c), 'export_share': round(v, 1)} for c, v in fb_top],
                 'spof': spof})

rows.sort(key=lambda r: -r['lead_share'])
spof_rows = [r for r in rows if r['spof']]
cn = [r for r in spof_rows if r['leader'] == 'CN']
print('=== refining supply-shock stress test (remove the top refiner; fallback = who else EXPORTS refined) ===')
for r in rows:
    fb = ', '.join(f"{f['iso']} {f['export_share']:.0f}%" for f in r['fallbacks']) or 'none'
    print(f"  {r['name'][:22]:22} leader {r['leader']} {r['lead_share']:.0f}% output / {r['lead_export_share']:.0f}% exports"
          f"  | fallback exporters: {fb}  {'<< SPOF' if r['spof'] else ''}")
print(f"\n{len(spof_rows)}/{len(rows)} materials are refining SINGLE POINTS OF FAILURE (leader >=50% output, "
      f"no fallback exporter above a third); China leads {len(cn)}:")
print('  ', ', '.join(r['name'] for r in cn))
json.dump({'year': YEAR, 'materials': rows, 'spof_count': len(spof_rows), 'cn_spof': len(cn)},
          open(os.path.join(ROOT, 'out', 'scenario.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('\nWROTE out/scenario.json')
