<script setup lang="ts">
withDefaults(
  defineProps<{
    message?: string
    compact?: boolean
  }>(),
  {
    message: 'Đang tải...',
    compact: false
  }
)
</script>

<template>
  <div
    :class="[
      'flex items-center justify-center gap-2 text-sm text-slate-600',
      compact ? 'py-4' : 'py-10'
    ]"
    role="status"
    aria-live="polite"
  >
    <i class="pi pi-spin pi-spinner text-slate-400" />
    <span>{{ message }}</span>
  </div>
</template>
