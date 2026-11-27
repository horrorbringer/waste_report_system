<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

const props = defineProps<{
  total: number
  limit: number
  offset: number
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:offset': [value: number]
}>()

const { t } = useI18n()

const currentPage = computed(() => Math.floor(props.offset / props.limit) + 1)
const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.limit)))
const startItem = computed(() => (props.total === 0 ? 0 : props.offset + 1))
const endItem = computed(() => Math.min(props.offset + props.limit, props.total))

function goPrev() {
  if (props.offset <= 0) return
  emit('update:offset', Math.max(0, props.offset - props.limit))
}

function goNext() {
  if (props.offset + props.limit >= props.total) return
  emit('update:offset', props.offset + props.limit)
}
</script>

<template>
  <div
    v-if="total > 0"
    class="flex flex-col items-center justify-between gap-3 border-t px-4 py-3 text-xs text-muted-foreground sm:flex-row"
  >
    <p class="tabular-nums">
      {{ t('pagination.showing', { start: startItem, end: endItem, total }) }}
    </p>
    <div class="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        class="h-7 gap-1 px-2.5 text-xs"
        :disabled="loading || offset <= 0"
        @click="goPrev"
      >
        <ChevronLeft class="h-3.5 w-3.5" />
        {{ t('pagination.prev') }}
      </Button>
      <span class="min-w-[84px] text-center font-medium tabular-nums text-foreground">
        {{ t('pagination.pageOf', { page: currentPage, pages: totalPages }) }}
      </span>
      <Button
        variant="outline"
        size="sm"
        class="h-7 gap-1 px-2.5 text-xs"
        :disabled="loading || offset + limit >= total"
        @click="goNext"
      >
        {{ t('pagination.next') }}
        <ChevronRight class="h-3.5 w-3.5" />
      </Button>
    </div>
  </div>
</template>
