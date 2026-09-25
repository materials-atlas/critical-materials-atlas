# Amendment A — the same measure on every commodity in the panel — filed 2026-09-24

Filed before any revision was computed for the nine commodities it adds. What was already known: the
result for the six the original filing names (copper, tungsten, antimony, graphite, cobalt, rare
earths), published at `/revisions`. Nothing about the measure, the thresholds or the direction rule
changes here; only the set of commodities does.

## Why

The panel behind the study grew from six commodities to fifteen (the 2000-2003 chapters cut from the
yearly volumes, and gallium, germanium, lithium, nickel, manganese, indium, tin, tellurium and
magnesium). Six was the set the data happened to hold when the study was filed, not a claim about
which commodities revise most. Running the same measure on the rest either widens the finding or
exposes it as a feature of the six — and the second outcome is the more useful one.

## What is unchanged

The measure (first published against latest printing, as a percentage of the first), the exclusions
(only mine, refinery, smelter and plain production; flagged cells dropped; a year needs two usable
printings), the bands (firm under 2%, soft 2-5%, weak above 5%), the 60% upward-direction rule, and
the separation of unchanged reprints from revisions down. Tonnes throughout, so a unit change is not
read as a revision.

## What is added

Every other commodity the panel holds with at least **five** measurable world-total years. The floor
is set here, before the counts are seen: a median over fewer than five years is not worth a band, and
a commodity below it is reported as "too few years to band", never as a null.

## Readings, decided now

1. The six originally filed keep their own table and are not re-read here.
2. For each added commodity: the same world and China medians, the largest single world revision, the
   up / down / unchanged shares, and the band on both windows.
3. **The question this amendment asks:** do the six filed commodities sit at the extremes of the wider
   set, or in the middle of it? Read off the ranks, and reported either way. If antimony stops being
   the worst, or copper the firmest, the published page says so.
4. No commodity-specific story is told from the added set without checking its own chapters, because
   the largest percentage moves in this data have been small producers on tiny bases.

## What this cannot say

The added commodities carry fewer editions in some cases (gallium and germanium print world output as
prose in several years, so they contribute few measurable years), and a median over few years is not
comparable with one over twenty-five. The count of years is reported beside every median, and the
five-year floor is a floor, not a guarantee of precision.

## Deviations log

Every change made after this filing goes here, dated, with its reason.
**2026-09-24 — deviation 1: each commodity is read at its own primary stage, not at "mine".**
The filing says the measure runs on mine, refinery, smelter and plain production. The code that
summarises a commodity took its world totals from the `mine` rows alone, and the code that selected
rows for the study omitted plain production altogether. Five of the nine added commodities do not
tabulate a mine stage at all — germanium, indium and tellurium are refinery chapters, gallium and
magnesium print plain production — so they scored zero measurable years, and gallium was dropped
before it could be counted. Fixed by selecting, per commodity, the measure carrying the most printed
world totals (its primary stage), and reporting that measure beside every median. No filed commodity
changes: all six are mine chapters and their numbers are identical to the published table.

**2026-09-24 — deviation 2: the "last ten years" column is each chapter's last ten *printed* years.**
The filed measure takes the recent window as the ten years up to a commodity's own latest measurable
year. For the six filed commodities that is 2015-2024, and the published page calls it "the last ten
years". Two added commodities stop earlier — the USGS prints no germanium world total after 2016 and
no magnesium one after 2018 — so their windows are 2007-2016 and 2009-2018. The computation is
unchanged; the column is relabelled "last 10 printed" and every added commodity's window is printed
beside its number, because a window that closed a decade ago says nothing about a current figure.

**2026-09-24 — deviation 3: one table the USGS renamed mid-series is read as one series.**
Magnesium's "World Primary Production and Reserves" table is parsed as `production` through the 2020
edition and as `smelter` from 2021, because the row label changed. Read as two measures it became two
half-series that never meet, and everything after 2018 dropped out. They are merged where the evidence
says it is one table: the same printed caption, and no edition printing both. Copper's mine and
refinery tables fail the second test — six editions print both — and are left separate. Magnesium's
window moves from 2009-2018 to 2015-2024 and its measurable years from 15 to 25.

