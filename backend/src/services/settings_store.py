from sqlmodel import Field, Session, SQLModel, select

from src.services.word_store import get_engine

# Namespaces the generic store must not write to. The provider namespace holds
# the active LLM configuration, which has a dedicated write path that also
# rebuilds the in-memory client; writing it here would let the two drift apart.
PROTECTED_NAMESPACES = frozenset({"provider"})


class SettingRecord(SQLModel, table=True):
    namespace: str = Field(primary_key=True)
    key: str = Field(primary_key=True)
    value: str = Field()


def _get_engine(engine=None):
    return engine or get_engine()


def init_settings_table(engine=None) -> None:
    """Create the settings table if it doesn't exist."""
    target = _get_engine(engine)
    SQLModel.metadata.create_all(target)


def get_setting(namespace: str, key: str, engine=None) -> str | None:
    """Return the value for a single setting, or None if not found."""
    target = _get_engine(engine)
    with Session(target) as session:
        record = session.exec(
            select(SettingRecord).where(
                SettingRecord.namespace == namespace,
                SettingRecord.key == key,
            )
        ).first()
        return record.value if record else None


def get_namespace(namespace: str, engine=None) -> dict[str, str]:
    """Return all settings in a namespace as a dict."""
    target = _get_engine(engine)
    with Session(target) as session:
        records = session.exec(
            select(SettingRecord).where(SettingRecord.namespace == namespace)
        ).all()
        return {r.key: r.value for r in records}


def get_all_settings(engine=None) -> dict[str, dict[str, str]]:
    """Return all settings grouped by namespace."""
    target = _get_engine(engine)
    with Session(target) as session:
        records = session.exec(select(SettingRecord)).all()
        result: dict[str, dict[str, str]] = {}
        for r in records:
            result.setdefault(r.namespace, {})[r.key] = r.value
        return result


def upsert_setting(namespace: str, key: str, value: str, engine=None) -> None:
    """Insert or update a single setting."""
    target = _get_engine(engine)
    with Session(target) as session:
        record = session.exec(
            select(SettingRecord).where(
                SettingRecord.namespace == namespace,
                SettingRecord.key == key,
            )
        ).first()
        if record:
            record.value = value
        else:
            session.add(SettingRecord(namespace=namespace, key=key, value=value))
        session.commit()


def upsert_namespace(namespace: str, settings: dict[str, str], engine=None) -> None:
    """Batch upsert all settings in a namespace."""
    target = _get_engine(engine)
    with Session(target) as session:
        for key, value in settings.items():
            record = session.exec(
                select(SettingRecord).where(
                    SettingRecord.namespace == namespace,
                    SettingRecord.key == key,
                )
            ).first()
            if record:
                record.value = value
            else:
                session.add(SettingRecord(namespace=namespace, key=key, value=value))
        session.commit()


def delete_namespace(namespace: str, engine=None) -> int:
    """Delete all settings in a namespace. Returns count of deleted rows."""
    target = _get_engine(engine)
    with Session(target) as session:
        records = session.exec(
            select(SettingRecord).where(SettingRecord.namespace == namespace)
        ).all()
        count = len(records)
        for record in records:
            session.delete(record)
        session.commit()
        return count


def delete_setting(namespace: str, key: str, engine=None) -> int:
    """Delete a single setting. Returns 1 when a row was removed, otherwise 0."""
    target = _get_engine(engine)
    with Session(target) as session:
        record = session.exec(
            select(SettingRecord).where(
                SettingRecord.namespace == namespace,
                SettingRecord.key == key,
            )
        ).first()
        if record is None:
            return 0
        session.delete(record)
        session.commit()
        return 1


def clear_all_settings(engine=None) -> int:
    """Delete every setting outside protected namespaces.

    Returns count of deleted rows. Protected namespaces are skipped so that
    resetting preferences cannot silently discard the model configuration.
    """
    target = _get_engine(engine)
    with Session(target) as session:
        records = session.exec(select(SettingRecord)).all()
        targets = [r for r in records if r.namespace not in PROTECTED_NAMESPACES]
        count = len(targets)
        for record in targets:
            session.delete(record)
        session.commit()
        return count
