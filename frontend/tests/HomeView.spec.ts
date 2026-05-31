import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createRouter, createMemoryHistory } from "vue-router";

import HomeView from "../src/views/HomeView.vue";
import SettingsView from "../src/views/SettingsView.vue";
import { useSettings } from "../src/composables/useSettings";

const tokenizedSentence = {
  sentence: "A lantern glowed by the window beside the meadow.",
  words: ["lantern", "meadow", "window"],
  tokens: [
    { text: "A", isWord: true, isTarget: false, pos: "DET" },
    { text: "lantern", isWord: true, isTarget: true, pos: "NOUN" },
    { text: "glowed", isWord: true, isTarget: false, pos: "VERB" },
    { text: "by", isWord: true, isTarget: false, pos: "ADP" },
    { text: "the", isWord: true, isTarget: false, pos: "DET" },
    { text: "window", isWord: true, isTarget: true, pos: "NOUN" },
    { text: "beside", isWord: true, isTarget: false, pos: "ADP" },
    { text: "the", isWord: true, isTarget: false, pos: "DET" },
    {
      text: "meadow",
      isWord: true,
      isTarget: true,
      pos: "NOUN",
      trailingSpace: false,
    },
    { text: ".", isWord: false, isTarget: false, trailingSpace: false },
  ],
};

const tokenizedRiddle = {
  mode: "riddle",
  sentence:
    "coastal signal\nI guide ships through dark water.\na harbor lantern",
  words: ["harbor", "lantern"],
  tokens: [
    { text: "coastal", isWord: true, isTarget: false, pos: "ADJ" },
    {
      text: "signal",
      isWord: true,
      isTarget: false,
      pos: "NOUN",
      trailingSpace: false,
    },
    { text: "I", isWord: true, isTarget: false, pos: "PRON" },
    { text: "guide", isWord: true, isTarget: false, pos: "VERB" },
    { text: "ships", isWord: true, isTarget: false, pos: "NOUN" },
    { text: "through", isWord: true, isTarget: false, pos: "ADP" },
    { text: "dark", isWord: true, isTarget: false, pos: "ADJ" },
    { text: "water", isWord: true, isTarget: false, pos: "NOUN" },
    { text: ".", isWord: false, isTarget: false, trailingSpace: false },
    { text: "a", isWord: true, isTarget: false, pos: "DET" },
    { text: "harbor", isWord: true, isTarget: true, pos: "NOUN" },
    {
      text: "lantern",
      isWord: true,
      isTarget: true,
      pos: "NOUN",
      trailingSpace: false,
    },
  ],
  riddle: {
    clue: "coastal signal",
    question: "I guide ships through dark water.",
    answer: "a harbor lantern",
    clueTokens: [
      { text: "coastal", isWord: true, isTarget: false, pos: "ADJ" },
      {
        text: "signal",
        isWord: true,
        isTarget: false,
        pos: "NOUN",
        trailingSpace: false,
      },
    ],
    questionTokens: [
      { text: "I", isWord: true, isTarget: false, pos: "PRON" },
      { text: "guide", isWord: true, isTarget: false, pos: "VERB" },
      { text: "ships", isWord: true, isTarget: false, pos: "NOUN" },
      { text: "through", isWord: true, isTarget: false, pos: "ADP" },
      { text: "dark", isWord: true, isTarget: false, pos: "ADJ" },
      { text: "water", isWord: true, isTarget: false, pos: "NOUN" },
      { text: ".", isWord: false, isTarget: false, trailingSpace: false },
    ],
    answerTokens: [
      { text: "a", isWord: true, isTarget: false, pos: "DET" },
      { text: "harbor", isWord: true, isTarget: true, pos: "NOUN" },
      {
        text: "lantern",
        isWord: true,
        isTarget: true,
        pos: "NOUN",
        trailingSpace: false,
      },
    ],
  },
};

