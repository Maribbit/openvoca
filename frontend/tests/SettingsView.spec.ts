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
  bodyFields: {},
  apiKeySet: true,
  apiKeyHint: "sk-••••1234",
};

const EMPTY_KEY_STATE = {
  endpoint: "https://opencode.ai/zen/go",
  model: "deepseek-v4-flash",
  headers: {},
  bodyFields: {},
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

/**
 * Save the model configuration the way the interface does.
 *
 * Saving is explicit, so tests that used to rely on a field's change event press
 * the button instead. Staging an edit first is still what ``setValue`` does, and
 * the button stays disabled until one has been made.
 */
async function saveConfiguration(wrapper: ReturnType<typeof mountSettings>) {
  await wrapper.find('[data-testid="provider-save"]').trigger("click");
  await flushPromises();
}

/** Open a folded group, so its contents exist to be interacted with. */
async function openSection(
  wrapper: ReturnType<typeof mountSettings>,
  testId: string,
) {
  await wrapper.find(`[data-testid="${testId}"]`).trigger("click");
  await flushPromises();
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
  it("sends only endpoint, model, headers and body fields when saving", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    const modelInput = wrapper.find('[data-testid="provider-model-input"]');
    await modelInput.setValue("new-model");
    await saveConfiguration(wrapper);

    expect(mocks.setProvider).toHaveBeenCalled();
    const payload = mocks.setProvider.mock.calls[0][0] as Record<string, unknown>;
    expect(Object.keys(payload).sort()).toEqual([
      "bodyFields",
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
    await saveConfiguration(wrapper);

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
  it("shows persisted headers as editable rows, with the group already open", async () => {
    mocks.fetchProvider.mockResolvedValue({
      ...STORED_KEY_STATE,
      headers: { "x-opencode-session": "session-abc" },
    });
    const wrapper = mountSettings();
    await flushPromises();

    // A configured group opens itself. Folded away by default is right for a
    // group nobody has used, and wrong for one that holds something: the reader
    // would have to go looking for settings they already have.
    const names = wrapper.findAll('[data-testid="provider-header-name"]');
    const values = wrapper.findAll('[data-testid="provider-header-value"]');
    expect(names.length).toBe(1);
    expect((names[0].element as HTMLInputElement).value).toBe(
      "x-opencode-session",
    );
    expect((values[0].element as HTMLInputElement).value).toBe("session-abc");
  });

  // Covers: AC-SET-005-08
  it("leaves an unused group folded", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    expect(wrapper.find('[data-testid="provider-header-name"]').exists()).toBe(
      false,
    );
    expect(wrapper.find('[data-testid="provider-body-name"]').exists()).toBe(
      false,
    );
  });

  // Covers: AC-SET-005-08
  it("folds each group on its own", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    // Opening one must not drag the others open: they are peers, and the point
    // of separating them is that a reader opens only what they came for.
    await openSection(wrapper, "provider-body-toggle");

    // An empty group shows its hint and its add button, and no rows.
    expect(wrapper.find('[data-testid="provider-body-add"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('[data-testid="provider-header-add"]').exists()).toBe(
      false,
    );
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
    await saveConfiguration(wrapper);

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
    await saveConfiguration(wrapper);

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

    await openSection(wrapper, "provider-headers-toggle");

    // A nameless row contributes nothing, so it cannot make the configuration
    // dirty on its own. A named row sits beside it so there is something to
    // save, and the assertion covers both at once.
    await wrapper.find('[data-testid="provider-header-add"]').trigger("click");
    await wrapper
      .find('[data-testid="provider-header-value"]')
      .setValue("orphan-value");
    await wrapper.find('[data-testid="provider-header-add"]').trigger("click");
    const names = wrapper.findAll('[data-testid="provider-header-name"]');
    const values = wrapper.findAll('[data-testid="provider-header-value"]');
    await names[1]!.setValue("x-real");
    await values[1]!.setValue("kept");
    await saveConfiguration(wrapper);

    const payload = mocks.setProvider.mock.calls[0][0] as Record<
      string,
      unknown
    >;
    expect(payload.headers).toEqual({ "x-real": "kept" });
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

    // Editing a header is what makes the configuration dirty, which is what
    // enables the save button whose payload this test inspects.
    await wrapper
      .find('[data-testid="provider-header-value"]')
      .setValue("rotated-session");
    await saveConfiguration(wrapper);

    const payload = mocks.setProvider.mock.calls[0][0] as Record<
      string,
      unknown
    >;
    expect(payload).not.toHaveProperty("apiKey");
  });
});

describe("SettingsView.vue – extra request body fields", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Mount with both optional groups open.
   *
   * They fold independently now, so a test that works with body fields has to
   * open that group rather than inheriting an open state from the headers one.
   */
  async function openAdvanced() {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();
    await openSection(wrapper, "provider-headers-toggle");
    await openSection(wrapper, "provider-body-toggle");
    return wrapper;
  }

  async function savedFields(wrapper: ReturnType<typeof mountSettings>) {
    await saveConfiguration(wrapper);
    const payload = mocks.setProvider.mock.calls[0][0] as Record<
      string,
      unknown
    >;
    return payload.bodyFields as Record<string, unknown>;
  }

  // Covers: AC-GEN-003-11
  it("sends a bare word as text", async () => {
    const wrapper = await openAdvanced();

    await wrapper.find('[data-testid="provider-body-add"]').trigger("click");
    await wrapper
      .find('[data-testid="provider-body-name"]')
      .setValue("reasoning_effort");
    await wrapper.find('[data-testid="provider-body-value"]').setValue("none");

    expect(await savedFields(wrapper)).toEqual({ reasoning_effort: "none" });
  });

  // Covers: AC-GEN-003-11
  it("reads a value that parses as JSON as JSON", async () => {
    const wrapper = await openAdvanced();

    await wrapper.find('[data-testid="provider-body-add"]').trigger("click");
    await wrapper
      .find('[data-testid="provider-body-name"]')
      .setValue("thinking");
    await wrapper
      .find('[data-testid="provider-body-value"]')
      .setValue('{"type": "disabled"}');

    expect(await savedFields(wrapper)).toEqual({
      thinking: { type: "disabled" },
    });
  });

  // Covers: AC-GEN-003-11
  it("keeps a boolean a boolean", async () => {
    const wrapper = await openAdvanced();

    await wrapper.find('[data-testid="provider-body-add"]').trigger("click");
    await wrapper
      .find('[data-testid="provider-body-name"]')
      .setValue("enable_thinking");
    await wrapper.find('[data-testid="provider-body-value"]').setValue("false");

    const fields = await savedFields(wrapper);
    expect(fields.enable_thinking).toBe(false);
  });

  // Covers: AC-GEN-003-10
  it("does not send a field the application owns, and says so", async () => {
    const wrapper = await openAdvanced();

    await wrapper.find('[data-testid="provider-body-add"]').trigger("click");
    await wrapper
      .find('[data-testid="provider-body-name"]')
      .setValue("messages");
    await wrapper.find('[data-testid="provider-body-value"]').setValue("[]");
    // A reserved row is dropped, so a valid one is needed as well before there
    // is anything the save button will accept.
    await wrapper.find('[data-testid="provider-body-add"]').trigger("click");
    const names = wrapper.findAll('[data-testid="provider-body-name"]');
    await names[1]!.setValue("reasoning_effort");
    const values = wrapper.findAll('[data-testid="provider-body-value"]');
    await values[1]!.setValue("none");

    // Checked before saving: the response is authoritative and would replace
    // the rows, so the warning is about what is on screen now.
    expect(
      wrapper.find('[data-testid="provider-body-reserved-warning"]').exists(),
    ).toBe(true);
    expect(await savedFields(wrapper)).toEqual({ reasoning_effort: "none" });
  });

  // Covers: AC-GEN-003-10
  it("warns only for reserved names", async () => {
    const wrapper = await openAdvanced();

    await wrapper.find('[data-testid="provider-body-add"]').trigger("click");
    await wrapper
      .find('[data-testid="provider-body-name"]')
      .setValue("reasoning_effort");

    expect(
      wrapper.find('[data-testid="provider-body-reserved-warning"]').exists(),
    ).toBe(false);
  });

  // Covers: AC-GEN-003-09
  it("fills a preset that can then be saved", async () => {
    const wrapper = await openAdvanced();

    const presets = wrapper.findAll('[data-testid="provider-body-preset"]');
    expect(presets.length).toBeGreaterThan(0);
    // The first preset is the flat string form used by OpenAI and DeepSeek.
    await presets[0]!.trigger("click");

    expect(await savedFields(wrapper)).toEqual({ reasoning_effort: "none" });
  });

  // Covers: AC-GEN-003-09
  it("offers a preset for every provider shape, each naming its own action", async () => {
    const wrapper = await openAdvanced();

    const labels = wrapper
      .findAll('[data-testid="provider-body-preset"]')
      .map((p) => p.text());

    // The actions are not uniform, so each button says what it does. Labelling
    // a lower-effort preset "disable thinking" would promise something the
    // provider cannot deliver.
    expect(labels).toContain("Disable thinking · OpenAI / DeepSeek / Ollama");
    expect(labels).toContain("Disable thinking · Z.AI GLM");
    expect(labels).toContain("Disable thinking · OpenRouter");
    expect(labels).toContain("Disable thinking · Qwen3 / vLLM");
    expect(labels).toContain("Lower effort · OpenCode Go");
  });

  // Covers: AC-GEN-003-09
  it("fills the OpenCode effort preset with a value its catalog allows", async () => {
    const wrapper = await openAdvanced();

    const opencode = wrapper
      .findAll('[data-testid="provider-body-preset"]')
      .find((p) => p.text().includes("OpenCode Go"));
    expect(opencode).toBeDefined();
    await opencode!.trigger("click");

    // opencode-go's catalog lists low/high/max for the models it serves and no
    // off value, so `none` would be rejected; `low` is the one that reduces the
    // cost.
    expect(await savedFields(wrapper)).toEqual({ reasoning_effort: "low" });
  });

  // Covers: AC-GEN-003-09
  it("replaces the value when two presets set the same field", async () => {
    const wrapper = await openAdvanced();

    const presets = wrapper.findAll('[data-testid="provider-body-preset"]');
    await presets[0]!.trigger("click"); // reasoning_effort: "none"
    const opencode = presets.find((p) => p.text().includes("OpenCode Go"))!;
    await opencode.trigger("click");

    // Both set reasoning_effort, and only one value can be sent. Two rows with
    // the same name would silently drop one of them on save, so the second
    // preset edits the row rather than adding a rival.
    const names = wrapper.findAll('[data-testid="provider-body-name"]');
    expect(names.filter((n) => (n.element as HTMLInputElement).value === "reasoning_effort")).toHaveLength(1);
    expect(await savedFields(wrapper)).toEqual({ reasoning_effort: "low" });
  });

  // Covers: AC-GEN-003-09
  it("shows stored fields again as editable rows", async () => {
    mocks.fetchProvider.mockResolvedValue({
      ...STORED_KEY_STATE,
      bodyFields: { thinking: { type: "disabled" }, reasoning_effort: "none" },
    });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();
    await wrapper
      .find('[data-testid="provider-headers-toggle"]')
      .trigger("click");

    const names = wrapper.findAll('[data-testid="provider-body-name"]');
    const values = wrapper.findAll('[data-testid="provider-body-value"]');
    const shown = Object.fromEntries(
      names.map((name, i) => [
        (name.element as HTMLInputElement).value,
        (values[i]!.element as HTMLInputElement).value,
      ]),
    );

    expect(shown).toEqual({
      reasoning_effort: "none",
      thinking: '{"type":"disabled"}',
    });
  });

  // Covers: AC-SET-005-10
  it("ignores body rows with an empty name", async () => {
    const wrapper = await openAdvanced();

    // The nameless row cannot make the configuration dirty by itself, so a
    // named row sits beside it and the assertion covers both.
    await wrapper.find('[data-testid="provider-body-add"]').trigger("click");
    await wrapper.find('[data-testid="provider-body-value"]').setValue("orphan");
    await wrapper.find('[data-testid="provider-body-add"]').trigger("click");
    const names = wrapper.findAll('[data-testid="provider-body-name"]');
    const values = wrapper.findAll('[data-testid="provider-body-value"]');
    await names[1]!.setValue("reasoning_effort");
    await values[1]!.setValue("none");

    expect(await savedFields(wrapper)).toEqual({ reasoning_effort: "none" });
  });

  // Covers: AC-SET-005-02
  it("enables Save only when something has changed", async () => {
    const wrapper = await openAdvanced();
    const saveButton = wrapper.find('[data-testid="provider-save"]');

    // The stored configuration is the baseline, so there is nothing to store.
    expect(saveButton.attributes("disabled")).toBeDefined();

    await wrapper
      .find('[data-testid="provider-model-input"]')
      .setValue("another-model");

    expect(saveButton.attributes("disabled")).toBeUndefined();
  });

  // Covers: AC-SET-005-02
  it("says when edits have not been stored yet", async () => {
    const wrapper = await openAdvanced();
    expect(wrapper.find('[data-testid="provider-save-state"]').exists()).toBe(
      false,
    );

    await wrapper
      .find('[data-testid="provider-model-input"]')
      .setValue("another-model");

    expect(
      wrapper.find('[data-testid="provider-save-state"]').text(),
    ).toContain("Unsaved changes");

    await saveConfiguration(wrapper);

    expect(wrapper.find('[data-testid="provider-save-state"]').text()).toContain(
      "Saved",
    );
  });
});

describe("SettingsView.vue – test connection", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  const OK_RESULT = {
    ok: true,
    url: "https://example.test/v1/chat/completions",
    request: { model: "m", stream: false, thinking: { type: false } },
    status: 200,
    response: '{"choices":[{"message":{"content":"ok"}}]}',
    elapsedMs: 812,
    error: "",
    usage: { prompt_tokens: 9, completion_tokens: 3 },
  };

  async function mountWithTest() {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();
    // The test group is always visible: it holds one row until it is run, so
    // there is nothing for a fold to save.
    return wrapper;
  }

  // Covers: AC-SET-005-11
  it("tests the configuration on screen without saving it", async () => {
    const wrapper = await mountWithTest();
    mocks.testProvider.mockResolvedValue({ ...OK_RESULT });

    await wrapper
      .find('[data-testid="provider-model-input"]')
      .setValue("another-model");
    await wrapper.find('[data-testid="provider-test"]').trigger("click");
    await flushPromises();

    // The whole point of testing first: the draft travels to the test, and
    // nothing is persisted until Save is pressed.
    expect(mocks.testProvider).toHaveBeenCalled();
    const [payload] = mocks.testProvider.mock.calls[0]!;
    expect(payload.model).toBe("another-model");
    expect(mocks.setProvider).not.toHaveBeenCalled();
    // Still unsaved, and the interface still says so.
    expect(
      wrapper.find('[data-testid="provider-save-state"]').text(),
    ).toContain("Unsaved changes");
  });

  // Covers: AC-SET-005-11
  it("prints the request and the response", async () => {
    const wrapper = await mountWithTest();
    mocks.testProvider.mockResolvedValue({ ...OK_RESULT });

    await wrapper.find('[data-testid="provider-test"]').trigger("click");
    await flushPromises();

    const output = wrapper.find('[data-testid="provider-test-output"]');
    expect(output.exists()).toBe(true);
    expect(wrapper.find('[data-testid="provider-test-status"]').text()).toContain(
      "200",
    );
    const text = output.text();
    // Seeing the outgoing body is how a configured field is confirmed to have
    // taken effect rather than merely been stored.
    expect(text).toContain("thinking");
    expect(text).toContain("ok");
  });

  // Covers: AC-SET-005-11
  it("reports an HTTP error with the body the provider returned", async () => {
    const wrapper = await mountWithTest();
    mocks.testProvider.mockResolvedValue({
      ...OK_RESULT,
      ok: false,
      status: 400,
      response: '{"error":{"message":"unknown field thinking"}}',
      error: "HTTP 400",
    });

    await wrapper.find('[data-testid="provider-test"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="provider-test-status"]').text()).toContain(
      "HTTP 400",
    );
    // The error body is the part that says what is wrong, so it has to survive.
    expect(wrapper.find('[data-testid="provider-test-output"]').text()).toContain(
      "unknown field thinking",
    );
  });

  // Covers: AC-SET-005-11
  it("flattens nested token counts, which is where reasoning shows up", async () => {
    const wrapper = await mountWithTest();
    mocks.testProvider.mockResolvedValue({
      ...OK_RESULT,
      usage: { completion_tokens: 40, completion_tokens_details: { reasoning_tokens: 0 } },
    });

    await wrapper.find('[data-testid="provider-test"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="provider-test-usage"]').text()).toContain(
      "reasoning_tokens 0",
    );
  });

  // Covers: AC-SET-005-11
  it("can be stopped while it is running", async () => {
    const wrapper = await mountWithTest();
    // A test that never settles stands in for a provider that never answers.
    mocks.testProvider.mockImplementation(
      (_config: unknown, signal?: AbortSignal) =>
        new Promise((_resolve, reject) => {
          signal?.addEventListener("abort", () =>
            reject(new DOMException("aborted", "AbortError")),
          );
        }),
    );

    const stop = wrapper.find('[data-testid="provider-test-stop"]');
    expect(stop.attributes("disabled")).toBeDefined();

    await wrapper.find('[data-testid="provider-test"]').trigger("click");
    await flushPromises();
    // Running: Stop becomes available and a clock shows the wait is live.
    expect(stop.attributes("disabled")).toBeUndefined();
    expect(wrapper.find('[data-testid="provider-test-elapsed"]').exists()).toBe(
      true,
    );

    await stop.trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="provider-test-status"]').text()).toContain(
      "Stopped",
    );
    expect(wrapper.find('[data-testid="provider-test-elapsed"]').exists()).toBe(
      false,
    );
  });

  // Covers: AC-SET-005-11
  it("clears a result that no longer describes what is on screen", async () => {
    const wrapper = await mountWithTest();
    mocks.testProvider.mockResolvedValue({ ...OK_RESULT });

    await wrapper.find('[data-testid="provider-test"]').trigger("click");
    await flushPromises();
    expect(wrapper.find('[data-testid="provider-test-output"]').exists()).toBe(
      true,
    );

    await wrapper
      .find('[data-testid="provider-model-input"]')
      .setValue("changed-after-testing");
    await flushPromises();

    expect(wrapper.find('[data-testid="provider-test-output"]').exists()).toBe(
      false,
    );
  });
});

