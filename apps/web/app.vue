<script setup lang="ts">
const authStore = useAuthStore()
</script>

<template>
  <div>
    <nav class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <NuxtLink to="/dashboard" class="text-base font-semibold">Legal Doc AI</NuxtLink>
        <div class="flex gap-4 text-sm text-slate-700">
          <NuxtLink to="/dashboard">Dashboard</NuxtLink>
          <NuxtLink to="/documents">Documents</NuxtLink>
          <NuxtLink to="/contracts">Contracts</NuxtLink>
          <NuxtLink to="/dispatches">Công văn</NuxtLink>
          <NuxtLink to="/decisions">Quyết định</NuxtLink>
          <NuxtLink to="/upload">Upload</NuxtLink>
          <NuxtLink v-if="authStore.isAdmin" to="/status">Status</NuxtLink>
          <NuxtLink v-if="authStore.isAdmin" to="/users">Users</NuxtLink>
        </div>
      </div>
    </nav>
    <main class="mx-auto max-w-6xl px-4 py-6">
      <NuxtPage />
    </main>
  </div>
</template>
