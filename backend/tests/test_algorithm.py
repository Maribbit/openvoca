"""SRS algorithm tests: level progression, cooldown queue,
target word picking, and the original_targets safety net."""

from src.services.word_store import (
    LEVEL_BASE,
    LEVEL_MAX,
    LEVEL_MIN,
    apply_feedback,
    list_all_words,
    pick_target_words,
    tick_cooldowns,
)

from conftest import _in_memory_engine


# ---------------------------------------------------------------------------
# Level progression
# ---------------------------------------------------------------------------


# Covers: AC-SRS-001-01
def test_apply_feedback_decreases_level_for_marked_words() -> None:
    """Marking a previously known word should decrement its level."""
    engine = _in_memory_engine()

    apply_feedback(["harbor"], [], "The harbor was calm.", engine=engine)
    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["harbor"].level == LEVEL_MIN + 1

    for _ in range(LEVEL_BASE ** (LEVEL_MIN + 1)):
        tick_cooldowns(engine)

    apply_feedback(["harbor"], ["harbor"], "Ships lined the harbor.", engine=engine)
    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["harbor"].level == LEVEL_MIN


# Covers: AC-SRS-001-02
def test_apply_feedback_caps_level_at_boundaries() -> None:
    """Level should never go below LEVEL_MIN or above LEVEL_MAX."""
    engine = _in_memory_engine()

    apply_feedback(["resolve"], [], "They showed resolve.", engine=engine)
    for _ in range(10):
        tick_cooldowns(engine)
    for _ in range(10):
        apply_feedback(["resolve"], [], "They showed resolve.", engine=engine)
        for _ in range(LEVEL_BASE**LEVEL_MAX):
            tick_cooldowns(engine)

    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["resolve"].level == LEVEL_MAX

    for _ in range(10):
        apply_feedback([], ["resolve"], "They showed resolve.", engine=engine)
    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["resolve"].level == LEVEL_MIN


# Covers: AC-SRS-001-03
def test_graduated_word_relapse_on_mark() -> None:
    """Marking a graduated word (level=MAX) should bring it back into review."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], [], "An apple.", engine=engine)
    for _ in range(20):
        for _ in range(LEVEL_BASE**LEVEL_MAX):
            tick_cooldowns(engine)
        apply_feedback(["apple"], [], "An apple.", engine=engine)

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].level == LEVEL_MAX

    apply_feedback([], ["apple"], "An apple fell.", engine=engine)
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].level == LEVEL_MAX - 1
    assert records["apple"].cooldown == LEVEL_BASE ** (LEVEL_MAX - 1)


# ---------------------------------------------------------------------------
# Cooldown queue
# ---------------------------------------------------------------------------


# Covers: AC-SRS-002-01
def test_tick_cooldowns_decrements() -> None:
    """tick_cooldowns should decrement cooldown by 1 for all words with cooldown > 0."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], ["apple"], "An apple.", engine=engine)
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].cooldown == LEVEL_BASE**LEVEL_MIN

    tick_cooldowns(engine)
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].cooldown == LEVEL_BASE**LEVEL_MIN - 1


# Covers: AC-SRS-002-02
def test_tick_cooldowns_does_not_go_below_zero() -> None:
    """tick_cooldowns should not decrement cooldown below 0."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], ["apple"], "An apple.", engine=engine)
    for _ in range(LEVEL_BASE**LEVEL_MIN + 5):
        tick_cooldowns(engine)
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].cooldown == 0


# Covers: AC-SRS-002-02
def test_cooldown_words_not_picked() -> None:
    """Words with cooldown > 0 should not be picked."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], ["apple"], "An apple.", engine=engine)
    picked = pick_target_words(limit=3, engine=engine)
    assert picked == []


