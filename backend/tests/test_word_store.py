import pytest
from src.services.word_store import (
    LEVEL_BASE,
    LEVEL_MAX,
    LEVEL_MIN,
    ImportResult,
    MAX_IMPORT_ROWS,
    _make_engine,
    apply_feedback,
    draft_feedback,
    clear_all_words,
    delete_word_record,
    import_vocabulary,
    list_all_words,
    tick_cooldowns,
    update_word_record,
)

from conftest import _in_memory_engine


# ---------------------------------------------------------------------------
# Word store / familiarity update tests
# ---------------------------------------------------------------------------


# Covers: AC-SRS-001-01, AC-SRS-005-01
def test_apply_feedback_creates_new_records() -> None:
    """Marked words should be created with level=LEVEL_MIN, unmarked targets with LEVEL_MIN+1."""
    engine = _in_memory_engine()

    apply_feedback(
        ["lantern", "meadow"],
        ["meadow"],
        "A lantern glowed beside the meadow.",
        engine=engine,
    )

    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["lantern"].level == LEVEL_MIN + 1  # hit
    assert words["meadow"].level == LEVEL_MIN  # miss


# Covers: AC-SRS-005-01
def test_apply_feedback_sets_first_seen_once() -> None:
    """first_seen should be set on creation and not modified on updates."""
    engine = _in_memory_engine()

    apply_feedback(["harbor"], [], "The harbor.", engine=engine)
    original_first_seen = list_all_words(engine)[0].first_seen

    for _ in range(LEVEL_BASE ** (LEVEL_MIN + 1)):
        tick_cooldowns(engine)
    apply_feedback(["harbor"], ["harbor"], "Ships lined the harbor.", engine=engine)

    words = list_all_words(engine)
    assert words[0].first_seen == original_first_seen


# Covers: AC-SRS-005-01
def test_apply_feedback_increments_seen_count() -> None:
    """seen_count should increment each time a word is a target word."""
    engine = _in_memory_engine()

    apply_feedback(["harbor"], [], "The harbor.", engine=engine)
    assert list_all_words(engine)[0].seen_count == 1

    for _ in range(LEVEL_BASE ** (LEVEL_MIN + 1)):
        tick_cooldowns(engine)

    apply_feedback(["harbor"], ["harbor"], "Ships lined the harbor.", engine=engine)
    assert list_all_words(engine)[0].seen_count == 2


# Covers: AC-SRS-005-02
def test_non_target_word_marked_creates_record() -> None:
    """Marking a non-target word should create it with miss rules."""
    engine = _in_memory_engine()

    apply_feedback([], ["flutter"], "The flag fluttered.", engine=engine)

    records = {r.lemma: r for r in list_all_words(engine)}
    assert "flutter" in records
    assert records["flutter"].level == LEVEL_MIN
    assert records["flutter"].cooldown == LEVEL_BASE**LEVEL_MIN


# Covers: AC-SRS-005-01
def test_last_context_stored() -> None:
    """apply_feedback should store the sentence as last_context."""
    engine = _in_memory_engine()

    sentence = "The harbor was calm."
    apply_feedback(["harbor"], [], sentence, engine=engine)
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].last_context == sentence


# Covers: AC-SRS-006-01
def test_clear_all_words_empties_database() -> None:
    """clear_all_words should delete every record."""
    engine = _in_memory_engine()

    apply_feedback(["a", "b", "c"], [], "sentence", engine=engine)
    assert len(list_all_words(engine)) == 3

    deleted = clear_all_words(engine)
    assert deleted == 3
    assert len(list_all_words(engine)) == 0


# ---------------------------------------------------------------------------
# Manual word record update
# ---------------------------------------------------------------------------


