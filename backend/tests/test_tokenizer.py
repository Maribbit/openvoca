from src.services.tokenizer import SentenceToken, tokenize_sentence


# Covers: AC-TOK-001-01
def test_tokenize_plain_sentence() -> None:
    """It should tokenize a simple sentence with POS tags from spaCy."""
    tokens = tokenize_sentence("A cat sat.")
    assert tokens == [
        SentenceToken(text="A", is_word=False, is_target=False, pos="DET", lemma="a"),
        SentenceToken(
            text="cat",
            is_word=True,
            is_target=False,
            pos="NOUN",
            lemma="cat",
        ),
        SentenceToken(
            text="sat",
            is_word=True,
            is_target=False,
            pos="VERB",
            lemma="sit",
            trailing_space=False,
        ),
        SentenceToken(
            text=".", is_word=False, is_target=False, pos=None, trailing_space=False
        ),
    ]


# Covers: AC-TOK-001-02
def test_tokenize_with_target_words() -> None:
    """It should parse *word* as a target word and strip the asterisks."""
    tokens = tokenize_sentence("A *lantern* glowed.")

    lantern = next(t for t in tokens if t.text == "lantern")
    assert lantern.is_word is True
    assert lantern.is_target is True
    assert lantern.pos == "NOUN"

    glowed = next(t for t in tokens if t.text == "glowed")
    assert glowed.is_word is True
    assert glowed.pos == "VERB"


# Covers: AC-TOK-001-02, AC-TOK-003-02
def test_tokenize_mixed_content() -> None:
    """It should handle punctuation next to markup."""
    tokens = tokenize_sentence("They *run*, said the *fox*!")

    run_tok = next(t for t in tokens if t.text == "run")
    assert run_tok.is_target is True
    assert run_tok.pos == "VERB"

    fox_tok = next(t for t in tokens if t.text == "fox")
    assert fox_tok.is_target is True
    assert fox_tok.pos == "NOUN"

    comma = next(t for t in tokens if t.text == ",")
    assert comma.is_word is False

    # "the" should be filtered by stopwords
    the_tok = next(t for t in tokens if t.text == "the")
    assert the_tok.is_word is False


# Covers: AC-TOK-001-03
def test_target_word_bypasses_stopword_filter() -> None:
    """A markdown-marked target must stay clickable even if it is a stop word."""
    tokens = tokenize_sentence("She said *the* softly.")

    the_tok = next(t for t in tokens if t.text == "the")
    assert the_tok.is_word is True
    assert the_tok.is_target is True

    # "She" is a stopword
    she_tok = next(t for t in tokens if t.text == "She")
    assert she_tok.is_word is False


# Covers: AC-TOK-001-02
def test_tokenize_bold_markdown() -> None:
    """It should robustly handle **bold** markdown which LLMs sometimes output."""
    tokens = tokenize_sentence("A **lantern** glowed.")

    lantern = next(t for t in tokens if t.text == "lantern")
    assert lantern.is_target is True
    assert lantern.pos == "NOUN"

    # No stray asterisk tokens
    texts = [t.text for t in tokens]
    assert "*" not in texts


# Covers: AC-TOK-001-01
def test_tokenize_with_pos_for_all_words() -> None:
    """Every is_word=True token should have a non-None POS tag."""
    tokens = tokenize_sentence("The cat sat on a beautiful mat.")
    for t in tokens:
        if t.is_word:
            assert t.pos is not None, f"'{t.text}' should have POS"


# Covers: AC-TOK-001-01
def test_tokenize_distinguishes_leaves_by_context() -> None:
    """'leaves' as a noun vs verb should get different POS tags."""
    tokens_noun = tokenize_sentence("The leaves are beautiful.")
    leaves_noun = next(t for t in tokens_noun if t.text == "leaves")
    assert leaves_noun.pos == "NOUN"

    tokens_verb = tokenize_sentence("She leaves the room every morning.")
    leaves_verb = next(t for t in tokens_verb if t.text == "leaves")
    assert leaves_verb.pos == "VERB"


# Covers: AC-TOK-001-04
def test_tokenize_empty_sentence() -> None:
    """An empty string should return an empty list."""
    assert tokenize_sentence("") == []
    assert tokenize_sentence("   ") == []


# Covers: AC-TOK-002-01
def test_tokenize_contraction() -> None:
    """spaCy splits contractions; each part should be a token."""
    tokens = tokenize_sentence("Don't stop.")
    texts = [t.text for t in tokens]
    # spaCy splits "Don't" into "Do" + "n't"
    assert "Do" in texts
    assert "n't" in texts


# Covers: AC-TOK-002-01
def test_trailing_space_on_contractions() -> None:
    """'Do' in 'Don't' should have no trailing space so it renders as 'Don't'."""
    tokens = tokenize_sentence("Don't stop now.")
    do_tok = next(t for t in tokens if t.text == "Do")
    assert do_tok.trailing_space is False

    nt_tok = next(t for t in tokens if t.text == "n't")
    assert nt_tok.trailing_space is True

    stop_tok = next(t for t in tokens if t.text == "stop")
    assert stop_tok.trailing_space is True

    # Period at end typically has no trailing space
    dot_tok = next(t for t in tokens if t.text == ".")
    assert dot_tok.trailing_space is False


