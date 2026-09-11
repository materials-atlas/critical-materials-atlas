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


def check_dim():
    """The material dimension must stay unique, in-vocabulary, and true to its sources.

    The table is keyed on (material, attribute, source, vintage), so a material may legitimately
    hold several values of one attribute - two editions of a report, or two definitions of
    recycling. What must never happen is two of them claiming to be CURRENT: a join on is_current
    would then match every cube row twice and silently double the tonnage. Extra vintages are
    welcome; extra current rows are the fan-out.

    Also caught here: a stale parquet still serving an EOL-RIR that data.json has since corrected
    - the same drift class as risk.json's germanium, one table further out.
    """
    path = 'pipeline/data/dim_material.parquet'
    if not os.path.exists(path):
        return
    try:
        import pandas as pd
    except ImportError:
        return
    dim = pd.read_parquet(path)

    key = ['material', 'attribute', 'source', 'vintage']
    dup = dim[dim.duplicated(subset=key, keep=False)]
    if len(dup):
        pairs = ', '.join(sorted({f"{r.material}/{r.attribute}" for r in dup.itertuples()}))
        fail('dim', f'dim_material records the same source and vintage twice for: {pairs}')

    if 'is_current' not in dim.columns:
        fail('dim', 'dim_material has no is_current column, so a join has no way to pick one row '
                    'per material and would fan out across vintages')
    else:
        n_cur = dim[dim.is_current].groupby(['material', 'attribute']).size()
        bad = n_cur[n_cur != 1]
        if len(bad):
            pairs = ', '.join(f'{m}/{a} ({n})' for (m, a), n in bad.items())
            fail('dim', f'more than one CURRENT row - a join on is_current would fan out cube '
                        f'rows and multiply tonnages: {pairs}')

    cube = 'pipeline/data/cube.parquet'
    if os.path.exists(cube):
        known = set(pd.read_parquet(cube, columns=['material'])['material'].unique())
        orphan = sorted(set(dim['material']) - known)
        if orphan:
            fail('dim', f'dim_material describes materials the cube does not have, so nothing can '
                        f'join to them: {", ".join(orphan)}')

    # the manifest is what a query author reads to decide what to pin. If it drifts from the
    # cube it is worse than absent: it advertises identities that no longer exist, or hides ones
    # that do, and the query written against it looks perfectly reasonable.
    if os.path.exists('out/cube_manifest.json') and os.path.exists(cube):
        try:
            man = json.load(open('out/cube_manifest.json', encoding='utf8'))
            c = pd.read_parquet(cube, columns=['material', 'source', 'measure', 'stage',
                                               'basis', 'unit'])
            live = len(c.groupby(['material', 'source', 'measure', 'stage', 'basis', 'unit'],
                                 dropna=False).size())
            if man.get('n_identities') != live:
                fail('dim', f'cube_manifest.json advertises {man.get("n_identities")} identities '
                            f'but the cube has {live} - rerun cube_query.py')
        except Exception as e:
            fail('dim', f'cube_manifest.json unreadable: {e}')

    try:
        d = json.load(open('out/data.json', encoding='utf8'))
    except Exception:
        return
    src = {m['label']: m for m in d.get('materials', [])}
    cur = dim[(dim.attribute == 'eol_rir') & dim.get('is_current', True)]
    live = cur.set_index('material')['value_num'].to_dict()
    for lab, v in live.items():
        want = src.get(lab, {}).get('recycling')
        if want is not None and abs(float(want) - v) > 0.01:
            fail('dim', f'dim_material has {lab} eol_rir={v:g} but data.json says {want} - the '
                        f'dimension is stale; rerun build_cube_dim.py')