# Covers: AC-SRS-006-02
def test_update_word_record_level() -> None:
    """update_word_record should update level within bounds."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], ["apple"], "An apple.", engine=engine)

    record = update_word_record("apple", level=LEVEL_MIN + 1, engine=engine)
    assert record is not None
    assert record.level == LEVEL_MIN + 1

    record = update_word_record("apple", level=LEVEL_MIN, engine=engine)
    assert record is not None
    assert record.level == LEVEL_MIN


# Covers: AC-SRS-006-02
def test_update_word_record_level_clamped() -> None:
    """Level should be clamped to [LEVEL_MIN, LEVEL_MAX]."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], ["apple"], "An apple.", engine=engine)

    record = update_word_record("apple", level=0, engine=engine)
    assert record is not None
    assert record.level == LEVEL_MIN

    record = update_word_record("apple", level=999, engine=engine)
    assert record is not None
    assert record.level == LEVEL_MAX


# Covers: AC-SRS-006-02
def test_update_word_record_cooldown() -> None:
    """update_word_record should update cooldown within [0, interval]."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], [], "An apple.", engine=engine)

    record = update_word_record("apple", cooldown=0, engine=engine)
    assert record is not None
    assert record.cooldown == 0

    record = update_word_record(
        "apple", cooldown=LEVEL_BASE ** (LEVEL_MIN + 1), engine=engine
    )
    assert record is not None
    assert record.cooldown == LEVEL_BASE ** (LEVEL_MIN + 1)


# Covers: AC-SRS-006-02
def test_update_word_record_cooldown_clamped() -> None:
    """Cooldown should be clamped to [0, interval]."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], ["apple"], "An apple.", engine=engine)

    record = update_word_record("apple", cooldown=-5, engine=engine)
    assert record is not None
    assert record.cooldown == 0

    record = update_word_record("apple", cooldown=999, engine=engine)
    assert record is not None
    assert record.cooldown == LEVEL_BASE**LEVEL_MIN


# Covers: AC-SRS-006-03
def test_update_word_record_not_found() -> None:
    """update_word_record should return None for missing records."""
    engine = _in_memory_engine()

    result = update_word_record("nonexistent", level=2, engine=engine)
    assert result is None


# ---------------------------------------------------------------------------
# Delete single word record
# ---------------------------------------------------------------------------


# Covers: AC-SRS-006-04
def test_delete_word_record() -> None:
    """delete_word_record should remove a specific word."""
    engine = _in_memory_engine()

    apply_feedback(
        ["apple", "banana"], ["apple"], "An apple and a banana.", engine=engine
    )
    assert len(list_all_words(engine)) == 2

    deleted = delete_word_record("apple", engine=engine)
    assert deleted is True
    remaining = list_all_words(engine)
    assert len(remaining) == 1
    assert remaining[0].lemma == "banana"


# Covers: AC-SRS-006-04
def test_delete_word_record_not_found() -> None:
    """delete_word_record should return False for missing records."""
    engine = _in_memory_engine()

    deleted = delete_word_record("nonexistent", engine=engine)
    assert deleted is False


# Covers: AC-SRS-006-04
def test_delete_stale_record() -> None:
    """Deleting an already-deleted record (stale tab) should return False."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], ["apple"], "An apple.", engine=engine)

    assert delete_word_record("apple", engine=engine) is True
    assert delete_word_record("apple", engine=engine) is False


# Covers: AC-SRS-006-03
def test_update_stale_record() -> None:
    """Updating a record that was deleted in another tab should return None."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], ["apple"], "An apple.", engine=engine)

    delete_word_record("apple", engine=engine)
    result = update_word_record("apple", level=3, engine=engine)
    assert result is None


# --- OPENVOCA_DATA_DIR engine path ---


# Covers: AC-SRS-007-01
def test_make_engine_default_path() -> None:
    """_make_engine() without env var uses a relative openvoca.db path."""
    engine = _make_engine()
    assert "openvoca.db" in str(engine.url)


