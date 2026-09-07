#!/usr/bin/env python3
"""Post-build canonical injector (idempotent).

The build_*.py generators emit page <head>s without a <link rel="canonical">.
Because GitHub Pages serves every /foo.html ALSO at the extensionless /foo, that
leaves duplicate URLs with no declared owner -> Google Search Console flags
"Duplicate without user-selected canonical" and the pages don't index cleanly.

This tool scans every published HTML page and adds a self-referential canonical
to its clean (extensionless) URL when one is missing. Safe to run repeatedly.

Run it as the LAST step after regenerating pages (see CADENCE.md), e.g.:
    python build_profiles.py && ... && python add_canonicals.py
"""
import re, os, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://criticalmaterialsatlas.org"
SKIP = {"404.html"}                      # error page: never canonicalised
EXCLUDE_DIRS = ("node_modules", ".git", "__pycache__", "out", "sources", "fixtures",
                "share",      # social-preview card templates (rendered to PNG, not indexable pages)
                "pipeline")   # private trade-pipeline UI, not part of the public site

def clean_url(relpath: str) -> str:
    p = relpath.replace(os.sep, "/")
    if p.lower().endswith(".html"):
        p = p[:-5]                       # site serves extensionless URLs
    return f"{BASE}/{p}"

def main() -> int:
    added, skipped = 0, 0
    for path in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if rel in SKIP or any(("/" + d + "/") in ("/" + rel) for d in EXCLUDE_DIRS):
            continue
        html = open(path, encoding="utf-8").read()
        if 'rel="canonical"' in html:                       # already owns its URL
            continue
        if re.search(r'name=["\']robots["\'][^>]*noindex', html, re.I):
            skipped += 1; continue                          # intentionally not indexed
        m = re.search(r'<meta charset="utf-8">', html, re.I)
        if not m:
            print(f"  ! no <meta charset> anchor, skipped: {rel}"); continue
        link = f'<link rel="canonical" href="{clean_url(rel)}">'
        html = html[:m.end()] + link + html[m.end():]
        open(path, "w", encoding="utf-8", newline="\n").write(html)
        print(f"  + {rel} -> {clean_url(rel)}")
        added += 1
    print(f"add_canonicals: added {added}, skipped {skipped} noindex")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
