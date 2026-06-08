<script setup lang="ts">
const authStore = useAuthStore()
const route = useRoute()
const mobileOpen = ref(false)

interface NavItem {
  label: string
  to: string
  adminOnly?: boolean
}

const navItems: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Documents', to: '/documents' },
  { label: 'Contracts', to: '/contracts' },
  { label: 'Công văn', to: '/dispatches' },
  { label: 'Quyết định', to: '/decisions' },
  { label: 'Mua sắm', to: '/procurements' },
  { label: 'Upload', to: '/upload' },
  { label: 'Danh mục VT', to: '/materials-catalog', adminOnly: true },
  { label: 'Status', to: '/status', adminOnly: true },
  { label: 'Users', to: '/users', adminOnly: true }
]

const visibleItems = computed(() =>
  navItems.filter((item) => !item.adminOnly || authStore.isAdmin)
)

function isActive(path: string) {
  if (path === '/dashboard') return route.path === '/dashboard' || route.path === '/'
  return route.path === path || route.path.startsWith(`${path}/`)
}

function closeMobile() {
  mobileOpen.value = false
}

watch(() => route.path, closeMobile)
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
    <div class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
      <NuxtLink to="/dashboard" class="shrink-0 text-base font-semibold text-slate-900">
        Legal Doc AI
      </NuxtLink>

      <button
        type="button"
        class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 lg:hidden"
        :aria-expanded="mobileOpen"
        aria-label="Mở menu điều hướng"
        @click="mobileOpen = !mobileOpen"
      >
        <i :class="mobileOpen ? 'pi pi-times' : 'pi pi-bars'" />
      </button>

      <nav class="hidden items-center gap-1 lg:flex" aria-label="Điều hướng chính">
        <NuxtLink
          v-for="item in visibleItems"
          :key="item.to"
          :to="item.to"
          class="app-nav-link"
          :class="{ 'app-nav-link--active': isActive(item.to) }"
        >
          {{ item.label }}
        </NuxtLink>
      </nav>
    </div>

    <nav
      v-show="mobileOpen"
      class="border-t border-slate-100 bg-white px-4 py-3 lg:hidden"
      aria-label="Điều hướng di động"
    >
      <div class="flex flex-col gap-1">
        <NuxtLink
          v-for="item in visibleItems"
          :key="`mobile-${item.to}`"
          :to="item.to"
          class="app-nav-link app-nav-link--mobile"
          :class="{ 'app-nav-link--active': isActive(item.to) }"
          @click="closeMobile"
        >
          {{ item.label }}
        </NuxtLink>
      </div>
    </nav>
  </header>
</template>
