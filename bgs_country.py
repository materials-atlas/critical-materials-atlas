# -*- coding: utf-8 -*-
"""The BGS panel's country codes, corrected once for every builder that reads them.

THE DEFECT
BGS ships `country_iso3_code` on every record, and in three cases it puts two different
countries on the same code. Found by asking a question the schema had never been asked: does
any ISO3 in the panel serve more than one country name? Three do.

  'Congo' (iso2 CG - the Republic of Congo, Brazzaville) is given iso3 COD, which is DR CONGO.
     A plain error in the source. 200 records across gold, copper, salt, lead, zinc, diamond,
     potash, tin and magnesium, overlapping DR Congo in every year from 1992. Its effect on DR
     Congo's totals is about 1% (copper +20 kt against 1,713 kt in 2020) - but the Republic of
     Congo disappears from the atlas entirely, which is the worse harm. Cobalt carries none of
     the bad records, so nothing published about DRC cobalt moves.
  'German Federal Republic' (1970-1992) and 'Germany' (1989-2024) both take DEU, and both are
     present 1989-1992. West Germany is not unified Germany.
  'Yemen (PDR)' (South Yemen, 1970-1991) and 'Yemen, Republic of' (1992-) both take YEM. They
     never overlap, but they are not the same state.

Two builders read the panel - the cube ingest and the concentration finding - and both summed
into a per-ISO3 dict, so both inherited the merge. The correction lives here rather than in
either of them, because two copies of a fix drift, and a drifted fix is the defect again.

Keyed on (country_trans, iso2), never on iso3: iso3 is the field that is wrong.
"""

COUNTRY_FIX = {
    ('Congo', 'CG'): 'COG',                        # Republic of Congo, mis-coded as DR Congo
    ('German Federal Republic', 'DE'): 'DEU_FRG',  # West Germany, distinct from unified Germany
    ('Yemen (PDR)', 'YD'): 'YMD',                  # Democratic Yemen (ISO 3166-3)
}

HISTORICAL = {
    'DEU_FRG': 'DEU (West Germany, 1970-1992; unified Germany is DEU)',
    'YMD': 'YEM (Democratic Yemen, 1970-1991)',
}


def resolve_iso3(rec):
    """The country an observation belongs to, correcting the source where it collides."""
    return (COUNTRY_FIX.get((rec.get('country_trans'), rec.get('country_iso2_code')))
            or rec.get('country_iso3_code'))


def collisions(names_by_iso):
    """Codes still serving more than one country name, after correction. Should be empty."""
    return {i: sorted(n for n in names if n) for i, names in names_by_iso.items()
            if len({n for n in names if n}) > 1}


def collision_message(bad):
    return ('BGS country codes collide - one ISO3 is serving two countries, so their figures '
            'would be summed:\n'
            + '\n'.join('    %s: %s' % (i, ', '.join(n)) for i, n in sorted(bad.items()))
            + '\nAdd the correction to COUNTRY_FIX in bgs_country.py, keyed on '
              '(country_trans, iso2).')
