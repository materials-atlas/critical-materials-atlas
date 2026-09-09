# -*- coding: utf-8 -*-
"""Move every BACI reader onto baci.py, in one sweep. Phase 2 of ARCHITECTURE.md.

WHY ONE SWEEP AND NOT "AS TOUCHED"
A reviewer said it plainly: migrating lazily keeps a proven bug class alive for months by choice.
So this patches all of them at once, mechanically, and the acceptance harness (phase2_accept.py)
then demands that every output reproduce byte for byte. A patch that changes a number is a patch
that failed, until the change is explained and accepted by name.

WHAT IT CHANGES, AND WHAT IT REFUSES TO
- Every open() / pd.read_csv() of raw/baci/country_codes -> _baci.country_file(), a VERBATIM
  in-memory copy. The reader keeps its own DictReader, its own filters, its own NA handling.
  Nothing downstream moves. (Fixing Namibia, which pd.read_csv silently drops, is deliberately
  NOT done here - a migration that also fixes things cannot be told apart from one that broke.)
- Every pandas read of a zip member -> _baci.year(<year>, columns=[...]). Same columns, same row
  order (the extract preserves it), same dtypes where it matters (k is str; v, q are float).
- Every line-by-line CSV loop -> the same loop over _baci.year(...).itertuples(), row order
  preserved, with the file's own filters reproduced exactly. The loop's TAIL - the accumulation
  code - is kept verbatim and re-indented, never rewritten.
- build_catalog.py's zip listing -> baci.NOMENCLATURE. It never read data, only member names.
- The nine chain extractors superseded by build_chain_trade.py are DELETED, not migrated. They
  write the same files with different content; the committed files match build_chain_trade.

Dry run by default: reports what it would do, writes nothing. --apply writes. Then a coverage
scan lists every in-scope file that still mentions raw/baci or ZipFile - the hand-patch list.

Run:  python migrate_baci.py            # dry run
      python migrate_baci.py --apply
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SCOPE = json.load(io.open(os.path.join(ROOT, '_phase2_scope.json'), encoding='utf-8'))['readers']

# Superseded by build_chain_trade.py: same output file, different bytes, committed = build_chain_trade.
DEAD = {
    'battery-chain/extract_baci.py', 'data-centre-chain/extract_baci.py',
    'electrolyser-chain/extract_baci.py', 'ev-chain/extract_baci.py', 'grid-chain/extract_baci.py',
    'heat-pump-chain/extract_baci.py', 'magnet-chain/extract_baci.py', 'nuclear-chain/extract_baci.py',
    'wind-chain/extract_baci.py',
}

IMPORT_TOP = ("import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)));"
              " import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)")
IMPORT_SUB = ("import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))));"
              " import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)")

CC_PATH = (r"os\.path\.join\(\s*(?:ROOT|RAW)\s*,\s*(?:['\"]raw['\"]\s*,\s*['\"]baci['\"]\s*,\s*)?"
           r"(?:['\"]country_codes_V202601\.csv['\"]|f['\"]country_codes_\{VER\}\.csv['\"])\s*\)")
KW = r"(?:\s*,\s*(?:encoding|newline)\s*=\s*['\"][^'\"]*['\"])*"

report = []


def note(f, what):
    report.append((f, what))


# ── generic: replace a compound loop's HEADER, keep its TAIL verbatim (re-indented) ──────────
def replace_loop(text, anchor, marker, new_header, f):
    """anchor: exact first line of the old compound statement. marker: exact line inside it after
    which the accumulation tail begins. new_header: the replacement lines, ending with the marker
    line at its new indent. The old tail is dedented by the difference and appended."""
    lines = text.split('\n')
    try:
        a = next(i for i, l in enumerate(lines) if l == anchor)
    except StopIteration:
        note(f, 'HAND-PATCH: anchor not found: %r' % anchor.strip()[:60]); return text
    ind = len(anchor) - len(anchor.lstrip())
    end = a + 1
    while end < len(lines) and (not lines[end].strip() or len(lines[end]) - len(lines[end].lstrip()) > ind):
        end += 1
    try:
        m = next(i for i in range(a, end) if lines[i] == marker)
    except StopIteration:
        note(f, 'HAND-PATCH: marker not found: %r' % marker.strip()[:60]); return text
    old_tail_ind = len(marker) - len(marker.lstrip())
    new_marker = new_header[-1]
    new_tail_ind = len(new_marker) - len(new_marker.lstrip())
    delta = old_tail_ind - new_tail_ind
    tail = []
    for l in lines[m + 1:end]:
        if l.strip():
            cur = len(l) - len(l.lstrip())
            tail.append(' ' * (cur - delta) + l.lstrip())
        else:
            tail.append(l)
    # trailing blank lines inside the compound belong after it
    out = lines[:a] + new_header + tail + lines[end:]
    note(f, 'loop rewritten from %r (%d lines -> %d)' % (anchor.strip()[:40], end - a, len(new_header) + len(tail)))
    return '\n'.join(out)


# ── the mechanical substitutions ─────────────────────────────────────────────────────────────
def sub_country(text, f):
    n = 0
    # open(<country path>[, encoding=...]) and open(COUNTRIES|CODES_CSV|CODES, ...)
    pat = re.compile(r"open\(\s*(?:" + CC_PATH + r"|COUNTRIES|CODES_CSV|CODES)" + KW + r"\s*\)")
    text, k = pat.subn('_baci.country_file()', text); n += k
    # pd.read_csv(<country path>[, encoding=...][, other kwargs...])
    pat = re.compile(r"pd\.read_csv\(\s*" + CC_PATH + r"(?:\s*,\s*encoding\s*=\s*['\"][^'\"]*['\"])?")
    text, k = pat.subn('pd.read_csv(_baci.country_file()', text); n += k
    # the constants those opens used
    pat = re.compile(r"^(COUNTRIES|CODES_CSV|CODES)(\s*=\s*)os\.path\.join\([^\n]*country_codes[^\n]*$", re.M)
    text, k = pat.subn(r"\1\2None  # served by _baci.country_file()", text); n += k
    # product codes (build_ps_network)
    pat = re.compile(r"pd\.read_csv\(\s*os\.path\.join\(ROOT, 'raw', 'baci', 'product_codes_HS17_V202601\.csv'\)")
    text, k = pat.subn("pd.read_csv(_baci.product_file('HS17')", text); n += k
    if n:
        note(f, 'country/product file -> _baci (%d)' % n)
    return text


def year_expr(member, text):
    """(year expression, nom expression) from the member string a reader opened.

    nom matters: CEPII publishes every nomenclature for every year since it began, so 2017-2024
    exist in BOTH HS02 and HS17 and are different tables. A reader that read HS02 must keep
    reading HS02. The first sweep dropped this and served HS17 to build_avalidate: a 37% change
    that the acceptance harness caught. HS17 is the accessor's default and is omitted."""
    s = member.strip()
    m = re.match(r"f['\"]BACI_(HS\d\d)_Y\{(\w+)\}_V202601\.csv['\"]$", s)
    if m:
        return m.group(2), (repr(m.group(1)) if m.group(1) != 'HS17' else None)
    m = re.match(r"f['\"]BACI_\{(\w+)\}_Y\{(\w+)\}_(?:V202601|\{VER\})\.csv['\"]$", s)
    if m:
        return m.group(2), m.group(1)
    m = re.match(r"(\w+)\.format\((\w+)\)$", s)
    if m:
        d = re.search(r"^\s*%s\s*=\s*['\"]BACI_(HS\d\d)_Y" % m.group(1), text, re.M)
        return m.group(2), (repr(d.group(1)) if d and d.group(1) != 'HS17' else None)
    m = re.match(r"(\w+)$", s)
    if m:
        d = re.search(r"^\s*%s\s*=\s*f['\"]BACI_(HS\d\d|\{\w+\})_Y\{(\w+)\}_(?:V202601|\{VER\})\.csv['\"]" % m.group(1), text, re.M)
        if d:
            nomtok = d.group(1)
            nom = nomtok.strip('{}') if nomtok.startswith('{') else (repr(nomtok) if nomtok != 'HS17' else None)
            return d.group(2), nom
    return None, None


