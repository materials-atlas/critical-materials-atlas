#!/usr/bin/env python3
"""Capex + time-to-build for the flagship diversification projects (breakout-page deepening).

The 'who is building it' layer named projects but not their SCALE or TIMELINE — so a reader could not
tell a $3bn, 2029 mine from a pilot. This adds capex, first-production year and target capacity for the
projects with reliable public figures, cross-checked against company / agency announcements (2025-26).
Kept deliberately small and sourced; a blank stays a blank (the page reads it as 'not tracked', not 'no
one'). Keyed by a distinctive substring of the project name so the breakout page can look each one up.

Run: python build_pipeline_specs.py  ->  out/pipeline_specs.json
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))

SPECS = {
    # key (substring of project name) : capex, first production, target capacity, source
    'Perpetua':     {'capex': '~$2.2bn', 'online': '2028', 'capacity': '~35% of US antimony demand (6 yrs)',
                     'src': 'Perpetua / US EXIM 2025'},
    'Sangdong':     {'capex': '~$0.1bn', 'online': '2025–26 (Ph.1)', 'capacity': '~2,300 t/yr WO₃ → ~40% ex-China',
                     'src': 'Almonty 2025'},
    'Seadrift':     {'capex': '~$0.3bn (DoD-backed)', 'online': '2026', 'capacity': '~2,500–3,000 t/yr heavy REO',
                     'src': 'Lynas / US DoD 2025'},
    'MP Materials': {'capex': '~$1.25bn (“10X”)', 'online': '2028 (10X); Independence live', 'capacity': '~10,000 t/yr magnets',
                     'src': 'MP Materials 2026'},
    'Thacker Pass': {'capex': '~$2.9bn (Ph.1)', 'online': '2027', 'capacity': 'Ph.1 lithium carbonate',
                     'src': 'Lithium Americas 2026'},
    'Nolans':       {'capex': '~US$1bn', 'online': '2029', 'capacity': '~4,440 t/yr NdPr (~4% of world)',
                     'src': 'Arafura FID 2026'},
}

out = {'note': ('Capex, first-production year and target capacity for flagship diversification projects, '
                'from public company / agency announcements 2025-26. Curated, not exhaustive; a project '
                'without a reliable public figure carries no specs (shown blank, not "unknown"). Keyed by '
                'a substring of the project name.'),
       'specs': SPECS}
json.dump(out, open(os.path.join(ROOT, 'out', 'pipeline_specs.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f'wrote out/pipeline_specs.json — {len(SPECS)} flagship projects with capex/timeline')
