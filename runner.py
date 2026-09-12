# -*- coding: utf-8 -*-
"""Rebuild what a change invalidates, in dependency order. Phase 3 of ARCHITECTURE.md.

WHAT IT IS FOR
Two failures, both already suffered:

  * THE GERMANIUM CLASS. data.json's germanium refining share was corrected; out/risk.json had
    been built weeks earlier and kept scoring the old value for three weeks. Every file was
    internally valid, so no link check and no schema check could see it. The only signal is
    "an input changed and its consumer did not rebuild" - which is this file.
  * THE 129-PAGE CLASS. The recorder's first pass ran the builders alphabetically, which put
    add_canonicals.py first and let 200 page builders overwrite its work. Nothing errored.
    THE REPOSITORY HAS A BUILD ORDER THAT NOTHING ENCODES - until this file, which encodes it
    as the topological order of the observed graph rather than as a list somebody maintains.

STALENESS IS CONTENT, NEVER TIME
A builder's fingerprint is a hash of its own source, the content of every input nothing else
produces, and - recursively - the fingerprints of the builders that produce its other inputs. So a
change anywhere upstream reaches everything downstream, and a fresh clone (which resets every
mtime) is not spuriously stale. build_cube.py currently derives `retrieved_at` from a file's
mtime, which is the defect class this project has already been bitten by; nothing here repeats it.

Hashing 3.6 GB of raw/ on every invocation would make the tool too slow to use, and a tool nobody
runs is not a guard. So content hashes are CACHED under a (size, mtime) key: if the stat matches,
the stored content hash is reused; if it does not, the file is re-read. The stat is a cache key
only - it never decides staleness, and a wrong stat costs a re-read, not a wrong answer.

WHAT IT REFUSES TO DO
- It will not run a builder that fetches from the network or costs API quota (NEVER_RUN below).
  A stale one of those is REPORTED and the run stops. A silent skip is how a stale cache ships.
- IT WILL NOT REBUILD A PAGE THE BUILDER IS BEHIND. Its first real run rebuilt eighteen builders
  correctly and produced eight pages that were WORSE than the published ones: no favicons, no
  skip-link, the old two-item navigation, and in one case a footer still carrying the repository's
  previous name. None of that lives in any builder - one commit on 28 Aug edited 244 pages and
  added no script, and headlines have been rewritten by hand since. So a rebuild is not obviously
  an improvement, and for 37 builders it is measurably a regression. Those are listed by name in
  _regressing_builders.json, measured by repro_audit.py, and refused here unless --force says
  otherwise. The list shrinks as builders are brought up to their pages; it is not a permanent
  exemption, it is a debt with names on it.
- It will not guess at a cycle. The graph has one real cycle and it is declared below, with the
  measurement that settles it.

Run:  python runner.py                 what is stale, in the order it would rebuild
      python runner.py --explain X     why X is stale
      python runner.py --run           rebuild the stale ones, in order
      python runner.py --from X        treat X as changed; show/run everything downstream
      python runner.py --accept        record the current tree as fresh, running nothing
      python runner.py --run --skip-held   rebuild only what is safe, and nothing fed by a held one
Out:  _runner_state.json (the baseline, committed) and _runner_cache.json (local, gitignored)
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
GRAPH = os.path.join(ROOT, 'out', 'graph.json')
STATE = os.path.join(ROOT, '_runner_state.json')     # the baseline: committed, shared
REGRESS = os.path.join(ROOT, '_regressing_builders.json')   # builders that no longer reproduce their page
CACHE = os.path.join(ROOT, '_runner_cache.json')     # (size, mtime) -> content hash: local, gitignored
#
# The two are separate on purpose. The fingerprints say WHICH TREE WAS BUILT and belong in git,
# so a fresh clone inherits the baseline. The hash cache is keyed on stat data that differs on
# every machine and changes on every checkout; committing it would churn the diff and teach
# nobody anything. A cold cache costs one full read, never a wrong answer.

# Never run by a rebuild: network fetchers and quota spenders. Same list as the recorder's, and
# for the same reason - except that here a stale one is a HARD STOP, not an omission. Rebuilding
# from a cache that is behind its source is exactly the hole build.py now refuses.
NEVER_RUN = ('backfill_', 'fetch_', 'refresh', 'pull_', 'download', 'record_graph',
             'check.py', 'scheduled_run', 'build_bgs_panel', 'runner.py', 'repro_audit.py', 'repro_triage.py', 'repro_worklist.py')

# COMPOSITION, not dependency. build_cube.py does `import build_cube_usgs` and calls .build(), so
# the audit hook attributes the callee's reads and writes to the caller as well. That makes the
# pair look mutually dependent when it is one program. Measured, not assumed: these are the only
# two composers in 268 builders, found by parsing imports.
CONTAINS = {
    'build_cube.py': ['build_cube_baci.py', 'build_cube_iea.py', 'build_cube_trade.py',
                      'build_cube_usgs.py', 'build_cube_wmd.py'],
    'build_nowcast_bootstrap.py': ['build_nowcast_models.py'],
}

# THE ONE REAL CYCLE. add_tonnes.py and build_flows_fix.py both read and both write
# out/flows_2024.json. Measured rather than reasoned about: run in either order, and run alone,
# each produces the byte-identical committed file (sha 8c3119ae). They have converged - the
# rebuild attaches the tonnage the attacher would have attached - so the cycle is harmless today
# and would not stay harmless silently: any divergence changes that hash and the harness sees it.
# Order declared the way the data flows: rebuild the file, then attach to it.
BREAK = [('add_tonnes.py', 'build_flows_fix.py'),   # (from, to) edges removed from the graph
         # add_head writes pages add_canonicals reads, so the recorder sees add_head ->
         # add_canonicals. The reverse is what reproduces the published head order (see ORDER
         # below), and both together are a cycle. The observed edge is the one to drop: these
         # two post-passes do not depend on each other's CONTENT at all - each inserts a tag
         # the other ignores - so the edge carries no information beyond 'they touch the same
         # files', while the declared one carries the reason.
         ('add_head.py', 'add_canonicals.py'),
         ('clean_links.py', 'add_canonicals.py'), ('clean_links.py', 'add_head.py')]

# EDGES THE GRAPH CANNOT OBSERVE, because an idempotent post-pass with nothing to do writes nothing
# and therefore has no recorded outputs to build an edge from.
#
# add_canonicals.py and add_head.py both anchor on `<meta charset="utf-8">` and insert immediately
# after it, so whichever runs LAST ends up closest to the charset. The published pages have the
# favicon block first and the canonical after it - which is what history produced: canonicals were
# injected first, then the 28 Aug favicon edit pushed them along. To reproduce a published page the
# rebuild has to make the same choice, so add_head runs last.
#
# Measured, not assumed: with add_head first, 34 pages that otherwise reproduce exactly came back
# byte-for-byte the same LENGTH and a different head order. Nothing was wrong with them; they simply
# were not the published file, and "not the published file" is the whole question I7 asks.
#
# This is a real weakness of an observed graph and is written here rather than hidden: a builder
# that DID something on the day it was recorded gets an edge, and one that found nothing to do does
# not. Only ordering is declared - never a read or a write.
ORDER = [('add_canonicals.py', 'add_head.py'),     # (first, second)
         # clean_links only rewrites hrefs, so it competes with neither of the other two for the
         # charset anchor; it is pinned last simply so the order is stated rather than emergent.
         ('add_head.py', 'clean_links.py')]

# The post-passes. They read every page and write every page, so they are downstream of EVERY page
# builder - including the held ones - and --skip-held's "do not rebuild anything fed by a held
# builder" rule therefore skipped them. It cost three live pages their favicon and their canonical
# within one run, which is the 129-page failure in miniature and was caught only by checking.
#
# The rule is right and the exception is right: it exists because a rebuild fed by a stale input
# bakes a stale NUMBER into a fresh output. These two read no numbers. They insert a tag and leave
# everything else alone, so a held builder's staleness cannot reach their output - and skipping
# them does active harm, which no other skip does.
POST_PASSES = ('add_canonicals.py', 'add_head.py', 'clean_links.py')


# A BUILD IS NOT REPRODUCIBLE WHILE SET ITERATION IS RANDOM.
# Python randomises string hashing per process, so any builder that iterates a set - or sorts by a
# value that ties and lets the input order decide - emits a different file every run. Measured, not
# assumed: build_trends.py and build_ot.py each produce three byte-identical outputs with the seed
# pinned, and a different output under a different seed. Eleven builders behave this way.
#
# This is the same fix as pinning gzip's mtime earlier today: the output was never about the data,
# and a build that cannot reproduce itself cannot be checked against anything. It is a floor, not
# an excuse - the eleven are named in _regressing_builders.json under `hash_seed_dependent`, so the
# fragility stays visible. A builder that needs a fixed seed to be stable would still shuffle under
# a different Python, and the real repair is a tiebreak at each site.
_ENV = dict(os.environ)
_ENV['PYTHONHASHSEED'] = '0'


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()[:20]


class Hasher:
    """Content hashes with a (size, mtime) cache. The stat is a cache key, never an answer."""

    def __init__(self, cache):
        self.cache = dict(cache or {})
        self.reads = 0
        self.hits = 0

    def file(self, rel):
        p = os.path.join(ROOT, rel)
        try:
            st = os.stat(p)
        except OSError:
            return None                                   # absent is a real state, not an error
        key = '%d:%d' % (st.st_size, int(st.st_mtime))
        got = self.cache.get(rel)
        if got and got[0] == key:
            self.hits += 1
            return got[1]
        h = hashlib.sha256()
        with open(p, 'rb') as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b''):
                h.update(chunk)
        d = h.hexdigest()[:20]
        self.cache[rel] = [key, d]
        self.reads += 1
        return d


def load_graph():
    g = json.load(io.open(GRAPH, encoding='utf-8'))['builders']
    return {b: v for b, v in g.items() if os.path.exists(os.path.join(ROOT, b))}


def never_run(b):
    return any(k in b for k in NEVER_RUN)


def graph_edges(g):
    """(producers, edges, back_edges_removed). A file's producer set drives every edge."""
    prod = {}
    for b, v in g.items():
        for w in v.get('writes', []):
            prod.setdefault(w, set()).add(b)
    contained = {c: owner for owner, cs in CONTAINS.items() for c in cs}
    edges, via, dropped = {}, {}, []
    for b, v in g.items():
        for r in v.get('reads', []):
            if r.endswith('/'):
                continue                                  # a directory listing is not a file edge
            for p in prod.get(r, ()):
                if p == b:
                    continue                              # a builder reading its own output
                if contained.get(p) == b or contained.get(b) == p:
                    dropped.append((p, b, 'composition'))  # one program, not two builders
                    continue
                if (p, b) in BREAK:
                    dropped.append((p, b, 'declared cycle break'))
                    continue
                edges.setdefault(p, set()).add(b)
                via.setdefault((p, b), []).append(r)
    for first, second in ORDER:
        if first in g and second in g:
            edges.setdefault(first, set()).add(second)
            via.setdefault((first, second), []).append('<declared order>')
    return prod, edges, via, dropped


