"""Release gate for the trade engine: raw UN Comtrade fixture -> reconciliation -> validated vs BACI.

This used to run in public CI from committed fixtures. The raw Comtrade declarations are the
holder's record and are no longer redistributed (17 Sep 2026), so this leg runs here, on the
maintainer's machine, before every release. Same bar as the old CI step: top-1 exporter and
importer match at least 20 of 30 codes, for both years.
Usage:  python reconcile/validate_fixtures.py
"""
import os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, ATLAS_ROOT='fixtures', PYTHONIOENCODING='utf-8')
bad = []
for y in ('2022', '2024'):
    raw = os.path.join(HERE, 'fixtures', 'raw', 'comtrade', 'comtrade_%s.csv.gz' % y)
    if not os.path.exists(raw):
        sys.exit('missing %s - the raw Comtrade fixtures live only on the maintainer machine' % raw)
    subprocess.run([sys.executable, 'reconcile.py', y], cwd=HERE, env=env, check=True,
                   stdout=subprocess.DEVNULL)
    out = subprocess.run([sys.executable, 'validate.py', y], cwd=HERE, env=env, check=True,
                         capture_output=True, text=True, encoding='utf-8').stdout
    for side in ('EXPORTER', 'IMPORTER'):
        m = re.search(side + r' : top-1 (\d+)/30', out)
        n = int(m.group(1)) if m else -1
        print('%s %s top-1 %d/30' % (y, side, n))
        if n < 20:
            bad.append('%s %s' % (y, side))
if bad:
    sys.exit('FAIL: ' + ', '.join(bad))
print('end-to-end reproduced for 2022 + 2024: raw Comtrade -> reconciliation -> validated vs BACI.')
