<template>
  <!-- Bottom sheet rather than a top panel: the effect of these controls is only
       visible in the sentence, and a top panel covers the start of it. -->
  <section
    data-testid="reading-settings-overlay"
    class="fixed inset-0 z-40 flex items-end justify-center bg-black/20 backdrop-blur-sm"
    @click.self="$emit('close')"
  >
    <div
      class="sheet-rise w-full max-w-lg rounded-t-2xl border-t border-ink/8 bg-surface shadow-[0_-10px_40px_rgba(44,44,44,0.16)]"
      style="padding-bottom: env(safe-area-inset-bottom, 0px)"
    >
      <div class="flex flex-col gap-1 p-3">
        <!-- Font size -->
        <div class="flex items-center justify-between gap-3 px-2 py-1">
          <span class="text-sm font-medium text-inkLight">
            {{ messages.fontSize }}
          </span>
          <div class="flex items-center gap-1 rounded-xl bg-paper p-1">
            <button
              v-for="opt in fontSizeOptions"
              :key="opt.value"
              type="button"
              class="tap-target rounded-lg transition-colors"
              :class="optionButtonClass(settings.fontSize === opt.value)"
              @click="
                $emit('update:settings', { ...settings, fontSize: opt.value })
              "
            >
              <span :class="opt.labelClass">{{ opt.label }}</span>
            </button>
          </div>
        </div>

        <!-- Spacing -->
        <div class="flex items-center justify-between gap-3 px-2 py-1">
          <span class="text-sm font-medium text-inkLight">
            {{ messages.spacing }}
          </span>
          <div class="flex items-center gap-1 rounded-xl bg-paper p-1">
            <button
              v-for="opt in spacingOptions"
              :key="opt.value"
              type="button"
              class="tap-target rounded-lg transition-colors"
              :class="optionButtonClass(settings.spacing === opt.value)"
              @click="
                $emit('update:settings', { ...settings, spacing: opt.value })
              "
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
                  :d="opt.iconPath"
                />
              </svg>
            </button>
          </div>
        </div>

        <!-- Theme -->
        <div class="flex items-center justify-between gap-3 px-2 py-1">
          <span class="text-sm font-medium text-inkLight">
            {{ messages.theme }}
          </span>
          <div class="flex items-center gap-1 rounded-xl bg-paper p-1">
            <button
              type="button"
              class="tap-target rounded-lg transition-colors"
              :class="optionButtonClass(settings.theme === 'light')"
              @click="$emit('update:settings', { ...settings, theme: 'light' })"
              :title="messages.themeLight"
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
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0z"
                />
              </svg>
            </button>
            <button
              type="button"
              class="tap-target rounded-lg transition-colors"
              :class="optionButtonClass(settings.theme === 'dark')"
              @click="$emit('update:settings', { ...settings, theme: 'dark' })"
              :title="messages.themeDark"
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
                  d="M20.354 15.354A9 9 0 0 1 8.646 3.646 9.003 9.003 0 0 0 12 21a9.003 9.003 0 0 0 8.354-5.646z"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
  export type FontSizeOption = "sm" | "md" | "lg";
  export type SpacingOption = "tight" | "normal" | "loose";
  export type ThemeOption = "light" | "dark";

  export interface ReadingUiSettings {
    fontSize: FontSizeOption;
    spacing: SpacingOption;
    theme: ThemeOption;
  }

  defineProps<{
    settings: ReadingUiSettings;
    messages: {
      fontSize: string;
      spacing: string;
      theme: string;
      themeLight: string;
      themeDark: string;
    };
  }>();

  defineEmits<{
    close: [];
    "update:settings": [settings: ReadingUiSettings];
  }>();

  const fontSizeOptions = [
    { value: "sm" as const, label: "A-", labelClass: "text-xs font-medium" },
    { value: "md" as const, label: "A", labelClass: "text-sm font-medium" },
    { value: "lg" as const, label: "A+", labelClass: "text-base font-medium" },
  ];

  const spacingOptions = [
    { value: "tight" as const, iconPath: "M4 8h16M4 16h16" },
    { value: "normal" as const, iconPath: "M4 6h16M4 12h16M4 18h16" },
    { value: "loose" as const, iconPath: "M4 4h16M4 12h16M4 20h16" },
  ];

  function optionButtonClass(isActive: boolean): string {
    return isActive
      ? "bg-surface text-ink shadow-sm"
      : "text-inkLight hover:bg-surface hover:text-ink";
  }
</script>
