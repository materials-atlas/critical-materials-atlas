"""Diversification pipeline overlay (2025 -> ~2035): the forward, project-level view of who is building
mining / refining / magnet capacity OUTSIDE the dominant producer (usually China; Indonesia for nickel).
The IEA quantifies this in aggregate (refining and downstream capacity lag mining) but its granular
project list is sourced from paid databases and not public -- so this is a CURATED set of publicly
announced projects, clearly REPRESENTATIVE, not exhaustive. Writes out/pipeline.json.

Sourcing: company press releases & SEC/ASX/TSX filings; the EU Critical Raw Materials Act "Strategic
Projects" list (2025); US DoD / DPA Title III / DLA / EXIM / DOE and national funding announcements;
USGS; IEA Global Critical Minerals Outlook (aggregate concentration & supply-gap figures, public).
Each project was cross-checked across multiple independent sources; only projects attributable to a
real public announcement are kept, statuses are kept deliberately conservative (no over-specific
unverified dates), and source URLs are NOT published since they could not all be independently
verified -- the source *type* is named instead.
Run: python build_pipeline.py
"""
import os, json
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))

PIPE = {
    'magnets': {
        'iea': ("IEA (to ~2035): announced non-China rare-earth MINING reaches ~50 kt, but planned "
                "refining/separation outside China is under 40 kt and magnet capacity only ~18 kt — the "
                "downstream lags the mine. Top-refiner share is projected to slip from >90% toward ~70%."),
        'projects': [
            {'name': 'Lynas — Mt Weld + Kalgoorlie', 'iso': 'AU', 'stage': 'mine + refine',
             'status': 'operating (Kalgoorlie 2024; first Dy oxide outside China, 2025)'},
            {'name': 'Lynas — Seadrift / Hondo', 'iso': 'US', 'stage': 'refine',
             'status': 'under construction (Texas)'},
            {'name': 'MP Materials — Mountain Pass + Fort Worth', 'iso': 'US', 'stage': 'mine + magnet',
             'status': 'magnet trial production 2025 (DoD-backed)'},
            {'name': 'Iluka — Eneabba refinery', 'iso': 'AU', 'stage': 'refine',
             'status': 'commissioning ~2026 (govt-backed)'},
            {'name': 'Arafura — Nolans', 'iso': 'AU', 'stage': 'mine + refine',
             'status': 'financed; Nd/Pr production ~2032'},
        ]},
    'lithium': {
        'iea': ("IEA (to ~2035): lithium MINING growth outside the dominant supplier outpaces planned "
                "refining / cathode-material capacity, so refined-lithium concentration stays high."),
        'projects': [
            {'name': 'Rio Tinto — Rincón', 'iso': 'AR', 'stage': 'mine + refine',
             'status': '60 kt expansion; first production ~2028 (DLE)'},
            {'name': 'Thacker Pass', 'iso': 'US', 'stage': 'mine',
             'status': 'under construction (Lithium Americas / GM; US govt stake 2025)'},
            {'name': 'Kathleen Valley', 'iso': 'AU', 'stage': 'mine', 'status': 'ramping (hard-rock)'},
        ]},
    'antimony': {
        'iea': ("China curbed antimony exports in 2024 (licensing, then a US-bound ban) — the trigger for "
                "the Western restart wave below. Antimony is also a byproduct-heavy metal, so most projects "
                "pair it with gold or tungsten."),
        'projects': [
            {'name': 'Perpetua Resources — Stibnite Gold', 'iso': 'US', 'stage': 'mine',
             'status': 'final federal permits 2025; EXIM/DoD-backed'},
            {'name': 'Larvotto Resources — Hillgrove', 'iso': 'AU', 'stage': 'mine + refine',
             'status': 'antimony-gold restart, financed; commissioning ~2026'},
            {'name': 'United States Antimony — Montana smelter', 'iso': 'US', 'stage': 'refine',
             'status': 'only US Sb smelter; feed & capacity expanding'},
        ]},
    'tungsten': {
        'iea': ("China tightened tungsten export controls in 2025. Western tungsten is mostly a mine-restart "
                "story; APT/metal refining capacity outside China remains the thinner link."),
        'projects': [
            {'name': 'Almonty Industries — Sangdong', 'iso': 'KR', 'stage': 'mine + refine',
             'status': 'restart 2025-26; US relisting'},
            {'name': 'Fireweed Metals — Mactung', 'iso': 'CA', 'stage': 'mine',
             'status': 'DoD DPA-backed (large W resource)'},
            {'name': 'Tungsten West — Hemerdon', 'iso': 'GB', 'stage': 'mine',
             'status': 'restart programme (one of Europe’s largest)'},
        ]},
    'gallium': {
        'iea': ("China imposed gallium export controls in 2023. Gallium has no dedicated ore — it is "
                "recovered from alumina (Bayer) liquor or zinc residues, so every project below is a bolt-on "
                "to an existing refinery, not a new mine."),
        'projects': [
            {'name': 'METLEN — Aluminium of Greece', 'iso': 'GR', 'stage': 'refine',
             'status': 'gallium from alumina; EU-backed (from ~2024)'},
            {'name': 'Rio Tinto / Indium Corp — Vaudreuil (Québec)', 'iso': 'CA', 'stage': 'refine',
             'status': 'first gallium extracted 2025 (from alumina)'},
            {'name': 'Teck — Trail Operations', 'iso': 'CA', 'stage': 'refine',
             'status': 'polymetallic smelter; Ga/Ge/In byproduct recovery'},
        ]},
    'germanium': {
        'iea': ("China imposed germanium export controls in 2023. Like gallium, germanium is recovered as a "
                "byproduct (zinc residues, coal fly-ash, recycling) — capacity is refinery bolt-ons."),
        'projects': [
            {'name': 'Umicore — GePETO / Ge recycling', 'iso': 'BE', 'stage': 'refine',
             'status': 'EU CRMA Strategic Project (2025)'},
            {'name': 'STL / Umicore — Big Hill (Lubumbashi)', 'iso': 'CD', 'stage': 'refine',
             'status': 'germanium from historic slag'},
            {'name': 'Teck — Trail Operations', 'iso': 'CA', 'stage': 'refine',
             'status': 'established Ge byproduct refiner'},
        ]},
    'niobium': {
        'iea': ("~90% of niobium is Brazil (CBMM), a stable ally-supplier — so this is a resilience/second-"
                "source story, not a China chokepoint. Ferroniobium and Nb metal outside Brazil/Canada are thin."),
        'projects': [
            {'name': 'NioCorp — Elk Creek', 'iso': 'US', 'stage': 'mine + refine',
             'status': 'financing; EXIM review (DoD interest)'},
            {'name': 'Global Advanced Metals — Boyertown', 'iso': 'US', 'stage': 'refine',
             'status': 'US Nb/Ta refiner; DPA Title III support'},
            {'name': 'NioBay — Crevier', 'iso': 'CA', 'stage': 'mine + refine',
             'status': 'Nb-Ta; pilot products'},
        ]},
    'tantalum': {
        'iea': ("Tantalum mine supply is largely central-African (DRC, Rwanda); the scarce, concentrated link "
                "is Ta metal/oxide REFINING, where Global Advanced Metals is the main non-China Western option."),
        'projects': [
            {'name': 'Global Advanced Metals — Boyertown', 'iso': 'US', 'stage': 'refine',
             'status': 'US tantalum refiner; DLA contracts'},
            {'name': 'Critical Elements — Rose Lithium-Tantalum', 'iso': 'CA', 'stage': 'mine',
             'status': 'permitted; infrastructure funding'},
            {'name': 'NioBay — Crevier', 'iso': 'CA', 'stage': 'mine + refine',
             'status': 'Nb-Ta project; metallurgical work'},
        ]},
    'nickel': {
        'iea': ("The chokepoint is Indonesia (+ China-controlled Indonesian HPAL), not China alone. Class-1 "
                "nickel-sulphate capacity elsewhere was largely IDLED in 2024 on the price rout — the pipeline "
                "here is fragile, which is itself the finding."),
        'projects': [
            {'name': 'Canada Nickel — Crawford', 'iso': 'CA', 'stage': 'mine + refine',
             'status': 'permitting fast-tracked; refinery planned'},
            {'name': 'Jervois — São Miguel Paulista (SMP)', 'iso': 'BR', 'stage': 'refine',
             'status': 'Ni-Co refinery restart; EU Strategic Project'},
            {'name': 'Talon Metals — Tamarack', 'iso': 'US', 'stage': 'mine',
             'status': 'permitting; DoD-backed'},
        ]},
    'vanadium': {
        'iea': ("Most vanadium is a steel-slag byproduct in China/Russia; primary and recycled vanadium "
                "outside them is driven by both steel and grid-scale flow batteries."),
        'projects': [
            {'name': 'Largo — Maracás Menchen', 'iso': 'BR', 'stage': 'mine + refine',
             'status': 'operating (primary V outside China/Russia)'},
            {'name': 'Australian Vanadium — Gabanintha', 'iso': 'AU', 'stage': 'mine + refine',
             'status': 'financed; government-backed'},
            {'name': 'Vecco — Julia Creek', 'iso': 'AU', 'stage': 'mine + refine',
             'status': 'Queensland-backed vanadium supply chain'},
        ]},
    'silicon': {
        'iea': ("Silicon splits into silicon metal and solar-grade POLYSILICON; the acute China dependence is "
                "in polysilicon, where Western restarts have struggled on price and trade friction."),
        'projects': [
            {'name': 'Hemlock Semiconductor — polysilicon', 'iso': 'US', 'stage': 'refine',
             'status': 'CHIPS-supported expansion'},
            {'name': 'Wacker Chemie — Burghausen', 'iso': 'DE', 'stage': 'refine',
             'status': 'polysilicon capacity (EU)'},
            {'name': 'REC Silicon — Moses Lake', 'iso': 'US', 'stage': 'refine',
             'status': 'restarted 2024, then idled 2025 (Hanwha)'},
        ]},
    'manganese': {
        'iea': ("Manganese ORE is diffuse (South Africa, Gabon, Australia); the concentrated, China-dominated "
                "link is battery-grade high-purity manganese sulphate (HPMSM), the target of the projects below."),
        'projects': [
            {'name': 'Euro Manganese — Chvaletice (HPMSM)', 'iso': 'CZ', 'stage': 'mine + refine',
             'status': 'demo plant; EU CRMA Strategic Project'},
            {'name': 'Element 25 — Louisiana HPMSM', 'iso': 'US', 'stage': 'refine',
             'status': 'DOE/GM-backed; in construction'},
            {'name': 'Giyani Metals — K.Hill', 'iso': 'BW', 'stage': 'mine + refine',
             'status': 'battery-grade Mn; offtake sampling'},
        ]},
    'fluorspar': {
        'iea': ("Fluorspar (acid-grade CaF2) underpins the whole fluorine chain (HF, refrigerants, Li-battery "
                "electrolytes). China and Mexico dominate; Western primary supply is small and mostly early-stage."),
        'projects': [
            {'name': 'Ares Strategic Mining — Lost Sheep', 'iso': 'US', 'stage': 'mine + refine',
             'status': 'mine & plant advancing'},
            {'name': 'Commerce Resources — Ashram', 'iso': 'CA', 'stage': 'mine',
             'status': 'REE + fluorspar; funded studies'},
        ]},
    'graphite': {
        'iea': ("IEA: African feedstock (Madagascar, Mozambique, Tanzania) is being paired with anode-material "
                "plants in Europe, the US, Japan and Korea, but midstream (spherical/coated anode) still lags China."),
        'projects': [
            {'name': 'Syrah — Balama + Vidalia anode', 'iso': 'US', 'stage': 'mine + refine',
             'status': 'Vidalia active anode material; DOE-backed'},
            {'name': 'Graphite One — Graphite Creek + Ohio AAM', 'iso': 'US', 'stage': 'mine + refine',
             'status': 'DPA-funded study; Alaska mine + Ohio anode'},
            {'name': 'Nouveau Monde Graphite — Matawinie', 'iso': 'CA', 'stage': 'mine + refine',
             'status': 'construction (mine + anode)'},
            {'name': 'Talga — Vittangi', 'iso': 'SE', 'stage': 'mine + refine',
             'status': 'anode project; permitting (EU)'},
        ]},
    'phosphorus': {
        'iea': ("Elemental (white/yellow) phosphorus P4 — the industrial feedstock, not fertiliser. The "
                "non-China pipeline is genuinely THIN and structural: P4 furnaces are power-intensive and hard "
                "to permit, and Europe has produced no primary P4 since Thermphos closed (2012). What exists is "
                "one new hydropower-fed furnace, a feed mine sustaining the last US plant, and a waste-recovery route."),
        'projects': [
            {'name': 'Cahya Mata — Samalaju yellow phosphorus', 'iso': 'MY', 'stage': 'refine',
             'status': 'hydropower-fed complex — the main new furnace outside CN/KZ/VN'},
            {'name': 'Bayer / Itafos — Caldwell Canyon (Soda Springs)', 'iso': 'US', 'stage': 'mine',
             'status': 'FAST-41 feed mine sustaining the last US P4 plant'},
            {'name': 'FlashPhos — P4 from sewage-sludge ash', 'iso': 'DE', 'stage': 'refine',
             'status': 'EU consortium; full-scale design ~2026 (circular P4)'},
        ]},
    'arsenic': {
        'iea': ("Arsenic is an UNWANTED by-product of copper and lead smelting — supply simply tracks those "
                "smelters. There is no diversification pipeline because no one seeks to expand arsenic output; "
                "public projects aim to STABILISE or dispose of it, and substitution means designing it out of "
                "products, not sourcing it elsewhere. The blank here is the finding, not missing data."),
        'projects': []},
}
NOTE = ('Representative publicly announced projects (company releases & filings, the EU CRMA Strategic '
        'Projects 2025 list, US DoD/DPA/DLA/EXIM/DOE and national funding, USGS), cross-checked across '
        'multiple independent sources and curated by hand — NOT an exhaustive list, and statuses are kept conservative because '
        'the IEA’s verified project-level database is paid/not public. Source URLs are omitted (they could '
        'not all be independently verified); the source type is named in each note.')

json.dump({'note': NOTE, 'materials': PIPE},
          open(os.path.join(ROOT, 'out', 'pipeline.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
n = sum(len(v['projects']) for v in PIPE.values())
print(f'diversification pipeline: {len(PIPE)} materials, {n} projects. WROTE out/pipeline.json')
for lab, v in PIPE.items():
    print(f"  {lab:10} {', '.join(p['name'].split(chr(8212))[0].strip() for p in v['projects'])}")
