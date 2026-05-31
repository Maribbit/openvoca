from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "docs" / "specs"
TRACEABILITY_FILE = SPEC_DIR / "test-traceability.md"
TEST_DIRS = [ROOT / "backend" / "tests", ROOT / "frontend" / "tests"]

AC_ID_PATTERN = re.compile(r"\bAC-[A-Z0-9]+-\d{3}-\d{2}\b")
AC_DEFINITION_PATTERN = re.compile(r"^\s*-\s+\*\*(AC-[A-Z0-9]+-\d{3}-\d{2})\*\*", re.MULTILINE)
TS_TEST_PATTERN = re.compile(r"\bit\(\s*([\"'])(?P<name>.+?)\1")


@dataclass(frozen=True)
class MappingEntry:
    test_id: str
    status: str
    covers: tuple[str, ...]
    reason: str | None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def relative_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def spec_files() -> list[Path]:
    if not SPEC_DIR.exists():
        return []
    return sorted(
        path
        for path in SPEC_DIR.glob("*.md")
        if path.name not in {"README.md", "test-traceability.md"}
    )


def collect_spec_ids(paths: list[Path]) -> set[str]:
    ids: set[str] = set()
    for path in paths:
        ids.update(AC_DEFINITION_PATTERN.findall(read_text(path)))
    return ids


def collect_python_tests(path: Path) -> list[str]:
    module = ast.parse(read_text(path), filename=str(path))
    test_ids: list[str] = []

    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            test_ids.append(f"{relative_path(path)}::{node.name}")
            continue
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                    test_ids.append(f"{relative_path(path)}::{node.name}::{child.name}")

    return test_ids


def collect_typescript_tests(path: Path) -> list[str]:
    text = read_text(path)
    return [f"{relative_path(path)}::{match.group('name')}" for match in TS_TEST_PATTERN.finditer(text)]


def collect_tests() -> set[str]:
    test_ids: set[str] = set()
    for test_dir in TEST_DIRS:
        test_ids.update(
            test_id
            for path in sorted(test_dir.rglob("test_*.py"))
            for test_id in collect_python_tests(path)
        )
        test_ids.update(
            test_id
            for path in sorted(test_dir.rglob("*.spec.ts"))
            for test_id in collect_typescript_tests(path)
        )
    return test_ids


def parse_mapping_entries() -> dict[str, MappingEntry]:
    if not TRACEABILITY_FILE.exists():
        return {}

    entries: dict[str, MappingEntry] = {}
    current: dict[str, str] | None = None

    def commit() -> None:
        if current is None:
            return
        test_id = current.get("test")
        if not test_id:
            return
        covers = tuple(AC_ID_PATTERN.findall(current.get("covers", "")))
        entries[test_id] = MappingEntry(
            test_id=test_id,
            status=current.get("status", "").strip(),
            covers=covers,
            reason=current.get("reason"),
        )

    for raw_line in read_text(TRACEABILITY_FILE).splitlines():
        line = raw_line.rstrip()
        if line.startswith("- test: "):
            commit()
            current = {"test": line.removeprefix("- test: ").strip()}
            continue
        if current is None:
            continue
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        current[key.strip()] = value.strip()

    commit()
    return entries


def main() -> int:
    specs = spec_files()
    if not specs:
        print("No spec files found under docs/specs.")
        return 1

    spec_ids = collect_spec_ids(specs)
    tests = collect_tests()
    mappings = parse_mapping_entries()

    if not spec_ids:
        print("No acceptance criteria definitions found in docs/specs.")
        return 1

    problems: list[str] = []
    mapped_tests = set(mappings)
    missing_mappings = sorted(tests - mapped_tests)
    stale_mappings = sorted(mapped_tests - tests)

    if missing_mappings:
        problems.append("Tests missing traceability entries:")
        problems.extend(f"- {test_id}" for test_id in missing_mappings)
    if stale_mappings:
        problems.append("Traceability entries reference missing tests:")
        problems.extend(f"- {test_id}" for test_id in stale_mappings)

    covered_ids: set[str] = set()
    referenced_ids: set[str] = set()
    invalid_status: list[str] = []
    deletion_without_reason: list[str] = []
    keep_without_covers: list[str] = []

    for entry in mappings.values():
        referenced_ids.update(entry.covers)
        if entry.status not in {"keep", "delete-candidate"}:
            invalid_status.append(entry.test_id)
            continue
        if entry.status == "keep":
            if not entry.covers:
                keep_without_covers.append(entry.test_id)
            covered_ids.update(entry.covers)
        if entry.status == "delete-candidate" and not entry.reason:
            deletion_without_reason.append(entry.test_id)

    unknown_ids = sorted(referenced_ids - spec_ids)
    uncovered_ids = sorted(spec_ids - covered_ids)

    if invalid_status:
        problems.append("Traceability entries with invalid status:")
        problems.extend(f"- {test_id}" for test_id in sorted(invalid_status))
    if keep_without_covers:
        problems.append("Kept tests without covered acceptance criteria:")
        problems.extend(f"- {test_id}" for test_id in sorted(keep_without_covers))
    if deletion_without_reason:
        problems.append("Deletion candidates missing a reason:")
        problems.extend(f"- {test_id}" for test_id in sorted(deletion_without_reason))
    if unknown_ids:
        problems.append("Traceability entries reference unknown acceptance criteria:")
        problems.extend(f"- {criterion_id}" for criterion_id in unknown_ids)
    if uncovered_ids:
        problems.append("Acceptance criteria without kept test coverage:")
        problems.extend(f"- {criterion_id}" for criterion_id in uncovered_ids)

    if problems:
        print("\n".join(problems))
        return 1

    delete_candidates = sum(1 for entry in mappings.values() if entry.status == "delete-candidate")
    print(
        "Traceability check passed: "
        f"{len(spec_ids)} acceptance criteria, {len(tests)} tests, "
        f"{delete_candidates} deletion candidates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())