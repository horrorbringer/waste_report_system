<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { VisDonut, VisSingleContainer, VisTooltip } from '@unovis/vue'
import { Donut } from '@unovis/ts'
import { translateStatus } from '@/i18n'
import type { StatusDistributionItem } from '@/types'
import ChartContainer, { type ChartConfig } from './ChartContainer.vue'

const props = defineProps<{
  data: StatusDistributionItem[]
}>()

const { t, locale } = useI18n()

const chartConfig = computed<ChartConfig>(() => ({
  Pending: { label: t('status.pending'), color: 'hsl(var(--chart-1))' },
  'In Progress': { label: t('status.inProgress'), color: 'hsl(var(--chart-2))' },
  Resolved: { label: t('status.resolved'), color: 'hsl(var(--chart-3))' },
}))

const totalCount = computed(() => props.data.reduce((sum, item) => sum + item.count, 0))
const nonZeroData = computed(() => props.data.filter((d) => d.count > 0))

const valueAccessor = (d: StatusDistributionItem) => d.count
const colorAccessor = (d: StatusDistributionItem) =>
  chartConfig.value[d.status]?.color ?? 'hsl(var(--chart-4))'

const tooltipTriggers = computed(() => ({
  [Donut.selectors.segment]: (d: { data: StatusDistributionItem }) => {
    const item = d.data
    const pct = totalCount.value ? Math.round((item.count / totalCount.value) * 100) : 0
    const statusLabel = translateStatus(item.status, t)
    const unit = t('charts.reportsUnit')
    return `
      <div style="padding: 6px 10px; font-size: 12px; line-height: 1.5;">
        <div style="font-weight: 600; margin-bottom: 2px;">${statusLabel}</div>
        <div style="color: hsl(var(--muted-foreground));">${item.count} ${unit} (${pct}%)</div>
      </div>
    `
  },
}))
</script>

<template>
  <ChartContainer :config="chartConfig" class="flex flex-col items-center">
    <div v-if="totalCount === 0" class="flex h-[240px] items-center justify-center text-sm text-muted-foreground">
      {{ t('charts.noReportData') }}
    </div>
    <template v-else>
      <div :key="locale" class="relative h-[240px] w-full max-w-[300px]">
        <VisSingleContainer :data="nonZeroData" :height="240">
          <VisDonut
            :value="valueAccessor"
            :color="colorAccessor"
            :arc-width="34"
            :pad-angle="0.03"
            :corner-radius="4"
            :central-label="String(totalCount)"
            :central-sub-label="t('charts.totalReports')"
          />
          <VisTooltip :triggers="tooltipTriggers" />
        </VisSingleContainer>
      </div>

      <div class="mt-4 flex flex-wrap items-center justify-center gap-4">
        <div
          v-for="item in data"
          :key="item.status"
          class="flex items-center gap-2 text-xs text-muted-foreground"
        >
          <span
            class="h-2.5 w-2.5 rounded-full"
            :style="{ backgroundColor: chartConfig[item.status]?.color }"
          />
          <span class="font-medium text-foreground">{{ translateStatus(item.status, t) }}</span>
          <span class="tabular-nums">({{ item.count }})</span>
        </div>
      </div>
    </template>
  </ChartContainer>
</template>
