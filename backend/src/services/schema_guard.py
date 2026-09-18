"""Startup check that the database matches the models this revision was built against.

``SQLModel.metadata.create_all()`` creates missing tables but leaves existing ones
untouched, so a model that gained a column keeps running against a table that never
received it. The failure is delayed and indirect: the application starts, the health
check answers, static pages load, and the first query touching that column raises.
Every automated probe reports the service as healthy, which makes this the most
expensive kind of failure to diagnose.

A surplus column is a different situation and is deliberately not reported as a gap.
That is what a rollback looks like, because the newer revision is the one that added
it. Refusing to start then would block the recovery path an operator reaches for
exactly when a deploy has gone wrong.
"""

from dataclasses import dataclass

from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel


@dataclass(frozen=True)
class SchemaGap:
    """Columns a model declares that the corresponding table does not have."""

    table: str
    missing: tuple[str, ...]


def find_schema_gaps(engine: Engine) -> list[SchemaGap]:
    """Return every table whose columns fall short of its model.

    Tables absent from the database are skipped rather than reported: creating
    them is ``create_all``'s job and it runs before this check.
    """
    inspector = inspect(engine)
    present = set(inspector.get_table_names())

    gaps: list[SchemaGap] = []
    for name, table in sorted(SQLModel.metadata.tables.items()):
        if name not in present:
            continue
        actual = {column["name"] for column in inspector.get_columns(name)}
        missing = {column.name for column in table.columns} - actual
        if missing:
            gaps.append(SchemaGap(table=name, missing=tuple(sorted(missing))))
    return gaps


def describe_gaps(gaps: list[SchemaGap]) -> str:
    """Explain which tables disagree with the models and how to recover."""
    lines = [
        "Database schema does not match the models this revision expects.",
        "Refusing to start: queries would fail at runtime instead of at startup.",
        "",
    ]
    lines.extend(
        f"  table {gap.table} is missing column(s): {', '.join(gap.missing)}"
        for gap in gaps
    )
    lines.extend(
        [
            "",
            "This is what a revision that added a field looks like against a database",
            "that predates it. Migrate the database, or start the revision that created",
            "the current schema.",
        ]
    )
    return "\n".join(lines)
