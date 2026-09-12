# -*- coding: utf-8 -*-
"""Make the site link to itself the way its own canonical tags say it should. Idempotent.

THE INCONSISTENCY
GitHub Pages serves every /foo.html also at the extensionless /foo, and add_canonicals.py has been
declaring the CLEAN form as canonical on all 286 pages since early September. But 71 pages still
link to each other with the .html ending - so the site tells search engines "the real address is
/method" and then links to /method.html everywhere on the page. Both work for a reader; only one is
the address we claim. Two URLs for one page with no declared owner is the exact condition
add_canonicals exists to remove, arriving from the other direction.

WHAT IT WILL NOT REWRITE, AND WHY EACH ONE MATTERS
  absolute URLs (http:, //)          another site's addressing is not ours to normalise
  a target with no .html file        if foo.html is not on disk, /foo is not served, and the link
                                     would break. Existence is checked per link, not assumed.
  anything outside an href="..."     a path inside a script string or a data attribute may be used
                                     for something other than navigation, and rewriting it could
                                     change behaviour rather than presentation
  #fragments and ?queries            preserved exactly, appended after the trimmed path
  out/, raw/, extract/, share/       generated data, inputs, and social cards that are fetched by
                                     path rather than navigated to

It writes by default, with --dry-run to inspect, for the same reason add_head.py does: runner.py
invokes builders with no arguments, so a post-pass that needed a flag would be called on every
rebuild and change nothing - a step that looks present and does nothing.

Run:  python clean_links.py            # writes
      python clean_links.py --dry-run  # report only
"""
import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
EXCLUDE_DIRS = ('node_modules', '.git', '__pycache__', 'out', 'sources', 'fixtures', 'raw',
                'extract', 'templates', 'share')
# href="path.html" or href="path.html#frag" / href="path.html?q" - not absolute, not a fragment
LINK = re.compile(r'(href=")(?!https?:|//|#|mailto:|data:)([^"#?]+)\.html((?:#|\?)[^"]*)?(")')


def pages():
    out = []
    for p in glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True):
        rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
        if any(part in EXCLUDE_DIRS for part in rel.split('/')[:-1]):
            continue
        out.append(rel)
    return sorted(out)


def main():
    apply = '--dry-run' not in sys.argv
    touched, rewritten, kept_missing = [], 0, set()

    for rel in pages():
        path = os.path.join(ROOT, rel)
        try:
            raw = io.open(path, 'rb').read()
        except OSError:
            continue
        crlf = b'\r\n' in raw
        text = raw.decode('utf-8', 'replace')
        n = [0]

        def sub(m):
            pre, target, tail, post = m.group(1), m.group(2), m.group(3) or '', m.group(4)
            # Resolve the target relative to the page that links it, and only trim the extension
            # when the file is really there - an extensionless URL for a file that does not exist
            # is a 404 where a working link used to be.
            base = os.path.dirname(os.path.join(ROOT, rel))
            if not os.path.isfile(os.path.join(base, target + '.html')):
                kept_missing.add(target + '.html')
                return m.group(0)
            n[0] += 1
            return pre + target + tail + post

        new = LINK.sub(sub, text)
        if n[0] and new != text:
            rewritten += n[0]
            touched.append((rel, n[0]))
            if apply:
                out = new.encode('utf-8')
                if crlf:
                    out = out.replace(b'\n', b'\r\n').replace(b'\r\r\n', b'\r\n')
                io.open(path, 'wb').write(out)

    print('%d pages scanned' % len(pages()))
    print('  links rewritten : %d' % rewritten)
    print('  pages changed   : %d' % len(touched))
    for rel, k in touched[:6]:
        print('      %-34s %d link(s)' % (rel, k))
    if len(touched) > 6:
        print('      ... and %d more pages' % (len(touched) - 6))
    if kept_missing:
        print('  LEFT ALONE - no such file, so the clean URL would 404 (%d): %s'
              % (len(kept_missing), ', '.join(sorted(kept_missing)[:6])))
    if not apply:
        print('\n--dry-run: nothing was written.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
