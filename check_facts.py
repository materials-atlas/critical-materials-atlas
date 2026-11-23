#!/usr/bin/env python3
"""
One fact, one number, on every page.  (Second half of list item A7, 23 Nov 2026.)

    python check_facts.py            every page, prints each disagreement
    python check.py facts            the same, as one of check.py's checks

WHY. In November 2026 four outside reviews found the same fact printed with different numbers on
different pages: strontium, nickel, lithium and bauxite mine shares, "17" and "18" materials where the
exporter is not the miner, "4" and "5" geological chains, "9" and "10" materials with a rising trend.
Each page was right on the day it was written. The data moved; the hand-typed copies did not. A file
check cannot see that - every file is valid. Only a comparison of the page with the store can.

HOW. Each FACT below names the store that owns the number, computes the number from it, and lists the
phrases pages use to state it. Every tracked page is read (tags, scripts and styles removed) and every
phrase found must carry the store's number. Separately, every material's top miner and share is taken
from out/data.json (the one-source mine shares, check `mined`), and a page sentence that names that
material, that country and "NN% of ... mine/mining" must give the same share, to the nearest point.

WHAT IT DOES NOT SEE. Text a page script writes at run time (check_rendered.py opens pages in a
browser, but compares nothing). A fact stated in words no phrase here matches. A new fact nobody has
registered: when a number drifts between pages, add the fact here in the same commit as the fix.

DATED RECORDS keep their numbers by rule (a published document is not rewritten; it gets a dated
note): the reports, the technical note, the review, the updates log, the share cards and the social
posts. They are listed in DATED and not checked. Anything else that legitimately differs goes in ALLOW
with its reason.
"""
import html
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def _j(p):
    return json.load(io.open(os.path.join(ROOT, p), encoding='utf-8'))


def DATED(p):
    b = os.path.basename(p)
    return (b.startswith('report-') or p.startswith(('share/', 'out/social/'))
            or b in {'technical-note.html', 'review.html', 'updates.html'})


# (page, fact name, number printed) -> why it is allowed to differ
ALLOW = {
    ('refining.html', 'top miner: lithium', 35): "the IEA dataset's own mine share, labelled IEA, beside IEA refining",
    ('challenge.html', 'top miner: lithium', 35): "quotes the IEA figure of refining.html, labelled IEA",
    ('profile-tungsten.html', 'top miner: tungsten', 79): "the refining line's source note (source_ledger.json): "
        "USGS's 2025 estimate, 67,000 of 85,000 t; the mine bar beside it is 2024, 82%",
}


def MINER_SKIP(p):
    """Pages whose mine shares are not the store's by design: a chain's source library reports what
    each source says, in that source's own number; the revisions page compares USGS editions."""
    return p.endswith('/library.html') or p == 'revisions.html'


# ------------------------------------------------------------------ the store's numbers
def trend_rising():
    """Materials whose export concentration rises significantly (FDR-corrected Mann-Kendall < 0.05,
    positive Sen slope) - the rule build_brief.py and build_insights.py both apply to out/trends.json."""
    t = _j('out/trends.json').get('materials', {})
    h = lambda v: v.get('stats', {}).get('hhi', {})
    return sum(1 for v in t.values() if h(v).get('mk_p_fdr', 1) < 0.05 and h(v).get('sen', 0) > 0)


def geological():
    return sum(1 for r in _j('chokepoint_map.json')['rows'] if r['mechanism'] == 'geological')


def chains():
    return _j('chokepoint_map.json')['count']


def breakout(kinds):
    return lambda: sum(_j('out/breakout.json')['summary']['by_moat'][k] for k in kinds)


def origin_gap():
    return _j('out/origin_gap_all.json')['n_atlas_gap']


N = r'(\d+)'
OF = r'(?:\s+of\s+(?:the\s+)?\d+)?'          # an optional "of 32" - the count is checked, not the total
FACTS = [
    ('materials with a significantly rising export concentration', trend_rising, [
        N + OF + r'\s+materials\s+(?:show|are)\s+(?:a\s+)?(?:statistically\s+)?significant',
        N + OF + r'\s+materials\s+show\s+a\s+(?:statistically\s+significant\s+)?rising\s+export-concentration',
        N + OF + r'\s+materials\s+are\s+significantly\s+concentrating',
    ]),
    ('geological chokepoint chains', geological, [
        N + r'\s+of\s+' + str(chains()) + r'\s+(?:chains\s+|chokepoints\s+)?(?:are\s+)?geological',
        r'geological\s+count\s+from\s+<?b?>?\d+\s+to\s+' + N,
    ]),
    ('chokepoints that are a mine (mine-side endowment)', breakout(['mine-side endowment']), [
        N + OF + r'\s+chokepoints\s+are\s+a\s+mine',
    ]),
    ('chokepoints that are a capability, not an ore endowment',
     breakout(['import-fed capability', 'by-product capability']), [
        N + OF + r'\s+chokepoints\s+that\s+are\s+a\s+capability',
        N + OF + r'\s+materials\s+the\s+chokepoint\s+is\s+a\s+processing\s+capability',
    ]),
    ('materials whose top exporter is not the top miner', origin_gap, [
        N + OF + r'\s+(?:critical\s+(?:raw\s+)?)?materials,?\s+(?:the\s+)?(?:country\s+that\s+(?:ships|exports)\s+the\s+most|top\s+exporter|leading\s+exporter)\s+(?:is\s+not|isn.t|never)',
        N + OF + r'\s+materials?\s+where\s+the\s+top\s+exporter\s+is\s+not',
    ]),
]