**2026-09-24 — deviation 4: four chapters were being dropped whole, and one was the wrong commodity.**
Found while checking the germanium window, not by the guard. (a) A table caption often carries the
previous paragraph's footnote reference ahead of it, so the line reads "8 World Refinery Production and
Reserves:" and the caption test, anchored on "World", failed: germanium 2021, nickel 2017, manganese
1996 and manganese 2000-2001 were skipped entirely. The marker is now stripped by type size, as
everywhere else in this parser. (b) The 2000-2003 volume cutter matched the chapter title as a prefix,
so for magnesium it cut MAGNESIUM COMPOUNDS — magnesite, a different commodity — instead of MAGNESIUM
METAL. Those four files parsed to nothing, so no magnesite figure ever entered the store, but the cut
now requires the chapter's own title and rejects a longer one. Counts after the repair: manganese 26
measurable years (was 24), nickel 26 (24), germanium 16 (14), magnesium 25. **No figure for the six
filed commodities changes** — their editions were complete before and after, and the published medians
are identical.

**2026-09-24 -- deviation 5: the direction rule is read on the filing's denominator.**
The filing defines the direction as "the share of *revisions* that are upward", at 60%. The code divided
by every printing, unchanged reprints included, which is a looser test and the one behind the published
sentence "no commodity has a direction". Both denominators are now computed and reported. On the
filing's wording two commodities clear 60% upward, both of them added by this amendment: gallium 86% of
its revisions (7 measurable years) and indium 66% (24 years). None of the six filed commodities reaches
60% on either denominator -- the highest is rare earths at 59% of its revisions -- so the published
section stands, but its wording now names the denominator.

**2026-09-24 -- deviation 6: the window labelling, and a correction to deviation 2 above.**
Deviation 2 said "the USGS prints no germanium world total after 2016 and no magnesium one after 2018".
That was a statement about the store, not about the USGS, and it is wrong as written: deviations 3, 4 and
8 restored those years. The correct statement: the window is the ten years to each commodity's own last
measurable year, and the dates printed beside each median are the first and last measurable year inside
that window. It is 2015-2024 for twelve of the fifteen; the exceptions are germanium 2011-2020, gallium
2018-2024 and tellurium 2017-2024. Germanium's window ends in 2020 because the 2023 edition prints its
country table with every cell "NA" or "W", and because from the 2024 edition the chapter prints no world
germanium figure at all -- neither a table nor a number in the text (checked in the PDFs, 2024-2026).

**2026-09-24 -- deviation 7: deviation 3's arithmetic was wrong.**
It credited the magnesium merge with taking the commodity from 15 measurable years to 25. The merge adds
the years from 2019 on, which is 6, for 21; the other 4 come from the separate repair in deviation 4.
The merge's own risk is the join year measured across the rename, 2019: it moves 1.8%, and dropping it
moves magnesium's median from 4.53% to 4.54%, so the rename is not manufacturing a revision. A caption
can stay while a definition changes, so that is evidence and not proof, and the page says so.

**2026-09-24 -- deviation 8: three retrieval faults, one of which changed a published figure.**
Found by a fact-checking pass over this section, not by the guard. (a) The germanium 2019 chapter is
published as `mcs-2019-germa_0.pdf` and the fetcher's pattern did not allow the trailing `_0`. (b) Eleven
indium chapters and the 2004 rare-earth chapter are linked from their USGS pages with a duplicated path
segment, which returns 403; they are now retried under the two paths the USGS actually serves. (c) The
germanium, tellurium and indium chapters for 2003 sit inside the yearly volume and had never been cut out
of it. Effects: germanium 16 measurable years -> 19 (median 2.3% -> 3.0%, and its recent band is no longer
firm), indium 12 -> 24 (3.0% -> 5.0%), tellurium 13 -> 14 (7.0% -> 6.2%), and **rare earths, one of the six
filed commodities, moves from the published 2.5% over 24 years to 2.8% over 26, with its China median
going from 0.0% to 0.4%**; its band does not change. The rare-earths correction is logged in the filing as
well, since it changes a published figure. Tin's 1996 and 2004-2007 chapters are still missing: they are
not served under any of the three naming schemes (403 on all), so tin stands at 21 years.

