# -*- coding: utf-8 -*-
"""The harmonization layer — map a source's NATIVE product code to a comparable material concept.
This is the piece TDM does not do: national 8-digit lines resolved to one shared vocabulary.
- HS-6 (the internationally comparable level): maps to the material, bundling where HS-6 can't split
  (e.g. 811292 -> 'gallium+germanium').
- 8-10 digit national lines: resolve to the SPECIFIC material where we have a concordance entry
  (e.g. CN8 81129289 -> 'gallium', 81129295 -> 'germanium'), which is exactly what splits the bundle.
Extend by adding (native_code -> material) entries per source scheme; unknown codes fall back to HS-6."""
import os, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_codes = json.load(open(os.path.join(ROOT, 'pipeline', 'critical_codes.json'), encoding='utf8'))['codes']

_by_hs6 = collections.defaultdict(list)
CODE_MATERIAL = {}          # exact native code (>=8 digit) -> specific material
MATERIAL_CONF = {}          # material -> (confidence, form, caveat): honest identity grade of the customs code
for c in _codes:
    _by_hs6[c['hs6']].append(c['material'])
    if len(c['code']) >= 8:
        CODE_MATERIAL[c['code']] = c['material']
    if c.get('confidence'):
        MATERIAL_CONF[c['material']] = (c['confidence'], c.get('form'), c.get('caveat'))
HS6_MATERIAL = {h: '+'.join(sorted(set(ms))) for h, ms in _by_hs6.items()}   # bundle label at HS-6


def confidence_for(material):
    """(confidence, form, caveat) for a material's customs-code identity, or (None,None,None) if ungraded."""
    return MATERIAL_CONF.get(material, (None, None, None))


def material_for(native_code, level):
    """Best-available material for a code: specific if the national line is known, else the HS-6 bundle."""
    if level >= 8 and native_code in CODE_MATERIAL:
        return CODE_MATERIAL[native_code]
    return HS6_MATERIAL.get(native_code[:6])


def hs6_tracked(hs6):
    return hs6 in HS6_MATERIAL


def tracked_hs6_set():
    return set(HS6_MATERIAL)