describe("HomeView.vue", () => {
  afterEach(() => {
    vi.useRealTimers();
    useSettings()._reset();
    window.localStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  const targetWordsResponse = { words: ["lantern", "meadow", "window"] };

  /** Create a fetch mock that routes by URL. */
  function mockFetch() {
    return vi.fn((url: string, init?: RequestInit) => {
      if (typeof url === "string" && url.startsWith("/api/target-words")) {
        return Promise.resolve({
          ok: true,
          json: async () => targetWordsResponse,
        });
      }
      if (
        typeof url === "string" &&
        url.startsWith("/api/reading-sentence/next/stream")
      ) {
        const body = JSON.parse(String(init?.body ?? "{}")) as {
          mode?: string;
        };
        const responseData =
          body.mode === "riddle" ? tokenizedRiddle : tokenizedSentence;
        return Promise.resolve({
          ok: true,
          body: makeSseStream(responseData),
        });
      }
      if (
        typeof url === "string" &&
        url.startsWith("/api/reading-sentence/next")
      ) {
        return Promise.resolve({
          ok: true,
          json: async () => tokenizedSentence,
        });
      }
      if (typeof url === "string" && url.startsWith("/api/tts")) {
        return Promise.resolve({
          ok: true,
          blob: async () =>
            new Blob([new Uint8Array([0xff, 0xfb])], { type: "audio/mpeg" }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      });
    });
  }

  /** Build a ReadableStream that emits SSE progress + complete events. */
  function makeSseStream(data: typeof tokenizedSentence): ReadableStream;
  function makeSseStream(data: typeof tokenizedRiddle): ReadableStream;
  function makeSseStream(
    data: typeof tokenizedSentence | typeof tokenizedRiddle,
  ): ReadableStream {
    const encoder = new TextEncoder();
    const wordCount = data.sentence.split(/\s+/).length;
    const lines = [
      `event: progress\ndata: ${JSON.stringify({ wordCount })}\n\n`,
      `event: complete\ndata: ${JSON.stringify(data)}\n\n`,
    ];
    return new ReadableStream({
      start(controller) {
        for (const line of lines) {
          controller.enqueue(encoder.encode(line));
        }
        controller.close();
      },
    });
  }

  function makeErrorSseStream(detail: string): ReadableStream {
    const encoder = new TextEncoder();
    const lines = [
      `event: progress\ndata: ${JSON.stringify({ wordCount: 4 })}\n\n`,
      `event: error\ndata: ${JSON.stringify({ detail })}\n\n`,
    ];
    return new ReadableStream({
      start(controller) {
        for (const line of lines) {
          controller.enqueue(encoder.encode(line));
        }
        controller.close();
      },
    });
  }

  function makeRouter() {
    return createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", component: HomeView },
        { path: "/stats", component: { template: "<div>Stats</div>" } },
        { path: "/settings", component: SettingsView },
      ],
    });
  }

  /** Click the composer "Generate" button to transition from composer to reading view. */
  async function generateFromComposer(
    wrapper: ReturnType<typeof mount>,
  ): Promise<void> {
    const generateBtn = wrapper
      .findAll("button")
      .find(
        (button) =>
          button.text().includes("Generate") || button.text().includes("生成"),
      );
    expect(generateBtn).toBeDefined();
    await generateBtn!.trigger("click");
    await flushPromises();
  }

  // Covers: AC-LOOP-001-01, AC-LOOP-001-02, AC-LOOP-006-01
  it("renders the generated reading sentence", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal("fetch", mockFetch());

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Composer is shown first — click Generate to load the sentence
    await generateFromComposer(wrapper);

    // Verify marked words have the correct class
    const markedWord = wrapper
      .findAll("button")
      .find((btn) => btn.text() === "lantern")
      ?.find("span");
    expect(markedWord?.classes()).toContain("border-dotted");
    expect(markedWord?.classes()).toContain("border-b");

    // Verify non-marked words do not have the class
    const regularWord = wrapper
      .findAll("button")
      .find((btn) => btn.text() === "glowed")
      ?.find("span");
    expect(regularWord?.classes()).not.toContain("border-dotted");

    const wordButtons = wrapper
      .findAll("button")
      .map((button) => button.text())
      .filter((text) =>
        tokenizedSentence.tokens.some(
          (token) => token.isWord && token.text === text,
        ),
      );

    expect(wrapper.text()).toContain("MENU");
    expect(wrapper.text()).toContain("Reading");
    expect(wordButtons).toEqual([
      "A",
      "lantern",
      "glowed",
      "by",
      "the",
      "window",
      "beside",
      "the",
      "meadow",
    ]);
    expect(wrapper.text()).toContain("meadow.");
    expect(wrapper.text()).toContain("Review Progress");
  });

  // Covers: AC-LOOP-004-01
  it("reveals riddle answers before progress review", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    const fetchMock = mockFetch();
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    const riddleModeButton = wrapper
      .findAll("button")
      .find((button) => button.text() === "Riddle");
    expect(riddleModeButton).toBeDefined();
    await riddleModeButton!.trigger("click");

    await generateFromComposer(wrapper);

    expect(wrapper.text()).toContain("Clue");
    expect(wrapper.text()).toContain("coastal signal");
    expect(
      wrapper.findAll("button").some((button) => button.text() === "coastal"),
    ).toBe(true);
    expect(wrapper.text()).toContain("I guide ships through dark water.");
    expect(wrapper.text()).not.toContain("a harbor lantern");
    expect(wrapper.text()).toContain("Reveal Answer");
    expect(wrapper.text()).not.toContain("Review Progress");

    const streamRequest = fetchMock.mock.calls.find(([url]) =>
      String(url).startsWith("/api/reading-sentence/next/stream"),
    );
    expect(JSON.parse(String(streamRequest?.[1]?.body))).toMatchObject({
      mode: "riddle",
    });

    const revealButton = wrapper
      .findAll("button")
      .find((button) => button.text().includes("Reveal Answer"));
    expect(revealButton).toBeDefined();
    await revealButton!.trigger("click");

    expect(wrapper.text()).toContain("Answer");
    expect(wrapper.text()).toContain("a harbor lantern");
    expect(wrapper.text()).toContain("Review Progress");
  });

  // Covers: AC-LOOP-004-02
  it("builds concise English riddle prompts from a scene and custom details", async () => {
    window.localStorage.setItem(
      "openvoca.settings.cache",
      JSON.stringify({ interface: { locale: "zh" } }),
    );

    const fetchMock = mockFetch();
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    const riddleModeButton = wrapper
      .findAll("button")
      .find((button) => button.text() === "猜谜");
    expect(riddleModeButton).toBeDefined();
    await riddleModeButton!.trigger("click");

    expect(wrapper.text()).toContain("商务");
    expect(wrapper.text()).toContain("自定义");
    expect(wrapper.text()).not.toContain("方向细化");

    const businessButton = wrapper
      .findAll("button")
      .find((button) => button.text().includes("商务"));
    expect(businessButton).toBeDefined();
    await businessButton!.trigger("click");

    const addDetailsButton = wrapper
      .findAll("button")
      .find((button) => button.text().includes("添加细节"));
    expect(addDetailsButton).toBeDefined();
    await addDetailsButton!.trigger("click");

    const detailInput = wrapper.find("textarea");
    expect(detailInput.exists()).toBe(true);
    await detailInput.setValue("SaaS renewal negotiation");

    await generateFromComposer(wrapper);

    const streamRequest = fetchMock.mock.calls.find(([url]) =>
      String(url).startsWith("/api/reading-sentence/next/stream"),
    );
    const body = JSON.parse(String(streamRequest?.[1]?.body)) as {
      mode?: string;
      prompt?: string;
    };
    expect(body.mode).toBe("riddle");
    expect(body.prompt).toContain("All output must be English");
    expect(body.prompt).toContain("question");
    expect(body.prompt).toContain(
      "Scene: Use a workplace or business situation",
    );
    expect(body.prompt).toContain("SaaS renewal negotiation");
    expect(body.prompt).not.toContain("方向细化");
    expect(body.prompt).not.toContain("商务英语");
    expect(body.prompt).not.toContain("Practice direction");
    expect(body.prompt).not.toContain("[Focus]");
  });

  // Covers: AC-LOOP-004-03, AC-LOOP-005-02
  it("shows stream generation error details in the composer", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.startsWith("/api/target-words")) {
          return Promise.resolve({
            ok: true,
            json: async () => targetWordsResponse,
          });
        }
        if (url.startsWith("/api/reading-sentence/next/stream")) {
          return Promise.resolve({
            ok: true,
            body: makeErrorSseStream("Riddle response must be valid JSON."),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({}),
        });
      }),
    );

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    await generateFromComposer(wrapper);

    expect(wrapper.text()).toContain("Riddle response must be valid JSON.");
    expect(wrapper.text()).not.toContain("Unable to reach the model");
  });

  // Covers: AC-LOOP-003-01, AC-LOOP-003-02
  it("opens progress summary on continue and advances on submit", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    let overrideFetchMock = vi
      .fn()
      .mockImplementation((url: string, init?: RequestInit) => {
        // Mock streams and feedback same as mockFetch
        if (url.startsWith("/api/reading-sentence/next/stream")) {
          const mockResponse = {
            sentence: "Cats are great.",
            tokens: [
              {
                word: "Cats",
                isTarget: true,
                isWord: true,
                lemma: "cat",
                pos: "NOUN",
              },
            ],
            words: ["cat"],
          };
          const stream = new ReadableStream({
            start(controller) {
              controller.enqueue(
                new TextEncoder().encode(
                  `data: ${JSON.stringify(mockResponse)}\n\n`,
                ),
              );
              controller.close();
            },
          });
          return Promise.resolve(
            new Response(stream, {
              headers: { "Content-Type": "text/event-stream" },
            }),
          );
        }
        if (url.startsWith("/api/feedback/draft")) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve([
                {
                  lemma: "lantern",
                  old_level: 1,
                  new_level: 2,
                  is_new: false,
                },
              ]),
          });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      });
    vi.stubGlobal("fetch", overrideFetchMock);

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Generate from composer to enter reading view
    await generateFromComposer(wrapper);

    const initialCallCount = overrideFetchMock.mock.calls.length;

    // Set proper tokens to bypass early return
    (wrapper.vm as any).tokens = [
      {
        text: "Cats",
        word: "Cats",
        isTarget: true,
        isWord: true,
        lemma: "cat",
        pos: "NOUN",
      },
    ];
    (wrapper.vm as any).currentResponse = { words: ["cat"] };

    await (wrapper.vm as any).openProgressSummary();
    await flushPromises();

    // Now modal should be open (so it will fetch vocabulary)
    expect((wrapper.vm as any).isSummaryModalOpen).toBe(true);

    // Call internal submit
    (wrapper.vm as any).goToNextSentence();
    await flushPromises();

    expect(wrapper.text()).toContain("Generate");
  });

  // Covers: AC-SET-002-03
  it("switches UI language to Chinese and persists locale", async () => {
    vi.stubGlobal("fetch", mockFetch());

    const router = makeRouter();
    const wrapper = mount(
      { template: "<router-view />" },
      { global: { plugins: [router] } },
    );
    await router.push("/settings");
    await flushPromises();

    const zhToggle = wrapper
      .findAll("button")
      .find((button) => button.text().includes("中文"));

    expect(zhToggle).toBeDefined();
    await zhToggle!.trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("设置");
    expect(wrapper.text()).toContain("界面");
    const cache = JSON.parse(
      window.localStorage.getItem("openvoca.settings.cache") ?? "{}",
    );
    expect(cache?.interface?.locale).toBe("zh");
  });

  // Covers: AC-SET-003-01
  it("applies and persists dark reading theme from inline settings", async () => {
    vi.stubGlobal("fetch", mockFetch());

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Generate from composer to access reading view with settings trigger
    await generateFromComposer(wrapper);

    const settingsTrigger = wrapper.find(
      '[data-testid="reading-settings-trigger"]',
    );

    expect(settingsTrigger.exists()).toBe(true);
    await settingsTrigger.trigger("click");
    await flushPromises();

    const darkThemeButton = wrapper.find('button[title="Dark"]');

    expect(darkThemeButton.exists()).toBe(true);
    await darkThemeButton.trigger("click");
    await flushPromises();

    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");

    const cache = window.localStorage.getItem("openvoca.settings.cache");
    expect(cache).not.toBeNull();
    const parsed = JSON.parse(cache!) as Record<string, Record<string, string>>;
    expect(parsed.reading?.theme).toBe("dark");
  });

  // Covers: AC-SET-003-02
  it("closes inline settings when clicking the blank overlay", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    vi.stubGlobal("fetch", mockFetch());

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Generate from composer to access reading view
    await generateFromComposer(wrapper);

    await wrapper
      .find('[data-testid="reading-settings-trigger"]')
      .trigger("click");
    await flushPromises();

    expect(
      wrapper.find('[data-testid="reading-settings-overlay"]').exists(),
    ).toBe(true);

    await wrapper
      .find('[data-testid="reading-settings-overlay"]')
      .trigger("click");
    await flushPromises();

    expect(
      wrapper.find('[data-testid="reading-settings-overlay"]').exists(),
    ).toBe(false);
  });

  // Covers: AC-LOOP-005-01
  it("shows streaming word count progress during generation", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    const encoder = new TextEncoder();
    let enqueueRef: ReadableStreamDefaultController<Uint8Array> | null = null;

    const fetchMock = vi.fn((url: string) => {
      if (typeof url === "string" && url.startsWith("/api/target-words")) {
        return Promise.resolve({
          ok: true,
          json: async () => targetWordsResponse,
        });
      }
      if (
        typeof url === "string" &&
        url.startsWith("/api/reading-sentence/next/stream")
      ) {
        const stream = new ReadableStream<Uint8Array>({
          start(controller) {
            enqueueRef = controller;
          },
        });
        return Promise.resolve({ ok: true, body: stream });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();

    // Trigger generate from composer
    await generateFromComposer(wrapper);

    // Send a progress event
    enqueueRef!.enqueue(
      encoder.encode(
        `event: progress\ndata: ${JSON.stringify({ wordCount: 5 })}\n\n`,
      ),
    );
    await flushPromises();

    const progress = wrapper.find('[data-testid="loading-progress"]');
    expect(progress.exists()).toBe(true);
    expect(progress.text()).toContain("5");

    // Send complete event
    enqueueRef!.enqueue(
      encoder.encode(
        `event: complete\ndata: ${JSON.stringify(tokenizedSentence)}\n\n`,
      ),
    );
    enqueueRef!.close();
    await flushPromises();

    // Sentence should now be displayed
    expect(wrapper.text()).toContain("lantern");
    expect(wrapper.find('[data-testid="loading-progress"]').exists()).toBe(
      false,
    );
  });

  // Covers: AC-LOOP-006-02
  it("plays TTS audio from backend when read aloud is clicked", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    let playWasCalled = false;
    let audioSrc = "";

    class FakeAudio {
      src = "";
      onplaying: (() => void) | null = null;
      onended: (() => void) | null = null;
      onerror: (() => void) | null = null;
      play = vi.fn(() => {
        audioSrc = this.src;
        playWasCalled = true;
        // Simulate the playing event
        if (this.onplaying) this.onplaying();
        return Promise.resolve();
      });
      pause = vi.fn();
      constructor(url?: string) {
        if (url) this.src = url;
      }
    }
    vi.stubGlobal("Audio", FakeAudio);

    vi.stubGlobal("fetch", mockFetch());

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();
    await generateFromComposer(wrapper);

    // Find and click the read-aloud button
    const readAloudBtn = wrapper
      .findAll("button")
      .find((b) => b.attributes("title") === "Read aloud");
    expect(readAloudBtn).toBeDefined();
    await readAloudBtn!.trigger("click");
    await flushPromises();

    expect(playWasCalled).toBe(true);
    expect(audioSrc).toContain("/api/tts?text=");
  });

  // Covers: AC-LOOP-003-03, AC-TOK-005-02
  it("uses corrected lemmas for draft and submit", async () => {
    window.localStorage.setItem("openvoca.ui.locale", "en");

    const draftBodies: unknown[] = [];
    const submitBodies: unknown[] = [];

    const correctionSentence = {
      sentence: "The analyses were careful.",
      words: ["analysis"],
      tokens: [
        {
          text: "analyses",
          isWord: true,
          isTarget: true,
          lemma: "analysis",
          pos: "NOUN",
        },
      ],
    };

    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url.startsWith("/api/target-words")) {
        return Promise.resolve({
          ok: true,
          json: async () => targetWordsResponse,
        });
      }
      if (url.startsWith("/api/reading-sentence/next/stream")) {
        return Promise.resolve({
          ok: true,
          body: makeSseStream(correctionSentence),
        });
      }
      if (url.startsWith("/api/feedback/draft")) {
        const body = JSON.parse(String(init?.body));
        draftBodies.push(body);
        const lemma = body.target_words[0] ?? body.original_targets[0];
        return Promise.resolve({
          ok: true,
          json: async () => [
            { lemma, old_level: 1, new_level: 2, is_new: false },
          ],
        });
      }
      if (url.startsWith("/api/feedback")) {
        submitBodies.push(JSON.parse(String(init?.body)));
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(HomeView, {
      global: { plugins: [makeRouter()] },
    });
    await flushPromises();
    await generateFromComposer(wrapper);

    await (wrapper.vm as any).openProgressSummary();
    await flushPromises();

    await wrapper.find('[data-testid="lemma-edit-trigger"]').trigger("click");
    await wrapper.find('[data-testid="lemma-edit-input"]').setValue("analyze");
    await wrapper.find('[data-testid="lemma-edit-save"]').trigger("click");
    await flushPromises();

    await (wrapper.vm as any).goToNextSentence();
    await flushPromises();

    expect(draftBodies).toHaveLength(2);
    expect(draftBodies[0]).toMatchObject({
      target_words: ["analysis"],
      original_targets: ["analysis"],
    });
    expect(draftBodies[1]).toMatchObject({
      target_words: ["analyze"],
      original_targets: ["analyze"],
    });
    expect(submitBodies[0]).toMatchObject({
      targetWords: ["analyze"],
      originalTargets: ["analyze"],
    });
  });
});
