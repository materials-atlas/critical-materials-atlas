# How much does the USGS revise its own production figures? — pre-registration

Filed 2026-09-23, before any revision was computed. What was read to plan it: the structure of
`pipeline/data/usgs_mcs_history.parquet` (which columns it holds, and that a data year appears in
more than one edition), the parser and its filing, and the printed MCS 2026 copper page. No revision,
distribution or summary had been computed when this was written.

## The question

Every chart that shows a latest year shows a number the USGS calls an estimate, and the next edition
revises it. **By how much, and in which direction?** A reader who takes this year's figure at face
value is making an implicit bet on that; this measures the bet. It applies to every page on this site
that quotes a current-year production figure.

## Data

`pipeline/data/usgs_mcs_history.parquet`, built by `pipeline/parse_usgs_mcs.py` from 150 Mineral
Commodity Summaries chapters, editions 1996-2026, for copper, tungsten, antimony, graphite, cobalt and
rare earths. Country rows and the printed world total; **mine, refinery and smelter production only**
— reserves are a stock, revised for reasons that have nothing to do with measuring a year's output.

## The measure

For one commodity, country (or the printed world total) and data year, take the editions that report
that year, oldest first.
- **First published** value: the earliest edition that reports the year. In an MCS chapter this is the
  newer of the two columns, the one the USGS marks as an estimate.
- **Latest** value: the value in the newest edition that reports the year.
- **Revision** = (latest − first) / first, as a percentage. Series where the first published value is
  zero, missing, withheld or a dash are dropped, and the drop count is reported.

Only years with **at least two editions** enter. The latest data year (reported by one edition so far)
cannot be measured and is excluded; its exclusion is stated, not hidden.

## Readings, decided now

1. **Headline, per commodity:** the median absolute revision of the printed **world total**, and of
   **China**, over all measurable years. Medians, not means, so one collapsed series cannot carry it.
2. **Direction:** the share of revisions that are upward, per commodity. Read as "revised up more often
   than down" only if that share is at least 60%, else "no consistent direction".
3. **Size bands, for the caution the site will carry:** a commodity's current-year figure is called
   **firm** if its median absolute world revision is under 2%, **soft** if 2-5%, and **weak** if above
   5%. These bounds are set here, before the numbers are seen.
4. **Settling:** whether a year keeps moving after its first revision, measured as the median absolute
   change between the second edition to report a year and the latest. Reported beside the headline.

## What this cannot say

It measures how the USGS's own published figure moved, not how close either version is to the truth;
both could be wrong in the same direction. Revisions are not independent across countries in a year
(the world total is revised with its parts). Country coverage changes across editions — a country
named in one edition can fall into "Other countries" in the next; those years are dropped for that
country, and the count is reported. Years where a chapter's unit changed are converted to tonnes
before comparison, so a unit change is not read as a revision.

## Result - run 2026-09-23

Run by `analysis.py`; every number is in `out/usgs_revisions.json`. 1,752 series (commodity, country or world total, measure, year) can be
measured; 752 cannot: 519 because only one edition reports them and 233 because a dash, a W or an NA left
fewer than two usable printings (deviation 6). The newest data year in each
chapter has been published once and cannot be measured yet.

### How far the first published figure moves

| Commodity | world, median abs revision | same, last 10 years | largest | China, median | up / down / unchanged | direction | band: filed / last 10 |
|---|---|---|---|---|---|---|---|
| antimony | 11.6% | 11.3% | 42.5% | 11.0% | 41% / 40% / 18% | no consistent direction | **weak** / **weak** |
| graphite | 6.9% | 8.3% | 29.9% | 5.7% | 26% / 36% / 39% | no consistent direction | **weak** / **weak** |
| cobalt | 5.7% | 3.6% | 29.0% | 4.7% | 49% / 38% / 13% | no consistent direction | **weak** / **soft** |
| tungsten | 5.3% | 2.4% | 55.0% | 5.6% | 42% / 43% / 15% | no consistent direction | **weak** / **soft** |
| rare earths | 2.5% | 3.1% | 17.1% | 0.0% | 38% / 27% / 36% | no consistent direction | **soft** / **soft** |
| copper | 1.5% | 2.1% | 3.8% | 5.0% | 53% / 42% / 5% | no consistent direction | **firm** / **soft** |

