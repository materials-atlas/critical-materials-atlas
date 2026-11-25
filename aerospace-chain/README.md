# Civil aero-engine supply research note

The [study](aerospace-chain.html) examines where material and component supply is
concentrated, which sources a civil engine programme can use, and when inventory
and alternative supply might bridge a disruption. The [claim register](PRODUCTION.md)
links to the reviewed pilot and explains the changes and remaining evidence gaps.

Run `python aerospace-chain/record_aerospace.py` from the repository root to
rebuild the article, [evidence JSON](out/aerospace_chain.json) and
[monthly scenario paths](out/aerospace_supply_scenarios.csv). The script uses
the checked-in [BACI trade extract](out/aerospace_trade.json), the inputs
transcribed from public sources in the script, and the local article template.
It needs no network access. The extract covers HS 810820, 750210, 841112, 841122
and 841191. Regenerating it with `extract_baci.py` requires the separate
BACI archives.

The [August 2026 reference library](library.md) retains its original entries
with a dated note linking readers to the revised findings.
