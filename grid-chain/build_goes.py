# -*- coding: utf-8 -*-
"""Is the transformer's core input diffuse, or is it the tightest node in the grid chain?

WHY THIS EXISTS
The grid chain published a contradiction. Hop 1 listed grain-oriented electrical steel beside
copper and aluminium as "abundant, diversified"; a panel two paragraphs below called it one of
"the real scarcities", made by "a small number of mills". Both cannot be true, and neither was
measured - the chain's own BACI extractor names the GOES codes and its output never contained
them. So the label was written, and the evidence for it was not.

Prompted by a reader flagging Amoah, Brown, Simon, Bazilian & Matisek, "Mineral demand from AI
data centers", Resources Policy 119 (2026) 105970, which reportedly calls GOES a particularly
constrained enabling material. The reference is verified via Crossref; the text is paywalled and
we have NOT read it, so it is recorded as what prompted the check, never as evidence for the
result. The result below is ours.

WHAT IS MEASURED, AND WHAT IS NOT
HS 722511 (grain-oriented, >=600mm) and 722611 (<600mm) are clean codes. Every group here is
measured identically - same source, same years, same basis - because the question is comparative:
does GOES belong in the same bucket as copper and aluminium?

Trade is not capacity. Export shares say who SELLS, not who can MAKE: a producer that consumes
its own output at home is understated, and China is exactly that. Some listed exporters are
distribution hubs re-selling other mills' steel. So the concentration computed here is a FLOOR on
the real thing, and the direction of the error is known.

Run:  python build_goes.py
"""
import csv, io, os, json, zipfile, collections, datetime
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))); import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]
WINDOW = [2022, 2023, 2024]

GROUPS = {
    'goes': ('Grain-oriented electrical steel', {'722511', '722611'},
             'GOES sheet and strip, both width classes. Broader than transformer-core end use.'),
    'aluminium_conductor': ('Bare aluminium stranded conductor', {'761410', '761490'},
                            'Non-insulated stranded wire, with or without steel core.'),
    'copper_wire': ('Copper wire over 6mm', {'740811'}, 'The grid conductor basket.'),
    'transformers': ('Liquid-dielectric transformers', {'850421', '850422', '850423'},
                     'Small distribution through large power transformers.'),
    'hv_cable': ('Insulated conductors above 1 kV', {'854460'}, 'Grid and non-grid uses.'),
}
ALL = set().union(*(c for _, c, _ in GROUPS.values()))


def iso_map():
    m = {}
    with _baci.country_file() as f:
        for row in csv.DictReader(f):
            c = (row.get('country_iso3') or '').strip()
            if c and c != 'NA':
                m[row['country_code'].strip()] = c
    m['490'] = 'TWN'
    return m


def build():
    iso = iso_map()
    per_year = {g: {y: collections.Counter() for y in YEARS} for g in GROUPS}
    for y in YEARS:
        for row in _baci.year(y, columns=['i', 'k', 'v'], codes=ALL).itertuples(index=False):
            k = row.k
            e = iso.get(str(row.i))
            if not e:
                continue
            v = row.v if row.v == row.v else 0.0
            for g, (_, codes, _) in GROUPS.items():
                if k in codes:
                    per_year[g][y][e] += v

    def stats(counter):
        t = sum(counter.values())
        if not t:
            return None
        sh = sorted(((c, v / t) for c, v in counter.items()), key=lambda kv: -kv[1])
        return {'total_kusd': round(t), 'n_exporters': len(counter),
                'hhi': round(sum(s * s for _, s in sh), 3),
                'top1': round(100 * sh[0][1], 1), 'top3': round(100 * sum(s for _, s in sh[:3]), 1),
                'top5': round(100 * sum(s for _, s in sh[:5]), 1),
                'top': [{'iso3': c, 'pct': round(100 * s, 1)} for c, s in sh[:8]]}

    out = {'generated': datetime.date.today().isoformat(),
           'source': 'CEPII BACI HS17 V202601 (Etalab 2.0; cite Gaulier & Zignago 2010)',
           'basis': 'exporter value shares, gross trade',
           'window': WINDOW,
           'what_this_is_not': ('Capacity. Export shares say who sells, not who can make. A producer '
                                'consuming its own output at home is understated - China notably - and '
                                'some exporters listed are re-selling hubs. Read every HHI here as a '
                                'FLOOR on the real concentration, with the error signed.'),
           'prompted_by': ('Amoah, Brown, Simon, Bazilian & Matisek, "Mineral demand from AI data '
                           'centers: infrastructure intensity, processing bottlenecks, and supply '
                           'competition", Resources Policy 119 (2026) 105970. Reference verified via '
                           'Crossref; full text paywalled and NOT read, so it prompted this check and '
                           'is not evidence for its result.'),
           'groups': {}}
    for g, (title, codes, boundary) in GROUPS.items():
        window = collections.Counter()
        for y in WINDOW:
            window.update(per_year[g][y])
        out['groups'][g] = {
            'title': title, 'hs_codes': sorted(codes), 'boundary': boundary,
            'window': stats(window),
            'by_year': {str(y): stats(per_year[g][y]) for y in YEARS},
        }

    path = os.path.join(HERE, 'out', 'goes.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    print('wrote grid-chain/out/goes.json   (exporter concentration, %d-%d)' % (WINDOW[0], WINDOW[-1]))
    print('%-34s %6s %7s %7s %7s  %s' % ('', 'HHI', 'top1', 'top3', 'top5', 'leader'))
    for g, d in sorted(out['groups'].items(), key=lambda kv: -kv[1]['window']['hhi']):
        w = d['window']
        print('%-34s %6.3f %6.1f%% %6.1f%% %6.1f%%  %s %.0f%%  (%d exporters)'
              % (d['title'], w['hhi'], w['top1'], w['top3'], w['top5'],
                 w['top'][0]['iso3'], w['top'][0]['pct'], w['n_exporters']))
    g = out['groups']['goes']
    print('\nGOES trend: ' + ', '.join('%s %.3f' % (y, g['by_year'][y]['hhi']) for y in
                                       sorted(g['by_year'])))


if __name__ == '__main__':
    build()
