# -*- coding: utf-8 -*-
"""Open every page the way a reader does, and fail on what a reader would see broken.

WHY THIS EXISTS
check.py reads files. It cannot see a page that fills itself in the browser from a JSON file, and that
is where four pages were broken for months without any check noticing (found 22 Nov 2026, the first by
an outside review, the other three by the first run of this script):

  robustness.html        empty table, "Of the undefined materials"   - two builders shared an output file
  limitations.html       "undefined of undefined", three times        - the same file
  cascade.html           "undefined" in the rank column               - the page read a field never written
  demand.html            a table and two notes that never appeared    - a script error stopped the page
  price-volatility.html  "r=undefined (p=undefined)"                  - its input field had been removed

Every one of them looked correct in the HTML source: the static text carried a sensible fallback and
the script overwrote it. Only a real browser shows it.

WHAT IT CHECKS, on every .html page of the site, after the page's scripts have finished:
  - the rendered text contains the word undefined, NaN or [object Object]
  - a script error was thrown
  - the page asked this site for a file and did not get it
  - a visible table with a body has no rows

Extensionless addresses are served as their .html file, as the live host does.

Run:   python check_rendered.py            every page
       python check_rendered.py demand     only pages whose name starts with "demand"
Exit code 1 when anything is found. Needs the playwright package and a Chromium-family browser;
without them it says so and exits 2 - it never reports a pass it did not earn.
"""
import functools
import glob
import http.server
import json
import os
import re
import sys
import threading

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = ('raw', 'node_modules', 'pipeline')
BAD = re.compile(r'\b(undefined|NaN)\b|\[object Object\]')

# A page may legitimately print one of the words (prose about an "undefined" quantity). List it here
# with the reason, as  'page.html': 'reason'.  Empty on purpose: nothing needs it today.
ALLOW_WORD = {}


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def translate_path(self, path):
        p = super().translate_path(path)
        if not os.path.exists(p) and os.path.exists(p + '.html'):
            return p + '.html'
        return p


def pages(prefix):
    found = glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, '*', '*.html'))
    out = sorted(os.path.relpath(p, ROOT).replace('\\', '/') for p in found)
    out = [p for p in out if not p.startswith('_') and p.split('/')[0] not in SKIP_DIRS]
    return [p for p in out if p.startswith(prefix)] if prefix else out


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('--')]
    prefix = names[0] if names else None
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('check_rendered: the playwright package is not installed. NOTHING WAS CHECKED.')
        return 2
    todo = pages(prefix)
    if not todo:
        print('check_rendered: no page matches %r. NOTHING WAS CHECKED.' % prefix)
        return 2
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d' % srv.server_address[1]
    found = {}
    with sync_playwright() as p:
        browser = None
        for kw in ({'channel': 'msedge'}, {'channel': 'chrome'}, {}):
            try:
                browser = p.chromium.launch(headless=True, **kw)
                break
            except Exception:
                continue
        if browser is None:
            print('check_rendered: no browser could be started. NOTHING WAS CHECKED.')
            return 2
        ctx = browser.new_context()
        for name in todo:
            pg = ctx.new_page()
            errs, missing = [], []
            pg.on('pageerror', lambda e, errs=errs: errs.append(str(e)[:160]))
            pg.on('response', lambda r, missing=missing: missing.append(
                '%d %s' % (r.status, r.url[len(base):])) if r.status >= 400 and r.url.startswith(base) else None)
            try:
                pg.goto(base + '/' + name, wait_until='networkidle', timeout=45000)
                text = pg.evaluate('document.body ? document.body.innerText : ""')
                empty = pg.evaluate(
                    "[...document.querySelectorAll('table')].filter(t=>t.tBodies.length && "
                    "t.tBodies[0].rows.length===0 && t.offsetParent!==null).map(t=>t.id||'(no id)')")
            except Exception as e:
                text, empty = '', []
                errs.append('did not load: ' + str(e)[:120])
            words = [] if name in ALLOW_WORD else [
                text[max(0, m.start() - 50):m.end() + 30].replace('\n', ' ') for m in BAD.finditer(text)]
            if words or errs or missing or empty:
                found[name] = {'words': words, 'errors': errs, 'missing': missing, 'empty_tables': empty}
            pg.close()
        browser.close()
    srv.shutdown()
    for name, f in found.items():
        print('\n' + name)
        if f['words']:
            print('   prints undefined / NaN %d time(s), e.g.: ...%s...' % (
                len(f['words']), f['words'][0].encode('ascii', 'replace').decode()))
        for e in f['errors'][:3]:
            print('   script error: ' + e.encode('ascii', 'replace').decode())
        for m in f['missing'][:5]:
            print('   asked for a file it did not get: ' + m)
        if f['empty_tables']:
            print('   table with no rows: ' + ', '.join(f['empty_tables']))
    print('\ncheck_rendered: %d pages opened, %d with something broken.' % (len(todo), len(found)))
    if '--json' in sys.argv:
        json.dump(found, sys.stdout, indent=1)
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
