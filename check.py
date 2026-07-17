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
    return [f for f in sorted(os.listdir('.')) if f.endswith('.html')]


def tracked(path):
    r = subprocess.run(['git', 'check-ignore', '-q', path], capture_output=True)
    return r.returncode != 0          # 1 = NOT ignored = trackable


# ---------------------------------------------------------------- 1. the .gitignore trap
def check_datasets():
    """Every out/*.json a page fetches must exist AND be trackable. out/* is gitignored behind an
    explicit allowlist, so a new dataset silently 404s in production while working fine locally."""
    for p in pages():
        html = open(p, encoding='utf8').read()
        for ds in set(re.findall(r"fetch\('(out/[\w.\-]+\.json)'\)", html)):
            if not os.path.exists(ds):
                fail('datasets', f'{p} fetches {ds} which does not exist')
            elif not tracked(ds):
                fail('datasets', f'{p} fetches {ds} but it is GITIGNORED -> will 404 live. '
                                 f'Add "!{ds}" to .gitignore')


# ---------------------------------------------------------------- 2. internal links
def check_links():
    have = set(pages())
    for p in pages():
        html = open(p, encoding='utf8').read()
        for href in set(re.findall(r'href="([\w.\-]+\.html)(?:#[\w\-]+)?"', html)):
            if href not in have:
                fail('links', f'{p} links to {href} which does not exist')
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

_BINEXT = ('png', 'jpg', 'jpeg', 'pdf', 'gpkg', 'zip', 'xlsx')

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


# ---------------------------------------------------------------- run
CHECKS = [('datasets', check_datasets), ('links', check_links), ('js', check_js),
          ('scrub', check_scrub), ('etapes', check_etapes), ('withdrawn', check_withdrawn),
          ('builders', check_builders)]

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