**A current-year figure is worth about what its commodity's band says.** Copper's world total is the firmest: it
moves 1.4% between its first and its latest printing over the whole period, 2.1% over the last ten
years, which is the difference between the filed "firm" and "soft" bands.
Antimony's moves 11.3%, and has moved 42.5%. Graphite's 6.5% gets worse in the recent decade, not
better (8.3%). The direction is not systematic. Under the filed rule - which licenses only an upward reading, at
60% - no commodity has a direction. Separating unchanged reprints from downward ones (deviation 11)
shows why an earlier draft of this result was wrong to call graphite and rare earths "revised down more
often than up": graphite's mine series are 25% up, 35% down and 40% UNCHANGED, and rare earths 39% up,
29% down, 32% unchanged. China's rare-earth
figure is the one that never moves: its median revision is 0.0%, which fits a number set by quota and
reported rather than measured.

The largest revisions are not the 1990s alone, but the single biggest are: tungsten's world total for
1995 went from 20,000 to 31,000 tonnes between the 1996 and 1997 editions (+55%), and China's from
10,000 to 21,000 in the same pair. That is why the recent decade is shown beside the whole period.

| Commodity | series | year | first published | latest | revision | editions |
|---|---|---|---|---|---|---|
| antimony | Kyrgyzstan | 2024 | 20 | 700 | +3400% | 2025 -> 2026 |
| rare earths | Brazil | 2024 | 20 | 560 | +2700% | 2025 -> 2026 |
| antimony | Kazakhstan | 2024 | 40 | 800 | +1900% | 2025 -> 2026 |
| rare earths | Malaysia | 2011 | 30 | 280 | +833% | 2012 -> 2013 |
| graphite | Turkey | 2005 | 1,000 | 6,000 | +500% | 2006 -> 2007 |
| graphite | Madagascar | 2018 | 9,000 | 46,900 | +421% | 2019 -> 2020 |

Those are small producers newly measured rather than errors corrected: Kyrgyzstan's antimony is
printed as 20 tonnes in the 2025 edition and 700 in the 2026 one, both marked estimates.

### Mine against refinery, from one source

USGS publishes a refinery table by country for copper only, so this is copper, 2025.

| Country | mine | share of world mine | refinery | share of world refinery |
|---|---|---|---|---|
| China | 1,800 | 8% | 14,000 | 48% |
| Congo (Kinshasa) | 3,200 | 14% | 2,800 | 10% |
| Chile | 5,300 | 23% | 1,700 | 6% |
| Japan | - | - | 1,400 | 5% |
| Russia | 1,300 | 6% | 950 | 3% |
| United States | 1,000 | 4% | 850 | 3% |
| India | 23 | 0% | 620 | 2% |
| Germany | - | - | 610 | 2% |
| Australia | 730 | 3% | 460 | 2% |
| Peru | 2,700 | 12% | 340 | 1% |
| Zambia | 940 | 4% | 270 | 1% |

**In this table China accounts for 8% of reported world mine production and 48% of reported refinery
production.** Mine shares and refinery shares are different maps, and a dependence read off mining alone
misses where the smelting and refining sit. A dash is printed where the chapter prints one, not a zero;
the rows are the eight largest on each measure. These are reported production, not ownership: a
Chinese-owned mine abroad counts in its host country, refined output includes scrap, and cathode won by
leaching at the mine counts in both columns.

### Where USGS and BGS disagree

Both count the same thing; neither is a correction of the other. The gap is the median absolute
difference in the world total (and China), USGS over BGS, on the years both cover.

