<script setup lang="ts">
defineProps<{
  title?: string
  subtitle?: string
  noPadding?: boolean
}>()
</script>

<template>
  <div class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
    <div v-if="title || $slots.header" class="border-b border-slate-100 px-4 py-3 sm:px-5">
      <slot name="header">
        <div>
          <h2 v-if="title" class="text-base font-semibold text-slate-900">{{ title }}</h2>
          <p v-if="subtitle" class="mt-0.5 text-xs text-slate-500">{{ subtitle }}</p>
        </div>
      </slot>
    </div>
    <div :class="noPadding ? '' : 'px-4 py-4 sm:px-5 sm:py-5'">
      <slot />
    </div>
  </div>
</template>
