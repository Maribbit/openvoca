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
                  placeholder="http://localhost:11434/v1"
                  class="rounded-xl border border-black/8 bg-paper px-4 py-2.5 font-mono text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight"
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
                    class="tap-finger flex-1 whitespace-nowrap rounded-xl border border-black/15 px-4 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-black/4 active:bg-black/8 dark:border-white/15 dark:hover:bg-white/8 sm:flex-none"
                    @click="confirmClearProviderKey"
                  >
                    {{ i18nMessages.apiKeyClear }}
                  </button>
                  <button
                    v-else
                    type="button"
                    data-testid="provider-key-save"
                    class="tap-finger flex-1 whitespace-nowrap rounded-xl border border-black/15 px-4 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-black/4 active:bg-black/8 dark:border-white/15 dark:hover:bg-white/8 sm:flex-none"
                    :disabled="!providerKeyDraft || savingKey"
                    @click="submitProviderKey"
                  >
                    {{ i18nMessages.apiKeySave }}
                  </button>
                </div>
              </div>
              <p class="text-xs text-inkLight">
                {{ i18nMessages.apiKeyHint }}
              </p>
            </div>

            <!-- Optional groups sit side by side as peers, each folding on its
                 own. They used to nest under one "Advanced" heading, which made
                 the card long and made a group the reader cared about as buried
                 as the two they did not. Only the groups with something in them
                 start open. -->
            <CollapsibleSection
              :title="i18nMessages.advancedHeaders"
              :open="showHeaders"
              test-id="provider-headers-toggle"
              @toggle="showHeaders = !showHeaders"
            >
              <p class="text-xs text-inkLight">
                {{ i18nMessages.advancedHeadersHint }}
              </p>
              <!-- Two inputs and a button in one row could not fit a phone: a
                   flex item will not shrink below its intrinsic width unless
                   told to, so the value field ran off the card. minmax(0,1fr)
                   allows the shrink, and the value drops to its own row while
                   narrow. -->
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
                  <!-- Icon only while narrow, so the name field keeps enough
                       width to show a header name undivided. -->
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
            </CollapsibleSection>

            <CollapsibleSection
              :title="i18nMessages.bodyFieldsLabel"
              :open="showBodyFields"
              test-id="provider-body-toggle"
              @toggle="showBodyFields = !showBodyFields"
            >
                <p class="text-xs text-inkLight">
                  {{ i18nMessages.bodyFieldsHint }}
                </p>
                <!-- A reserved name is shown rather than dropped in silence: a
                     row that looks configured but is never sent is the failure
                     these fields exist to avoid. -->
                <p
                  v-if="reservedBodyFields.length > 0"
                  data-testid="provider-body-reserved-warning"
                  class="rounded-xl border border-amber-300/60 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200"
                >
                  {{ i18nMessages.bodyFieldRejected }}
                </p>
                <div
                  v-for="(field, index) in bodyFieldDrafts"
                  :key="index"
                  class="grid grid-cols-[minmax(0,1fr)_auto] gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]"
                >
                  <input
                    v-model="field.name"
                    data-testid="provider-body-name"
                    type="text"
                    :placeholder="i18nMessages.bodyFieldName"
                    :class="[
                      'col-start-1 row-start-1 min-w-0 rounded-xl border bg-paper px-4 py-2.5 font-mono text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight',
                      isReservedBodyField(field.name)
                        ? 'border-amber-400'
                        : 'border-black/8',
                    ]"
                  />
                  <input
                    v-model="field.value"
                    data-testid="provider-body-value"
                    type="text"
                    :placeholder="i18nMessages.bodyFieldValue"
                    class="col-span-2 row-start-2 min-w-0 rounded-xl border border-black/8 bg-paper px-4 py-2.5 font-mono text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight sm:col-span-1 sm:col-start-2 sm:row-start-1"
                  />
                  <button
                    type="button"
                    data-testid="provider-body-remove"
                    class="col-start-2 row-start-1 whitespace-nowrap rounded-xl border border-black/15 px-3.5 py-2.5 text-sm font-medium text-inkLight transition-colors hover:bg-black/4 hover:text-ink active:bg-black/8 dark:border-white/15 dark:hover:bg-white/8 sm:col-start-3 sm:px-4"
                    :title="i18nMessages.removeHeader"
                    :aria-label="i18nMessages.removeHeader"
                    @click="removeBodyField(index)"
                  >
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
                  data-testid="provider-body-add"
                  class="rounded-xl border border-black/15 px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-black/4 dark:border-white/15 dark:hover:bg-white/8"
                  @click="addBodyField"
                >
                  + {{ i18nMessages.addBodyField }}
                </button>

                <!-- Presets are data, not logic: each one fills rows the user can
                     then edit, so a provider renaming a field is a one-line
                     change here rather than a code path that guesses what to
                     send. -->
                <div class="space-y-2 pt-2">
                  <p class="text-xs font-medium text-inkLight">
                    {{ i18nMessages.bodyFieldPresets }}
                  </p>
                  <p class="text-xs text-inkLight/70">
                    {{ i18nMessages.bodyFieldPresetsHint }}
                  </p>
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="preset in BODY_FIELD_PRESETS"
                      :key="preset.providers"
                      type="button"
                      data-testid="provider-body-preset"
                      class="rounded-full border border-black/10 bg-paper px-3 py-1.5 text-xs text-inkLight transition-colors hover:border-ink/20 hover:text-ink active:bg-black/5 dark:border-white/15 dark:hover:bg-white/8"
                      @click="applyPreset(preset.fields)"
                    >
                      {{ i18nMessages[preset.action] }} ·
                      <span class="font-mono">{{ preset.providers }}</span>
                    </button>
                  </div>
                </div>
            </CollapsibleSection>

            <!-- Testing is a step of its own, above Save and not beside it.
                 Nothing here writes to the database, so the two are genuinely
                 different actions and the reading order says which comes
                 first: prove the configuration, then commit it.

                 Not foldable, unlike the two groups above: it has no content
                 until it is run, so it occupies one row at rest and folding it
                 would only hide a control that is already compact. -->
            <div class="border-t border-black/5 pt-5">
              <p class="text-sm font-semibold text-ink">
                {{ i18nMessages.testConnection }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.testConnectionHint }}
              </p>
              <div class="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  data-testid="provider-test"
                  class="tap-finger flex-1 whitespace-nowrap rounded-xl border border-black/15 px-4 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-black/4 active:bg-black/8 disabled:opacity-40 dark:border-white/15 dark:hover:bg-white/8 sm:flex-none"
                  :disabled="testing"
                  @click="runTest"
                >
                  {{
                    testing
                      ? i18nMessages.testingConnection
                      : i18nMessages.runTest
                  }}
                </button>
                <!-- Always present rather than swapping in place of Run: a
                     button that changes identity is easy to press by mistake
                     when the request it belongs to takes a minute. -->
                <button
                  type="button"
                  data-testid="provider-test-stop"
                  class="tap-finger flex-1 whitespace-nowrap rounded-xl border border-black/15 px-4 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-black/4 active:bg-black/8 disabled:opacity-40 dark:border-white/15 dark:hover:bg-white/8 sm:flex-none"
                  :disabled="!testing"
                  @click="stopTest"
                >
                  {{ i18nMessages.stopTest }}
                </button>
                <!-- A request can take a minute, and a motionless button for a
                     minute is indistinguishable from a frozen one. -->
                <span
                  v-if="testing"
                  data-testid="provider-test-elapsed"
                  class="self-center text-xs tabular-nums text-inkLight"
                >
                  {{ (testElapsedMs / 1000).toFixed(1) }}s
                </span>
              </div>

              <div
                v-if="testOutcome"
                data-testid="provider-test-output"
                class="space-y-3"
              >
                <p
                  data-testid="provider-test-status"
                  class="text-xs font-medium"
                  :class="testOutcome.toneClass"
                >
                  {{ testOutcome.status }}
                </p>
                <p
                  v-if="testOutcome.usage"
                  data-testid="provider-test-usage"
                  class="text-xs text-inkLight"
                >
                  <span class="font-medium">{{
                    i18nMessages.testUsageLabel
                  }}</span>
                  · <span class="font-mono">{{ testOutcome.usage }}</span>
                </p>
                <div v-for="block in testOutcome.blocks" :key="block.label">
                  <p
                    class="text-[11px] font-medium uppercase tracking-wider text-inkLight/70"
                  >
                    {{ block.label }}
                  </p>
                  <pre
                    class="mt-1 max-h-44 overflow-auto rounded-xl border border-black/8 bg-black/3 p-3 font-mono text-[11px] leading-relaxed whitespace-pre-wrap text-ink dark:border-white/10 dark:bg-white/5"
                    >{{ block.text }}</pre
                  >
                </div>
              </div>
            </div>

            <!-- The action row is sticky, not merely last. The groups above can
                 be expanded past a screenful, and a Save that scrolls away is
                 one a reader leaves the page without pressing -- taking the
                 edits with it. It stays at the bottom of the viewport for as
                 long as the card is on screen.

                 -mx/-mb/px/pb undo the card's padding for this one row, so the
                 strip spans the full card width and its background covers what
                 scrolls beneath it rather than letting content show through at
                 the edges. -->
            <div
              data-testid="provider-action-bar"
              class="sticky bottom-0 z-10 -mx-6 -mb-6 mt-5 flex flex-col gap-3 border-t border-black/5 bg-surface px-6 pt-4 pb-6 sm:flex-row sm:items-center sm:justify-between"
            >
              <div class="min-w-0 space-y-1">
                <p
                  v-if="providerError"
                  data-testid="provider-save-state"
                  class="text-xs text-red-500"
                >
                  ✗ {{ providerError }}
                </p>
                <p
                  v-else-if="providerDirty"
                  data-testid="provider-save-state"
                  class="text-xs text-amber-600"
                >
                  ● {{ i18nMessages.modelUnsaved }}
                </p>
                <p
                  v-else-if="savedFlash"
                  data-testid="provider-save-state"
                  class="text-xs text-green-600"
                >
                  ✓ {{ i18nMessages.modelSaved }}
                </p>
              </div>
              <div class="flex shrink-0 gap-2">
                <!-- Discard sits before Save and is deliberately quieter, but
                     it is not hidden: it is the way out of an edit that turned
                     out badly, and looking for it is already a bad moment. -->
                <button
                  type="button"
                  data-testid="provider-discard"
                  class="tap-finger flex-1 whitespace-nowrap rounded-xl border border-black/15 px-4 py-2.5 text-sm font-medium text-inkLight transition-colors hover:bg-black/4 hover:text-ink active:bg-black/8 disabled:opacity-40 dark:border-white/15 dark:hover:bg-white/8 sm:flex-none"
                  :disabled="savingProvider || !providerDirty"
                  @click="handleDiscard"
                >
                  {{ i18nMessages.discardModel }}
                </button>
                <button
                  type="button"
                  data-testid="provider-save"
                  class="tap-finger flex-1 whitespace-nowrap rounded-xl bg-ink px-4 py-2.5 text-sm font-medium text-paper transition-opacity hover:opacity-90 active:opacity-80 disabled:opacity-40 sm:flex-none"
                  :disabled="savingProvider || !providerDirty"
                  @click="handleSave"
                >
                  {{
                    savingProvider
                      ? i18nMessages.savingModel
                      : i18nMessages.saveModel
                  }}
                </button>
              </div>
            </div>
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
  import { onBeforeUnmount, onMounted, ref, watch, computed } from "vue";
  import { onBeforeRouteLeave } from "vue-router";

  import CollapsibleSection from "../components/CollapsibleSection.vue";
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
  const providerEndpoint = ref("http://localhost:11434/v1");
  /** Draft value for a not-yet-saved key. Never holds a stored or masked value. */
  const providerKeyDraft = ref("");
  const apiKeySet = ref(false);
  const apiKeyHint = ref("");
  const savingKey = ref(false);
  const savingProvider = ref(false);
  /** Shown after a save, then cleared; see flashSaved. */
  const savedFlash = ref(false);
  const providerError = ref("");
  /**
   * The last state the server confirmed, as a comparable string.
   *
   * Saving is explicit, so the interface has to be able to say whether what is
   * on screen has been stored. Comparing against this is how it knows.
   */
  const savedSnapshot = ref("");
  /**
   * Whether a baseline exists yet.
   *
   * Until the stored configuration has been read, the form holds defaults and
   * the baseline is empty, so the two differ and the form would report unsaved
   * changes on every visit -- and, if the read failed, would report them
   * forever and block leaving the page over an edit nobody made.
   */
  const providerLoaded = ref(false);
  let savedFlashTimer: ReturnType<typeof setTimeout> | undefined;
  /** Header rows are kept as a list so ordering is stable while editing. */
  interface HeaderDraft {
    name: string;
    value: string;
  }
  const headerDrafts = ref<HeaderDraft[]>([]);

  /**
   * Extra request body fields, kept as rows so ordering is stable while editing.
   *
   * Values are text until save: providers disagree on whether reasoning is
   * turned off by a string, a boolean or a nested object, so the row holds what
   * was typed and parseBodyFieldValue decides how to send it.
   */
  interface BodyFieldDraft {
    name: string;
    value: string;
  }
  const bodyFieldDrafts = ref<BodyFieldDraft[]>([]);

  /**
   * Starting points for controlling reasoning, one per provider shape.
   *
   * Data rather than logic, deliberately. If these were code that decided which
   * field to send, this would be the per-provider normalisation the design
   * avoids, and a provider renaming a field would silently stop working.
   *
   * Each carries its own action, because they no longer all do the same thing:
   * OpenCode Go's router rejects `none` for the models it serves -- the catalog
   * lists only low, high and max -- so the useful setting there is a lower
   * effort rather than an off switch. Labelling that "disable thinking" would
   * promise something the provider cannot deliver.
   */
  const BODY_FIELD_PRESETS: {
    action: "disableThinking" | "lowerThinking";
    providers: string;
    fields: Record<string, unknown>;
  }[] = [
    {
      action: "disableThinking",
      providers: "OpenAI / DeepSeek / Ollama",
      fields: { reasoning_effort: "none" },
    },
    {
      action: "disableThinking",
      providers: "Z.AI GLM",
      fields: { thinking: { type: "disabled" } },
    },
    {
      action: "disableThinking",
      providers: "OpenRouter",
      fields: { reasoning: { effort: "none" } },
    },
    {
      action: "disableThinking",
      providers: "Qwen3 / vLLM",
      fields: { chat_template_kwargs: { enable_thinking: false } },
    },
    {
      // opencode-go serves several model families under one router, and its
      // catalog advertises effort levels without an off value. `low` is the
      // one that reduces the cost, and it is valid for every effort-capable
      // model it lists.
      action: "lowerThinking",
      providers: "OpenCode Go",
      fields: { reasoning_effort: "low" },
    },
  ];
  const showHeaders = ref(false);
  const showBodyFields = ref(false);
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

  // --- Extra request body fields ---

  /**
   * Read a value the way the request will carry it.
   *
   * JSON when it parses, text otherwise. That lets a snippet from a provider's
   * documentation be pasted as-is -- {"type": "disabled"}, false -- while a
   * bare word such as none still means the string "none" rather than failing
   * to parse and disappearing.
   */
  function parseBodyFieldValue(raw: string): unknown {
    const text = raw.trim();
    if (!text) return "";
    try {
      return JSON.parse(text);
    } catch {
      return raw;
    }
  }

  /** Render a stored value back into the text a row edits. */
  function formatBodyFieldValue(value: unknown): string {
    return typeof value === "string" ? value : JSON.stringify(value);
  }

  /** Rows the application owns. Mirrors RESERVED_PAYLOAD_KEYS on the server. */
  const RESERVED_BODY_FIELDS = new Set(["model", "messages", "stream"]);

  function isReservedBodyField(name: string): boolean {
    return RESERVED_BODY_FIELDS.has(name.trim());
  }

  /**
   * Names that are reserved, so the interface can say so.
   *
   * These rows are not sent. Saying that outright is the point: a row that
   * looks configured and is silently ignored is the failure this whole field
   * exists to prevent, and it would be worse here than having no field at all.
   */
  const reservedBodyFields = computed(() =>
    bodyFieldDrafts.value
      .map((row) => row.name.trim())
      .filter((name) => RESERVED_BODY_FIELDS.has(name)),
  );

  function collectBodyFields(): Record<string, unknown> {
    const result: Record<string, unknown> = {};
    for (const row of bodyFieldDrafts.value) {
      const name = row.name.trim();
      if (!name || isReservedBodyField(name)) continue;
      result[name] = parseBodyFieldValue(row.value);
    }
    return result;
  }

  function addBodyField(): void {
    bodyFieldDrafts.value.push({ name: "", value: "" });
  }

  function removeBodyField(index: number): void {
    bodyFieldDrafts.value.splice(index, 1);
  }

  /** Everything the Save button stores, as one comparable string. */
  const currentSnapshot = computed(() =>
    JSON.stringify({
      endpoint: providerEndpoint.value.trim(),
      model: selectedModel.value.trim(),
      headers: collectHeaders(),
      bodyFields: collectBodyFields(),
    }),
  );

  const providerDirty = computed(
    () => providerLoaded.value && currentSnapshot.value !== savedSnapshot.value,
  );

  // A tested configuration stops being tested the moment it changes. Dropping
  // the result keeps a pass from describing a configuration that is no longer
  // on screen, which is the same ambiguity the save state exists to remove.
  watch(currentSnapshot, () => {
    testOutcome.value = null;
  });

  /** Fill rows from a preset, replacing a row that already sets the same field. */
  function applyPreset(fields: Record<string, unknown>): void {
    for (const [name, value] of Object.entries(fields)) {
      const text = formatBodyFieldValue(value);
      const existing = bodyFieldDrafts.value.find(
        (row) => row.name.trim() === name,
      );
      if (existing) {
        existing.value = text;
        continue;
      }
      bodyFieldDrafts.value.push({ name, value: text });
    }
  }

  async function saveProvider(): Promise<boolean> {
    savingProvider.value = true;
    providerError.value = "";
    try {
      applyProviderState(
        await setProvider({
          endpoint: providerEndpoint.value,
          model: selectedModel.value,
          headers: collectHeaders(),
          bodyFields: collectBodyFields(),
        }),
      );
      return true;
    } catch {
      providerError.value = i18nMessages.value.providerSaveFailed;
      return false;
    } finally {
      savingProvider.value = false;
    }
  }

  async function handleSave(): Promise<void> {
    if (await saveProvider()) flashSaved();
  }

  /**
   * Put the form back to what is stored, discarding unsaved edits.
   *
   * Re-reads rather than remembering an earlier value. "Undo" would mean
   * keeping a history, and after a second save the earlier value is no longer
   * what the user means by "before" -- whereas the stored state is unambiguous
   * at every moment.
   *
   * The API key is deliberately left alone: a key being typed but not yet saved
   * is not part of this payload, and clearing it would discard something the
   * stored configuration cannot restore.
   */
  async function handleDiscard(): Promise<void> {
    providerError.value = "";
    testOutcome.value = null;
    try {
      applyProviderState(await fetchProvider());
    } catch {
      providerError.value = i18nMessages.value.providerSaveFailed;
    }
  }

  /** Confirm a save briefly, then fall back to reporting the current state. */
  function flashSaved(): void {
    savedFlash.value = true;
    if (savedFlashTimer !== undefined) clearTimeout(savedFlashTimer);
    savedFlashTimer = setTimeout(() => {
      savedFlash.value = false;
    }, 2500);
  }

  /** Mirror server state so the key's configured status stays authoritative. */
  function applyProviderState(state: {
    endpoint: string;
    model: string;
    headers: Record<string, string>;
    bodyFields: Record<string, unknown>;
    apiKeySet: boolean;
    apiKeyHint: string;
  }): void {
    providerEndpoint.value = state.endpoint;
    selectedModel.value = state.model;
    headerDrafts.value = Object.entries(state.headers ?? {}).map(
      ([name, value]) => ({ name, value }),
    );
    bodyFieldDrafts.value = Object.entries(state.bodyFields ?? {}).map(
      ([name, value]) => ({ name, value: formatBodyFieldValue(value) }),
    );
    // Open a group that has something in it, and leave the empty ones folded:
    // a configured header the reader cannot see is worse than a long card.
    if (headerDrafts.value.length > 0) showHeaders.value = true;
    if (bodyFieldDrafts.value.length > 0) showBodyFields.value = true;
    apiKeySet.value = state.apiKeySet;
    apiKeyHint.value = state.apiKeyHint;
    // The server has confirmed this state, so it becomes the baseline the
    // unsaved-changes check compares against. Normalization means this is not
    // necessarily what was typed.
    savedSnapshot.value = currentSnapshot.value;
    providerLoaded.value = true;
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
  }

  /** One line summarising a completed test, plus the blocks printed under it. */
  interface TestOutcome {
    status: string;
    toneClass: string;
    usage: string;
    blocks: { label: string; text: string }[];
  }

  const testOutcome = ref<TestOutcome | null>(null);
  const testing = ref(false);
  const testElapsedMs = ref(0);
  /**
   * Aborts the request in flight.
   *
   * Held so the interface can abandon a provider that never answers. The
   * backend bounds its own call with the client timeout, but nothing bounds the
   * wait on this side, and a control that cannot be stopped is the difference
   * between "slow" and "broken".
   */
  let testAbort: AbortController | null = null;
  let testTimer: ReturnType<typeof setInterval> | undefined;

  function startElapsedTimer(): void {
    const started = Date.now();
    testElapsedMs.value = 0;
    testTimer = setInterval(() => {
      testElapsedMs.value = Date.now() - started;
    }, 200);
  }

  function stopElapsedTimer(): void {
    if (testTimer !== undefined) clearInterval(testTimer);
    testTimer = undefined;
  }

  /** Render token counts on one line, keeping whatever shape the provider used. */
  function formatUsage(usage: Record<string, unknown> | null): string {
    if (!usage) return "";
    const parts: string[] = [];
    for (const [key, value] of Object.entries(usage)) {
      if (typeof value === "number") {
        parts.push(`${key} ${value}`);
        continue;
      }
      // Providers nest the interesting counts one level down, as in
      // completion_tokens_details.reasoning_tokens. That is the field that
      // answers "did it really stop thinking?", so it is worth flattening: the
      // visible reply cannot show it, because reasoning is not returned as
      // content.
      if (value && typeof value === "object") {
        for (const [inner, innerValue] of Object.entries(
          value as Record<string, unknown>,
        )) {
          if (typeof innerValue === "number") parts.push(`${inner} ${innerValue}`);
        }
      }
    }
    return parts.join(" · ");
  }

  async function runTest(): Promise<void> {
    if (testing.value) return;
    testing.value = true;
    testOutcome.value = null;
    testAbort = new AbortController();
    startElapsedTimer();

    try {
      const result = await testProvider(
        {
          endpoint: providerEndpoint.value,
          model: selectedModel.value,
          headers: collectHeaders(),
          bodyFields: collectBodyFields(),
          apiKey: providerKeyDraft.value.trim(),
        },
        testAbort.signal,
      );
      testOutcome.value = {
        status: result.ok
          ? `✓ ${result.status} · ${result.elapsedMs} ms`
          : `✗ ${result.error} · ${result.elapsedMs} ms`,
        toneClass: result.ok ? "text-green-600" : "text-red-500",
        usage: formatUsage(result.usage),
        blocks: [
          {
            label: `${i18nMessages.value.testRequestLabel} · ${result.url}`,
            text: JSON.stringify(result.request, null, 2),
          },
          ...(result.response
            ? [{ label: i18nMessages.value.testResponseLabel, text: result.response }]
            : []),
        ],
      };
    } catch (error) {
      const aborted =
        error instanceof DOMException && error.name === "AbortError";
      testOutcome.value = {
        status: aborted
          ? `■ ${i18nMessages.value.testStopped} · ${(
              testElapsedMs.value / 1000
            ).toFixed(1)}s`
          : `✗ ${i18nMessages.value.testUnreachable}`,
        toneClass: aborted ? "text-inkLight" : "text-red-500",
        usage: "",
        blocks: aborted
          ? []
          : [
              {
                label: i18nMessages.value.testResponseLabel,
                text: String(error),
              },
            ],
      };
    } finally {
      stopElapsedTimer();
      testAbort = null;
      testing.value = false;
    }
  }

  function stopTest(): void {
    testAbort?.abort();
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
            endpoint: "http://localhost:11434/v1",
            model: DEFAULT_MODEL,
            headers: {},
            bodyFields: {},
            apiKeySet: false,
            apiKeyHint: "",
          },
        );
      })
      .catch(() => {
        // No stored configuration could be read. Adopt what is on screen as the
        // baseline anyway: the form is usable with defaults, and leaving the
        // flag unset would mean edits could never be saved.
        savedSnapshot.value = currentSnapshot.value;
        providerLoaded.value = true;
      });
  });

  // Unsaved edits are guarded rather than silently dropped. Save sits at the
  // bottom of a card that can be taller than the screen, so leaving the page is
  // the natural way to lose an edit -- and a state line above the button cannot
  // help anyone who has already scrolled past it.
  onBeforeRouteLeave(() => {
    if (!providerDirty.value) return true;
    return window.confirm(i18nMessages.value.leaveWithUnsaved);
  });

  // Save on leave as a safety net
  onBeforeUnmount(() => {
    set("generation", {
      suggestionPoolSize: String(draftSuggestionPoolSize.value),
      targetWordCount: String(draftTargetWordCount.value),
    });
    if (savedFlashTimer !== undefined) clearTimeout(savedFlashTimer);
    // Leaving the page must not leave a request running: nothing would be
    // around to show its result, and the provider would still be working.
    testAbort?.abort();
    stopElapsedTimer();
  });
</script>