def _year_call(y, nom, columns):
    return '_baci.year(%s, columns=%s%s)' % (y, columns, (', nom=%s' % nom) if nom else '')


def sub_pandas_zip(text, f):
    n = 0
    # with zipfile.ZipFile(X) as z:\n    raw = pd.read_csv(io.TextIOWrapper(z.open(MEMBER), encoding='utf-8'),\n dtype={'k': str}, usecols=COLS)
    pat = re.compile(r"^(\s*)with zipfile\.ZipFile\(\w+\) as (\w+):\n\s+(\w+) = pd\.read_csv\(io\.TextIOWrapper\(\2\.open\((.+?)\), encoding='utf-8'\),\s*\n?\s*dtype=\{'k': str\}, usecols=(\[[^\]]*\]|\w+)\)[ \t]*\n", re.M)

    def rep(m):
        nonlocal n
        y, nom = year_expr(m.group(4), text)
        if y is None:
            note(f, 'HAND-PATCH: cannot resolve year from member %r' % m.group(4)); return m.group(0)
        n += 1
        return '%s%s = %s\n' % (m.group(1), m.group(3), _year_call(y, nom, m.group(5)))
    text = pat.sub(rep, text)
    # the same read without an adjacent with-block (a function receiving zf)
    pat2 = re.compile(r"^(\s*)(\w+) = pd\.read_csv\(io\.TextIOWrapper\((\w+)\.open\((.+?)\), encoding='utf-8'\),\s*\n?\s*dtype=\{'k': str\}, usecols=(\[[^\]]*\]|\w+)\)[ \t]*\n", re.M)

    def rep2(m):
        nonlocal n
        y, nom = year_expr(m.group(4), text)
        if y is None:
            note(f, 'HAND-PATCH: cannot resolve year from member %r' % m.group(4)); return m.group(0)
        n += 1
        return '%s%s = %s\n' % (m.group(1), m.group(2), _year_call(y, nom, m.group(5)))
    text = pat2.sub(rep2, text)
    text, k = re.subn(r"with zipfile\.ZipFile\(ZIP\) as zf:", "with _baci.no_archive() as zf:", text); n += k
    if n:
        note(f, 'pandas zip read -> _baci.year (%d)' % n)
    return text