def check_series_key():
    """Every observation in the cube must be uniquely identified. This is the SDMX requirement,
    adopted because asking the question found real defects that nothing else caught.

    A key is (source, material, measure, stage, basis, country, year, native_code). When two rows
    share it, some query somewhere adds them together or picks one at random, and both answers
    look ordinary. Three causes were found the first time this was asked, and all three were in
    the SOURCES, not in our code: BGS files the Republic of Congo under DR Congo's ISO code, so
    two countries were being summed; USGS repeats its final year label on two rows of different
    figures in cadmium.xlsx and nickel.xlsx; and West Germany shared a code with unified Germany
    for four overlapping years. 144 rows, one of them wrong by a factor of 6,000.
    """
    path = 'pipeline/data/cube.parquet'
    if not os.path.exists(path):
        return
    try:
        import pandas as pd
    except ImportError:
        return
    # freq and period joined the key when monthly trade arrived: Chile copper exports in 2025 and
    # in March 2025 are different observations, and without freq they collide on `year` and look
    # like a duplicate. period carries YYYY for annual rows and YYYYMM for monthly ones.
    key = ['source', 'material', 'measure', 'stage', 'basis', 'country_iso3', 'freq', 'period',
           'native_code']
    c = pd.read_parquet(path, columns=key)
    n = c.groupby(key, dropna=False).size()
    bad = n[n > 1]
    if len(bad):
        ex = '; '.join('%s %s %s %s' % (i[1], i[0].split()[0], i[6], i[7])
                       for i in list(bad.index)[:4])
        fail('key', f'{len(bad)} observations in the cube share a series key, so a query will '
                    f'either sum two different things or pick one at random: {ex}')


def check_sdmx():
    """The SDMX export must satisfy its own declared structure, read from the published files.

    A structure definition that the data does not obey is worse than none: it invites another
    agency to load the dataflow, trust the key, and get silently wrong answers. So this reads
    out/sdmx/ the way a receiving agency would - structure first, then data - and checks that
    every dimension and coded attribute resolves to a code the structure declares, and that the
    declared series key actually holds. It also refuses an export carrying a source with no
    recorded redistribution licence, because an export IS a redistribution channel.
    """
    import csv as _csv, gzip as _gzip, hashlib as _hl
    d = 'out/sdmx'
    sp, dp = os.path.join(d, 'structure.json'), os.path.join(d, 'mineral_flows.sdmx.csv.gz')
    if not (os.path.exists(sp) and os.path.exists(dp)):
        return

    # Reading half a million observations turns this check from 3 seconds into 37, on something
    # that runs before every push. So the result is cached against the CONTENT of the two files,
    # never their timestamps: mtime is the signal that failed us on risk.json, where a rebuilt
    # file looked fresh while serving a retracted number. Same bytes, same verdict; one byte
    # different anywhere and the full scan runs again.
    def sha(path):
        h = _hl.sha256()
        with open(path, 'rb') as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b''):
                h.update(chunk)
        return h.hexdigest()

    fingerprint = {'structure': sha(sp), 'data': sha(dp)}
    stamp = os.path.join(d, '.verified.json')
    if os.path.exists(stamp):
        try:
            if json.load(open(stamp, encoding='utf8')) == fingerprint:
                return
        except Exception:
            pass
    st = json.load(open(sp, encoding='utf8'))
    dsd = st['data']['dataStructures'][0]
    flow = st['data']['dataflows'][0]
    cls = {c['id']: {x['id'] for x in c['codes']} for c in st['data']['codelists']}
    coded = {x['id']: x['codelist'] for x in dsd['dimensions'] + dsd['attributes']
             if x.get('codelist')}
    key = flow['series_key'] + ['TIME_PERIOD']

    seen, bad = set(), {}
    dups = 0
    with _gzip.open(dp, 'rt', encoding='utf8') as f:
        for row in _csv.DictReader(f):
            k = tuple(row[c] for c in key)
            if k in seen:
                dups += 1
            seen.add(k)
            for field, cl in coded.items():
                v = row.get(field, '')
                if v and v not in cls[cl]:
                    bad.setdefault((field, v), 0)
                    bad[(field, v)] += 1
    if dups:
        fail('sdmx', f'{dups} observations in the SDMX export share a series key, so the '
                     f'structure it declares is a lie')
    if bad:
        ex = '; '.join(f'{f}={v!r}' for (f, v), _ in list(bad.items())[:3])
        fail('sdmx', f'{len(bad)} values in the export are not in the code list they declare: {ex}')
    ok = True
    for src in flow.get('sources_and_licences', {}):
        if not flow['sources_and_licences'][src]:
            fail('sdmx', f'{src} is exported with no recorded redistribution licence')
            ok = False
    if ok and not dups and not bad:
        json.dump(fingerprint, open(stamp, 'w', encoding='utf8'))


