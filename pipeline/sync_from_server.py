# -*- coding: utf-8 -*-
"""Bring the server's nightly results to this machine.

From 18 Nov 2026 the nightly refresh runs on the server (pipeline/scheduled_run.py in server mode,
pipeline/server/atlas-nightly.*), next to the UN bulk corpus. This PC no longer refreshes anything
by itself; before building here (build.py, build_cube.py, the site), copy what the server made:

  raw/comtrade_bulk_crm/      the atlas's UN rows cut from the corpus (what adapter_comtrade reads)
  pipeline/data/cache/        every source's refreshed cache (what build.py unions)
  pipeline/data/scheduled.log the server's run log (what check.py `refresh` and refresh_watch read)

Then `python pipeline/build.py` here gives the same tables as the server's (the build is
reproducible across the two machines since 10 Nov 2026, to the 16th decimal).

    python pipeline/sync_from_server.py            # host from $CMA_SERVER, default 'lenovo' (ssh alias)

Copies whole folders with scp; the three together are well under 200 MB on the home network.
Exits non-zero when the server cannot be reached, so a caller can tell a stale copy from a fresh one.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
HOST = os.environ.get('CMA_SERVER', 'lenovo')
REMOTE = os.environ.get('CMA_SERVER_REPO', 'critical-materials-atlas')   # relative to the server home

ITEMS = [('raw/comtrade_bulk_crm', True),
         ('pipeline/data/cache', True),
         ('pipeline/data/scheduled.log', False)]


def main():
    ok = True
    for rel, is_dir in ITEMS:
        dest = os.path.join(REPO, *rel.split('/'))
        tmp = dest + '.sync'
        if os.path.isdir(tmp):
            shutil.rmtree(tmp)
        elif os.path.exists(tmp):
            os.remove(tmp)
        src = '%s:%s/%s' % (HOST, REMOTE, rel)
        cmd = ['scp', '-q', '-o', 'ConnectTimeout=15'] + (['-r'] if is_dir else []) + [src, tmp]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print('FAILED %s: %s' % (rel, (r.stderr or '').strip()[:200]))
            ok = False
            continue
        # Swap in only a complete copy: a half-finished scp must never replace a good folder.
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        elif os.path.exists(dest):
            os.remove(dest)
        os.replace(tmp, dest)
        print('synced %s' % rel)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
