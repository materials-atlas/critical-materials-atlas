#!/usr/bin/env python3
"""
Pre-flight checks for the atlas. Run before every push:  python check.py

WHAT THIS CANNOT DO, STATED FIRST so nobody mistakes a green run for safety:
it would not have caught a single one of the four claims on challenge.html. The volatility code ran
perfectly and computed 37% vs 31% correctly; the host-coupling code computed r_host - r_base exactly as
written; the demand multiples were entered without a typo. Every one of those was a THINKING error - a
missing control, an invalid control, an unchecked assertion - and no assertion in this file detects
"you did not ask what else could produce this number". The countermeasure for that is an outside source
or an adversarial reader, not a script. Do not let a passing run feel like a clean bill of health.

WHAT IT DOES CATCH is the mechanical failure that actually bit us, repeatedly, on 15 July 2026:
  - the etapes doc drifting out of sync with the data (happened TWICE in one session)
  - the anonymity scrub leaking (happened TWICE - both times because a narrowed grep pattern missed it)
  - a fabricated cross-reference to a step that does not exist (happened once, caught by luck)
  - inline JS syntax errors shipping to a live page (happened once: a dangling `if(false){`)
  - the .gitignore trap: out/* is ignored with an explicit !out/x.json allowlist, so every NEW dataset is
    invisible to git until allowlisted - a page fetches a 404 and the failure is silent
  - withdrawn numbers creeping back into the open data
  - a page fetching a dataset that does not exist, or linking to a page that does not exist

Exit code 0 = all green. Non-zero = something is broken. Public data; deterministic.
"""
import base64, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
FAIL, WARN = [], []


def fail(check, msg):
    FAIL.append(f'{check}: {msg}')


def warn(check, msg):
    WARN.append(f'{check}: {msg}')


def pages():
    """Tracked site HTML at any depth (root + the value-chain subfolders), so nested pilot pages no
    longer escape the link/JS/dataset checks. Excludes the pipeline/reconcile tooling trees."""
    out = subprocess.run(['git', 'ls-files', '*.html'], capture_output=True, text=True).stdout.split()
    return sorted(p for p in out if not p.startswith(('pipeline/', 'reconcile/')))


def tracked(path):
    r = subprocess.run(['git', 'check-ignore', '-q', path], capture_output=True)
    return r.returncode != 0          # 1 = NOT ignored = trackable


# ---------------------------------------------------------------- 1. the .gitignore trap
def check_datasets():
    """Every out/*.json a page fetches must exist AND be trackable. out/* is gitignored behind an
    explicit allowlist, so a new dataset silently 404s in production while working fine locally."""
    for p in pages():
        html = open(p, encoding='utf8').read()
        base = os.path.dirname(p)
        # inline fetch('out/..json') AND the chain shells' window.CHAIN_DATA/CHAIN_TRADE='out/..json'
        refs = set(re.findall(r"fetch\('(out/[\w.\-]+\.json)'\)", html))
        refs |= set(re.findall(r"CHAIN_(?:DATA|TRADE)\s*=\s*'(out/[\w.\-]+\.json)'", html))
        for ds in refs:
            full = os.path.normpath(os.path.join(base, ds)) if base else ds
            rel = full.replace(os.sep, '/')
            if not os.path.exists(full):
                fail('datasets', f'{p} references {ds} which does not exist')
            elif not tracked(full):
                fail('datasets', f'{p} references {ds} but it is GITIGNORED -> will 404 live. '
                                 f'Add "!{rel}" to .gitignore')


