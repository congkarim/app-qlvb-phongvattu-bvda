<script setup lang="ts">
import { formatFileSize } from '~/utils/format'
import type { DocumentMetadataInput } from '~/types/document'

const uploadMode = ref<'single' | 'multi' | 'zip'>('single')
const selectedFiles = ref<File[]>([])
const documentTitle = ref('')
const metadata = reactive<Required<DocumentMetadataInput>>({
  document_number: '',
  issued_date: '',
  issuing_agency: '',
  business_type: ''
})
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
const businessTypeOptions = [
  { label: 'Chưa phân loại', value: '' },
  { label: 'Công văn đến', value: 'incoming_dispatch' },
  { label: 'Công văn đi', value: 'outgoing_dispatch' },
  { label: 'Hợp đồng', value: 'contract' },
  { label: 'Quyết định', value: 'decision' }
]

function currentMetadata(): DocumentMetadataInput {
  return {
    document_number: metadata.document_number,
    issued_date: metadata.issued_date,
    issuing_agency: metadata.issuing_agency,
    business_type: metadata.business_type
  }
}

function handleSelected(files: File[]) {
  selectedFiles.value = isMultiFileMode.value ? files : files.slice(0, 1)
  clearUploadResult()
}

async function submit() {
  if (!canSubmit.value) return

  const result = isMultiFileMode.value
    ? await uploadMultiFileDocument(selectedFiles.value, documentTitle.value, currentMetadata())
    : isZipMode.value
      ? await uploadZipDocument(selectedFiles.value[0], documentTitle.value, currentMetadata())
    : await uploadDocument(selectedFiles.value[0], documentTitle.value, currentMetadata())
  if (result) {
    await navigateTo(`/documents/${result.document.id}`)
  }
}

watch(uploadMode, () => {
  selectedFiles.value = []
  documentTitle.value = ''
  metadata.document_number = ''
  metadata.issued_date = ''
  metadata.issuing_agency = ''
  metadata.business_type = ''
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

          <div class="grid gap-3 sm:grid-cols-2">
            <div class="space-y-2">
              <label for="document-number" class="block text-sm font-medium text-slate-700">Số văn bản</label>
              <InputText
                id="document-number"
                v-model="metadata.document_number"
                class="w-full"
                placeholder="Ví dụ: 123/CV-VT"
                maxlength="128"
              />
            </div>
            <div class="space-y-2">
              <label for="issued-date" class="block text-sm font-medium text-slate-700">Ngày ban hành</label>
              <InputText id="issued-date" v-model="metadata.issued_date" class="w-full" type="date" />
            </div>
            <div class="space-y-2">
              <label for="issuing-agency" class="block text-sm font-medium text-slate-700">Đơn vị ban hành</label>
              <InputText
                id="issuing-agency"
                v-model="metadata.issuing_agency"
                class="w-full"
                placeholder="Ví dụ: Phòng Vật tư"
                maxlength="255"
              />
            </div>
            <div class="space-y-2">
              <label for="business-type" class="block text-sm font-medium text-slate-700">Loại nghiệp vụ</label>
              <select id="business-type" v-model="metadata.business_type" class="w-full rounded border border-slate-300 px-3 py-2 text-sm">
                <option v-for="option in businessTypeOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
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
