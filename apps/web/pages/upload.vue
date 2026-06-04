<script setup lang="ts">
import { formatFileSize } from '~/utils/format'

const uploadMode = ref<'single' | 'multi' | 'zip'>('single')
const selectedFiles = ref<File[]>([])
const documentTitle = ref('')
const {
  uploadResult,
  multiFileUploadResult,
  loading,
  error,
  uploadDocument,
  uploadMultiFileDocument,
  uploadZipDocument,
  clearUploadResult
} = useDocuments()

const isMultiFileMode = computed(() => uploadMode.value === 'multi')
const isZipMode = computed(() => uploadMode.value === 'zip')
const requiresTitle = computed(() => uploadMode.value !== 'single')
const canSubmit = computed(() => {
  if (!selectedFiles.value.length) return false
  if (requiresTitle.value) return Boolean(documentTitle.value.trim())
  return true
})

const uploadSummary = computed(() => multiFileUploadResult.value || uploadResult.value)

function handleSelected(files: File[]) {
  selectedFiles.value = isMultiFileMode.value ? files : files.slice(0, 1)
  clearUploadResult()
}

async function submit() {
  if (!canSubmit.value) return

  const result = isMultiFileMode.value
    ? await uploadMultiFileDocument(selectedFiles.value, documentTitle.value)
    : isZipMode.value
      ? await uploadZipDocument(selectedFiles.value[0], documentTitle.value)
    : await uploadDocument(selectedFiles.value[0], documentTitle.value)
  if (result) {
    await navigateTo(`/documents/${result.document.id}`)
  }
}

watch(uploadMode, () => {
  selectedFiles.value = []
  documentTitle.value = ''
  clearUploadResult()
})
</script>

<template>
  <section class="max-w-3xl space-y-5">
    <div>
      <h1 class="text-2xl font-semibold">Upload văn bản</h1>
      <p class="mt-1 text-sm text-slate-600">File được lưu local và tạo OCR job pending.</p>
    </div>

    <Card>
      <template #content>
        <div class="space-y-5">
          <div class="inline-flex rounded border border-slate-200 bg-slate-50 p-1 text-sm">
            <button
              type="button"
              class="rounded px-3 py-2"
              :class="uploadMode === 'single' ? 'bg-white font-medium shadow-sm' : 'text-slate-600'"
              @click="uploadMode = 'single'"
            >
              Một tệp
            </button>
            <button
              type="button"
              class="rounded px-3 py-2"
              :class="uploadMode === 'multi' ? 'bg-white font-medium shadow-sm' : 'text-slate-600'"
              @click="uploadMode = 'multi'"
            >
              Nhiều tệp cùng văn bản
            </button>
            <button
              type="button"
              class="rounded px-3 py-2"
              :class="uploadMode === 'zip' ? 'bg-white font-medium shadow-sm' : 'text-slate-600'"
              @click="uploadMode = 'zip'"
            >
              Zip cùng văn bản
            </button>
          </div>

          <div class="space-y-2">
            <label for="document-title" class="block text-sm font-medium text-slate-700">
              Tên văn bản <span v-if="requiresTitle" class="text-red-600">*</span>
            </label>
            <InputText
              id="document-title"
              v-model="documentTitle"
              class="w-full"
              :placeholder="requiresTitle ? 'Ví dụ: Công văn số 123/CV-VT' : 'Để trống sẽ tự lấy theo tên file'"
              maxlength="512"
            />
          </div>

          <BaseUploadDropzone :multiple="isMultiFileMode" @selected="handleSelected" />
          <div v-if="selectedFiles.length" class="rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
            <p class="font-medium">
              {{ isZipMode ? 'Tệp zip đã chọn' : `Tệp nguồn đã chọn: ${selectedFiles.length}` }}
            </p>
            <ul class="mt-2 space-y-2">
              <li v-for="(file, index) in selectedFiles" :key="`${file.name}-${index}`" class="rounded bg-white p-2">
                <p class="break-words font-medium">{{ index + 1 }}. {{ file.name }}</p>
                <p class="mt-1 text-xs text-slate-600">
                  {{ formatFileSize(file.size) }} · {{ file.type || 'Không xác định' }}
                </p>
              </li>
            </ul>
          </div>
          <Message v-if="error" severity="error">{{ error }}</Message>
          <Button label="Upload" icon="pi pi-upload" :disabled="!canSubmit" :loading="loading" @click="submit" />
        </div>
      </template>
    </Card>

    <Card v-if="uploadSummary">
      <template #title>OCR job đã tạo</template>
      <template #content>
        <p class="text-sm">Document: {{ uploadSummary.document.id }}</p>
        <p class="text-sm">Job: {{ uploadSummary.ocr_job.id }}</p>
        <p class="text-sm">Trạng thái job: {{ uploadSummary.ocr_job.status }}</p>
        <NuxtLink class="mt-3 inline-block text-sky-700" :to="`/documents/${uploadSummary.document.id}`">
          Xem chi tiết
        </NuxtLink>
      </template>
    </Card>
  </section>
</template>