# ---------------------------------------------------------------- 2. internal links
def check_links():
    have = set(pages())                       # repo-relative 'x.html' paths
    SKIP = ('http', '//', 'mailto:', 'tel:', '#', 'data:', 'javascript:')
    for p in pages():
        html = open(p, encoding='utf8').read()
        base = os.path.dirname(p)
        # (a) any explicit .html links (legacy or external-with-html) resolve to a real page
        for href in set(re.findall(r'href="([\w./\-]+\.html)(?:[#?][^"]*)?"', html)):
            if href.lower().startswith(SKIP):
                continue
            if href.startswith('/'):          # root-relative on the custom domain = repo root
                rel = href.lstrip('/')
            else:
                rel = os.path.normpath(os.path.join(base, href)).replace(os.sep, '/') if base else href
            if href not in have and rel not in have:
                fail('links', f'{p} links to {href} which does not exist')
        # (b) clean extensionless internal page links must resolve to <target>.html — since the
        # clean-URL migration these are the normal form; keep the safety net that catches typos.
        for href in set(re.findall(r'href="([\w./\-]+)(?:[#?][^"]*)?"', html)):
            if not href or href in ('.', '/', './', '../') or href.endswith('/'):
                continue
            if href.lower().startswith(SKIP):
                continue
            leaf = href.rsplit('/', 1)[-1]
            if '.' in leaf:                    # has an extension (.json/.css/.png/.html) — not a clean page link
                continue
            if href.startswith('/'):           # root-relative on the custom domain = repo root
                target = href.lstrip('/')
            else:
                target = os.path.normpath(os.path.join(base, href)).replace(os.sep, '/') if base else href
            if target + '.html' not in have:
                fail('links', f'{p} links to clean URL "{href}" but {target}.html does not exist')
        for anchor in set(re.findall(r'href="#([\w\-]+)"', html)):
            if f'id="{anchor}"' not in html:
                fail('links', f'{p} links to #{anchor} but no element has that id')


# ---------------------------------------------------------------- 3. inline JS syntax
def check_js():
    """A dangling brace in an inline <script> ships a blank page. Only caught by parsing it."""
    if subprocess.run(['node', '--version'], capture_output=True).returncode != 0:
        warn('js', 'node not available - skipped')
        return
    for p in pages():
        html = open(p, encoding='utf8').read()
        for i, js in enumerate(re.findall(r'<script>(.*?)</script>', html, re.S)):
            if not js.strip():
                continue
            with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf8') as fh:
                fh.write(js); tmp = fh.name
            r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
            os.unlink(tmp)
            if r.returncode != 0:
                fail('js', f'{p} inline script #{i+1} has a syntax error: '
                           f'{r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "?"}')
    # standalone renderer/helper JS (the value-chain pages load these instead of inlining)
    stray = subprocess.run(['git', 'ls-files', 'chain-assets/*.js', 'assets/*.js'],
                           capture_output=True, text=True).stdout.split()
    for jsf in stray:
        r = subprocess.run(['node', '--check', jsf], capture_output=True, text=True)
        if r.returncode != 0:
            fail('js', f'{jsf} has a syntax error: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "?"}')


# ---------------------------------------------------------------- 4. the anonymity scrub
def _scrub_pattern():
    """The wordlist is base64 ON PURPOSE. This file is committed to a public, anonymous repo, and a
    plain-text list of the terms to scrub for IS the leak it exists to prevent. Not hypothetical: the
    first version of this checker spelled them out, was committed and pushed, and then caught its own
    words live on GitHub. The scrubber became the leak. Decode it to read it; never inline it back."""
    return re.compile(base64.b64decode(
        'XGIoY2xhdWRlfGFudGhyb3BpY3xncm9rfGNoYXRncHR8b3BlbmFpfGNvcGlsb3R8bGxtfGdwdC0/WzAtOV18YWlbIC1d'
        'KG1vZGVsfGFzc2lzdHxnZW5lcmF0fGNyb3NzfHdyaXQpfGFydGlmaWNpYWwgaW50ZWxsaWdlbmNlfGxhbmd1YWdlIG1v'
        'ZGVsKVxi').decode(), re.I)

_BINEXT = ('png', 'jpg', 'jpeg', 'pdf', 'gpkg', 'zip', 'xlsx', 'parquet', 'gz')

def check_scrub(staged=False):
    """The anonymity scrub. Leaked FOUR times, every time because the guard ran AFTER the commit -- it
    scans tracked/committed files, so it only catches a term once it is already in history (and, on push,
    live on GitHub). The fix is `staged=True`: scan the STAGED blob of each file about to be committed,
    from a pre-commit hook, so the term is blocked BEFORE it can reach history. Keep the pattern WIDE and
    off binaries (compressed streams false-positive)."""
    pat = _scrub_pattern()
    if staged:
        names = subprocess.run(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                               capture_output=True, text=True).stdout.split()
        def read(f):  # the STAGED content (index blob), not the working tree
            r = subprocess.run(['git', 'show', f':{f}'], capture_output=True, text=True, errors='ignore')
            return r.stdout if r.returncode == 0 else None
    else:
        names = subprocess.run(['git', 'ls-files'], capture_output=True, text=True).stdout.split()
        def read(f):
            try:
                return open(f, encoding='utf8', errors='ignore').read()
            except (OSError, UnicodeDecodeError):
                return None
    for f in names:
        if f.rsplit('.', 1)[-1].lower() in _BINEXT:
            continue
        txt = read(f)
        if txt is None:
            continue
        for m in pat.finditer(txt):
            line = txt[:m.start()].count('\n') + 1
            fail('scrub', f'{f}:{line} mentions "{m.group(0)}" - the repo is public and anonymous')


