"""
The four kinds of figure on the atlas - one definition, one look, used by every builder that labels a
number. Defined for readers on how-it-works.html#evidence (keep the two in step). Part B item 10,
23 Nov 2026.

    observed   read straight from a published source (a USGS mine share, a customs value)
    estimated  a gap filled where nobody measures, by the source or by us
    inferred   worked out from observed figures by a stated rule (the origin gap)
    modelled   depends on a model with assumptions or settings (nowcast, anchor, demand, risk weights)

The badge carries its own style, so it renders the same on pages that do not load assets/site.css.
"""
KINDS = {
    'observed':  ('#e2f0ec', '#0b6f66', 'Observed: read straight from a published source'),
    'estimated': ('#fdf4e7', '#a5641a', 'Estimated: a gap filled where nobody measures, by the source or by us'),
    'inferred':  ('#e6edf2', '#15323a', 'Inferred: worked out from observed figures by a stated rule'),
    'modelled':  ('#efe9f6', '#5b3a85', 'Modelled: depends on a model with assumptions or settings'),
}


def badge(kind):
    bg, fg, tip = KINDS[kind]
    return (f'<a href="how-it-works#evidence" title="{tip}" style="display:inline-block;font-size:.66rem;'
            f'font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 7px;border-radius:4px;'
            f'vertical-align:.12em;text-decoration:none;white-space:nowrap;background:{bg};color:{fg}">{kind}</a>')


def headline(kind):
    """The line under a page title that says what kind of figure the page's headline numbers are."""
    return (f'<p style="margin:.55rem 0 0;font-size:.82rem;opacity:.92">Headline figures on this page: '
            f'{badge(kind)}</p>')


def tagify(s):
    """Turn the store's provenance tags into badges in VISIBLE text ('[measured]' -> observed)."""
    return s.replace('[measured]', badge('observed')).replace('[estimate]', badge('estimated'))


def plain(s):
    """The same tags in a tooltip (title attribute), where HTML cannot go."""
    return (s or '').replace('[measured]', '(observed)').replace('[estimate]', '(estimated)')
