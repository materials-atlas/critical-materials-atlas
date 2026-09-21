# Did China's export controls bite? — design draft (not yet filed)

Draft, 2026-09-21. Not a filing: dates, legal scope and customs codes marked [VERIFY] are being
confirmed from primary sources, and the design goes to two independent referees before it is filed.
No value from the data below has been pulled.

## The question

Between 2023 and 2025 China placed export controls on gallium and germanium, on graphite, and on seven
medium and heavy rare earths including magnets that contain them, and in December 2024 banned several of
these outright to the United States. A control can bite in three ways that customs records can see:
**buyers get less from China, they pay more, or they get less in total.** It can also fail to bite —
licences are granted, material is re-routed, stocks cover the gap. The question is which happened, for
each control, in the EU's and the United States' own import records, and how fast.

## The decision this serves

A government or a buyer deciding how much to spend on stockpiles or alternative supply needs to know
whether past controls cut supply or only raised its price, and whether anyone else filled the gap. An
answer across four controls, on one design, is more useful than four anecdotes.

## Data

- **EU:** Eurostat Comext monthly, CN8, imports of the EU27 from outside the EU, value (EUR) and
  quantity (kg), January 2012 to the latest month, the United Kingdom excluded in every year.
- **US:** Census international trade API, general imports, HS10, value (USD) and quantity, same span.
- **Goods and events** [VERIFY dates and codes]:

| Control | Announced | Effective | Treated codes | Comparison codes (same heading, not controlled) |
|---|---|---|---|---|
| Gallium, germanium | Jul 2023 | 1 Aug 2023 | US 8112.92.10 (Ga), 8112.92.60/65 (Ge); EU [VERIFY] | indium, niobium (same heading) |
| Graphite | Oct 2023 | 1 Dec 2023 | 2504 natural, 3801 artificial [VERIFY scope] | [VERIFY] |
| Ga, Ge (and Sb) to the US | Dec 2024 | Dec 2024 | the US codes above | EU imports of the same codes |
| Rare earths incl. magnets | Apr 2025 | Apr 2025 | 2805.30, 2846 [VERIFY], 8505.11 magnets of metal | 8505.19 other magnets (ferrite) |

## Outcomes, per control and per importer

1. **China's share** of the value of imports of the treated goods.
2. **Price:** import unit value of the treated goods, all origins, and from China separately.
3. **Quantity:** total imports of the treated goods, in kilograms.

## Design

For each control, a difference-in-differences on monthly data: treated against comparison codes, in
the same importer, relative to the 24 months before the announcement. Months between announcement and
effective date are a separate anticipation window. Post-period: from the effective date to twelve
months after, or to the latest month. Seasonality by calendar-month effects. Inference: Newey-West
errors, and every estimate reported with the smallest effect it could detect at 80% power.

**Readings, decided now.** A control *bit* in an importer if, within twelve months of taking effect,
China's share of the treated goods fell by at least 10 percentage points relative to the comparison,
or the treated unit value rose by at least 20% relative to it, with the interval excluding zero. It
*did not visibly bite* if the intervals exclude those sizes. Otherwise it is *untestable at this
size*, and the page says so rather than reporting a null.

## What this cannot say

Customs value is not a contract price; small volumes make monthly unit values noisy; material can be
re-routed through third countries, which shows as China's share falling without supply falling; stocks
bought ahead of a control show as anticipation, not as the effect; and none of this measures licences
granted. Not causal beyond the comparison it states.
