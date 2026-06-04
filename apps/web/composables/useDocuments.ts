import type {
  DocumentDetail,
  DocumentItem,
  DocumentListFilters,
  DocumentMetadataInput,
  DocumentMetadataUpdateInput,
  MultiFileUploadResponse,
  ReprocessDocumentResponse,
  SourceFileMutationResponse,
  UploadResponse
} from '~/types/document'
import { createDocumentService } from '~/services/document.service'

export function useDocuments() {
  const documents = ref<DocumentItem[]>([])
  const document = ref<DocumentDetail | null>(null)
  const uploadResult = ref<UploadResponse | null>(null)
  const multiFileUploadResult = ref<MultiFileUploadResponse | null>(null)
  const loading = ref(false)
  const metadataLoading = ref(false)
  const reprocessLoading = ref(false)
  const sourceFileLoading = ref(false)
  const error = ref('')
  const service = createDocumentService()

  async function fetchDocuments(filters: DocumentListFilters = {}, options: { silent?: boolean } = {}) {
    if (!options.silent) loading.value = true
    error.value = ''
    try {
      documents.value = await service.list(filters)
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

  async function uploadDocument(file: File, title = '', metadata: DocumentMetadataInput = {}): Promise<UploadResponse | null> {
    loading.value = true
    error.value = ''
    try {
      uploadResult.value = await service.upload(file, 'document', title, metadata)
      return uploadResult.value
    } catch {
      error.value = 'Upload không thành công'
      return null
    } finally {
      loading.value = false
    }
  }

  async function uploadMultiFileDocument(
    files: File[],
    title: string,
    metadata: DocumentMetadataInput = {}
  ): Promise<MultiFileUploadResponse | null> {
    loading.value = true
    error.value = ''
    try {
      multiFileUploadResult.value = await service.uploadMultiFile(files, title, 'document', metadata)
      return multiFileUploadResult.value
    } catch {
      error.value = 'Upload nhiều tệp không thành công'
      return null
    } finally {
      loading.value = false
    }
  }

  async function uploadZipDocument(
    zipFile: File,
    title: string,
    metadata: DocumentMetadataInput = {}
  ): Promise<MultiFileUploadResponse | null> {
    loading.value = true
    error.value = ''
    try {
      multiFileUploadResult.value = await service.uploadZip(zipFile, title, 'document', metadata)
      return multiFileUploadResult.value
    } catch {
      error.value = 'Upload zip không thành công'
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateDocumentMetadata(
    id: string,
    metadata: DocumentMetadataUpdateInput
  ): Promise<DocumentItem | null> {
    metadataLoading.value = true
    error.value = ''
    try {
      const result = await service.updateMetadata(id, metadata)
      if (document.value?.id === id) {
        document.value = {
          ...document.value,
          ...result
        }
      }
      return result
    } catch {
      error.value = 'Không cập nhật được metadata'
      return null
    } finally {
      metadataLoading.value = false
    }
  }

  async function addSourceFiles(id: string, files: File[]): Promise<SourceFileMutationResponse | null> {
    sourceFileLoading.value = true
    error.value = ''
    try {
      const result = await service.addSourceFiles(id, files)
      await applySourceFileMutation(id, result)
      return result
    } catch {
      error.value = 'Không thêm được tệp nguồn'
      return null
    } finally {
      sourceFileLoading.value = false
    }
  }

  async function reorderSourceFiles(id: string, fileIds: string[]): Promise<SourceFileMutationResponse | null> {
    sourceFileLoading.value = true
    error.value = ''
    try {
      const result = await service.reorderSourceFiles(id, fileIds)
      await applySourceFileMutation(id, result)
      return result
    } catch {
      error.value = 'Không đổi được thứ tự tệp nguồn'
      return null
    } finally {
      sourceFileLoading.value = false
    }
  }

  async function deleteSourceFile(id: string, fileId: string): Promise<SourceFileMutationResponse | null> {
    sourceFileLoading.value = true
    error.value = ''
    try {
      const result = await service.deleteSourceFile(id, fileId)
      await applySourceFileMutation(id, result)
      return result
    } catch {
      error.value = 'Không xóa được tệp nguồn'
      return null
    } finally {
      sourceFileLoading.value = false
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

  async function applySourceFileMutation(id: string, result: SourceFileMutationResponse) {
    if (document.value?.id !== id) return
    document.value = {
      ...document.value,
      ...result.document,
      files: result.files,
      ocr_jobs: [result.ocr_job, ...document.value.ocr_jobs]
    }
  }

  return {
    documents,
    document,
    uploadResult,
    multiFileUploadResult,
    loading,
    metadataLoading,
    reprocessLoading,
    sourceFileLoading,
    error,
    fetchDocuments,
    fetchDocument,
    uploadDocument,
    uploadMultiFileDocument,
    uploadZipDocument,
    updateDocumentMetadata,
    addSourceFiles,
    reorderSourceFiles,
    deleteSourceFile,
    reprocessDocument,
    clearUploadResult
  }
}
