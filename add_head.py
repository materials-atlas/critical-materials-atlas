# -*- coding: utf-8 -*-
"""The post-pass that should have existed since 28 August. Idempotent, and it writes.

WHAT IT IS FIXING
On 28 Aug a commit edited 244 published pages to add the Google-recommended favicon set, and added
no script. Another added a skip-link. Both improved the site and neither is reproducible: a builder
that regenerates its page emits none of it, so re-running any of those builders silently deletes
work. That is the same defect as the 129 pages the recorder degraded in phase 1 - a build step that
exists only as an action somebody once took.

Measured 11 Sep across 287 published pages: 194 carried the favicon block and 93 did not; 191
carried the skip-link and 96 did not. The gap was not random - pages built after the bulk edit never
received it, so the newest work on the site was the least equipped for search results and for
keyboard navigation. Run 12 Sep with the owner's go: favicons now on 285 of 287, skip-links on 195.

THE FIRST RUN IMMEDIATELY PROVED WHY THIS MUST BE A BUILD STEP.
Applying it changed 92 pages. Then the runner rebuilt three builders whose inputs those pages are,
one of them build_scheme.py - and project-scheme.html came back out WITHOUT the favicon block,
because its builder does not emit one and this post-pass had already run. One page, undone within
the minute, by exactly the mechanism that lost 129 pages in phase 1: a step that exists only as
something somebody runs at the right moment. So it is in the recorded graph now, and runner.py
orders it after the page builders instead of trusting anyone to remember.

WHAT IT DOES, AND WHAT IT DELIBERATELY DOES NOT
  favicons     inserted straight after <meta charset>, in the same order and form as the 244 pages
               that already have them, so a page cannot be told apart from one edited by hand.
  skip-link    inserted as the first element of <body> - but ONLY where the page actually has an
               element with id="main" to skip to. A skip-link pointing at nothing is worse than no
               skip-link: it announces an accessibility feature to a screen reader and then does
               not work. Pages without a target are reported, not patched.

It does not touch navigation, footers or headlines. Those also drift from what builders emit, but
they are CONTENT: which links belong in the nav is an editorial decision, and a script that guesses
at it would be inventing rather than restoring.

Run it as a post-pass, after the page builders and beside add_canonicals.py:
    python add_head.py            # writes, like add_canonicals.py does
    python add_head.py --dry-run  # report what would change, touch nothing

It writes by default DELIBERATELY. runner.py invokes builders with no arguments, so a post-pass
that needed a flag would be called on every rebuild and change nothing - a step that looks present
and does nothing, which is this project's most persistent defect. It was dry only until the owner
approved its first run over 92 live pages, which happened on 12 Sep.
"""
import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_FILES = {'404.html'}
EXCLUDE_DIRS = ('node_modules', '.git', '__pycache__', 'out', 'sources', 'fixtures', 'raw',
                'extract', 'templates')

# Verbatim from the pages the 28 Aug commit produced. Copied, not re-invented: a second variant of
# the same block would be a new inconsistency wearing the costume of a fix.
FAVICONS = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">'
            '<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png">'
            '<link rel="icon" type="image/png" sizes="96x96" href="/favicon-96.png">'
            '<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48.png">'
            '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">'
            '<link rel="icon" href="/favicon.ico" sizes="any">'
            '<link rel="apple-touch-icon" href="/apple-touch-icon.png">')
SKIPLINK = '<a class="skip" href="#main">Skip to content</a>'

HAS_FAV = re.compile(r'<link[^>]+href="/favicon-192\.png"', re.I)
HAS_SKIP = re.compile(r'<a[^>]+class="skip"', re.I)
CHARSET = re.compile(r'(<meta charset="?utf-8"?\s*/?>)', re.I)
BODY = re.compile(r'(<body[^>]*>)', re.I)
MAIN_TARGET = re.compile(r'id="main"', re.I)


def pages():
    out = []
    for p in glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True):
        rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
        if os.path.basename(rel) in SKIP_FILES:
            continue
        if any(part in EXCLUDE_DIRS for part in rel.split('/')[:-1]):
            continue
        out.append(rel)
    return sorted(out)


def main():
    apply = '--dry-run' not in sys.argv
    added_fav = added_skip = 0
    no_target = []
    no_anchor = []
    touched = []
    for rel in pages():
        path = os.path.join(ROOT, rel)
        try:
            raw = io.open(path, 'rb').read()
        except OSError:
            continue
        crlf = b'\r\n' in raw
        text = raw.decode('utf-8', 'replace')
        before = text
        if not HAS_FAV.search(text):
            m = CHARSET.search(text)
            if m:
                text = text[:m.end()] + FAVICONS + text[m.end():]
                added_fav += 1
            else:
                no_anchor.append(rel)
        if not HAS_SKIP.search(text):
            if MAIN_TARGET.search(text):
                m = BODY.search(text)
                if m:
                    text = text[:m.end()] + '\n' + SKIPLINK + text[m.end():]
                    added_skip += 1
                else:
                    no_anchor.append(rel)
            else:
                no_target.append(rel)
        if text != before:
            touched.append(rel)
            if apply:
                out = text.encode('utf-8')
                if crlf:
                    out = out.replace(b'\n', b'\r\n').replace(b'\r\r\n', b'\r\n')
                io.open(path, 'wb').write(out)

    n = len(pages())
    print('%d published pages scanned' % n)
    print('  favicons added   : %d' % added_fav)
    print('  skip-links added : %d' % added_skip)
    print('  pages changed    : %d' % len(touched))
    if no_target:
        print('  NO SKIP TARGET (left alone, they have no id="main"): %d' % len(no_target))
        for r in no_target[:8]:
            print('      %s' % r)
        if len(no_target) > 8:
            print('      ... and %d more' % (len(no_target) - 8))
    if no_anchor:
        print('  NO INSERTION POINT (no <meta charset> or no <body>): %d  %s'
              % (len(no_anchor), ', '.join(sorted(set(no_anchor))[:5])))
    if not apply:
        print('\n--dry-run: nothing was written.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
