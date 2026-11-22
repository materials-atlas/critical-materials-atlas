# -*- coding: utf-8 -*-
"""Set every <lastmod> in sitemap.xml to the day its page last changed.

WHY. sitemap.xml is written by hand and its dates were never touched again: on 22 Nov 2026, 211 of its
215 entries carried a date older than the page's last change, most of them 16 Aug 2026. A search engine
that finds the dates wrong stops reading them.

THE RULE. A page's date is the day of the last commit that touched its file; a page that is changed
but not yet committed gets today. Nothing else in the sitemap is touched: no entry is added, removed or
re-ordered - which pages are listed stays a decision made by hand.

This is not a builder (its answer depends on the repository's history, not on the data), so it is not
in the build graph. Run it before a push:   python update_sitemap_dates.py
"""
import datetime
import io
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://criticalmaterialsatlas.org/'


def git(*args):
    return subprocess.run(('git',) + args, cwd=ROOT, capture_output=True, text=True, check=True).stdout


def main():
    last, day = {}, None
    for line in git('log', '--format=@%cs', '--name-only', '--', '*.html').splitlines():
        if line.startswith('@'):
            day = line[1:]
        elif line.strip():
            last.setdefault(line.strip(), day)
    today = datetime.date.today().isoformat()
    for line in git('status', '--porcelain', '--', '*.html').splitlines():
        last[line[3:].strip().strip('"')] = today

    path = os.path.join(ROOT, 'sitemap.xml')
    text = io.open(path, encoding='utf8', newline='').read()
    changed, unknown = [0], []

    def fix(m):
        route = m.group(1)
        d = last.get((route or 'index') + '.html')
        if d is None:
            unknown.append(route)
            return m.group(0)
        if d != m.group(2):
            changed[0] += 1
        return '<loc>%s%s</loc><lastmod>%s</lastmod>' % (SITE, route, d)

    new, n = re.subn(r'<loc>%s([^<]*)</loc><lastmod>([^<]*)</lastmod>' % re.escape(SITE), fix, text)
    if new != text:
        io.open(path, 'w', encoding='utf8', newline='').write(new)
    print('sitemap.xml: %d entries, %d dates changed.' % (n, changed[0]))
    if unknown:
        print('NO FILE IN THE HISTORY for: ' + ', '.join(unknown) + '  - left as they were. Look at them.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