# ── the hand patches: exact anchors, tails kept ──────────────────────────────────────────────
def patch_chain_template(text, f):
    anchor = '    for hs, years, archive, member in BATCHES:'
    marker = '                        row = bag[year][p[3]]'
    new = [
        '    for hs, years, archive, member in BATCHES:',
        '        for year in years:',
        '            print("reading", year, hs, flush=True)',
        '            for p in _baci.year(year, columns=["i", "j", "k", "v", "q"], codes=CODES).itertuples(index=False):',
        '                exporter, importer = iso_map.get(str(p.i)), iso_map.get(str(p.j))',
        '                if not exporter or not importer or exporter == importer:',
        '                    continue',
        '                if p.v != p.v:',
        '                    continue          # value NA -> the old float() raised and skipped the row',
        '                usd = p.v * 1000',
        '                if usd <= 0:',
        '                    continue',
        '                tonnes = p.q if p.q == p.q else 0.0',
        '                row = bag[year][p.k]',
    ]
    return replace_loop(text, anchor, marker, new, f)


def patch_chain_trade(text, f):
    """build_chain_trade.py - the 48-file writer. The first sweep patched its country read and
    missed its archive loop; the opens-only ratchet caught it. Same shape as the chain template,
    with ALL_CODES / CODE_TO_CHAINS instead of CODES."""
    anchor = '    for hs, years, archive, member in BATCHES:'
    marker = '                        for ch in CODE_TO_CHAINS[code]:'
    new = [
        '    for hs, years, archive, member in BATCHES:',
        '        for year in years:',
        '            vintage[year] = hs',
        '        for year in years:',
        '            print("reading", year, hs, flush=True)',
        '            for p in _baci.year(year, columns=["i", "j", "k", "v", "q"], codes=ALL_CODES).itertuples(index=False):',
        '                code = p.k',
        '                exporter, importer = iso_map.get(str(p.i)), iso_map.get(str(p.j))',
        '                if not exporter or not importer or exporter == importer:',
        '                    continue',
        '                if p.v != p.v:',
        '                    continue',
        '                usd = p.v * 1000',
        '                if usd <= 0:',
        '                    continue',
        '                tonnes = p.q if p.q == p.q else 0.0',
        '                for ch in CODE_TO_CHAINS[code]:',
    ]
    return replace_loop(text, anchor, marker, new, f)


def patch_silicon(text, f):
    anchor = '    for batch in BATCHES:'
    marker = '                        cell = bag[year][k]'
    new = [
        '    for batch in BATCHES:',
        '        for year in batch["years"]:',
        '            print(f"reading {year} {batch[\'hs\']} …", flush=True)',
        '            for p in _baci.year(year, columns=["i", "j", "k", "v", "q"], codes=set(CODES)).itertuples(index=False):',
        '                k = p.k',
        '                exp = iso_map.get(str(p.i))',
        '                imp = iso_map.get(str(p.j))',
        '                if not exp or not imp or exp == imp:',
        '                    continue',
        '                if p.v != p.v:',
        '                    continue',
        '                usd = p.v * 1000.0',
        '                if usd <= 0:',
        '                    continue',
        '                tonnes = p.q if p.q == p.q else 0.0',
        '                cell = bag[year][k]',
    ]
    return replace_loop(text, anchor, marker, new, f)


