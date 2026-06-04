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
  document_number?: string | null
  issued_date?: string | null
  issuing_agency?: string | null
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

export interface DocumentChunk {
  id: string
  chunk_index: number
  text: string
  page_from?: number | null
  page_to?: number | null
  section_title?: string | null
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

export interface SearchResult {
  document_id: string
  chunk_id: string
  score: number
  text: string
  title?: string | null
  page_from?: number | null
  page_to?: number | null
}
