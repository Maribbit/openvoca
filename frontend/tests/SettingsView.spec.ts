import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import SettingsView from "../src/views/SettingsView.vue";

const mocks = vi.hoisted(() => ({
  clearProviderKey: vi.fn(),
  fetchProvider: vi.fn(),
  setProvider: vi.fn(),
  setProviderKey: vi.fn(),
  testProvider: vi.fn(),
}));

vi.mock("../src/api/settings", () => ({
  clearProviderKey: mocks.clearProviderKey,
  deleteAllSettings: vi.fn().mockResolvedValue(0),
  fetchAllSettings: vi.fn().mockResolvedValue({}),
  fetchProvider: mocks.fetchProvider,
  putNamespace: vi.fn().mockResolvedValue(undefined),
  setProvider: mocks.setProvider,
  setProviderKey: mocks.setProviderKey,
  testProvider: mocks.testProvider,
}));

vi.mock("../src/api/reading", () => ({
  clearVocabulary: vi.fn().mockResolvedValue(undefined),
  exportVocabulary: vi.fn().mockResolvedValue(undefined),
}));

const STORED_KEY_STATE = {
  endpoint: "https://opencode.ai/zen/go",
  model: "deepseek-v4-flash",
  headers: {},
  apiKeySet: true,
  apiKeyHint: "sk-••••1234",
};

const EMPTY_KEY_STATE = {
  endpoint: "https://opencode.ai/zen/go",
  model: "deepseek-v4-flash",
  headers: {},
  apiKeySet: false,
  apiKeyHint: "",
};

function mountSettings() {
  return mount(SettingsView, {
    global: {
      stubs: {
        RouterLink: {
          props: ["to"],
          template: '<a :href="to"><slot /></a>',
        },
      },
    },
  });
}

describe("SettingsView.vue – API key lifecycle", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  // Covers: AC-SET-005-07
  it("shows a stored key as read-only text, never as an input value", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    expect(wrapper.text()).toContain("sk-••••1234");
    for (const input of wrapper.findAll("input")) {
      expect((input.element as HTMLInputElement).value).not.toContain("••••");
    }
  });

  // Covers: AC-SET-005-07
  it("offers a password input when no key is stored", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...EMPTY_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    const keyInput = wrapper.find('[data-testid="provider-key-input"]');
    expect(keyInput.exists()).toBe(true);
    expect(keyInput.attributes("type")).toBe("password");
  });

  // Covers: AC-SET-005-01
  it("sends only endpoint, model and headers when saving the connection", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    const modelInput = wrapper.find('[data-testid="provider-model-input"]');
    await modelInput.setValue("new-model");
    await modelInput.trigger("change");
    await flushPromises();

    expect(mocks.setProvider).toHaveBeenCalled();
    const payload = mocks.setProvider.mock.calls[0][0] as Record<string, unknown>;
    expect(Object.keys(payload).sort()).toEqual([
      "endpoint",
      "headers",
      "model",
    ]);
    expect(payload).not.toHaveProperty("apiKey");
  });

  // Covers: AC-SET-005-02
  it("keeps showing the key as configured after a connection save", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    const modelInput = wrapper.find('[data-testid="provider-model-input"]');
    await modelInput.setValue("new-model");
    await modelInput.trigger("change");
    await flushPromises();

    expect(wrapper.text()).toContain("sk-••••1234");
    expect(wrapper.find('[data-testid="provider-key-input"]').exists()).toBe(
      false,
    );
  });

  // Covers: AC-SET-005-04
  it("stores a new key through the dedicated key endpoint", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...EMPTY_KEY_STATE });
    mocks.setProviderKey.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    await wrapper
      .find('[data-testid="provider-key-input"]')
      .setValue("sk-brand-new-9999");
    await wrapper.find('[data-testid="provider-key-save"]').trigger("click");
    await flushPromises();

    expect(mocks.setProviderKey).toHaveBeenCalledWith("sk-brand-new-9999");
  });

  // Covers: AC-SET-005-04
  it("does not call the key endpoint when the input is empty", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...EMPTY_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    await wrapper.find('[data-testid="provider-key-save"]').trigger("click");
    await flushPromises();

    expect(mocks.setProviderKey).not.toHaveBeenCalled();
  });

  // Covers: AC-SET-005-05
  it("clears the stored key through the dedicated endpoint", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    mocks.clearProviderKey.mockResolvedValue({ ...EMPTY_KEY_STATE });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const wrapper = mountSettings();
    await flushPromises();

    await wrapper.find('[data-testid="provider-key-clear"]').trigger("click");
    await flushPromises();

    expect(mocks.clearProviderKey).toHaveBeenCalled();
  });

  // Covers: AC-SET-005-05
  it("returns to the editable input after the key is cleared", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    mocks.clearProviderKey.mockResolvedValue({ ...EMPTY_KEY_STATE });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const wrapper = mountSettings();
    await flushPromises();

    await wrapper.find('[data-testid="provider-key-clear"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="provider-key-input"]').exists()).toBe(
      true,
    );
    expect(wrapper.text()).not.toContain("sk-••••1234");
  });
});