def toposort(nodes, edges):
    """Kahn. Raises on a cycle: an undeclared cycle is a finding, not something to route around."""
    indeg = {n: 0 for n in nodes}
    for p, cs in edges.items():
        for c in cs:
            if c in indeg:
                indeg[c] += 1
    ready = sorted(n for n, d in indeg.items() if d == 0)
    out = []
    while ready:
        n = ready.pop(0)
        out.append(n)
        for c in sorted(edges.get(n, ())):
            if c in indeg:
                indeg[c] -= 1
                if indeg[c] == 0:
                    ready.append(c)
                    ready.sort()
    if len(out) != len(nodes):
        left = sorted(n for n in nodes if n not in set(out))
        raise SystemExit('CYCLE among %d builders, none of them declared in BREAK: %s'
                         % (len(left), ', '.join(left[:10])))
    return out


def fingerprints(g, prod, edges, order, hasher):
    """fp(b) = its code + the content of EVERY input + fp of every producer it reads.

    Computed in topological order, so a producer's fingerprint is always ready before its
    consumer asks for it. That is the whole reason the order is computed first.

    WHY THE PRODUCED FILES ARE HASHED TOO, AND NOT JUST THE PRODUCER'S FINGERPRINT
    The first version took a producer's fingerprint as a complete summary of its output, and that
    is false whenever a file on disk is older than the code that makes it. Found 12 Sep, on the
    germanium share again: out/capability_years.json had been stale for weeks, the baseline had
    been accepted with it stale, and re-running build_feedstock.py by hand fixed the FILE while
    changing nothing about its inputs or its code - so its fingerprint did not move, so
    build_refiners.py never learned, so refiners.html went on publishing the retracted 0.94.

    Both terms are kept because they catch different moments. The producer's fingerprint fires
    BEFORE it runs (its code or inputs changed, so everything downstream is about to change), and
    the content hash fires AFTER (the file on disk is not what the consumer last saw, however it
    got that way - a hand-run, a partial build, a checkout). Either alone leaves a hole.
    """
    fp, detail = {}, {}
    contained = {c: owner for owner, cs in CONTAINS.items() for c in cs}
    for b in order:
        parts = ['code:' + (hasher.file(b) or 'MISSING')]
        ins, ups = [], []
        for r in sorted(set(g[b].get('reads', []))):
            if r.endswith('/') or r == b:
                continue
            owners = {p for p in prod.get(r, ()) if p != b
                      and contained.get(p) != b and contained.get(b) != p
                      and (p, b) not in BREAK}
            if owners:
                for p in sorted(owners):
                    if p in fp:
                        ups.append((p, fp[p]))
                # AND the file itself: a producer's fingerprint describes its inputs, not the bytes
                # currently on disk, and those two disagree exactly when something was rebuilt out
                # of band. See the docstring.
                ins.append((r, hasher.file(r)))
            else:
                ins.append((r, hasher.file(r)))
        for r, h in sorted(set(ins)):
            parts.append('in:%s=%s' % (r, h))
        for p, h in sorted(set(ups)):
            parts.append('up:%s=%s' % (p, h))
        fp[b] = sha_bytes('\n'.join(parts).encode('utf-8'))
        detail[b] = {'inputs': sorted(set(ins)), 'upstream': sorted(set(ups))}
    return fp, detail


