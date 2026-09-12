# -*- coding: utf-8 -*-
"""What would it cost to clear each held builder? Measure before touching any of them.

_regressing_builders.json names the builders that are behind the page they publish. The name alone
does not say whether clearing it is a one-line fix or a week of editorial work, and the first one
cleared (build_profiles.py) turned out to be three separate problems wearing one label. So this
classifies every remaining one by the KIND of difference, which is what decides the cost:

  exact          the builder already reproduces the page; the entry is stale and can be dropped
  data-only      same tag skeleton, different numbers - the page is behind the data, and a rebuild
                 IS the fix. Cheap and safe.
  unstable       the builder disagrees with ITSELF across two runs. Must be made deterministic
                 before anything else can be judged, because "different" is meaningless until then.
  reordered      same text content, different order - a tie sorted over an unordered collection.
                 A tiebreak away.
  content        the page carries text the builder does not produce. Somebody edited the page by
                 hand, and no machine can guess it back. This is the expensive kind.

Every builder is run with ALL THREE post-passes, in the order runner.ORDER declares, because that is
what the build actually does - the first audit ran builders alone and called 35 pages broken that
were not.

Run:  python repro_triage.py [--only PREFIX]
Out:  out/repro_triage.json + a summary
"""
import collections
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import record_graph as rg                                        # noqa: E402

POST = ('add_canonicals.py', 'add_head.py', 'clean_links.py')
OUT = os.path.join(ROOT, 'out', 'repro_triage.json')


def committed(p):
    r = subprocess.run(['git', 'show', 'HEAD:' + p], capture_output=True, cwd=ROOT)
    return r.stdout if r.returncode == 0 else None


def n(b):
    return b'' if b is None else b.replace(b'\r\n', b'\n')


def skeleton(t):
    return re.sub(r'>[^<]*<', '><', t)


def tokens(t):
    return collections.Counter(re.findall(r'>([^<>]{2,120})<', t))


def build_once():
    w = []
    for s in POST:
        w += rg.run(s, 900).get('writes', [])
    return w


def main():
    a = sys.argv[1:]
    only = a[a.index('--only') + 1].strip() if '--only' in a else None
    reg = json.load(io.open(os.path.join(ROOT, '_regressing_builders.json'), encoding='utf-8'))
    held = [b for b in reg['unsafe_to_run'] if not only or b.startswith(only)]
    g = json.load(io.open(os.path.join(ROOT, 'out', 'graph.json'), encoding='utf-8'))['builders']

    print('triaging %d held builders (builder + %d post-passes each)\n' % (len(held), len(POST)),
          flush=True)
    res, tally = {}, collections.Counter()
    for i, b in enumerate(sorted(held), 1):
        outs = [w for w in g.get(b, {}).get('writes', ()) if w.endswith('.html')]
        if not outs:
            res[b] = {'verdict': 'no page', 'pages': {}}
            tally['no page'] += 1
            continue
        # run twice, so self-disagreement is separable from disagreement with the page
        snaps, writes = [], []
        for _ in range(2):
            r = rg.run(b, 900)
            writes += r.get('writes', [])
            writes += build_once()
            snaps.append({p: n(io.open(os.path.join(ROOT, p), 'rb').read())
                          if os.path.exists(os.path.join(ROOT, p)) else b'' for p in outs})
        rg.restore(writes)

        pages, worst = {}, 'exact'
        rank = {'exact': 0, 'data-only': 1, 'reordered': 2, 'unstable': 3, 'content': 4}
        for p in outs:
            was, r1, r2 = n(committed(p)), snaps[0][p], snaps[1][p]
            if r1 != r2:
                k = 'unstable'
            elif r1 == was:
                k = 'exact'
            else:
                A = was.decode('utf-8', 'replace')
                B = r1.decode('utf-8', 'replace')
                ta, tb = tokens(A), tokens(B)
                if skeleton(A) == skeleton(B):
                    k = 'data-only'
                elif ta == tb:
                    k = 'reordered'
                elif (ta - tb):
                    k = 'content'          # the page says things the builder does not
                else:
                    k = 'data-only'
            pages[p] = k
            if rank[k] > rank[worst]:
                worst = k
        res[b] = {'verdict': worst, 'pages': pages}
        tally[worst] += 1
        print('  [%2d/%2d] %-40s %-10s %s' % (i, len(held), b[:40], worst,
              collections.Counter(pages.values()).most_common()), flush=True)

    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
        {'note': 'Cost of clearing each held builder. See repro_triage.py.',
         'tally': dict(tally), 'builders': res}, indent=1, sort_keys=True))
    print('\n' + json.dumps(dict(tally), indent=1))
    print('wrote out/repro_triage.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
