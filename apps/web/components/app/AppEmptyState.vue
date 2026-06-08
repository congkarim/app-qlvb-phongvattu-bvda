<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string
    description?: string
    icon?: string
  }>(),
  {
    title: 'Chưa có dữ liệu',
    description: '',
    icon: 'pi-inbox'
  }
)
</script>

<template>
  <div class="flex flex-col items-center justify-center px-4 py-10 text-center">
    <div class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
      <i :class="['pi text-xl', icon]" />
    </div>
    <p class="text-sm font-medium text-slate-700">{{ title }}</p>
    <p v-if="description" class="mt-1 max-w-sm text-sm text-slate-500">{{ description }}</p>
    <div v-if="$slots.action" class="mt-4">
      <slot name="action" />
    </div>
  </div>
</template>
