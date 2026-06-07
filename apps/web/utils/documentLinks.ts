export function buildDocumentChunkUrl(documentId: string, chunkId?: string | null): string {
  const base = `/documents/${documentId}`
  if (!chunkId?.trim()) return base
  return `${base}#chunk-${chunkId.trim()}`
}