| Commodity | USGS measure | BGS series | years | BGS reporters | world gap | China gap |
|---|---|---|---|---|---|---|
| graphite | mine | graphite | 2002-2024 | 17 | 30.7% | 31.0% |
| antimony | mine | antimony, mine | 2002-2024 | 15 | 13.1% | 15.5% |
| cobalt | mine | cobalt, mine | 2002-2024 | 19 | 12.7% | 25.0% |
| rare earths | mine | rare earth oxides | 2003-2024 | 7 | 7.0% | 3.5% |
| tungsten | mine | tungsten, mine | 2002-2024 | 21 | 6.9% | 8.6% |
| copper | refinery | copper, refined | 2019-2024 | 40 | 1.2% | 0.2% |
| copper | mine | copper, mine | 2002-2024 | 54 | 0.6% | 1.2% |

Copper is the close case (0.6% on mine over 2002-2024; 1.2% on refined, where the comparison covers
2019-2024 because BGS stops at 2024, though the USGS has printed a refinery world total since 2019).
Graphite is the far one at 30.7%, and not because the baskets differ - both series are natural graphite
and exclude synthetic material. China accounts for much of the early distance (BGS 1,800,000 t in 2010
against the USGS's 600,000) and that difference has closed: both print 1,270,000 t in 2024. But the
world totals are still 10% apart in that year, so the remainder is other countries, coverage or
rounding, and 30.7% is a median over 2002-2024, not today's gap. Rare earths compare at 7.0% on a BGS
series with a median of 7 reporting countries against a USGS table carrying 3-13 countries with output,
so coverage may be doing the work there.

## Deviations log

Every change made after this filing goes here, dated, with its reason.
1. **2026-09-23, before the first result - a zero row broke the unit conversion.** The USGS-against-BGS
   panel works out the chapter's unit factor from a country row (tonnes over printed value); the first
   such row for some commodity-years is a dash printed as zero, which divided by zero. It now takes the
   first non-zero row. Code fix, no result had been read.
2. **2026-09-23, after the first result - the same medians over the last ten data years, added.** The
   largest revisions are from the 1990s (tungsten's world total for 1995 went from 20,000 to 31,000
   tonnes between the 1996 and 1997 editions), which would make a caution drawn from the whole period
   too harsh for figures published now. The filed headline over all years is reported unchanged, with
   the recent-decade median beside it, and the band is given on both.
3. **2026-09-23, after the first result - the filed settling check cannot be computed, and the
   comparison is equal-exposure.** The filing asked for the movement between the second edition to
   report a year and the latest. There is none: an MCS edition prints last year as an estimate and the
   year before it revised, so **no series in this store is printed three times**: 144 world-total
   series have two editions (139 mine, 5 copper refinery) and 24 have one, counting a world row by its
   measure and year rather than by its printed label (the chapters spell it "World total (rounded)" and
   "World total (may be rounded)"; on the raw label it is 142 and 28), and none of the 2,065
   country series has three. An earlier draft of this entry said 139 and described it as every data
   year, which was the mine count only. "First against latest" is therefore "the estimate
   against its single revision", and every year carries the same exposure - the objection that older
   years have more chances to move does not apply here. The check is reported as not computable rather
   than as a zero.
4. **2026-09-23 - the BGS rare-earth comparison used the wrong form twice.** The comparison first
   looked for a BGS form named "rare earth minerals", which does not exist, so the row was dropped
   without a message. The next attempt used "rare earths", which is a residual category carrying ONE
   reporting country (925 t in 2024) against "rare earth oxides" with nine (360,714 t); it produced a
   meaningless 89% gap. The comparison now uses "rare earth oxides", names the BGS form in the output
   and carries the median number of BGS reporting countries, so a residual basket cannot pass as a
   disagreement again.
5. **2026-09-23 - the parser missed the unit line in every rare-earth chapter from 2010.** Those
   chapters bracket it ("[Data in metric tons, rare-earth-oxide (REO) equivalent...]") where others
   parenthesise it, and the search ran line by line while the line wraps. With no unit there were no
   tonnes, and the agency comparison silently stopped at 2008. The parser now reads the unit from the
   whole page and accepts either bracket; every row in the store now carries a unit.
6. **2026-09-23, after the council review - the dropped series were reported under one reason, and it
   was the wrong one.** The result said 692 series were dropped because the first edition printed a
   dash, a W or nothing. A fact-check recomputed it: 481 of them appear in only ONE edition at all (the
   newest data year, and years either side of a gap in the editions held), and 211 lost a printing to a
   flag. None was dropped for a zero first value. Both counts are now reported.
7. **2026-09-23 - the BGS comparison summed production, imports and exports.** The panel carries all
   three under the same commodity form and the code did not filter on the statistic type. It changed
   only graphite, whose BGS "world production" was the sum of all three: its median gap falls from 31.6%
   to 30.7% and the pre-2012 rows change materially. Production rows only, from now on.
8. **2026-09-23 - a 1,000x error inside the published comparison.** The USGS world total was converted
   to tonnes with a factor taken from another edition's country row. Graphite changed unit (thousand
   tonnes to tonnes) at the 2019 edition, so the 2017 row was multiplied by 1,000 and printed a 74,579%
   gap in the output file. The world total is now read in tonnes from the row that printed it. The
   median contained the error rather than ignoring it: graphite's published gap would have been 31.1%
   instead of 30.7%, a 0.4-point difference, which is why a calm median is not evidence of a clean file
   and why this survived the first reading. The output now carries, for every comparison, the median it
   would have had under the old conversion (`median_abs_world_gap_before_unit_fix`), so the size of the
   fault is recorded rather than remembered.