# Covers: AC-SRS-002-03
def test_graduated_words_not_picked() -> None:
    """Words with level >= LEVEL_MAX should not be picked."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], [], "An apple.", engine=engine)
    for _ in range(20):
        for _ in range(LEVEL_BASE**LEVEL_MAX):
            tick_cooldowns(engine)
        apply_feedback(["apple"], [], "An apple.", engine=engine)

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].level == LEVEL_MAX

    for _ in range(LEVEL_BASE**LEVEL_MAX):
        tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "apple" not in picked


# Covers: AC-SRS-002-04
def test_pick_target_words_returns_lowest_level() -> None:
    """pick_target_words should return words with lowest level first."""
    engine = _in_memory_engine()

    apply_feedback(
        ["alpha", "beta", "gamma", "delta"],
        ["alpha", "beta", "gamma", "delta"],
        "sentence",
        engine=engine,
    )
    for _ in range(LEVEL_BASE**LEVEL_MIN):
        tick_cooldowns(engine)

    for _ in range(3):
        apply_feedback(["alpha"], [], "sentence", engine=engine)
        for _ in range(LEVEL_BASE**LEVEL_MAX):
            tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "alpha" not in picked
    assert len(picked) == 3


# ---------------------------------------------------------------------------
# Full round simulation
# ---------------------------------------------------------------------------


# Covers: AC-SRS-003-01
def test_full_round_simulation() -> None:
    """Simulate a complete 3-round scenario from Algorithm.md."""
    engine = _in_memory_engine()

    apply_feedback(
        ["apple", "harbor", "lantern"],
        ["apple", "harbor", "lantern"],
        "initial",
        engine=engine,
    )

    for r in list_all_words(engine):
        assert r.level == LEVEL_MIN
        assert r.cooldown == LEVEL_BASE**LEVEL_MIN

    for _ in range(LEVEL_BASE**LEVEL_MIN):
        tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert len(picked) == 3

    apply_feedback(
        ["apple", "harbor", "lantern"],
        ["apple"],
        "Apple harbor lantern.",
        engine=engine,
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].level == LEVEL_MIN
    assert records["apple"].cooldown == LEVEL_BASE**LEVEL_MIN
    assert records["harbor"].level == LEVEL_MIN + 1
    assert records["harbor"].cooldown == LEVEL_BASE ** (LEVEL_MIN + 1)
    assert records["lantern"].level == LEVEL_MIN + 1

    for _ in range(LEVEL_BASE**LEVEL_MIN):
        tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "apple" in picked
    assert "harbor" not in picked
    assert "lantern" not in picked


# ---------------------------------------------------------------------------
# original_targets safety net (prevents infinite loop from lemma mismatch)
# ---------------------------------------------------------------------------


# Covers: AC-SRS-004-01
def test_original_targets_advances_unmatched_word() -> None:
    """original_targets should advance a word even when the tokenizer didn't match it."""
    engine = _in_memory_engine()

    apply_feedback(["analyze"], ["analyze"], "Analyze the data.", engine=engine)
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["analyze"].level == LEVEL_MIN

    for _ in range(LEVEL_BASE**LEVEL_MIN):
        tick_cooldowns(engine)

    apply_feedback(
        ["analysis"],
        [],
        "The analysis was thorough.",
        original_targets=["analyze"],
        engine=engine,
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["analyze"].level == LEVEL_MIN + 1


# Covers: AC-SRS-004-02
def test_original_targets_skipped_when_already_processed() -> None:
    """original_targets should not double-increment a word already in target_words."""
    engine = _in_memory_engine()

    apply_feedback(["apple"], ["apple"], "An apple.", engine=engine)
    for _ in range(LEVEL_BASE**LEVEL_MIN):
        tick_cooldowns(engine)

    apply_feedback(
        ["apple"],
        [],
        "An apple fell.",
        original_targets=["apple"],
        engine=engine,
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].level == LEVEL_MIN + 1


# Covers: AC-SRS-004-03
def test_original_targets_skipped_when_marked_unknown() -> None:
    """original_targets should not advance a word the user marked as unknown."""
    engine = _in_memory_engine()

    apply_feedback(["harbor"], [], "The harbor.", engine=engine)
    for _ in range(LEVEL_BASE ** (LEVEL_MIN + 1)):
        tick_cooldowns(engine)

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == LEVEL_MIN + 1

    apply_feedback(
        [],
        ["harbor"],
        "The harbor glowed.",
        original_targets=["harbor"],
        engine=engine,
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == LEVEL_MIN
