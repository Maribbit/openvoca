<template>
  <div
    class="def-anchor pointer-events-none fixed inset-x-0 z-50 flex justify-center px-3"
  >
    <Transition name="def-toast">
      <div
        v-if="entry || notFoundWord || loadingWord"
        class="pointer-events-auto"
        @click.stop
      >
        <div
          class="def-toast flex flex-col gap-2 rounded-xl border border-ink/5 bg-surface px-4 py-2.5 shadow-lg dark:border-white/10"
        >
          <!-- Loading State -->
          <span
            v-if="loadingWord && !entry && !notFoundWord"
            class="flex min-w-0 flex-col gap-1 items-center justify-center py-1 px-4"
          >
            <span class="flex items-center gap-2">
              <svg
                class="animate-spin h-4 w-4 text-inkLight"
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
              <span class="font-sans text-sm font-semibold text-ink">{{
                loadingWord
              }}</span>
            </span>
          </span>

          <!-- Found Entry -->
          <span v-else-if="entry" class="flex min-w-0 flex-col gap-0.5">
            <span class="flex items-center gap-2">
              <span class="font-sans text-sm font-semibold text-ink">{{
                entry.word
              }}</span>
              <span
                v-if="entry.phonetic"
                class="font-sans text-xs text-inkLight"
                >/{{ entry.phonetic }}/</span
              >
              <span
                v-if="entry.pos"
                class="rounded bg-ink/5 px-1 py-px font-mono text-[10px] leading-none text-inkLight/60 dark:bg-white/10"
                >{{ entry.pos.toUpperCase() }}</span
              >
              <span
                v-if="showLemmaLabel"
                class="rounded bg-ink/5 px-1.5 py-px font-sans text-[10px] leading-none text-inkLight/70 dark:bg-white/10"
              >
                {{ lemmaLabel ?? "lemma" }}: {{ lemma }}
              </span>
              <button
                v-if="lemma && !isEditingLemma"
                type="button"
                data-testid="lemma-edit-trigger"
                class="shrink-0 rounded p-0.5 text-inkLight/40 transition-colors hover:text-ink"
                :title="editLemmaLabel ?? 'Edit lemma'"
                @click="startLemmaEdit"
              >
                <svg
                  class="h-3 w-3"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.7"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L7.5 19.152 3.75 20.25l1.098-3.75 13.701-13.701Z"
                  />
                </svg>
              </button>
              <button
                type="button"
                data-testid="speak-word"
                class="ml-auto shrink-0 rounded-full p-0.5 text-inkLight/40 transition-colors hover:text-ink"
                :class="{ 'animate-pulse text-ink': wordSpeaking }"
                :title="pronounceLabel"
                @click="speakWord"
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
                    d="M11 5L6 9H2v6h4l5 4V5Z"
                  />
                  <path
                    v-if="!wordSpeaking"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15.54 8.46a5 5 0 0 1 0 7.07"
                  />
                </svg>
              </button>
            </span>
            <span
              v-if="lemma && isEditingLemma"
              class="flex items-center gap-1 font-sans text-[11px] text-inkLight/55"
            >
              <template v-if="isEditingLemma">
                <span>{{ lemmaLabel ?? "lemma" }}:</span>
                <input
                  v-model="draftLemma"
                  data-testid="lemma-edit-input"
                  class="w-24 rounded border border-ink/10 bg-paper px-1.5 py-0.5 text-[11px] text-ink outline-none focus:border-ink/25 dark:border-white/10"
                  :class="{ 'border-red-400': lemmaEditInvalid }"
                  @keydown.enter.prevent="commitLemmaEdit"
                  @keydown.escape.prevent="cancelLemmaEdit"
                />
                <button
                  type="button"
                  data-testid="lemma-edit-save"
                  class="rounded px-1 text-inkLight transition-colors hover:text-ink disabled:opacity-40"
                  :disabled="lemmaEditInvalid"
                  @click="commitLemmaEdit"
                >
                  <svg
                    class="h-3 w-3"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="m4.5 12.75 6 6 9-13.5"
                    />
                  </svg>
                </button>
                <button
                  type="button"
                  class="rounded px-1 text-inkLight/60 transition-colors hover:text-ink"
                  @click="cancelLemmaEdit"
                >
                  <svg
                    class="h-3 w-3"
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
              </template>
              <template v-else>
                <span>{{ lemmaLabel ?? "lemma" }}: {{ lemma }}</span>
                <button
                  type="button"
                  data-testid="lemma-edit-trigger"
                  class="rounded p-0.5 text-inkLight/40 transition-colors hover:text-ink"
                  :title="editLemmaLabel ?? 'Edit lemma'"
                  @click="startLemmaEdit"
                >
                  <svg
                    class="h-3 w-3"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.7"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L7.5 19.152 3.75 20.25l1.098-3.75 13.701-13.701Z"
                    />
                  </svg>
                </button>
              </template>
            </span>
            <div class="def-lines">
              <template v-if="displayMode !== 'en' && entry.translation">
                <span
                  v-for="(line, i) in splitLines(entry.translation)"
                  :key="'zh-' + i"
                  class="font-sans text-sm leading-snug text-inkLight"
                  >{{ line }}</span
                >
              </template>
              <template v-if="displayMode !== 'zh' && entry.definition">
                <span
                  v-for="(line, i) in splitLines(entry.definition)"
                  :key="'en-' + i"
                  class="font-sans text-sm leading-snug text-inkLight"
                  >{{ line }}</span
                >
              </template>
            </div>
          </span>
          <span v-else class="flex min-w-0 flex-col gap-0.5">
            <span class="flex items-center gap-2">
              <span class="font-sans text-sm font-semibold text-ink">{{
                notFoundWord
              }}</span>
              <span
                v-if="showLemmaLabel"
                class="rounded bg-ink/5 px-1.5 py-px font-sans text-[10px] leading-none text-inkLight/70 dark:bg-white/10"
              >
                {{ lemmaLabel ?? "lemma" }}: {{ lemma }}
              </span>
              <button
                v-if="lemma && !isEditingLemma"
                type="button"
                data-testid="lemma-edit-trigger"
                class="shrink-0 rounded p-0.5 text-inkLight/40 transition-colors hover:text-ink"
                :title="editLemmaLabel ?? 'Edit lemma'"
                @click="startLemmaEdit"
              >
                <svg
                  class="h-3 w-3"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.7"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L7.5 19.152 3.75 20.25l1.098-3.75 13.701-13.701Z"
                  />
                </svg>
              </button>
              <button
                type="button"
                data-testid="speak-word"
                class="ml-auto shrink-0 rounded-full p-0.5 text-inkLight/40 transition-colors hover:text-ink"
                :class="{ 'animate-pulse text-ink': wordSpeaking }"
                :title="pronounceLabel"
                @click="speakWord"
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
                    d="M11 5L6 9H2v6h4l5 4V5Z"
                  />
                  <path
                    v-if="!wordSpeaking"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15.54 8.46a5 5 0 0 1 0 7.07"
                  />
                </svg>
              </button>
            </span>
            <span
              v-if="lemma && isEditingLemma"
              class="flex items-center gap-1 font-sans text-[11px] text-inkLight/55"
            >
              <template v-if="isEditingLemma">
                <span>{{ lemmaLabel ?? "lemma" }}:</span>
                <input
                  v-model="draftLemma"
                  data-testid="lemma-edit-input"
                  class="w-24 rounded border border-ink/10 bg-paper px-1.5 py-0.5 text-[11px] text-ink outline-none focus:border-ink/25 dark:border-white/10"
                  :class="{ 'border-red-400': lemmaEditInvalid }"
                  @keydown.enter.prevent="commitLemmaEdit"
                  @keydown.escape.prevent="cancelLemmaEdit"
                />
                <button
                  type="button"
                  data-testid="lemma-edit-save"
                  class="rounded px-1 text-inkLight transition-colors hover:text-ink disabled:opacity-40"
                  :disabled="lemmaEditInvalid"
                  @click="commitLemmaEdit"
                >
                  <svg
                    class="h-3 w-3"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="m4.5 12.75 6 6 9-13.5"
                    />
                  </svg>
                </button>
                <button
                  type="button"
                  class="rounded px-1 text-inkLight/60 transition-colors hover:text-ink"
                  @click="cancelLemmaEdit"
                >
                  <svg
                    class="h-3 w-3"
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
              </template>
              <template v-else>
                <span>{{ lemmaLabel ?? "lemma" }}: {{ lemma }}</span>
                <button
                  type="button"
                  data-testid="lemma-edit-trigger"
                  class="rounded p-0.5 text-inkLight/40 transition-colors hover:text-ink"
                  :title="editLemmaLabel ?? 'Edit lemma'"
                  @click="startLemmaEdit"
                >
                  <svg
                    class="h-3 w-3"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.7"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L7.5 19.152 3.75 20.25l1.098-3.75 13.701-13.701Z"
                    />
                  </svg>
                </button>
              </template>
            </span>
            <span class="font-sans text-sm leading-snug text-inkLight/60">{{
              notFoundText
            }}</span>
          </span>

          <!-- External dictionary links -->
          <div class="flex items-center justify-center gap-2">
            <a
              :href="`https://www.merriam-webster.com/dictionary/${encodeURIComponent(lookupWord)}`"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[11px] text-inkLight/40 transition-colors hover:text-inkLight"
              >MW</a
            >
            <span class="select-none text-inkLight/20">·</span>
            <a
              :href="`https://dictionary.cambridge.org/dictionary/english/${encodeURIComponent(lookupWord)}`"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[11px] text-inkLight/40 transition-colors hover:text-inkLight"
              >Cambridge</a
            >
            <span class="select-none text-inkLight/20">·</span>
            <a
              :href="`https://dict.youdao.com/result?word=${encodeURIComponent(lookupWord)}&lang=en`"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[11px] text-inkLight/40 transition-colors hover:text-inkLight"
              >Youdao</a
            >
          </div>

          <!-- Know / Don't know toggle -->
          <div class="flex justify-center">
            <div
              class="inline-flex items-center rounded-full border border-ink/5 bg-paper p-0.5 dark:border-white/10 dark:bg-white/5"
            >
              <button
                type="button"
                class="def-choice rounded-full px-3.5 py-1 text-xs font-medium transition-all"
                :class="
                  !isMarked
                    ? 'bg-ink text-paper shadow-sm dark:bg-white dark:text-black'
                    : 'text-inkLight hover:text-ink'
                "
                @click="$emit('mark', false)"
              >
                {{ knowText }}
              </button>
              <button
                type="button"
                class="def-choice rounded-full px-3.5 py-1 text-xs font-medium transition-all"
                :class="
                  isMarked
                    ? 'bg-highlight text-ink shadow-sm'
                    : 'text-inkLight hover:text-ink'
                "
                @click="$emit('mark', true)"
              >
                {{ dontKnowText }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
  import { computed, ref, onBeforeUnmount } from "vue";
  import type { DictionaryEntry } from "../api/reading";
  import {
    isValidLemmaInput,
    normalizeLemmaInput,
  } from "../composables/useLemmaOverrides";

  export type DictionaryDisplayMode = "zh" | "en" | "both";

  const props = defineProps<{
    entry: DictionaryEntry | null;
    notFoundWord: string | null;
    loadingWord?: string | null;
    lemma?: string | null;
    lemmaLabel?: string;
    notFoundText: string;
    loadingText?: string;
    editLemmaLabel?: string;
    knowText: string;
    dontKnowText: string;
    isMarked: boolean;
    displayMode: DictionaryDisplayMode;
    pronounceLabel: string;
  }>();

  const lookupWord = computed(
    () =>
      props.entry?.word ??
      props.notFoundWord ??
      props.loadingWord ??
      props.lemma ??
      "",
  );

  const showLemmaLabel = computed(
    () =>
      Boolean(props.lemma) &&
      normalizeLemmaInput(props.lemma ?? "") !==
        normalizeLemmaInput(lookupWord.value),
  );

  const emit = defineEmits<{
    mark: [marked: boolean];
    "lemma-change": [lemma: string];
  }>();

  const isEditingLemma = ref(false);
  const draftLemma = ref("");

  const lemmaEditInvalid = computed(() => !isValidLemmaInput(draftLemma.value));

  function startLemmaEdit(): void {
    draftLemma.value = props.lemma ?? lookupWord.value;
    isEditingLemma.value = true;
  }

  function cancelLemmaEdit(): void {
    isEditingLemma.value = false;
    draftLemma.value = "";
  }

  function commitLemmaEdit(): void {
    if (lemmaEditInvalid.value) return;
    emit("lemma-change", normalizeLemmaInput(draftLemma.value));
    cancelLemmaEdit();
  }

  const MAX_LINES = 4;

  function splitLines(text: string): string[] {
    return text
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean)
      .slice(0, MAX_LINES);
  }

  // --- Word pronunciation ---

  const wordSpeaking = ref(false);
  let wordAudio: HTMLAudioElement | null = null;

  function stopWordAudio(): void {
    if (wordAudio) {
      wordAudio.pause();
      wordAudio.src = "";
      wordAudio = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    wordSpeaking.value = false;
  }

  function speakWordBrowser(word: string): void {
    const utterance = new SpeechSynthesisUtterance(word);
    utterance.lang = "en-US";
    utterance.onend = () => {
      wordSpeaking.value = false;
    };
    wordSpeaking.value = true;
    window.speechSynthesis.speak(utterance);
  }

  function speakWord(): void {
    const word = lookupWord.value;
    if (!word) return;
    if (wordSpeaking.value) {
      stopWordAudio();
      return;
    }
    stopWordAudio();
    wordSpeaking.value = true;
    const params = new URLSearchParams({ text: word });
    const audio = new Audio(`/api/tts?${params.toString()}`);
    wordAudio = audio;
    audio.onplaying = () => {
      wordSpeaking.value = true;
    };
    audio.onended = () => {
      wordAudio = null;
      wordSpeaking.value = false;
    };
    audio.onerror = () => {
      wordAudio = null;
      wordSpeaking.value = false;
      if (window.speechSynthesis) {
        speakWordBrowser(word);
      }
    };
    audio.play().catch(() => {
      wordAudio = null;
      wordSpeaking.value = false;
      if (window.speechSynthesis) {
        speakWordBrowser(word);
      }
    });
  }

  onBeforeUnmount(() => {
    stopWordAudio();
  });
</script>

<style scoped>
  /* Clears the reading dock, which is two rows on narrow screens and a single
     row once the controls fit beside the primary button. */
  .def-anchor {
    bottom: calc(env(safe-area-inset-bottom, 0px) + 132px);
  }

  @media (min-width: 640px) {
    .def-anchor {
      bottom: calc(env(safe-area-inset-bottom, 0px) + 84px);
    }
  }

  .def-toast-enter-active,
  .def-toast-leave-active {
    transition:
      transform 0.3s ease,
      opacity 0.25s ease;
  }
  .def-toast-enter-from,
  .def-toast-leave-to {
    transform: translateY(120%);
    opacity: 0;
  }

  /* Definition lines stack one per row. This has to hold at every width: as
     inline spans they ran together into a single unbroken line, so "光辉, 壮丽,
     显赫" was immediately followed by the English sense with no separation. */
  .def-lines {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  /* On touch the panel is capped and scrolls, because a word with several
     senses would otherwise cover the sentence being read. */
  @media (hover: none) {
    .def-lines {
      max-height: 132px;
      overflow-y: auto;
      overscroll-behavior: contain;
    }
  }

  /* This panel is transient and its controls were sized for a cursor. On touch
     every control gets a finger-sized box: the knowledge choice is the primary
     action and the rest are references, but all are tapped without aiming. */
  @media (hover: none) {
    .def-toast button,
    .def-toast a {
      min-height: 40px;
      min-width: 40px;
    }
    .def-toast a {
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .def-toast .def-choice {
      min-height: 44px;
      padding-inline: 1.25rem;
    }
  }
</style>
