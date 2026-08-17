# silicon-chip (unpublished)

Draft work on `wip/silicon-chip-chain`. Extends Atlas silicon one hop toward chips.

- `extract_baci.py` — pull HS 280469 / 280461 / 381800 from the local BACI zip
- `record_iea_pv.py` — record IEA-PVPS solar factory production shares
- `out/silicon_stages.json` — yearly exporter / importer shares, HHI, unit values
- `out/iea_pv_production.json` — who *makes* solar poly / wafers (not chips)
- `NOTES.md` — trade reading
- `PRODUCTION.md` — factory reading, next to trade

- `silicon-chain.html` — unpublished draft page (noindex, not in site nav)

Open the draft locally (JSON fetch needs a tiny static server), e.g. from repo root:

```
python -m http.server 8765
```

then http://localhost:8765/silicon-chip/silicon-chain.html

Not wired into the live site or the 32 materials.