**2026-09-24 -- deviation 9: what the page reports, after review.**
The amendment's reading 2 commits to the China median and the band on both windows for every added
commodity; the first draft of the page printed neither. Both are now in the table. Two further
disclosures were added because the reviewers were right that the ranking implies more than it can carry:
the fifteen-way order mixes stages, so the ten mine chapters are also ranked on their own (antimony 11.6,
lithium 7.3, graphite 6.9, cobalt 5.7, tungsten 5.3, tin 4.3, manganese 4.2, rare earths 2.8, nickel 2.1,
copper 1.5); and gallium's table is re-captioned "World Low-Purity Production and Production Capacity"
from the 2025 edition, a change this study has no check for, so its rank is provisional on that ground.

## Result -- filed question answered 2026-09-24

**The endpoints hold and the six do not sit together at the extremes.** Antimony still moves most (11.6%
over 25 years) and copper least (1.5% over 25), and no added commodity falls outside that range. But the
filed six sit at ranks 1, 4, 6, 7, 13 and 15 of fifteen, and three added commodities take ranks 2 to 4,
so the added set does not simply fill the middle either. Full order, all-year window: antimony 1 (11.6%),
gallium 2 (9.0%), lithium 3 (7.3%), graphite 4 (6.9%), tellurium 5 (6.2%), cobalt 6 (5.7%), tungsten 7
(5.3%), indium 8 (5.0%), magnesium 9 (4.5%), tin 10 (4.3%), manganese 11 (4.2%), germanium 12 (3.0%),
rare earths 13 (2.8%), nickel 14 (2.1%), copper 15 (1.5%).

On the same-stage reading -- the only one that compares like with like -- the commodity worth naming is
**lithium, second of the ten mine chapters at 7.3% over 25 measurable years**, the same window as copper
and above three of the six that were filed. That is the amendment's real addition to the finding.

One of the filing's own escape clauses fired, and one half-fired. Copper does **not** stop being the
lowest on the recent window -- at 2.07% it is still first of fifteen, with indium 2.17% behind it -- but
2.07% is above the 2% cut, so on that window its label is soft rather than firm. Rank kept, band lost,
and the page says both. (An earlier draft of this log said copper stopped being the firmest and named
germanium as the lowest; that was true of the numbers before deviation 8's retrieval repairs and is
wrong now.) The escape clause that did fire is the direction rule: read on the filing's denominator it is
reached by gallium and indium, so "no commodity has a direction" is true of the filed six and not of the
wider set.

**2026-09-24 -- deviation 10: tin's missing chapters were in the yearly volumes after all.**
Deviation 8 recorded that tin's 1996 and 2004-2007 chapters "are not served under any of the three
naming schemes (403 on all), so tin stands at 21 years". That was true of the commodity page, which
links nothing before its 2008 edition, and wrong as a conclusion: the full yearly volumes for 2004-2007
exist on the same path as the 2000-2003 ones already used, and carry the chapter. Cut from there, tin
moves from 21 measurable years to 25 and its median from 4.3% to 4.5%; its band and its rank of fifteen
do not change. 1996-1999 remain out, being scans. No other commodity gained a year from the wider
volume range -- their pages already link those editions. This is the fourth retrieval fault in the
study and the second time a "not served anywhere" conclusion was drawn from one route having failed.

**2026-09-25 — deviation 11: the panel grew again, to twenty-five, and the page had drifted from it.**
The self-audit needed a measured revision record for the concentration study's own materials, so ten
more commodities were added to the panel (lead, chromium, molybdenum, fluorspar, phosphate rock,
barite, feldspar, titanium, vanadium, zinc). Amendment A covers every commodity in the panel, so its
table grows with it and no new filing is needed for the set - but the page did not rebuild, because
`build_revisions.py` raised on a number it had no word for, and a builder that crashes leaves the last
good page in place with no symptom. For a day the published page described fifteen commodities while
the output file held twenty-five, and one sentence on it was wrong: tellurium was named as rank 4 when
the wider panel puts it at 8.

Fixed at the root rather than by editing the sentence: every rank, count and "of fifteen" on that page
is now computed from the panel, so the same drift cannot recur silently. **The endpoints and the filed
six are unchanged by the widening** - antimony still moves most and copper least, and the six now rank
1, 5, 10, 11, 21 and 25 of twenty-five, with four of the six largest movers being added commodities.
