<script setup lang="ts">
defineProps<{
  message: string
}>()
</script>

<template>
  <Message severity="error" class="w-full">
    <div class="flex items-start gap-2">
      <i class="pi pi-exclamation-circle mt-0.5 shrink-0" />
      <span>{{ message }}</span>
    </div>
  </Message>
</template>
