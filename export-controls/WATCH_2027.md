# Watch: did China's suspended export controls come back? — due February 2027

Written 2026-09-24, when the export-controls study was published. This is the follow-up it promises.

## What is suspended, and until when

| Suspended | Covers | Until |
|---|---|---|
| MOFCOM/GAC 2025 Nos. 55-58, 61, 62 (suspended by No. 70, 7 Nov 2025) | superhard materials; rare-earth equipment and inputs; five further medium and heavy rare earths (holmium, erbium, thulium, europium, ytterbium); lithium batteries and artificial-graphite anode material; the extraterritorial 0.1% rule; rare-earth technologies | **10 November 2026** |
| MOFCOM 2024 No. 46, clause 2 (suspended by No. 72, 9 Nov 2025) | the ban in principle on gallium, germanium and antimony **to the United States** | **27 November 2026** |

## Why February 2027

Eurostat Comext publishes a month about two months after it ends, so November and December 2026 land
in January and February 2027. Until then there is nothing to read.

## What to run

    python export-controls/fetch_comext_ec.py --start 202608 --end 202702   # new months only
    python export-controls/analysis.py                                      # re-reads every control
    python check.py

Then compare the new months with the pre-suspension pattern the study found: tonnes from China, the
unit value of all imports, and which origins gained (`export-controls/origins.py`).

## What the page says will show it

The published page (`/export-controls`) states that a return would show first as a fall in tonnes from
China, a rise in the unit value of all imports, and new origins whose own imports from China should
then be checked. **These EU lines do not cover the suspended goods**: No. 57 is other rare earths, No.
58 is battery and anode material, and No. 46 is a ban on shipments to the United States, which EU
records do not see. Following those needs their own customs lines - the method carries over, the codes
do not.

## Honest limits, from the study

- The filed test could not certify a bite even where the raw series moved; a new episode will have the
  same problem unless the monthly series are thicker.
- Antimony's fall began before its control was announced, so a change after November 2026 is not
  evidence on its own that the control caused it.
- The comparison goods (magnesium, talc and baryte, ferrite magnets, light rare earths) were coarse and
  two of them broke on the data; they would need rechecking before any new reading.
