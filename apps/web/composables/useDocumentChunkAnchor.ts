import type { DocumentChunk } from '~/types/document'

const CHUNK_HASH_PREFIX = '#chunk-'
const HIGHLIGHT_MS = 2500

type ChunkFilter = 'all' | 'review' | 'appendix' | 'appendix_review'

export function parseChunkIdFromHash(hash: string): string | null {
  if (!hash.startsWith(CHUNK_HASH_PREFIX)) return null
  const chunkId = hash.slice(CHUNK_HASH_PREFIX.length).trim()
  return chunkId || null
}

export function chunkDomId(chunkId: string): string {
  return `chunk-${chunkId}`
}

function chunkMatchesFilter(chunk: DocumentChunk, filter: ChunkFilter): boolean {
  if (filter === 'review') return chunk.requires_review
  if (filter === 'appendix') return chunk.section_role === 'appendix'
  if (filter === 'appendix_review') {
    return chunk.section_role === 'appendix' && chunk.requires_review
  }
  return true
}

export function useDocumentChunkAnchor(options: {
  allChunks: Ref<DocumentChunk[]>
  chunkFilter: Ref<ChunkFilter>
}) {
  const route = useRoute()
  const highlightedChunkId = ref<string | null>(null)
  const chunkAnchorMiss = ref(false)
  const lastFocusedHash = ref('')
  let highlightTimer: ReturnType<typeof setTimeout> | undefined

  function clearHighlightTimer() {
    if (!highlightTimer) return
    clearTimeout(highlightTimer)
    highlightTimer = undefined
  }

  function scheduleHighlightClear() {
    clearHighlightTimer()
    highlightTimer = setTimeout(() => {
      highlightedChunkId.value = null
    }, HIGHLIGHT_MS)
  }

  async function focusChunkFromHash() {
    const chunkId = parseChunkIdFromHash(route.hash)
    if (!chunkId) {
      chunkAnchorMiss.value = false
      highlightedChunkId.value = null
      lastFocusedHash.value = ''
      return
    }

    const chunk = options.allChunks.value.find((item) => item.id === chunkId)
    if (!chunk) {
      chunkAnchorMiss.value = true
      highlightedChunkId.value = null
      return
    }

    if (!chunkMatchesFilter(chunk, options.chunkFilter.value)) {
      options.chunkFilter.value = 'all'
      await nextTick()
    }

    const element = document.getElementById(chunkDomId(chunkId))
    if (!element) {
      chunkAnchorMiss.value = true
      highlightedChunkId.value = null
      return
    }

    chunkAnchorMiss.value = false
    element.scrollIntoView({ block: 'start', behavior: 'auto' })
    highlightedChunkId.value = chunkId
    lastFocusedHash.value = route.hash
    scheduleHighlightClear()
  }

  watch(
    () => route.hash,
    () => {
      void focusChunkFromHash()
    }
  )

  watch(options.allChunks, () => {
    if (!route.hash.startsWith(CHUNK_HASH_PREFIX)) return
    if (chunkAnchorMiss.value || lastFocusedHash.value !== route.hash) {
      void focusChunkFromHash()
    }
  })

  onBeforeUnmount(() => {
    clearHighlightTimer()
  })

  return {
    highlightedChunkId,
    chunkAnchorMiss,
    focusChunkFromHash
  }
}
