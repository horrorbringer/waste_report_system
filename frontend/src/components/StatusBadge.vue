<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Clock, Loader2, CheckCircle2 } from 'lucide-vue-next'
import { translateStatus } from '@/i18n'
import { Badge } from '@/components/ui/badge'
import type { ReportStatus } from '@/types'

const props = defineProps<{
  status: ReportStatus | string
}>()

const { t } = useI18n()

const variant = computed(() => {
  if (props.status === 'Resolved') return 'resolved'
  if (props.status === 'In Progress') return 'progress'
  return 'pending'
})

const label = computed(() => translateStatus(props.status, t))
</script>

<template>
  <Badge :variant="variant" class="gap-1.5 whitespace-nowrap font-medium">
    <Clock v-if="status === 'Pending'" class="h-3 w-3" />
    <Loader2 v-else-if="status === 'In Progress'" class="h-3 w-3" />
    <CheckCircle2 v-else class="h-3 w-3" />
    <span>{{ label }}</span>
  </Badge>
</template>
