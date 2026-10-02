#!/usr/bin/env python3
"""Build out/search-index.json — the header-search index (Phase-2 IA). One record per user-facing
page: clean URL, title, short description, and a group tag. Powers the persistent search box in
assets/nav.js, the real replacement for a 58-link mega-menu. Run: python build_search_index.py

WHAT COUNTS AS A PAGE, and two corrections made 2026-10-02 after the index was measured against
sitemap.xml (203 entries against 217 routes):

1. The 16 share/card-*.html files were being INDEXED. They are Open Graph card templates - no
   <title>, so the leaf name was used, and the search box offered "card-r01" and "card1" as
   results that land on a bare image template. They are not in the sitemap and are not pages.
   That was a straightforward bug.

2. The ~27 country profiles were EXCLUDED, and that was deliberate - this file used to say "kept
   lean". Reversed, because the reason no longer holds: the exclusion dates from when this index
   replaced a 58-link mega-menu and leanness was the point, but the country profiles are in the
   sitemap, are reachable through /countries, and are the pages a visitor is most likely to search
   for by name. Searching "France" returning nothing is worse than 27 extra rows in a 200-row
   index. If leanness ever matters again, the fix is ranking, not absence.

check.py's `search` check now compares this index against sitemap.xml in BOTH directions, so a
page class cannot silently fall out again - which is how both faults above survived.
"""
import subprocess, re, json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
# share/ holds Open Graph card templates, not pages - see the header
pages = [p for p in subprocess.run(['git', 'ls-files', '*.html'], capture_output=True, text=True).stdout.split()
         if not p.startswith(('pipeline/', 'reconcile/', 'share/'))]

def clean_url(p):
    r = p[:-5]
    return '' if r == 'index' else r

idx, seen = [], set()
for p in pages:
    leaf = p.rsplit('/', 1)[-1][:-5]
    if leaf == '404' or p.endswith('/library.html'):
        continue
    s = open(p, encoding='utf8').read()
    mt = re.search(r'<title>(.*?)</title>', s, re.S)
    md = re.search(r'<meta name="description" content="(.*?)"', s, re.S)
    title = html.unescape(re.sub(r'\s+', ' ', mt.group(1)).strip()) if mt else leaf
    title = re.split(r'\s+[—-]\s+Critical Materials Atlas', title)[0].strip()
    desc = html.unescape(re.sub(r'\s+', ' ', md.group(1)).strip())[:160] if md else ''
    u = clean_url(p)
    if u in seen:
        continue
    seen.add(u)
    if '-chain' in p:
        g = 'Value chain'
        # chain <title> is usually the finding, not the name — show a clean "<Material> chain" title,
        # and demote the finding to the description so it's still searchable.
        folder = p.split('/')[0]
        name = folder[:-6] if folder.endswith('-chain') else folder.replace('-chip', '')
        pretty = name.replace('-', ' ').strip().title() + ' chain'
        if not desc:
            desc = title
        elif title.lower() not in desc.lower():
            desc = title + ' — ' + desc
        title = pretty
    elif leaf.startswith('profile-country-'):
        g = 'Country'
    elif leaf.startswith('profile-'):
        g = 'Profile'
    elif leaf.startswith('report-') or leaf == 'reports':
        g = 'Report'
    else:
        g = 'Page'
    idx.append({'u': u, 't': title, 'd': desc, 'g': g})

idx.sort(key=lambda x: x['t'].lower())
os.makedirs('out', exist_ok=True)
json.dump(idx, open('out/search-index.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print(f"wrote out/search-index.json — {len(idx)} pages")
