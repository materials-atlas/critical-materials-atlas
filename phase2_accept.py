# -*- coding: utf-8 -*-
"""The acceptance test for the BACI migration. Written BEFORE the migration, as promised.

WHAT IT PROVES
Every builder that opens raw/baci/ today is run, its outputs hashed, then its writes reverted. That
is the baseline. After the 56 readers are moved onto baci.py, the same run must produce the same
hashes. A reader that produces different bytes has changed a published number, and the migration
does not land until that is explained or fixed.

WHY PER (READER, OUTPUT) AND NOT PER OUTPUT
Eight chain trade files have TWO writers that produce DIFFERENT content (build_chain_trade.py and
the per-chain extract_baci.py). A single hash per file cannot express that. Keying on the pair
records what each writer produces, so the migration is judged writer by writer - and the race
itself stays visible instead of being averaged away.

WHY IT REUSES THE RECORDER
record_graph.run() already runs a builder in a subprocess under the audit hook and returns what it
wrote; record_graph.restore() already reverts tracked writes and leaves gitignored data stores
alone. Reusing them means this harness cannot degrade the repository in a way the recorder has
not already been made safe against.

Run:  python phase2_accept.py --baseline        # record, before touching anything
      python phase2_accept.py                   # compare, after migration
      python phase2_accept.py --only build_productspace
Out:  _phase2_hashes.json (baseline), stdout (comparison)
"""
import hashlib
import io
import json
import os
import sys

import record_graph as rg

ROOT = os.path.dirname(os.path.abspath(__file__))
SCOPE = os.path.join(ROOT, '_phase2_scope.json')
HASHES = os.path.join(ROOT, '_phase2_hashes.json')
ACCEPTED = os.path.join(ROOT, '_phase2_accepted.json')   # {reader: {output: reason}}


def sha(path):
    try:
        with open(path, 'rb') as fh:
            return hashlib.sha256(fh.read()).hexdigest()[:20]
    except OSError:
        return None


def run_all(readers, timeout):
    """{reader: {'exit':..., 'outputs': {path: sha}}} - hashed BEFORE the writes are reverted."""
    got = {}
    for n, b in enumerate(readers, 1):
        r = rg.run(b, timeout)
        outs = {w: sha(os.path.join(ROOT, w)) for w in r.get('writes', [])}
        rg.restore(r.get('writes', []))
        got[b] = {'exit': r['exit'], 'secs': r.get('secs'), 'outputs': outs}
        flag = ' ' if r['exit'] == 0 else '!'
        print('%s [%2d/%2d] %-42s %2d outputs %6.1fs %s'
              % (flag, n, len(readers), b[:42], len(outs), r.get('secs', 0),
                 '' if r['exit'] == 0 else str(r['exit'])[:50]), flush=True)
    return got


def main():
    a = sys.argv[1:]
    baseline = '--baseline' in a
    # .strip(): a name read from a file written on Windows carries a trailing CR, and a loop that
    # fed 23 such names once recorded one builder while reporting success. Whitespace is never
    # part of a builder's name.
    only = a[a.index('--only') + 1].strip() if '--only' in a else None
    timeout = int(a[a.index('--timeout') + 1]) if '--timeout' in a else 900

    scope = json.load(io.open(SCOPE, encoding='utf-8'))
    readers = [r for r in scope['readers'] if not only or r.startswith(only)]
    if not readers:
        raise SystemExit('--only %r matched no reader in scope' % only)
    print('%s %d BACI readers (timeout %ds)\n' % ('BASELINING' if baseline else 'COMPARING', len(readers), timeout))

    # The sweep DELETES the nine chain extractors superseded by build_chain_trade.py. A reader
    # that is gone by design is reported as such, not as a failure - and never silently skipped.
    gone = [r for r in readers if not os.path.exists(os.path.join(ROOT, r))]
    readers = [r for r in readers if r not in gone]
    for r in gone:
        print('  xx %-42s deleted (superseded; see migrate_baci.DEAD)' % r)

    got = run_all(readers, timeout)

    if baseline:
        held = json.load(io.open(HASHES, encoding='utf-8')) if os.path.exists(HASHES) else {}
        held.update(got)
        io.open(HASHES, 'w', encoding='utf-8').write(json.dumps(held, indent=1))
        bad = [b for b, v in got.items() if v['exit'] != 0]
        print('\nbaseline recorded for %d readers -> %s' % (len(got), os.path.relpath(HASHES, ROOT)))
        if bad:
            print('  %d did not run clean and are baselined as failing: %s' % (len(bad), ', '.join(bad)))
        return 0

    if not os.path.exists(HASHES):
        raise SystemExit('no baseline - run with --baseline first, BEFORE migrating anything')
    base = json.load(io.open(HASHES, encoding='utf-8'))
    # A difference that is KNOWN and CORRECT is accepted by name, with its reason, never by
    # loosening the comparison. The first dry run found one: pandas.read_csv reads Namibia's
    # ISO2 "NA" as missing, so every legacy reader silently dropped Namibia; baci.countries()
    # does not. That is a fix, and it must be recorded as one, per (reader, output).
    accepted = json.load(io.open(ACCEPTED, encoding='utf-8')) if os.path.exists(ACCEPTED) else {}
    same = changed = missing = newfail = acc = 0
    for b, v in got.items():
        was = base.get(b)
        if was is None:
            print('  ?  %-42s not in baseline' % b); continue
        if was['exit'] == 0 and v['exit'] != 0:
            newfail += 1
            print('  !! %-42s ran clean before, now fails: %s' % (b, str(v['exit'])[:60])); continue
        for path, h in was['outputs'].items():
            now = v['outputs'].get(path)
            reason = accepted.get(b, {}).get(path)
            if now is None:
                missing += 1; print('  -- %-42s no longer writes %s' % (b, path))
            elif now != h and reason:
                acc += 1; print('  ok %-42s changed, ACCEPTED: %s' % (b, reason))
            elif now != h:
                changed += 1; print('  != %-42s CHANGED %s' % (b, path))
            else:
                same += 1
    print('\nidentical %d | accepted %d | changed %d | missing %d | newly failing %d'
          % (same, acc, changed, missing, newfail))
    if changed or missing or newfail:
        print('MIGRATION NOT ACCEPTED. A different byte is a different number until shown otherwise.')
        return 1
    print('ACCEPTED: every output reproduces exactly.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
