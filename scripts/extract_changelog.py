"""Extract one release section from CHANGELOG.md for use as release notes.

Kept as a script rather than inline shell so the extraction is testable and
portable. The earlier shell version used an ``awk`` range pattern whose start
and end both matched the version heading; the range therefore covered only that
one line, and the following cleanup removed it, so nine consecutive releases
were published with empty notes.

Usage:
    python3 scripts/extract_changelog.py <version> [changelog-path]

``version`` may be given with or without a leading ``v``. The section heading
itself is excluded, because the hosting release page already shows the tag as
the title. Exits non-zero when the section is missing so a release cannot be
published with empty notes.
"""

import re
import sys

HEADING = re.compile(r"^##\s+(?P<version>\S+)\s*$")


def extract(text, version):
    """Return the body of *version*'s section, or None when absent.

    The returned text has surrounding blank lines removed so the published
    notes do not begin or end with empty lines.
    """
    wanted = version.lstrip("v")
    lines = []
    capturing = False

    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            if capturing:
                # Reached the next release heading; the section is complete.
                break
            if match.group("version").lstrip("v") == wanted:
                capturing = True
            continue
        if capturing:
            lines.append(line)

    if not capturing:
        return None

    body = "\n".join(lines).strip("\n")
    return body


def main(argv):
    if len(argv) not in (2, 3):
        print(
            f"usage: {argv[0]} <version> [changelog-path]",
            file=sys.stderr,
        )
        return 2

    version = argv[1]
    path = argv[2] if len(argv) == 3 else "CHANGELOG.md"

    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        return 1

    body = extract(text, version)
    if not body:
        print(f"ERROR: {path} has no section for v{version.lstrip('v')}.", file=sys.stderr)
        return 1

    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