9. **2026-09-23 - the parser missed the estimate marker in two different places.** Where the
   superscript "e" is a separate span before the value, it was stored as a footnote code and
   `is_estimate` came out False. Fixed first; a second fact-check then found the other case, an "e" on
   the group-header line above the year row (29 of the 150 chapters print it there, which left those
   chapters with no estimate flag at all). Both are read now: 2,426 of 7,349 rows are marked estimates,
   against 2,039 after the first fix. No published number depended on the field.
10. **2026-09-23 - page-level corrections from the same review.** The mine-against-refinery figure
   selected its rows after sorting by refinery share, which silently dropped Peru and Zambia, two of the
   largest miners; it now takes the leaders on both measures. A dash in the printed table is shown as a
   dash rather than a computed zero. Both bands (filed and recent-decade) are shown, not only the
   recent one.
11. **2026-09-23, second council round - unchanged reprints were being counted as revisions down, and
   the downward reading was never filed.** The share revised up was reported alone, so its complement
   read as "down"; in fact graphite's mine series are 25% up, 35% down and 40% unchanged, and rare
   earths 39/29/32. The three shares are now reported separately. The filing licenses only an upward
   reading (at 60%) and leaves everything else as "no consistent direction"; the code had added a
   symmetric downward reading that the filing does not define, and the earlier result text repeated it.
   Removed: under the filed rule no commodity here has a direction.
12. **2026-09-23, second fact-check - prose numbers that were not computed.** The page carried "150
   chapters", "2,065 country series" and, for rare earths, "a USGS table of nine or ten countries". The
   first two were right but hardcoded; the third was wrong - over the compared years the USGS rare-earth
   table carries 3 to 13 countries with output, and "nine" had been carried over from the count of BGS
   reporters in 2024. All three now come from the output file, and the comparison records how many
   countries each side carries.
13. **2026-09-24 - the panel gained the 2000-2003 editions, so every median was recomputed.** Those
   editions are not linked from the commodity pages; they were cut out of the full yearly volumes
   (pipeline/fetch_usgs_mcs.py --volumes), which adds the data years 1998-2002 for five of the six
   commodities. Nothing about the measure changed. The medians move a little: copper 1.4% to 1.5%,
   antimony 11.3% to 11.6%, graphite 6.5% to 6.9%, rare earths 2.4% to 2.5%; cobalt's largest world
   revision rises from 17.4% to 29.0% and graphite's China median from 2.2% to 5.7%. The 1996-1999
   volumes are scans whose OCR breaks the columns and carries no superscript tier, so they are left out.
   The store itself now holds thirteen commodities, but this study keeps the six it filed; widening it
   is a scope change that belongs in an amendment.

