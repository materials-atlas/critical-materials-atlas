# The two-machine system

Written 4 Oct 2026, to be built once Ubuntu is on the Lenovo.

The atlas outgrew one laptop on 4 October 2026, when the full-universe Comtrade crawl was measured
at **13.6 billion records**. The size on disk and the number of calls have both been revised
upwards since, measured rather than assumed (9 Oct 2026):

| | first estimate, 4 Oct | measured, 9 Oct |
|---|---|---|
| on disk | ~139 GB | **~341 GB** |
| API calls | ~203,550 | **~567,000** |
| daily running | 7-18 months | **~645 days** |

The record count did not change; what we store per record did. The first figures assumed nine
columns and a clean 70,000 records per call. The nine-column schema turned out to be dropping
`customsCode`, `motCode` and `partner2Code` - which is where transit and re-export are visible, so
the point rather than noise - and rows differing only in those were being written as identical
duplicates, up to 26x over for Germany. The full 35-column schema stores 25.1 bytes a row against
11.5, and delivers 23,914 rows a call against the assumed 70,000.

**The UN has since granted a complimentary one-year premium account with bulk file access**
(8 Oct 2026). That route is ~280 GB of compressed files over ~76,000 downloads, which at the
measured 46-54 MB/s of this connection is hours rather than months. It does not change the storage
requirement, which is why the Lenovo is still the plan. That is not work for a machine that travels in a bag and gets
closed at night. So there are two machines now, and they need to behave as one system rather than
two computers that happen to belong to the same person.

## The pieces, and why each one has the job it has

| | what it is | its job | why it suits |
|---|---|---|---|
| **Zenbook** | ASUS UX3404VC, i9-13900H, 14 cores / 20 threads, **31.6 GB RAM soldered**, 475 GB NVMe | analysis | the only machine with the memory for it. DuckDB over the corpus wants 8–16 GB of working set. It has **31 GB free**, so it cannot hold the corpus and does not need to - it reads it over the network |
| **Lenovo** | Y520-15IKBN, i5-7300HQ 4 cores, **8 GB RAM** (2 slots, takes 32), 1 TB SanDisk SSD | crawler + primary storage | it only has to be **on**. 500 API calls a day with sleeps between them is nothing. The 1 TB SSD is real - SanDisk SSD PLUS, 931.5 GB - but it is FULL, measured on the machine 13 Oct 2026: C: 500.8 GB with 13.9 free, D: 430.2 GB with 106.4 free, one physical disk in two partitions. D: holds family photographs and video. So the claim this row used to make, that it holds the corpus with room to spare, was never checked on the machine and is false as things stand |

**Space, measured rather than assumed (13 Oct 2026).** The corpus is ~232 GB unfiltered and the
Lenovo has ~120 GB free across both partitions, so it does not fit today. Emptying D:'s recycle
bin returns 23.5 GB; the rest of D: is family media and is not ours to reclaim. What DOES fit as
things stand: the full 27 years filtered to the atlas's own 54 product codes (0.4 GB), and the
recent five years unfiltered (~100 GB) - together, the whole product history plus a full-detail
recent window. The full universe needs an external disk.

The Toshiba is **out of the plan**: it failed for good on 7 Oct 2026 and was returned to its owner.
Everything below that referred to it as a third pool has been removed - there is no spare disk, so
the Lenovo's 1 TB is the whole storage budget.

The RAM asymmetry is the thing to design around: the fast machine cannot be left running for seven
months, and the machine that can be left running cannot do the analysis. Hence a network, not a
pile of USB drives.

## The four layers

### 1. Tailscale — reachability

Free for personal use. Puts both on one private network that works **anywhere**, not just on
the home LAN, so the Lenovo stays reachable when the Zenbook is out of the house. Install per
machine, sign in with the same account, done. Everything below assumes it.

### 2. SSH — control, and the end of the relay

Ubuntu runs `openssh-server`; Windows 11 ships the client. Then from the Zenbook:

```
ssh toma@lenovo
```

**The Lenovo already HAS its assistant session**, set up on 4 October and still there - so
nothing needs installing on it to drive work by hand; it is opened, not installed. Written down
because I twice gave install instructions from scratch, having read the sentence below and taken
it as history rather than as current state.

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

One copy, both machines see it. Gigabit ethernet moves ~110 MB/s, which is fine for sequential
parquet scans. Wi-Fi will be slower; for a heavy
pass, plug in.

## The shape

```
Tailscale ── both mutually reachable, anywhere
   ├── Zenbook   analysis          32 GB RAM, DuckDB, the repo
   └── Lenovo    crawler+storage   always on, SSH + Samba, 1 TB SSD (the only big disk)
```