# ---------------------------------------------------------------- 5. the etapes doc
def check_etapes():
    """Hand-written while every page is generated, so it drifts every time a page changes. It drifted
    TWICE on 15 July 2026. It is gitignored (internal), so nothing else would ever catch this."""
    p = 'project-formulas.html'
    if not os.path.exists(p):
        warn('etapes', f'{p} not found - skipped')
        return
    s = open(p, encoding='utf8').read()
    nums = [int(x) for x in re.findall(r'<span class="num">(\d+)</span>', s)]
    if nums != list(range(len(nums))):
        fail('etapes', f'step numbering is not sequential from 0: {nums}')
    for ref in set(int(x) for x in re.findall(r'\[step (\d+)\]', s)):
        if ref not in nums:
            fail('etapes', f'cross-reference [step {ref}] points at a step that does not exist')
    for href in set(re.findall(r'href="([\w.\-]+\.html)"', s)):
        if not os.path.exists(href):
            fail('etapes', f'links to {href} which does not exist')
    # Numbers quoted in the doc must match the data. EXTRACT what the doc says and compare it -
    # do not merely test for the old literal. Testing `if '174x' in doc and data != 174` only fires
    # when the doc is stale AND still says 174; a doc that says 999 slips through untouched. That hole
    # was found by deliberately breaking the doc and watching this check pass. Test your tests.
    try:
        v = json.load(open('out/price_volatility.json', encoding='utf8'))
        h = json.load(open('out/host_coupling.json', encoding='utf8'))
        quoted = [
            (r'~(\d+)× smaller markets', float(v['confound']['size_ratio']), 'step 9 market-size ratio'),
            (r'Total effect is real: \+([\d.]+)pp', round(v['model_wide']['terms'][1]['coef'], 2), 'step 9 total effect'),
            (r'Mean coupling <b>([\d.]+) → ([\d.]+)</b>', (h['mean_raw_corr'], h['mean_partial_corr']), 'step 10 coupling'),
        ]
        for rx, truth, what in quoted:
            m = re.search(rx, s)
            if not m:
                warn('etapes', f'cannot find the quoted figure for {what} - reworded? check it by hand')
                continue
            got = tuple(float(g) for g in m.groups()) if len(m.groups()) > 1 else float(m.group(1))
            ok = (got == truth) if not isinstance(truth, tuple) else (got == tuple(float(x) for x in truth))
            if not ok:
                fail('etapes', f'{what}: doc says {got}, data says {truth}')
    except (FileNotFoundError, KeyError, IndexError) as e:
        warn('etapes', f'could not cross-check numbers against data ({e})')


# ---------------------------------------------------------------- 6. withdrawn claims
def check_withdrawn():
    """Numbers we retracted must not reappear - not in a page, and above all not in an open dataset
    where someone could download and reuse them without ever seeing the strike-through."""
    ps = 'out/price_squeeze.json'
    if os.path.exists(ps):
        d = json.load(open(ps, encoding='utf8'))
        for dead in ('vol_byproduct', 'vol_primary', 'corr_companionality_volatility'):
            if dead in d:
                fail('withdrawn', f'{ps} ships "{dead}" - that claim is retracted, remove it from the data')
        if d.get('rows') and 'volatility' in d['rows'][0]:
            fail('withdrawn', f'{ps} rows still carry a "volatility" field - retracted')
        if 'withdrawn_note' not in d:
            warn('withdrawn', f'{ps} has no withdrawn_note documenting the removal')
    # The retracted phrasing must not be asserted on any PUBLIC page outside the record and the
    # changelog. Gitignored pages (project-formulas, project-map) are private working notes and are
    # SUPPOSED to carry the full history - policing them would be policing our own notebook.
    allowed = {'challenge.html', 'updates.html', 'price-volatility.html', 'host-coupling.html'}
    pat = re.compile(r'(37% vs 31%|mean best-host correlation|five metals beat)', re.I)
    for p in pages():
        if p in allowed or not tracked(p):
            continue
        for m in pat.finditer(open(p, encoding='utf8').read()):
            fail('withdrawn', f'{p} still asserts a retracted claim: "{m.group(0)}"')


