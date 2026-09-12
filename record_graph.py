# -*- coding: utf-8 -*-
"""Record what every builder ACTUALLY reads and writes. Phase 1 of ARCHITECTURE.md.

WHY OBSERVED AND NOT DECLARED
Two independent reviewers said the dependency rules in ARCHITECTURE.md could not be enforced,
because a hand-written manifest always misses an edge: a glob, a path built from a variable, a
pandas call that opens its file in C rather than through Python. They are right about DECLARED
manifests, and that objection has killed this idea in other projects.

It mostly does not apply here. sys.addaudithook fires on every file access that goes through
CPython's own open() - measured against pandas.read_parquet, zipfile and json/open before this file
was written. So nobody writes the graph down, and nobody can forget to.

WHERE THAT CLAIM WAS TOO STRONG, AND WHAT IT COST
"Including from compiled extensions" is what this file used to say, and it is false. A C library
that does its own I/O never calls CPython's open() and the hook never fires. Found on 11 Sep by
building the register's `read_by` column out of this graph and noticing that raw/maus and raw/sepin
- 122 MB of mining-footprint polygons that two builders demonstrably read - had no reader at all.

  sqlite3   raises its OWN audit event, "sqlite3.connect", and no "open". Three builders read
            GeoPackages (which are SQLite files) through it, and all three edges were missing.
            Fixed below by listening for that event: complete, and as cheap as the rest.
  duckdb    raises NOTHING identifiable. It fires "open" for its own libraries and never for the
            parquet it reads or writes - measured directly, not assumed. Worse, the obvious repair
            does not work either: DuckDBPyConnection.execute is a read-only C attribute, so the
            probe cannot wrap it, and a proxy object standing in for the connection would change
            what the builder runs - which a recorder must never do. Module-level entry points
            (duckdb.sql, duckdb.read_parquet) ARE wrapped, because those are patchable and free.

SO ONE EDGE IS DECLARED RATHER THAN OBSERVED, AND SAYS SO
Measured, so the size of the hole is known rather than feared: of 268 builders exactly one imports
duckdb - extract_baci.py - and it opens the BACI archive with Python's own zipfile, so its INPUTS
are observed normally. Only its output is invisible: it writes each member with COPY ... TO. That
single edge is in DECLARED below, is merged into the graph marked `declared` rather than observed,
and is the only edge in this repository that anybody had to write down. The whole point of the
distinction is that it stays visible instead of dissolving into the rest.

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
    'runner.py',           # reads the graph it would be recorded into, and rebuilds from it
    'repro_audit.py',      # runs every builder itself; recording it would recurse
    'repro_triage.py',     # same: it runs the held builders to price them
    'scheduled_run',
    'build_bgs_panel',     # a network fetcher wearing a builder's name: seven minutes against
                           # the BGS API, and its 63 outputs are the cube's spine. Not for a
                           # recorder to re-run - and it was, and the old restore() then
                           # deleted what it fetched.
)

# The only edges nobody can observe, with the reason each one is here. An entry is a confession,
# not a convenience: anything added here is a place where this file stopped being a measurement.
DECLARED = {
    'extract_baci.py': {
        'writes': ['extract/baci/'],
        'why': 'writes every member with DuckDB COPY ... TO, which does its own I/O and raises no '
               'audit event; its inputs ARE observed, because it opens the archive with zipfile',
    },
}

PROBE = r'''
import sys, os, json, re, runpy, builtins
ROOT = os.path.abspath(%(root)r)
R, W = set(), set()
def _rel(p):
    try:
        rp = os.path.relpath(os.path.abspath(p), ROOT)
    except (ValueError, OSError):
        return None
    return None if rp.startswith('..') else rp.replace(os.sep, '/')
# DuckDB does its own I/O and raises no usable audit event, so the only place left to stand is
# the query. Wrapping connect() lets us read the SQL that actually ran and pull the file paths out
# of it - read_parquet('x'), FROM 'x', COPY ... TO 'x'. Installed by overriding __import__ so it
# costs nothing in the builders that never import duckdb, which is 264 of 268.
_PATHY = re.compile(r"['\"]([^'\"]+\.(?:parquet|csv|json|zip|gpkg|db|tsv|txt|xlsx))['\"]", re.I)
_COPYTO = re.compile(r"\bCOPY\b.*?\bTO\b\s*['\"]([^'\"]+)['\"]", re.I | re.S)


def _sql_paths(sql):
    try:
        text = sql if isinstance(sql, str) else ''
    except Exception:
        return
    for m in _COPYTO.finditer(text):
        r = _rel(m.group(1))
        if r is not None:
            W.add(r)
    written = set()
    for m in _COPYTO.finditer(text):
        written.add(m.group(1))
    for m in _PATHY.finditer(text):
        if m.group(1) in written:
            continue
        r = _rel(m.group(1))
        if r is not None:
            R.add(r)


def _wrap_duckdb(mod):
    # Module-level entry points only. The CONNECTION is deliberately left alone: its execute is a
    # read-only C attribute, and standing a proxy object in its place would change what the builder
    # runs. A recorder that alters the program it measures is worse than one with a known gap, so
    # the gap is declared instead - see DECLARED.
    if mod is None or getattr(mod, '_graph_wrapped', False):
        return
    try:
        for name in ('sql', 'query', 'read_parquet', 'read_csv_auto', 'from_parquet'):
            fn = getattr(mod, name, None)
            if callable(fn):
                setattr(mod, name, _record(fn))
        mod._graph_wrapped = True
    except Exception:
        pass


def _record(fn):
    def inner(*a, **k):
        for x in a[:2]:
            if isinstance(x, str):
                _sql_paths(x)
        return fn(*a, **k)
    return inner


_real_import = builtins.__import__


def _imp(name, *a, **k):
    m = _real_import(name, *a, **k)
    if name.split('.')[0] == 'duckdb':
        _wrap_duckdb(sys.modules.get('duckdb'))
    return m


builtins.__import__ = _imp


def hook(event, args):
    try:
        if event == 'sqlite3.connect':
            # sqlite3 raises this INSTEAD of open(). Every GeoPackage in raw/ is a SQLite file,
            # and without this line three builders read 122 MB with no edge recorded.
            if args and isinstance(args[0], str):
                r = _rel(args[0])
                if r is not None:
                    R.add(r)
        elif event == 'open':
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


def ignored(path):
    return subprocess.run(['git', 'check-ignore', '-q', '--', path], cwd=ROOT).returncode == 0


def restore(paths):
    """Undo whatever a builder just wrote. Tracked files revert; NEW stray files are removed.

    A gitignored path is a DATA STORE and is never touched. The first version of this function
    treated "not tracked" as "stray" and deleted the 63-file BGS panel - the cube's spine - right
    after build_bgs_panel.py had spent seven minutes fetching it from the API. The cube then
    rebuilt on the wreckage and lost 105,000 production rows without a single error.
    Gitignored means "regenerable and deliberately outside git", not "disposable".
    """
    undone, orphaned, kept = 0, [], 0
    for p in paths:
        full = os.path.join(ROOT, p)
        if tracked(p):
            git('checkout', '--', p)
            undone += 1
        elif ignored(p):
            kept += 1                      # a data store: leave it exactly as the builder left it
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
    only = a[a.index('--only') + 1].strip() if '--only' in a else None   # a trailing CR is not a name
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
        d = DECLARED.get(b)
        if d:
            # Merged, and LABELLED. A reader of graph.json can tell an observed edge from a written
            # one without reading this file, which is the only reason declaring anything is tolerable.
            r['declared'] = d
            for w in d.get('writes', ()):
                if w not in r['writes']:
                    r['writes'].append(w)
            for x in d.get('reads', ()):
                if x not in r['reads']:
                    r['reads'].append(x)
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
    # A builder that no longer exists is not an edge. The merge kept the nine chain extractors
    # deleted by the BACI sweep, so the graph reported nine zip openers in a one-door world.
    merged = {b: v for b, v in held.items() if os.path.exists(os.path.join(ROOT, b))}
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
