<script setup lang="ts">
interface ActionOption {
  label: string
  value: string
  icon?: string
}

defineProps<{
  options: ActionOption[]
  modelValue: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="inline-flex flex-wrap gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1" role="group">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="inline-flex min-h-[44px] items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors"
      :class="
        modelValue === option.value
          ? 'bg-white text-slate-900 shadow-sm ring-1 ring-slate-200'
          : 'text-slate-600 hover:bg-white/70 hover:text-slate-900'
      "
      :disabled="disabled"
      :aria-pressed="modelValue === option.value"
      @click="emit('update:modelValue', option.value)"
    >
      <i v-if="option.icon" :class="option.icon" />
      {{ option.label }}
    </button>
  </div>
</template>
