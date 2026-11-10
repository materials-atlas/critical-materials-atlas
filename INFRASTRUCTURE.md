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

**Superseded 9 Nov 2026.** That session lived on the old disk, under Windows, and went out with
it. The Ubuntu install starts with none, so until SSH is up every command on the Lenovo is typed
by hand there.

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
   - **done 9 Nov 2026**, see "Ubuntu installed" at the end
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

The BX500 is in the Lenovo's 2.5" bay and the SanDisk is out. Ubuntu went onto it the same evening
(next section).

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

## Ubuntu installed (9 Nov 2026)

Ubuntu 26.04.1 LTS desktop is on the BX500 and the Lenovo boots from it, the same evening as the
swap. The installer card written on 27 Oct worked at the first attempt.

- **Booting the card.** In the Novo Button Menu, Boot Menu lists the card as **"Linpus lite
  (Flash)"**. Nothing in that list says Ubuntu, USB or SD.
- **Choices made in the installer:** English, French keyboard, interactive installation, default
  selection, neither of the two proprietary-software boxes, erase disk and install, **no
  encryption**. An encrypted disk asks for a passphrase at every start, and this machine has to
  come back on its own after a power cut.
- **Result:** `CT1000BX500SSD1` as `sda`, with `sda1` FAT32 on `/boot/efi` and `sda2` ext4 on `/`.
  User `toma`, host `lenovo`, which is what the `ssh toma@lenovo` line above expects.

## Server setup (9 Nov 2026)

Done the same evening, in this order, because step 3 of the Order section removes the typing:

- **SSH first.** `openssh-server` installed by hand on the Lenovo (the only two commands typed
  there). A key made on the Zenbook (`~/.ssh/id_ed25519`, no passphrase) went into
  `~/.ssh/authorized_keys`, and key login works. Until Tailscale gives the machine a name it is
  reached at its DHCP address on the home network, which can change.
- **One root script,** `server_setup.sh`, kept in the kit folder outside this repo: the 105 waiting
  updates; `python3-venv`, `pip`, `git`, `curl`, `tmux`, `htop`, `smartmontools`; a logind drop-in
  (`/etc/systemd/logind.conf.d/50-server.conf`) so that **closing the lid no longer suspends**;
  linger for the user, so its background services run with nobody logged in; Tailscale 1.104.5
  installed. Checked after the restart: no updates pending, lid switch reads `ignore`, linger on.
- **It cannot sleep.** `sleep.target`, `suspend.target`, `hibernate.target` and
  `hybrid-sleep.target` are masked, and the desktop session is set never to blank, dim or lock
  the screen, so the machine can be looked at without typing the password. The one report of
  "it switches off by itself" was the screen blanking after five minutes: the journal showed no
  suspend and the pull never paused. Check the journal before believing in a sleep.
- **Measured on the machine:** 857 GB free of 915 GB; 7.1 GiB of RAM visible; no NVMe device, so
  the M.2 slot is empty as far as the system can see. Idle suspend on mains is already off by
  default. The Wi-Fi profile is system-wide with its key stored, so it reconnects at start.

Traps met:

- **Root still needs the password.** There is no passwordless `sudo`. Anything needing root is
  put in a script and started from the Zenbook with `ssh -t`, so the password is typed once, by
  hand, in that window.
- `tailscale set --operator` inside the script did not take, so `tailscale up` still asked for
  root. Pass `--operator` to `tailscale up` itself.
- The Windows `ssh-keyscan` (OpenSSH 9.5) fails against this server (OpenSSH 10.2) with an
  unsupported key-exchange error. `ssh` itself connects fine; the error is not a network fault.

**Tailscale is up on both machines (9 Nov 2026, late evening).** `ssh toma@lenovo` now works from
the Zenbook by name, from anywhere, and the DHCP address no longer matters. Both signed in through
the same GitHub identity. Traps met on the way:

- `tailscale up` prints its link and then **blocks until the browser confirms**. Started over
  plain SSH with `nohup ... &`, it dies when that SSH session ends, and the link dies with it: the
  browser then says "Login successful" while the machine still says "Logged out". Start it with
  `setsid nohup ... </dev/null &`, or keep the SSH window open until the machine says Running.
- Two `tailscale up` processes waiting at once each regenerate the link, and the sign-in cannot
  complete. Check `pgrep -af "tailscale up"` before starting another.
- The confirm page returned a 500 on the first "Connect" click; reloading it and clicking again
  worked.
- On the Windows side, `winget install Tailscale.Tailscale` cannot show the elevation prompt from
  a non-interactive shell (exit 1602 "cancelled"); the signed MSI run by hand installs fine.

**Not done yet:** Samba, Syncthing, the RAM (15 Nov). The Lenovo is on Wi-Fi; its ethernet port
is unplugged, and a pull of this size wants the cable.

## The corpus pull is running (started 9 Nov 2026, 20:04)

