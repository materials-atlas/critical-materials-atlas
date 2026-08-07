#!/usr/bin/env python3
"""
The atlas's headline finding, computed from the data: the ORIGIN GAP.

For each material we compare, in the same year, where it is exported from (reconciled bilateral trade)
against where it is mined (USGS reference shares). The gap between the top exporter's TRADE share and that
same country's MINE share is how much customs import-origin statistics overstate the geographic
diversification of true supply — i.e. how much the refiner/hub stands in front of the mine.

  origin_gap(material) = top_exporter_trade_share - (that country's mine share)

Aggregated by country, it produces the "refiner-illusion league table": who dominates the export of
materials they barely mine. Reads ../out/{data.json,flows_2024.json}. Pure stdlib. Writes
results/findings.json and prints the tables that seed FINDINGS.md.
"""
import json, os, glob

YEAR = os.environ.get('FINDINGS_YEAR', '2024')
SHARED_HS6 = {'gallium', 'germanium', 'hafnium'}  # one HS6 code 811292 — identical trade columns

def root():
    here = os.path.dirname(os.path.abspath(__file__))
    for d in [os.environ.get('FLOWS_DIR'), os.path.join('..', 'out'), 'out', os.path.join(here, '..', 'out'), os.path.join(here, 'fixtures', 'out')]:
        if d and glob.glob(os.path.join(d, 'flows_20*.json')):
            return d
    raise SystemExit('No out/ found; set FLOWS_DIR.')

def top_exporter(flows):
    o, tot = {}, 0.0
    for f in flows:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; tot += f['value']
    if not tot:
        return None
    c = max(o, key=o.get)
    return {'c': c, 'share': o[c] / tot * 100, 'tot': tot}

def main():
    fd = root()
    data = {m['label']: m for m in json.load(open(os.path.join(fd, 'data.json'), encoding='utf8'))['materials']}
    flows = json.load(open(os.path.join(fd, f'flows_{YEAR}.json'), encoding='utf8'))['materials']

    rows = []
    for label, m in data.items():
        fl = flows.get(label)
        te = top_exporter(fl) if fl else None
        if not te:
            continue
        mined = {x['c']: x['v'] for x in (m.get('mined') or [])}
        te_mine = mined.get(te['c'], 0.0)
        top_miner = max(mined, key=mined.get) if mined else None
        rows.append({
            'label': label, 'title': m['title'].split(' (')[0],
            'top_exporter': te['c'], 'exporter_share': round(te['share'], 1),
            'exporter_mine_share': round(te_mine, 1),
            'origin_gap': round(te['share'] - te_mine, 1),
            'top_miner': top_miner, 'top_mine_share': round(mined.get(top_miner, 0), 1) if top_miner else None,
            'mismatch': bool(top_miner and te['c'] != top_miner),
            'shared_hs6': label in SHARED_HS6,
        })

    rows.sort(key=lambda r: r['origin_gap'], reverse=True)
    n = len(rows)
    mismatch = [r for r in rows if r['mismatch']]
    illusion = [r for r in rows if r['exporter_mine_share'] < 5 and r['exporter_share'] > 25]

    # league table: by top exporter, over materials where it exports much more than it mines
    league = {}
    for r in rows:
        if r['origin_gap'] <= 0:
            continue
        d = league.setdefault(r['top_exporter'], {'country': r['top_exporter'], 'materials': [], 'gaps': []})
        d['materials'].append(r['title']); d['gaps'].append(r['origin_gap'])
    league = sorted(league.values(), key=lambda d: (len(d['materials']), sum(d['gaps'])), reverse=True)
    for d in league:
        d['n'] = len(d['materials']); d['mean_gap'] = round(sum(d['gaps']) / len(d['gaps']), 1)
        d['total_gap'] = round(sum(d['gaps']), 1)

    out = {'year': YEAR, 'n_materials': n,
           'n_top_exporter_not_top_miner': len(mismatch),
           'n_refiner_illusion': len(illusion),
           'by_origin_gap': rows, 'league_table': league}
    os.makedirs('results', exist_ok=True)
    json.dump(out, open(os.path.join('results', 'findings.json'), 'w', encoding='utf8'), indent=2)

    print(f"ORIGIN GAP — {YEAR}  ({n} materials)\n")
    print(f"  In {len(mismatch)}/{n} materials the top EXPORTER is not the top MINER.")
    print(f"  In {len(illusion)}/{n} a country exporting >25% of world trade mines <5% of it.\n")
    print(f"  {'material':<26}{'exporter':>9}{'exp%':>6}{'mines%':>7}{'gap(pp)':>9}   miner")
    for r in rows[:14]:
        s = '*' if r['shared_hs6'] else ' '
        print(f"  {r['title'][:25]:<26}{r['top_exporter']:>9}{r['exporter_share']:>6.0f}{r['exporter_mine_share']:>7.0f}{r['origin_gap']:>8.0f}{s}  {r['top_miner']} {r['top_mine_share']:.0f}%")
    print(f"\n  REFINER-ILLUSION LEAGUE TABLE (exports >> mines)\n")
    print(f"  {'country':>8}{'#mats':>7}{'mean gap':>10}   materials")
    for d in league[:8]:
        print(f"  {d['country']:>8}{d['n']:>7}{d['mean_gap']:>9.0f}pp   {', '.join(d['materials'][:6])}")
    print("\n  (* = gallium/germanium/hafnium share one HS6 code; identical trade)")
    print("  -> wrote results/findings.json")

if __name__ == '__main__':
    main()
