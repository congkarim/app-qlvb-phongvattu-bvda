<script setup lang="ts">
const props = defineProps<{
  quantity?: string | number | null
  minStockLevel?: string | number | null
}>()

const level = computed<'ok' | 'low' | 'empty'>(() => {
  const qty = Number(props.quantity ?? 0)
  const min = props.minStockLevel != null && props.minStockLevel !== '' ? Number(props.minStockLevel) : null
  if (qty <= 0) return 'empty'
  if (min != null && !Number.isNaN(min) && qty <= min) return 'low'
  return 'ok'
})

const label = computed(() => {
  if (level.value === 'empty') return 'Hết tồn'
  if (level.value === 'low') return 'Tồn thấp'
  return 'Đủ tồn'
})

const severityClass = computed(() => {
  if (level.value === 'empty') return 'bg-red-50 text-red-700 ring-red-200'
  if (level.value === 'low') return 'bg-amber-50 text-amber-800 ring-amber-200'
  return 'bg-emerald-50 text-emerald-700 ring-emerald-200'
})
</script>

<template>
  <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset" :class="severityClass">
    {{ label }}
  </span>
</template>
