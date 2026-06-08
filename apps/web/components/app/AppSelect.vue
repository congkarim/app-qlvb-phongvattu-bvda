<script setup lang="ts">
const model = defineModel<string | number | boolean | null>({ required: true })

defineProps<{
  id?: string
  disabled?: boolean
}>()
</script>

<template>
  <select
    :id="id"
    v-model="model"
    class="app-select"
    :disabled="disabled"
  >
    <slot />
  </select>
</template>
