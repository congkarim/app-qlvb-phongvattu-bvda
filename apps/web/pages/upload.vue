<script setup lang="ts">
import { formatFileSize } from '~/utils/format'

const selectedFile = ref<File | null>(null)
const { uploadResult, loading, error, uploadDocument, clearUploadResult } = useDocuments()

function handleSelected(file: File) {
  selectedFile.value = file
  clearUploadResult()
}

async function submit() {
  if (!selectedFile.value) return

  const result = await uploadDocument(selectedFile.value)
  if (result) {
    await navigateTo(`/documents/${result.document.id}`)
  }
}
</script>

<template>
  <section class="max-w-2xl space-y-5">
    <div>
      <h1 class="text-2xl font-semibold">Upload văn bản</h1>
      <p class="mt-1 text-sm text-slate-600">File được lưu local và tạo OCR job pending.</p>
    </div>

    <Card>
      <template #content>
        <div class="space-y-4">
          <BaseUploadDropzone @selected="handleSelected" />
          <div v-if="selectedFile" class="rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
            <p class="font-medium">{{ selectedFile.name }}</p>
            <p class="mt-1">Dung lượng: {{ formatFileSize(selectedFile.size) }}</p>
            <p>Content type: {{ selectedFile.type || 'Không xác định' }}</p>
          </div>
          <Message v-if="error" severity="error">{{ error }}</Message>
          <Button label="Upload" icon="pi pi-upload" :disabled="!selectedFile" :loading="loading" @click="submit" />
        </div>
      </template>
    </Card>

    <Card v-if="uploadResult">
      <template #title>OCR job đã tạo</template>
      <template #content>
        <p class="text-sm">Document: {{ uploadResult.document.id }}</p>
        <p class="text-sm">Job: {{ uploadResult.ocr_job.id }}</p>
        <p class="text-sm">Trạng thái job: {{ uploadResult.ocr_job.status }}</p>
        <NuxtLink class="mt-3 inline-block text-sky-700" :to="`/documents/${uploadResult.document.id}`">
          Xem chi tiết
        </NuxtLink>
      </template>
    </Card>
  </section>
</template>
