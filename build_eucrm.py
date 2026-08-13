"""EU Critical Raw Materials 2023 study (European Commission, DOI 10.2873/725585) -- authoritative top
global supplier of each CRM at its bottleneck stage (E = extraction, P = processing), from Table A of the
Final Report. This is the one public, official source that gives a per-country PROCESSING-stage figure for
the specialty metals BGS/USGS/IEA leave as narrative (tungsten P China 86%, gallium P China 94%, germanium
P China 83%, platinum P S.Africa 71%, silicon P China 76%, niobium P Brazil 92%). Parses the committed
report PDF; writes out/eucrm.json {atlas_label: {stage, iso, name, pct}} for use as a card cross-check.

Run:  python build_eucrm.py
"""
import os, re, json
import pdfplumber
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, 'raw', 'eucrm', 'crm2023_final.pdf')

# EU CRM material name -> atlas label (data.json). REE handled via the binding input where sensible.
NAME2LAB = {'aluminium': 'bauxite', 'antimony': 'antimony', 'arsenic': 'arsenic', 'baryte': 'baryte',
            'beryllium': 'beryllium', 'boron': 'boron', 'cobalt': 'cobalt', 'coking coal': 'cokingcoal',
            'copper': 'copper', 'feldspar': 'feldspar', 'fluorspar': 'fluorspar', 'gallium': 'gallium',
            'germanium': 'germanium', 'hafnium': 'hafnium', 'helium': 'helium', 'lithium': 'lithium',
            'magnesium': 'magnesium', 'manganese': 'manganese', 'natural graphite': 'graphite',
            'neodymium': 'magnets', 'niobium': 'niobium', 'nickel': 'nickel', 'palladium': 'palladium',
            'phosphate rock': 'phosphate', 'phosphorus': 'phosphorus', 'platinum': 'platinum',
            'silicon metal': 'silicon', 'strontium': 'strontium', 'tantalum': 'tantalum',
            'titanium metal': 'titanium', 'tungsten': 'tungsten', 'vanadium': 'vanadium'}
COUNTRY2ISO = {'Australia': 'AU', 'China': 'CN', 'S. Africa': 'ZA', 'South Africa': 'ZA', 'DRC': 'CD',
               'Chile': 'CL', 'Türkiye': 'TR', 'Turkiye': 'TR', 'USA': 'US', 'Brazil': 'BR',
               'Russia': 'RU', 'France': 'FR', 'Spain': 'ES', 'Morocco': 'MA'}

with pdfplumber.open(PDF) as pdf:
    text = pdf.pages[8].extract_text() or ''

# each row holds two entries: "N material [E|P] Country NN%"  x2
ENTRY = re.compile(r'\d+\s+([A-Za-zÿü.\' ]+?)\s+([EP])\s+([A-Za-zÿü.\' ]+?)\s+(\d+)%')
out, report = {}, []
for name, stage, country, pct in ENTRY.findall(text):
    name = name.strip().lower(); country = country.strip()
    lab = NAME2LAB.get(name)
    if not lab:
        continue
    iso = COUNTRY2ISO.get(country)
    out[lab] = {'stage': 'processing' if stage == 'P' else 'extraction', 'stage_code': stage,
                'iso': iso, 'name': country, 'pct': int(pct)}
    report.append(f"  {lab:11} {out[lab]['stage']:10} {country:12} {pct}%")

json.dump({'source': 'EU CRM 2023 Final Report (EC, DOI 10.2873/725585), Table A: major global supplier',
           'materials': out},
          open(os.path.join(ROOT, 'out', 'eucrm.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print(f'parsed EU CRM 2023 top suppliers: {len(out)} atlas materials')
print('\n'.join(sorted(report)))
n_proc = sum(1 for v in out.values() if v['stage_code'] == 'P')
n_cn = sum(1 for v in out.values() if v['iso'] == 'CN')
print(f'\n{n_proc}/{len(out)} bottleneck at PROCESSING; China is top supplier of {n_cn}. WROTE out/eucrm.json')
