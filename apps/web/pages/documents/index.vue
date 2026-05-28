<script setup lang="ts">
const { documents, loading, error, fetchDocuments } = useDocuments()

onMounted(fetchDocuments)
</script>

<template>
  <section class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold">Documents</h1>
        <p class="mt-1 text-sm text-slate-600">Danh sách văn bản đã upload.</p>
      </div>
      <div class="flex gap-2">
        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" :loading="loading" @click="fetchDocuments" />
        <NuxtLink to="/upload">
          <Button label="Upload" icon="pi pi-upload" />
        </NuxtLink>
      </div>
    </div>
    <Message v-if="error" severity="error">{{ error }}</Message>
    <BaseDataTable :rows="documents" :loading="loading" />
  </section>
</template>
