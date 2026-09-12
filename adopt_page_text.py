# -*- coding: utf-8 -*-
"""Teach each builder the headline and deck its own page already publishes. Dry-run by default.

THE SHAPE OF THE REMAINING DEBT
After the menu, the footer and the skip-link were repaired mechanically, what was left under the
label "content" turned out to be narrow and repetitive: somebody improved a headline on the page and
never carried it back into the builder. demand.html says "The squeeze falls on gallium, germanium,
vanadium" while build_demand.py still writes "The squeeze"; the deck underneath was rewritten the
same way. The builder is not wrong, it is OLD, and the page is the better copy.

So the repair is to move the text the other way for once: the page keeps what it says, and the
builder learns it.

WHAT IT REFUSES TO TOUCH, AND WHY
  a heading the builder composes    if the builder's own text contains {placeholders} or an f-string
                                    brace, replacing it with flat text would freeze a value that is
                                    supposed to vary per build. Reported, never rewritten.
  a heading that is not a literal   if the current text cannot be found verbatim in the builder's
                                    source, there is nothing to replace and guessing where it came
                                    from is how a machine invents code.
  more than one candidate           if the builder's text appears twice in its source, which one is
                                    the heading is not knowable from here.
  a builder writing many pages      one template cannot hold two different headlines.

Run:  python adopt_page_text.py            # report
      python adopt_page_text.py --apply    # write
"""
import io
import json
import os
import re
import subprocess
import sys

try:                                   # a Windows console is cp1252 and these headlines are not
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
FIELDS = (('h1', re.compile(r'<h1[^>]*>(.*?)</h1>', re.S)),
          ('deck', re.compile(r'<p class="deck"[^>]*>(.*?)</p>', re.S)))


def committed(p):
    r = subprocess.run(['git', 'show', 'HEAD:' + p], capture_output=True, cwd=ROOT)
    return r.stdout.replace(b'\r\n', b'\n').decode('utf-8', 'replace') if r.returncode == 0 else ''


def main():
    apply = '--apply' in sys.argv
    reg = json.load(io.open(os.path.join(ROOT, '_regressing_builders.json'), encoding='utf-8'))
    g = json.load(io.open(os.path.join(ROOT, 'out', 'graph.json'), encoding='utf-8'))['builders']

    done, skipped = [], []
    for b in sorted(reg['unsafe_to_run']):
        if not os.path.exists(b):
            continue
        pages = [w for w in g.get(b, {}).get('writes', ()) if w.endswith('.html')]
        if len(pages) != 1:
            skipped.append((b, 'writes %d pages; one template cannot hold several headlines' % len(pages)))
            continue
        page = committed(pages[0])
        src = io.open(b, encoding='utf-8').read()
        edits = []
        for name, pat in FIELDS:
            pm = pat.search(page)
            bm = pat.search(src)
            if not pm or not bm:
                continue
            want, have = pm.group(1).strip(), bm.group(1).strip()
            if want == have:
                continue
            if '{' in have or '}' in have:
                skipped.append((b, '%s is composed, not a literal: %s' % (name, have[:60])))
                continue
            if src.count(have) != 1:
                skipped.append((b, '%s appears %d times in the source' % (name, src.count(have))))
                continue
            edits.append((name, have, want))
        if not edits:
            continue
        new = src
        for _, have, want in edits:
            new = new.replace(have, want, 1)
        if apply:
            io.open(b, 'w', encoding='utf-8', newline='').write(new)
            import ast
            try:
                ast.parse(io.open(b, encoding='utf-8').read())
            except SyntaxError as e:
                io.open(b, 'w', encoding='utf-8', newline='').write(src)
                skipped.append((b, 'REVERTED, would not parse: %s' % str(e)[:60]))
                continue
        done.append((b, [(n, h[:50], w[:50]) for n, h, w in edits]))

    print('builders that can adopt their page text: %d' % len(done))
    for b, edits in done:
        print('  %s' % b)
        for n, h, w in edits:
            print('      %-5s %r' % (n, h))
            print('      %-5s -> %r' % ('', w))
    if skipped:
        print('\nleft for a person (%d):' % len(skipped))
        for b, why in skipped:
            print('  %-34s %s' % (b, why))
    if not apply:
        print('\nnothing was written. --apply writes.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