## What this is not

**Not a cluster.** Two computers do not give twice the speed; that needs software to split
work across machines and a fast interconnect, and at 139 GB the coordination would cost more than
it saved. One decent machine with DuckDB beats a small cluster at this scale.

**Not a fix for the API limit.** The crawl's pace is set by UN Comtrade's 500 calls/day **per key**
(50 million records a day per account, which is the same ceiling stated the other way round). Ten
machines still get 500. The levers are more keys, more patience, or the granted premium bulk
access - which is a different route entirely, not a faster version of this one.

**Not a backup.** Two machines on one network, in one flat, is one fire. Anything irreplaceable
still belongs in the cloud — which is why 184 GB of photographs went to OneDrive before the Lenovo
was wiped.

## Effort

Tailscale ~10 min · SSH ~5 min · Syncthing ~15 min · Samba ~30 min. An evening, after Ubuntu.

## Order

1. Ubuntu 26.04 LTS on the Lenovo (supported to April 2031; Windows 10 support ended 14 Oct 2025)
2. Tailscale on both
3. SSH — **do this before anything else that needs typing on the Lenovo**
4. Samba for the crawl folder
5. Syncthing for the repo and notes

**That shopping list was wrong on all three counts (measured on the machine, 13 Oct 2026).**

The charger is NOT dead: the Lenovo reports PowerOnline=True, BatteryStatus=2 and a battery at
100%, so whatever is plugged in works. That sentence cost hours of planning around a machine
believed unpowerable. The USB stick is not needed either - an SD card in a USB reader boots the
same way. And the 1 TB SSD it already has is exactly what DOES need buying: it is failing, with
14 files already unreadable with CRC errors, 1,568 bad blocks and SMART attribute 187 at 6.96M.

What the machine actually takes, read from it: 2 RAM slots, one holding 8 GB DDR4-2400, the other
EMPTY, board maximum 32 GB. One physical disk, the SanDisk SSD PLUS 1 TB on SATA; the M.2 slot is
probably empty but only opening the cover confirms it. CPU i5-7300HQ, 4 cores and 4 threads, no
hyper-threading - so about 3 parallel decodes at most, and 2 while RAM is 8 GB.

The real list: a 1 TB 2.5" SATA SSD and one 8 GB DDR4-2400 SODIMM. NVMe buys little here, because
the bottleneck is CPU decode and not disk throughput.

## Bought (27 Oct 2026)

The **Crucial BX500 1 TB** (2.5", 7 mm, SATA III) was ordered on 27 Oct and arrives **28 Oct**. Same
form factor and interface as the failing SanDisk it replaces, so it drops into the same bay. The
**8 GB DDR4-2400 SODIMM** for the empty second slot is scheduled for **15 Nov 2026**.

The RAM is not a prerequisite for the corpus pull. `pull_comtrade_bulk.py` reads one reporter-month
at a time and the largest file measured (France 202506, 112.6 MB gzip, 5.08M rows) decodes inside
8 GB. So the order of work is: new SSD in, Ubuntu on it, pull running - then RAM on 15 Nov, which
buys parallel decodes (2 -> 3) and the headroom for DuckDB queries over the finished corpus.

The old SanDisk comes out rather than being wiped in place: D:'s family media is already verified
in the OneDrive backup (10,278 of 10,278 files per the rclone logs), and a disk with
1,568 bad blocks has no second job. Keep it in a drawer, do not reuse it.

## Installed (9 Nov 2026)

The BX500 is in the Lenovo's 2.5" bay and the SanDisk is out. **Not yet booted**: the new disk is
empty, so the machine does not start on its own. Ubuntu is the next step, from the installer card
written on 27 Oct.

What the swap involves on this machine, because the generic guides leave most of it out:

- The drive sits in a metal frame held to the chassis by **four** screws: two beside the SATA
  socket, two at the far end next to the I/O-board ribbon. With only the socket-end pair out it
  does not move, and it looks as though it should.
- Frame and drive come out together, sliding away from the socket. Four more screws on the two
  long sides hold the drive in the frame. The foil flap belongs to the frame and marks the
  connector end, so the new drive goes in label up with its connector under the flap.
- The green tape on the drive only holds the fan wires down. It peels off the drive and presses
  back onto the new one.
- The battery connector (printed `BATT` on the board, beside the bay) was **left plugged in**: its
  plug would not come out without force. Machine fully off and charger out instead.
- The fans and heat pipes were thick with dust when the cover came off. Worth clearing before the
  machine runs day and night.
