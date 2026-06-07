<script setup lang="ts">
import type { DocumentRelationsResponse, RelationType } from '~/types/document-relation'
import { formatDateTime } from '~/utils/format'
import {
  RELATION_TYPE_OPTIONS,
  documentRelationLink,
  formatIncomingRelationType,
  formatOutgoingRelationType,
  formatRelatedDocumentLabel
} from '~/utils/documentRelations'

const props = defineProps<{
  documentId: string
  relations: DocumentRelationsResponse | null
  loading?: boolean
  saving?: boolean
  deleting?: string
  error?: string
  targetSearchResults: Array<{
    id: string
    title: string
    document_number?: string | null
    document_type: string
  }>
  targetSearchLoading?: boolean
}>()

const emit = defineEmits<{
  create: [{ target_document_id: string; relation_type: RelationType; notes?: string }]
  delete: [relationId: string]
  searchTargets: [query: string]
}>()

const showAddForm = ref(false)
const targetDocumentId = ref('')
const targetSearchQuery = ref('')
const relationType = ref<RelationType>('references')
const notes = ref('')

const canSubmit = computed(() => {
  return Boolean(targetDocumentId.value.trim()) && !props.saving
})

function resetForm() {
  targetDocumentId.value = ''
  targetSearchQuery.value = ''
  relationType.value = 'references'
  notes.value = ''
}

function toggleAddForm() {
  showAddForm.value = !showAddForm.value
  if (!showAddForm.value) resetForm()
}

function submitSearchTargets() {
  emit('searchTargets', targetSearchQuery.value)
}

function selectTargetDocument(id: string) {
  targetDocumentId.value = id
}

function submitCreate() {
  if (!canSubmit.value) return
  emit('create', {
    target_document_id: targetDocumentId.value.trim(),
    relation_type: relationType.value,
    notes: notes.value.trim() || undefined
  })
}

function submitDelete(relationId: string, label: string) {
  const confirmed = window.confirm(`Xóa liên kết "${label}"?`)
  if (!confirmed) return
  emit('delete', relationId)
}

watch(
  () => props.saving,
  (value, previous) => {
    if (previous && !value && !props.error) {
      resetForm()
      showAddForm.value = false
    }
  }
)
</script>

