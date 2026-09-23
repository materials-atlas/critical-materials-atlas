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

Run by `analysis.py`; every number is in `out/usgs_revisions.json`. 1596 series (commodity, country or
world total, measure, year) have at least two editions and a usable first value; 692 were dropped
because the first edition to report them printed a dash, a W or nothing. The newest data year in each
chapter has been published once and cannot be measured yet.

### How far the first published figure moves

| Commodity | world, median abs revision | same, last 10 years | largest | China, median | revised up | direction | band (last 10) |
|---|---|---|---|---|---|---|---|
| antimony | 11.3% | 11.3% | 42.5% | 11.0% | 41% | no consistent direction | **weak** |
| graphite | 6.5% | 8.3% | 29.9% | 2.2% | 25% | revised down more often than up | **weak** |
| cobalt | 5.7% | 3.6% | 17.4% | 4.7% | 49% | no consistent direction | **soft** |
| tungsten | 5.3% | 2.4% | 55.0% | 5.6% | 42% | no consistent direction | **soft** |
| rare earths | 2.4% | 3.1% | 17.1% | 0.0% | 39% | revised down more often than up | **soft** |
| copper | 1.4% | 2.1% | 3.6% | 5.0% | 52% | no consistent direction | **soft** |

**A current-year figure is worth about what its commodity's band says.** Copper's world total is the firmest: it
moves 1.4% between its first and its latest printing over the whole period, 2.1% over the last ten
years, which is the difference between the filed "firm" and "soft" bands.
Antimony's moves 11.3%, and has moved 42.5%. Graphite's 6.5% gets worse in the recent decade, not
better (8.3%). The direction is not systematic: only graphite and rare earths are revised down more
often than up, and no commodity is revised up more often than down at the 60% bar set in the filing. China's rare-earth
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
| Japan | 0 | 0% | 1,400 | 5% |
| Russia | 1,300 | 6% | 950 | 3% |
| United States | 1,000 | 4% | 850 | 3% |
| India | 23 | 0% | 620 | 2% |
| Germany | 0 | 0% | 610 | 2% |

**China mines 8% of the world's copper and refines 48% of it.** The atlas's argument in one line, from
a single table: mine shares and refinery shares are different maps, and a dependence read off mining
alone misses where the leverage sits.

### Where USGS and BGS disagree

Both count the same thing; neither is a correction of the other. The gap is the median absolute
difference in the world total (and China), USGS over BGS, on the years both cover.

| Commodity | measure | years | world gap | China gap |
|---|---|---|---|---|

| graphite | mine | 2002-2024 | 31.6% | 31.0% |
| antimony | mine | 2002-2024 | 13.1% | 15.5% |
| cobalt | mine | 2002-2024 | 12.7% | 25.0% |
| tungsten | mine | 2002-2024 | 6.9% | 8.6% |
| copper | refinery | 2019-2024 | 1.2% | 0.2% |
| copper | mine | 2002-2024 | 0.6% | 1.2% |

Copper is the close case (0.6% on mine, 1.2% on refined). Graphite is the far one (31.6%), and the
two are not measuring the same basket there: the BGS series carries the forms it collects, the USGS
chapter is natural graphite. A page that quotes a graphite share should say which source it used.

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
   year before it revised, so **every data year appears in exactly two editions** (139 of the measurable
   world-total years have two, none has three). "First against latest" is therefore "the estimate
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

