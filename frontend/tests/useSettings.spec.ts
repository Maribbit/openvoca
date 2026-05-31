import { describe, it, expect, beforeEach, vi } from "vitest";
import { useSettings } from "../src/composables/useSettings";

// Stub the settings API to avoid real HTTP calls
vi.mock("../src/api/settings", () => ({
  fetchAllSettings: vi.fn().mockResolvedValue({}),
  putNamespace: vi.fn().mockResolvedValue(undefined),
  deleteAllSettings: vi.fn().mockResolvedValue(0),
}));

describe("useSettings – exportAll / importAll", () => {
  let settings: ReturnType<typeof useSettings>;

  beforeEach(() => {
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
});
