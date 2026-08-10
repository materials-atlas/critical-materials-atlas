"""Long-run mine-production year series from the BGS World Mineral Statistics OGC API (free, 1970s–2024,
by country). Extends the Mined slider from the 5-year USGS window to ~25 years so structural shifts show
(Congo cobalt 21->69%, China antimony 84->35%). Cross-validates against our USGS headline: a material's
BGS series is only shipped if its 2023 slice reproduces the current USGS mined layer (top-1 + 2-of-3
overlap); divergences are reported, not silently shipped. Writes/merges out/mined_years.json and stamps
out/mined_years_src.json so the profile can label the source. Fetch via curl (BGS blocks bare urllib).

Run:  python build_bgs_mined.py
"""
import os, sys, json, subprocess, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
API = "https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics/items"
UA = "Mozilla/5.0"
STEPS = [2000, 2005, 2010, 2015, 2020, 2021, 2022, 2023, 2024]

# our material -> BGS mine-stage commodity name (candidates; first that validates wins)
MAP = {
    'copper': ['copper, mine'], 'cobalt': ['cobalt, mine'], 'nickel': ['nickel, mine'],
    'tungsten': ['tungsten, mine'], 'vanadium': ['vanadium, mine'], 'antimony': ['antimony, mine'],
    'lithium': ['lithium minerals'], 'graphite': ['graphite'], 'manganese': ['manganese ore'],
    'bauxite': ['bauxite'], 'beryllium': ['beryl'], 'strontium': ['strontium minerals'],
    'titanium': ['titanium minerals', 'titanium'], 'fluorspar': ['fluorspar'], 'baryte': ['barytes'],
    'phosphate': ['phosphate rock'], 'magnets': ['rare earth minerals'], 'niobium': ['niobium'],
    'tantalum': ['tantalum'], 'platinum': ['platinum group metals, mine'],
}

def fetch(commodity):
    url = f"{API}?bgs_commodity_trans={urllib.parse.quote(commodity, safe='')}&limit=6000&f=json"
    out = subprocess.run(["curl", "-s", "-A", UA, url], capture_output=True, text=True, timeout=90).stdout
    try:
        return json.loads(out).get('features', [])
    except Exception:
        return []

def series(commodity):
    feats = fetch(commodity)
    by = {}
    for f in feats:
        p = f['properties']
        iso, q, yr = p.get('country_iso2_code'), p.get('quantity'), (p.get('year') or '')[:4]
        if not iso or len(iso) != 2 or not yr.isdigit() or q in (None, ''):
            continue
        try:
            q = float(q)
        except ValueError:
            continue
        if q <= 0:
            continue
        by.setdefault(int(yr), {})
        by[int(yr)][iso] = by[int(yr)].get(iso, 0.0) + q
    out = {}
    for y in STEPS:
        if y not in by:
            continue
        tot = sum(by[y].values())
        if tot <= 0:
            continue
        rows = sorted(((c, round(100 * v / tot)) for c, v in by[y].items()), key=lambda x: -x[1])
        rows = [{'c': c, 'v': p} for c, p in rows if p >= 1]
        if rows:
            out[str(y)] = rows
    return out

d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
cur = {m['label']: [(x['c'], x['v']) for x in (m.get('mined') or [])] for m in d['materials']}
mined = json.load(open(os.path.join(ROOT, 'out', 'mined_years.json'), encoding='utf-8'))  # existing USGS 5-yr
src = {}
report = []
for lab, cands in MAP.items():
    curm = cur.get(lab)
    if not curm:
        continue
    chosen = None
    for c in cands:
        ser = series(c)
        v23 = ser.get('2023') or ser.get('2024')
        if not v23:
            continue
        ranked = v23
        top1 = ranked[0]['c'] == curm[0][0]
        ov = len(set(x['c'] for x in ranked[:3]) & set(cc for cc, _ in curm[:3]))
        if top1 and ov >= 2 and len(ser) >= 4:
            chosen = (c, ser); break
        else:
            report.append(f"  {lab:11} DIVERGES from USGS (BGS '{c}' 2023 top {ranked[0]['c']} vs USGS {curm[0][0]}) — kept USGS")
    if chosen:
        c, ser = chosen
        mined[lab] = ser
        src[lab] = 'BGS World Mineral Statistics'
        report.append(f"  {lab:11} BGS {sorted(int(y) for y in ser)} · '{c}' — 2023 matches USGS ✓")

json.dump(mined, open(os.path.join(ROOT, 'out', 'mined_years.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
json.dump(src, open(os.path.join(ROOT, 'out', 'mined_years_src.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print('\n'.join(report))
print(f"\nBGS long-run mined series for {len(src)} materials; mined_years.json now {len(mined)} total")
