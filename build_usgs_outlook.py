"""USGS World Minerals Outlook to 2029 (SIR 2025-5021; data release DOI 10.5066/P1HTTCWN, CC0) -- the
public, forward-looking capacity layer. Country-level production CAPACITY 2024->2029 for 8 commodities.
Crucially the capacity FORM is the metal/refining stage for gallium, magnesium, titanium and helium (a
forward REFINING signal), and the mine stage for cobalt, lithium and the PGMs.

For each commodity we compute the top holder's 2024 capacity SHARE + HHI, and the WORLD capacity growth
2024->2029 (the release gives a country breakdown for 2024 only; outlook years are world totals). So the atlas
can say whether a chokepoint is expected to HARDEN or EASE -- turning the static snapshot into a short
forward view. Parses the committed CSV; writes out/usgs_outlook.json.  Run: python build_usgs_outlook.py
"""
import os, csv, json
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, 'raw', 'usgs_outlook', 'outlook.csv')

COM2LAB = {'Cobalt': 'cobalt', 'Gallium': 'gallium', 'Helium': 'helium', 'Lithium': 'lithium',
           'Magnesium metal': 'magnesium', 'Palladium': 'palladium', 'Platinum': 'platinum', 'Titanium': 'titanium'}
STAGE = {'gallium': 'refining', 'magnesium': 'refining', 'titanium': 'refining', 'helium': 'refining',
         'cobalt': 'mine', 'lithium': 'mine', 'platinum': 'mine', 'palladium': 'mine'}
N2I = {'Algeria': 'DZ', 'Argentina': 'AR', 'Australia': 'AU', 'Brazil': 'BR', 'Canada': 'CA', 'Chile': 'CL',
       'China': 'CN', 'Colombia': 'CO', 'Congo (Kinshasa)': 'CD', 'Cuba': 'CU', 'Ethiopia': 'ET',
       'Finland': 'FI', 'Germany': 'DE', 'Hungary': 'HU', 'India': 'IN', 'Indonesia': 'ID', 'Iran': 'IR',
       'Israel': 'IL', 'Japan': 'JP', 'Kazakhstan': 'KZ', 'Korea, Republic of': 'KR', 'South Korea': 'KR',
       'Madagascar': 'MG', 'Mexico': 'MX', 'Morocco': 'MA', 'Namibia': 'NA', 'New Caledonia': 'NC',
       'Papua New Guinea': 'PG', 'Philippines': 'PH', 'Poland': 'PL', 'Portugal': 'PT', 'Qatar': 'QA',
       'Russia': 'RU', 'Saudi Arabia': 'SA', 'Serbia': 'RS', 'South Africa': 'ZA', 'Turkey': 'TR',
       'Türkiye': 'TR', 'Ukraine': 'UA', 'United States': 'US', 'Uzbekistan': 'UZ', 'Zambia': 'ZM',
       'Zimbabwe': 'ZW', 'Norway': 'NO', 'Bolivia': 'BO'}

def region_iso(r):
    if r.startswith('United States'):
        return 'US'
    return N2I.get(r)

rows = list(csv.reader(open(CSV, encoding='utf-8-sig')))[1:]
country24 = {}    # commodity -> {iso: 2024 capacity}
world = {}        # commodity -> {year: world-total capacity}
for r in rows:
    if not r or r[4] != 'Capacity':
        continue
    com, yr = r[0], r[1]
    try:
        q = float(r[3])
    except ValueError:
        continue
    if r[7] in ('World', 'Total'):
        world.setdefault(com, {})[yr] = q
        continue
    if yr == '2024':                              # country breakdown exists for 2024 only
        iso = region_iso(r[7])
        if iso:
            country24.setdefault(com, {})[iso] = country24.get(com, {}).get(iso, 0.0) + q

out = {}
for com, lab in COM2LAB.items():
    cc = country24.get(com, {}); w = world.get(com, {})
    if not cc or '2024' not in w or '2029' not in w:
        continue
    # normalise by the sum of REPORTED national capacity (listed countries can exceed the world figure,
    # which is a rounded/different measure) so shares form a valid composition and HHI is well-defined.
    denom = sum(cc.values()) + 1e-9
    s = sorted(((iso, v / denom * 100) for iso, v in cc.items()), key=lambda kv: -kv[1])
    hhi = sum((v / 100) ** 2 for _, v in s)
    growth = round((w['2029'] / (w['2024'] + 1e-9) - 1) * 100)
    out[lab] = {'stage': STAGE[lab], 'top': s[0][0], 'top_share': round(s[0][1], 1), 'hhi': round(hhi, 3),
                'by': {iso: round(v, 1) for iso, v in s[:5]},
                'world_growth_pct': growth, 'world_2024': round(w['2024'], 1), 'world_2029': round(w['2029'], 1)}

json.dump({'source': 'USGS World Minerals Outlook to 2029 (SIR 2025-5021; DOI 10.5066/P1HTTCWN, CC0)',
           'materials': out},
          open(os.path.join(ROOT, 'out', 'usgs_outlook.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('USGS capacity outlook (2024 concentration + world capacity growth to 2029):')
for lab, o in out.items():
    print(f"  {lab:10} [{o['stage']:8}] {o['top']} {o['top_share']:.0f}% of 2024 capacity (HHI {o['hhi']:.2f})"
          f"  ·  world capacity {o['world_growth_pct']:+d}% by 2029")
print('WROTE out/usgs_outlook.json')