def patch_network_sensitivity(text, f):
    anchor = "with zipfile.ZipFile(zp).open('BACI_HS17_Y2024_V202601.csv') as fh:"
    marker = '        for lab in c2l[p[3]]:'
    new = [
        "for p in _baci.year(2024, columns=['i', 'j', 'k', 'v'], codes=set(CODES)).itertuples(index=False):",
        '    frm, to = num2iso.get(str(p.i)), num2iso.get(str(p.j))',
        '    if not frm or not to or frm == to:',
        '        continue',
        '    if p.v != p.v:',
        '        continue',
        '    v = p.v',
        '    for lab in c2l[p.k]:',
    ]
    return replace_loop(text, anchor, marker, new, f)


def patch_vq(text, f):
    anchor = '    with zipfile.ZipFile(zpath).open(name) as fh:'
    marker = '            for lab in c2l[p[3]]:'
    new = [
        "    for p in _baci.year(year, columns=['i', 'k', 'v', 'q'], codes=codes, nom=hs).itertuples(index=False):",
        '        frm = num2iso.get(str(p.i))',
        '        if not frm:',
        '            continue',
        '        if p.v != p.v:',
        '            continue',
        '        v = p.v * 1000.0',
        '        qv = p.q if p.q == p.q else 0.0',
        '        for lab in c2l[p.k]:',
    ]
    return replace_loop(text, anchor, marker, new, f)


def patch_cube_baci(text, f):
    # two simple statements precede the compound loop; replace_loop needs a compound anchor
    setup = ("    z = zipfile.ZipFile(ZIP)\n"
             "    files = sorted(n for n in z.namelist() if n.endswith('.csv') and '_Y' in n)\n")
    if setup not in text:
        note(f, 'HAND-PATCH: zip setup lines not found'); return text
    text = text.replace(setup, '', 1)
    anchor = '    for name in files:'
    marker = '                ex, im = num2iso.get(row[1].strip()), num2iso.get(row[2].strip())'
    new = [
        "    for yr in _baci.NOMENCLATURE['HS02']:          # 2002-2024, all in HS02 - as the archive loop always did",
        '        if years and yr not in years:',
        '            continue',
        "        for row in _baci.year(yr, columns=['i', 'j', 'k', 'q'], codes=wanted, nom='HS02').itertuples(index=False):",
        '            k = row.k',
        '            q = row.q',
        '            if q != q:',
        '                continue                          # value-only row: no tonnage to record',
        '            if q <= 0:',
        '                continue',
        '            ex, im = num2iso.get(str(row.i)), num2iso.get(str(row.j))',
    ]
    return replace_loop(text, anchor, marker, new, f)


def patch_goes(text, f):
    anchor = "    with zipfile.ZipFile(os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')) as z:"
    marker = "                    v = float(row['v'] or 0)"
    new = [
        '    for y in YEARS:',
        "        for row in _baci.year(y, columns=['i', 'k', 'v'], codes=ALL).itertuples(index=False):",
        '            k = row.k',
        '            e = iso.get(str(row.i))',
        '            if not e:',
        '                continue',
        '            v = row.v if row.v == row.v else 0.0',
    ]
    return replace_loop(text, anchor, marker, new, f)


def patch_two_stage(text, f):
    anchor = 'with zipfile.ZipFile(Z) as z:'
    marker = '            exp[k][iso] = exp[k].get(iso, 0.0) + q'
    new = [
        "for row in _baci.year(2023, columns=['i', 'k', 'v', 'q'], codes=WANT).itertuples(index=False):",
        '    k = row.k',
        '    iso = I2ISO.get(str(row.i))',
        '    if not iso: continue',
        '    q = row.q if row.q == row.q else row.v      # NULL q -> fall back to value, as before',
        '    if q != q: continue',
        '    exp[k][iso] = exp[k].get(iso, 0.0) + q',
    ]
    return replace_loop(text, anchor, marker, new, f)


def patch_catalog(text, f):
    old = """for z in sorted(glob.glob(os.path.join(ROOT, 'raw', 'baci', '*.zip'))):
    try:
        names = zipfile.ZipFile(z).namelist()
        yrs = sorted({int(n.split('_Y')[1][:4]) for n in names if '_Y' in n})
        vint = os.path.basename(z).replace('BACI_', '').replace('.zip', '')
"""
    new = """for nom, yrs in _baci.NOMENCLATURE.items():
    z = os.path.join(ROOT, 'raw', 'baci', 'BACI_%s_%s.zip' % (nom, _baci.VINTAGE))
    try:
        yrs = sorted(yrs)
        vint = '%s_%s' % (nom, _baci.VINTAGE)
"""
    if old in text:
        note(f, 'catalog zip listing -> _baci.NOMENCLATURE')
        return text.replace(old, new, 1)
    note(f, 'HAND-PATCH: catalog block not found')
    return text


