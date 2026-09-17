import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import StatsView from "../src/views/StatsView.vue";

vi.mock("../src/api/reading", () => ({
  deleteWordRecord: vi.fn().mockResolvedValue(undefined),
  exportVocabulary: vi.fn().mockResolvedValue(undefined),
  fetchVocabulary: vi.fn().mockResolvedValue({
    words: [
      {
        lemma: "melancholy",
        level: 1,
        cooldown: 0,
        lastSeen: null,
        firstSeen: null,
        seenCount: 1,
        lastContext: "A melancholy tune filled the room.",
      },
    ],
  }),
  importVocabulary: vi.fn().mockResolvedValue({ imported: 0, skipped: 0 }),
  updateWordRecord: vi.fn().mockImplementation((lemma: string, patch) =>
    Promise.resolve({
      lemma,
      level: patch.level ?? 1,
      cooldown: patch.cooldown ?? 0,
    }),
  ),
}));

function mountStatsView() {
  return mount(StatsView, {
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

describe("StatsView.vue", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  // Covers: AC-STATS-001-01
  it("moves delete out of the row edit action", async () => {
    const wrapper = mountStatsView();
    await flushPromises();

    const rowAction = wrapper.find('[data-testid="stats-row-action"]');
    expect(rowAction.findAll("button")).toHaveLength(1);
    expect(wrapper.find('[data-testid="stats-detail-delete"]').exists()).toBe(
      false,
    );

    await wrapper.find('[data-testid="stats-row"]').trigger("click");
    await flushPromises();

    const deleteButton = wrapper.find('[data-testid="stats-detail-delete"]');
    expect(deleteButton.exists()).toBe(true);
    expect(deleteButton.text()).toContain("Delete word");
  });
});
