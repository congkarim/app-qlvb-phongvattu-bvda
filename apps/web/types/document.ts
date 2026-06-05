export interface OCRJob {
  id: string
  document_id: string
  job_type: string
  status: string
  attempts: number
  reason?: string | null
  error_message?: string | null
  created_at: string
  updated_at: string
}

export interface AuditActor {
  id: string
  email: string
  full_name: string
}

export interface AuditLog {
  id: string
  actor_user_id?: string | null
  actor?: AuditActor | null
  action: string
  entity_type: string
  entity_id: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface DocumentItem {
  id: string
  title: string
  original_filename: string
  content_type?: string | null
  document_type: string
  classification_confidence?: number | null
  document_number?: string | null
  document_symbol?: string | null
  issued_date?: string | null
  issued_place?: string | null
  issuing_agency?: string | null
  excerpt?: string | null
  recipient?: string | null
  signer_name?: string | null
  signer_title?: string | null
  seals_present?: boolean | null
  attachment_present?: boolean | null
  page_count?: number | null
  metadata_source?: string | null
  metadata_reviewed_at?: string | null
  business_type?: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface DocumentMetadataInput {
  document_number?: string
  issued_date?: string
  issuing_agency?: string
  business_type?: string
}

export interface DocumentMetadataUpdateInput extends DocumentMetadataInput {
  title: string
  document_type: string
  classification_confidence?: number | null
  document_symbol?: string
  issued_place?: string
  excerpt?: string
  recipient?: string
  signer_name?: string
  signer_title?: string
  seals_present?: boolean | null
  attachment_present?: boolean | null
  page_count?: number | null
}

export interface DocumentPage {
  id: string
  page_number: number
  text: string
  confidence: number
  status: string
}

export interface DocumentFile {
  id: string
  document_id: string
  original_filename: string
  content_type?: string | null
  file_size: number
  file_order: number
  status: string
  created_at: string
  updated_at: string
}

export type SourceFilePreviewMode = 'pdf' | 'image' | 'text'

export interface SourceFilePreview {
  file: DocumentFile
  mode: SourceFilePreviewMode
  object_url: string
  text?: string
}

export interface DocumentChunk {
  id: string
  chunk_index: number
  text: string
  page_from?: number | null
  page_to?: number | null
  section_title?: string | null
  doc_group?: string | null
  chunk_level?: string | null
  section_role?: string | null
  section_path?: string[] | null
  chunk_confidence?: number | null
  requires_review: boolean
  qdrant_point_id?: string | null
}

export interface DocumentDetail extends DocumentItem {
  files: DocumentFile[]
  pages: DocumentPage[]
  chunks: DocumentChunk[]
  ocr_jobs: OCRJob[]
  audit_logs: AuditLog[]
}

export interface UploadResponse {
  document: DocumentItem
  ocr_job: OCRJob
}

export interface MultiFileUploadResponse {
  document: DocumentItem
  files: DocumentFile[]
  ocr_job: OCRJob
}

export interface SourceFileMutationResponse {
  document: DocumentItem
  files: DocumentFile[]
  ocr_job: OCRJob
}

export interface DocumentListFilters {
  q?: string
  status?: string
  document_type?: string
  business_type?: string
  sort_by?: 'created_at' | 'updated_at' | 'issued_date' | 'title' | 'status' | 'document_type' | 'business_type'
  sort_dir?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface ReprocessDocumentResponse {
  document: DocumentItem
  ocr_job: OCRJob
}

export interface ReviewQueueChunk {
  id: string
  document_id: string
  document_title: string
  document_number?: string | null
  issued_date?: string | null
  business_type?: string | null
  chunk_index: number
  text: string
  page_from?: number | null
  page_to?: number | null
  section_title?: string | null
  doc_group?: string | null
  chunk_level?: string | null
  section_role?: string | null
  section_path?: string[] | null
  chunk_confidence?: number | null
  requires_review: boolean
  created_at: string
  updated_at: string
}

export interface ReviewQueueFilters {
  limit?: number
  offset?: number
  section_role?: string
  document_id?: string
  max_confidence?: number | null
}

export interface SearchResult {
  document_id: string
  chunk_id: string
  score: number
  text: string
  title?: string | null
  document_type?: string | null
  document_number?: string | null
  issued_date?: string | null
  business_type?: string | null
  page_from?: number | null
  page_to?: number | null
  doc_group?: string | null
  section_role?: string | null
  section_path: string[]
  requires_review: boolean
}

export interface SemanticSearchFilters {
  limit?: number
  document_type?: string
  business_type?: string
  document_number?: string
  issued_date?: string
  doc_group?: string
  section_role?: string
  requires_review?: boolean | null
}
