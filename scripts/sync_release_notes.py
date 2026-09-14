"""Sync GitHub release notes from CHANGELOG.md.

Repairs releases published with empty notes. The release job extracts notes from
the changelog, but a defect in that extraction meant nine consecutive releases
were published with no notes at all; this tool fills them in afterwards.

By default only releases with an empty body are touched, so a hand-written body
is never overwritten. Pass ``--all`` to overwrite every release body from the
changelog. Bodies are whitespace-trimmed either way.

Requires a token with repository read and release write access:

    GITHUB_TOKEN=... python3 scripts/sync_release_notes.py
    GITHUB_TOKEN=... python3 scripts/sync_release_notes.py --all
    GITHUB_TOKEN=... python3 scripts/sync_release_notes.py --dry-run
"""

import json
import os
import sys
import urllib.error
import urllib.request

from extract_changelog import extract

API = "https://api.github.com"
REPO = "Maribbit/openvoca"
CHANGELOG = "CHANGELOG.md"


def _request(method, path, token, payload=None):
    """Call the API and return (status, parsed-body-or-None)."""
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "openvoca-release-tool",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode()
            return response.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:200]
        print(f"    HTTP {exc.code}: {detail}", file=sys.stderr)
        return exc.code, None


def main(argv):
    overwrite = "--all" in argv
    dry_run = "--dry-run" in argv

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("ERROR: set GITHUB_TOKEN to a token with release write access.", file=sys.stderr)
        return 2

    with open(CHANGELOG, encoding="utf-8") as handle:
        changelog = handle.read()

    status, releases = _request("GET", f"/repos/{REPO}/releases?per_page=100", token)
    if status != 200 or not isinstance(releases, list):
        print(f"ERROR: cannot list releases (HTTP {status}).", file=sys.stderr)
        return 1

    updated = skipped = missing = 0

    for release in sorted(releases, key=lambda r: r["tag_name"]):
        tag = release["tag_name"]
        existing = (release.get("body") or "").strip()

        if existing and not overwrite:
            print(f"  {tag:10} kept (already has notes, {len(existing)} bytes)")
            skipped += 1
            continue

        body = extract(changelog, tag)
        if not body:
            print(f"  {tag:10} SKIP - no section in {CHANGELOG}")
            missing += 1
            continue

        if existing == body:
            print(f"  {tag:10} unchanged ({len(body)} bytes)")
            skipped += 1
            continue

        if dry_run:
            print(f"  {tag:10} would update -> {len(body)} bytes")
            updated += 1
            continue

        status, _ = _request(
            "PATCH", f"/repos/{REPO}/releases/{release['id']}", token, {"body": body}
        )
        if status == 200:
            print(f"  {tag:10} updated -> {len(body)} bytes")
            updated += 1
        else:
            print(f"  {tag:10} FAILED (HTTP {status})")
            missing += 1

    verb = "would update" if dry_run else "updated"
    print(f"\n{verb}: {updated} | skipped: {skipped} | failed/missing: {missing}")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
