<script setup lang="ts">
withDefaults(
  defineProps<{
    narrow?: boolean
  }>(),
  { narrow: false }
)
</script>

<template>
  <section :class="['space-y-6', narrow ? 'max-w-3xl' : '']">
    <slot />
  </section>
</template>
