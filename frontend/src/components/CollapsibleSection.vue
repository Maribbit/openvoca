<template>
  <div class="border-t border-black/5 pt-5">
    <button
      type="button"
      :data-testid="testId"
      class="tap-finger flex w-full items-center justify-between text-left"
      :aria-expanded="open"
      @click="emit('toggle')"
    >
      <span class="text-sm font-semibold text-ink">{{ title }}</span>
      <span class="text-xs text-inkLight">{{ open ? "▾" : "▸" }}</span>
    </button>
    <div v-if="open" class="mt-4 space-y-4">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
  /**
   * A collapsible block inside a settings card.
   *
   * Exists because the model card holds several optional groups, and the card
   * had grown long enough that scrolling past groups nobody had configured
   * became the normal experience. Each group folds on its own so the card shows
   * only what is in use.
   *
   * The trigger is a full-width row rather than a small chevron: it is the
   * whole row that reads as the label, and a target the size of the text would
   * be awkward on a phone.
   */
  defineProps<{
    title: string;
    open: boolean;
    /** Kept explicit so each block stays addressable from tests. */
    testId: string;
  }>();

  const emit = defineEmits<{ toggle: [] }>();
</script>