# ---------------------------------------------------------------- 7. builders parse
def check_builders():
    import ast
    for f in sorted(f for f in os.listdir('.') if f.startswith('build_') and f.endswith('.py')):
        try:
            ast.parse(open(f, encoding='utf8').read())
        except SyntaxError as e:
            fail('builders', f'{f} has a syntax error at line {e.lineno}: {e.msg}')


def check_chokepoint_sync():
    """The Chokepoint Map and the hub counts DERIVE from chokepoint_map.json, which is built from each
    chain record's `chokepoint` field by build_chokepoint_map.py. If a record's classification changed
    but the map JSON was not rebuilt, the live page silently goes stale. Re-derive from the records and
    compare, so a stale map is impossible, not merely unlikely. Run: python build_chokepoint_map.py"""
    import importlib.util
    bp, mp = os.path.join(ROOT, 'build_chokepoint_map.py'), os.path.join(ROOT, 'chokepoint_map.json')
    if not os.path.exists(bp) or not os.path.exists(mp):
        return
    try:
        spec = importlib.util.spec_from_file_location('bcm', bp)
        bcm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bcm)
        derived = {r['chain']: r for r in bcm.derive()['rows']}
    except Exception as e:
        fail('chokepoint', f'could not derive the map from records: {e}'); return
    try:
        onfile = {r['chain']: r for r in json.load(open(mp, encoding='utf8')).get('rows', [])}
    except Exception as e:
        fail('chokepoint', f'chokepoint_map.json is unreadable: {e}'); return
    if derived == onfile:
        return
    detail = []
    miss, extra = sorted(set(derived) - set(onfile)), sorted(set(onfile) - set(derived))
    diff = sorted(c for c in derived if c in onfile and derived[c] != onfile[c])
    if miss:  detail.append(f'records missing from map: {miss[:5]}')
    if extra: detail.append(f'map rows with no record: {extra[:5]}')
    if diff:  detail.append(f'{len(diff)} row(s) changed (e.g. {diff[0]})')
    fail('chokepoint', 'chokepoint_map.json is STALE — run: python build_chokepoint_map.py  (' + '; '.join(detail) + ')')


def check_ledger():
    """Every chokepoint tagged conf=measured with a NUMERIC share is a load-bearing figure that can be
    posted. Each such figure MUST have an entry in source_ledger.json tying it to a named source and a
    QUOTED row/sentence — a bare citation hid the boron misread ('~70% of deposits IN Turkey' became
    '~70% of WORLD reserves') once. Fail if any numeric measured share has no ledger entry, so the
    'measured' tag cannot drift back to unverified judgment the moment nobody is looking."""
    lp, mp = os.path.join(ROOT, 'source_ledger.json'), os.path.join(ROOT, 'chokepoint_map.json')
    if not os.path.exists(lp) or not os.path.exists(mp):
        return
    try:
        L = json.load(open(lp, encoding='utf8'))
        rows = json.load(open(mp, encoding='utf8')).get('rows', [])
    except Exception as e:
        fail('ledger', f'ledger or map unreadable: {e}'); return
    # A share carries a quantitative claim if it has a digit OR a word-quantifier. The word form
    # ("~half", "most", "largest", "few") must not launder a number past the guard: swapping "50%"
    # for "~half" is the same claim. A bare em-dash ("—") asserts no number and is not caught.
    quant = re.compile(r'\d|~half|\bhalf\b|\bmost\b|\bmajority\b|\blargest\b|~all|\bfew\b')
    for r in rows:
        if r.get('conf') == 'measured' and quant.search(r.get('share', '').lower()):
            e = L.get(r['chain'])
            if not e:
                fail('ledger', f"{r['chain']} chokepoint is measured with a quantitative share ({r['share']}) "
                               f"but has NO source_ledger.json entry — add one with its quoted source row")
            elif e.get('supports') is not True:
                # A 'measured' figure must be genuinely supported by its quoted row — not 'pending'
                # or an industry figure that is 'not a quoted row'. (The Auditor's boron-class-2 hole:
                # manganese/cobalt passed green while their own quoted_row contradicted the share.)
                fail('ledger', f"{r['chain']} chokepoint is 'measured' with a quantitative share ({r['share']}) but its "
                               f"ledger entry is NOT fully supported (supports={e.get('supports')!r}) — either supply a "
                               f"quoted source row that supports it, or demote the chokepoint conf to 'estimate'")