def load_state():
    st = {'fingerprints': {}, 'last_run': {}}
    if os.path.exists(STATE):
        try:
            st.update(json.load(io.open(STATE, encoding='utf-8')))
        except Exception:
            pass
    st['hash_cache'] = {}
    if os.path.exists(CACHE):
        try:
            st['hash_cache'] = json.load(io.open(CACHE, encoding='utf-8'))
        except Exception:
            pass
    return st


def save_state(st, hasher, fp):
    io.open(STATE, 'w', encoding='utf-8').write(json.dumps(
        {'note': 'Content fingerprints of the tree at its last accepted build. See runner.py.',
         'updated': time.strftime('%Y-%m-%d'),
         'fingerprints': st['fingerprints'], 'last_run': st.get('last_run', {})},
        indent=1, sort_keys=True))
    io.open(CACHE, 'w', encoding='utf-8').write(json.dumps(hasher.cache, sort_keys=True))


def downstream(edges, start):
    seen, work = set(), [start]
    while work:
        n = work.pop()
        for c in sorted(edges.get(n, ())):
            if c not in seen:
                seen.add(c)
                work.append(c)
    return seen


def main():
    a = sys.argv[1:]
    do_run = '--run' in a
    skip_held = '--skip-held' in a
    accept = '--accept' in a
    explain = a[a.index('--explain') + 1].strip() if '--explain' in a else None
    frm = a[a.index('--from') + 1].strip() if '--from' in a else None

    g = load_graph()
    prod, edges, via, dropped = graph_edges(g)
    order = toposort(sorted(g), edges)
    st = load_state()
    hasher = Hasher(st.get('hash_cache'))
    fp, detail = fingerprints(g, prod, edges, order, hasher)
    was = st.get('fingerprints', {})

    if explain:
        if explain not in fp:
            raise SystemExit('%r is not a recorded builder' % explain)
        print('%s\n  fingerprint  %s\n  last built   %s'
              % (explain, fp[explain], was.get(explain, 'NEVER')))
        d = detail[explain]
        print('  inputs nothing produces (%d):' % len(d['inputs']))
        for r, h in d['inputs'][:40]:
            print('    %-58s %s' % (r, h))
        print('  upstream builders (%d):' % len(d['upstream']))
        for p, h in d['upstream']:
            mark = '' if was.get(p) == h else '   <- CHANGED'
            print('    %-58s %s%s' % (p, h, mark))
        return 0

    if accept:
        st['fingerprints'] = fp
        save_state(st, hasher, fp)
        print('accepted %d builders as fresh (nothing was run)' % len(fp))
        print('hashed %d files, %d served from the stat cache' % (hasher.reads, hasher.hits))
        return 0

    stale = [b for b in order if was.get(b) != fp[b]]
    if frm:
        if frm not in fp:
            raise SystemExit('%r is not a recorded builder' % frm)
        want = downstream(edges, frm) | {frm}
        stale = [b for b in order if b in want]

    print('%d builders | %d edges | %d dropped (%s)'
          % (len(g), sum(len(v) for v in edges.values()), len(dropped),
             ', '.join(sorted({d[2] for d in dropped})) or 'none'))
    print('hashed %d files, %d served from the stat cache' % (hasher.reads, hasher.hits))
    if not stale:
        print('\nnothing is stale.')
        save_state(st, hasher, fp)
        return 0

    blocked = [b for b in stale if never_run(b)]
    regress, fed_by_held = [], []
    if os.path.exists(REGRESS):
        try:
            unsafe = set(json.load(io.open(REGRESS, encoding='utf-8'))['unsafe_to_run'])
            regress = [b for b in stale if b in unsafe]
            # Downstream of a held builder is ALSO blocked, and for a sharper reason than the held
            # one: its input is a file we know is behind, so rebuilding it would bake a stale number
            # into a fresh output and look like progress. Naming it separately matters - "behind its
            # page" is a debt someone has to pay, "fed by a held builder" clears itself the moment
            # the upstream one is paid.
            poisoned = set()
            for b in regress:
                poisoned |= downstream(edges, b)
            poisoned -= set(POST_PASSES) | set(regress)
            fed_by_held = [b for b in stale if b in poisoned]
        except Exception:
            regress, fed_by_held = [], []
    print('\n%d stale, in rebuild order:' % len(stale))
    for b in stale:
        why = 'never built' if b not in was else 'inputs or code changed'
        tag = ('   [WILL NOT RUN: network/quota]' if never_run(b)
               else '   [WILL NOT RUN: behind its published page]' if b in regress
               else '   [WILL NOT RUN: fed by a held builder]' if b in fed_by_held else '')
        print('   %-46s %s%s' % (b, why, tag))

    if not do_run:
        print('\nnothing was run. `python runner.py --run` rebuilds these in this order.')
        save_state(st, hasher, fp)
        return 0

    if regress and skip_held:
        # Rebuild what is safe and leave the rest alone - but do NOT rebuild anything DOWNSTREAM of
        # a held builder. Its input would be the old file, so the rebuild would bake a stale number
        # into a fresh output and look like progress. Refusing to run is honest; running with one
        # input knowingly wrong is not.
        poisoned = set()
        for b in regress:
            poisoned |= downstream(edges, b)
        poisoned -= set(POST_PASSES)
        held_all = sorted((set(regress) | (poisoned & set(stale))) - set(POST_PASSES))
        stale = [b for b in stale if b not in held_all]
        print('\n --skip-held: leaving %d builder(s) alone (%d behind their page, %d downstream '
              'of one):' % (len(held_all), len(regress), len(held_all) - len(regress)))
        for b in held_all:
            why = 'behind its published page' if b in regress else 'fed by a held builder'
            print('   %-46s %s' % (b, why))
        held_names = set(held_all)
        if not stale:
            print('\nnothing left to rebuild.')
            save_state(st, hasher, fp)
            return 0
        print('\n rebuilding the %d that are safe:' % len(stale))
    elif regress and '--force' not in a:
        print('\n REFUSING to run: %d of these are behind the page they publish, and rebuilding'
              ' would overwrite it with less than it has now:' % len(regress))
        for b in regress:
            print('   %s' % b)
        print('See _regressing_builders.json for what differs, and repro_audit.py to re-measure.')
        print('`--force` overrides, and you should expect to lose published work if you use it.')
        return 3
    if blocked:
        # A fetcher cannot be rebuilt by a rebuilder. Saying so and stopping is the whole point:
        # the alternative is building on a cache that is behind its source, which this repository
        # has already shipped once.
        print('\nREFUSING to run: %d of these fetch from the network or cost API quota:' % len(blocked))
        for b in blocked:
            print('   %s' % b)
        print('Run them yourself, then re-run the runner.')
        return 2

    ok = 0
    for n, b in enumerate(stale, 1):
        t0 = time.time()
        p = subprocess.run([sys.executable, b], cwd=ROOT, capture_output=True, text=True,
                           env=_ENV)
        secs = time.time() - t0
        if p.returncode != 0:
            print(' ! [%2d/%2d] %-44s FAILED in %.1fs' % (n, len(stale), b, secs))
            print((p.stderr or '')[-600:])
            print('\nSTOPPED. %d rebuilt, %d not attempted. Nothing downstream of a failure is '
                  'rebuilt on a guess.' % (ok, len(stale) - n))
            save_state(st, hasher, fp)
            return 1
        print('   [%2d/%2d] %-44s ok %.1fs' % (n, len(stale), b, secs))
        ok += 1
        st.setdefault('last_run', {})[b] = time.strftime('%Y-%m-%d %H:%M')

    # Re-fingerprint AFTER the run: the builders just changed their outputs, so the inputs of
    # everything downstream have moved and the stored fingerprint must describe the new tree.
    hasher2 = Hasher(hasher.cache)
    fp2, _ = fingerprints(g, prod, edges, order, hasher2)
    # A builder that was SKIPPED keeps its old fingerprint, so it stays stale. Blessing it here
    # would mean a run that deliberately did not rebuild something reported it as rebuilt - and the
    # gate would go green over a page we know is behind its builder. The debt has names; it does
    # not get to disappear because a different builder ran.
    held_names = locals().get('held_names') or set()
    st['fingerprints'] = {b: (was.get(b, v) if b in held_names else v) for b, v in fp2.items()}
    save_state(st, hasher2, fp2)
    print('\nrebuilt %d in dependency order.' % ok)
    return 0


if __name__ == '__main__':
    sys.exit(main())