def check_mirror_independence():
    """Is there enough DATA behind the mirror comparison - and can we tell if a side was estimated?

    CORRECTED 7 Sep 2026, after the user pointed out that the original version measured the wrong
    thing. It failed a pair when both sides came through the same PORTAL, describing that as "one
    compiler compared against itself". That was wrong. UN Comtrade does not produce trade data; it
    collects what each country files. An exporter's declaration and an importer's declaration are
    two independent national measurements whether they are fetched from Comtrade or from two
    separate national websites. Portal diversity is not measurement independence, and calling it
    that overstated a real weakness into a fake one.

    What genuinely limits the comparison:
      1. BREADTH. One month of one source is a thin sample - a sample problem, not a validity one.
      2. ESTIMATION. Comtrade sometimes derives a country's figures rather than receiving them,
         and comparing a derived side against the partner it was derived from IS circular. That is
         answerable: the API returns isReported and legacyEstimationFlag per row. We were storing
         seven fields and neither was among them, so the question could not be asked at all.
         adapter_comtrade now keeps both; this check will assert on them once the cache is
         repulled with the wider field set.

    So this checks what it can check today - that no reconcilable source has collapsed to a single
    period, which is the state that produced a 51% disagreement rate off one December.
    """
    path = 'pipeline/data/cache/_manifest.json'
    if not os.path.exists(path):
        return
    try:
        man = json.load(open(path, encoding='utf8'))
    except Exception:
        return
    thin = [k for k in ('comtrade', 'uscensus', 'eurostat', 'hmrc', 'comexstat')
            if man.get(k, {}).get('n_periods') == 1]
    if thin:
        print('  NOTE: single-period feeds (a sample limit, not an error): ' + ', '.join(thin)
              + ' — repeated refreshes accumulate now, so this shrinks with scheduled runs')
    stale = [k for k, v in man.items()
             if isinstance(v, dict) and 'n_periods' not in v]
    if stale:
        fail('mirror', 'cache manifest has no period span for: ' + ', '.join(stale)
                       + ' — re-save those sources; span is how a one-month feed becomes visible')


def check_withheld():
    """No source we may not redistribute appears in anything served off the website.

    This exists because the rule was enforced in one exporter out of two. build_sdmx.py refused to
    publish our monthly reconciliation - correctly, it is 79% UN Comtrade - while the four lines
    that write out/cube.parquet and out/cube.csv.gz had no gate at all and wrote the same 59,577
    rows to files anyone can download. The SDMX export was clean and the plain download was not,
    and nothing would have told us.

    So the check does not ask whether the exporters INTEND to withhold. It opens the published
    files and looks.
    """
    import licences
    import pandas as pd   # check.py has no module-level pandas; the injection test found this
    if not licences.WITHHELD:
        return
    targets = [('out/cube.parquet', 'source'), ('out/cube.csv.gz', 'source')]
    for rel, col in targets:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        try:
            d = (pd.read_parquet(p, columns=[col]) if rel.endswith('.parquet')
                 else pd.read_csv(p, usecols=[col], compression='gzip'))
        except Exception as e:
            fail('withheld', '%s could not be read to verify it: %s' % (rel, e))
            continue
        leaked = sorted(set(d[col].dropna().unique()) & set(licences.WITHHELD))
        if leaked:
            n = int(d[col].isin(leaked).sum())
            fail('withheld', '%s publishes %d rows from a source we may not redistribute: %s'
                 % (rel, n, ', '.join(leaked)))
    # AND NOW THE PART THAT ACTUALLY MATTERED. The version of this check above looked at three
    # files I had thought of. Meanwhile pipeline/data/flows_best.parquet - 144,188 raw Comtrade
    # declarations - had been tracked on the PUBLIC remote for weeks, because nobody had thought
    # of it. A gate you have to remember to apply is not a gate.
    #
    # So this asks git what it is actually publishing, and opens every one of them. A new file
    # carrying holder records is caught the first time it is staged, whether or not anyone
    # remembered it exists.
    RAW_DECLARATIONS = {'comtrade', 'eurostat', 'hmrc', 'uscensus', 'comexstat', 'mirror'}
    try:
        tracked = subprocess.run(['git', 'ls-files', '*.parquet'], cwd=ROOT,
                                 capture_output=True, text=True, timeout=60).stdout.split()
    except Exception:
        tracked = []
    for rel in tracked:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        try:
            cols = pd.read_parquet(p).columns
            if 'source' not in cols:
                continue
            vals = set(pd.read_parquet(p, columns=['source']).source.dropna().unique())
        except Exception:
            continue
        raw = sorted(v for v in vals if str(v).lower() in RAW_DECLARATIONS)
        wh = sorted(vals & set(licences.WITHHELD))
        if raw:
            fail('withheld', 'git tracks %s, which holds raw national customs declarations we may '
                             'not republish (%s). Untrack it and add it to .gitignore.'
                 % (rel, ', '.join(raw)))
        if wh:
            fail('withheld', 'git tracks %s, which holds a withheld source (%s).'
                 % (rel, ', '.join(wh)))

    g = os.path.join(ROOT, 'out', 'sdmx', 'mineral_flows.sdmx.csv.gz')
    if os.path.exists(g):
        import gzip
        head = gzip.open(g, 'rt', encoding='utf-8').read(2_000_000)
        for w in licences.WITHHELD:
            if w in head:
                fail('withheld', 'the SDMX export contains withheld source ' + w)



