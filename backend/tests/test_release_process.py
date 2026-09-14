"""Tests for the release tooling in ``scripts/``.

These scripts run outside the application, but a defect in the changelog
extraction once published nine consecutive releases with empty notes while CI
reported success. The extraction and the repair tool's decision rules are
therefore covered here.

The version-consistency check is here too: the three version sources are
documented as needing to stay in sync, and nothing enforced it before.
"""

import json
import tomllib
from pathlib import Path

import pytest

import sync_release_notes
from extract_changelog import extract, main as extract_main
from sync_release_notes import plan_updates

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

SAMPLE = """# Changelog

All notable changes to this project will be documented in this file.

## v1.2.0

Date: 2026-02-01

### Added
- A newer feature.

## v1.1.0

Date: 2026-01-01

### Fixed
- An older bug.

## v1.0.0

Date: 2025-12-01

### Added
- The first release.
"""


# ---------------------------------------------------------------------------
# Version consistency
# ---------------------------------------------------------------------------


# Covers: AC-REL-001-01
def test_version_sources_agree() -> None:
    """VERSION, pyproject.toml and package.json must report the same version."""
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()

    pyproject = tomllib.loads(
        (REPO_ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8")
    )
    package = json.loads(
        (REPO_ROOT / "frontend" / "package.json").read_text(encoding="utf-8")
    )

    assert pyproject["project"]["version"] == version, "pyproject.toml is out of sync"
    assert package["version"] == version, "package.json is out of sync"


# ---------------------------------------------------------------------------
# Changelog extraction
# ---------------------------------------------------------------------------


# Covers: AC-REL-002-01
def test_extraction_excludes_the_heading_line() -> None:
    """The release page already shows the tag, so the heading is not repeated."""
    body = extract(SAMPLE, "1.1.0")

    assert body is not None
    assert not body.startswith("##")
    assert "v1.1.0" not in body


# Covers: AC-REL-002-01
def test_extraction_returns_only_the_requested_section() -> None:
    """Content from other releases must not leak into the notes."""
    body = extract(SAMPLE, "1.1.0")

    assert body is not None
    assert "An older bug." in body
    assert "A newer feature." not in body
    assert "The first release." not in body


# Covers: AC-REL-002-04
def test_extraction_stops_at_the_next_heading() -> None:
    """A section ends where the following release begins."""
    body = extract(SAMPLE, "1.2.0")

    assert body is not None
    assert "A newer feature." in body
    assert "An older bug." not in body


# Covers: AC-REL-002-04
def test_extraction_handles_the_final_section() -> None:
    """The oldest release has no following heading to stop at."""
    body = extract(SAMPLE, "1.0.0")

    assert body is not None
    assert "The first release." in body


# Covers: AC-REL-002-02
def test_extraction_trims_surrounding_blank_lines() -> None:
    """Blank lines around the body would render as stray padding on the page."""
    body = extract(SAMPLE, "1.1.0")

    assert body is not None
    assert body == body.strip("\n")
    assert not body.startswith("\n")
    assert not body.endswith("\n")


# Covers: AC-REL-002-03
def test_extraction_accepts_version_with_and_without_prefix() -> None:
    """Tag names carry a ``v`` prefix while headings have not always done so."""
    with_prefix = extract(SAMPLE, "v1.2.0")
    without_prefix = extract(SAMPLE, "1.2.0")

    assert with_prefix is not None
    assert with_prefix == without_prefix


# Covers: AC-REL-002-03
def test_extraction_matches_headings_without_prefix() -> None:
    """A heading written without the prefix must still be found."""
    changelog = "## 2.0.0\n\nDate: 2026-03-01\n\n### Added\n- Unprefixed heading.\n"

    assert extract(changelog, "v2.0.0") is not None
    assert extract(changelog, "2.0.0") is not None


# Covers: AC-REL-002-05
def test_extraction_returns_none_for_unknown_version() -> None:
    """An absent section must be distinguishable from an empty one."""
    assert extract(SAMPLE, "9.9.9") is None


# Covers: AC-REL-002-05
def test_cli_fails_when_the_section_is_missing(tmp_path: Path) -> None:
    """A missing section must fail the release job rather than publish nothing."""
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(SAMPLE, encoding="utf-8")

    exit_code = extract_main(["extract_changelog.py", "9.9.9", str(changelog)])

    assert exit_code != 0


# Covers: AC-REL-002-05
def test_cli_succeeds_for_a_present_section(tmp_path: Path) -> None:
    """The happy path exits zero so the release job can continue."""
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(SAMPLE, encoding="utf-8")

    exit_code = extract_main(["extract_changelog.py", "1.1.0", str(changelog)])

    assert exit_code == 0


# Covers: AC-REL-002-05
def test_cli_rejects_wrong_argument_count() -> None:
    """Misuse must not look like success."""
    assert extract_main(["extract_changelog.py"]) != 0


# Covers: AC-REL-002-05
def test_current_version_has_release_notes() -> None:
    """Guards the actual release: the shipped version must have notes.

    This catches a version bump that forgot to add the changelog entry, which
    would otherwise surface as empty notes on the release page.
    """
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    body = extract(CHANGELOG.read_text(encoding="utf-8"), version)

    assert body, f"CHANGELOG.md has no section for v{version}"


# Covers: AC-REL-002-01
def test_every_single_release_heading_is_extractable() -> None:
    """Every release named in the real changelog must yield notes.

    Older entries were sometimes written as a range covering several releases
    at once (``## v0.4.6 - v0.4.1``). Such a heading does not name one version,
    so no tag can address it; those are skipped rather than treated as failures.
    """
    text = CHANGELOG.read_text(encoding="utf-8")
    headings = [
        line.removeprefix("## ").strip()
        for line in text.splitlines()
        if line.startswith("## v")
    ]
    single = [h for h in headings if " " not in h]

    assert len(single) > 10, "expected many single-release headings"
    for heading in single:
        assert extract(text, heading), f"{heading} produced empty notes"


# ---------------------------------------------------------------------------
# Release note repair tool
# ---------------------------------------------------------------------------


# Covers: AC-REL-003-01
def test_plan_keeps_a_hand_written_body() -> None:
    """A body a human wrote must survive the repair tool."""
    releases = [{"tag_name": "v1.1.0", "id": 1, "body": "Hand-written."}]

    plan = plan_updates(releases, SAMPLE)

    assert [(r["tag_name"], action) for r, action, _ in plan] == [("v1.1.0", "keep")]


# Covers: AC-REL-003-01
def test_plan_fills_an_empty_body() -> None:
    """The whole point of the tool: empty notes get filled from the changelog."""
    releases = [{"tag_name": "v1.1.0", "id": 1, "body": None}]

    plan = plan_updates(releases, SAMPLE)

    assert len(plan) == 1
    _, action, body = plan[0]
    assert action == "update"
    assert "An older bug." in body


# Covers: AC-REL-003-01
def test_plan_treats_whitespace_as_empty() -> None:
    """A body of only whitespace carries no content and should be replaced."""
    releases = [{"tag_name": "v1.1.0", "id": 1, "body": "   \n\n  "}]

    plan = plan_updates(releases, SAMPLE)

    assert plan[0][1] == "update"


# Covers: AC-REL-003-01
def test_plan_overwrite_replaces_a_hand_written_body() -> None:
    """Overwriting is available, but only when explicitly requested."""
    releases = [{"tag_name": "v1.1.0", "id": 1, "body": "Hand-written."}]

    plan = plan_updates(releases, SAMPLE, overwrite=True)

    assert plan[0][1] == "update"
    assert "An older bug." in plan[0][2]


# Covers: AC-REL-003-01
def test_plan_leaves_a_matching_body_alone() -> None:
    """No write is needed when the body already matches the changelog."""
    body = extract(SAMPLE, "1.1.0")
    releases = [{"tag_name": "v1.1.0", "id": 1, "body": body}]

    plan = plan_updates(releases, SAMPLE)

    assert plan[0][1] == "unchanged"


# Covers: AC-REL-003-01
def test_plan_reports_releases_without_a_section() -> None:
    """A release absent from the changelog is reported, never silently skipped."""
    releases = [{"tag_name": "v9.9.9", "id": 1, "body": None}]

    plan = plan_updates(releases, SAMPLE)

    assert plan[0][1] == "missing"


# Covers: AC-REL-003-01
def test_plan_orders_releases_by_tag() -> None:
    """Reporting follows version order so output is readable."""
    releases = [
        {"tag_name": "v1.2.0", "id": 2, "body": None},
        {"tag_name": "v1.0.0", "id": 0, "body": None},
        {"tag_name": "v1.1.0", "id": 1, "body": None},
    ]

    plan = plan_updates(releases, SAMPLE)

    assert [r["tag_name"] for r, _, _ in plan] == ["v1.0.0", "v1.1.0", "v1.2.0"]


# Covers: AC-REL-003-02
def test_dry_run_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A dry run must inspect and report without writing anything."""
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(SAMPLE, encoding="utf-8")
    changelog_path = str(changelog)

    calls: list[tuple[str, str]] = []

    def fake_request(method, path, token, payload=None):
        calls.append((method, path))
        if method == "GET":
            return 200, [{"tag_name": "v1.1.0", "id": 7, "body": None}]
        return 200, {}

    monkeypatch.setattr(sync_release_notes, "_request", fake_request)
    monkeypatch.setattr(sync_release_notes, "CHANGELOG", changelog_path)
    monkeypatch.setenv("GITHUB_TOKEN", "token-value")

    exit_code = sync_release_notes.main(["--dry-run"])

    assert exit_code == 0
    assert [method for method, _ in calls] == ["GET"]


# Covers: AC-REL-003-02
# Covers: AC-REL-003-01
def test_real_run_patches_only_the_empty_release(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Without a dry run, only releases that need notes are written."""
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(SAMPLE, encoding="utf-8")
    changelog_path = str(changelog)

    patched: list[str] = []

    def fake_request(method, path, token, payload=None):
        if method == "GET":
            return 200, [
                {"tag_name": "v1.1.0", "id": 11, "body": None},
                {"tag_name": "v1.2.0", "id": 12, "body": "Hand-written."},
            ]
        patched.append(path)
        return 200, {}

    monkeypatch.setattr(sync_release_notes, "_request", fake_request)
    monkeypatch.setattr(sync_release_notes, "CHANGELOG", changelog_path)
    monkeypatch.setenv("GITHUB_TOKEN", "token-value")

    exit_code = sync_release_notes.main([])

    assert exit_code == 0
    assert patched == ["/repos/Maribbit/openvoca/releases/11"]


# Covers: AC-REL-003-01
def test_missing_section_fails_the_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A release with no changelog section is reported, not silently skipped."""
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(SAMPLE, encoding="utf-8")
    changelog_path = str(changelog)

    def fake_request(method, path, token, payload=None):
        if method == "GET":
            return 200, [{"tag_name": "v9.9.9", "id": 99, "body": None}]
        return 200, {}

    monkeypatch.setattr(sync_release_notes, "_request", fake_request)
    monkeypatch.setattr(sync_release_notes, "CHANGELOG", changelog_path)
    monkeypatch.setenv("GITHUB_TOKEN", "token-value")

    assert sync_release_notes.main([]) != 0


# Covers: AC-REL-003-02
def test_missing_token_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Running without a token must explain itself instead of failing obscurely."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    assert sync_release_notes.main([]) == 2
