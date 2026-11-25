# Nuclear fuel supply study

Evidence release dated 24 November 2026. The [article](nuclear-chain.html)
contains the findings and figures in its initial HTML. Its customs table can
also explore older years when the trade data load.

## Reproduce the study

From the repository root:

```text
python nuclear-chain/record_nuclear.py
python -m http.server 8765
```

Open [the local article](http://localhost:8765/nuclear-chain/nuclear-chain.html).
The builder reads [the source and scenario inputs](evidence_inputs.json),
the [article template](article.html.in) and the checked-in
[customs data](out/nuclear_trade.json). It writes the [article](nuclear-chain.html)
and [evidence and results JSON](out/nuclear_chain.json). The main Atlas copy
can regenerate the original trade extract from BACI with
`python build_chain_trade.py`.

The [methods annex](NOTES.md) describes the calculation and its limits. The
[claim register](PRODUCTION.md) records the original narrative, source
reconciliation and publication status.

## Scenario addendum reproduction

Added 24 November 2026. The addendum records the stock draws and closing
balances for the published cases. Its capacity screen compares the immediate
joint replacement requirement with two operators' reported annual capacity.
Use these commands from the repository root.

```text
python nuclear-chain/test_record_nuclear.py
python nuclear-chain/record_nuclear.py
```

The first command verifies the inventory balance, the early-gap decision
rule and the arithmetic of the 2025 capacity screen. The second generates
the article and the `scenario_addendum` section of the evidence JSON.

## Review of the follow-up, 25 November 2026

Scenario arithmetic re-done (stock draws, replacement rates; 6.019 million SWU = 24.4% of the 24.7 million SWU that ESA
Table 8 lists for Urenco 17,200 and Orano 7,500 tSW - the sum is ours). Sources checked: ESA 2025 Table 4 (ConverDyn
2,825 / 2,898 tU), section 1.5; Orano Annual Activity Report 2025 p.39 (first production 2028, full commissioning 2030).
Fix: the NEA Figures 5.2-5.3 link pointed to PDF page 45 (Figure 5.1); now #page=46. Model tests pass (5).