describe("SettingsView.vue – custom request headers", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  // Covers: AC-SET-005-08
  it("shows persisted headers as editable rows", async () => {
    mocks.fetchProvider.mockResolvedValue({
      ...STORED_KEY_STATE,
      headers: { "x-opencode-session": "session-abc" },
    });
    const wrapper = mountSettings();
    await flushPromises();

    const names = wrapper.findAll('[data-testid="provider-header-name"]');
    const values = wrapper.findAll('[data-testid="provider-header-value"]');
    expect(names.length).toBe(1);
    expect((names[0].element as HTMLInputElement).value).toBe(
      "x-opencode-session",
    );
    expect((values[0].element as HTMLInputElement).value).toBe("session-abc");
  });

  // Covers: AC-SET-005-10
  it("sends the edited header set when saving the connection", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    // The section starts collapsed while no headers are configured.
    await wrapper
      .find('[data-testid="provider-headers-toggle"]')
      .trigger("click");
    await wrapper.find('[data-testid="provider-header-add"]').trigger("click");
    await wrapper
      .find('[data-testid="provider-header-name"]')
      .setValue("x-opencode-session");
    await wrapper
      .find('[data-testid="provider-header-value"]')
      .setValue("session-xyz");
    const modelInput = wrapper.find('[data-testid="provider-model-input"]');
    await modelInput.trigger("change");
    await flushPromises();

    expect(mocks.setProvider).toHaveBeenCalled();
    const payload = mocks.setProvider.mock.calls[0][0] as Record<
      string,
      unknown
    >;
    expect(payload.headers).toEqual({ "x-opencode-session": "session-xyz" });
  });

  // Covers: AC-SET-005-10
  it("drops removed headers from the saved set", async () => {
    mocks.fetchProvider.mockResolvedValue({
      ...STORED_KEY_STATE,
      headers: { "x-opencode-session": "keep-me-out" },
    });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    await wrapper
      .find('[data-testid="provider-header-remove"]')
      .trigger("click");
    await wrapper.find('[data-testid="provider-model-input"]').trigger("change");
    await flushPromises();

    const payload = mocks.setProvider.mock.calls[0][0] as Record<
      string,
      unknown
    >;
    expect(payload.headers).toEqual({});
  });

  // Covers: AC-SET-005-10
  it("ignores header rows with an empty name", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    await wrapper
      .find('[data-testid="provider-headers-toggle"]')
      .trigger("click");
    await wrapper.find('[data-testid="provider-header-add"]').trigger("click");
    await wrapper
      .find('[data-testid="provider-header-value"]')
      .setValue("orphan-value");
    await wrapper.find('[data-testid="provider-model-input"]').trigger("change");
    await flushPromises();

    const payload = mocks.setProvider.mock.calls[0][0] as Record<
      string,
      unknown
    >;
    expect(payload.headers).toEqual({});
  });

  // Covers: AC-SET-005-01
  it("does not send the api key when saving headers", async () => {
    mocks.fetchProvider.mockResolvedValue({
      ...STORED_KEY_STATE,
      headers: { "x-opencode-session": "session-abc" },
    });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    await wrapper.find('[data-testid="provider-model-input"]').trigger("change");
    await flushPromises();

    const payload = mocks.setProvider.mock.calls[0][0] as Record<
      string,
      unknown
    >;
    expect(payload).not.toHaveProperty("apiKey");
  });
});
