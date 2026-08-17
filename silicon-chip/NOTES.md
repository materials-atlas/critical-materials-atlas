# Silicon → chips: first data pull

Unpublished draft on `wip/silicon-chip-chain`. Not added to the 32. Not on the live site.

Source: the same CEPII BACI HS17 V202601 files the Atlas already uses (2018–2024).
Reproduce: `python silicon-chip/extract_baci.py`

## What we pulled

| Code | What the customs line says | Role here |
|---|---|---|
| **280469** | Silicon **under** 99.99% | Control. This *is* current Atlas silicon. |
| **280461** | Silicon **at least** 99.99% | Next hop after the metal. |
| **381800** | Doped discs / wafers for electronics | Hop after that. |

## Sanity check

2024 industrial silicon (280469) from this pull vs the live profile:

| | This pull | Live profile (`profile-silicon.html`) |
|---|---|---|
| World | $3.89B | — |
| China export share | 40.0% | 40% |
| China value | $1.555B | $1.5B |
| China tonnes | 724 kt | 721.6 kt |
| China $/t | $2,148 | $2,146 |
| Next: Norway / Brazil / France | 13% / 12% / 6% | 13% / 12% / 6% |

Close enough. The extractor is reading the same trade the Atlas already trusts.

## 2024 headline

**Industrial silicon (280469)** — $3.9B, 1,557 kt, about **$2,500/t**.
China 40% of exports. Same story you already publish.

**High-purity silicon (280461)** — $3.6B, only **164 kt**, about **$22,000/t**.
Same dollars as the cheap metal, one-tenth the tonnes, nine times the price.

Top exporters by *value*: Germany 32%, United States 30%, China 13%.
Top exporters by *tonnes*: Germany 31%, China 26%, United States 21%.
China’s cargo is cheap ($10,600/t). Japan’s is $57,000/t, Taiwan’s $40,000/t, the US $31,000/t.

Top importers: Vietnam 24%, China 24%, Japan 17%.

**Wafers (381800)** — $17.8B, 114 kt, about **$156,000/t**.

Top exporters by *value*: Japan 28%, China 22%, United States 10%.
Top exporters by *tonnes*: China **58%**, Singapore 10%, Japan 8%.
China’s wafers are $59,000/t. Japan $533,000/t, US $764,000/t, Germany $753,000/t.

Top importers: Taiwan 17%, Korea 14%, China 14% — the places that actually run fabs.

## What this means (plainly)

1. **Both new codes are measurable.** They are real, thick trade lines in the files you already have. We do not need a new vendor for this first hop.

2. **Both codes are mixed. Say so on any future page.**
   - 280461 is *not* “chip-grade silicon”. It is “silicon pure enough for solar *or* chips”. Vietnam as the top importer is the solar-cell industry, not TSMC.
   - 381800 is *not* “Shin-Etsu 300 mm wafers”. It is “any doped disc”, including cheap solar wafers. That is why China can lead tonnes and Japan can lead dollars.

3. **Unit price splits the mix.** Cheap Chinese tonnes vs expensive Japanese / US / German / Taiwanese kilos is the same move the Atlas already uses (value next to tonnes). Do not pick one number and call it “the” market.

4. **Trade is not production.** IEA is right that China dominates *making* solar polysilicon. That barely shows up as Chinese *exports* of 280461, because most of it is used at home. China is a top *importer* of the high-purity code. Same Atlas thesis: the customs ledger is not the factory.

5. **Wafers are already a bigger traded market than either silicon code** ($18B vs $4B). The money in this chain jumps at the wafer, not at the metal.

## What we will not claim

- That 280461 is electronic-grade polysilicon (9N–12N). The legal cut is 99.99% (4N). Solar lives in this code.
- That 381800 is semiconductor wafers only.
- That Germany “owns” high-purity silicon. Wacker is real; the code still mixes solar and electronic, and Denmark’s tiny high-price slice looks like a trading hub.
- Any company share (Shin-Etsu, SUMCO, Wacker, Hemlock). BACI cannot see firms.

## Next data (not a page)

**Done for solar.** See `PRODUCTION.md`: IEA-PVPS 2023 production shares (China 92% poly, 98% solar wafers) sit next to the BACI export shares (China 13% / 22%). Factory ≠ customs ledger.

**Still missing for chips.** No public IEA/USGS country table for electronic-grade poly or semiconductor wafers.

Do not add these codes to the 32. Do not publish a page until the mixed-code flags are in the same file as the numbers (they are, here).
