# Germanium in optical fibre and the suppliers of submarine cables

The [research note](fibre-optics-chain.html) sets out how much germanium optical fibre uses, what is
known about germanium supply, which fibre is made without germanium in the core, and who supplies
submarine cable systems. The [claim register](PRODUCTION.md) records the audit of the previous page.

Run `python fibre-optics-chain/record_fibre.py` from the repository root. The builder needs no network
access. It reads:

- `evidence_inputs.json`: the USGS, IEA and European Commission expert-group figures as transcribed and checked on 25 November 2026, with source links;
- `article.html.in`: the page text;
- `out/fibre_trade.json`: the frozen BACI extract written by `extract_baci.py`.

It writes the page and `out/fibre_chain.json` (inputs, results and the chokepoint-map entry).

## Calculations

- Germanium per kilometre, by fibre type, is taken from USGS Open-File Report 2024-1057, table 1.24.
- Average germanium per kilometre at a given multimode share = share × 0.19 g + (1 − share) × 0.0039 g.
- Germanium in world fibre = that average × an assumed 500 million kilometres. Primary germanium = × 2.68.
- The multimode share that matches the comparison figure solves the same equation for 30% of the USGS estimate of 210 tonnes of primary germanium (2022).
- Supplier shares = each supplier's cable length divided by the total of the listed lengths (389.7 thousand km).
- The concentration index (HHI) is a lower bound: the group of smaller suppliers is left out because its members are not listed.

The builder stops if contained germanium times 2.68 does not give the USGS primary figure, if a
supplier's length does not reproduce its printed share, if the vessel rows do not add to the printed
totals, or if any sentence that states a number in words no longer matches the data.
