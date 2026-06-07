<script setup lang="ts">
import type { RagCitation } from '~/types/document'

const props = defineProps<{
  question: string
  answer: string
  citations: RagCitation[]
  grounded: boolean
  confidence: number
  fallbackReason: string | null
  loading: boolean
  error: string
  hasAsked: boolean
  filterChangedHint?: boolean
}>()

const emit = defineEmits<{
  'update:question': [value: string]
  ask: []
  clear: []
}>()

const { formatBusinessType } = useCatalogs()

const isInsufficientEvidence = computed(
  () => !props.grounded && props.fallbackReason === 'insufficient_evidence'
)

function formatSectionRole(value?: string | null) {
  if (value === 'article') return 'Điều'
  if (value === 'clause') return 'Khoản'
  if (value === 'point') return 'Điểm'
  if (value === 'task') return 'Nhiệm vụ'
  if (value === 'appendix') return 'Phụ lục'
  if (value === 'recipient') return 'Nơi nhận'
  if (value === 'signature') return 'Chữ ký'
  if (value === 'unknown') return 'Không xác định'
  return value || ''
}

function formatCitationMeta(citation: RagCitation) {
  const parts = [
    citation.document_number ? `Số ${citation.document_number}` : '',
    citation.issued_date || '',
    citation.issuing_agency || '',
    citation.page_from
      ? `Trang ${citation.page_from}${citation.page_to && citation.page_to !== citation.page_from ? `-${citation.page_to}` : ''}`
      : '',
    formatSectionRole(citation.section_role),
    citation.section_path?.join(' > ') || ''
  ].filter(Boolean)
  return parts.length ? parts.join(' · ') : 'Chưa có metadata nguồn'
}

function formatConfidence(value: number) {
  return `${Math.round(value * 100)}%`
}
</script>

<template>
  <div class="space-y-3">
    <form class="space-y-3" @submit.prevent="emit('ask')">
      <div class="flex gap-3">
        <InputText
          :model-value="question"
          class="w-full"
          placeholder="Hỏi về nội dung văn bản, điều khoản, trách nhiệm..."
          @update:model-value="emit('update:question', $event ?? '')"
        />
        <Button
          type="submit"
          label="Hỏi"
          icon="pi pi-comments"
          :loading="loading"
          :disabled="!question.trim()"
        />
      </div>
      <p class="text-xs text-slate-500">
        Trả lời dựa trên các đoạn văn bản đã truy xuất (RAG extractive). Dùng chung bộ lọc semantic search phía trên.
      </p>
      <div class="flex flex-wrap gap-2">
        <Button
          type="button"
          label="Xóa"
          icon="pi pi-times"
          severity="secondary"
          :disabled="loading || (!hasAsked && !question.trim())"
          @click="emit('clear')"
        />
      </div>
    </form>

    <Message v-if="error" severity="error">{{ error }}</Message>
    <Message v-else-if="filterChangedHint" severity="info">
      Bộ lọc đã thay đổi. Bấm Hỏi lại để truy xuất với điều kiện mới.
    </Message>
    <p v-else-if="loading" class="text-sm text-slate-600">Đang trả lời...</p>

    <template v-else-if="hasAsked && !error">
      <Message v-if="isInsufficientEvidence" severity="warn" :closable="false">
        Không đủ căn cứ trong kho văn bản để trả lời chắc chắn.
      </Message>

      <div
        v-if="grounded"
        class="rounded border border-emerald-200 bg-emerald-50 p-4"
      >
        <p class="text-xs font-medium uppercase tracking-wide text-emerald-700">Câu trả lời</p>
        <p class="mt-2 whitespace-pre-wrap text-sm text-slate-800">{{ answer }}</p>
        <p class="mt-2 text-xs text-slate-500">Độ tin cậy: {{ formatConfidence(confidence) }}</p>
      </div>

      <div
        v-else-if="isInsufficientEvidence"
        class="rounded border border-amber-200 bg-amber-50 p-4"
      >
        <p class="text-xs font-medium uppercase tracking-wide text-amber-700">Giải thích</p>
        <p class="mt-2 whitespace-pre-wrap text-sm text-slate-700">{{ answer }}</p>
      </div>

      <div v-if="citations.length" class="space-y-3">
        <p class="text-sm font-medium text-slate-700">
          {{ grounded ? 'Nguồn trích dẫn' : 'Tham khảo yếu' }}
          <span class="font-normal text-slate-500">({{ citations.length }})</span>
        </p>
        <article
          v-for="citation in citations"
          :key="citation.chunk_id"
          class="rounded border border-slate-200 p-3"
        >
          <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <NuxtLink class="font-medium text-sky-700" :to="`/documents/${citation.document_id}`">
                {{ citation.title || citation.document_id }}
              </NuxtLink>
              <p class="mt-1 text-xs text-slate-500">
                Chunk {{ citation.chunk_id.slice(0, 8) }}… · Score {{ citation.score.toFixed(4) }}
                <span v-if="citation.business_type"> · {{ formatBusinessType(citation.business_type) }}</span>
              </p>
            </div>
            <NuxtLink
              :to="`/documents/${citation.document_id}`"
              class="inline-flex shrink-0 items-center gap-1 text-sm text-sky-700 hover:underline"
            >
              <i class="pi pi-external-link text-xs" />
              Mở văn bản
            </NuxtLink>
          </div>
          <blockquote class="mt-2 border-l-2 border-slate-300 pl-3 text-sm italic text-slate-700">
            {{ citation.quote }}
          </blockquote>
          <p class="mt-2 text-xs text-slate-500">{{ formatCitationMeta(citation) }}</p>
        </article>
      </div>

      <p v-else-if="grounded" class="text-sm text-slate-600">Không có citation kèm theo.</p>
    </template>
  </div>
</template>
