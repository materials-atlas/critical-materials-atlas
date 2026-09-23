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

## Deviations log

Every change made after this filing goes here, dated, with its reason.
