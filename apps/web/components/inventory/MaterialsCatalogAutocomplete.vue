<script setup lang="ts">
import type { MaterialsCatalogAutocompleteItem } from '~/types/materials-catalog'

const props = defineProps<{
  modelValue: string
  catalogItemId?: string | null
  placeholder?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:catalogItemId': [value: string | null]
  select: [item: MaterialsCatalogAutocompleteItem]
}>()

const { autocompleteItems, autocompleteLoading, searchActiveCatalog } = useMaterialsCatalog()

async function onComplete(event: { query: string }) {
  await searchActiveCatalog(event.query)
}

function onSelect(event: { value: MaterialsCatalogAutocompleteItem }) {
  const item = event.value
  emit('update:modelValue', item.name)
  emit('update:catalogItemId', item.id)
  emit('select', item)
}

function onInput(value: string) {
  emit('update:modelValue', value)
  if (!value.trim()) emit('update:catalogItemId', null)
}
</script>

<template>
  <AutoComplete
    :model-value="modelValue"
    :suggestions="autocompleteItems"
    option-label="name"
    class="w-full"
    input-class="w-full"
    :loading="autocompleteLoading"
    :placeholder="placeholder || 'Gõ để tìm vật tư...'"
    :disabled="disabled"
    @update:model-value="onInput"
    @complete="onComplete"
    @item-select="onSelect"
  />
</template>
