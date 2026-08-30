#!/usr/bin/env python3
"""Block-bootstrap confidence intervals for the nowcast bake-off (author-run; answers an
adversarial-council demand). The council objected that the nine-model leaderboard showed point
estimates with no uncertainty, so sub-percentage-point gaps read as real when they may be noise, and
the material-years are dependent (one country tops many materials). This resamples the 32 MATERIALS
with replacement (a block bootstrap that respects that dependence), B=2000, and recomputes each model's
top-exporter hit rate and leader-share MAE, plus the PAIRED difference versus naive persistence. A
model is 'distinguishable from persistence' only if the 95% CI of the paired difference excludes zero.

Reuses the reproducible model suite in build_nowcast_models.py (the fast, importable models; the
heavier ETS/panel/Bayesian rows shown on the site are single-run point estimates and are not
bootstrapped here). Run: python build_nowcast_bootstrap.py -> writes out/nowcast_bootstrap.json
"""
import os, json, random, statistics
from build_nowcast_models import per_material_records, MODELS, LAB

random.seed(20260830)
B = 2000
REC = per_material_records()
LABS = [lab for lab in LAB if any(REC[lab][n] for n in MODELS)]
BASE = 'persistence (naive)'

def metrics_over(labs, name):
    obs = [o for lab in labs for o in REC[lab][name]]
    n = len(obs)
    hit = 100 * sum(h for h, _ in obs) / n
    mae = statistics.mean(e for _, e in obs)
    return hit, mae

def ci(vals):
    v = sorted(vals)
    return round(v[int(0.025 * len(v))], 2), round(v[int(0.975 * len(v))], 2)

# point estimates
point = {name: metrics_over(LABS, name) for name in MODELS}

# bootstrap
boot = {name: {'hit': [], 'mae': [], 'dhit': [], 'dmae': []} for name in MODELS}
for _ in range(B):
    samp = [random.choice(LABS) for _ in LABS]        # resample materials with replacement
    bh, bm = metrics_over(samp, BASE)
    for name in MODELS:
        h, m = metrics_over(samp, name)
        boot[name]['hit'].append(h); boot[name]['mae'].append(m)
        boot[name]['dhit'].append(h - bh)             # model - persistence (hit; higher better)
        boot[name]['dmae'].append(m - bm)             # model - persistence (mae; lower better)

def boot_p(dd):
    """two-sided bootstrap p-value for a paired difference vs persistence."""
    neg = sum(d < 0 for d in dd) / len(dd); pos = sum(d > 0 for d in dd) / len(dd)
    return round(2 * min(neg, pos), 4)

rows = []
for name in MODELS:
    ph, pm = point[name]
    dhit_ci = ci(boot[name]['dhit']); dmae_ci = ci(boot[name]['dmae'])
    beats_mae = dmae_ci[1] < 0
    worse_mae = dmae_ci[0] > 0
    beats_hit = dhit_ci[0] > 0
    worse_hit = dhit_ci[1] < 0
    rows.append({
        'model': name,
        'top_hit_pct': round(ph, 1), 'top_hit_ci': ci(boot[name]['hit']),
        'share_mae_pp': round(pm, 2), 'share_mae_ci': ci(boot[name]['mae']),
        'd_hit_vs_persist_ci': dhit_ci, 'd_mae_vs_persist_ci': dmae_ci,
        'p_mae_vs_persist': None if name == BASE else boot_p(boot[name]['dmae']),
        'distinguishable_from_persistence_uncorrected': bool(name != BASE and (beats_mae or worse_mae or beats_hit or worse_hit)),
        'verdict_uncorrected': ('baseline' if name == BASE else
                    'beats persistence (share)' if beats_mae else
                    'worse than persistence (share)' if worse_mae else
                    'indistinguishable from persistence'),
    })

# --- Holm-Bonferroni across the non-baseline models (the council's multiplicity demand) ---
alt = sorted((r for r in rows if r['model'] != BASE), key=lambda r: r['p_mae_vs_persist'])
m = len(alt); still = True
for i, r in enumerate(alt):
    thr = 0.05 / (m - i)
    r['holm_threshold'] = round(thr, 4)
    r['survives_holm'] = bool(still and r['p_mae_vs_persist'] < thr)
    still = r['survives_holm']
    r['direction'] = 'better' if r['d_mae_vs_persist_ci'][1] < 0 else ('worse' if r['d_mae_vs_persist_ci'][0] > 0 else 'n/a')
holm_winners = [r['model'] for r in alt if r['survives_holm'] and r['direction'] == 'better']
holm_worse = [r['model'] for r in alt if r['survives_holm'] and r['direction'] == 'worse']

out = {'note': ('Block bootstrap over 32 materials (B=2000, seed 20260830). ESTIMAND: uncertainty across '
                'the 32-material atlas conditional on the 2019-2024 backtest window -- not a claim about all '
                'future years. Raw 95% paired-difference CIs are exploratory; the Holm-Bonferroni column '
                'corrects for testing several models. Heavier ETS/panel/Bayesian rows on the site are '
                'single-run point estimates, not bootstrapped and outside this multiplicity correction.'),
       'B': B, 'n_materials': len(LABS), 'baseline': BASE,
       'holm_significant_better': holm_winners, 'holm_significant_worse': holm_worse,
       'models': rows}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'nowcast_bootstrap.json'),
                    'w', encoding='utf-8'), indent=1, ensure_ascii=False)

print(f"Block bootstrap over {len(LABS)} materials, B={B}\n")
print(f"{'model':30}{'hit%':>6}  {'MAE':>5}  {'dMAE 95%CI':>16} {'p':>6} {'Holm':>10}")
for r in rows:
    if r['model'] == BASE:
        print(f"{r['model']:30}{r['top_hit_pct']:6.1f}  {r['share_mae_pp']:5.2f}  {'(baseline)':>16}")
        continue
    print(f"{r['model']:30}{r['top_hit_pct']:6.1f}  {r['share_mae_pp']:5.2f}  {str(r['d_mae_vs_persist_ci']):>16} "
          f"{r['p_mae_vs_persist']:6.3f} {('SURVIVES' if r['survives_holm'] else 'no')+' '+r.get('direction',''):>10}")
print(f"\nHolm-Bonferroni verdict: better-than-persistence {holm_winners or 'NONE'}; "
      f"worse {holm_worse or 'none'}.")
print("No model reliably beats persistence after multiplicity correction." if not holm_winners
      else f"Survives as better: {holm_winners}")
print("wrote out/nowcast_bootstrap.json")
