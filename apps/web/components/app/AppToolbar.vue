<script setup lang="ts">
defineProps<{
  summary: string
  loading?: boolean
  canGoPrevious?: boolean
  canGoNext?: boolean
}>()

const emit = defineEmits<{
  previous: []
  next: []
}>()
</script>

<template>
  <div
    class="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
  >
    <p class="text-sm text-slate-600">{{ summary }}</p>
    <div class="flex gap-2">
      <Button
        label="Trước"
        icon="pi pi-chevron-left"
        severity="secondary"
        size="small"
        :disabled="loading || !canGoPrevious"
        @click="emit('previous')"
      />
      <Button
        label="Sau"
        icon="pi pi-chevron-right"
        icon-pos="right"
        severity="secondary"
        size="small"
        :disabled="loading || !canGoNext"
        @click="emit('next')"
      />
    </div>
  </div>
</template>
