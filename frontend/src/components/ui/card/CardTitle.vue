<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <h3 :class="cn('font-display text-base font-semibold leading-snug tracking-[-0.015em]', props.class)">
    <slot />
  </h3>
</template>
