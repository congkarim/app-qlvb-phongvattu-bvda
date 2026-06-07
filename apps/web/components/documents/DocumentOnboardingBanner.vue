<script setup lang="ts">
import type { OnboardingSuggestion } from '~/types/onboarding'
import { moduleLabel } from '~/utils/moduleOnboarding'

const props = defineProps<{
  suggestion: OnboardingSuggestion
  loading?: boolean
  applying?: boolean
  showApplyBusinessType: boolean
  createModuleLink: string
}>()

const emit = defineEmits<{
  applyBusinessType: []
}>()

const targetLabel = computed(() => {
  if (!props.suggestion.target_module) return 'Module'
  return moduleLabel(props.suggestion.target_module)
})

const confidenceText = computed(() => {
  const value = props.suggestion.module_confidence
  if (value === null || value === undefined) return ''
  return `${Math.round(value * 100)}%`
})
</script>

<template>
  <Card>
    <template #title>Gợi ý metadata module</template>
    <template #content>
      <p v-if="loading" class="text-sm text-slate-600">Đang tải gợi ý...</p>
      <template v-else>
        <Message
          v-if="suggestion.needs_metadata_review"
          class="mb-3"
          severity="warn"
        >
          Gợi ý cần xác nhận (confidence {{ confidenceText || 'thấp' }}). Hãy kiểm tra metadata văn bản trước khi tạo module.
        </Message>
        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <p class="text-xs text-slate-500">Loại nghiệp vụ gợi ý</p>
            <p class="font-medium">
              {{ suggestion.suggested_business_type || '-' }}
              <span v-if="confidenceText" class="text-xs text-slate-500">({{ confidenceText }})</span>
            </p>
          </div>
          <div>
            <p class="text-xs text-slate-500">Module đích</p>
            <p class="font-medium">{{ targetLabel }}</p>
          </div>
          <div v-if="suggestion.module_kind">
            <p class="text-xs text-slate-500">Phân loại module</p>
            <p class="font-medium">{{ suggestion.module_kind }}</p>
          </div>
        </div>
        <p v-if="suggestion.reasons.length" class="mt-2 text-xs text-slate-500">
          {{ suggestion.reasons.join(' · ') }}
        </p>
        <div class="mt-4 flex flex-wrap gap-2">
          <Button
            v-if="showApplyBusinessType"
            label="Áp dụng loại nghiệp vụ"
            icon="pi pi-check"
            size="small"
            :loading="applying"
            :disabled="applying"
            @click="emit('applyBusinessType')"
          />
          <NuxtLink :to="createModuleLink">
            <Button
              :label="`Tạo metadata ${targetLabel}`"
              icon="pi pi-plus"
              size="small"
              severity="secondary"
            />
          </NuxtLink>
        </div>
      </template>
    </template>
  </Card>
</template>
