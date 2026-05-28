<script setup lang="ts">
const email = ref('')
const password = ref('')
const { loading, error, login } = useAuth()

async function submit() {
  await login(email.value, password.value)
}
</script>

<template>
  <section class="mx-auto max-w-md">
    <Card>
      <template #title>Đăng nhập</template>
      <template #content>
        <form class="space-y-4" @submit.prevent="submit">
          <div class="space-y-2">
            <label class="text-sm font-medium" for="email">Email</label>
            <InputText id="email" v-model="email" class="w-full" type="email" />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium" for="password">Mật khẩu</label>
            <Password id="password" v-model="password" class="w-full" input-class="w-full" :feedback="false" />
          </div>
          <Message v-if="error" severity="error">{{ error }}</Message>
          <Button type="submit" label="Đăng nhập" icon="pi pi-sign-in" :loading="loading" class="w-full" />
        </form>
      </template>
    </Card>
  </section>
</template>