<template>
  <Card>
    <template #title>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <span>Văn bản liên quan</span>
        <Button
          :label="showAddForm ? 'Đóng form' : 'Thêm liên kết'"
          :icon="showAddForm ? 'pi pi-times' : 'pi pi-plus'"
          size="small"
          severity="secondary"
          @click="toggleAddForm"
        />
      </div>
    </template>
    <template #content>
      <Message v-if="error" severity="error">{{ error }}</Message>
      <p v-if="loading" class="text-sm text-slate-600">Đang tải liên kết văn bản...</p>

      <form
        v-if="showAddForm"
        class="mb-4 space-y-3 rounded border border-slate-200 bg-slate-50 p-3"
        @submit.prevent="submitCreate"
      >
        <div class="space-y-2">
          <label for="relation-target-search" class="block text-sm font-medium text-slate-700">
            Tìm văn bản đích
          </label>
          <div class="flex flex-wrap gap-2">
            <InputText
              id="relation-target-search"
              v-model="targetSearchQuery"
              class="min-w-0 flex-1"
              placeholder="Số văn bản, tiêu đề..."
              maxlength="200"
              :disabled="saving"
            />
            <Button
              type="button"
              label="Tìm"
              icon="pi pi-search"
              severity="secondary"
              size="small"
              :loading="targetSearchLoading"
              :disabled="saving"
              @click="submitSearchTargets"
            />
          </div>
          <div v-if="targetSearchResults.length" class="space-y-1">
            <button
              v-for="item in targetSearchResults"
              :key="item.id"
              type="button"
              class="block w-full rounded border border-slate-200 bg-white px-3 py-2 text-left text-sm hover:border-sky-300 hover:bg-sky-50"
              :class="targetDocumentId === item.id ? 'border-sky-400 bg-sky-50' : ''"
              @click="selectTargetDocument(item.id)"
            >
              <span class="font-medium">{{ formatRelatedDocumentLabel(item) }}</span>
              <span class="mt-0.5 block text-xs text-slate-500">{{ item.id }}</span>
            </button>
          </div>
        </div>

        <div class="space-y-2">
          <label for="relation-target-id" class="block text-sm font-medium text-slate-700">
            ID văn bản đích *
          </label>
          <InputText
            id="relation-target-id"
            v-model="targetDocumentId"
            class="w-full"
            placeholder="UUID văn bản đích"
            maxlength="64"
            :disabled="saving"
          />
        </div>

        <div class="space-y-2">
          <label for="relation-type" class="block text-sm font-medium text-slate-700">Loại liên kết *</label>
          <select
            id="relation-type"
            v-model="relationType"
            class="w-full rounded border border-slate-300 px-3 py-2 text-sm"
            :disabled="saving"
          >
            <option v-for="option in RELATION_TYPE_OPTIONS" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="space-y-2">
          <label for="relation-notes" class="block text-sm font-medium text-slate-700">Ghi chú</label>
          <Textarea
            id="relation-notes"
            v-model="notes"
            class="w-full"
            rows="2"
            maxlength="2000"
            placeholder="Ghi chú tùy chọn"
            :disabled="saving"
          />
        </div>

        <Button
          type="submit"
          label="Thêm liên kết"
          icon="pi pi-link"
          :disabled="!canSubmit"
          :loading="saving"
        />
      </form>

      <template v-if="!loading && relations">
        <div class="space-y-4">
          <section>
            <h3 class="text-sm font-semibold text-slate-800">Liên kết đi</h3>
            <p v-if="!relations.outgoing.length" class="mt-2 text-sm text-slate-600">Chưa có liên kết đi.</p>
            <div v-else class="mt-2 space-y-2">
              <article
                v-for="item in relations.outgoing"
                :key="item.id"
                class="rounded border border-slate-200 p-3 text-sm"
              >
                <div class="flex flex-wrap items-start justify-between gap-2">
                  <div class="min-w-0 flex-1">
                    <Tag :value="formatOutgoingRelationType(item.relation_type)" severity="info" />
                    <NuxtLink
                      :to="documentRelationLink(item.target_document.id)"
                      class="mt-2 block font-medium text-sky-700 hover:underline"
                    >
                      {{ formatRelatedDocumentLabel(item.target_document) }}
                    </NuxtLink>
                    <p v-if="item.notes" class="mt-1 break-words text-slate-600">{{ item.notes }}</p>
                    <p class="mt-1 text-xs text-slate-500">{{ formatDateTime(item.created_at) }}</p>
                  </div>
                  <Button
                    icon="pi pi-trash"
                    severity="danger"
                    size="small"
                    text
                    :loading="deleting === item.id"
                    :disabled="Boolean(deleting)"
                    @click="submitDelete(item.id, formatOutgoingRelationType(item.relation_type))"
                  />
                </div>
              </article>
            </div>
          </section>

          <section>
            <h3 class="text-sm font-semibold text-slate-800">Liên kết đến</h3>
            <p v-if="!relations.incoming.length" class="mt-2 text-sm text-slate-600">Chưa có liên kết đến.</p>
            <div v-else class="mt-2 space-y-2">
              <article
                v-for="item in relations.incoming"
                :key="item.id"
                class="rounded border border-slate-200 p-3 text-sm"
              >
                <div class="flex flex-wrap items-start justify-between gap-2">
                  <div class="min-w-0 flex-1">
                    <Tag :value="formatIncomingRelationType(item.relation_type)" severity="secondary" />
                    <NuxtLink
                      :to="documentRelationLink(item.source_document.id)"
                      class="mt-2 block font-medium text-sky-700 hover:underline"
                    >
                      {{ formatRelatedDocumentLabel(item.source_document) }}
                    </NuxtLink>
                    <p v-if="item.notes" class="mt-1 break-words text-slate-600">{{ item.notes }}</p>
                    <p class="mt-1 text-xs text-slate-500">{{ formatDateTime(item.created_at) }}</p>
                  </div>
                  <Button
                    icon="pi pi-trash"
                    severity="danger"
                    size="small"
                    text
                    :loading="deleting === item.id"
                    :disabled="Boolean(deleting)"
                    @click="submitDelete(item.id, formatIncomingRelationType(item.relation_type))"
                  />
                </div>
              </article>
            </div>
          </section>
        </div>
      </template>
    </template>
  </Card>
</template>
