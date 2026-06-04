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

export interface DocumentItem {
  id: string
  title: string
  original_filename: string
  content_type?: string | null
  document_type: string
  status: string
  created_at: string
  updated_at: string
}

export interface DocumentPage {
  id: string
  page_number: number
  text: string
  confidence: number
  status: string
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
  pages: DocumentPage[]
  chunks: DocumentChunk[]
  ocr_jobs: OCRJob[]
}

export interface UploadResponse {
  document: DocumentItem
  ocr_job: OCRJob
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
