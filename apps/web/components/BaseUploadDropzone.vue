<script setup lang="ts">
defineProps<{
  multiple?: boolean
}>()

const emit = defineEmits<{
  selected: [files: File[]]
}>()

function handleSelect(event: { files: File[] }) {
  if (event.files.length) emit('selected', event.files)
}
</script>

<template>
  <FileUpload
    mode="basic"
    name="file"
    choose-label="Chọn file"
    :auto="false"
    :multiple="multiple"
    custom-upload
    @select="handleSelect"
  />
</template>
