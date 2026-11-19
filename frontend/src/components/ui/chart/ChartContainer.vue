<script setup lang="ts">
import { computed, type HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

export interface ChartConfigItem {
  label: string
  color: string
}

export type ChartConfig = Record<string, ChartConfigItem>

const props = defineProps<{
  config: ChartConfig
  class?: HTMLAttributes['class']
}>()

const cssVars = computed(() => {
  const vars: Record<string, string> = {}
  for (const [key, item] of Object.entries(props.config)) {
    vars[`--color-${key}`] = item.color
  }
  return vars
})
</script>

<template>
  <div
    :style="cssVars"
    :class="
      cn(
        'w-full [&_.unovis-xy-container]:w-full [&_.unovis-single-container]:w-full',
        props.class
      )
    "
  >
    <slot />
  </div>
</template>
