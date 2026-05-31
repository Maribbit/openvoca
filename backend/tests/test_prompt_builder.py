import pytest

from src.services.prompt_builder import (
    build_sentence_generation_prompt,
)


# Covers: AC-GEN-001-01
def test_build_prompt_appends_marking_directive() -> None:
    """When target words are provided, the marking directive should be appended."""
    prompt = build_sentence_generation_prompt(
        "Write a sentence with lantern, meadow.", ["lantern", "meadow"]
    )

    assert "Write a sentence with lantern, meadow." in prompt
    assert "You MUST mark the target words" in prompt
    assert "*word*" in prompt


# Covers: AC-GEN-001-02
def test_build_prompt_no_marking_without_words() -> None:
    """When no target words are provided, the marking directive should NOT appear."""
    prompt = build_sentence_generation_prompt("Write any sentence.", [])

    assert "Write any sentence." in prompt
    assert "IMPORTANT" not in prompt


# Covers: AC-GEN-001-03
def test_build_prompt_requires_prompt() -> None:
    """The builder should raise ValueError if the prompt is empty."""
    with pytest.raises(ValueError, match="prompt is required"):
        build_sentence_generation_prompt("", ["word"])


# Covers: AC-GEN-001-03
def test_build_prompt_strips_whitespace() -> None:
    """Leading and trailing whitespace should be stripped."""
    prompt = build_sentence_generation_prompt("  Write a sentence.  ", ["hello"])

    assert prompt.startswith("Write a sentence.")


# Covers: AC-GEN-001-02
def test_build_prompt_ignores_blank_words() -> None:
    """Blank or whitespace-only target words should not trigger the marking directive."""
    prompt = build_sentence_generation_prompt("Write any sentence.", ["", "  "])

    assert "IMPORTANT" not in prompt


# Covers: AC-GEN-001-04
def test_build_prompt_preserves_full_prompt() -> None:
    """The user-built prompt (with scenario, difficulty, etc.) should be preserved."""
    full = (
        "Write a sentence with harbor.\n"
        "[Scenario] You are a pirate.\n"
        "[Difficulty] Use simple vocabulary."
    )
    prompt = build_sentence_generation_prompt(full, ["harbor"])

    assert "[Scenario] You are a pirate." in prompt
    assert "[Difficulty] Use simple vocabulary." in prompt
    assert "harbor" in prompt
