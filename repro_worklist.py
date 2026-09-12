# -*- coding: utf-8 -*-
"""For every held builder: the exact text the page has and the builder writes instead.

The triage priced the debt. This itemises it, because "the builder is behind its page" is not
actionable and "the page says X where the builder writes Y, and Y is a literal on line N" is.

For each page it pairs up what changed: the block the page carries against the block the builder
produces in the same position. Where the builder's side appears VERBATIM in its own source, the
repair is a string replacement and the line is reported as such. Where it does not - because the
text is assembled from variables, or the page carries something with no counterpart at all - it is
reported as needing a human, and that distinction is the whole point of the file.

Nothing is edited here. This only writes the worklist.

Run:  python repro_worklist.py [--only PREFIX]
Out:  out/repro_worklist.json
"""
import difflib
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import record_graph as rg                                       # noqa: E402

POST = ('add_canonicals.py', 'add_head.py', 'clean_links.py')
OUT = os.path.join(ROOT, 'out', 'repro_worklist.json')


def committed(p):
    r = subprocess.run(['git', 'show', 'HEAD:' + p], capture_output=True, cwd=ROOT)
    return r.stdout if r.returncode == 0 else b''


def text(b):
    return b.replace(b'\r\n', b'\n').decode('utf-8', 'replace')


def main():
    a = sys.argv[1:]
    only = a[a.index('--only') + 1].strip() if '--only' in a else None
    reg = json.load(io.open(os.path.join(ROOT, '_regressing_builders.json'), encoding='utf-8'))
    held = [b for b in reg['unsafe_to_run'] if not only or b.startswith(only)]
    g = json.load(io.open(os.path.join(ROOT, 'out', 'graph.json'), encoding='utf-8'))['builders']

    work, n_fix, n_human = {}, 0, 0
    for i, b in enumerate(sorted(held), 1):
        if not os.path.exists(b):
            continue
        src = io.open(b, encoding='utf-8', errors='replace').read()
        pages = [w for w in g.get(b, {}).get('writes', ()) if w.endswith('.html')]
        w = list(rg.run(b, 900).get('writes', []))
        for s in POST:
            w += rg.run(s, 900).get('writes', [])
        items = []
        for p in pages:
            try:
                now = text(io.open(os.path.join(ROOT, p), 'rb').read())
            except OSError:
                continue
            was = text(committed(p))
            if was == now:
                continue
            sm = difflib.SequenceMatcher(None, was, now, autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == 'equal':
                    continue
                page_side = was[i1:i2]
                built_side = now[j1:j2]
                if len(page_side) < 4 and len(built_side) < 4:
                    continue                       # punctuation-level noise
                # Can it be repaired by editing the builder's own source?
                key = built_side.strip()
                fixable = bool(key) and len(key) > 8 and key in src
                items.append({'page': p, 'page_has': page_side[:400],
                              'builder_writes': built_side[:400],
                              'builder_literal': fixable})
                n_fix += fixable
                n_human += not fixable
        rg.restore(w)
        work[b] = items
        kinds = sum(1 for x in items if x['builder_literal'])
        print('  [%2d/%2d] %-34s %2d difference(s), %d editable as a literal'
              % (i, len(held), b[:34], len(items), kinds), flush=True)

    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
        {'note': 'What each held builder would have to change to reproduce its page.',
         'totals': {'differences': n_fix + n_human, 'editable_literal': n_fix,
                    'needs_a_person': n_human},
         'builders': work}, indent=1, ensure_ascii=False))
    print('\n%d differences: %d are a literal in the builder, %d are not'
          % (n_fix + n_human, n_fix, n_human))
    print('wrote out/repro_worklist.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
