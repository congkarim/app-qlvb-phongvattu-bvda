<script setup lang="ts">
const email = ref('')
const password = ref('')
const { loading, error, login } = useAuth()

async function submit() {
  await login(email.value, password.value)
}
</script>

<template>
  <section class="w-full max-w-md">
    <div class="mb-6 text-center">
      <h1 class="text-2xl font-semibold tracking-tight text-slate-900">Legal Doc AI</h1>
      <p class="mt-1 text-sm text-slate-600">Hệ thống quản lý văn bản và OCR</p>
    </div>

    <AppCard title="Đăng nhập">
      <form class="space-y-4" @submit.prevent="submit">
        <div class="space-y-2">
          <label class="text-sm font-medium text-slate-700" for="email">Email</label>
          <InputText id="email" v-model="email" class="w-full" type="email" required autocomplete="email" />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-medium text-slate-700" for="password">Mật khẩu</label>
          <Password id="password" v-model="password" class="w-full" input-class="w-full" :feedback="false" required autocomplete="current-password" />
        </div>
        <AppErrorState v-if="error" :message="error" />
        <Button type="submit" label="Đăng nhập" icon="pi pi-sign-in" :loading="loading" class="w-full" />
      </form>
    </AppCard>
  </section>
</template>
