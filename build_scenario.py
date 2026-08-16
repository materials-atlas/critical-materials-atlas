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
CW = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))
EUCRM = json.load(open(os.path.join(ROOT, 'out', 'eucrm.json'), encoding='utf-8')).get('materials', {})

# Materials with no separable trade series (811292 basket) can't be run through the export screen, but
# authoritative PRODUCTION data can see them. Curated context (USGS MCS 2025 + EU CRM 2023 + BGS):
#   gallium  = genuine near-monopoly (China ~99% USGS / ~94% EU CRM); no material alternative.
#   germanium= concentrated (China ~68-77% USGS / ~83% EU CRM) but real alternative refiners exist.
SHARED_CONTEXT = {
    'gallium':   {'verdict': 'chokepoint', 'alt': [],
                  'note': 'No material alternative — a genuine chokepoint the trade code cannot see. '
                          'China put gallium under export licensing in 2023.'},
    'germanium': {'verdict': 'has-alt', 'alt': ['Umicore (BE)', 'Teck (CA)', 'Russia'],
                  'note': 'Concentrated, but real alternative refiners exist: Umicore (Belgium recycling), '
                          'Teck (Canada, zinc-to-Ge), Russia — invisible in the shared trade code.'},
}
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso = dict(zip(cc.country_code, cc.country_iso2)); num2name = dict(zip(cc.country_code, cc.country_name))
_PREF = {'DE': 'Germany', 'TR': 'Türkiye', 'RU': 'Russia', 'KR': 'South Korea', 'CD': 'DR Congo',
         'US': 'United States', 'GB': 'United Kingdom', 'CZ': 'Czechia', 'VN': 'Viet Nam', 'IR': 'Iran',
         'BO': 'Bolivia', 'BE': 'Belgium', 'LA': 'Laos', 'SY': 'Syria', 'TW': 'Taiwan'}
_iso_name = {}
for _num, _iso in num2iso.items():
    if not isinstance(_iso, str):
        continue
    _nm = str(num2name.get(_num, _iso))
    if _iso not in _iso_name or ('(' in _iso_name[_iso] and '(' not in _nm):
        _iso_name[_iso] = _nm
def disp(iso): return _PREF.get(iso, _iso_name.get(iso, iso))

# human labels for the refined forms of multi-code materials (metal vs alloy/chemical)
FORM_LABEL = {'810194': 'metal', '284180': 'APT / tungstates', '811100': 'metal',
              '720211': 'ferro-alloy (high-C)', '720219': 'ferro-alloy', '720230': 'silico-alloy',
              '750210': 'unwrought', '720260': 'ferro-alloy'}

def hs6(t):
    c = ''.join(ch for ch in t[t.find('(') + 1:t.find(')')] if ch.isdigit()); return c[:6]
def nicename(m):
    t = m['title']; return t[:t.find('(')].strip() if '(' in t else t
MATS = {}
for m in d['materials']:
    if not m.get('refined'):
        continue
    cw = CW.get(m['label'], {})
    MATS[m['label']] = {'name': nicename(m), 'codes': cw.get('refined_hs') or [hs6(m['title'])],
                        'flags': cw.get('flags', []),
                        'phys': sorted(((x['c'], x['v']) for x in m['refined']), key=lambda kv: -kv[1])}
CODES = sorted({c for v in MATS.values() for c in v['codes']})

with zipfile.ZipFile(BACI_ZIP) as z:
    raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{YEAR}_V202601.csv'), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'k', 'v'])
raw = raw[raw.k.isin(CODES)].copy(); raw['v'] = pd.to_numeric(raw['v'], errors='coerce').fillna(0.0)
xpo = raw.groupby(['i', 'k']).v.sum()

def trade_shares(codes):
    by = {}
    for (c, k) in xpo.index:
        if k not in codes:
            continue
        iso = num2iso.get(int(c))
        if isinstance(iso, str):
            by[iso] = by.get(iso, 0.0) + float(xpo.get((c, k), 0.0))
    tot = sum(by.values()) + EPS
    return sorted(((k, v / tot * 100) for k, v in by.items()), key=lambda kv: -kv[1])

rows = []
for lab, info in MATS.items():
    phys = info['phys']; leader, lead_share = phys[0]
    # Ga/Ge sit in the shared "other minor metals" basket 811292 (indium etc. too); their individual
    # export series is not separable, so trade fallbacks are degenerate -> suppress. (Hafnium=811231 is
    # its own code and not affected.)
    shared = 'shared_refined' in info['flags']
    trade = [] if shared else trade_shares(info['codes'])
    lead_exp = next((v for c, v in trade if c == leader), 0.0)
    fb = [(c, v) for c, v in trade if c != leader]           # export fallbacks (exclude the leader)
    fb_top = fb[:3]
    best_fb = fb_top[0][1] if fb_top else 0.0
    # SPOF: leader dominates output AND no exporter fallback above a third of the leader's export volume.
    # Shared-code materials have no separable export series, so this screen cannot assess them -- exclude
    # rather than flag (a zeroed export figure makes the test vacuously true).
    spof = (not shared) and lead_share >= 50 and best_fb < max(lead_exp, EPS) / 3.0

    def spof_of(codes):                                       # verdict for one refined form (single code)
        sh = trade_shares(codes); le = next((v for c, v in sh if c == leader), 0.0)
        fbx = [(c, v) for c, v in sh if c != leader][:3]
        bf = fbx[0][1] if fbx else 0.0
        return le, fbx, (lead_share >= 50 and bf < max(le, EPS) / 3.0)
    # per-form breakdown: metal vs alloy/chemical can flip the verdict (tungsten APT, manganese ferroalloys)
    by_form = []
    if not shared and len(info['codes']) > 1:
        for c in info['codes']:
            le, fbx, sp = spof_of([c])
            by_form.append({'code': c, 'label': FORM_LABEL.get(c, c), 'lead_export_share': round(le, 1),
                            'fallbacks': [{'iso': k, 'name': disp(k), 'export_share': round(v, 1)} for k, v in fbx],
                            'spof': sp})
    form_dependent = len({f['spof'] for f in by_form}) > 1    # the answer depends on which form

    row = {'label': lab, 'name': info['name'], 'code': info['codes'][0], 'shared': shared,
           'leader': leader, 'leader_name': disp(leader), 'lead_share': round(lead_share, 1),
           'lead_export_share': round(lead_exp, 1),
           'fallbacks': [{'iso': c, 'name': disp(c), 'export_share': round(v, 1)} for c, v in fb_top],
           'spof': spof, 'by_form': by_form, 'form_dependent': form_dependent}
    if shared:                                               # production-based read (trade can't see it)
        ctx = SHARED_CONTEXT.get(lab, {})
        row['prod'] = {'usgs_bgs_share': round(lead_share, 0),
                       'eucrm_share': (EUCRM.get(lab) or {}).get('pct'),
                       'verdict': ctx.get('verdict', 'chokepoint'),
                       'alt': ctx.get('alt', []), 'note': ctx.get('note', '')}
    rows.append(row)

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