def check_baci_door():
    """I1 for BACI: only the one door opens raw/baci/. ARCHITECTURE.md phase 2.

    Before the sweep, 56 builders opened raw/baci/ themselves and 53 held their own copy of the
    country mapping. A correction to that mapping would have had to be made in 53 places, which
    is how the Congo fix had to be made twice. After the sweep, every reader goes through
    baci.py, and this check is the ratchet that stops the number growing back from zero.

    Static, deliberately: it scans source text, so a builder that merely MENTIONS the archive in
    a comment is fine, but one that builds a path to it is caught the moment it is written -
    before it is ever run, and whether or not anyone remembers the rule.
    """
    import re
    allow = {'baci.py', 'extract_baci.py', 'build_library.py', 'record_graph.py', 'migrate_baci.py',
             'phase2_accept.py', 'check.py', 'check_baci_release.py'}
    # The invariant is about OPENING, not mentioning. A dead constant like BACI_ZIP = ... that
    # nothing reads any more is untidy, not a door; build_catalog builds the archive's path as a
    # STRING for the holdings record and never opens it. So: flag a ZipFile() anywhere (the only
    # legitimate one on BACI is extract_baci.py), and an open()/read_csv() whose argument text
    # names a raw/baci file. Both are how a door looks in source.
    door = re.compile(r"ZipFile[(]|(?:open|read_csv|read_parquet)[(][^)]*(?:raw['\"]?[ ]*,[ ]*['\"]baci|raw/baci|country_codes_V202601|product_codes_HS)")
    pat = door
    offenders = []
    for dirpath, dirnames, files in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in ('.git', 'raw', 'extract', 'pipeline', '__pycache__', 'node_modules')]
        for f in files:
            if not f.endswith('.py'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, f), ROOT).replace(os.sep, '/')
            if rel in allow or rel.split('/')[-1] in allow:
                continue
            try:
                lines = open(os.path.join(dirpath, f), encoding='utf-8', errors='replace').read().splitlines()
            except OSError:
                continue
            for i, l in enumerate(lines, 1):
                code = l.split('#', 1)[0]
                if pat.search(code) and 'served by _baci' not in l:
                    offenders.append('%s:%d' % (rel, i))
                    break
    if offenders:
        fail('baci_door', '%d builders still open raw/baci/ themselves instead of going through baci.py: %s'
             % (len(offenders), ', '.join(offenders[:8]) + (' ...' if len(offenders) > 8 else '')))


