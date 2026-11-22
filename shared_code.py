"""Materials whose world trade is one shared customs code, not a series of their own.

The world trade file is CEPII BACI in the HS 2017 nomenclature. Its product table has no line for
hafnium alone. Code 811292 reads "Gallium, germanium, hafnium, indium, niobium (columbium), rhenium
and vanadium: articles thereof, unwrought, including waste and scrap, powders", and
build_flows_fix.py therefore gives gallium, germanium and hafnium the SAME flows.

Until November 2026 the builders each kept their own typed list of two names and a note saying
"hafnium is separate", and the pages printed the basket's figures as hafnium's own (same top
seller, same top buyer, same concentration as gallium and germanium, with no mark). Hafnium has a
series of its own in two places: the EU view (CN 8112 31 00) and the atlas's own reconciliation
(out/cube.parquet, HS6 811231, from 2022). The pages built on the world trade file use neither yet.

So: ONE list, read from out/crosswalk.json (the flag `shared_refined`, set in build_crosswalk.py),
and ONE sentence for the page notes. A builder that needs either imports this module.
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

SHARED = {k for k, v in json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf8')).items()
          if 'shared_refined' in v.get('flags', [])}

# The sentence names the materials, so it must fail loudly the day the list changes.
if SHARED != {'gallium', 'germanium', 'hafnium'}:
    raise SystemExit('shared_code: the shared-code list is now %s; rewrite NOTE and the pages that name '
                     'the three materials before building' % sorted(SHARED))

CODE = '811292'
NOTE = ('⛓ Gallium, germanium and hafnium are read from one customs code in the world trade file '
        '(HS 811292, which also holds unwrought indium, niobium, rhenium and vanadium). Their trade '
        'figures are the same basket, not three results.')
MARK = ' <span title="trade read from a customs code shared by gallium, germanium and hafnium (HS 811292)" style="color:#b07a18">⛓</span>'
