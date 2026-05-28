<script setup lang="ts">
const props = defineProps<{
  status: string
}>()

const severity = computed(() => {
  if (props.status === 'searchable' || props.status === 'completed') return 'success'
  if (props.status.includes('failed')) return 'danger'
  if (props.status.includes('running') || props.status.includes('pending')) return 'warn'
  return 'info'
})
</script>

<template>
  <Tag :value="status" :severity="severity" />
</template>
