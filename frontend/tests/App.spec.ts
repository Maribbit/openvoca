import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createRouter, createMemoryHistory } from "vue-router";

import App from "../src/App.vue";
import { useSettings } from "../src/composables/useSettings";
import HomeView from "../src/views/HomeView.vue";
import SettingsView from "../src/views/SettingsView.vue";

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/", component: { template: "<div>Home</div>" } }],
  });
}

describe("App.vue update banner", () => {
  afterEach(() => {
    vi.useRealTimers();
    useSettings()._reset();
    window.localStorage.clear();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  // Covers: AC-SHELL-002-01
  it("shows banner when update is available", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/update-check") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              checked: true,
              hasUpdate: true,
              currentVersion: "0.9.0",
              latestVersion: "0.10.0",
              url: "https://github.com/example/releases/tag/v0.10.0",
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    const router = makeRouter();
    const wrapper = mount(App, { global: { plugins: [router] } });
    await router.isReady();
    await flushPromises();

    // Banner should not appear before the 3-second delay
    expect(wrapper.find("[data-testid='update-banner']").exists()).toBe(false);

    await vi.runAllTimersAsync();
    await flushPromises();

    expect(wrapper.find("[data-testid='update-banner']").exists()).toBe(true);
    expect(wrapper.text()).toContain("0.10.0");
  });

  // Covers: AC-SHELL-002-02
  it("hides banner when dismissed", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/update-check") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              checked: true,
              hasUpdate: true,
              currentVersion: "0.9.0",
              latestVersion: "0.10.0",
              url: "https://github.com/example/releases/tag/v0.10.0",
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    const router = makeRouter();
    const wrapper = mount(App, { global: { plugins: [router] } });
    await router.isReady();
    await flushPromises();
    await vi.runAllTimersAsync();
    await flushPromises();

    const banner = wrapper.find("[data-testid='update-banner']");
    expect(banner.exists()).toBe(true);

    await banner.find("button").trigger("click");
    await flushPromises();

    expect(wrapper.find("[data-testid='update-banner']").exists()).toBe(false);
  });

  // Covers: AC-SHELL-002-01
  it("does not show banner when no update is available", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/update-check") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              checked: true,
              hasUpdate: false,
              currentVersion: "0.9.0",
              latestVersion: "0.9.0",
              url: "",
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    const router = makeRouter();
    const wrapper = mount(App, { global: { plugins: [router] } });
    await router.isReady();
    await flushPromises();
    await vi.runAllTimersAsync();
    await flushPromises();

    expect(wrapper.find("[data-testid='update-banner']").exists()).toBe(false);
  });

  // Covers: AC-LOOP-001-03
  it("keeps the reading sentence when visiting another route", async () => {
    vi.useFakeTimers();
    let draftRequestCount = 0;
    const sentenceResponse = {
      sentence: "A lantern glowed by the window beside the meadow.",
      words: ["lantern", "window", "meadow"],
      tokens: [
        { text: "A", isWord: true, isTarget: false, pos: "DET" },
        { text: "lantern", isWord: true, isTarget: true, pos: "NOUN" },
        { text: "glowed", isWord: true, isTarget: false, pos: "VERB" },
        { text: "by", isWord: true, isTarget: false, pos: "ADP" },
        { text: "the", isWord: true, isTarget: false, pos: "DET" },
        { text: "window", isWord: true, isTarget: true, pos: "NOUN" },
        { text: "beside", isWord: true, isTarget: false, pos: "ADP" },
        { text: "the", isWord: true, isTarget: false, pos: "DET" },
        { text: "meadow", isWord: true, isTarget: true, pos: "NOUN" },
        { text: ".", isWord: false, isTarget: false, trailingSpace: false },
      ],
    };

    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/update-check") {
          return Promise.resolve({
            ok: true,
            json: async () => ({ hasUpdate: false }),
          });
        }
        if (url.startsWith("/api/target-words")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ words: sentenceResponse.words }),
          });
        }
        if (url.startsWith("/api/reading-sentence/next/stream")) {
          const encoder = new TextEncoder();
          const stream = new ReadableStream({
            start(controller) {
              controller.enqueue(
                encoder.encode(
                  `event: complete\ndata: ${JSON.stringify(sentenceResponse)}\n\n`,
                ),
              );
              controller.close();
            },
          });
          return Promise.resolve({ ok: true, body: stream });
        }
        if (url.startsWith("/api/feedback/draft")) {
          draftRequestCount += 1;
          return Promise.resolve({ ok: true, json: async () => [] });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: HomeView },
        {
          path: "/stats",
          name: "stats",
          component: { template: "<div>Stats</div>" },
        },
        {
          path: "/settings",
          name: "settings",
          component: { template: "<div>Settings</div>" },
        },
      ],
    });

    const wrapper = mount(App, { global: { plugins: [router] } });
    await router.isReady();
    await flushPromises();

    const generateBtn = wrapper
      .findAll("button")
      .find((button) => button.text().includes("Generate"));
    expect(generateBtn).toBeDefined();
    await generateBtn!.trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("lantern");

    await router.push("/stats");
    await flushPromises();
    expect(wrapper.text()).toContain("Stats");

    window.dispatchEvent(new KeyboardEvent("keydown", { code: "Space" }));
    await flushPromises();
    expect(draftRequestCount).toBe(0);

    await router.push("/");
    await flushPromises();
    expect(wrapper.text()).toContain("lantern");
    expect(wrapper.text()).toContain("Review Progress");
    expect(wrapper.text()).not.toContain("Generate");
  });

  // Covers: AC-SET-002-03
  it("updates cached reading copy when language changes in settings", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/update-check") {
          return Promise.resolve({
            ok: true,
            json: async () => ({ hasUpdate: false }),
          });
        }
        if (url === "/api/settings") {
          return Promise.resolve({ ok: true, json: async () => ({}) });
        }
        if (url.startsWith("/api/target-words")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ words: ["lantern", "window", "meadow"] }),
          });
        }
        if (url === "/api/provider") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              endpoint: "http://localhost:11434",
              model: "",
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "home", component: HomeView },
        {
          path: "/stats",
          name: "stats",
          component: { template: "<div>Stats</div>" },
        },
        {
          path: "/settings",
          name: "settings",
          component: SettingsView,
        },
      ],
    });

    const wrapper = mount(App, { global: { plugins: [router] } });
    await router.isReady();
    await flushPromises();

    expect(wrapper.text()).toContain("MENU");
    expect(wrapper.text()).toContain("Generate next sentence");

    await router.push("/settings");
    await flushPromises();

    const zhToggle = wrapper
      .findAll("button")
      .find((button) => button.text().includes("中文"));
    expect(zhToggle).toBeDefined();
    await zhToggle!.trigger("click");
    await flushPromises();

    await router.push("/");
    await flushPromises();

    expect(wrapper.text()).toContain("菜单");
    expect(wrapper.text()).toContain("生成下一句");
    expect(wrapper.text()).not.toContain("MENU");
  });
});
