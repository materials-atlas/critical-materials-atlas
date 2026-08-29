#!/usr/bin/env python3
"""Build out/search-index.json — the header-search index (Phase-2 IA). One record per user-facing
page: clean URL, title, short description, and a group tag. Powers the persistent search box in
assets/nav.js, the real replacement for a 58-link mega-menu. Excludes 404, per-chain library dumps,
and the ~28 country-profile pages (kept lean). Run: python build_search_index.py
"""
import subprocess, re, json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
pages = [p for p in subprocess.run(['git', 'ls-files', '*.html'], capture_output=True, text=True).stdout.split()
         if not p.startswith(('pipeline/', 'reconcile/'))]

def clean_url(p):
    r = p[:-5]
    return '' if r == 'index' else r

idx, seen = [], set()
for p in pages:
    leaf = p.rsplit('/', 1)[-1][:-5]
    if leaf == '404' or p.endswith('/library.html') or leaf.startswith('profile-country-'):
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
