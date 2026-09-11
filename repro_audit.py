# -*- coding: utf-8 -*-
"""Can this repository still rebuild what it publishes? Measured, one builder at a time.

WHY THIS EXISTS
The runner (phase 3) rebuilt eighteen builders in dependency order on 11 Sep. It worked - and what
it produced was WORSE than what was committed. Eight published pages came back without their
favicons, without the skip-link, with the old two-item navigation instead of the five-hub one, with
`.html` URLs instead of the clean ones, and in one case with a headline that had been rewritten by
hand weeks ago.

None of that is in any builder. `git log -S favicon-192` finds one commit that edited 244 HTML
files and added no script at all. So the site has been improved by bulk edits and by hand, and the
builders were never brought up to match: THE PAGE A BUILDER PRODUCES IS NOT THE PAGE WE PUBLISH.

That reverses the direction of the usual staleness question. The runner asks "is the output behind
its inputs?" This asks the other one: "is the BUILDER behind its output?" A repository can be green
on the first and still be unable to reproduce a single page.

HOW IT MEASURES, AND WHY IT IS SAFE
It reuses record_graph.run(), which runs a builder in a subprocess under the audit hook, and
record_graph.restore(), which reverts every tracked file the builder wrote and leaves gitignored
data stores alone. So each builder is run, its outputs hashed, and the tree put back - the same
machinery the BACI acceptance harness ran 268 times without damaging anything. The comparison is
against the COMMITTED blob (`git show HEAD:path`), not against the working tree, so a file this
audit has already touched cannot corrupt the answer.

Bytes are compared after normalising line endings only. A page that differs solely because git
would rewrite CRLF is not a finding; anything else is.

Run:  python repro_audit.py [--only PREFIX] [--timeout N]
Out:  out/repro_audit.json + a summary on stdout
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import record_graph as rg                                    # noqa: E402

OUT = os.path.join(ROOT, 'out', 'repro_audit.json')


def committed(path):
    p = subprocess.run(['git', 'show', 'HEAD:' + path], capture_output=True, cwd=ROOT)
    return p.stdout if p.returncode == 0 else None


def norm(b):
    return None if b is None else b.replace(b'\r\n', b'\n')


def sha(b):
    return None if b is None else hashlib.sha256(b).hexdigest()[:16]


def read(path):
    try:
        return io.open(os.path.join(ROOT, path), 'rb').read()
    except OSError:
        return None


def main():
    a = sys.argv[1:]
    only = a[a.index('--only') + 1].strip() if '--only' in a else None
    timeout = int(a[a.index('--timeout') + 1]) if '--timeout' in a else 300

    g = json.load(io.open(os.path.join(ROOT, 'out', 'graph.json'), encoding='utf-8'))['builders']
    # Only builders that write something git tracks: a gitignored data store has no committed blob
    # to compare against, and is not what "what we publish" means.
    cand = []
    for b, v in sorted(g.items()):
        if rg.never_run(b) if hasattr(rg, 'never_run') else any(k in b for k in rg.NEVER_RUN):
            continue
        if not os.path.exists(os.path.join(ROOT, b)):
            continue
        outs = [w for w in v.get('writes', ()) if not w.endswith('/') and committed(w) is not None]
        if outs:
            cand.append((b, outs))
    if only:
        cand = [(b, o) for b, o in cand if b.startswith(only)]
    print('auditing %d builders that write %d tracked outputs (timeout %ds each)'
          % (len(cand), sum(len(o) for o in (x[1] for x in cand)), timeout), flush=True)

    res = {}
    same = diff = gone = failed = 0
    t0 = time.time()
    for n, (b, outs) in enumerate(cand, 1):
        r = rg.run(b, timeout)
        rows = {}
        for w in outs:
            now, was = read(w), committed(w)
            if now is None:
                rows[w] = 'not-written'
            elif norm(now) == norm(was):
                rows[w] = 'same'
            else:
                rows[w] = 'DIFFERS'
                rows[w + '::bytes'] = [len(was or b''), len(now)]
        rg.restore(r.get('writes', []))
        ok = r['exit'] == 0
        res[b] = {'exit': r['exit'], 'secs': r.get('secs'), 'outputs': rows}
        d = sum(1 for k, v in rows.items() if v == 'DIFFERS')
        s = sum(1 for k, v in rows.items() if v == 'same')
        m = sum(1 for k, v in rows.items() if v == 'not-written')
        same += s
        diff += d
        gone += m
        failed += 0 if ok else 1
        print('%s [%3d/%3d] %-44s %2d same %2d DIFFER %2d missing %6.1fs%s'
              % (' ' if ok and not d else '!', n, len(cand), b[:44], s, d, m, r.get('secs', 0),
                 '' if ok else '  ' + str(r['exit'])[:40]), flush=True)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
        {'note': 'Can each builder reproduce the output committed in git? See repro_audit.py.',
         'measured': time.strftime('%Y-%m-%d'),
         'totals': {'outputs_same': same, 'outputs_differ': diff,
                    'outputs_not_written': gone, 'builders_failed': failed},
         'builders': res}, indent=1, sort_keys=True))
    print('\n%d outputs reproduce exactly | %d DIFFER | %d not written | %d builders failed | %.1f min'
          % (same, diff, gone, failed, (time.time() - t0) / 60))
    print('wrote out/repro_audit.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