def check_basis():
    """The other half of the ledger guard, aimed at the 'estimate' set. An estimate is not a quoted
    primary figure, so on the site it is clickable and must open how it was derived and its limits —
    basis.json. Fail if any estimate with a QUANTITATIVE share (digit or word-quantifier) has no basis
    entry, so 'estimate' can never mean an unexplained number. Also range-check every percentage share
    (measured or estimate): a share written as N% must be 0-100 — a typo'd 610% can't reach the page."""
    mp, bp = os.path.join(ROOT, 'chokepoint_map.json'), os.path.join(ROOT, 'basis.json')
    if not os.path.exists(mp):
        return
    try:
        rows = json.load(open(mp, encoding='utf8')).get('rows', [])
        B = {k: v for k, v in json.load(open(bp, encoding='utf8')).items() if not k.startswith('_')} if os.path.exists(bp) else {}
    except Exception as e:
        fail('basis', f'map or basis unreadable: {e}'); return
    quant = re.compile(r'\d|~half|\bhalf\b|\bmost\b|\bmajority\b|\blargest\b|~all|\bfew\b')
    for r in rows:
        share = r.get('share', '')
        if r.get('conf') == 'estimate' and quant.search(share.lower()):
            b = B.get(r['chain'])
            if not b or not (b.get('text') or '').strip():
                fail('basis', f"{r['chain']} chokepoint is an estimate with a quantitative share ({share}) but has "
                              f"NO basis.json entry — add one saying how it was derived and its limits (it renders as "
                              f"the clickable note behind the estimate)")
        for pct in re.findall(r'(\d+(?:\.\d+)?)\s*%', share):
            if not (0 <= float(pct) <= 100):
                fail('basis', f"{r['chain']} share {share!r} has a percentage outside 0-100 — check for a typo")


def check_anchor_sync():
    """out/anchor.json DERIVES from production.json + consumption.json + flows_2024.json via build_anchor.py.
    If an input changed but the anchor wasn't rebuilt, the live page silently goes stale. Re-derive and
    compare (like the chokepoint guard), and range-check every share to 0-100. Run: python build_anchor.py"""
    import importlib.util
    bp, mp = os.path.join(ROOT, 'build_anchor.py'), os.path.join(ROOT, 'out', 'anchor.json')
    if not os.path.exists(bp) or not os.path.exists(mp):
        return
    try:
        spec = importlib.util.spec_from_file_location('banch', bp)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        derived = m.derive()
    except Exception as e:
        fail('anchor', f'could not derive anchor from inputs: {e}'); return
    try:
        onfile = json.load(open(mp, encoding='utf8'))
    except Exception as e:
        fail('anchor', f'anchor.json unreadable: {e}'); return
    if derived != onfile:
        d = {r['material']: r for r in derived['results']}
        o = {r['material']: r for r in onfile.get('results', [])}
        diff = sorted(set(d) ^ set(o)) or sorted(k for k in d if k in o and d[k] != o[k])
        fail('anchor', f'anchor.json is STALE — run: python build_anchor.py  (differs: {diff[:6]})')
    for r in onfile.get('results', []):          # range-check shares
        for row in r['rows']:
            for k in ('obs_pc', 'expble_pc', 'prod_pc'):
                if row.get(k) is not None and not (0 <= row[k] <= 100):
                    fail('anchor', f"{r['material']}/{row['iso']} {k}={row[k]} outside 0-100")
    # consumption honesty invariant: a capture ratio must never exceed ~1 (never inflated to fit)
    cp = os.path.join(ROOT, 'out', 'consumption.json')
    if os.path.exists(cp):
        cj = json.load(open(cp, encoding='utf8'))
        for mat, c in cj.get('capture', {}).items():
            if c > 1.05:
                fail('anchor', f'consumption capture for {mat} is {c} (>1) — an inflated fit, not honest coverage')


# ---------------------------------------------------------------- run

