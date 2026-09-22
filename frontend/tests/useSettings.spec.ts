import { describe, it, expect, beforeEach, vi } from "vitest";
import { useSettings } from "../src/composables/useSettings";
import * as settingsApi from "../src/api/settings";

// Stub the settings API to avoid real HTTP calls
vi.mock("../src/api/settings", () => ({
  fetchAllSettings: vi.fn().mockResolvedValue({}),
  putNamespace: vi.fn().mockResolvedValue(undefined),
  deleteAllSettings: vi.fn().mockResolvedValue(0),
  setProvider: vi.fn().mockResolvedValue({}),
}));

const mocks = {
  setProvider: vi.mocked(settingsApi.setProvider),
  putNamespace: vi.mocked(settingsApi.putNamespace),
};

describe("useSettings – exportAll / importAll", () => {
  let settings: ReturnType<typeof useSettings>;

  beforeEach(() => {
    // Reset both the store and the recorded calls: without this, a test that
    // reads mock.calls[0] would read a previous test's call.
    vi.clearAllMocks();
    settings = useSettings();
    settings._reset();
  });

  // Covers: AC-SET-002-01
  it("exportAll excludes provider.apiKey", () => {
    settings.set("provider", {
      endpoint: "http://localhost:11434",
      model: "llama3",
      apiKey: "sk-secret-key-12345",
    });
    settings.set("interface", { locale: "en" });

    const exported = settings.exportAll();

    expect(exported.provider).toBeDefined();
    expect(exported.provider!.endpoint).toBe("http://localhost:11434");
    expect(exported.provider!.model).toBe("llama3");
    expect(exported.provider!.apiKey).toBeUndefined();
    expect(exported.interface!.locale).toBe("en");
  });

  // Covers: AC-SET-002-01
  it("exportAll omits namespace when only apiKey present", () => {
    settings.set("provider", { apiKey: "sk-only-key" });

    const exported = settings.exportAll();

    expect(exported.provider).toBeUndefined();
  });

  // Covers: AC-SET-002-02
  it("importAll merges settings and skips apiKey", async () => {
    settings.set("interface", { locale: "en", colorTheme: "default" });

    await settings.importAll({
      interface: { locale: "zh", colorTheme: "sepia" },
      provider: {
        endpoint: "http://example.com",
        apiKey: "sk-should-be-ignored",
      },
    });

    const store = settings.store;
    expect(store.interface?.locale).toBe("zh");
    expect(store.interface?.colorTheme).toBe("sepia");
    expect(store.provider?.endpoint).toBe("http://example.com");
    expect(store.provider?.apiKey).toBeUndefined();
  });

  // Covers: AC-SET-002-02
  it("importAll skips non-string values", async () => {
    await settings.importAll({
      reading: { theme: "dark", broken: 123 as unknown as string },
    });

    const store = settings.store;
    expect(store.reading?.theme).toBe("dark");
    expect(store.reading?.broken).toBeUndefined();
  });

  // Covers: AC-SET-002-02
  it("importAll skips non-object namespaces", async () => {
    await settings.importAll({
      bad: "not-an-object" as unknown as Record<string, string>,
      array: ["a", "b"] as unknown as Record<string, string>,
      reading: { theme: "light" },
    });

    expect(settings.store.bad).toBeUndefined();
    expect(settings.store.array).toBeUndefined();
    expect(settings.store.reading?.theme).toBe("light");
  });

  // Covers: AC-SET-002-02
  it("importAll handles empty object without error", async () => {
    settings.set("interface", { locale: "en" });
    await settings.importAll({});

    expect(settings.store.interface?.locale).toBe("en");
  });

  // Covers: AC-SET-002-01
  it("exportAll carries provider.headers", () => {
    settings.set("provider", {
      endpoint: "https://opencode.ai/zen/go",
      model: "deepseek-v4-flash",
      headers: '{"x-opencode-session":"session-value"}',
    });

    const exported = settings.exportAll();

    // A backup that omits part of the configuration is worse than none: it
    // gives the confidence of a backup without being one.
    expect(exported.provider).toBeDefined();
    expect(exported.provider!.endpoint).toBe("https://opencode.ai/zen/go");
    expect(exported.provider!.model).toBe("deepseek-v4-flash");
    expect(exported.provider!.headers).toBe(
      '{"x-opencode-session":"session-value"}',
    );
  });

  // Covers: AC-SET-005-09
  it("localStorage cache still excludes provider.headers and apiKey", () => {
    settings.set("provider", {
      endpoint: "https://opencode.ai/zen/go",
      apiKey: "sk-secret-key",
      headers: '{"x-opencode-session":"secret-session"}',
    });

    const raw = window.localStorage.getItem("openvoca.settings.cache") ?? "";

    // The endpoint proves the cache was actually written.
    expect(raw).toContain("opencode.ai");
    // The cache is written on every change without being asked, and
    // localStorage is readable by any script on the origin. A header value can
    // be a credential -- that is partly what custom headers are for -- so it
    // does not belong in an automatic copy, however welcome it is in an
    // explicit backup.
    expect(raw).not.toContain("secret-session");
    expect(raw).not.toContain("sk-secret-key");
  });

  // Covers: AC-SET-002-02
  it("importAll writes provider config through the provider API", async () => {
    await settings.importAll({
      provider: {
        endpoint: "https://example.com/v1",
        model: "imported-model",
        headers: '{"x-opencode-session":"imported-session"}',
        bodyFields: '{"reasoning_effort":"low"}',
      },
    });

    // The generic settings write refuses this namespace, so a plain
    // putNamespace would be rejected and silently swallowed -- which is how
    // provider settings came to be exported but never restored.
    expect(mocks.setProvider).toHaveBeenCalled();
    const [config] = mocks.setProvider.mock.calls[0]!;
    expect(config.endpoint).toBe("https://example.com/v1");
    expect(config.model).toBe("imported-model");
    expect(config.headers).toEqual({ "x-opencode-session": "imported-session" });
    expect(config.bodyFields).toEqual({ reasoning_effort: "low" });
  });

  // Covers: AC-SET-002-02
  it("importAll omits provider fields the file did not carry", async () => {
    await settings.importAll({
      provider: { endpoint: "https://example.com/v1" },
    });

    const [config] = mocks.setProvider.mock.calls[0]!;
    // Absent means "leave it at the server default", not "set it to nothing":
    // an export from an older version has no bodyFields, and sending {} would
    // silently clear whatever is configured.
    expect(config).not.toHaveProperty("bodyFields");
    expect(config).not.toHaveProperty("model");
  });

  // Covers: AC-SET-002-02
  it("importAll never sends the api key", async () => {
    await settings.importAll({
      provider: { endpoint: "https://example.com", apiKey: "sk-smuggled-in" },
    });

    const [config] = mocks.setProvider.mock.calls[0]!;
    // The key has its own endpoint and the client is never given the value, so
    // a settings file cannot carry one.
    expect(config).not.toHaveProperty("apiKey");
    expect(JSON.stringify(config)).not.toContain("sk-smuggled-in");
  });

  // Covers: AC-SET-002-02
  it("importAll tolerates corrupt provider JSON", async () => {
    await settings.importAll({
      provider: {
        endpoint: "https://example.com",
        headers: "not json at all",
        bodyFields: '["an","array"]',
      },
    });

    const [config] = mocks.setProvider.mock.calls[0]!;
    expect(config.endpoint).toBe("https://example.com");
    // Both are dropped rather than sent as garbage the server would reject.
    expect(config).not.toHaveProperty("headers");
    expect(config).not.toHaveProperty("bodyFields");
  });

  // Covers: AC-SET-002-02
  it("importAll drops non-string header values", async () => {
    await settings.importAll({
      provider: {
        endpoint: "https://example.com",
        headers: '{"x-good":"value","x-bad":123}',
      },
    });

    const [config] = mocks.setProvider.mock.calls[0]!;
    // Header values are strings by definition; a number would be rejected on
    // write, so it is filtered here instead of failing the whole import.
    expect(config.headers).toEqual({ "x-good": "value" });
  });
});
