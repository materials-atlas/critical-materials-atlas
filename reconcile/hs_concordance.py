# -*- coding: utf-8 -*-
"""One HS edition for every declaration.

Reporters file in whichever Harmonized System edition they use: in the 2019-2026 corpus
HS 2017 (H5) until 2021, HS 2022 (H6) from 2022, with a tail of HS 2012 (H4), HS 2007 (H3) and
HS 2002 (H2) reporters every year. A code means different things across editions (HS 2022
renumbered hundreds of them), so two declarations of one flow in two editions do not match, and
a product's series breaks at 2022. BACI builds each of its datasets in a single edition; so does
this module, with the UN Statistics Division's own correspondence tables
(https://unstats.un.org/unsd/classifications/Econ, files kept in raw/concordance/).

Direction matters. UNSD's CONVERSION tables assign every code of a NEWER edition to exactly one
code of an OLDER one, so going down (HS 2022 -> HS 2012) is a merge and loses nothing but detail.
Going up has no unique answer: an old code split in the new edition can only be allocated. The
target is therefore HS 2012 for the modern window: HS 2022 and HS 2017 declarations convert
uniquely; the few HS 2007 and HS 2002 reporters go up through the CORRELATION tables, 1:1 and
n:1 relationships uniquely, 1:n and n:n split equally over the candidates (and counted, so the
share of value that was split is known). The long history (2000-2011) will take HS 1992, the
edition every later one converts down to, when the yearly series is in.

    from hs_concordance import mapping_table
    m = mapping_table('H4')      # columns ver, code_from, code_to, share   (identity rows omitted)
"""
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIR = os.path.join(ROOT, 'raw', 'concordance')
YEAR = {'H0': 1992, 'H1': 1996, 'H2': 2002, 'H3': 2007, 'H4': 2012, 'H5': 2017, 'H6': 2022}
FILES = {(2022, 2017): 'HS2022toHS2017.xlsx', (2022, 2012): 'HS2022toHS2012.xlsx',
         (2022, 1992): 'HS2022toHS1992.xlsx', (2017, 2012): 'HS2017toHS2012.xlsx',
         (2017, 1992): 'HS2017toHS1992.xlsx', (2017, 2007): 'HS2017toHS2007.xlsx',
         (2017, 2002): 'HS2017toHS2002.xlsx', (2017, 1996): 'HS2017toHS1996.xlsx', (2012, 2007): 'HS2012toHS2007.xls',
         (2012, 2002): 'HS2012toHS2002.xls', (2012, 1996): 'HS2012toHS1996.xls',
         (2012, 1992): 'HS2012toHS1992.xls'}
_CODE = re.compile(r'^\d{5,6}$')


def _pad(x):
    s = str(x).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s.zfill(6) if _CODE.match(s) else None


def _sheet(path, kind):
    x = pd.ExcelFile(path)
    names = [s for s in x.sheet_names if kind in s.lower()]
    if not names:
        raise KeyError('%s has no %s sheet: %s' % (path, kind, x.sheet_names))
    return x.parse(names[0], header=None, dtype=str)


def conversion(new, old):
    """newer code -> the one older code UNSD assigns it (dict)."""
    df = _sheet(os.path.join(DIR, FILES[(new, old)]), 'conversion')
    out = {}
    for _, row in df.iterrows():
        codes = [_pad(v) for v in row.tolist()]
        codes = [c for c in codes if c]
        if len(codes) >= 2:
            out.setdefault(codes[0], codes[1])
    return out


def correlation(new, old):
    """every (newer code, older code) relationship UNSD lists, as a DataFrame new, old, rel."""
    df = _sheet(os.path.join(DIR, FILES[(new, old)]), 'correlation')
    hdr = None
    for i, row in df.iterrows():
        if any(str(v).strip().lower() == 'relationship' for v in row.tolist()):
            hdr = i
            break
    rel_col = None
    if hdr is not None:
        rel_col = [j for j, v in enumerate(df.iloc[hdr].tolist()) if str(v).strip().lower() == 'relationship'][0]
    rows = []
    for _, row in df.iloc[(hdr + 1) if hdr is not None else 0:].iterrows():
        vals = row.tolist()
        codes = [(j, _pad(v)) for j, v in enumerate(vals)]
        codes = [(j, c) for j, c in codes if c and (rel_col is None or j < rel_col)]
        if len(codes) >= 2:
            rows.append((codes[0][1], codes[1][1], str(vals[rel_col]).strip() if rel_col is not None else ''))
    return pd.DataFrame(rows, columns=['new', 'old', 'rel'])


def mapping_table(target='H4'):
    """Rows (ver, code_from, code_to, share) for every edition other than the target that the
    tables cover. Newer editions convert uniquely (share 1); older ones go up through the
    correlation table, splitting equally where UNSD lists several candidates."""
    ty = YEAR[target]
    rows = []
    for ver, y in YEAR.items():
        if y == ty:
            continue
        if y > ty:
            if (y, ty) not in FILES or not os.path.exists(os.path.join(DIR, FILES[(y, ty)])):
                continue
            for a, b in conversion(y, ty).items():
                rows.append((ver, a, b, 1.0, 'down'))
        else:
            if (ty, y) not in FILES or not os.path.exists(os.path.join(DIR, FILES[(ty, y)])):
                continue
            c = correlation(ty, y)
            for old, g in c.groupby('old'):
                news = sorted(set(g.new))
                for n in news:
                    rows.append((ver, old, n, 1.0 / len(news), 'up-unique' if len(news) == 1 else 'up-split'))
    return pd.DataFrame(rows, columns=['ver', 'code_from', 'code_to', 'share', 'how'])


if __name__ == '__main__':
    m = mapping_table('H4')
    print(m.groupby(['ver', 'how']).agg(codes=('code_from', 'nunique'), rows=('code_to', 'size')).to_string())
    changed = m[(m.how == 'down') & (m.code_from != m.code_to)]
    print('codes that change number on the way down:', changed.groupby('ver').code_from.nunique().to_dict())
