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
    return add_calm(html.replace('</head>', CALM_HERO + '</head>', 1))


# The calm pass (25 Nov 2026), for the pages that do not load assets/site.css. Same rules as the
# "Calm pass" block at the end of assets/site.css; keep the two in step.
CALM_PASS = ('<style id="calm-pass">'
  '.eyebrow,.hero .eyebrow{font-size:.85rem!important;font-weight:500!important;letter-spacing:0!important;'
  'text-transform:none!important;color:#667179!important}'
  '.callout,.callout.hot,.intro{background:transparent!important;border:0!important;'
  'border-left:2px solid #ccd5d3!important;border-radius:0!important;padding:.15rem 0 .15rem 1rem!important}'
  '.card,.card:hover{box-shadow:none!important}'
  'main b,main strong,article b,article strong{font-weight:600}'
  '</style>')


def add_calm(html):
    """The calm pass at the end of <head>, once; an older copy is replaced."""
    import re
    html = re.sub(r'<style id="calm-pass">.*?</style>', '', html, flags=re.S)
    return html.replace('</head>', CALM_PASS + '</head>', 1)
