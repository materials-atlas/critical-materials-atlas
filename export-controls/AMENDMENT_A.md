# Amendment A — who replaced China, and why these two? — filed 2026-09-21

Filed before any origin-level EU figure, any production figure, or any Comtrade figure for these goods
was read. **What was already known when this was written:** the study's results (`PREREGISTRATION.md`,
deviations 1-11), which include, for each EU control, tonnes from China and from all origins before and
after. The motivation is therefore post-hoc: the study found that EU imports of antimony from China all
but stopped while total imports held, and that bismuth from other origins rose. This amendment asks
where that material came from, and why these two controls moved while the others did not. Its readings
are decided here, before the figures that answer them are looked at.

Same windows as the study: the pre-period is the 24 months before announcement, the post-period months
7-12 after entry into force. Same EU data and filters (Comext, extra-EU imports, the United Kingdom
excluded). Same codes.

## A. Where the replacement came from (EU, all six controls; antimony and bismuth are the headline)

For each origin other than China: mean tonnes a month in the pre-period and in the post-period, and the
change. The **replacement** is the sum of the positive changes. The origins that together account for
at least 80% of it, largest first, are reported by name.

Each of those origins is classed by its own output of the material, from BGS World Mineral Statistics
as held in the atlas (mine production for antimony, bismuth and graphite; processed production for
gallium, germanium and rare earths), mean 2021-2023:
- **producer:** its production is at least twelve times its post-period monthly exports to the EU,
  i.e. it produces at least what it ships the EU in a year;
- **non-producer:** no production recorded in 2021-2024, or less than that.

A refiner of ore mined elsewhere reads "non-producer" on this screen; the class is a screen, not a
verdict, and says nothing about the refiner's inputs.

A **transit candidate** is a non-producer whose EU exports rose by at least 10 tonnes a month and at
least tripled (or rose by at least 10 tonnes a month from nothing).

**Reading:** the share of the replacement that came from producers, and the list of transit candidates.
No origin is called a route for Chinese material on this screen alone, and the filing's "diverted"
reading is not claimed from it.

## B. Did the transit candidates' own imports from China rise?

For each transit candidate, its monthly imports from China as it reports them to UN Comtrade (HS 811010
for antimony; the HS 8106 lines for bismuth; the matching lines for any other control that yields a
candidate), January 2022 to the latest month available. Compared: the mean over months 0-12 after
entry into force against the pre-period mean.
- **Consistent with rerouting:** the candidate's imports from China rose by at least 50% and by at least
  10 tonnes a month.
- **Not consistent:** they fell, or rose by less.
- **No answer:** the candidate does not report the months needed.

Consistent is not proof. Material can be processed in the transit country, declared under another
line, or come from stocks. Comtrade records are used for derived figures only and not redistributed.

## C. Why these two? A comparison across the six (descriptive)

For each of the six EU series: China's share of world production (BGS, mean 2021-2023, the same stage
as in part A; rare earths processed for both the magnet and the heavy rare-earth series); the number of
other countries with at least 5% of world production; China's share of EU import tonnes in the
pre-period; and the observed raw movements (tonnes from China after over before, unit-value multiple).

**This part is descriptive and cannot confirm anything.** The outcomes are known, there are six rows,
and world production shares are only a proxy for how easily buyers can switch. The question it asks,
stated now: *do antimony and bismuth, the two series that moved, stand out from the other four on
China's share of world production, on the number of alternative producers, or on the EU's own
dependence on China before the control?* The answer is read off the ranks and reported whichever way it
falls, including "on none of them".

## D. Not tests

The study already estimated the effect over months 0-3, 4-6 and 7-12; the page will chart that path.
The page will also list the controls suspended in November 2025 and the dates the suspensions end, as
context. Neither is a test and neither changes a reading.

## Result - run 2026-09-21

Run by `origins.py` (parts A and C) and `partb.py` (part B, on records fetched by `fetch_comtrade_ec.py`);
every number is in `out/export_controls_origins.json`.

### A. Who replaced China (tonnes a month, pre-period against months 7-12)

| Series | origin | before | after | change | class | transit candidate |
|---|---|---|---|---|---|---|
| gallium and germanium | Canada | 0.2 | 0.4 | +0.2 | non-producer |  |
| gallium and germanium | Rep. of Korea | 0.0 | 0.1 | +0.1 | producer |  |
| graphite | Canada | 62.0 | 212.7 | +150.8 | producer |  |
| graphite | Türkiye | 95.9 | 185.0 | +89.1 | producer |  |
| graphite | USA | 121.3 | 202.1 | +80.8 | non-producer |  |
| rare-earth magnets | Viet Nam | 16.9 | 34.1 | +17.2 | producer |  |
| rare-earth magnets | Switzerland | 7.4 | 14.0 | +6.6 | non-producer |  |
| Gd, Tb, Dy metals and compounds | India | 0.3 | 2.6 | +2.4 | producer |  |
| antimony | Myanmar | 47.6 | 183.0 | +135.4 | producer |  |
| antimony | Viet Nam | 177.9 | 264.2 | +86.2 | non-producer |  |
| antimony | Malaysia | 0.0 | 67.4 | +67.4 | non-producer | yes |
| antimony | Thailand | 80.6 | 145.9 | +65.3 | non-producer |  |
| bismuth | Rep. of Korea | 1.5 | 25.9 | +24.5 | non-producer | yes |
| bismuth | Kazakhstan | 0.0 | 8.5 | +8.5 | producer |  |

