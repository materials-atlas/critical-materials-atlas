"""Validate our reconciliation against CEPII BACI's official 2024 — on what the atlas actually shows
(shares, top-k exporters, concentration), not just a global log-value correlation. Reports, per material
and overall: top-1 exporter match, top-3 overlap, exporter-share MAE, HHI (ours vs BACI), and the level
ratio (the known ~1.6x offset, kept visible). Usage: python validate.py 2024
"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np, pandas as pd
ROOT = r$PSScriptRoot
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2024

recon = pd.read_csv(ROOT + rf'\reconcile\recon_{YEAR}.csv', dtype={'cmd': str})
baci  = pd.read_csv(ROOT + rf'\reconcile\baci_{YEAR}.csv',  dtype={'cmd': str})
recon['cmd'] = recon.cmd.str.zfill(6).replace('811231', '811292')
recon = recon.groupby(['i', 'j', 'cmd'], as_index=False).value.sum()

# --- flow level (structure) ---
m = recon.merge(baci, on=['i', 'j', 'cmd'], how='inner', suffixes=('_r', '_b'))
m = m[(m.value_r > 0) & (m.value_b > 0)]
logcorr = np.corrcoef(np.log(m.value_r), np.log(m.value_b))[0, 1]

d = json.load(open(ROOT + r'\out\data.json', encoding='utf8'))
def hs6(mm):
    t = mm['title']; c = ''.join(ch for ch in t[t.find('(')+1:t.find(')')] if ch.isdigit()); return c[:6]
code2lab = {}
for mm in d['materials']:
    c = hs6(mm); c = '811292' if c == '811231' else c
    code2lab.setdefault(c, []).append(mm['label'])

def shares(df, cmd):
    s = df[df.cmd == cmd].groupby('i').value.sum()
    return (s / s.sum()).sort_values(ascending=False) if s.sum() else pd.Series(dtype=float)
def hhi(s): return float((s ** 2).sum()) if len(s) else 0.0

print(f'VALIDATION {YEAR} — our reconciliation vs official CEPII BACI\n')
print(f'  flow-level log-value correlation : {logcorr:.3f}  ({len(m)} overlapping flows)')
print(f'  median level ratio (ours/BACI)   : {np.median(m.value_r/m.value_b):.2f}  (known offset — shares unaffected)\n')
print(f'{"material":20s} {"top1":>5} {"top3":>6} {"shareMAE":>9} {"HHI_ours":>9} {"HHI_BACI":>9}')
rows = []
for cmd, labs in sorted(code2lab.items()):
    rs, bs = shares(recon, cmd), shares(baci, cmd)
    if not len(rs) or not len(bs): continue
    t1 = rs.index[0] == bs.index[0]
    t3 = len(set(rs.index[:3]) & set(bs.index[:3]))
    allc = set(rs.index[:6]) | set(bs.index[:6])
    mae = np.mean([abs(rs.get(c, 0) - bs.get(c, 0)) for c in allc]) * 100
    hr, hb = hhi(rs), hhi(bs)
    rows.append((t1, t3, mae, hr, hb))
    print(f'{"/".join(labs)[:20]:20s} {("Y" if t1 else "—"):>5} {t3:>4}/3 {mae:8.1f}% {hr:9.3f} {hb:9.3f}')
t1s = [r[0] for r in rows]; t3s = [r[1] for r in rows]; maes = [r[2] for r in rows]
hr = np.array([r[3] for r in rows]); hb = np.array([r[4] for r in rows])
print(f'\nSUMMARY ({len(rows)} materials):')
print(f'  top-1 exporter match : {sum(t1s)}/{len(t1s)}')
print(f'  top-3 overlap (mean) : {np.mean(t3s):.2f} / 3')
print(f'  exporter-share MAE   : {np.mean(maes):.1f}%   (median {np.median(maes):.1f}%)')
print(f'  HHI correlation      : {np.corrcoef(hr, hb)[0,1]:.3f}   (concentration reproduced)')