# Covers: AC-SRS-007-01
def test_make_engine_respects_data_dir(
    tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_make_engine() uses OPENVOCA_DATA_DIR when set."""
    monkeypatch.setenv("OPENVOCA_DATA_DIR", str(tmp_path))
    engine = _make_engine()
    assert str(tmp_path / "openvoca.db") in str(engine.url)


# ---------------------------------------------------------------------------
# Vocabulary import
# ---------------------------------------------------------------------------


# Covers: AC-SRS-008-02
def test_import_vocabulary_creates_new_records() -> None:
    """import_vocabulary should insert records that don't exist yet."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "harbor", "level": "3", "cooldown": "3"},
        {"lemma": "lantern", "level": "2", "cooldown": "0"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 2
    assert result.skipped == 0
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == 3
    assert records["harbor"].cooldown == 3
    assert records["lantern"].level == 2
    assert records["lantern"].cooldown == 0


# Covers: AC-SRS-008-03
def test_import_vocabulary_overwrite_existing_records() -> None:
    """import_vocabulary(mode='overwrite') should overwrite existing records."""
    engine = _in_memory_engine()

    apply_feedback(["harbor"], [], "The harbor.", engine=engine)

    rows = [{"lemma": "harbor", "level": "4", "cooldown": "8"}]
    result = import_vocabulary(rows, mode="overwrite", engine=engine)

    assert result.imported == 1
    assert result.skipped == 0
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == 4
    assert records["harbor"].cooldown == 8


# Covers: AC-SRS-008-03
def test_import_vocabulary_skip_preserves_existing_records() -> None:
    """import_vocabulary(mode='skip') should keep existing records untouched."""
    engine = _in_memory_engine()

    apply_feedback(["harbor"], [], "The harbor.", engine=engine)
    original_level = list_all_words(engine)[0].level

    rows = [
        {"lemma": "harbor", "level": "5", "cooldown": "16"},
        {"lemma": "lantern", "level": "2", "cooldown": "0"},
    ]
    result = import_vocabulary(rows, mode="skip", engine=engine)

    assert result.imported == 1  # only lantern
    assert result.skipped == 1  # harbor skipped
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == original_level  # preserved
    assert records["lantern"].level == 2  # new


# Covers: AC-SRS-008-03
def test_import_vocabulary_default_mode_is_skip() -> None:
    """The default import mode should be 'skip' (safe default)."""
    engine = _in_memory_engine()

    apply_feedback(["harbor"], [], "The harbor.", engine=engine)
    original_level = list_all_words(engine)[0].level

    rows = [{"lemma": "harbor", "level": "5", "cooldown": "16"}]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 0
    assert result.skipped == 1
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == original_level


# Covers: AC-SRS-008-04
def test_import_vocabulary_skips_missing_columns() -> None:
    """Rows missing required columns should be skipped and counted."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "apple", "level": "2", "cooldown": "0"},
        {"level": "2", "cooldown": "0"},  # missing lemma
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 1
    assert result.skipped == 1
    assert len(result.errors) == 1


# Covers: AC-SRS-008-04
def test_import_vocabulary_skips_empty_lemma() -> None:
    """Rows with empty lemma should be skipped."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "", "level": "2", "cooldown": "0"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 0
    assert result.skipped == 1


# Covers: AC-SRS-008-04
def test_import_vocabulary_skips_non_integer_values() -> None:
    """Rows with non-integer level or cooldown should be skipped."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "cherry", "level": "abc", "cooldown": "0"},
        {"lemma": "mango", "level": "2", "cooldown": "xyz"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 0
    assert result.skipped == 2
    assert len(result.errors) == 2


# Covers: AC-SRS-008-05
def test_import_vocabulary_clamps_out_of_range_values() -> None:
    """Level and cooldown outside valid ranges should be clamped, not rejected."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "alpha", "level": "0", "cooldown": "0"},
        {"lemma": "beta", "level": "999", "cooldown": "500"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 2
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["alpha"].level == LEVEL_MIN
    assert records["beta"].level == LEVEL_MAX
    assert records["beta"].cooldown == LEVEL_BASE**LEVEL_MAX


# Covers: AC-SRS-008-05
def test_import_vocabulary_normalizes_case() -> None:
    """lemma should be lowercased on import."""
    engine = _in_memory_engine()

    rows = [{"lemma": "HARBOR", "level": "2", "cooldown": "0"}]
    import_vocabulary(rows, engine=engine)

    records = list_all_words(engine)
    assert records[0].lemma == "harbor"


# Covers: AC-SRS-008-05
def test_import_vocabulary_legacy_pos_column_ignored() -> None:
    """Legacy CSV files with a 'pos' column should still import successfully."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "harbor", "pos": "NOUN", "level": "3", "cooldown": "3"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 1
    records = list_all_words(engine)
    assert records[0].lemma == "harbor"
    assert records[0].level == 3


# Covers: AC-SRS-008-04
def test_import_vocabulary_empty_rows() -> None:
    """Empty row list should return imported=0 with no errors."""
    engine = _in_memory_engine()
    result = import_vocabulary([], engine=engine)

    assert result.imported == 0
    assert result.skipped == 0
    assert result.errors == []


# Covers: AC-SRS-008-04
def test_import_vocabulary_too_many_rows() -> None:
    """Row count exceeding MAX_IMPORT_ROWS should fail without inserting anything."""
    engine = _in_memory_engine()

    overflow = [
        {"lemma": f"word{i}", "level": "1", "cooldown": "0"}
        for i in range(MAX_IMPORT_ROWS + 1)
    ]
    result = import_vocabulary(overflow, engine=engine)

    assert result.imported == 0
    assert len(result.errors) == 1
    assert len(list_all_words(engine)) == 0


@pytest.mark.skip(
    reason="只验证 ImportResult 的 dataclass 默认值，概念价值低，导入结果语义已由导入测试覆盖。"
)
def test_import_result_is_dataclass() -> None:
    """ImportResult should have default zero values."""
    r = ImportResult()
    assert r.imported == 0
    assert r.skipped == 0
    assert r.errors == []


# Covers: AC-SRS-008-02
def test_import_vocabulary_minimal_columns() -> None:
    """Rows with only lemma should import with default values."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "harbor"},
        {"lemma": "glow"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 2
    assert result.skipped == 0
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == LEVEL_MIN
    assert records["harbor"].cooldown == 0
    assert records["harbor"].last_context is None
    assert records["glow"].level == LEVEL_MIN


# Covers: AC-SRS-008-05
def test_import_vocabulary_with_last_seen_and_context() -> None:
    """Import should accept and preserve last_seen and last_context."""
    engine = _in_memory_engine()

    rows = [
        {
            "lemma": "harbor",
            "level": "3",
            "cooldown": "3",
            "last_seen": "2026-01-15T10:30:00+00:00",
            "last_context": "The harbor was calm.",
        },
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 1
    records = list_all_words(engine)
    assert records[0].last_seen.year == 2026
    assert records[0].last_seen.month == 1
    assert records[0].last_context == "The harbor was calm."


# Covers: AC-SRS-008-04
def test_import_vocabulary_bad_last_seen_skips_row() -> None:
    """Invalid last_seen format should cause the row to be skipped."""
    engine = _in_memory_engine()

    rows = [
        {
            "lemma": "harbor",
            "level": "3",
            "cooldown": "3",
            "last_seen": "not-a-date",
        },
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 0
    assert result.skipped == 1
    assert "ISO 8601" in result.errors[0]


# Covers: AC-SRS-010-01, AC-LOOP-003-01
def test_draft_feedback() -> None:
    engine = _in_memory_engine()

    apply_feedback(
        ["apple", "banana", "elephant", "dog"], [], "sentence", engine=engine
    )

    deltas = draft_feedback(
        target_words=["apple", "carrot"],
        marked_words=["carrot", "dog"],
        original_targets=["elephant"],
        engine=engine,
    )

    deltas = sorted(deltas, key=lambda d: d.lemma)
    assert len(deltas) == 4

    assert deltas[0].lemma == "apple"
    assert deltas[0].new_level == 3
    assert deltas[0].is_new is False

    assert deltas[1].lemma == "carrot"
    assert deltas[1].new_level == 1
    assert deltas[1].is_new is True

    assert deltas[2].lemma == "dog"
    assert deltas[2].new_level == 1
    assert deltas[2].is_new is False

    assert deltas[3].lemma == "elephant"
    assert deltas[3].new_level == 3
    assert deltas[3].is_new is False
