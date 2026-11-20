#!/usr/bin/env python3
"""Point a printed PDF's links at the live site, not at the machine it was printed on.

brief.pdf and technical-note.pdf are rendered by printing the local HTML with headless Chrome/Edge.
The browser resolves every relative link against the local file, so the PDF ships links of the form
file:///<drive>/<folders>/critical-materials-atlas/<page>.html - broken for every reader, and they
publish the local folder path. Found 20 Nov 2026 in both PDFs. Run this after every print:

    python fix_pdf_links.py brief.pdf technical-note.pdf

Any file:// link is rewritten to https://criticalmaterialsatlas.org/<page>; `check.py` has no PDF
check, so this is the only guard.
"""
import re
import sys

import pypdf
from pypdf.generic import NameObject, TextStringObject

SITE = 'https://criticalmaterialsatlas.org/'


def live(uri):
    m = re.search(r'critical-materials-atlas/(.*)$', uri)
    page = m.group(1) if m else ''
    page = re.sub(r'\.html(?=$|#)', '', page).rstrip('/')
    return SITE + page


def fix(path):
    w = pypdf.PdfWriter(clone_from=pypdf.PdfReader(path))
    n = 0
    for page in w.pages:
        for annot in page.get('/Annots') or []:
            action = annot.get_object().get('/A')
            if action is None:
                continue
            action = action.get_object()
            uri = action.get('/URI')
            if uri and str(uri).lower().startswith('file:'):
                action[NameObject('/URI')] = TextStringObject(live(str(uri)))
                n += 1
    w.write(path)
    print('%s: %d local link(s) pointed at the live site' % (path, n))


if __name__ == '__main__':
    for p in sys.argv[1:] or ['brief.pdf', 'technical-note.pdf']:
        fix(p)
