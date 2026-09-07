# -*- coding: utf-8 -*-
"""Publish, for every source we will not hand over, exactly how to fetch it first-hand.

"You cannot have this" is not an answer a research firm can sell, and a licence refusal that ends
there reads as either evasion or incompetence. It is neither: the holder's terms let us USE their
records and not republish them, which is an ordinary and reasonable condition.

So the refusal ships with its remedy. For each withheld source this writes the holder, the reason,
the cost, where to register, the exact endpoint and parameters, the code in this repository that
performs those calls, and the traps that cost us time - so a customer who needs the underlying
rows spends an afternoon getting them rather than reverse-engineering our silence.

What we do NOT withhold is the part that is actually ours: the two-sided reconciliation, where two
independent customs services declared the same shipment and the published figure is the output of
our method. That is a derived statistic, it reproduces neither declaration, and it is CC BY 4.0.

Run:  python build_retrieval.py
"""
import json
import os

import licences

ROOT = os.path.dirname(os.path.abspath(__file__))


def build():
    doc = {
        'title': 'Sources we cannot redistribute, and how to get them yourself',
        'principle':
            'A licence that forbids redistribution does not forbid analysis, and it does not own '
            'the conclusions. Everything the Atlas derives is published. Where a figure is still '
            'substantially the holder\'s own record, we withhold it and hand you the recipe.',
        'published': {k: v for k, v in licences.LICENCES.items()},
        'withheld': [],
    }
    for src, why in sorted(licences.WITHHELD.items()):
        r = licences.recipe(src) or {}
        doc['withheld'].append({'source': src, 'reason': why, **r})
    p = os.path.join(ROOT, 'out', 'retrieval.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    return doc, p


if __name__ == '__main__':
    d, p = build()
    print('wrote %s' % os.path.relpath(p, ROOT))
    print('  %d sources published, %d withheld with a recipe'
          % (len(d['published']), len(d['withheld'])))
    for w in d['withheld']:
        print('   - %s -> %s' % (w['source'], w.get('endpoint', 'NO ENDPOINT')))
