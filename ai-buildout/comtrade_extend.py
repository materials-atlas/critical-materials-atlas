# -*- coding: utf-8 -*-
"""World trade after 2024, as reported by importers to UN Comtrade: a fixed panel, 2024 against 2025
and January-June 2025 against January-June 2026.

Reads ai-buildout/comtrade/*.parquet (fetch_comtrade_ai.py; raw, gitignored, never redistributed) and
writes only derived totals and shares:
  out/ai_buildout_comtrade.json   - every line on the AI build-out page
  out/buildout_comtrade.json      - buildout-study Amendment D (filed before the pull)

A FIXED PANEL. An importer enters a comparison only if it reported in every month of both periods, so
a country that has not filed yet cannot look like a fall in trade. Each panel's size is stated as its
share of the same line's 2024 world imports in CEPII BACI (the atlas's reconciled world record).
Partner code 0 (World) is a total of the partner rows and is excluded. Values are as the importer
declared them (mostly CIF), so they are not compared with BACI's FOB levels, only with themselves.

Usage:  python ai-buildout/comtrade_extend.py
"""
import glob
import json
import os
import sys

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import baci                                                   # the one door for BACI

OUT_AI = os.path.join(ROOT, 'out', 'ai_buildout_comtrade.json')
OUT_NOTE = os.path.join(ROOT, 'out', 'buildout_comtrade.json')
LINE_OF = {'854141': '85414', '854142': '85414', '854143': '85414', '854149': '85414'}
TRANSFORMERS = ['850421', '850422', '850423']
GOES = ['722511', '722611']
HEAVY = ['842810', '842649', '847420', '847431', '851531', '851539']
MOTORS = ['850152', '850153', '841370', '841480']
Y24 = ['2024%02d' % m for m in range(1, 13)]
Y25 = ['2025%02d' % m for m in range(1, 13)]
H25 = ['2025%02d' % m for m in range(1, 7)]
H26 = ['2026%02d' % m for m in range(1, 7)]
# Comtrade partner codes that are not a country.
NOT_COUNTRY = {0, 97, 290, 492, 527, 568, 577, 636, 637, 838, 839, 849, 879, 899}


def load():
    files = sorted(glob.glob(os.path.join(HERE, 'comtrade', 'c_*.parquet')))
    con = duckdb.connect()
    d = con.execute("""select reporterCode as rep, partnerCode as par, cmdCode as code, period,
                              primaryValue as v, netWgt as kg
                       from read_parquet(?, union_by_name=true)
                       where flowCode = 'M' and partnerCode <> 0""", [files]).df()
    d['line'] = [LINE_OF.get(c, c) for c in d.code]
    return d


def panel(d, months):
    """Reporters that filed in every one of these months (for any line in the pull)."""
    seen = d[d.period.isin(months)].groupby('rep').period.nunique()
    return set(seen[seen == len(months)].index)


def names():
    c = baci.countries()
    n = c.set_index('code')['name'].to_dict()
    n = {int(k): v for k, v in n.items()}
    n.update({490: 'Taiwan', 842: 'the United States', 410: 'South Korea', 344: 'Hong Kong',
              251: 'France', 757: 'Switzerland', 699: 'India', 579: 'Norway', 156: 'China'})
    return n


def coverage(reps, lines):
    """The panel importers' share of 2024 world imports of these lines, in BACI."""
    t = baci.year(2024)
    t['k'] = t.k.astype(str).str.zfill(6)
    keep = [l for l in lines]
    t = t[t.k.str.startswith(tuple(keep))]
    tot = t.v.sum()
    return round(float(t[t.j.astype(int).isin(reps)].v.sum() / tot), 4) if tot > 0 else None


