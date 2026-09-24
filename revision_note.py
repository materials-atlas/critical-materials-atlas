# -*- coding: utf-8 -*-
"""The agency-disagreement note that BGS-based pages carry, from the revision measurement.

/revisions measures two things about a current-year production figure: how far the USGS moves its own
first estimate, and how far the USGS and BGS world totals sit apart. The first belongs beside a USGS
figure; the pages that import this are BGS-based, so the second is the one that applies. Putting a USGS
revision band beside a BGS number would say something the measurement does not support.

Read from out/usgs_revisions.json, so the note cannot drift from the study that computed it.
"""
import io
import json
import os

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
RESULT = os.path.join(ROOT, 'out', 'usgs_revisions.json')
NAME = {'rare_earths': 'rare earths'}


def gaps():
    """{(commodity, measure): median absolute world-total gap}, largest first."""
    if not os.path.exists(RESULT):
        return {}
    with io.open(RESULT, encoding='utf-8') as f:
        d = json.load(f)
    out = {}
    for k, v in d.get('usgs_vs_bgs', {}).items():
        c, m = k.rsplit('_', 1)
        out[(c, m)] = v
    return dict(sorted(out.items(), key=lambda kv: -kv[1]['median_abs_world_gap']))


def band_range():
    """(firmest commodity, its median, weakest commodity, its median) over the measured panel."""
    if not os.path.exists(RESULT):
        return None
    with io.open(RESULT, encoding='utf-8') as f:
        d = json.load(f)
    allc = dict(d.get('by_commodity', {}), **d.get('amendment_a', {}))
    if not allc:
        return None
    lo = min(allc, key=lambda c: allc[c]['world_median_abs_revision'])
    hi = max(allc, key=lambda c: allc[c]['world_median_abs_revision'])
    return (NAME.get(lo, lo), 100 * allc[lo]['world_median_abs_revision'],
            NAME.get(hi, hi), 100 * allc[hi]['world_median_abs_revision'], len(allc))


def pointer():
    """For a page whose figures are current-year production shares from mixed sources: how much the
    underlying figure has moved between its first printing and its revision."""
    b = band_range()
    if not b:
        return ''
    lo, lov, hi, hiv, n = b
    return ('<p class="howto-src"><b>What a current-year share rests on.</b> A physical share is '
            'computed from production figures whose first printing is an estimate, and the next '
            'edition revises it. Measured across %d commodities and thirty years of editions, the '
            'world total ends up a median %.1f%% from its first estimate for %s and %.1f%% for %s. '
            'A share built on those figures inherits that movement, which is the thing to check '
            'before reading a small year-on-year change as a trend: '
            '<a href="revisions">how firm is a current-year production figure?</a></p>'
            % (n, lov, lo, hiv, hi))


def note(materials=None, mine_only=True, lead=None):
    """One paragraph: how far the USGS world total sits from the BGS one, per commodity.

    `materials` limits the list to what the page actually shows (atlas names, lowercase); None lists
    every measured series.
    """
    g = gaps()
    if not g:
        return ''
    rows = [(c, m, v) for (c, m), v in g.items()
            if (not mine_only or m == 'mine') and (materials is None or c in materials)]
    if not rows:
        return ''
    parts = ', '.join('%s %.1f%%' % (NAME.get(c, c), 100 * v['median_abs_world_gap'])
                      for c, m, v in rows)
    y0 = min(v['years'][0] for _, _, v in rows)
    y1 = max(v['years'][1] for _, _, v in rows)
    return ('<p class="howto-src"><b>How far the other agency sits from these figures.</b> ' +
            (lead or 'The numbers on this page are BGS.') + ' For the commodities where the atlas has '
            'measured it, the USGS world '
            'total for the same commodity and stage differs from the BGS one by a median of: %s '
            '(median absolute difference over %d&ndash;%d, unsigned). That is a disagreement between two '
            'compilations, not an error bar and not a correction of either &mdash; it can be '
            'measurement, definition, coverage or vintage. The same measurement also shows how far the '
            'USGS moves its own current-year estimate, which is the figure to check before treating a '
            '<a href="revisions">how firm is a current-year production figure?</a></p>'
            'figure?</a></p>' % (parts, y0, y1))
