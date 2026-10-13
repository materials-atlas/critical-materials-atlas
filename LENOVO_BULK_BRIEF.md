# Brief for the session on the Lenovo: pull the whole Comtrade monthly series

Written 13 Oct 2026 by the session on the Zenbook, which made every measurement below. If you are
the assistant on the Lenovo, this is your work order. Toma should not have to do anything after
handing you the API key.

## The job

Pull the **whole** UN Comtrade monthly HS6 series: 2000-2026, every reporter, **every product**,
all 34 columns. No product filter. Toma has asked for this twice, explicitly.

```
python reconcile/pull_comtrade_bulk.py --all-codes
```

`--all-codes` needs nothing else from this repository: no `baci`, no cube. Verified by running it
from an otherwise empty folder.

## Setup, in order

1. `pip install requests pyarrow`
2. The API key is NOT in this repository and never will be. Ask Toma for it and write it as the
   only line of `pipeline/.comtrade_key`. Do not print it back, do not put it in a commit, do not
   paste it into any message.
3. `python reconcile/pull_comtrade_bulk.py --all-codes --plan` first. It must say
   **322 periods** and **filter ALL products**. If it says `54 codes`, the flag was lost.
4. Then run it for real. It takes days on this machine; that is expected.

## Why this route, and not the other one

The premium access the UN granted on 8 Oct 2026 is **live on the bulk endpoint** with the key you
will be given. No new key ever arrived and the portal still shows the subscription as "free" - the
data API still refuses more than 12 periods. Do not go looking for a new key and do not try to
"activate" anything. It already works.

| | |
|---|---|
| per-call crawl, whole corpus | **783 days** (17.3M rows/day, measured over 3 full days) |
| bulk transfer, whole corpus | **263 GB** (summed from real listings, 7 periods 2000-2026) |
| kept on disk, unfiltered | **232 GB** parquet+zstd |
| one file (France 202506) | 112.6 MB gzip, 5,083,358 rows, 99.3 MB parquet |

The old per-call crawl is stopped and its scheduled task disabled on the Zenbook. Do not restart it.

## Six things that will waste your time if you do not know them

1. **`fileSize` is a STRING** - `"107.41 MB"`. `int()` on it raises. The script already parses it.
2. **`cmdCode` must be read as text.** Inferred as an integer it loses its leading zero and
   `010121` silently matches nothing.
3. **Decoding is the bottleneck, not downloading.** France arrives in 10.5 s and takes 38.8 s to
   read with the `csv` module, 13.1 s with pyarrow. The script uses pyarrow. Do not change it back.
4. **Archives are never kept.** Each `.gz` is deleted as soon as it is read - 263 GB of transfer
   must not land. Check at the end that no `.gz` or `.part` survives.
5. **Recent periods are empty.** 202609 and 202610 list 0 reporters; the data lags. Not an error.
6. It **resumes** per reporter-month and **stops itself** below 5 GB free, checked on every file.

## What to report back to Toma

- the Lenovo's free disk before starting (the job needs about 250 GB)
- that `--plan` said 322 periods and ALL products
- while running: periods done, rows kept, GB transferred
- at the end: that no archive survived, and the total

He has asked to be kept informed without having to ask. Push the status to him; do not wait to be
questioned.