# ------------------------------------------------------------------ the pages
def pages():
    out = subprocess.run(['git', 'ls-files', '*.html'], capture_output=True, text=True, cwd=ROOT).stdout.split()
    return sorted(p for p in out if not p.startswith(('pipeline/', 'reconcile/')))


_DROP = re.compile(r'<(script|style)\b.*?</\1>', re.S | re.I)
_TAG = re.compile(r'<[^>]+>')


def text(p):
    s = io.open(os.path.join(ROOT, p), encoding='utf-8', errors='replace').read()
    s = _TAG.sub(' ', _DROP.sub(' ', s))
    return re.sub(r'\s+', ' ', html.unescape(s)).replace(' ', ' ')


def _names():
    sys.path.insert(0, ROOT)
    try:
        import baci
        nm = {r.iso2: r.name for r in baci.countries().itertuples() if r.iso2 and r.name}
    except Exception:
        nm = {}
    nm.update({'US': 'United States', 'CD': 'DR Congo', 'RU': 'Russia', 'KR': 'South Korea',
               'GB': 'United Kingdom', 'TR': 'Turkey', 'AE': 'United Arab Emirates', 'DE': 'Germany',
               'CN': 'China', 'ZA': 'South Africa', 'IR': 'Iran', 'VN': 'Viet Nam'})
    return nm


ALIAS = {'DR Congo': ['DR Congo', 'DRC', 'Congo'], 'United States': ['United States', 'the US', 'US'],
         'Viet Nam': ['Viet Nam', 'Vietnam'], 'Turkey': ['Turkey', 'Türkiye'], 'Russia': ['Russia']}


def miner_facts():
    """(fact name, share, material words, country words) for each material's top miner."""
    nm = _names()
    out = []
    for m in _j('out/data.json')['materials']:
        mi = (m.get('mined') or [None])[0]
        if not mi or mi.get('v') is None:
            continue
        name = m['title'].split(' (')[0].split(',')[0].strip()
        words = {name.lower(), m['label'].lower()}
        cn = nm.get(mi['c'])
        if not cn:
            continue
        out.append(('top miner: ' + m['label'], mi['v'], words, ALIAS.get(cn, [cn])))
    return out


def run():
    """Returns a list of (page, fact, printed, store) disagreements."""
    bad = []
    facts = [(name, fn(), [re.compile(p, re.I) for p in pats]) for name, fn, pats in FACTS]
    miners = miner_facts()
    for p in pages():
        if DATED(p):
            continue
        t = text(p)
        for name, want, pats in facts:
            for rx in pats:
                for m in rx.finditer(t):
                    got = int(m.group(1))
                    if got != want and (p, name, got) not in ALLOW:
                        bad.append((p, name, got, want, t[max(0, m.start() - 60):m.end() + 40]))
        if not MINER_SKIP(p):
            bad += miner_check(p, t, miners)
    seen, out = set(), []
    for b in bad:                      # two phrases can match one sentence: report it once
        key = b[:4] + (b[4][-80:],)
        if key not in seen:
            seen.add(key)
            out.append(b)
    return out


# country, then within a few words a share, then "of (the world's) mine / mining"; an arrow, slash,
# bullet or bar between them means the share belongs to something else ("~37% Chile / 80% superalloy")
_GAP = r'[^.%/→·|]{0,30}?'


def miner_check(p, t, miners):
    bad = []
    for sent in re.split(r'(?<=[.;!?])\s', t):
        sl = sent.lower()
        if '%' not in sl or not re.search(r'\bmin(e|es|ed|ing)\b', sl):
            continue
        for name, want, words, cwords in miners:
            if not any(re.search(r'\b' + re.escape(w) + r'\b', sl) for w in words):
                continue
            for cw in cwords:
                rx = (r'\b' + re.escape(cw) + r'\b' + _GAP + r'(~|about |around |roughly )?\b(\d{1,3}(?:\.\d+)?)\s?%'
                      + _GAP + r'\b(?:of\s+)?(?:the\s+)?(?:world\S*\s+|global\s+)?(?:\w+\s+)?(?:mine|mining|mined)\b')
                for m in re.finditer(rx, sent):
                    got = float(m.group(2))
                    tol = 2.5 if m.group(1) else 0.5          # "~80%" may round 82; a bare "80%" may not
                    if abs(got - want) > tol and (p, name, round(got)) not in ALLOW:
                        bad.append((p, name, got, want, sent[:220]))
    return bad


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    bad = run()
    for p, name, got, want, ctx in bad:
        print(f'{p}: "{name}" printed {got:g}, store says {want:g}\n      ... {ctx.strip()} ...')
    print(f'\n{len(bad)} disagreement(s)' if bad else 'every registered fact agrees with its store')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
