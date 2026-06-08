<script setup lang="ts">
const route = useRoute()
const isLoginPage = computed(() => route.path === '/login')
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <AppNavbar v-if="!isLoginPage" />
    <main :class="isLoginPage ? 'flex min-h-screen items-center justify-center px-4 py-8' : 'mx-auto max-w-6xl px-4 py-6 sm:px-6'">
      <NuxtPage />
    </main>
  </div>
</template>