HAND = {
    'build_chain_trade.py': patch_chain_trade,
    'build_network_sensitivity.py': patch_network_sensitivity,
    'build_vq.py': patch_vq,
    'build_cube_baci.py': patch_cube_baci,
    'grid-chain/build_goes.py': patch_goes,
    'build_two_stage.py': patch_two_stage,
    'build_catalog.py': patch_catalog,
    'silicon-chip/extract_baci.py': patch_silicon,
}
TEMPLATE = {'aerospace-chain', 'aluminium-chain', 'copper-chain', 'defence-chain', 'displays-indium-chain',
            'fibre-optics-chain', 'pgm-catalyst-chain', 'phosphate-food-chain', 'steel-alloys-chain'}


def inject_import(text, f):
    if 'import baci as _baci' in text:
        return text
    # A module docstring can start on ANY line (after a coding cookie, after comments) and can
    # contain a line that begins with "from " - build_mining_expansion.py has `from 2016 to 2024`
    # in its docstring, and the first version of this put the import inside it. So: track
    # triple-quote state from the top, and only accept an import that is outside a string.
    lines = text.split('\n')
    in_doc = None
    for i, l in enumerate(lines):
        s = l.strip()
        if in_doc:
            if in_doc in s:
                in_doc = None
            continue
        for q in ('"""', "'''"):
            if s.startswith(q):
                if s.count(q) == 1:          # opens and does not close on this line
                    in_doc = q
                break
        else:
            if s.startswith('import ') or s.startswith('from '):
                lines.insert(i + 1, IMPORT_SUB if '/' in f else IMPORT_TOP)
                return '\n'.join(lines)
    return IMPORT_TOP + '\n' + text


def migrate(f):
    p = os.path.join(ROOT, f)
    text = io.open(p, encoding='utf-8').read()
    orig = text
    # A file that already imports _baci may still hold an unpatched archive loop - the first
    # sweep left build_chain_trade.py exactly so. A hand patch is allowed through; its own
    # anchor/marker checks make it a no-op once applied. Files without a hand patch are done.
    if 'import baci as _baci' in text and f not in HAND:
        note(f, 'already migrated'); return text, False
    if 'import baci as _baci' in text and 'ZipFile' not in text:
        note(f, 'already migrated'); return text, False
    text = sub_country(text, f)
    if f in HAND:
        text = HAND[f](text, f)
    elif f.split('/')[0] in TEMPLATE and f.endswith('/extract_baci.py'):
        text = patch_chain_template(text, f)
    else:
        text = sub_pandas_zip(text, f)
    if text != orig:
        text = inject_import(text, f)
    return text, text != orig


def coverage(files):
    left = []
    for f in files:
        t = io.open(os.path.join(ROOT, f), encoding='utf-8').read()
        hits = [l.strip()[:90] for l in t.split('\n')
                if re.search(r"raw['\"]?\s*,\s*['\"]baci|raw/baci|ZipFile\(|country_codes_V|BACI_HS\d\d_V202601\.zip", l)
                and not l.strip().startswith('#') and 'served by _baci' not in l and '_baci.' not in l]
        if hits:
            left.append((f, hits))
    return left


def main():
    apply = '--apply' in sys.argv
    files = [f for f in SCOPE if f not in DEAD]
    changed = 0
    staged = {}
    for f in files:
        if not os.path.exists(os.path.join(ROOT, f)):
            note(f, 'missing on disk'); continue
        text, did = migrate(f)
        if did:
            changed += 1
            staged[f] = text
    print('%s: %d of %d in-scope files would change; %d dead extractors %s'
          % ('APPLY' if apply else 'DRY RUN', changed, len(files), len(DEAD), 'deleted' if apply else 'to delete'))
    for f, what in report:
        print('  %-40s %s' % (f, what))
    if apply:
        for f, text in staged.items():
            io.open(os.path.join(ROOT, f), 'w', encoding='utf-8', newline='').write(text)
        for f in DEAD:
            p = os.path.join(ROOT, f)
            if os.path.exists(p):
                os.remove(p)
        print('\nwritten. coverage scan of what still touches raw/baci:')
        files = [f for f in files if os.path.exists(os.path.join(ROOT, f))]
    else:
        print('\ncoverage scan (as the files are NOW, before --apply):')
    for f, hits in coverage(files if not apply else files):
        print('  %s' % f)
        for h in hits[:3]:
            print('      %s' % h)
    return 0


if __name__ == '__main__':
    sys.exit(main())
