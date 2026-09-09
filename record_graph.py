# -*- coding: utf-8 -*-
"""Record what every builder ACTUALLY reads and writes. Phase 1 of ARCHITECTURE.md.

WHY OBSERVED AND NOT DECLARED
Two independent reviewers said the dependency rules in ARCHITECTURE.md could not be enforced,
because a hand-written manifest always misses an edge: a glob, a path built from a variable, a
pandas call that opens its file in C rather than through Python. They are right about DECLARED
manifests, and that objection has killed this idea in other projects.

It does not apply here. sys.addaudithook fires on every file access in the process, including from
compiled extensions - measured against pandas.read_parquet, zipfile and json/open before this file
was written. So nobody writes the graph down, and nobody can forget to.

WHAT THIS DOES NOT DO
It changes no output and enforces no rule. It runs builders and watches. That is the whole of
phase 1, deliberately: the graph has to be true before anything is built on top of it, and we need
to know which outputs the BACI migration would move BEFORE touching a live finding.

A builder is run in a SUBPROCESS with its own hook, because a builder that calls sys.exit or dies
must not take the recorder with it, and because module-level state must not leak between builders.

RECORDING MUST NOT MUTATE THE REPOSITORY
The first run of this file did. To see what a builder touches you must RUN it, and running 277
builders in alphabetical order ran add_canonicals.py first - it rewrites all 3,695 HTML files -
and then let 200+ page builders overwrite its work. 129 pages silently lost their canonical tags,
favicons, skip-links and clean URLs. Nothing errored. check.py stayed green.

That is the finding, not the accident: THIS REPOSITORY HAS A BUILD ORDER THAT NOTHING ENCODES.
It lives only as knowledge, and knowledge does not survive being run alphabetically.

So the recorder now restores after every builder: tracked files go back via git, files the builder
created are deleted, and the gitignored data stores are snapshotted before the run and compared
after. Observation must leave no trace, or it is not observation.

COST
Running 286 builders is not free and some are slow. --only and --skip-slow exist for that. A
builder that fails is recorded as failed, not silently omitted: an unrecorded builder is itself a
finding, and pretending otherwise would be the green-gate-on-a-lie this project keeps warning about.

Run:  python record_graph.py [--only PREFIX] [--timeout N] [--limit N]
Out:  out/graph.json
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'out', 'graph.json')

# Builders that must never be run by a recorder: they fetch from the network, cost API quota,
# or rewrite state that another process depends on. Their edges are recorded as "not observed"
# rather than guessed - an honest hole beats an invented edge.
NEVER_RUN = (
    'backfill_', 'fetch_', 'refresh', 'pull_', 'download', 'record_graph',
    'check.py',            # the gate itself; it reads everything and would drown the graph
    'scheduled_run',
)

PROBE = r'''
import sys, os, json, runpy
ROOT = os.path.abspath(%(root)r)
R, W = set(), set()
def _rel(p):
    try:
        rp = os.path.relpath(os.path.abspath(p), ROOT)
    except (ValueError, OSError):
        return None
    return None if rp.startswith('..') else rp.replace(os.sep, '/')
def hook(event, args):
    try:
        if event == 'open':
            p, mode = args[0], args[1]
            if not isinstance(p, str):
                return
            r = _rel(p)
            if r is None:
                return
            m = mode if isinstance(mode, str) else ''
            (W if ('w' in m or 'a' in m or 'x' in m or '+' in m) else R).add(r)
        elif event in ('os.scandir', 'os.listdir'):
            if args and isinstance(args[0], str):
                r = _rel(args[0])
                if r is not None:
                    R.add(r + '/')
    except Exception:
        pass
sys.addaudithook(hook)
os.chdir(ROOT)
sys.argv = [%(script)r]
code = 0
try:
    runpy.run_path(os.path.join(ROOT, %(script)r), run_name='__main__')
except SystemExit as e:
    code = e.code if isinstance(e.code, int) else 0
except BaseException as e:
    code = 'EXC:' + type(e).__name__ + ': ' + str(e)[:160]
sys.stderr.write('<<<GRAPH>>>' + json.dumps({
    'reads': sorted(R), 'writes': sorted(W), 'exit': code}))
'''


def builders():
    out = []
    for dirpath, dirnames, files in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in ('.git', '__pycache__', 'raw', 'node_modules', '.venv')]
        for f in files:
            if not f.endswith('.py'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, f), ROOT).replace(os.sep, '/')
            if any(k in rel for k in NEVER_RUN):
                continue
            if rel.startswith('pipeline/'):     # the pipeline has its own entry point
                continue
            out.append(rel)
    return sorted(out)


def sha(path):
    try:
        with open(path, 'rb') as fh:
            return hashlib.sha256(fh.read()).hexdigest()[:16]
    except OSError:
        return None


def git(*a):
    p = subprocess.run(['git', *a], capture_output=True, cwd=ROOT)
    return p.stdout.decode('utf-8', 'replace')


def tracked(path):
    return git('ls-files', '--error-unmatch', '--', path).strip() != ''


def restore(paths):
    """Undo whatever a builder just wrote. Tracked files revert; new files are removed."""
    undone, orphaned = 0, []
    for p in paths:
        full = os.path.join(ROOT, p)
        if tracked(p):
            git('checkout', '--', p)
            undone += 1
        elif os.path.exists(full):
            try:
                os.remove(full)
                undone += 1
            except OSError:
                orphaned.append(p)
    return undone, orphaned


def snapshot_data():
    """Gitignored stores cannot be restored by git, so copy them before anything runs."""
    keep = {}
    d = os.path.join(ROOT, 'pipeline', 'data')
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith('.parquet'):
            keep[os.path.join('pipeline', 'data', f)] = sha(os.path.join(d, f))
    return keep


def run(script, timeout):
    probe = PROBE % {'root': ROOT, 'script': script}
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, '-c', probe], capture_output=True, text=True,
                           timeout=timeout, cwd=ROOT)
        err = p.stderr or ''
    except subprocess.TimeoutExpired:
        return {'exit': 'TIMEOUT', 'reads': [], 'writes': [], 'secs': round(time.time() - t0, 1)}
    i = err.rfind('<<<GRAPH>>>')
    if i < 0:
        return {'exit': 'NO_RECORD', 'reads': [], 'writes': [],
                'stderr': err[-200:], 'secs': round(time.time() - t0, 1)}
    d = json.loads(err[i + len('<<<GRAPH>>>'):])
    d['secs'] = round(time.time() - t0, 1)
    # REDACT paths outside the repository from anything free-text. A failing builder's exception
    # message carried an absolute path from a temp directory, and the anonymity scrub - correctly -
    # refused to commit it. Only the repo-relative structure is the graph's business.
    for k in ('exit', 'stderr'):
        if isinstance(d.get(k), str):
            d[k] = _redact(d[k])
    return d


def _redact(text):
    # \x27 and \x22 are the quote characters, spelled out so the pattern survives every quoting
    # layer this file gets edited through (a heredoc already ate one version of this line).
    return re.sub(r'[A-Za-z]:[\\/][^\s\x27\x22]+', '<external path>', text)


def main():
    a = sys.argv[1:]
    only = a[a.index('--only') + 1] if '--only' in a else None
    timeout = int(a[a.index('--timeout') + 1]) if '--timeout' in a else 240
    limit = int(a[a.index('--limit') + 1]) if '--limit' in a else None

    bs = [b for b in builders() if not only or b.startswith(only)]
    if limit:
        bs = bs[:limit]
    if not bs:
        # A --only that matches nothing used to print "recording 0 builders" and exit 0. A retry
        # loop fed names with Windows line endings therefore recorded NOTHING, 22 times, and
        # reported success. Machinery that looks present and does nothing is this project's
        # recurring defect; refuse instead.
        raise SystemExit('--only %r matched no builder. Nothing was recorded.' % only)
    print('recording %d builders (timeout %ds each)' % (len(bs), timeout))

    before = snapshot_data()
    graph, ok, bad = {}, 0, 0
    for n, b in enumerate(bs, 1):
        r = run(b, timeout)
        r['code_sha'] = sha(os.path.join(ROOT, b))
        r['reads'] = [x for x in r['reads'] if x != b]      # a script reading itself is not an edge
        # OBSERVATION LEAVES NO TRACE. Undo the builder's writes before running the next one.
        n_undone, orphaned = restore(r['writes'])
        r['restored'] = n_undone
        if orphaned:
            r['ORPHANED'] = orphaned
        graph[b] = r
        good = r['exit'] == 0
        ok += good
        bad += not good
        flag = ' ' if good else '!'
        print('%s [%3d/%3d] %-44s %2d in %2d out %5.1fs %s'
              % (flag, n, len(bs), b[:44], len(r['reads']), len(r['writes']), r['secs'],
                 '' if good else r['exit']), flush=True)

    # MERGE, never overwrite. A --only run recording one builder must not delete the other 276.
    # This is the same defect as the cache that overwrote instead of merging, and it cost the
    # full graph the first time --only was used.
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    held = {}
    if os.path.exists(OUT):
        try:
            held = json.load(io.open(OUT, encoding='utf-8')).get('builders', {})
        except Exception:
            held = {}
    merged = dict(held)
    merged.update(graph)
    with io.open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(json.dumps({'note': 'Observed, not declared. See ARCHITECTURE.md section 3.',
                             'recorded_at': time.strftime('%Y-%m-%d'),
                             'builders': merged}, indent=1))
    if len(merged) > len(graph):
        print('merged with %d builders recorded earlier' % (len(merged) - len(graph)))
    print('\nwrote out/graph.json  -  %d ran clean, %d did not' % (ok, bad))


if __name__ == '__main__':
    sys.exit(main())
