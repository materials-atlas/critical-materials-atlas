"""Diversification pipeline overlay (2025 -> ~2035): the forward, project-level view of who is building
mining / refining / magnet capacity OUTSIDE the dominant producer. The IEA quantifies this in aggregate
(refining and downstream capacity lag mining) but its granular project list is sourced from paid databases
and not public -- so this is a CURATED set of publicly announced projects (company releases, EU CRMA
Strategic Projects list, national funding announcements), clearly REPRESENTATIVE, not exhaustive. Each
material carries the IEA structural finding as context. Writes out/pipeline.json.  Run: python build_pipeline.py

Sources: company announcements & SEC filings; EU CRMA Strategic Projects (2025); IEA Global Critical
Minerals Outlook (aggregate concentration & supply-gap figures, publicly released).
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
    'germanium': {
        'iea': None,
        'projects': [
            {'name': 'Umicore — Ge recovery & recycling', 'iso': 'BE', 'stage': 'refine',
             'status': 'EU CRMA Strategic Projects (2025)'},
        ]},
    'graphite': {
        'iea': ("IEA: African feedstock (Madagascar, Mozambique, Tanzania) is being paired with anode-"
                "material plants in Europe, the US, Japan and Korea, but midstream still lags China."),
        'projects': [
            {'name': 'Anode-material plants (EU / US / JP / KR)', 'iso': '', 'stage': 'refine',
             'status': 'various, mostly pre-2030'},
        ]},
}
NOTE = ('Representative publicly announced projects (company releases, EU CRMA Strategic Projects, national '
        'funding), not an exhaustive list. The IEA quantifies the pipeline in aggregate; its project-level '
        'data is sourced from paid databases and not public.')

json.dump({'note': NOTE, 'materials': PIPE},
          open(os.path.join(ROOT, 'out', 'pipeline.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
n = sum(len(v['projects']) for v in PIPE.values())
print(f'diversification pipeline: {len(PIPE)} materials, {n} projects. WROTE out/pipeline.json')
for lab, v in PIPE.items():
    print(f"  {lab:10} {', '.join(p['name'].split(chr(8212))[0].strip() for p in v['projects'])}")
