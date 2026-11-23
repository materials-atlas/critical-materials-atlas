"""
The calm banner (the homepage look) for pages that carry their OWN .hero CSS and so do not follow
assets/site.css. 23 Nov 2026, Part B item 11: one visual style site-wide.

Appended at the end of <head>, so it comes after the page's own rules and wins at equal specificity.
Screen only: the brief's and the technical note's print styles stay as they are. Hand pages carry a
copy of CALM_HERO (findings, explorer, methodology, technical-note); build_brief.py calls add().
Keep the colours in step with the .hero rules in assets/site.css.
"""
CALM_HERO = ('<style id="calm-hero">'
  "@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap');"
  '@media screen{'
  'body{background:#fbfaf7}'
  '.hero{background:#fbfaf7;color:#1a1f24;border-bottom:1px solid #e6e9e8}'
  '.hero-motif{display:none}'
  '.hero .eyebrow{color:#0e7c74}'
  ".hero h1{font-family:'Source Serif 4',Georgia,serif;font-weight:600;color:#15323a;letter-spacing:-.01em}"
  '.hero .deck,.hero .sub,.hero p,.hero .authors{color:#3c4650}'
  '.hero .byline,.hero .meta-links,.hero .stamp{color:#667179}'
  '.hero .authors b,.hero b{color:#15323a}'
  '.hero a,.hero .meta-links a{color:#0e7c74}'
  '.hero [style*="color:#9fbab6"]{color:#667179!important}'
  '.hero [style*="color:#fff"],.hero [style*="color: #fff"]{color:#15323a!important}'
  ".hero h2,article h2,main h2{font-family:'Source Serif 4',Georgia,serif;font-weight:600}"
  '}</style>')


def add(html):
    """Put the calm banner at the end of <head>, once; an older copy is replaced."""
    import re
    html = re.sub(r'<style id="calm-hero">.*?</style>', '', html, flags=re.S)
    return html.replace('</head>', CALM_HERO + '</head>', 1)
