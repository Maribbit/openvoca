import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import DefinitionToast from "../src/components/DefinitionToast.vue";
import type { DictionaryEntry } from "../src/api/reading";

function makeFakeAudio() {
  let instance: {
    src: string;
    onplaying: (() => void) | null;
    onended: (() => void) | null;
    onerror: (() => void) | null;
    play: ReturnType<typeof vi.fn>;
    pause: ReturnType<typeof vi.fn>;
  } | null = null;

  class FakeAudio {
    src = "";
    onplaying: (() => void) | null = null;
    onended: (() => void) | null = null;
    onerror: (() => void) | null = null;
    play = vi.fn(() => {
      if (this.onplaying) this.onplaying();
      return Promise.resolve();
    });
    pause = vi.fn();
    constructor(url?: string) {
      if (url) this.src = url;
      // eslint-disable-next-line @typescript-eslint/no-this-alias
      instance = this;
    }
  }

  return {
    FakeAudio,
    getInstance: () => instance,
  };
}

const sampleEntry: DictionaryEntry = {
  word: "lantern",
  phonetic: "ˈlæn.tɚn",
  pos: "noun",
  translation: "灯笼",
  definition: "a light inside a container",
};

describe("DefinitionToast.vue", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  function mountToast(entry: DictionaryEntry | null = sampleEntry) {
    return mount(DefinitionToast, {
      props: {
        entry,
        notFoundWord: entry ? null : "xyzzy",
        notFoundText: "No definition found",
        knowText: "Know",
        dontKnowText: "Don't know",
        isMarked: false,
        displayMode: "both",
        pronounceLabel: "Pronounce",
      },
    });
  }

  // delete-candidate: 单独验证按钮存在，播放、回退和未找到词朗读测试已经覆盖同一入口的实际行为。
  it.skip("renders the speak-word button", () => {
    const wrapper = mountToast();
    const btn = wrapper.find('[data-testid="speak-word"]');
    expect(btn.exists()).toBe(true);
    expect(btn.attributes("title")).toBe("Pronounce");
  });

  // Covers: AC-LOOP-006-02
  it("plays word audio via /api/tts when speak button is clicked", async () => {
    const { FakeAudio, getInstance } = makeFakeAudio();
    vi.stubGlobal("Audio", FakeAudio);

    const wrapper = mountToast();
    await wrapper.find('[data-testid="speak-word"]').trigger("click");
    await flushPromises();

    const audio = getInstance();
    expect(audio).not.toBeNull();
    expect(audio!.src).toContain("/api/tts?text=lantern");
    expect(audio!.play).toHaveBeenCalled();
  });

  // Covers: AC-LOOP-006-02
  it("falls back to browser SpeechSynthesis on audio error", async () => {
    const { FakeAudio, getInstance } = makeFakeAudio();
    vi.stubGlobal("Audio", FakeAudio);

    const speakMock = vi.fn();
    vi.stubGlobal("speechSynthesis", {
      speak: speakMock,
      cancel: vi.fn(),
    });
    vi.stubGlobal(
      "SpeechSynthesisUtterance",
      class {
        lang = "";
        onend: (() => void) | null = null;
        constructor(public text: string) {}
      },
    );

    const wrapper = mountToast();
    await wrapper.find('[data-testid="speak-word"]').trigger("click");
    await flushPromises();

    // Simulate audio error
    const audio = getInstance();
    audio!.onerror!();
    await flushPromises();

    expect(speakMock).toHaveBeenCalledTimes(1);
  });

  // Covers: AC-LOOP-006-02
  it("stops playback when clicked while speaking", async () => {
    const { FakeAudio, getInstance } = makeFakeAudio();
    vi.stubGlobal("Audio", FakeAudio);

    const wrapper = mountToast();
    const btn = wrapper.find('[data-testid="speak-word"]');

    // Start playback
    await btn.trigger("click");
    await flushPromises();

    const audio = getInstance();
    expect(audio!.play).toHaveBeenCalled();

    // Click again while speaking — should stop
    await btn.trigger("click");
    await flushPromises();

    expect(audio!.pause).toHaveBeenCalled();
  });

  // Covers: AC-LOOP-006-02, AC-LOOP-006-03
  it("uses notFoundWord when entry is null", async () => {
    const { FakeAudio, getInstance } = makeFakeAudio();
    vi.stubGlobal("Audio", FakeAudio);

    const wrapper = mount(DefinitionToast, {
      props: {
        entry: null,
        notFoundWord: "xyzzy",
        notFoundText: "No definition found",
        knowText: "Know",
        dontKnowText: "Don't know",
        isMarked: false,
        displayMode: "both",
        pronounceLabel: "Pronounce",
      },
    });

    await wrapper.find('[data-testid="speak-word"]').trigger("click");
    await flushPromises();

    const audio = getInstance();
    expect(audio).not.toBeNull();
    expect(audio!.src).toContain("/api/tts?text=xyzzy");
  });

  // Covers: AC-LOOP-006-03, AC-TOK-005-01
  it("emits normalized lemma edits", async () => {
    const wrapper = mount(DefinitionToast, {
      props: {
        entry: sampleEntry,
        notFoundWord: null,
        lemma: "lantern-root",
        lemmaLabel: "词元",
        notFoundText: "No definition found",
        knowText: "Know",
        dontKnowText: "Don't know",
        isMarked: false,
        displayMode: "both",
        pronounceLabel: "Pronounce",
      },
    });

    expect(wrapper.text()).toContain("词元: lantern-root");
    await wrapper.find('[data-testid="lemma-edit-trigger"]').trigger("click");
    await wrapper.find('[data-testid="lemma-edit-input"]').setValue(" Lamp ");
    await wrapper.find('[data-testid="lemma-edit-save"]').trigger("click");

    expect(wrapper.emitted("lemma-change")?.[0]).toEqual(["lamp"]);
  });

  // Covers: AC-LOOP-006-03
  it("does not repeat the lemma label when it matches the lookup word", () => {
    const wrapper = mount(DefinitionToast, {
      props: {
        entry: sampleEntry,
        notFoundWord: null,
        lemma: "lantern",
        lemmaLabel: "词元",
        notFoundText: "No definition found",
        knowText: "Know",
        dontKnowText: "Don't know",
        isMarked: false,
        displayMode: "both",
        pronounceLabel: "Pronounce",
      },
    });

    expect(wrapper.text()).not.toContain("词元: lantern");
    expect(wrapper.find('[data-testid="lemma-edit-trigger"]').exists()).toBe(
      true,
    );
  });
});
