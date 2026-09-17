<template>
  <div class="min-h-zoom-screen bg-paper px-8 pb-32 pt-10 text-ink antialiased">
    <div class="mx-auto max-w-3xl">
      <!-- Kept first in the document so the heading still leads the page for
           assistive tech; the visible label lives in the dock below. -->
      <h1 class="sr-only">{{ i18nMessages.settings }}</h1>

      <div class="space-y-10">
        <!-- ===== Interface ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div class="border-b border-black/5 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.interfaceSection }}
            </h2>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-1 gap-x-8 gap-y-5 sm:grid-cols-2">
              <!-- Language -->
              <div>
                <span class="mb-3 block text-sm font-medium text-ink">
                  {{ i18nMessages.language }}
                </span>
                <div
                  class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
                >
                  <button
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-sm transition-all"
                    :class="toggleClass(locale === 'en')"
                    @click="switchLanguage('en')"
                  >
                    English
                  </button>
                  <button
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-sm transition-all"
                    :class="toggleClass(locale === 'zh')"
                    @click="switchLanguage('zh')"
                  >
                    中文
                  </button>
                </div>
              </div>

              <!-- Theme -->
              <div>
                <span class="mb-3 block text-sm font-medium text-ink">
                  {{ i18nMessages.theme }}
                </span>
                <div
                  class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
                >
                  <button
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-sm transition-all"
                    :class="toggleClass(currentTheme === 'light')"
                    @click="setTheme('light')"
                  >
                    {{ i18nMessages.themeLight }}
                  </button>
                  <button
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-sm transition-all"
                    :class="toggleClass(currentTheme === 'dark')"
                    @click="setTheme('dark')"
                  >
                    {{ i18nMessages.themeDark }}
                  </button>
                </div>
              </div>

              <!-- Color Theme -->
              <div>
                <span class="mb-3 block text-sm font-medium text-ink">
                  {{ i18nMessages.colorTheme }}
                </span>
                <div
                  class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
                >
                  <button
                    v-for="opt in COLOR_THEME_OPTIONS"
                    :key="opt"
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-sm transition-all"
                    :class="toggleClass(colorTheme === opt)"
                    @click="setColorTheme(opt)"
                  >
                    {{
                      i18nMessages[
                        `colorTheme_${opt}` as keyof typeof i18nMessages
                      ]
                    }}
                  </button>
                </div>
              </div>

              <!-- UI Size -->
              <div>
                <label
                  class="mb-3 flex items-center gap-1.5 text-sm font-medium text-ink"
                >
                  {{ i18nMessages.uiSize }}
                  <button
                    type="button"
                    class="flex h-4 w-4 cursor-pointer items-center justify-center rounded-full border border-black/10 text-[10px] text-inkLight transition-colors hover:bg-black/4 hover:text-ink"
                    @click="showZoomHint = !showZoomHint"
                    :title="i18nMessages.uiSizeHint"
                  >
                    ?
                  </button>
                </label>
                <!-- Five fixed-width options slightly exceeded the column on a
                     phone. They share the available width until there is room to
                     size to their labels again. -->
                <div
                  class="flex w-full rounded-xl border border-black/8 bg-paper p-1 sm:inline-flex sm:w-auto"
                >
                  <button
                    v-for="opt in uiFontSizeOptions"
                    :key="opt.value"
                    type="button"
                    class="flex h-8 min-w-0 flex-1 items-center justify-center rounded-lg px-2 transition-all sm:flex-none sm:px-2.5"
                    :class="toggleClass(uiFontSize === opt.value)"
                    @click="setUiFontSize(opt.value)"
                  >
                    <span class="text-xs font-medium">{{ opt.label }}</span>
                  </button>
                </div>
                <p v-if="showZoomHint" class="mt-2 text-xs text-inkLight">
                  {{ i18nMessages.uiSizeHint }}
                </p>
              </div>
            </div>
          </div>
        </section>

        <!-- ===== LLM Provider ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div class="border-b border-black/5 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.llmProvider }}
            </h2>
            <p class="mt-1 text-xs text-inkLight/70">
              {{ i18nMessages.llmProviderHint }}
            </p>
          </div>
          <div class="space-y-5 p-6">
            <!-- Endpoint & Model -->
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div class="flex flex-col gap-2">
                <label
                  class="flex items-center gap-1.5 text-sm font-medium text-ink"
                >
                  {{ i18nMessages.endpoint }}
                  <button
                    type="button"
                    class="flex h-4 w-4 items-center justify-center rounded-full border border-black/10 text-[10px] text-inkLight transition-colors hover:bg-black/4 hover:text-ink cursor-pointer"
                    @click="showEndpointHint = !showEndpointHint"
                    :title="i18nMessages.endpointHint"
                  >
                    ?
                  </button>
                </label>
                <input
                  v-model="providerEndpoint"
                  type="text"
                  placeholder="http://localhost:11434"
                  class="rounded-xl border border-black/8 bg-paper px-4 py-2.5 font-mono text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight"
                  @change="saveProvider"
                />
                <p v-if="showEndpointHint" class="text-xs text-inkLight">
                  {{ i18nMessages.endpointHint }}
                </p>
              </div>
              <div class="flex flex-col gap-2">
                <label class="text-sm font-medium text-ink">
                  {{ i18nMessages.model }}
                </label>
                <input
                  v-model="selectedModel"
                  data-testid="provider-model-input"
                  type="text"
                  :placeholder="i18nMessages.modelPlaceholder"
                  class="rounded-xl border border-black/8 bg-paper px-4 py-2.5 text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight"
                  @change="saveProvider"
                />
              </div>
            </div>

            <!-- API Key -->
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-ink">
                {{ i18nMessages.apiKey }}
              </label>
              <!-- The field and the actions share a row only when it fits. Three
                   fixed-width controls in a row overflowed the card on a phone,
                   and the masked hint was squeezed onto two lines. -->
              <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
                <!-- Stored: read-only. The hint is text, never an input value,
                     so it can never be written back as if it were the key. -->
                <div
                  v-if="apiKeySet"
                  data-testid="provider-key-status"
                  class="flex items-center gap-2 rounded-xl border border-black/8 bg-black/3 px-4 py-2.5 text-sm dark:border-white/10 dark:bg-white/5 sm:min-w-0 sm:flex-1"
                >
                  <span class="text-inkLight">
                    {{ i18nMessages.apiKeyConfigured }}
                  </span>
                  <span class="font-mono text-ink">{{ apiKeyHint }}</span>
                </div>
                <input
                  v-else
                  v-model="providerKeyDraft"
                  data-testid="provider-key-input"
                  type="password"
                  :placeholder="i18nMessages.apiKeyPlaceholder"
                  class="min-w-0 rounded-xl border border-black/8 bg-paper px-4 py-2.5 text-sm transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight sm:flex-1"
                />
                <div class="flex gap-2 sm:shrink-0">
                  <button
                    v-if="apiKeySet"
                    type="button"
                    data-testid="provider-key-clear"
                    class="flex-1 whitespace-nowrap rounded-xl border border-black/15 px-4 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-black/4 active:bg-black/8 dark:border-white/15 dark:hover:bg-white/8 sm:flex-none"
                    @click="confirmClearProviderKey"
                  >
                    {{ i18nMessages.apiKeyClear }}
                  </button>
                  <button
                    v-else
                    type="button"
                    data-testid="provider-key-save"
                    class="flex-1 whitespace-nowrap rounded-xl border border-black/15 px-4 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-black/4 active:bg-black/8 dark:border-white/15 dark:hover:bg-white/8 sm:flex-none"
                    :disabled="!providerKeyDraft || savingKey"
                    @click="submitProviderKey"
                  >
                    {{ i18nMessages.apiKeySave }}
                  </button>
                  <button
                    type="button"
                    class="flex-1 whitespace-nowrap rounded-xl border border-black/15 px-4 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-black/4 active:bg-black/8 dark:border-white/15 dark:hover:bg-white/8 sm:flex-none"
                    :disabled="connectionStatus === 'testing'"
                    @click="handleTestConnection"
                  >
                    {{
                      connectionStatus === "testing"
                        ? i18nMessages.testingConnection
                        : i18nMessages.testConnection
                    }}
                  </button>
                </div>
              </div>
              <div class="flex items-center justify-between">
                <p class="text-xs text-inkLight">
                  {{ i18nMessages.apiKeyHint }}
                </p>
                <span
                  v-if="connectionStatus === 'ok'"
                  class="text-xs text-green-600"
                >
                  ✓ {{ connectionMessage }}
                </span>
                <span
                  v-else-if="connectionStatus === 'error'"
                  class="max-w-xs truncate text-xs text-red-500"
                  :title="connectionMessage"
                >
                  ✗ {{ connectionMessage }}
                </span>
              </div>
            </div>
          </div>
        </section>

        <!-- ===== Custom Request Headers ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <button
            type="button"
            data-testid="provider-headers-toggle"
            class="flex w-full items-center justify-between px-6 py-4 text-left"
            @click="showAdvanced = !showAdvanced"
          >
            <span class="text-sm font-semibold text-ink">
              {{ i18nMessages.advancedHeaders }}
            </span>
            <span class="text-xs text-inkLight">
              {{ showAdvanced ? "▾" : "▸" }}
            </span>
          </button>
          <div v-if="showAdvanced" class="space-y-4 px-6 pb-6">
            <p class="text-xs text-inkLight">
              {{ i18nMessages.advancedHeadersHint }}
            </p>
            <!-- Two inputs and a button in one row could not fit a phone: a flex
                 item will not shrink below its intrinsic width unless told to,
                 so the value field ran off the card. minmax(0,1fr) allows the
                 shrink, and the value drops to its own row while narrow. -->
            <div
              v-for="(header, index) in headerDrafts"
              :key="index"
              class="grid grid-cols-[minmax(0,1fr)_auto] gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]"
            >
              <input
                v-model="header.name"
                data-testid="provider-header-name"
                type="text"
                :placeholder="i18nMessages.headerName"
                class="col-start-1 row-start-1 min-w-0 rounded-xl border border-black/8 bg-paper px-4 py-2.5 font-mono text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight"
              />
              <input
                v-model="header.value"
                data-testid="provider-header-value"
                type="text"
                :placeholder="i18nMessages.headerValue"
                class="col-span-2 row-start-2 min-w-0 rounded-xl border border-black/8 bg-paper px-4 py-2.5 font-mono text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight sm:col-span-1 sm:col-start-2 sm:row-start-1"
              />
              <button
                type="button"
                data-testid="provider-header-remove"
                class="col-start-2 row-start-1 whitespace-nowrap rounded-xl border border-black/15 px-3.5 py-2.5 text-sm font-medium text-inkLight transition-colors hover:bg-black/4 hover:text-ink active:bg-black/8 dark:border-white/15 dark:hover:bg-white/8 sm:col-start-3 sm:px-4"
                :title="i18nMessages.removeHeader"
                :aria-label="i18nMessages.removeHeader"
                @click="removeHeader(index)"
              >
                <!-- Icon only while narrow, so the name field keeps enough width
                     to show a header name undivided. -->
                <svg
                  class="h-4 w-4 sm:hidden"
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
                <span class="hidden sm:inline">{{
                  i18nMessages.removeHeader
                }}</span>
              </button>
            </div>
            <button
              type="button"
              data-testid="provider-header-add"
              class="rounded-xl border border-black/15 px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-black/4 dark:border-white/15 dark:hover:bg-white/8"
              @click="addHeader"
            >
              + {{ i18nMessages.addHeader }}
            </button>
          </div>
        </section>

        <!-- ===== Generation Defaults ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div class="border-b border-black/5 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.generationDefaults }}
            </h2>
          </div>
          <div class="space-y-6 p-6">
            <!-- Suggestion pool size -->
            <div>
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-medium text-ink">
                  {{ i18nMessages.suggestionPoolSize }}
                </span>
                <span
                  class="rounded-full border border-black/8 bg-paper px-3 py-1 font-mono text-xs text-inkLight"
                >
                  {{ draftSuggestionPoolSize }}
                </span>
              </div>
              <input
                v-model="draftSuggestionPoolSize"
                type="range"
                min="1"
                max="6"
                step="1"
                class="w-full accent-ink"
              />
              <div
                class="mt-1 flex justify-between px-1 text-[11px] text-inkLight/70"
              >
                <span>1</span>
                <span>2</span>
                <span>3</span>
                <span>4</span>
                <span>5</span>
                <span>6</span>
              </div>
              <p class="mt-2 text-xs text-inkLight">
                {{ i18nMessages.suggestionPoolSizeHint }}
              </p>
            </div>
            <!-- Auto-selected count -->
            <div>
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-medium text-ink">
                  {{ i18nMessages.targetWordCount }}
                </span>
                <span
                  class="rounded-full border border-black/8 bg-paper px-3 py-1 font-mono text-xs text-inkLight"
                >
                  {{ draftTargetWordCount }}
                </span>
              </div>
              <input
                v-model="draftTargetWordCount"
                type="range"
                min="0"
                :max="draftSuggestionPoolSize"
                step="1"
                class="w-full accent-ink"
              />
              <div
                class="mt-1 flex justify-between px-1 text-[11px] text-inkLight/70"
              >
                <span v-for="i in draftSuggestionPoolSize + 1" :key="i">{{
                  i - 1
                }}</span>
              </div>
              <p class="mt-2 text-xs text-inkLight">
                {{ i18nMessages.targetWordCountHint }}
              </p>
            </div>
          </div>
        </section>

        <!-- ===== Dictionary ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div class="border-b border-black/5 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.dictionarySection }}
            </h2>
          </div>
          <div class="p-6">
            <div>
              <span class="mb-3 block text-sm font-medium text-ink">
                {{ i18nMessages.dictionaryDisplay }}
              </span>
              <div
                class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
              >
                <button
                  type="button"
                  class="rounded-lg px-3 py-1.5 text-sm transition-all"
                  :class="toggleClass(dictionaryDisplay === 'en')"
                  @click="setDictionaryDisplay('en')"
                >
                  {{ i18nMessages.dictionaryDisplayEn }}
                </button>
                <button
                  type="button"
                  class="rounded-lg px-3 py-1.5 text-sm transition-all"
                  :class="toggleClass(dictionaryDisplay === 'both')"
                  @click="setDictionaryDisplay('both')"
                >
                  {{ i18nMessages.dictionaryDisplayBoth }}
                </button>
                <button
                  type="button"
                  class="rounded-lg px-3 py-1.5 text-sm transition-all"
                  :class="toggleClass(dictionaryDisplay === 'zh')"
                  @click="setDictionaryDisplay('zh')"
                >
                  {{ i18nMessages.dictionaryDisplayZh }}
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- ===== Data ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div class="border-b border-black/5 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.dataSection }}
            </h2>
          </div>
          <div class="flex items-center justify-between p-6">
            <div>
              <p class="text-sm font-medium text-ink">
                {{ i18nMessages.exportVocabularySettings }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.exportVocabularySettingsDescription }}
              </p>
            </div>
            <button
              type="button"
              class="whitespace-nowrap rounded-xl border border-black/15 px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-black/4 dark:border-white/15 dark:hover:bg-white/8"
              @click="handleExportVocabulary"
            >
              {{ i18nMessages.exportVocabularySettingsButton }}
            </button>
          </div>
          <div
            class="flex items-center justify-between border-t border-black/5 p-6"
          >
            <div>
              <p class="text-sm font-medium text-ink">
                {{ i18nMessages.importVocabularySettings }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.importVocabularySettingsDescription }}
              </p>
            </div>
            <router-link
              to="/stats"
              class="whitespace-nowrap rounded-xl border border-black/15 px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-black/4 dark:border-white/15 dark:hover:bg-white/8"
            >
              {{ i18nMessages.importVocabularySettingsButton }}
            </router-link>
          </div>
          <div
            class="flex items-center justify-between border-t border-black/5 p-6"
          >
            <div>
              <p class="text-sm font-medium text-ink">
                {{ i18nMessages.exportSettings }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.exportSettingsDescription }}
              </p>
            </div>
            <button
              type="button"
              class="whitespace-nowrap rounded-xl border border-black/15 px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-black/4 dark:border-white/15 dark:hover:bg-white/8"
              @click="handleExportSettings"
            >
              {{ i18nMessages.exportSettingsButton }}
            </button>
          </div>
          <div
            class="flex items-center justify-between border-t border-black/5 p-6"
          >
            <input
              ref="settingsFileInput"
              type="file"
              accept=".json"
              class="hidden"
              @change="onSettingsFileSelected"
            />
            <div>
              <p class="text-sm font-medium text-ink">
                {{ i18nMessages.importSettings }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.importSettingsDescription }}
              </p>
            </div>
            <button
              type="button"
              class="whitespace-nowrap rounded-xl border border-black/15 px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-black/4 dark:border-white/15 dark:hover:bg-white/8"
              @click="settingsFileInput?.click()"
            >
              {{ i18nMessages.importSettingsButton }}
            </button>
          </div>
        </section>

        <!-- ===== Danger Zone ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-red-200/60 bg-surface shadow-sm"
        >
          <div class="border-b border-red-100 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-red-400"
            >
              {{ i18nMessages.dangerZone }}
            </h2>
          </div>
          <div class="flex items-center justify-between p-6">
            <div>
              <p class="text-sm font-medium text-ink">
                {{ i18nMessages.clearAllVocabulary }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.clearAllVocabularyDescription }}
              </p>
            </div>
            <button
              type="button"
              class="whitespace-nowrap rounded-xl border border-red-200 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
              @click="confirmClearVocabulary"
            >
              {{ i18nMessages.clearDatabase }}
            </button>
          </div>
          <div
            class="flex items-center justify-between border-t border-red-100 p-6"
          >
            <div>
              <p class="text-sm font-medium text-ink">
                {{ i18nMessages.clearAllSettings }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.clearAllSettingsDescription }}
              </p>
            </div>
            <button
              type="button"
              class="whitespace-nowrap rounded-xl border border-red-200 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
              @click="confirmClearSettings"
            >
              {{ i18nMessages.clearSettingsButton }}
            </button>
          </div>
        </section>
      </div>

    </div>

    <!-- Title and action sit together here, so the control stays in reach while
         the settings list scrolls instead of living in a bar at the top. -->
    <footer
      data-testid="settings-dock"
      class="fixed inset-x-0 bottom-0 z-30 border-t border-ink/8 bg-paper/95 backdrop-blur-md"
      style="padding-bottom: env(safe-area-inset-bottom, 0px)"
    >
      <div
        class="mx-auto flex w-full max-w-3xl items-center justify-between gap-3 px-4 py-2.5 sm:px-8"
      >
        <div class="min-w-0">
          <p
            class="truncate font-serif text-lg leading-tight tracking-wide text-ink"
          >
            {{ i18nMessages.settings }}
          </p>
          <p class="hidden truncate text-xs text-inkLight sm:block">
            {{ i18nMessages.settingsSubtitle }}
          </p>
        </div>
        <router-link
          to="/"
          data-testid="settings-back"
          class="tap-target shrink-0 gap-2 rounded-full border border-ink/10 bg-surface px-5 text-sm font-medium text-ink transition-colors hover:border-ink/18 active:bg-ink/5"
        >
          <svg
            class="h-4 w-4"
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
          {{ i18nMessages.backToReading }}
        </router-link>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
  import { onBeforeUnmount, onMounted, ref, watch } from "vue";

  import { clearVocabulary, exportVocabulary } from "../api/reading";
  import {
    clearProviderKey,
    fetchProvider,
    setProvider,
    setProviderKey,
    testProvider,
  } from "../api/settings";
  import { type Locale, useI18n } from "../composables/useI18n";
  import { useSettings } from "../composables/useSettings";

  type ThemeOption = "light" | "dark";
  type UiFontSizeOption = "xs" | "sm" | "md" | "lg" | "xl";
  type ColorThemeOption = "default" | "sepia" | "sage" | "slate";

  const DEFAULT_MODEL = "";

  const THEME_OPTIONS: ThemeOption[] = ["light", "dark"];
  const COLOR_THEME_OPTIONS: ColorThemeOption[] = [
    "default",
    "sepia",
    "sage",
    "slate",
  ];

  const { get, set, clearAll, exportAll, importAll } = useSettings();
  const { locale, messages: i18nMessages, setLocale } = useI18n();

  const draftTargetWordCount = ref(
    Number(get("generation", "targetWordCount", "1")),
  );

  const draftSuggestionPoolSize = ref(
    Number(get("generation", "suggestionPoolSize", "3")),
  );

  const currentTheme = ref<ThemeOption>(loadTheme());
  const colorTheme = ref<ColorThemeOption>(loadColorTheme());
  const uiFontSize = ref<UiFontSizeOption>(loadUiFontSize());

  const selectedModel = ref("");
  const providerEndpoint = ref("http://localhost:11434");
  /** Draft value for a not-yet-saved key. Never holds a stored or masked value. */
  const providerKeyDraft = ref("");
  const apiKeySet = ref(false);
  const apiKeyHint = ref("");
  const savingKey = ref(false);
  /** Header rows are kept as a list so ordering is stable while editing. */
  interface HeaderDraft {
    name: string;
    value: string;
  }
  const headerDrafts = ref<HeaderDraft[]>([]);
  const showAdvanced = ref(false);
  const connectionStatus = ref<"idle" | "testing" | "ok" | "error">("idle");
  const connectionMessage = ref("");
  const showEndpointHint = ref(false);
  const showZoomHint = ref(false);
  const settingsFileInput = ref<HTMLInputElement | null>(null);

  type DictionaryDisplayOption = "zh" | "en" | "both";
  const DICT_DISPLAY_OPTIONS: DictionaryDisplayOption[] = ["en", "both", "zh"];
  const dictionaryDisplay = ref<DictionaryDisplayOption>(loadDictDisplay());

  const uiFontSizeOptions = [
    { value: "xs" as const, label: "90%" },
    { value: "sm" as const, label: "100%" },
    { value: "md" as const, label: "125%" },
    { value: "lg" as const, label: "140%" },
    { value: "xl" as const, label: "150%" },
  ];

  // --- Persistence helpers ---

  function loadTheme(): ThemeOption {
    const saved = get("reading", "theme", "light");
    return THEME_OPTIONS.includes(saved as ThemeOption)
      ? (saved as ThemeOption)
      : "light";
  }

  function applyTheme(theme: ThemeOption): void {
    if (typeof window === "undefined") return;
    window.document.documentElement.setAttribute("data-theme", theme);
  }

  function setTheme(theme: ThemeOption): void {
    currentTheme.value = theme;
    applyTheme(theme);
    set("reading", { theme });
  }

  function loadColorTheme(): ColorThemeOption {
    const saved = get("interface", "colorTheme", "default");
    return COLOR_THEME_OPTIONS.includes(saved as ColorThemeOption)
      ? (saved as ColorThemeOption)
      : "default";
  }

  function applyColorTheme(theme: ColorThemeOption): void {
    if (typeof document === "undefined") return;
    if (theme === "default") {
      document.documentElement.removeAttribute("data-palette");
    } else {
      document.documentElement.setAttribute("data-palette", theme);
    }
  }

  function setColorTheme(theme: ColorThemeOption): void {
    colorTheme.value = theme;
    applyColorTheme(theme);
    set("interface", { colorTheme: theme });
  }

  const UI_ZOOM_MAP: Record<UiFontSizeOption, string> = {
    xs: "0.9",
    sm: "1",
    md: "1.25",
    lg: "1.4",
    xl: "1.5",
  };

  function loadUiFontSize(): UiFontSizeOption {
    const saved = get("interface", "uiFontSize", "sm");
    const valid: UiFontSizeOption[] = ["xs", "sm", "md", "lg", "xl"];
    if (valid.includes(saved as UiFontSizeOption))
      return saved as UiFontSizeOption;
    return "sm";
  }

  function applyZoom(size: UiFontSizeOption): void {
    if (typeof document === "undefined") return;
    const appEl = document.getElementById("app");
    if (appEl) {
      const zoomVal = UI_ZOOM_MAP[size];
      appEl.style.zoom = zoomVal;
      appEl.style.setProperty("--app-zoom", zoomVal);
    }
  }

  function setUiFontSize(size: UiFontSizeOption): void {
    uiFontSize.value = size;
    applyZoom(size);
    set("interface", { uiFontSize: size });
  }

  function switchLanguage(nextLocale: Locale): void {
    setLocale(nextLocale);
  }

  function toggleClass(isActive: boolean): string {
    return isActive
      ? "bg-ink text-paper shadow-sm font-medium"
      : "text-inkLight hover:text-ink";
  }

  function loadDictDisplay(): DictionaryDisplayOption {
    const saved = get("dictionary", "display", "");
    if (DICT_DISPLAY_OPTIONS.includes(saved as DictionaryDisplayOption)) {
      return saved as DictionaryDisplayOption;
    }
    return typeof window !== "undefined" &&
      window.navigator.language.toLowerCase().startsWith("zh")
      ? "both"
      : "en";
  }

  function setDictionaryDisplay(mode: DictionaryDisplayOption): void {
    dictionaryDisplay.value = mode;
    set("dictionary", { display: mode });
  }

  /** Collect edited rows, dropping rows without a name. */
  function collectHeaders(): Record<string, string> {
    const result: Record<string, string> = {};
    for (const row of headerDrafts.value) {
      const name = row.name.trim();
      if (!name) continue;
      result[name] = row.value;
    }
    return result;
  }

  function addHeader(): void {
    headerDrafts.value.push({ name: "", value: "" });
  }

  function removeHeader(index: number): void {
    headerDrafts.value.splice(index, 1);
  }

  async function saveProvider(): Promise<void> {
    const state = await setProvider({
      endpoint: providerEndpoint.value,
      model: selectedModel.value,
      headers: collectHeaders(),
    });
    applyProviderState(state);
  }

  /** Mirror server state so the key's configured status stays authoritative. */
  function applyProviderState(state: {
    endpoint: string;
    model: string;
    headers: Record<string, string>;
    apiKeySet: boolean;
    apiKeyHint: string;
  }): void {
    providerEndpoint.value = state.endpoint;
    selectedModel.value = state.model;
    headerDrafts.value = Object.entries(state.headers ?? {}).map(
      ([name, value]) => ({ name, value }),
    );
    // Surface existing headers without hiding them behind a collapsed toggle.
    if (headerDrafts.value.length > 0) showAdvanced.value = true;
    apiKeySet.value = state.apiKeySet;
    apiKeyHint.value = state.apiKeyHint;
  }

  async function submitProviderKey(): Promise<void> {
    const draft = providerKeyDraft.value.trim();
    if (!draft) return;
    savingKey.value = true;
    try {
      applyProviderState(await setProviderKey(draft));
      providerKeyDraft.value = "";
    } catch {
      window.alert(i18nMessages.value.providerSaveFailed);
    } finally {
      savingKey.value = false;
    }
  }

  function confirmClearProviderKey(): void {
    if (window.confirm(i18nMessages.value.apiKeyClearConfirm)) {
      void handleClearProviderKey();
    }
  }

  async function handleClearProviderKey(): Promise<void> {
    applyProviderState(await clearProviderKey());
    providerKeyDraft.value = "";
    connectionStatus.value = "idle";
    connectionMessage.value = "";
  }

  async function handleTestConnection(): Promise<void> {
    connectionStatus.value = "testing";
    connectionMessage.value = "";
    try {
      await saveProvider();
    } catch {
      connectionStatus.value = "error";
      connectionMessage.value = "Network error";
      return;
    }
    try {
      const result = await testProvider();
      connectionStatus.value = result.ok ? "ok" : "error";
      connectionMessage.value = result.message;
    } catch {
      connectionStatus.value = "error";
      connectionMessage.value = "Network error";
    }
  }

  async function handleClearVocabulary(): Promise<void> {
    await clearVocabulary();
  }

  function confirmClearVocabulary(): void {
    if (window.confirm(i18nMessages.value.confirmClearVocabulary)) {
      void handleClearVocabulary();
    }
  }

  async function handleClearSettings(): Promise<void> {
    await clearAll();
    window.location.reload();
  }

  function confirmClearSettings(): void {
    if (window.confirm(i18nMessages.value.confirmClearSettings)) {
      void handleClearSettings();
    }
  }

  function handleExportVocabulary(): void {
    void exportVocabulary();
  }

  function handleExportSettings(): void {
    const data = exportAll();
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "openvoca-settings.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function onSettingsFileSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    input.value = "";
    try {
      const text = await file.text();
      const data = JSON.parse(text) as Record<string, unknown>;
      if (typeof data !== "object" || data === null || Array.isArray(data)) {
        window.alert(i18nMessages.value.importSettingsBadFormat);
        return;
      }
      await importAll(data as Record<string, Record<string, string>>);
      window.location.reload();
    } catch {
      window.alert(i18nMessages.value.importSettingsBadFormat);
    }
  }

  // Auto-save generation preferences when drafts change
  watch(draftSuggestionPoolSize, (newPool) => {
    if (draftTargetWordCount.value > newPool) {
      draftTargetWordCount.value = newPool;
    }
    set("generation", {
      suggestionPoolSize: String(newPool),
      targetWordCount: String(draftTargetWordCount.value),
    });
  });

  watch(draftTargetWordCount, () => {
    set("generation", {
      targetWordCount: String(draftTargetWordCount.value),
    });
  });

  // Apply current theme on mount
  onMounted(() => {
    applyTheme(currentTheme.value);

    Promise.all([fetchProvider()])
      .then(([provider]) => {
        applyProviderState(
          provider ?? {
            endpoint: "http://localhost:11434",
            model: DEFAULT_MODEL,
            headers: {},
            apiKeySet: false,
            apiKeyHint: "",
          },
        );
      })
      .catch(() => {
        // keep defaults
      });
  });

  // Save on leave as a safety net
  onBeforeUnmount(() => {
    set("generation", {
      suggestionPoolSize: String(draftSuggestionPoolSize.value),
      targetWordCount: String(draftTargetWordCount.value),
    });
  });
</script>
