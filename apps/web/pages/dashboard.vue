<script setup lang="ts">
import type { SemanticSearchFilters } from '~/types/document'

const query = ref('')
const { results, loading, error, hasSearched, search } = useSemanticSearch()

const filters = reactive<SemanticSearchFilters>({
  limit: 10,
  business_type: '',
  document_number: '',
  issued_date: '',
  doc_group: '',
  section_role: '',
  requires_review: null
})

const businessTypeOptions = [
  { label: 'Tất cả nghiệp vụ', value: '' },
  { label: 'Công văn đến', value: 'incoming_dispatch' },
  { label: 'Công văn đi', value: 'outgoing_dispatch' },
  { label: 'Hợp đồng', value: 'contract' },
  { label: 'Quyết định', value: 'decision' }
]

const docGroupOptions = [
  { label: 'Tất cả nhóm', value: '' },
  { label: 'A - Quy phạm', value: 'A' },
  { label: 'B - Công văn', value: 'B' },
  { label: 'C - Quyết định', value: 'C' },
  { label: 'D - Biểu mẫu', value: 'D' },
  { label: 'E - Khác/review', value: 'E' }
]

const sectionRoleOptions = [
  { label: 'Tất cả vai trò', value: '' },
  { label: 'Điều', value: 'article' },
  { label: 'Khoản', value: 'clause' },
  { label: 'Điểm', value: 'point' },
  { label: 'Nhiệm vụ', value: 'task' },
  { label: 'Nơi nhận', value: 'recipient' },
  { label: 'Chữ ký', value: 'signature' },
  { label: 'Không xác định', value: 'unknown' }
]

const reviewOptions: Array<{ label: string; value: boolean | null }> = [
  { label: 'Tất cả review', value: null },
  { label: 'Cần review', value: true },
  { label: 'Đã ổn định', value: false }
]

async function submitSearch() {
  await search(query.value, filters)
}

function resetFilters() {
  filters.limit = 10
  filters.business_type = ''
  filters.document_number = ''
  filters.issued_date = ''
  filters.doc_group = ''
  filters.section_role = ''
  filters.requires_review = null
}

function formatBusinessType(value?: string | null) {
  return businessTypeOptions.find((option) => option.value === value)?.label || value || '-'
}

function formatChunkMeta(result: { doc_group?: string | null; section_role?: string | null; section_path?: string[] }) {
  const parts = [result.doc_group, result.section_role, result.section_path?.join(' > ')].filter(Boolean)
  return parts.length ? parts.join(' · ') : 'Chưa có metadata chunk'
}
</script>

<template>
  <section class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold">Dashboard</h1>
      <p class="mt-1 text-sm text-slate-600">Upload, OCR và semantic search skeleton.</p>
    </div>

    <Card>
      <template #title>Semantic search</template>
      <template #content>
        <form class="space-y-3" @submit.prevent="submitSearch">
          <div class="flex gap-3">
            <InputText v-model="query" class="w-full" required placeholder="Tìm điều khoản, trách nhiệm, hợp đồng..." />
            <Button type="submit" label="Search" icon="pi pi-search" :loading="loading" :disabled="!query.trim()" />
          </div>
          <div class="grid gap-3 md:grid-cols-6">
            <select v-model="filters.business_type" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in businessTypeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <InputText v-model="filters.document_number" placeholder="Số văn bản" />
            <InputText v-model="filters.issued_date" type="date" />
            <select v-model="filters.doc_group" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in docGroupOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <select v-model="filters.section_role" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in sectionRoleOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <select v-model="filters.requires_review" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option v-for="option in reviewOptions" :key="String(option.value)" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          <div class="flex flex-wrap gap-2">
            <select v-model.number="filters.limit" class="rounded border border-slate-300 px-3 py-2 text-sm">
              <option :value="5">5 kết quả</option>
              <option :value="10">10 kết quả</option>
              <option :value="20">20 kết quả</option>
              <option :value="50">50 kết quả</option>
            </select>
            <Button type="button" label="Xóa lọc" icon="pi pi-times" severity="secondary" :disabled="loading" @click="resetFilters" />
          </div>
        </form>
        <Message v-if="error" class="mt-4" severity="error">{{ error }}</Message>
        <p v-else-if="loading" class="mt-4 text-sm text-slate-600">Đang tìm kiếm...</p>
        <p v-else-if="hasSearched && !results.length" class="mt-4 text-sm text-slate-600">Không có kết quả phù hợp.</p>
        <div class="mt-5 space-y-3">
          <article v-for="result in results" :key="result.chunk_id" class="border-b border-slate-200 pb-3">
            <NuxtLink class="font-medium text-sky-700" :to="`/documents/${result.document_id}`">
              {{ result.title || result.document_id }}
            </NuxtLink>
            <p class="mt-1 text-sm text-slate-700">{{ result.text }}</p>
            <p class="mt-1 text-xs text-slate-500">
              Score: {{ result.score.toFixed(4) }}
              <span v-if="result.business_type"> · {{ formatBusinessType(result.business_type) }}</span>
              <span v-if="result.document_number"> · Số {{ result.document_number }}</span>
              <span v-if="result.issued_date"> · {{ result.issued_date }}</span>
              <span v-if="result.page_from"> · Trang {{ result.page_from }}{{ result.page_to && result.page_to !== result.page_from ? `-${result.page_to}` : '' }}</span>
            </p>
            <p class="mt-1 text-xs text-slate-500">
              {{ formatChunkMeta(result) }}
              <Tag v-if="result.requires_review" class="ml-2" value="review" severity="warn" />
            </p>
          </article>
        </div>
      </template>
    </Card>
  </section>
</template>