# Covers: AC-TOK-002-02
def test_hyphenated_target_word() -> None:
    """A *hyphenated-compound* target should become a single merged target token."""
    tokens = tokenize_sentence("It was a *well-known* fact.")
    # After merging, "well-known" should be a single token
    compound = next(t for t in tokens if t.text == "well-known")
    assert compound.is_target is True
    assert compound.is_word is True
    assert compound.lemma == "well-known"

    # No separate "well", "-", or "known" tokens
    texts = [t.text for t in tokens]
    assert "well" not in texts
    assert "known" not in texts


# Covers: AC-TOK-002-02
def test_hyphenated_non_target_word() -> None:
    """Non-target hyphenated words should also be merged into one token."""
    tokens = tokenize_sentence("I love lo-fi music.")
    compound = next(t for t in tokens if t.text == "lo-fi")
    assert compound.is_word is True
    assert compound.is_target is False
    assert compound.lemma == "lo-fi"

    texts = [t.text for t in tokens]
    assert "lo" not in texts
    assert "fi" not in texts


# Covers: AC-TOK-002-02
def test_hyphenated_chain() -> None:
    """Multi-part hyphenated words like 'state-of-the-art' are merged."""
    tokens = tokenize_sentence("It is a state-of-the-art design.")
    compound = next(t for t in tokens if t.text == "state-of-the-art")
    assert compound.is_word is True
    assert compound.lemma == "state-of-the-art"


# ---------------------------------------------------------------------------
# POS-aware stopword filtering (v0.4.2)
# ---------------------------------------------------------------------------


# Covers: AC-TOK-003-01
def test_well_noun_is_clickable() -> None:
    """'well' as a NOUN (water well) should NOT be filtered as a stopword."""
    tokens = tokenize_sentence("The well was deep.")
    well_tok = next(t for t in tokens if t.text == "well")
    assert well_tok.pos == "NOUN"
    assert well_tok.is_word is True


# Covers: AC-TOK-003-01
def test_can_noun_is_clickable() -> None:
    """'can' as a NOUN (tin can) should NOT be filtered as a stopword."""
    tokens = tokenize_sentence("She opened the can quickly.")
    can_tok = next(t for t in tokens if t.text == "can")
    assert can_tok.pos == "NOUN"
    assert can_tok.is_word is True


# Covers: AC-TOK-003-01
def test_will_noun_is_clickable() -> None:
    """'will' as a NOUN (testament) should NOT be filtered as a stopword."""
    tokens = tokenize_sentence("He left his will on the desk.")
    will_tok = next(t for t in tokens if t.text == "will")
    assert will_tok.pos == "NOUN"
    assert will_tok.is_word is True


# Covers: AC-TOK-003-01
def test_auxiliaries_always_filtered() -> None:
    """Auxiliary uses of ambiguous words should still be filtered."""
    tokens = tokenize_sentence("She can run fast.")
    can_tok = next(t for t in tokens if t.text == "can")
    assert can_tok.pos == "AUX"
    assert can_tok.is_word is False

    tokens2 = tokenize_sentence("It will rain tomorrow.")
    will_tok = next(t for t in tokens2 if t.text == "will")
    assert will_tok.pos == "AUX"
    assert will_tok.is_word is False


# Covers: AC-TOK-003-02
def test_function_pos_always_filtered() -> None:
    """Determiners, pronouns, prepositions, conjunctions should all be filtered."""
    tokens = tokenize_sentence("She and I walked to the bright store.")
    filtered = {t.text: t.is_word for t in tokens}
    # Function words
    assert filtered["She"] is False  # PRON
    assert filtered["and"] is False  # CCONJ
    assert filtered["I"] is False  # PRON


# ---------------------------------------------------------------------------
# Lemma field (v0.4.4)
# ---------------------------------------------------------------------------


# Covers: AC-TOK-004-01
def test_tokens_include_lemma() -> None:
    """Every alphabetic token should carry its lemma from spaCy."""
    tokens = tokenize_sentence("The cats were running quickly.")
    cats = next(t for t in tokens if t.text == "cats")
    assert cats.lemma == "cat"

    running = next(t for t in tokens if t.text == "running")
    assert running.lemma == "run"

    # Non-alpha tokens should have no lemma
    dot = next(t for t in tokens if t.text == ".")
    assert dot.lemma is None


# Covers: AC-TOK-004-02
def test_double_s_lemma_preserved() -> None:
    """Words ending in double-s should not be spuriously de-pluralized."""
    tokens = tokenize_sentence("sheets of fiberglass covered the roof.")
    fg = next(t for t in tokens if t.text == "fiberglass")
    assert fg.lemma == "fiberglass"

    tokens2 = tokenize_sentence("The compass pointed north.")
    cp = next(t for t in tokens2 if t.text == "compass")
    assert cp.lemma == "compass"
