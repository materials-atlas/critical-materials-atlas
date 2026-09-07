"""Has CEPII published a BACI release newer than V202601 (i.e. one carrying trade-year 2025)?

WHY: the atlas pre-registration (reconcile/PREREGISTRATION.md, filed 2026-06-26) is scored the moment
BACI 2025 exists. out/flows_2025.json is frozen at commit beb94dd. On 2026-09-06 the current release
was V202601 (30 Jan 2026), which stops at trade-year 2024.

HOW: the CEPII item page is a JavaScript shell and its /DATA_DOWNLOAD/ directory returns a soft error
page, so neither can be scraped. Instead we HEAD the versioned zip directly. The pattern is verified
against the known-good V202601 on every run, so a change in CEPII's URL scheme fails LOUDLY rather
than being reported as "not yet".

    python check_baci_release.py       # exit 0 = a newer release exists, 1 = not yet, 2 = cannot tell

When it reports READY: download into raw/baci/, then `python validate.py 2025`, and commit the output
to results/ pass or fail - the pre-registration commits to publishing a miss.
Then, and only then, the single short note owed to Morgan Bazilian (Payne Institute) comes due.
"""
import sys, urllib.request

BASE = "https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS17_V%s.zip"
KNOWN = "202601"                      # verified present, 794,583,540 bytes, covers through 2024
CANDIDATES = ["2026%02d" % m for m in range(2, 13)] + ["2027%02d" % m for m in range(1, 13)]

def exists(version, timeout=30):
    req = urllib.request.Request(BASE % version,
                                 headers={"User-Agent": "critical-materials-atlas release check"},
                                 method="HEAD")
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status == 200, r.headers.get("Content-Length")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, None
        raise

def main():
    try:
        ok, size = exists(KNOWN)
    except Exception as e:
        print("CANNOT TELL - could not reach CEPII:", e); return 2
    if not ok:
        print("CANNOT TELL - the known release V%s is no longer at the expected URL." % KNOWN)
        print("CEPII has changed its scheme; check by hand and update this script.")
        return 2
    print("pattern OK: V%s present (%s bytes)" % (KNOWN, size))

    found = []
    for v in CANDIDATES:
        try:
            ok, size = exists(v, timeout=20)
        except Exception:
            continue
        if ok:
            found.append((v, size))
    if found:
        print("\nREADY - newer release(s) published:")
        for v, size in found:
            print("  V%s  (%s bytes)" % (v, size))
        print("\n  1. download into raw/baci/")
        print("  2. python validate.py 2025")
        print("  3. commit the score to results/ - pass or fail")
        print("  4. the single note owed to Morgan Bazilian is now due")
        return 0
    print("\nNOT YET - V%s is still the newest. Check again next month." % KNOWN)
    return 1

if __name__ == "__main__":
    sys.exit(main())
