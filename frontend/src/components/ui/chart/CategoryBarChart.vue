<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { VisAxis, VisGroupedBar, VisTooltip, VisXYContainer } from '@unovis/vue'
import { GroupedBar } from '@unovis/ts'
import { localizedCategory } from '@/i18n'
import type { CategoryDistributionItem } from '@/types'
import ChartContainer, { type ChartConfig } from './ChartContainer.vue'

const props = defineProps<{
  data: CategoryDistributionItem[]
}>()

const { t, locale } = useI18n()

const chartConfig = computed<ChartConfig>(() => ({
  count: { label: t('charts.reportsUnit'), color: 'hsl(var(--chart-3))' },
}))

const xAccessor = (_d: CategoryDistributionItem, i: number) => i
const yAccessor = [(d: CategoryDistributionItem) => d.count]
const barColor = () => 'hsl(var(--chart-3))'

const formatXTick = (index: number) => {
  const item = props.data[index]
  if (!item) return ''
  const name = localizedCategory(item.category, item.category_km, locale.value)
  return name.length > 13 ? `${name.slice(0, 12)}…` : name
}

const tooltipTriggers = computed(() => ({
  [GroupedBar.selectors.bar]: (d: CategoryDistributionItem) => {
    const label = localizedCategory(d.category, d.category_km, locale.value)
    const unit = t('charts.reportsUnit')
    return `
      <div style="padding: 6px 10px; font-size: 12px; line-height: 1.5;">
        <div style="font-weight: 600; margin-bottom: 2px;">${label}</div>
        <div style="color: hsl(var(--muted-foreground));">${d.count} ${unit}</div>
      </div>
    `
  },
}))
</script>

<template>
  <ChartContainer :config="chartConfig">
    <div v-if="data.length === 0" class="flex h-[280px] items-center justify-center text-sm text-muted-foreground">
      {{ t('charts.noCategories') }}
    </div>
    <div v-else :key="locale" class="h-[280px] w-full">
      <VisXYContainer :data="data" :height="280" :padding="{ top: 12, right: 12, bottom: 16, left: 4 }">
        <VisGroupedBar
          :x="xAccessor"
          :y="yAccessor"
          :color="barColor"
          :rounded-corners="6"
          :bar-padding="0.3"
        />
        <VisAxis
          type="x"
          :tick-format="formatXTick"
          :num-ticks="data.length"
          :grid-line="false"
          :domain-line="false"
          :tick-line="false"
        />
        <VisAxis
          type="y"
          :tick-format="(v: number) => (Number.isInteger(v) ? String(v) : '')"
          :domain-line="false"
          :tick-line="false"
        />
        <VisTooltip :triggers="tooltipTriggers" />
      </VisXYContainer>
    </div>
  </ChartContainer>
</template>
