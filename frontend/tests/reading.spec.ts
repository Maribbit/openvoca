import { describe, expect, it } from "vitest";

import {
  tokensToPlainText,
  type ReadingSentenceToken,
} from "../src/api/reading";

describe("tokensToPlainText", () => {
  // Covers: AC-TOK-002-03
  it("joins tokens with spaces based on trailingSpace", () => {
    const tokens: ReadingSentenceToken[] = [
      { text: "A", isWord: true },
      { text: "cat", isWord: true },
      { text: "sat", isWord: true, trailingSpace: false },
      { text: ".", isWord: false, trailingSpace: false },
    ];
    expect(tokensToPlainText(tokens)).toBe("A cat sat.");
  });

  // Covers: AC-TOK-002-03
  it("handles contractions without extra spaces", () => {
    const tokens: ReadingSentenceToken[] = [
      { text: "Do", isWord: false, trailingSpace: false },
      { text: "n't", isWord: false },
      { text: "stop", isWord: true, trailingSpace: false },
      { text: ".", isWord: false, trailingSpace: false },
    ];
    expect(tokensToPlainText(tokens)).toBe("Don't stop.");
  });

  // Covers: AC-TOK-002-03
  it("handles hyphenated compound words", () => {
    const tokens: ReadingSentenceToken[] = [
      { text: "I", isWord: false },
      { text: "love", isWord: true },
      { text: "lo-fi", isWord: true },
      { text: "music", isWord: true, trailingSpace: false },
      { text: ".", isWord: false, trailingSpace: false },
    ];
    expect(tokensToPlainText(tokens)).toBe("I love lo-fi music.");
  });

  // Covers: AC-TOK-002-03
  it("returns empty string for empty token list", () => {
    expect(tokensToPlainText([])).toBe("");
  });

  // Covers: AC-TOK-002-03
  it("defaults trailingSpace to true when undefined", () => {
    const tokens: ReadingSentenceToken[] = [
      { text: "Hello", isWord: true },
      { text: "world", isWord: true },
    ];
    expect(tokensToPlainText(tokens)).toBe("Hello world");
  });

  // Covers: AC-TOK-002-03
  it("handles punctuation attached to words", () => {
    const tokens: ReadingSentenceToken[] = [
      { text: "Yes", isWord: true, trailingSpace: false },
      { text: ",", isWord: false },
      { text: "of", isWord: false },
      { text: "course", isWord: true, trailingSpace: false },
      { text: "!", isWord: false, trailingSpace: false },
    ];
    expect(tokensToPlainText(tokens)).toBe("Yes, of course!");
  });
});