def check_drift():
    """Derived outputs must agree with data.json on the shares they COPY.

    The failure this exists to stop: data.json's germanium refining share was corrected, but
    out/risk.json had been built weeks earlier and kept scoring the old value, so the supply-risk
    page published a number the rest of the site had already retracted. Nothing was broken -
    every file was internally valid - which is exactly why a link check or a schema check misses
    it. The only reliable signal is comparing the copy against the source.

    Also enforced: a material whose share is an INTERVAL must never have its point value shown on
    a profile page without the interval. A scalar is allowed to exist for an index that needs one;
    it is not allowed to be displayed as if it were a measurement.
    """
    try:
        d = json.load(open('out/data.json', encoding='utf8'))
    except Exception:
        return
    mats = {m['label']: m for m in d.get('materials', [])}

    # 1. risk.json copies the refining share into its components - it must match
    if os.path.exists('out/risk.json'):
        try:
            r = json.load(open('out/risk.json', encoding='utf8'))
            for row in r.get('materials', []):
                m = mats.get(row.get('label'))
                if not m or not m.get('refined'):
                    continue
                src = round(float(m['refined'][0]['v']), 1)
                got = row.get('components', {}).get('refining')
                if got is None:
                    continue
                if abs(float(got) - src) > 0.55:
                    fail('drift', f'out/risk.json scores {row["label"]} refining at {got} but '
                                  f'data.json says {src} - rebuild build_risk.py')
        except Exception as e:
            warn('drift', f'could not compare risk.json: {e}')

    # 2. an interval must be displayed as an interval, never as its scalar alone
    for lab, m in mats.items():
        rng = m.get('refined_range')
        if not rng:
            continue
        page = f'profile-{lab}.html'
        if not os.path.exists(page) or not tracked(page):
            continue
        html = open(page, encoding='utf8').read()
        band = f'{rng[0]}–{rng[1]}%'
        if band not in html:
            fail('drift', f'{page} does not show the interval {band} for a share that has no '
                          f'measured value - a point estimate must not stand alone')
        pt = m['refined'][0]['v']
        if re.search(rf'lead refiner[^<]{{0,12}}{int(pt)}%', html):
            fail('drift', f'{page} prints the scalar {int(pt)}% as the lead-refiner share; that '
                          f'number exists only for the index, not for display')


CHECKS = [('drift', check_drift), ('datasets', check_datasets), ('links', check_links), ('js', check_js),
          ('scrub', check_scrub), ('etapes', check_etapes), ('withdrawn', check_withdrawn),
          ('builders', check_builders), ('chokepoint', check_chokepoint_sync), ('ledger', check_ledger),
          ('basis', check_basis), ('anchor', check_anchor_sync)]

HOOK = ('#!/bin/sh\n'
        '# Auto-installed by check.py --install-hook. Blocks a commit that would leak an anonymity term\n'
        '# into staged content, BEFORE it can reach history. Reinstall after a fresh clone: python check.py --install-hook\n'
        'python check.py --staged || { echo "commit blocked: anonymity scrub failed on staged content"; exit 1; }\n')

def install_hook():
    root = subprocess.run(['git', 'rev-parse', '--git-path', 'hooks'], capture_output=True, text=True).stdout.strip()
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, 'pre-commit')
    with open(path, 'w', encoding='utf8', newline='\n') as fh:
        fh.write(HOOK)
    try:
        os.chmod(path, 0o755)
    except OSError:
        pass
    print(f'installed pre-commit hook -> {path}')
    print('It runs `python check.py --staged` and blocks any commit that stages an anonymity term.')

if __name__ == '__main__':
    if '--install-hook' in sys.argv:
        install_hook(); sys.exit(0)
    # --staged: pre-commit mode. Scrub the STAGED blobs only (fast, and the leak-prevention that matters).
    if '--staged' in sys.argv:
        check_scrub(staged=True)
        for f in FAIL:
            print(f'  FAIL  {f}')
        sys.exit(1 if FAIL else 0)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for name, fn in CHECKS:
        if only and only != name:
            continue
        fn()
        n = sum(1 for f in FAIL if f.startswith(name + ':'))
        print(f'  {"FAIL" if n else "ok  "}  {name}')
    print()
    for w in WARN:
        print(f'  warn  {w}')
    for f in FAIL:
        print(f'  FAIL  {f}')
    print()
    if FAIL:
        print(f'{len(FAIL)} problem(s). Not safe to push.')
    else:
        print('All mechanical checks pass.')
        print('This says NOTHING about whether the claims are true. It would not have caught any of the')
        print('four errors on challenge.html - those were thinking errors, and only an outside source or')
        print('an adversarial reader catches those.')
    sys.exit(1 if FAIL else 0)