`reconcile/pull_comtrade_bulk.py --all-codes` runs on the Lenovo as a **systemd user service**,
`comtrade-bulk.service`, from `~/comtrade/` (the script, the key file, a `.venv` with `requests`
and `pyarrow`). Output goes to `~/comtrade/raw/comtrade_bulk/<year>/<period>_<reporter>.parquet`,
with `_bulk.log`, `_state.json` and `_manifest.tsv` beside it. The plan check saw 323 periods
(200001 .. 202611) and "ALL products".

- **It survives everything short of a dead disk.** Linger is on, the unit is enabled, and it
  restarts hourly whatever the exit code, so a restart of the machine, a network outage or a
  crash all resume from the state file with nobody logged in. Once the pull is complete that
  hourly run costs a few listing calls.
- **To look:** `tail ~/comtrade/raw/comtrade_bulk/_bulk.log`, or
  `systemctl --user status comtrade-bulk`. **To stop:** `systemctl --user stop comtrade-bulk`
  (and `disable` to keep it stopped across restarts).

Two faults the script had, both invisible on Windows, fixed in the repo the same evening:

- The start-up disk check measured `ROOT[:3]`, which is the drive letter on Windows and a path
  that does not exist on Linux. It now measures the output folder.
- It imported `pandas` without using it, so the documented two-package install
  (`requests`, `pyarrow`) failed on a clean machine.

One limit to know about: a period's listing is cached in the state file the first time it comes
back non-empty. The most recent months were listed with a handful of reporters (202609: 6), and
reporters that publish later will **not** be fetched until those cached listings are cleared.

## Day two of the pull (10 Nov 2026): the quota, the memory, and the yearly series

**Overnight:** 118 GB and 6.3 billion rows by 07:07, no errors, Aug 2020 reached. Five files
(reporter 180, 2022) answered 404 and are left for a later run.

**The quota.** The key has a **daily quota of API calls, and every bulk LISTING call counts**
against it; file downloads do not (5,000 files came down in one day), but once the quota is gone every endpoint refuses, downloads included. A sizing pass of ~300
listing calls, made to measure the yearly series while the pull was running, spent the day's
quota at 09:01, and the pull then skipped its remaining 264 periods in six minutes with
`listing http 403` and ended. The server's answer carries the wait: `Out of call volume quota.
Quota will be replenished in HH:MM:SS` (about 01:00 Paris). The script now reads that and sleeps
it out, caches empty listings for a week so an hourly restart costs nothing, and the rule is: no
other use of the key while a pull runs.

**The memory.** `systemctl --user show comtrade-bulk -p MemoryPeak` read **6.5 GB** on an 8 GB
machine, from decoding one 275 MB archive whole (Spain, 11M rows). Archives above 150 MB are now
decoded in batches with an explicit 34-column schema, in constant memory; tested on a 9M-row file,
the output is identical. The value columns are pinned to float64 on both paths, because inference
had already produced one file with `CIFValue` typed null. One failing file no longer ends the run:
it is logged with its error and retried next time.

**The yearly series, measured before the quota ran out** (listing sizes, nothing downloaded):

| series | files | download | reporters | years |
|---|---|---|---|---|
| goods yearly, HS | 6,054 | 50.7 GB | 221 | 1988-2025 |
| goods yearly, SITC rev.1 | 8,857 | 21.8 GB | 234 | 1962-2025 |
| goods yearly, SITC rev.2 | 2,303 | 1.6 GB | 191 | 1976-1998 (later years not measured) |
| SITC rev.3, rev.4, services | not measured: those calls came after the quota was gone, and a 403 there means nothing | | | |

Against the disk: monthly ~232 GB + yearly ~65 GB on disk, out of 915 GB. The service now runs
`pull_all.sh`: monthly, then yearly HS, SITC1, SITC2, each resumable, each a no-op once complete,
into `raw/comtrade_bulk_A_HS/`, `_A_S1/`, `_A_S2/`. Services trade and SITC3/4 are to be measured
on a fresh quota, a few calls at a time, after the pulls are done.

## Tuning pass (10 Nov 2026)

Measured first: 60 s of full load on all four cores held 3.1 GHz at 76 C with no throttling, so
the dust is not yet a problem; the desktop session costs 0.2 GB of the 7.3 GB; the disk writes
at 425 MB/s. Then one root script, `server_tune.sh` in the kit folder:

- the ext4 root reserve went from 5% to 0.5%, which handed **40 GB** back to data (774 GB free);
- SMART on the new disk: PASSED, 24 power-on hours, zero reallocated or pending sectors;
- Lenovo's battery conservation mode is on and survives restarts (`/etc/tmpfiles.d/`), so a
  machine that lives on mains stops cooking its battery at 100% (it is already at 71% of its
  design capacity);
- Wi-Fi power saving is off (`/etc/NetworkManager/conf.d/`); the signal is -69 dBm, which is
  why a cable is still the better answer;
- SSH takes keys only; the local keyboard is unaffected.

The Zenbook now administers the machine without a password, by the owner's decision: a sudoers
drop-in on the Lenovo, and an allow rule for `ssh lenovo` on the Zenbook side, so root work no
longer goes through a launcher window. Still open: a network cable, the BIOS setting for power
on after a power cut, and the RAM on 15 Nov.

