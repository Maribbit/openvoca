<template>
  <div class="min-h-zoom-screen bg-paper px-8 pb-32 pt-10 text-ink antialiased">
    <div class="mx-auto max-w-5xl">
      <!-- Kept first in the document so the heading still leads the page for
           assistive tech; the visible label lives in the dock below. -->
      <h1 class="sr-only">{{ i18nMessages.vocabulary }}</h1>

      <!-- Import result banner -->
      <Transition name="menu-fade">
        <div
          v-if="importStatus"
          class="mb-6 flex items-center justify-between rounded-xl px-5 py-3 text-sm shadow-sm"
          :class="
            importError
              ? 'border border-red-200 bg-red-50 text-red-600'
              : 'border border-green-500/20 bg-green-500/5 text-green-600'
          "
        >
          <div class="flex items-center gap-3">
            <span>{{ importStatus }}</span>
            <button
              v-if="lastImportedFile && importSkippedExisting"
              type="button"
              class="cursor-pointer rounded-full bg-black/5 px-3 py-1 text-xs font-medium text-ink transition-colors hover:bg-black/10"
              @click="reimportOverwrite"
            >
              {{ i18nMessages.importModeOverwrite }}
            </button>
          </div>
          <button
            type="button"
            class="ml-4 cursor-pointer rounded p-1 transition-colors hover:bg-black/5"
            @click="importStatus = ''"
          >
            <svg
              class="h-3.5 w-3.5"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M6 18 18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </Transition>

      <div
        v-if="isLoading"
        class="flex flex-col items-center justify-center rounded-2xl border border-black/5 bg-surface p-12 text-center"
      >
        <svg
          class="h-8 w-8 animate-spin text-inkLight/40 mb-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        <p class="text-sm text-inkLight">{{ i18nMessages.statsLoading }}</p>
      </div>

      <div
        v-else-if="words.length === 0"
        class="rounded-2xl border border-black/5 bg-surface p-12 text-center"
      >
        <p class="text-inkLight">{{ i18nMessages.emptyVocabulary }}</p>
      </div>

      <div
        v-else
        class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
      >
        <!-- Sort toggle -->
        <div
          class="flex flex-wrap items-center justify-between gap-1 border-b border-black/5 px-6 py-3"
        >
          <div class="flex gap-1">
            <button
              type="button"
              class="rounded-full px-3 py-1 text-xs font-medium transition-colors"
              :class="
                sortMode === 'due'
                  ? 'bg-black/8 text-ink'
                  : 'text-inkLight hover:bg-black/4'
              "
              @click="sortMode = 'due'"
            >
              {{ i18nMessages.sortByDue }}
            </button>
            <button
              type="button"
              class="rounded-full px-3 py-1 text-xs font-medium transition-colors"
              :class="
                sortMode === 'familiarity'
                  ? 'bg-black/8 text-ink'
                  : 'text-inkLight hover:bg-black/4'
              "
              @click="sortMode = 'familiarity'"
            >
              {{ i18nMessages.sortByFamiliarity }}
            </button>
            <button
              type="button"
              class="rounded-full px-3 py-1 text-xs font-medium transition-colors"
              :class="
                sortMode === 'recent'
                  ? 'bg-black/8 text-ink'
                  : 'text-inkLight hover:bg-black/4'
              "
              @click="sortMode = 'recent'"
            >
              {{ i18nMessages.sortByRecent }}
            </button>
          </div>
          <span class="text-xs text-inkLight/60">
            {{ i18nMessages.statsIntervalTip }}
          </span>
        </div>

        <table class="w-full table-fixed border-collapse text-left">
          <colgroup>
            <col />
            <col class="w-40" />
            <col class="w-40" />
            <col class="w-14" />
          </colgroup>
          <thead>
            <tr
              class="border-b border-black/5 bg-surface text-xs uppercase tracking-widest text-inkLight"
            >
              <th class="px-6 py-4 font-medium">
                {{ i18nMessages.statsLemma }}
              </th>
              <th
                data-testid="stats-level-header"
                class="px-4 py-4 text-center font-medium"
              >
                {{ i18nMessages.statsInterval }}
              </th>
              <th
                data-testid="stats-cooldown-header"
                class="px-4 py-4 text-center font-medium"
              >
                {{ i18nMessages.statsCooldown }}
              </th>
              <th class="px-2 py-4"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-black/3 text-sm">
            <template v-for="word in words" :key="word.lemma">
              <tr
                class="cursor-pointer transition-colors hover:bg-black/2"
                @click="toggleExpand(word)"
              >
                <td class="px-6 py-4">
                  <span class="font-serif text-lg text-ink">{{
                    word.lemma
                  }}</span>
                </td>
                <td
                  data-testid="stats-level-cell"
                  class="px-4 py-4 text-center"
                >
                  <span
                    v-if="editingKey !== word.lemma"
                    class="mx-auto inline-flex h-8 w-20 items-center justify-center rounded-md font-mono text-sm tabular-nums"
                    :class="
                      word.level >= 6
                        ? 'text-emerald-500 font-semibold'
                        : 'text-inkLight'
                    "
                  >
                    {{ word.level }}
                  </span>
                  <input
                    v-else
                    type="text"
                    inputmode="numeric"
                    pattern="[0-9]*"
                    :value="word.level"
                    class="mx-auto block h-8 w-20 rounded-md border border-ink/12 bg-paper/70 px-0 text-center font-mono text-sm tabular-nums outline-none transition-colors focus:border-ink/20 focus:bg-surface focus:ring-2 focus:ring-highlight/60"
                    :class="
                      word.level >= 6
                        ? 'text-emerald-500 font-semibold'
                        : 'text-inkLight'
                    "
                    @change="onLevelInput(word, $event)"
                    @click.stop
                  />
                </td>
                <td
                  data-testid="stats-cooldown-cell"
                  class="px-4 py-4 text-center"
                >
                  <span
                    v-if="editingKey !== word.lemma"
                    class="mx-auto inline-flex h-8 w-20 items-center justify-center rounded-md font-mono text-sm tabular-nums"
                    :class="
                      word.cooldown > 0
                        ? 'text-inkLight'
                        : 'text-green-500 font-semibold'
                    "
                  >
                    {{ word.cooldown }}
                  </span>
                  <input
                    v-else
                    type="text"
                    inputmode="numeric"
                    pattern="[0-9]*"
                    :value="word.cooldown"
                    class="mx-auto block h-8 w-20 rounded-md border border-ink/12 bg-paper/70 px-0 text-center font-mono text-sm tabular-nums outline-none transition-colors focus:border-ink/20 focus:bg-surface focus:ring-2 focus:ring-highlight/60"
                    :class="
                      word.cooldown > 0
                        ? 'text-inkLight'
                        : 'text-green-500 font-semibold'
                    "
                    @change="onCooldownInput(word, $event)"
                    @click.stop
                  />
                </td>
                <td class="px-2 py-4">
                  <div
                    data-testid="stats-row-action"
                    class="flex items-center justify-end"
                  >
                    <button
                      type="button"
                      class="cursor-pointer rounded p-1 text-inkLight/40 transition-colors hover:bg-black/5 hover:text-ink dark:text-white/40 dark:hover:bg-white/10 dark:hover:text-white"
                      :class="{
                        'bg-black/8 text-ink dark:bg-white/15 dark:text-white':
                          editingKey === word.lemma,
                      }"
                      :title="
                        editingKey === word.lemma
                          ? i18nMessages.doneEditingRow || 'Done'
                          : i18nMessages.editRow || 'Edit'
                      "
                      @click.stop="toggleEdit(word)"
                    >
                      <svg
                        v-if="editingKey === word.lemma"
                        class="h-4 w-4"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.5"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="m4.5 12.75 6 6 9-13.5"
                        />
                      </svg>
                      <svg
                        v-else
                        class="h-4 w-4"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.5"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125"
                        />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
              <!-- Expanded detail row -->
              <tr v-if="expandedKey === word.lemma">
                <td colspan="4" class="bg-black/2 px-6 py-3">
                  <div
                    class="flex flex-col gap-3 text-xs text-inkLight sm:flex-row sm:items-start sm:justify-between"
                  >
                    <div class="flex flex-col gap-1">
                      <div>
                        <span class="font-medium"
                          >{{ i18nMessages.lastSeenLabel }}:</span
                        >
                        {{ formatLastSeen(word.lastSeen) }}
                      </div>
                      <div v-if="word.firstSeen">
                        <span class="font-medium"
                          >{{ i18nMessages.firstSeenLabel }}:</span
                        >
                        {{ formatLastSeen(word.firstSeen) }}
                      </div>
                      <div v-if="word.seenCount !== undefined">
                        <span class="font-medium"
                          >{{ i18nMessages.seenCountLabel }}:</span
                        >
                        {{ word.seenCount }}×
                      </div>
                      <div v-if="word.lastContext">
                        <span class="font-medium"
                          >{{ i18nMessages.lastContextLabel }}:</span
                        >
                        <span class="ml-1 font-serif italic">{{
                          word.lastContext
                        }}</span>
                      </div>
                    </div>
                    <button
                      type="button"
                      data-testid="stats-detail-delete"
                      class="inline-flex w-fit shrink-0 items-center gap-1.5 rounded-full border border-red-500/15 px-3 py-1.5 text-xs font-medium text-red-500 transition-colors hover:bg-red-500/8 hover:text-red-600 dark:border-red-400/20 dark:text-red-400 dark:hover:bg-red-400/10"
                      :title="i18nMessages.deleteWord"
                      @click.stop="handleDeleteWord(word)"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.5"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
                        />
                      </svg>
                      <span>{{ i18nMessages.deleteWord }}</span>
                    </button>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>

        <div
          class="border-t border-black/5 bg-black/2 px-6 py-4 text-sm text-inkLight"
        >
          {{ words.length }} {{ i18nMessages.showingWords }}
        </div>
      </div>
    </div>

    <!-- Title and actions sit together here, so they stay in reach while the
         list scrolls instead of occupying a bar at the top of the page. -->
    <footer
      data-testid="stats-dock"
      class="fixed inset-x-0 bottom-0 z-30 border-t border-ink/8 bg-paper/95 backdrop-blur-md"
      style="padding-bottom: env(safe-area-inset-bottom, 0px)"
    >
      <div
        class="mx-auto flex w-full max-w-5xl items-center justify-between gap-3 px-4 py-2.5 sm:px-8"
      >
        <div class="min-w-0">
          <p
            class="truncate font-serif text-lg leading-tight tracking-wide text-ink"
          >
            {{ i18nMessages.vocabulary }}
          </p>
          <p class="truncate text-xs text-inkLight">
            {{ words.length }} {{ i18nMessages.showingWords }}
          </p>
        </div>
        <div class="flex shrink-0 items-center gap-1">
          <input
            ref="importFileInput"
            type="file"
            accept=".csv"
            class="hidden"
            @change="onFileSelected"
          />
          <button
            type="button"
            data-testid="stats-import"
            class="tap-target gap-2 rounded-full border border-ink/10 bg-surface text-sm font-medium text-ink transition-colors hover:border-ink/18 active:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-50 sm:px-4"
            @click="importFileInput?.click()"
            :disabled="isImporting || isLoading"
            :title="i18nMessages.importVocabulary"
            :aria-label="i18nMessages.importVocabulary"
          >
            <svg
              v-if="isImporting"
              class="h-5 w-5 animate-spin text-ink"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <svg
              v-else
              class="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2m-4-8-4-4m0 0L8 8m4-4v12"
              />
            </svg>
            <span class="hidden sm:inline">{{
              i18nMessages.importVocabulary
            }}</span>
          </button>
          <button
            type="button"
            data-testid="stats-export"
            class="tap-target gap-2 rounded-full border border-ink/10 bg-surface text-sm font-medium text-ink transition-colors hover:border-ink/18 active:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-50 sm:px-4"
            @click="handleExport"
            :disabled="isExporting || isLoading"
            :title="i18nMessages.exportVocabulary"
            :aria-label="i18nMessages.exportVocabulary"
          >
            <svg
              v-if="isExporting"
              class="h-5 w-5 animate-spin text-ink"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <svg
              v-else
              class="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V3"
              />
            </svg>
            <span class="hidden sm:inline">{{
              i18nMessages.exportVocabulary
            }}</span>
          </button>
          <router-link
            to="/"
            data-testid="stats-back"
            class="tap-target gap-2 rounded-full border border-ink/10 bg-surface text-sm font-medium text-ink transition-colors hover:border-ink/18 active:bg-ink/5 sm:px-4"
            :title="i18nMessages.backToReading"
            :aria-label="i18nMessages.backToReading"
          >
            <svg
              class="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            <span class="hidden sm:inline">{{
              i18nMessages.backToReading
            }}</span>
          </router-link>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
  import { onMounted, ref, watch } from "vue";

  import {
    deleteWordRecord,
    exportVocabulary,
    fetchVocabulary,
    importVocabulary,
    updateWordRecord,
    type WordRecordOut,
  } from "../api/reading";
  import { useI18n } from "../composables/useI18n";

  type SortMode = "due" | "familiarity" | "recent";

  const { messages: i18nMessages } = useI18n();
  const words = ref<WordRecordOut[]>([]);
  const sortMode = ref<SortMode>("due");
  const expandedKey = ref<string | null>(null);
  const importFileInput = ref<HTMLInputElement | null>(null);
  const importStatus = ref<string>("");
  const importError = ref(false);
  const lastImportedFile = ref<File | null>(null);
  const importSkippedExisting = ref(false);
  const isLoading = ref(true);
  const isImporting = ref(false);
  const isExporting = ref(false);
  const editingKey = ref<string | null>(null);

  function toggleExpand(word: WordRecordOut): void {
    const key = word.lemma;
    expandedKey.value = expandedKey.value === key ? null : key;
  }

  function toggleEdit(word: WordRecordOut): void {
    editingKey.value = editingKey.value === word.lemma ? null : word.lemma;
  }

  function formatLastSeen(iso: string | null | undefined): string {
    if (!iso) return "—";
    const date = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return i18nMessages.value.timeJustNow;
    if (diffMin < 60) return i18nMessages.value.timeMinutesAgo(diffMin);
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24) return i18nMessages.value.timeHoursAgo(diffH);
    const diffD = Math.floor(diffH / 24);
    return i18nMessages.value.timeDaysAgo(diffD);
  }

  async function loadWords(): Promise<void> {
    isLoading.value = true;
    try {
      const response = await fetchVocabulary(sortMode.value);
      words.value = response.words;
    } catch {
      words.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function handleExport(): Promise<void> {
    if (isExporting.value) return;
    isExporting.value = true;
    try {
      await exportVocabulary();
    } finally {
      isExporting.value = false;
    }
  }

  async function onFileSelected(event: Event): Promise<void> {
    if (isImporting.value) return;
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    input.value = "";
    importStatus.value = "";
    importError.value = false;
    importSkippedExisting.value = false;
    lastImportedFile.value = file;
    isImporting.value = true;
    try {
      const result = await importVocabulary(file, "skip");
      importSkippedExisting.value = result.skipped > 0;
      importStatus.value =
        result.skipped > 0
          ? i18nMessages.value.importedSkipped
              .replace("{0}", String(result.imported))
              .replace("{1}", String(result.skipped))
          : i18nMessages.value.importedWords.replace(
              "{0}",
              String(result.imported),
            );
      importError.value = false;
      await loadWords();
    } catch (err) {
      importError.value = true;
      lastImportedFile.value = null;
      importStatus.value =
        err instanceof Error ? err.message : i18nMessages.value.importFailed;
    } finally {
      isImporting.value = false;
    }
  }

  async function reimportOverwrite(): Promise<void> {
    if (isImporting.value) return;
    const file = lastImportedFile.value;
    if (!file) return;
    importStatus.value = "";
    importError.value = false;
    importSkippedExisting.value = false;
    isImporting.value = true;
    try {
      const result = await importVocabulary(file, "overwrite");
      lastImportedFile.value = null;
      importStatus.value =
        result.skipped > 0
          ? i18nMessages.value.importedSkipped
              .replace("{0}", String(result.imported))
              .replace("{1}", String(result.skipped))
          : i18nMessages.value.importedWords.replace(
              "{0}",
              String(result.imported),
            );
      importError.value = false;
      await loadWords();
    } catch (err) {
      importError.value = true;
      importStatus.value =
        err instanceof Error ? err.message : i18nMessages.value.importFailed;
    } finally {
      isImporting.value = false;
    }
  }

  async function changeLevel(
    word: WordRecordOut,
    newLevel: number,
  ): Promise<void> {
    try {
      const updated = await updateWordRecord(word.lemma, {
        level: Math.round(newLevel),
      });
      word.level = updated.level;
      word.cooldown = updated.cooldown;
    } catch {
      /* silently ignore */
    }
  }

  async function changeCooldown(
    word: WordRecordOut,
    newCooldown: number,
  ): Promise<void> {
    try {
      const updated = await updateWordRecord(word.lemma, {
        cooldown: newCooldown,
      });
      word.cooldown = updated.cooldown;
    } catch {
      /* silently ignore */
    }
  }

  function onLevelInput(word: WordRecordOut, event: Event): void {
    const input = event.target as HTMLInputElement;
    const value = parseInt(input.value, 10);
    if (Number.isNaN(value)) {
      input.value = String(word.level);
      return;
    }
    void changeLevel(word, value);
  }

  function onCooldownInput(word: WordRecordOut, event: Event): void {
    const input = event.target as HTMLInputElement;
    const value = parseInt(input.value, 10);
    if (Number.isNaN(value)) {
      input.value = String(word.cooldown);
      return;
    }
    void changeCooldown(word, value);
  }

  async function handleDeleteWord(word: WordRecordOut): Promise<void> {
    try {
      await deleteWordRecord(word.lemma);
      words.value = words.value.filter((w) => w.lemma !== word.lemma);
    } catch {
      /* silently ignore — record may already be deleted */
    }
  }

  watch(sortMode, () => {
    expandedKey.value = null;
    void loadWords();
  });

  onMounted(() => {
    void loadWords();
  });
</script>
