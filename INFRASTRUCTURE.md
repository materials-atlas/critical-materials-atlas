# The three-machine system

Written 4 Oct 2026, to be built once Ubuntu is on the Lenovo.

The atlas outgrew one laptop on 4 October 2026, when the full-universe Comtrade crawl was measured
at **13.6 billion records, ~139 GB, ~203,550 API calls, seven to eighteen months of daily running**
depending on how many keys we hold. That is not work for a machine that travels in a bag and gets
closed at night. So there are three pieces now, and they need to behave as one system rather than
three computers that happen to belong to the same person.

## The pieces, and why each one has the job it has

| | what it is | its job | why it suits |
|---|---|---|---|
| **Zenbook** | ASUS UX3404VC, i9-13900H, 14 cores / 20 threads, **31.6 GB RAM soldered**, 475 GB NVMe | analysis | the only machine with the memory for it. DuckDB over 139 GB wants 8–16 GB of working set |
| **Lenovo** | Y520-15IKBN, i5-7300HQ 4 cores, **8 GB RAM** (2 slots, takes 32), 1 TB SanDisk SSD | crawler + primary storage | it only has to be **on**. 500 API calls a day with sleeps between them is nothing. The SSD holds the whole corpus |
| **Toshiba** | Seagate ST1000LM035 1 TB, 2.5" SMR, made Nov 2017 | third storage pool | SMR, nine years old, already failed once through a bad USB bridge. Fine for things that can be re-created, not for anything that cannot |

The RAM asymmetry is the thing to design around: the fast machine cannot be left running for seven
months, and the machine that can be left running cannot do the analysis. Hence a network, not a
pile of USB drives.

## The four layers

### 1. Tailscale — reachability

Free for personal use. Puts all three on one private network that works **anywhere**, not just on
the home LAN, so the Lenovo stays reachable when the Zenbook is out of the house. Install per
machine, sign in with the same account, done. Everything below assumes it.

### 2. SSH — control, and the end of the relay

Ubuntu runs `openssh-server`; Windows 11 ships the client. Then from the Zenbook:

```
ssh toma@lenovo
```

**This is the layer that matters most, and the reason this document exists.** On 4 October the
Lenovo had to be set up by relaying every instruction between two separate assistant sessions, one
per machine — each step typed by hand, screenshots carried back, decisions re-confirmed twice
because a message from one session is not the operator's instruction in another. That boundary was
correct and it held. But it is a boundary between *sessions*, not between machines: with `sshd` on
the Lenovo, the session on the Zenbook runs commands there directly and the relay disappears.

Key-based auth, not passwords. `ssh-keygen` on the Zenbook, public key into
`~/.ssh/authorized_keys` on the Lenovo.

### 3. Syncthing — small files that should exist in both places

Peer-to-peer, no cloud, no subscription. Nominate folders and they stay identical. Right for the
repo, notes, anything edited on either machine. **Wrong for the crawl output** — 139 GB does not
want duplicating, and Syncthing's conflict handling is not what you want for a dataset that is
written once and read many times.

### 4. Samba — the big data, in one place only

The crawl output lives on the Lenovo and is **not** copied. Samba shares the folder, the Zenbook
mounts it as a drive letter, and DuckDB reads it over the network:

```sql
SELECT ... FROM parquet_scan('Z:/comtrade_full/*/*.parquet')
```

One copy, both machines see it. Gigabit ethernet moves ~110 MB/s, which is faster than the SMR
Toshiba manages locally and fine for sequential parquet scans. Wi-Fi will be slower; for a heavy
pass, plug in.

The Toshiba hangs off the Lenovo and is shared the same way, so it becomes a third pool on the
network rather than a disk anybody carries between machines.

## The shape

```
Tailscale ── all three mutually reachable, anywhere
   ├── Zenbook   analysis          32 GB RAM, DuckDB, the repo
   ├── Lenovo    crawler+storage   always on, SSH + Samba, 1 TB SSD
   └── Toshiba   third pool        attached to the Lenovo, shared over the net
```

## What this is not

**Not a cluster.** Three computers do not give three times the speed; that needs software to split
work across machines and a fast interconnect, and at 139 GB the coordination would cost more than
it saved. One decent machine with DuckDB beats a small cluster at this scale.

**Not a fix for the API limit.** The crawl's pace is set by UN Comtrade's 500 calls/day **per key**.
Ten machines still get 500. The only levers are more keys or more patience.

**Not a backup.** Three machines on one network, in one flat, is one fire. Anything irreplaceable
still belongs in the cloud — which is why 184 GB of photographs went to OneDrive before the Lenovo
was wiped.

## Effort

Tailscale ~10 min · SSH ~5 min · Syncthing ~15 min · Samba ~30 min. An evening, after Ubuntu.

## Order

1. Ubuntu 26.04 LTS on the Lenovo (supported to April 2031; Windows 10 support ended 14 Oct 2025)
2. Tailscale on all three
3. SSH — **do this before anything else that needs typing on the Lenovo**
4. Samba for the crawl folder
5. Syncthing for the repo and notes
6. Toshiba, once it is proven healthy in a working enclosure
