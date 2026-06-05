import type {
  DocumentDetail,
  DocumentFile,
  DocumentItem,
  DocumentListFilters,
  DocumentMetadataInput,
  DocumentMetadataUpdateInput,
  MultiFileUploadResponse,
  ReprocessDocumentResponse,
  ReviewQueueChunk,
  ReviewQueueFilters,
  SourceFilePreview,
  SourceFileMutationResponse,
  UploadResponse
} from '~/types/document'
import { createDocumentService } from '~/services/document.service'

export function useDocuments() {
  const documents = ref<DocumentItem[]>([])
  const document = ref<DocumentDetail | null>(null)
  const reviewQueue = ref<ReviewQueueChunk[]>([])
  const uploadResult = ref<UploadResponse | null>(null)
  const multiFileUploadResult = ref<MultiFileUploadResponse | null>(null)
  const loading = ref(false)
  const reviewQueueLoading = ref(false)
  const metadataLoading = ref(false)
  const reprocessLoading = ref(false)
  const sourceFileLoading = ref(false)
  const sourceFileViewLoading = ref('')
  const sourceFilePreviewLoading = ref('')
  const chunkReviewLoading = ref('')
  const sourceFilePreview = ref<SourceFilePreview | null>(null)
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

  async function fetchReviewQueue(filters: ReviewQueueFilters = {}): Promise<ReviewQueueChunk[]> {
    reviewQueueLoading.value = true
    error.value = ''
    try {
      reviewQueue.value = await service.listReviewQueue(filters)
      return reviewQueue.value
    } catch {
      error.value = 'Không tải được review queue'
      reviewQueue.value = []
      return []
    } finally {
      reviewQueueLoading.value = false
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

  async function openSourceFile(id: string, file: DocumentFile): Promise<boolean> {
    sourceFileViewLoading.value = file.id
    error.value = ''
    try {
      const blob = await service.downloadSourceFile(id, file)
      const objectUrl = URL.createObjectURL(blob)
      if (isBrowserPreviewable(file)) {
        const opened = window.open(objectUrl, '_blank', 'noopener')
        if (!opened) downloadBlob(objectUrl, file.original_filename)
      } else {
        downloadBlob(objectUrl, file.original_filename)
      }
      setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000)
      return true
    } catch {
      error.value = 'Không mở được tệp nguồn'
      return false
    } finally {
      sourceFileViewLoading.value = ''
    }
  }

  async function previewSourceFile(id: string, file: DocumentFile): Promise<boolean> {
    sourceFilePreviewLoading.value = file.id
    error.value = ''
    try {
      const blob = await service.downloadSourceFile(id, file)
      const previewMode = sourceFilePreviewMode(file, blob)
      const objectUrl = URL.createObjectURL(blob)
      if (!previewMode) {
        clearSourceFilePreview()
        downloadBlob(objectUrl, file.original_filename)
        setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000)
        return true
      }

      clearSourceFilePreview()
      sourceFilePreview.value = {
        file,
        mode: previewMode,
        object_url: objectUrl,
        text: previewMode === 'text' ? await blob.text() : undefined
      }
      return true
    } catch {
      error.value = 'Không preview được tệp nguồn'
      return false
    } finally {
      sourceFilePreviewLoading.value = ''
    }
  }

  function clearSourceFilePreview() {
    if (sourceFilePreview.value?.object_url) {
      URL.revokeObjectURL(sourceFilePreview.value.object_url)
    }
    sourceFilePreview.value = null
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

  async function markChunkReviewed(id: string, chunkId: string): Promise<boolean> {
    chunkReviewLoading.value = chunkId
    error.value = ''
    try {
      const reviewedChunk = await service.markChunkReviewed(id, chunkId)
      if (document.value?.id === id) {
        document.value = {
          ...document.value,
          chunks: document.value.chunks.map((chunk) => (chunk.id === reviewedChunk.id ? reviewedChunk : chunk))
        }
      }
      return true
    } catch {
      error.value = 'Không đánh dấu được chunk đã review'
      return false
    } finally {
      chunkReviewLoading.value = ''
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

  function isBrowserPreviewable(file: DocumentFile): boolean {
    const contentType = (file.content_type || '').toLowerCase()
    const filename = file.original_filename.toLowerCase()
    if (contentType.startsWith('image/') || contentType.startsWith('text/') || contentType === 'application/pdf') {
      return true
    }
    return ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.txt', '.md', '.csv'].some((ext) => filename.endsWith(ext))
  }

  function sourceFilePreviewMode(file: DocumentFile, blob?: Blob): SourceFilePreview['mode'] | null {
    const contentType = (blob?.type || file.content_type || '').toLowerCase()
    const filename = file.original_filename.toLowerCase()
    if (contentType === 'application/pdf' || filename.endsWith('.pdf')) return 'pdf'
    if (contentType.startsWith('image/') || ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'].some((ext) => filename.endsWith(ext))) {
      return 'image'
    }
    if (contentType.startsWith('text/') || ['.txt', '.md', '.csv', '.json', '.xml'].some((ext) => filename.endsWith(ext))) {
      return 'text'
    }
    return null
  }

  function downloadBlob(objectUrl: string, filename: string) {
    const link = window.document.createElement('a')
    link.href = objectUrl
    link.download = filename
    link.rel = 'noopener'
    window.document.body.appendChild(link)
    link.click()
    link.remove()
  }

  return {
    documents,
    document,
    reviewQueue,
    uploadResult,
    multiFileUploadResult,
    loading,
    reviewQueueLoading,
    metadataLoading,
    reprocessLoading,
    sourceFileLoading,
    sourceFileViewLoading,
    sourceFilePreviewLoading,
    chunkReviewLoading,
    sourceFilePreview,
    error,
    fetchDocuments,
    fetchDocument,
    fetchReviewQueue,
    uploadDocument,
    uploadMultiFileDocument,
    uploadZipDocument,
    updateDocumentMetadata,
    addSourceFiles,
    openSourceFile,
    previewSourceFile,
    clearSourceFilePreview,
    reorderSourceFiles,
    deleteSourceFile,
    reprocessDocument,
    markChunkReviewed,
    clearUploadResult
  }
}