**Antimony.** Other origins added 392 tonnes a month, more than the 182 China lost. Myanmar, a producer,
supplied the largest part; 35% of the replacement came from producers. Viet Nam and Thailand read as
non-producers on this screen, which counts only their own mine output; a refiner of ore mined elsewhere
reads the same way. **Malaysia** is the one transit candidate: nothing before, 67 tonnes a month after.
**Bismuth.** Other origins added 34 tonnes a month against the 75 China lost. The **Republic of
Korea** is the transit candidate on this screen (1.5 to 25.9 tonnes a month), and Kazakhstan, a producer,
the rest.

### B. The candidates' own imports from China (as they report them to UN Comtrade)

| Material | candidate | from China before, t a month | months 0-12 after | months available | reading |
|---|---|---|---|---|---|
| antimony | Malaysia | 0.14 | 0.03 | 13 of 13 | not consistent |
| bismuth | Republic of Korea | 7.83 | 2.60 | 11 of 13 | not consistent |

**Neither candidate is consistent with rerouting.** Malaysia reports almost no unwrought antimony from
China in any month, before or after; in the three months checked, its antimony imports were ores and concentrates
from elsewhere (deviation 2). Korea's imports of bismuth from China fell after the control, and were in any case a
fraction of what it added to its exports to the EU. Korea Zinc recovers bismuth as a
by-product of zinc, lead and copper smelting (deviation 3), so the Korean rise is most plausibly its
own refined output, which the part A screen cannot see.

### C. Why these two? (descriptive)

| Series | China's share of world production (BGS, 2021-23) | other countries with 5%+ | China's share of EU imports before | tonnes from China, after / before | unit-value multiple |
|---|---|---|---|---|---|
| gallium and germanium | gallium 96%, germanium 94% | 0, 0 | 91% | 0.73 | 1.4 |
| graphite | graphite 70% | 3 | 30% | 1.15 | 0.9 |
| rare-earth magnets | rare earths 70% | 3 | 93% | 1.31 | 0.9 |
| Gd, Tb, Dy metals and compounds | rare earths 70% | 3 | 25% | 0.42 | 3.2 |
| antimony | antimony 38% | 3 | 11% | 0.04 | 4.1 |
| bismuth | bismuth 40% | 3 | 91% | 0.43 | 2.6 |

**On none of the three.** Antimony and bismuth, the two that moved, have the *lowest* China share of
world mine production of the six (38% and 40%), not the highest; every series but gallium and germanium
has three other producers above 5%; and the EU's dependence on China before the control was the lowest
of the six for antimony (11%) and among the highest for bismuth (91%). Nothing in this table explains
why these two moved. One reason the table may miss it: BGS records mine production for antimony and
bismuth, while the controls cover refined metal, where China's share may be larger (deviation 4).

## Deviations log

Every change made after this filing goes here, dated, with its reason.
1. **2026-09-21, part B - Korea's months.** Korea's Comtrade records end in December 2025, so 11 of the
   13 months 0-12 after the bismuth control are available; the reading uses those. Within a reporter's
   reported span, a month with no record for the line is read as no trade.
2. **2026-09-21, part B - a check that Malaysia reports.** Malaysia's records for unwrought antimony from
   China were almost empty, which could mean no trade or no reporting. One added query of Malaysia's total
   monthly imports from China (September 2024, March and June 2025: USD 5.0-6.6bn a month) confirms it
   reports. The same query showed its antimony imports in those months were ores and concentrates from
   Myanmar, Turkiye, Thailand and a partner recorded as the United Kingdom; that is context from three
   months, not a test.
3. **2026-09-21, part B - the Korean refiner.** Korea's classification as a non-producer comes from BGS
   mine production, which it has none of. Korea Zinc recovers bismuth, antimony and indium from the
   by-products of its zinc, lead and copper smelting at Onsan (Seoul Economic Daily, 8 March 2026,
   https://en.sedaily.com/finance/2026/03/08/korea-zincs-onsan-smelter-produces-10-tons-daily-of-defense).
   Stated beside the result; the filed class is unchanged.
4. **2026-09-21, part C - stage.** The atlas holds BGS mine production for antimony and bismuth and no
   refined series; the controls cover refined metal. The comparison is reported at the stage filed.
5. **2026-09-21, part A - falls reported too.** The filing names only the origins that added to EU
   imports. For antimony, other origins also fell (net 117 tonnes a month once the named gainers are
   counted), so the three largest falls among other origins are now written to the output and shown,
   descriptively. No class or reading depends on them.
