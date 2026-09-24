"""Has Zenodo archived the newest GitHub release?

WHY: on 2026-09-24 release v1.8 was published, GitHub delivered the webhook, and Zenodo answered
202 Accepted - and then never created the record. Its own answer to a redelivery was "The release has
already been received", so the event could not be retried, and the uploads list held only v1.7 while
zenodo.org showed a service-degradation banner. Nothing on our side failed and nothing alerted: the
site was correct, the repo was pushed, and only the citable record silently lagged a published
correction. That is the same class of fault as a fetch that fails silently - no symptom, wrong
downstream - so it gets a check rather than a memory.

HOW: compare the newest GitHub release tag against the newest version string in the Zenodo concept
record. Both are public and need no token. The concept DOI 10.5281/zenodo.21948855 always resolves to
the latest version, so its version list is the archive of record.

    python check_zenodo_archive.py     # exit 0 = archived, 1 = not yet, 2 = cannot tell

Exit 1 is expected for a little while after a release: Zenodo takes minutes, sometimes longer. The
workflow that calls this runs daily, so a "not yet" only becomes an issue when it persists.

When it reports NOT ARCHIVED for more than a day: check https://zenodo.org/me/uploads for a stuck
draft, and if there is none, publish a new patch release (the failed one can never be retried, since
Zenodo refuses it as already received). Say in those release notes that the previous tag failed to
archive, so the gap in the version history is documented rather than mysterious.
"""
import json
import sys
import urllib.request

CONCEPT = "21948855"          # the atlas concept record; CITATION.cff carries its DOI
REPO = "materials-atlas/critical-materials-atlas"
UA = {"User-Agent": "critical-materials-atlas archive check"}


def get_json(url, timeout=45):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def latest_github_release():
    d = get_json("https://api.github.com/repos/%s/releases/latest" % REPO)
    return d["tag_name"], d.get("published_at", "")


def zenodo_versions():
    """Every version string Zenodo holds for the concept record, newest first."""
    d = get_json("https://zenodo.org/api/records?q=parent.id:%s&sort=newest&size=10" % CONCEPT)
    out = []
    for h in d.get("hits", {}).get("hits", []):
        out.append((str(h.get("id")), h.get("metadata", {}).get("version", "?"),
                    h.get("metadata", {}).get("publication_date", "?")))
    return out


def main():
    try:
        tag, published = latest_github_release()
    except Exception as e:
        print("cannot read the GitHub release list: %s" % e)
        return 2
    try:
        versions = zenodo_versions()
    except Exception as e:
        # Zenodo being down is exactly the condition this check exists for, but it cannot be told
        # apart from "not archived" without an answer, so it reports "cannot tell" and says why.
        print("cannot read Zenodo (service down, or the API changed): %s" % e)
        return 2
    if not versions:
        print("Zenodo returned no versions for concept record %s - the API or the record moved" % CONCEPT)
        return 2
    print("newest GitHub release: %s (published %s)" % (tag, published))
    print("Zenodo versions held: %s" % ", ".join("%s=%s" % (v, rid) for rid, v, _ in versions))
    # Zenodo's version string is the tag as GitHub sent it, so compare on the tag with and without "v"
    wanted = {tag, tag.lstrip("v")}
    for rid, version, date in versions:
        if version in wanted or str(version).lstrip("v") in {t.lstrip("v") for t in wanted}:
            print("ARCHIVED: %s is Zenodo record %s (published %s)" % (version, rid, date))
            print("  https://zenodo.org/records/%s" % rid)
            return 0
    print("NOT ARCHIVED: Zenodo holds no version matching %s." % tag)
    print("  Newest there is %s. If this persists, the release cannot be retried - see this file's"
          % versions[0][1])
    print("  header for the repair.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
