import type {
  DocumentDetail,
  DocumentItem,
  MultiFileUploadResponse,
  ReprocessDocumentResponse,
  UploadResponse
} from '~/types/document'
import { createDocumentService } from '~/services/document.service'

export function useDocuments() {
  const documents = ref<DocumentItem[]>([])
  const document = ref<DocumentDetail | null>(null)
  const uploadResult = ref<UploadResponse | null>(null)
  const multiFileUploadResult = ref<MultiFileUploadResponse | null>(null)
  const loading = ref(false)
  const reprocessLoading = ref(false)
  const error = ref('')
  const service = createDocumentService()

  async function fetchDocuments(options: { silent?: boolean } = {}) {
    if (!options.silent) loading.value = true
    error.value = ''
    try {
      documents.value = await service.list()
    } catch {
      error.value = 'Không tải được danh sách văn bản'
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  async function fetchDocument(id: string, options: { silent?: boolean } = {}) {
    if (!options.silent) loading.value = true
    error.value = ''
    try {
      document.value = await service.get(id)
    } catch {
      error.value = 'Không tải được chi tiết văn bản'
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  async function uploadDocument(file: File, title = ''): Promise<UploadResponse | null> {
    loading.value = true
    error.value = ''
    try {
      uploadResult.value = await service.upload(file, 'document', title)
      return uploadResult.value
    } catch {
      error.value = 'Upload không thành công'
      return null
    } finally {
      loading.value = false
    }
  }

  async function uploadMultiFileDocument(files: File[], title: string): Promise<MultiFileUploadResponse | null> {
    loading.value = true
    error.value = ''
    try {
      multiFileUploadResult.value = await service.uploadMultiFile(files, title)
      return multiFileUploadResult.value
    } catch {
      error.value = 'Upload nhiều tệp không thành công'
      return null
    } finally {
      loading.value = false
    }
  }

  async function reprocessDocument(id: string, reason: string): Promise<ReprocessDocumentResponse | null> {
    reprocessLoading.value = true
    error.value = ''
    try {
      const result = await service.reprocess(id, reason)
      if (document.value?.id === id) {
        document.value = {
          ...document.value,
          ...result.document,
          ocr_jobs: [result.ocr_job, ...document.value.ocr_jobs]
        }
      }
      return result
    } catch {
      error.value = 'Không tạo được job reprocess'
      return null
    } finally {
      reprocessLoading.value = false
    }
  }

  function clearUploadResult() {
    uploadResult.value = null
    multiFileUploadResult.value = null
  }

  return {
    documents,
    document,
    uploadResult,
    multiFileUploadResult,
    loading,
    reprocessLoading,
    error,
    fetchDocuments,
    fetchDocument,
    uploadDocument,
    uploadMultiFileDocument,
    reprocessDocument,
    clearUploadResult
  }
}
