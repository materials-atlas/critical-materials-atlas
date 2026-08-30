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

rows = []
for name in MODELS:
    ph, pm = point[name]
    dhit_ci = ci(boot[name]['dhit']); dmae_ci = ci(boot[name]['dmae'])
    # distinguishable on share MAE if the paired-diff CI excludes 0 (negative = beats persistence)
    beats_mae = dmae_ci[1] < 0
    worse_mae = dmae_ci[0] > 0
    beats_hit = dhit_ci[0] > 0
    worse_hit = dhit_ci[1] < 0
    rows.append({
        'model': name,
        'top_hit_pct': round(ph, 1), 'top_hit_ci': ci(boot[name]['hit']),
        'share_mae_pp': round(pm, 2), 'share_mae_ci': ci(boot[name]['mae']),
        'd_hit_vs_persist_ci': dhit_ci, 'd_mae_vs_persist_ci': dmae_ci,
        'distinguishable_from_persistence': bool(name != BASE and (beats_mae or worse_mae or beats_hit or worse_hit)),
        'verdict': ('baseline' if name == BASE else
                    'beats persistence (share)' if beats_mae else
                    'worse than persistence (share)' if worse_mae else
                    'indistinguishable from persistence'),
    })

out = {'note': ('Block bootstrap over 32 materials (B=2000, seed 20260830). A model differs from naive '
                'persistence only if the 95% CI of the paired difference excludes zero. Heavier '
                'ETS/panel/Bayesian rows on the site are single-run point estimates, not bootstrapped.'),
       'B': B, 'n_materials': len(LABS), 'baseline': BASE, 'models': rows}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'nowcast_bootstrap.json'),
                    'w', encoding='utf-8'), indent=1, ensure_ascii=False)

print(f"Block bootstrap over {len(LABS)} materials, B={B}\n")
print(f"{'model':30}{'hit%':>6} {'hitCI':>13}  {'MAE':>5} {'MAEci':>12}  {'dMAE vs persist 95%CI':>22}  verdict")
for r in rows:
    print(f"{r['model']:30}{r['top_hit_pct']:6.1f} {str(r['top_hit_ci']):>13}  "
          f"{r['share_mae_pp']:5.2f} {str(r['share_mae_ci']):>12}  {str(r['d_mae_vs_persist_ci']):>22}  {r['verdict']}")
print("\nwrote out/nowcast_bootstrap.json")
