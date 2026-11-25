#!/usr/bin/env python3
"""
Guard for a wording-only edit (the calm pass, 25 Nov 2026).

    python prose_guard.py page.html [page2.html ...]      compare each page with its committed version

A plain-style rewrite may change words, never facts. For each page it compares the committed version
(git HEAD) with the working copy and FAILS if any of these changed:
  - the multiset of numbers in the visible text (years, shares, counts, values);
  - the set of link targets (".html" ignored, as clean_links.py strips it);
  - the text of every h1, h2 and h3 (headings are decided separately);
  - the <title>.
It also reports the em-dashes in running text, before and after. Not a builder (runner skips it).
"""
import collections
import html
import re
import subprocess
import sys


def visible(s):
    s = re.sub(r'<(script|style)\b.*?</\1>', ' ', s, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', ' ', s))


def facts(s):
    t = visible(s)
    nums = collections.Counter(re.findall(r'\d+(?:[.,]\d+)*', t))
    # links in the page text only: <head> links and the skip link are added by the post-processors
    links = {re.sub(r'\.html(?=$|[#?])', '', h) for h in re.findall(r'<a[^>]*?href="([^"]*)"', s)} - {'#main'}
    heads = [re.sub(r'\s+', ' ', visible(h)).strip() for h in re.findall(r'<h[123]\b[^>]*>(.*?)</h[123]>', s, re.S)]
    title = re.findall(r'<title>(.*?)</title>', s, re.S)
    prose = ' '.join(visible(x) for x in re.findall(r'<(?:p|li)\b[^>]*>(.*?)</(?:p|li)>',
                                                       re.sub(r'<(script|style|table)\b.*?</\1>', ' ', s, flags=re.S), re.S))
    return nums, links, heads, title, prose.count('—')


def main(paths):
    bad = 0
    for p in paths:
        old = subprocess.run(['git', 'show', 'HEAD:' + p], capture_output=True).stdout.decode('utf-8', 'replace')
        new = open(p, encoding='utf-8', errors='replace').read()
        if not old:
            print('%-34s not in HEAD - skipped' % p); continue
        (n0, l0, h0, t0, d0), (n1, l1, h1, t1, d1) = facts(old), facts(new)
        errs = []
        if n0 != n1:
            errs.append('numbers changed: lost %s, gained %s' % (dict(n0 - n1), dict(n1 - n0)))
        if l0 != l1:
            errs.append('links changed: lost %s, gained %s' % (sorted(l0 - l1)[:5], sorted(l1 - l0)[:5]))
        if h0 != h1:
            errs.append('headings changed: %s' % [(a, b) for a, b in zip(h0, h1) if a != b][:3] if len(h0) == len(h1)
                        else 'heading count changed %d -> %d' % (len(h0), len(h1)))
        if t0 != t1:
            errs.append('title changed')
        print('%-34s dashes %3d -> %3d  %s' % (p, d0, d1, 'OK' if not errs else 'FAIL'))
        for e in errs:
            print('      ' + e)
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
