<script setup lang="ts">
const query = ref('')
const { results, loading, error, hasSearched, search } = useSemanticSearch()

async function submitSearch() {
  await search(query.value)
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
        <form class="flex gap-3" @submit.prevent="submitSearch">
          <InputText v-model="query" class="w-full" required placeholder="Tìm điều khoản, trách nhiệm, hợp đồng..." />
          <Button type="submit" label="Search" icon="pi pi-search" :loading="loading" :disabled="!query.trim()" />
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
              <span v-if="result.page_from"> · Trang {{ result.page_from }}{{ result.page_to && result.page_to !== result.page_from ? `-${result.page_to}` : '' }}</span>
            </p>
          </article>
        </div>
      </template>
    </Card>
  </section>
</template>
