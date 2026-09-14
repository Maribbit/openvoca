<template>
  <div
    class="relative min-h-zoom-screen overflow-hidden bg-paper font-sans text-ink transition-colors duration-300"
  >
    <header
      class="group fixed inset-x-0 top-0 z-10 flex items-center justify-between px-6 py-6 uppercase tracking-[0.45em] text-inkLight/50 md:px-10"
      :class="uiHeaderSizeClass"
    >
      <div class="flex flex-1 items-center justify-start gap-1">
        <router-link
          to="/settings"
          class="cursor-pointer rounded-full px-3 py-2 transition-colors hover:text-ink"
        >
          {{ i18nMessages.menu }}
        </router-link>
        <button
          v-if="!showComposer"
          type="button"
          data-testid="reading-settings-trigger"
          class="cursor-pointer rounded-full p-2 transition-all hover:text-ink opacity-0 group-hover:opacity-100 focus:opacity-100"
          @click="toggleUiPanel"
          :title="i18nMessages.readingDisplaySettings"
        >
          <span class="sr-only">{{ i18nMessages.readingDisplaySettings }}</span>
          <svg
            class="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065Z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
            />
          </svg>
        </button>
      </div>

      <div class="pointer-events-none flex flex-1 items-center justify-center">
        <span
          v-if="showComposer"
          class="font-serif text-[13px] tracking-[0.35em] text-inkLight/40"
          >OpenVoca</span
        >
      </div>

      <div class="flex flex-1 items-center justify-end">
        <router-link
          to="/stats"
          class="cursor-pointer rounded-full px-3 py-2 transition-colors hover:text-ink"
        >
          {{ i18nMessages.stats }}
        </router-link>
      </div>
    </header>

    <ReadingSettingsBar
      v-if="isUiPanelOpen"
      :settings="readingUiSettings"
      :messages="i18nMessages"
      @close="closeUiPanel"
      @update:settings="onReadingSettingsChange"
    />

    <main
      class="flex min-h-zoom-screen flex-col items-center justify-center px-8 py-24"
      :class="showComposer ? 'gap-14' : 'gap-7'"
    >
      <template v-if="showComposer">
        <ComposerCard @generate="onComposerGenerate" />
        <Transition name="fade">
          <p
            v-if="composerError"
            class="flex items-center gap-2 text-sm text-red-500/80"
          >
            <svg
              class="h-4 w-4 shrink-0"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
              />
            </svg>
            <span>{{ composerError }}</span>
            <router-link
              to="/settings"
              class="ml-1 underline underline-offset-2 hover:text-red-500 transition-colors"
              >{{ i18nMessages.goToSettings }}</router-link
            >
          </p>
        </Transition>

        <!-- Footer links -->
        <div class="flex items-center gap-4 text-inkLight/25">
          <a
            href="https://github.com/Maribbit/openvoca"
            target="_blank"
            rel="noopener noreferrer"
            class="transition-colors hover:text-inkLight/60"
            title="GitHub"
          >
            <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
              <path
                d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12Z"
              />
            </svg>
          </a>
          <button
            type="button"
            class="cursor-pointer transition-colors hover:text-inkLight/60"
            :title="i18nMessages.aboutOpenVoca"
            @click="showAbout = true"
          >
            <svg
              class="h-4 w-4"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M11.25 11.25l.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"
              />
            </svg>
          </button>
        </div>
      </template>

      <template v-else>
        <div
          v-if="isRiddleMode && !isLoading && !errorMessage"
          class="flex w-full flex-col items-center gap-8"
        >
          <div class="flex w-full flex-col items-center gap-4">
            <div
              v-if="riddleClueTokens.length > 0"
              class="flex w-full max-w-3xl flex-col items-center gap-1.5"
            >
              <p
                class="text-[10px] font-semibold uppercase tracking-[0.16em] text-inkLight/55"
              >
                {{ i18nMessages.riddleClue }}
              </p>
              <SentenceDisplay
                :tokens="riddleClueTokens"
                :marked-words="markedWords"
                :is-loading="false"
                error-message=""
                loading-text=""
                :typography-class="riddleClueTypographyClass"
                @word-click="onWordClick"
              />
            </div>
            <SentenceDisplay
              :tokens="riddleQuestionTokens"
              :marked-words="markedWords"
              :is-loading="false"
              error-message=""
              loading-text=""
              :typography-class="sentenceTypographyClass"
              @word-click="onWordClick"
            />
          </div>
          <Transition name="fade">
            <div
              v-if="answerRevealed"
              class="flex w-full max-w-3xl flex-col items-center gap-3 rounded-lg border border-ink/6 bg-surface/55 px-5 py-5 shadow-sm dark:border-white/8 dark:bg-white/5"
            >
              <p class="text-sm font-semibold text-inkLight">
                {{ i18nMessages.riddleAnswer }}
              </p>
              <SentenceDisplay
                :tokens="riddleAnswerTokens"
                :marked-words="markedWords"
                :is-loading="false"
                error-message=""
                loading-text=""
                :typography-class="sentenceTypographyClass"
                @word-click="onWordClick"
              />
            </div>
          </Transition>
        </div>
        <SentenceDisplay
          v-else
          :tokens="tokens"
          :marked-words="markedWords"
          :is-loading="isLoading"
          :error-message="errorMessage"
          :loading-text="loadingText"
          :loading-progress="loadingProgress"
          :typography-class="sentenceTypographyClass"
          @word-click="onWordClick"
        />

        <div v-if="visibleTokens.length > 0" class="flex items-center gap-1">
          <button
            type="button"
            class="cursor-pointer rounded-full p-2 transition-colors hover:bg-black/4"
            :class="
              copyConfirmed
                ? 'text-emerald-500'
                : 'text-inkLight/40 hover:text-inkLight'
            "
            :title="i18nMessages.copySentence"
            @click="copySentence"
          >
            <svg
              v-if="!copyConfirmed"
              class="h-4 w-4"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9.75a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184"
              />
            </svg>
            <svg
              v-else
              class="h-4 w-4"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M4.5 12.75l6 6 9-13.5"
              />
            </svg>
          </button>
          <button
            type="button"
            class="cursor-pointer rounded-full p-2 transition-colors hover:bg-black/4"
            :class="
              isSpeaking || ttsLoading
                ? 'text-ink'
                : 'text-inkLight/40 hover:text-inkLight'
            "
            :title="i18nMessages.readAloud"
            @click="readAloud"
          >
            <svg
              v-if="ttsLoading"
              class="h-4 w-4 animate-pulse"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z"
              />
            </svg>
            <svg
              v-else-if="!isSpeaking"
              class="h-4 w-4"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z"
              />
            </svg>
            <svg v-else class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
              <path
                fill-rule="evenodd"
                d="M4.5 7.5a3 3 0 0 1 3-3h9a3 3 0 0 1 3 3v9a3 3 0 0 1-3 3h-9a3 3 0 0 1-3-3v-9Z"
                clip-rule="evenodd"
              />
            </svg>
          </button>
        </div>

        <div class="flex flex-col items-center">
          <button
            v-if="isRiddleMode && !answerRevealed"
            @click="answerRevealed = true"
            class="group relative flex items-center justify-center gap-2 rounded-full border border-ink/10 bg-ink/5 px-8 py-3 text-[15px] font-medium tracking-wide text-ink shadow-none transition-all hover:bg-ink/8 hover:shadow-sm active:scale-[0.99] dark:border-white/10 dark:bg-white/8 dark:hover:bg-white/12"
          >
            <span>{{ i18nMessages.revealAnswer }}</span>
          </button>
          <button
            v-else
            @click="openProgressSummary"
            :disabled="isLoading || isDrafting || isUiPanelOpen"
            class="group relative flex items-center justify-center gap-2 rounded-full border border-ink/10 bg-ink/5 px-8 py-3 text-[15px] font-medium tracking-wide text-ink shadow-none transition-all hover:bg-ink/8 hover:shadow-sm active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-75 dark:border-white/10 dark:bg-white/8 dark:hover:bg-white/12"
          >
            <svg
              v-if="isDrafting"
              class="animate-spin -ml-1 mr-2 h-4 w-4 text-ink"
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
            <span>{{
              i18nMessages.reviewProgressBtn || "Review Progress"
            }}</span>
            <kbd
              v-if="!isDrafting"
              class="rounded border border-ink/15 bg-ink/8 px-2 py-0.5 font-mono text-xs font-semibold text-inkLight transition-colors dark:border-white/15 dark:bg-white/10"
              >Space</kbd
            >
          </button>
        </div>
      </template>
    </main>

    <DefinitionToast
      :entry="definitionEntry"
      :not-found-word="definitionNotFound"
      :loading-word="definitionWord"
      :lemma="currentDefinitionLemma"
      :lemma-label="i18nMessages.lemmaLabel"
      :not-found-text="i18nMessages.definitionNotFound"
      :edit-lemma-label="i18nMessages.editLemma"
      :know-text="i18nMessages.definitionKnow"
      :dont-know-text="i18nMessages.definitionDontKnow"
      :is-marked="isCurrentWordMarked"
      :display-mode="dictionaryDisplayMode"
      :pronounce-label="i18nMessages.pronounceWord"
      @mark="onDefinitionMark"
      @lemma-change="onDefinitionLemmaChange"
    />

    <Transition name="fade">
      <p
        v-if="feedbackError"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 rounded-lg bg-red-600 px-4 py-2 text-sm text-white shadow-lg"
      >
        {{ feedbackError }}
      </p>
    </Transition>

    <ProgressSummaryModal
      v-if="isSummaryModalOpen"
      :words="wordStatusList"
      :is-submitting="isSubmittingFeedback || isDrafting"
      :messages="i18nMessages"
      @submit="goToNextSentence"
      @cancel="isSummaryModalOpen = false"
      @lemma-change="onProgressLemmaChange"
    />

    <!-- About modal -->
    <Transition name="fade">
      <div
        v-if="showAbout"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        @click.self="showAbout = false"
      >
        <div
          class="mx-4 w-full max-w-sm rounded-2xl border border-black/5 bg-surface p-6 shadow-lg dark:border-white/5"
        >
          <div class="text-center">
            <h2 class="font-serif text-xl tracking-wide text-ink">OpenVoca</h2>
            <p class="mt-1 text-xs text-inkLight">
              {{ i18nMessages.aboutTagline }}
            </p>
            <p class="mt-3 text-xs leading-relaxed text-inkLight/70">
              {{ i18nMessages.aboutDescription }}
            </p>
          </div>
          <hr class="my-4 border-ink/5 dark:border-white/5" />
          <p
            class="mb-3 text-[10px] font-semibold uppercase tracking-wider text-inkLight/40"
          >
            {{ i18nMessages.howItWorks }}
          </p>
          <div class="flex flex-col gap-3">
            <div
              v-for="(step, i) in [
                {
                  title: i18nMessages.onboardingStep1Title,
                  desc: i18nMessages.onboardingStep1Desc,
                },
                {
                  title: i18nMessages.onboardingStep2Title,
                  desc: i18nMessages.onboardingStep2Desc,
                },
                {
                  title: i18nMessages.onboardingStep3Title,
                  desc: i18nMessages.onboardingStep3Desc,
                },
              ]"
              :key="i"
              class="flex gap-3"
            >
              <span
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-ink/8 font-mono text-[10px] font-semibold text-ink dark:bg-white/10"
                >{{ i + 1 }}</span
              >
              <div class="min-w-0">
                <p class="text-xs font-semibold text-ink">{{ step.title }}</p>
                <p class="mt-0.5 text-[11px] leading-relaxed text-inkLight/60">
                  {{ step.desc }}
                </p>
              </div>
            </div>
          </div>
          <div class="mt-5 flex items-center justify-center gap-3">
            <span class="font-mono text-[10px] text-inkLight/40"
              >v{{ appVersion }}</span
            >
            <a
              href="https://github.com/Maribbit/openvoca"
              target="_blank"
              rel="noopener noreferrer"
              class="text-inkLight/40 transition-colors hover:text-inkLight"
              title="GitHub"
            >
              <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                <path
                  d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12Z"
                />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
  import {
    computed,
    onActivated,
    onDeactivated,
    onMounted,
    onUnmounted,
    ref,
  } from "vue";

  import {
    fetchNextReadingSentenceStream,
    fetchDefinition,
    submitFeedback,
    submitFeedbackDraft,
    tokensToPlainText,
    type DictionaryEntry,
    type FeedbackRequest,
    type ReadingMode,
    type ReadingRiddle,
    type ReadingSentenceToken,
  } from "../api/reading";
  import { useLemmaOverrides } from "../composables/useLemmaOverrides";
  import { useI18n } from "../composables/useI18n";
  import { useSettings } from "../composables/useSettings";
  import ComposerCard from "../components/ComposerCard.vue";
  import DefinitionToast from "../components/DefinitionToast.vue";
  import type { DictionaryDisplayMode } from "../components/DefinitionToast.vue";
  import ProgressSummaryModal, {
    type WordProgress,
  } from "../components/ProgressSummaryModal.vue";
  import ReadingSettingsBar from "../components/ReadingSettingsBar.vue";
  import type {
    ReadingUiSettings,
    ThemeOption,
  } from "../components/ReadingSettingsBar.vue";
  import SentenceDisplay from "../components/SentenceDisplay.vue";

  defineOptions({ name: "HomeView" });

  type FontSizeOption = "sm" | "md" | "lg";
  type SpacingOption = "tight" | "normal" | "loose";
  type UiFontSizeOption = "xs" | "sm" | "md" | "lg" | "xl";

  const FONT_SIZE_OPTIONS: FontSizeOption[] = ["sm", "md", "lg"];
  const SPACING_OPTIONS: SpacingOption[] = ["tight", "normal", "loose"];
  const THEME_OPTIONS: ThemeOption[] = ["light", "dark"];

  const DEFAULT_READING_UI_SETTINGS: ReadingUiSettings = {
    fontSize: "md",
    spacing: "normal",
    theme: "light",
  };

  const { get, set } = useSettings();
  const lemmaOverrides = useLemmaOverrides();

  const appVersion = __APP_VERSION__;
  const readingMode = ref<ReadingMode>("sentence");
  const sentence = ref("");
  const tokens = ref<ReadingSentenceToken[]>([]);
  const riddle = ref<ReadingRiddle | null>(null);
  const answerRevealed = ref(false);
  const originalTargets = ref<string[]>([]);
  const errorMessage = ref("");
  const composerError = ref("");
  const feedbackError = ref("");
  const isLoading = ref(false);
  const isDrafting = ref(false);
  const isSubmittingFeedback = ref(false);
  const loadingProgress = ref<string | null>(null);
  const isUiPanelOpen = ref(false);
  const markedWords = ref<Set<string>>(new Set());
  const showComposer = ref(true);
  const showAbout = ref(false);
  const copyConfirmed = ref(false);
  const isSpeaking = ref(false);
  const ttsLoading = ref(false);
  let ttsAudio: HTMLAudioElement | null = null;

  const isSummaryModalOpen = ref(false);
  const wordStatusList = ref<WordProgress[]>([]);

  const definitionEntry = ref<DictionaryEntry | null>(null);
  const definitionWord = ref<string | null>(null);
  const definitionNotFound = ref<string | null>(null);
  const definitionToken = ref<ReadingSentenceToken | null>(null);
  let wordClickedThisFrame = false;

  const isCurrentWordMarked = computed(() => {
    if (!definitionToken.value) return false;
    return markedWords.value.has(tokenKey(definitionToken.value));
  });

  const currentDefinitionLemma = computed(() => {
    if (definitionToken.value) {
      return lemmaOverrides.effectiveLemma(definitionToken.value);
    }
    return definitionWord.value;
  });

  const readingUiSettings = ref<ReadingUiSettings>(loadReadingUiSettings());
  const uiFontSize = ref<UiFontSizeOption>(loadUiFontSize());
  const { messages: i18nMessages } = useI18n();

  const dictionaryDisplayMode = computed<DictionaryDisplayMode>(() => {
    const v = get("dictionary", "display", "");
    if (v === "zh" || v === "en" || v === "both") return v;
    return window.navigator.language.toLowerCase().startsWith("zh")
      ? "both"
      : "en";
  });

  const sentenceTypographyClass = computed(() => {
    const fontSizeMap: Record<FontSizeOption, string> = {
      sm: "text-[1.55rem] md:text-[2.0rem]",
      md: "text-[1.7rem] md:text-[2.2rem]",
      lg: "text-[1.85rem] md:text-[2.45rem]",
    };

    const spacingMap: Record<SpacingOption, string> = {
      tight: "leading-[1.5] tracking-[0.005em]",
      normal: "leading-[1.62] tracking-[0.012em]",
      loose: "leading-[1.75] tracking-[0.02em]",
    };

    return `${fontSizeMap[readingUiSettings.value.fontSize]} ${spacingMap[readingUiSettings.value.spacing]}`;
  });

  const isRiddleMode = computed(
    () => readingMode.value === "riddle" && riddle.value !== null,
  );

  const riddleClueTypographyClass =
    "text-[1.05rem] md:text-[1.2rem] leading-[1.55] tracking-normal";
  const riddleClueTokens = computed(() => riddle.value?.clueTokens ?? []);
  const riddleQuestionTokens = computed(
    () => riddle.value?.questionTokens ?? [],
  );
  const riddleAnswerTokens = computed(() => riddle.value?.answerTokens ?? []);
  const loadingText = computed(() =>
    readingMode.value === "riddle"
      ? i18nMessages.value.loadingRiddle
      : i18nMessages.value.loadingSentence,
  );

  const visibleTokens = computed(() => {
    if (!isRiddleMode.value) return tokens.value;
    return answerRevealed.value
      ? [
          ...riddleClueTokens.value,
          ...riddleQuestionTokens.value,
          ...riddleAnswerTokens.value,
        ]
      : [...riddleClueTokens.value, ...riddleQuestionTokens.value];
  });

  const uiHeaderSizeClass = computed(() => {
    const map: Record<UiFontSizeOption, string> = {
      xs: "text-[11px]",
      sm: "text-[12px]",
      md: "text-[13px]",
      lg: "text-[14px]",
      xl: "text-[15px]",
    };
    return map[uiFontSize.value];
  });

  // --- Persistence helpers ---

  function loadReadingUiSettings(): ReadingUiSettings {
    const fs = get("reading", "fontSize", "md");
    const sp = get("reading", "spacing", "normal");
    const th = get("reading", "theme", "light");
    return {
      fontSize: FONT_SIZE_OPTIONS.includes(fs as FontSizeOption)
        ? (fs as FontSizeOption)
        : DEFAULT_READING_UI_SETTINGS.fontSize,
      spacing: SPACING_OPTIONS.includes(sp as SpacingOption)
        ? (sp as SpacingOption)
        : DEFAULT_READING_UI_SETTINGS.spacing,
      theme: THEME_OPTIONS.includes(th as ThemeOption)
        ? (th as ThemeOption)
        : DEFAULT_READING_UI_SETTINGS.theme,
    };
  }

  function saveReadingUiSettings(): void {
    const s = readingUiSettings.value;
    set("reading", {
      fontSize: s.fontSize,
      spacing: s.spacing,
      theme: s.theme,
    });
  }

  function loadUiFontSize(): UiFontSizeOption {
    const saved = get("interface", "uiFontSize", "sm");
    const valid: UiFontSizeOption[] = ["xs", "sm", "md", "lg", "xl"];
    if (valid.includes(saved as UiFontSizeOption))
      return saved as UiFontSizeOption;
    return "sm";
  }

  function applyTheme(theme: ThemeOption): void {
    if (typeof window === "undefined") return;
    window.document.documentElement.setAttribute("data-theme", theme);
  }

  // --- UI panel ---

  function toggleUiPanel(): void {
    isUiPanelOpen.value = !isUiPanelOpen.value;
  }

  function closeUiPanel(): void {
    isUiPanelOpen.value = false;
  }

  function copySentence(): void {
    navigator.clipboard.writeText(tokensToPlainText(visibleTokens.value));
    copyConfirmed.value = true;
    setTimeout(() => {
      copyConfirmed.value = false;
    }, 1500);
  }

  function stopTts(): void {
    if (ttsAudio) {
      ttsAudio.pause();
      ttsAudio.src = "";
      ttsAudio = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    isSpeaking.value = false;
    ttsLoading.value = false;
  }

  function readAloudBrowser(text: string): void {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.onend = () => {
      isSpeaking.value = false;
    };
    isSpeaking.value = true;
    window.speechSynthesis.speak(utterance);
  }

  function readAloud(): void {
    if (isSpeaking.value || ttsLoading.value) {
      stopTts();
      return;
    }
    const text = tokensToPlainText(visibleTokens.value);
    if (!text) return;
    stopTts();
    ttsLoading.value = true;
    const params = new URLSearchParams({ text });
    const audio = new Audio(`/api/tts?${params.toString()}`);
    ttsAudio = audio;
    audio.onplaying = () => {
      ttsLoading.value = false;
      isSpeaking.value = true;
    };
    audio.onended = () => {
      ttsAudio = null;
      isSpeaking.value = false;
    };
    audio.onerror = () => {
      ttsAudio = null;
      ttsLoading.value = false;
      // Fallback to browser TTS
      if (window.speechSynthesis) {
        readAloudBrowser(text);
      }
    };
    audio.play().catch(() => {
      ttsAudio = null;
      ttsLoading.value = false;
      // Fallback to browser TTS
      if (window.speechSynthesis) {
        readAloudBrowser(text);
      }
    });
  }

  function onReadingSettingsChange(next: ReadingUiSettings): void {
    readingUiSettings.value = next;
    applyTheme(next.theme);
    saveReadingUiSettings();
  }

  // --- Sentence & feedback ---

  function tokenKey(token: ReadingSentenceToken): string {
    return `${token.text.toLowerCase()}/${token.pos ?? ""}`;
  }

  function dismissDefinition(): void {
    definitionEntry.value = null;
    definitionWord.value = null;
    definitionNotFound.value = null;
    definitionToken.value = null;
  }

  async function showDefinitionForToken(
    token: ReadingSentenceToken,
  ): Promise<void> {
    const word = lemmaOverrides.effectiveLemma(token);
    definitionWord.value = word;
    definitionToken.value = token;
    definitionNotFound.value = null;
    definitionEntry.value = null;
    try {
      const entry = await fetchDefinition(word);
      if (definitionWord.value === word) {
        definitionEntry.value = entry;
        definitionNotFound.value = entry ? null : word;
      }
    } catch {
      if (definitionWord.value === word) {
        definitionEntry.value = null;
        definitionNotFound.value = word;
      }
    }
  }

  async function onWordClick(token: ReadingSentenceToken): Promise<void> {
    wordClickedThisFrame = true;

    // If the same word is already showing, toggle know/don't-know
    if (
      definitionToken.value &&
      tokenKey(definitionToken.value) === tokenKey(token)
    ) {
      onDefinitionMark(!isCurrentWordMarked.value);
      return;
    }

    await showDefinitionForToken(token);
  }

  async function onDefinitionLemmaChange(newLemma: string): Promise<void> {
    if (!definitionToken.value || !currentDefinitionLemma.value) return;
    const oldLemma = currentDefinitionLemma.value;
    if (!lemmaOverrides.setOverride(oldLemma, newLemma, "dictionary")) return;
    await showDefinitionForToken(definitionToken.value);
  }

  function onDefinitionMark(marked: boolean): void {
    if (!definitionToken.value) return;
    const key = tokenKey(definitionToken.value);
    const next = new Set(markedWords.value);
    if (marked) {
      next.add(key);
    } else {
      next.delete(key);
    }
    markedWords.value = next;
  }

  function onDocumentClick(): void {
    if (wordClickedThisFrame) {
      wordClickedThisFrame = false;
      return;
    }
    if (
      definitionEntry.value ||
      definitionNotFound.value ||
      definitionWord.value
    ) {
      dismissDefinition();
    }
  }

  let elapsedTimer: ReturnType<typeof setInterval> | null = null;

  function startElapsedTimer(): void {
    let seconds = 0;
    loadingProgress.value = "0s";
    elapsedTimer = setInterval(() => {
      seconds += 1;
      loadingProgress.value = `${seconds}s`;
    }, 1000);
  }

  function stopElapsedTimer(): void {
    if (elapsedTimer !== null) {
      clearInterval(elapsedTimer);
      elapsedTimer = null;
    }
  }

  function generationErrorDetail(error: unknown): string | null {
    if (!(error instanceof Error)) return null;
    const message = error.message.trim();
    if (
      !message ||
      message === "Failed to fetch" ||
      message === "No response received."
    ) {
      return null;
    }
    return message;
  }

  async function loadSentence(
    prompt: string,
    targetWords: string[],
    mode: ReadingMode,
  ): Promise<void> {
    isLoading.value = true;
    loadingProgress.value = null;
    errorMessage.value = "";
    readingMode.value = mode;
    riddle.value = null;
    answerRevealed.value = false;
    startElapsedTimer();
    try {
      await fetchNextReadingSentenceStream(
        { prompt, targetWords, mode },
        {
          onProgress(wordCount: number) {
            stopElapsedTimer();
            loadingProgress.value = `${wordCount} ${wordCount === 1 ? i18nMessages.value.wordSingular : i18nMessages.value.wordPlural}`;
          },
          onComplete(response) {
            readingMode.value = response.mode ?? mode;
            sentence.value = response.sentence;
            tokens.value = response.tokens;
            riddle.value = response.riddle ?? null;
            answerRevealed.value = false;
            originalTargets.value = response.words ?? [];
            markedWords.value = new Set();
            lemmaOverrides.clearOverrides();
            dismissDefinition();
          },
          onError(detail: string) {
            throw new Error(detail);
          },
        },
      );
      if (!sentence.value) {
        throw new Error("No response received.");
      }
    } catch (error) {
      showComposer.value = true;
      composerError.value =
        generationErrorDetail(error) ?? i18nMessages.value.connectionError;
      tokens.value = [];
      riddle.value = null;
      answerRevealed.value = false;
      lemmaOverrides.clearOverrides();
    } finally {
      stopElapsedTimer();
      isLoading.value = false;
      loadingProgress.value = null;
    }
  }

  function buildFeedbackRequest(): FeedbackRequest {
    const feedbackTokens = visibleTokens.value;
    const targetEntries = lemmaOverrides.uniqueEffectiveLemmas(
      feedbackTokens.filter((token) => token.isTarget && token.isWord),
    );
    const markedEntries = lemmaOverrides.uniqueEffectiveLemmas(
      feedbackTokens.filter(
        (token) => token.isWord && markedWords.value.has(tokenKey(token)),
      ),
    );
    const originalTargetsRef = lemmaOverrides.uniqueEffectiveLemmas(
      originalTargets.value,
    );

    return {
      targetWords: targetEntries,
      markedWords: markedEntries,
      sentence: tokensToPlainText(feedbackTokens),
      originalTargets: originalTargetsRef,
    };
  }

  function progressTypeForDelta(
    delta: {
      lemma: string;
      old_level: number;
      new_level: number;
      is_new: boolean;
    },
    markedEntries: string[],
  ): "recognized" | "unknown" | "new" {
    if (delta.is_new) return "new";
    if (delta.new_level < delta.old_level) return "unknown";
    if (delta.new_level > delta.old_level) return "recognized";
    return markedEntries.includes(delta.lemma) ? "unknown" : "recognized";
  }

  async function fetchWordProgressDraft(): Promise<WordProgress[]> {
    const request = buildFeedbackRequest();
    const allRelevantLemmas = Array.from(
      new Set([
        ...request.targetWords,
        ...request.markedWords,
        ...(request.originalTargets ?? []),
      ]),
    );

    if (allRelevantLemmas.length === 0) return [];

    const deltas = await submitFeedbackDraft(request);

    return deltas.map((delta) => ({
      lemma: delta.lemma,
      currentLevel: delta.is_new ? undefined : delta.old_level,
      newLevel: delta.new_level,
      type: progressTypeForDelta(delta, request.markedWords),
    }));
  }

  async function openProgressSummary(): Promise<void> {
    if (isLoading.value || isDrafting.value || isSubmittingFeedback.value)
      return;

    if (tokens.value.length === 0) return;
    if (isRiddleMode.value && !answerRevealed.value) return;

    isDrafting.value = true;
    try {
      wordStatusList.value = await fetchWordProgressDraft();
      isSummaryModalOpen.value = true;
    } catch (e) {
      console.error("Failed to fetch vocabulary for summary modal:", e);
      // Fallback
      await goToNextSentence();
    } finally {
      isDrafting.value = false;
    }
  }

  async function onProgressLemmaChange(
    oldLemma: string,
    newLemma: string,
  ): Promise<void> {
    if (!lemmaOverrides.setOverride(oldLemma, newLemma, "progress")) return;
    isDrafting.value = true;
    try {
      wordStatusList.value = await fetchWordProgressDraft();
    } catch {
      feedbackError.value = i18nMessages.value.feedbackError;
      setTimeout(() => {
        feedbackError.value = "";
      }, 4000);
    } finally {
      isDrafting.value = false;
    }
  }

  async function goToNextSentence(): Promise<void> {
    if (isLoading.value || isSubmittingFeedback.value) return;

    isSubmittingFeedback.value = true;
    try {
      if (sentence.value) {
        try {
          await submitFeedback(buildFeedbackRequest());
        } catch {
          feedbackError.value = i18nMessages.value.feedbackError;
          setTimeout(() => {
            feedbackError.value = "";
          }, 4000);
        }
      }
    } finally {
      isSubmittingFeedback.value = false;
      isSummaryModalOpen.value = false;
    }

    showComposer.value = true;
    riddle.value = null;
    answerRevealed.value = false;
    readingMode.value = "sentence";
    closeUiPanel();
    dismissDefinition();
    lemmaOverrides.clearOverrides();
    stopTts();
  }

  async function onComposerGenerate(
    prompt: string,
    targetWords: string[],
    mode: ReadingMode = "sentence",
  ): Promise<void> {
    composerError.value = "";
    showComposer.value = false;
    await loadSentence(prompt, targetWords, mode);
  }

  // --- Keyboard ---

  function handleKeydown(event: KeyboardEvent): void {
    if (event.code === "Space" && !isUiPanelOpen.value && !showComposer.value) {
      const target = event.target as HTMLElement;
      if (target.tagName === "TEXTAREA" || target.tagName === "INPUT") return;
      event.preventDefault();
      if (
        !event.repeat &&
        !isSummaryModalOpen.value &&
        tokens.value.length > 0
      ) {
        if (isRiddleMode.value && !answerRevealed.value) {
          answerRevealed.value = true;
        } else {
          openProgressSummary();
        }
      }
    }
  }

  function handleKeyup(): void {
    // Space handled in keydown for opening, modal handles inside for submission
  }

  // --- Lifecycle ---

  let routeListenersAttached = false;

  function syncReadingUiSettingsFromStore(): void {
    readingUiSettings.value = loadReadingUiSettings();
    uiFontSize.value = loadUiFontSize();
    applyTheme(readingUiSettings.value.theme);
  }

  function attachRouteListeners(): void {
    if (routeListenersAttached) return;
    window.addEventListener("keydown", handleKeydown);
    window.addEventListener("keyup", handleKeyup);
    document.addEventListener("click", onDocumentClick);
    routeListenersAttached = true;
  }

  function detachRouteListeners(): void {
    if (!routeListenersAttached) return;
    window.removeEventListener("keydown", handleKeydown);
    window.removeEventListener("keyup", handleKeyup);
    document.removeEventListener("click", onDocumentClick);
    routeListenersAttached = false;
  }

  onMounted(() => {
    syncReadingUiSettingsFromStore();
    attachRouteListeners();
  });

  onActivated(() => {
    syncReadingUiSettingsFromStore();
    attachRouteListeners();
  });

  onDeactivated(() => {
    closeUiPanel();
    dismissDefinition();
    detachRouteListeners();
  });

  onUnmounted(() => {
    stopElapsedTimer();
    detachRouteListeners();
  });
</script>
