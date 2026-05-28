<script setup lang="ts">
const emit = defineEmits<{
  selected: [file: File]
}>()

function handleSelect(event: { files: File[] }) {
  const [file] = event.files
  if (file) emit('selected', file)
}
</script>

<template>
  <FileUpload
    mode="basic"
    name="file"
    choose-label="Chọn file"
    :auto="false"
    custom-upload
    @select="handleSelect"
  />
</template>