def check_register():
    """Every folder under raw/ has a row in the register. Invariant for phase 4.

    raw/ is gitignored - 3.7 GB, all re-downloadable - so the repository's only knowledge of what
    was collected, under what licence, and why, is DATA_LIBRARY.md. A folder that arrives without a
    note is a file on a disk that nobody can account for, and the whole point of the register is
    that it cannot silently happen.

    The register also derives `read_by` and `reaches_cube` from the observed graph. Those are not
    checked here: a dataset read by nothing is a judgement about priorities, not an error, and
    turning it into a gate would push people to delete reference data to get a green tick.
    """
    lp = os.path.join(ROOT, 'out', 'library.json')
    if not os.path.exists(lp):
        warn('register', 'out/library.json missing - run `python build_library.py`')
        return
    try:
        lib = json.load(open(lp, encoding='utf8'))
    except Exception as e:
        fail('register', f'library.json unreadable: {e}'); return
    undoc = lib.get('undocumented') or []
    if undoc:
        fail('register', '%d raw/ folder(s) held with no register row: %s - add a note in '
                         'build_library.NOTES' % (len(undoc), ', '.join(undoc[:6])))
    known = {r['folder'] for r in lib.get('library', ())}
    rawdir = os.path.join(ROOT, 'raw')
    if not os.path.isdir(rawdir):
        return                              # a clone without the data: the record still stands
    # The register's own unit is a DIRECT CHILD of raw/, with raw/iea_bulk expanded one level
    # because it holds one folder per IEA dataset. Walking every directory instead would report
    # raw/ itself and every nested subfolder as missing, which is noise, not a finding.
    seen = set()
    for name in sorted(os.listdir(rawdir)):
        p = os.path.join(rawdir, name)
        if not os.path.isdir(p):
            continue
        kids = [os.path.join(p, k) for k in sorted(os.listdir(p))] if name == 'iea_bulk' else []
        for q in (kids or [p]):
            if os.path.isdir(q) and any(True for _, _, fs in os.walk(q) for _ in fs):
                seen.add(os.path.relpath(q, ROOT).replace(os.sep, '/'))
    missing = sorted(f for f in seen if f not in known)
    if missing:
        fail('register', '%d folder(s) on disk under raw/ are absent from the register: %s - run '
                         '`python build_library.py`' % (len(missing), ', '.join(missing[:6])))


def check_stale():
    """An output whose inputs or producer changed must be rebuilt. Invariant I4.

    This is the germanium guard in its general form. The drift check above compares two specific
    files because that specific pair burned us; this one compares every builder against the
    content of everything it reads, so the next pair does not need to burn us first.

    It asks runner.py, which fingerprints each builder from its own source, the content of every
    input nothing else produces, and - recursively - the fingerprints of its producers. Content,
    never mtime: a fresh clone resets every timestamp and must not read as stale.

    Going red here is not a bug in the gate. It means a file changed and something that reads it
    did not rebuild, which is precisely the state that shipped a retracted germanium score for
    three weeks. Clear it with `python runner.py --run`, or - if the change genuinely cannot move
    any output - `python runner.py --accept`, which records that judgement instead of hiding it.
    """
    if not os.path.exists('runner.py'):
        return
    if not os.path.exists('_runner_state.json'):
        warn('stale', 'no _runner_state.json - run `python runner.py --accept` to set the baseline')
        return
    r = subprocess.run([sys.executable, 'runner.py'], capture_output=True, text=True)
    out = (r.stdout or '') + (r.stderr or '')
    if 'CYCLE among' in out:
        fail('stale', 'the builder graph has an undeclared cycle - a rebuild order cannot exist: '
                      + out.strip().splitlines()[-1][:160])
        return
    if r.returncode != 0:
        warn('stale', 'runner.py could not report: %s' % out.strip()[-160:])
        return
    if 'nothing is stale' in out:
        return
    names = [ln.strip().split()[0] for ln in out.splitlines()
             if ln.strip().endswith('never built') or ln.strip().endswith('inputs or code changed')]
    head = ', '.join(names[:6]) + (' and %d more' % (len(names) - 6) if len(names) > 6 else '')
    fail('stale', '%d builder(s) have inputs or code newer than their last build: %s '
                  '- run `python runner.py --run`' % (len(names), head))


CHECKS = [('drift', check_drift), ('datasets', check_datasets), ('links', check_links), ('js', check_js),
          ('scrub', check_scrub), ('etapes', check_etapes), ('withdrawn', check_withdrawn),
          ('builders', check_builders), ('chokepoint', check_chokepoint_sync), ('ledger', check_ledger),
          ('basis', check_basis), ('anchor', check_anchor_sync), ('dim', check_dim), ('key', check_series_key), ('sdmx', check_sdmx), ('mirror', check_mirror_independence), ('withheld_src', check_withheld), ('baci_door', check_baci_door), ('stale', check_stale), ('register', check_register)]

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