describe("SettingsView.vue – discarding and staying reachable", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  async function mountDirty() {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    mocks.setProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();
    await wrapper
      .find('[data-testid="provider-model-input"]')
      .setValue("edited-model");
    await flushPromises();
    return wrapper;
  }

  // Covers: AC-SET-005-12
  it("puts the form back to what is stored", async () => {
    const wrapper = await mountDirty();

    await wrapper.find('[data-testid="provider-discard"]').trigger("click");
    await flushPromises();

    expect(
      (wrapper.find('[data-testid="provider-model-input"]')
        .element as HTMLInputElement).value,
    ).toBe(STORED_KEY_STATE.model);
    // No longer dirty, so there is nothing left to save.
    expect(wrapper.find('[data-testid="provider-save-state"]').exists()).toBe(
      false,
    );
  });

  // Covers: AC-SET-005-12
  it("writes nothing when discarding", async () => {
    const wrapper = await mountDirty();

    await wrapper.find('[data-testid="provider-discard"]').trigger("click");
    await flushPromises();

    // Discarding is the opposite of saving: it must not persist the draft it is
    // throwing away.
    expect(mocks.setProvider).not.toHaveBeenCalled();
  });

  // Covers: AC-SET-005-12
  it("re-reads instead of remembering an earlier value", async () => {
    const wrapper = await mountDirty();
    mocks.fetchProvider.mockClear();
    mocks.fetchProvider.mockResolvedValue({
      ...STORED_KEY_STATE,
      model: "changed-elsewhere",
    });

    await wrapper.find('[data-testid="provider-discard"]').trigger("click");
    await flushPromises();

    // Whatever is stored now is what "before" means. A history of past saves
    // would mean something different after a second save.
    expect(mocks.fetchProvider).toHaveBeenCalled();
    expect(
      (wrapper.find('[data-testid="provider-model-input"]')
        .element as HTMLInputElement).value,
    ).toBe("changed-elsewhere");
  });

  // Covers: AC-SET-005-12
  it("drops a test result, which described the discarded draft", async () => {
    const wrapper = await mountDirty();
    mocks.testProvider.mockResolvedValue({
      ok: true,
      url: "https://example.test/v1/chat/completions",
      request: {},
      status: 200,
      response: "{}",
      elapsedMs: 5,
      error: "",
      usage: null,
    });
    await wrapper.find('[data-testid="provider-test"]').trigger("click");
    await flushPromises();
    expect(wrapper.find('[data-testid="provider-test-output"]').exists()).toBe(
      true,
    );

    await wrapper.find('[data-testid="provider-discard"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="provider-test-output"]').exists()).toBe(
      false,
    );
  });

  // Covers: AC-SET-005-12
  it("offers no discard when there is nothing to discard", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    expect(
      wrapper.find('[data-testid="provider-discard"]').attributes("disabled"),
    ).toBeDefined();
  });

  // Covers: AC-SET-005-13
  it("keeps the actions in view while the card scrolls", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    // Sticky rather than merely last: the groups above expand past a screenful,
    // and a Save that scrolls away is one that gets skipped.
    const bar = wrapper.find('[data-testid="provider-action-bar"]');
    expect(bar.exists()).toBe(true);
    expect(bar.classes()).toContain("sticky");
  });

  // Covers: AC-SET-005-12
  it("reports nothing unsaved before the stored configuration has been read", async () => {
    // A fetch that never settles: the state the page is in while loading.
    mocks.fetchProvider.mockReturnValue(new Promise(() => {}));
    const wrapper = mountSettings();
    await flushPromises();

    // The form holds defaults and the baseline is still empty, so a naive
    // comparison would call that an edit -- on every visit, and permanently if
    // the read failed.
    expect(wrapper.find('[data-testid="provider-save-state"]').exists()).toBe(
      false,
    );
    expect(
      wrapper.find('[data-testid="provider-save"]').attributes("disabled"),
    ).toBeDefined();
  });

  // Covers: AC-SET-005-12
  it("stays usable when the stored configuration cannot be read", async () => {
    mocks.fetchProvider.mockRejectedValue(new Error("offline"));
    const wrapper = mountSettings();
    await flushPromises();

    // Not dirty, so leaving is not blocked over an edit nobody made.
    expect(wrapper.find('[data-testid="provider-save-state"]').exists()).toBe(
      false,
    );

    // And editing still works, so the failure does not make the form a dead end.
    await wrapper
      .find('[data-testid="provider-model-input"]')
      .setValue("typed-anyway");
    await flushPromises();
    expect(
      wrapper.find('[data-testid="provider-save"]').attributes("disabled"),
    ).toBeUndefined();
  });

  // Covers: AC-SET-005-11
  it("keeps the test controls visible without unfolding anything", async () => {
    mocks.fetchProvider.mockResolvedValue({ ...STORED_KEY_STATE });
    const wrapper = mountSettings();
    await flushPromises();

    // It holds one row until it runs, so folding it would hide a control that is
    // already compact -- unlike the two groups above it.
    expect(wrapper.find('[data-testid="provider-test"]').exists()).toBe(true);
    expect(
      wrapper.find('[data-testid="provider-test-toggle"]').exists(),
    ).toBe(false);
  });
});