def compare(d, lines, a_months, b_months, nm):
    reps = panel(d, a_months) & panel(d, b_months)
    q = d[d.rep.isin(reps) & d.line.isin(lines)]
    A, B = q[q.period.isin(a_months)], q[q.period.isin(b_months)]
    va, vb = A.v.sum(), B.v.sum()
    ka, kb = A.kg.sum(), B.kg.sum()

    def shares(x):
        s = x[~x.par.isin(NOT_COUNTRY)].groupby('par').v.sum()
        tot = x.v.sum()
        top = (s / tot).sort_values(ascending=False).head(3)
        return {'china': round(float(s.get(156, 0.0) / tot), 4) if tot else None,
                'russia': round(float(s.get(643, 0.0) / tot), 4) if tot else None,
                'japan': round(float(s.get(392, 0.0) / tot), 4) if tot else None,
                'top3': [[nm.get(int(p), str(p)), round(float(v), 4)] for p, v in top.items()],
                'top3_share': round(float(top.sum()), 4)}
    return {'importers': len(reps), 'coverage_of_2024_world_imports': coverage(reps, lines),
            'value_a_musd': round(va / 1e6, 1), 'value_b_musd': round(vb / 1e6, 1),
            'value_change_pct': round(100 * (vb / va - 1), 3) if va > 0 else None,
            'value_per_kg_change_pct': (round(100 * ((vb / kb) / (va / ka) - 1), 3)
                                        if va > 0 and ka > 0 and kb > 0 else None),
            'suppliers_a': shares(A), 'suppliers_b': shares(B)}


def main():
    d = load()
    nm = names()
    lines = sorted(set(d.line))
    ai = {'note': 'UN Comtrade monthly imports as reported by importers; a fixed panel of importers that '
                  'filed every month of both periods; coverage = the panel\'s share of the line\'s 2024 '
                  'world imports in CEPII BACI. Derived totals and shares only.',
          'last_month': d.period.max(),
          'year_2025_vs_2024': {l: compare(d, [l], Y24, Y25, nm) for l in lines},
          'h1_2026_vs_h1_2025': {l: compare(d, [l], H25, H26, nm) for l in lines}}
    with open(OUT_AI, 'w', encoding='utf-8') as f:
        json.dump(ai, f, indent=1, default=float)
    note = {'filing': 'buildout-study/AMENDMENT_COMTRADE_2026.md', 'last_month': d.period.max(),
            'goes': {'2025_vs_2024': compare(d, GOES, Y24, Y25, nm),
                     'h1_2026_vs_h1_2025': compare(d, GOES, H25, H26, nm)},
            'groups_2025_vs_2024': {'transformers': compare(d, TRANSFORMERS, Y24, Y25, nm),
                                    'heavy_machinery': compare(d, HEAVY, Y24, Y25, nm),
                                    'motors_pumps_compressors': compare(d, MOTORS, Y24, Y25, nm)}}
    g = note['goes']['2025_vs_2024']
    note['question_1_reading'] = ('the concentration continued into 2025, as reported by importers'
                                  if g['suppliers_b']['china'] > g['suppliers_a']['china']
                                  else 'the concentration did not continue into 2025, as reported by importers')
    with open(OUT_NOTE, 'w', encoding='utf-8') as f:
        json.dump(note, f, indent=1, default=float)
    print('last month', d.period.max(), '| reporters', d.rep.nunique())
    for k, v in note['groups_2025_vs_2024'].items():
        print('%-26s value %+.1f%%  per kg %s  importers %d  coverage %s'
              % (k, v['value_change_pct'], v['value_per_kg_change_pct'], v['importers'], v['coverage_of_2024_world_imports']))
    for k, v in note['goes'].items():
        print('GOES', k, 'China', v['suppliers_a']['china'], '->', v['suppliers_b']['china'],
              'top3', v['suppliers_a']['top3_share'], '->', v['suppliers_b']['top3_share'], v['suppliers_b']['top3'],
              'coverage', v['coverage_of_2024_world_imports'])
    print(note['question_1_reading'])


if __name__ == '__main__':
    main()
