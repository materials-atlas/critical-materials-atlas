#!/usr/bin/env python3
"""
Out-of-sample evaluation of the persistence nowcast.

The live 2025*/2026** nowcasts hold each material's TRADE STRUCTURE (exporter shares) at the last
reconciled year and only tilt the levels. This script asks the honest question the nowcast depends on:
how well does "last year's structure" actually predict "this year's structure"?

We answer it on the MEASURED 2018-2024 reconciled BACI series, where the truth is known. For every
material and every consecutive year pair (T-1 -> T) we use year T-1's exporter shares as the nowcast
for year T and score it against the realised year-T shares:

  top1_hit      did T-1's top exporter stay the top exporter in T?
  share_mae     mean |share_T - share_{T-1}| over exporters (percentage points)
  top1_abs_err  |topshare_T - topshare_{T-1}| (pp)
  hhi_abs_err   |HHI_T - HHI_{T-1}|

The same year-over-year movements are the empirical UNCERTAINTY BANDS for the live nowcast: the P50/P90
of |Δ top-exporter share| is how far a leader's share typically/at-worst moves in a year.

Usage:
  python backtest.py                 # reads ../out/flows_YYYY.json (atlas layout)
  FLOWS_DIR=/some/dir python backtest.py
Writes results/backtest.json and prints a summary. Pure stdlib, no key, no network.
"""
import json, os, glob, statistics as st

def find_flows_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [os.environ.get('FLOWS_DIR'),
             os.path.join('..', 'out'), 'out',
             os.path.join(here, '..', 'out'),
             os.path.join(here, 'fixtures', 'out')]   # standalone-clone fallback
    for d in cands:
        if d and glob.glob(os.path.join(d, 'flows_20*.json')):
            return d
    raise SystemExit('No flows_YYYY.json found; set FLOWS_DIR=<dir with flows_2018.json ...>')

def exporter_shares(materials, label):
    flows = materials.get(label) or []
    o, tot = {}, 0.0
    for f in flows:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']
        tot += f['value']
    if not tot:
        return None
    return {c: v / tot for c, v in o.items()}

def hhi(shares):
    return sum(s * s for s in shares.values())

def top1(shares):
    c = max(shares, key=shares.get)
    return c, shares[c]

def pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return float('nan')
    k = (len(xs) - 1) * p
    f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)

def main():
    fd = find_flows_dir()
    years = sorted(int(os.path.basename(p)[6:10]) for p in glob.glob(os.path.join(fd, 'flows_20*.json')))
    data = {}
    for y in years:
        d = json.load(open(os.path.join(fd, f'flows_{y}.json'), encoding='utf8'))
        if d.get('provisional') or d.get('nowcast_kind'):
            continue  # measured years only — never score the nowcast against itself
        data[y] = d['materials']
    measured = sorted(data)
    if len(measured) < 2:
        raise SystemExit('Need >=2 measured years.')
    pairs = [(measured[i - 1], measured[i]) for i in range(1, len(measured))]

    per_pair = {}
    all_smae, all_t1abs, all_hhiabs, all_top1hit = [], [], [], []
    mat_smae = {}     # per-material instability across pairs
    for a, b in pairs:
        hits = n = 0
        smae, t1abs, hhab = [], [], []
        for label in data[b]:
            sa = exporter_shares(data[a], label)
            sb = exporter_shares(data[b], label)
            if not sa or not sb:
                continue
            n += 1
            ca, va = top1(sa); cb, vb = top1(sb)
            hit = (ca == cb); hits += hit; all_top1hit.append(1 if hit else 0)
            cs = set(sa) | set(sb)
            mae = sum(abs(sa.get(c, 0) - sb.get(c, 0)) for c in cs) / len(cs) * 100
            smae.append(mae); t1abs.append(abs(va - vb) * 100); hhab.append(abs(hhi(sa) - hhi(sb)))
            mat_smae.setdefault(label, []).append(mae)
        per_pair[f'{a}->{b}'] = {
            'n': n,
            'top1_hit_rate': round(hits / n, 3),
            'share_mae_pp': round(st.mean(smae), 2),
            'top1_abs_err_pp': round(st.mean(t1abs), 2),
            'hhi_abs_err': round(st.mean(hhab), 3),
        }
        all_smae += smae; all_t1abs += t1abs; all_hhiabs += hhab

    overall = {
        'pairs_scored': len(pairs),
        'material_year_obs': len(all_smae),
        'top1_persistence_rate': round(sum(all_top1hit) / len(all_top1hit), 3),
        'share_mae_pp_mean': round(st.mean(all_smae), 2),
        'top1_abs_err_pp_mean': round(st.mean(all_t1abs), 2),
        'hhi_abs_err_mean': round(st.mean(all_hhiabs), 3),
        'bands_top1_abs_err_pp': {  # uncertainty bands for a leader's annual share move
            'p50': round(pct(all_t1abs, .50), 2),
            'p90': round(pct(all_t1abs, .90), 2),
            'p95': round(pct(all_t1abs, .95), 2),
        },
        'bands_share_mae_pp': {
            'p50': round(pct(all_smae, .50), 2),
            'p90': round(pct(all_smae, .90), 2),
        },
    }
    stable = sorted(((round(st.mean(v), 2), k) for k, v in mat_smae.items()))
    overall['most_predictable'] = [{'material': k, 'mean_share_mae_pp': v} for v, k in stable[:6]]
    overall['least_predictable'] = [{'material': k, 'mean_share_mae_pp': v} for v, k in stable[-6:][::-1]]

    out = {'flows_dir': os.path.abspath(fd), 'measured_years': measured,
           'method': 'persistence: shares_T_hat = shares_{T-1}',
           'overall': overall, 'per_pair': per_pair}
    os.makedirs('results', exist_ok=True)
    json.dump(out, open(os.path.join('results', 'backtest.json'), 'w', encoding='utf8'), indent=2)

    print(f"Out-of-sample persistence backtest  ({measured[0]}-{measured[-1]}, {len(all_smae)} material-years)\n")
    print(f"  {'pair':<12}{'n':>4}{'top1 hit':>10}{'share MAE':>11}{'top1 |d|':>10}{'HHI |d|':>9}")
    for k, v in per_pair.items():
        print(f"  {k:<12}{v['n']:>4}{v['top1_hit_rate']*100:>9.0f}%{v['share_mae_pp']:>10.2f}pp{v['top1_abs_err_pp']:>8.2f}pp{v['hhi_abs_err']:>9.3f}")
    o = overall
    print(f"\n  OVERALL  top-exporter persistence {o['top1_persistence_rate']*100:.0f}%  -  "
          f"share MAE {o['share_mae_pp_mean']:.2f}pp  -  leader |dshare| P50 {o['bands_top1_abs_err_pp']['p50']:.1f} / "
          f"P90 {o['bands_top1_abs_err_pp']['p90']:.1f}pp")
    print(f"  most predictable : {', '.join(m['material'] for m in o['most_predictable'])}")
    print(f"  least predictable: {', '.join(m['material'] for m in o['least_predictable'])}")
    print("\n  -> wrote results/backtest.json")

if __name__ == '__main__':
    main()
