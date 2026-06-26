"""Validate our home-built reconciliation against CEPII BACI's official 2024 (V202601).
Compares: total value, flow-level overlap + log-value correlation, BACI value coverage, and the
headline per-material top-exporter share (recon vs BACI). High agreement => the engine reproduces BACI.
Usage:  python validate.py 2024
"""
import sys, json
import numpy as np, pandas as pd
ROOT = r$PSScriptRoot
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2024

recon = pd.read_csv(ROOT + rf'\reconcile\recon_{YEAR}.csv', dtype={'cmd': str})
baci  = pd.read_csv(ROOT + rf'\reconcile\baci_{YEAR}.csv',  dtype={'cmd': str})
recon['cmd'] = recon.cmd.str.zfill(6).replace('811231', '811292')        # match BACI HS17 grouping
recon = recon.groupby(['i', 'j', 'cmd'], as_index=False).value.sum()

print(f'TOTAL {YEAR}: recon ${recon.value.sum()/1e9:.1f}B  vs  BACI ${baci.value.sum()/1e9:.1f}B  '
      f'(ratio {recon.value.sum()/baci.value.sum():.2f})')
m = recon.merge(baci, on=['i', 'j', 'cmd'], how='outer', suffixes=('_rec', '_baci'))
ov = m.dropna(subset=['value_rec', 'value_baci']); ov = ov[(ov.value_rec > 0) & (ov.value_baci > 0)]
print(f'flows: recon {len(recon)}  baci {len(baci)}  overlap {len(ov)}')
print(f'log-value correlation on overlap: {np.corrcoef(np.log(ov.value_rec), np.log(ov.value_baci))[0,1]:.3f}')
print(f'BACI value captured by overlap: {100*ov.value_baci.sum()/baci.value.sum():.1f}%')
print(f'median |recon/baci| ratio on overlap: {np.median(ov.value_rec/ov.value_baci):.2f}')

d = json.load(open(ROOT + r'\out\data.json', encoding='utf8'))
def hs6(mm):
    t = mm['title']; c = ''.join(ch for ch in t[t.find('(')+1:t.find(')')] if ch.isdigit()); return c[:6]
code2lab = {}
for mm in d['materials']:
    c = hs6(mm); c = '811292' if c == '811231' else c
    code2lab.setdefault(c, []).append(mm['label'])
def topexp(df, cmd):
    s = df[df.cmd == cmd].groupby('i').value.sum()
    return ('-', 0) if not len(s) else (s.idxmax(), round(100*s.max()/s.sum()))

print('\nmaterial             recon top-exp   BACI top-exp')
agree = 0; tot = 0
for cmd in sorted(code2lab):
    lab = '/'.join(code2lab[cmd]); r = topexp(recon, cmd); b = topexp(baci, cmd)
    tot += 1; same = (r[0] == b[0]); agree += same
    print(f'{lab[:19]:19s}  {r[0]:>3} {r[1]:3d}%      {b[0]:>3} {b[1]:3d}%   {"" if same else "<-- differ"}')
print(f'\ntop-exporter agreement: {agree}/{tot} materials')
