import { describe, expect, it } from "vitest";

import {
  isValidLemmaInput,
  normalizeLemmaInput,
  useLemmaOverrides,
} from "../src/composables/useLemmaOverrides";
import type { ReadingSentenceToken } from "../src/api/reading";

const token: ReadingSentenceToken = {
  text: "analyses",
  lemma: "analysis",
  isWord: true,
  isTarget: true,
};

describe("useLemmaOverrides", () => {
  // Covers: AC-TOK-005-01
  it("normalizes and validates lemma input", () => {
    expect(normalizeLemmaInput("  Running\u2019s ")).toBe("running's");
    expect(isValidLemmaInput("well-known")).toBe(true);
    expect(isValidLemmaInput("state-of-the-art")).toBe(true);
    expect(isValidLemmaInput("can't")).toBe(true);
    expect(isValidLemmaInput("well-")).toBe(false);
    expect(isValidLemmaInput("two words")).toBe(false);
    expect(isValidLemmaInput("123")).toBe(false);
  });

  // Covers: AC-TOK-005-02
  it("resolves current-sentence overrides without persistence", () => {
    const overrides = useLemmaOverrides();

    expect(overrides.effectiveLemma(token)).toBe("analysis");
    expect(overrides.setOverride("analysis", "analyze", "dictionary")).toBe(
      true,
    );
    expect(overrides.effectiveLemma(token)).toBe("analyze");
    expect(overrides.effectiveLemma("analysis")).toBe("analyze");

    overrides.clearOverrides();
    expect(overrides.effectiveLemma(token)).toBe("analysis");
  });

  // Covers: AC-TOK-005-02, AC-LOOP-003-03
  it("supports chained row edits from the progress modal", () => {
    const overrides = useLemmaOverrides();

    overrides.setOverride("analysis", "analyze", "dictionary");
    overrides.setOverride("analyze", "analyse", "progress");

    expect(overrides.effectiveLemma(token)).toBe("analyse");
    expect(overrides.uniqueEffectiveLemmas(["analysis", "analyze"])).toEqual([
      "analyse",
    ]);
  });
});
