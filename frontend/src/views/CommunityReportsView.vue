<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppLayout from '@/layouts/AppLayout.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { Button } from '@/components/ui/button'
import { localizedCategory } from '@/i18n'
import { useReportStore } from '@/stores/reports'
import type { CommunityReport } from '@/types'

const { t, locale } = useI18n()
const reportStore = useReportStore()
const pageSize = 20
const reports = ref<CommunityReport[]>([])
const page = ref(0)
const hasMore = ref(false)
const loading = ref(false)
const failed = ref(false)

const dateFormatter = computed(() => new Intl.DateTimeFormat(locale.value === 'km' ? 'km-KH' : 'en-GB', {
  dateStyle: 'medium',
  timeZone: 'UTC',
}))

async function loadPage(nextPage = page.value) {
  if (loading.value) return
  loading.value = true
  failed.value = false
  try {
    const result = await reportStore.fetchCommunityReports(pageSize, nextPage * pageSize)
    reports.value = result.items
    hasMore.value = result.has_more
    page.value = nextPage
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => loadPage())
</script>

<template>
  <AppLayout>
    <div class="container max-w-4xl space-y-6 py-8 sm:py-12">
      <header class="space-y-2">
        <h1 class="heading-page text-3xl font-bold tracking-tight sm:text-4xl">{{ t('community.title') }}</h1>
        <p class="max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base">{{ t('community.description') }}</p>
      </header>

      <div v-if="failed" role="alert" class="flex flex-wrap items-center justify-between gap-3 rounded-xl border p-4">
        <p class="text-sm text-destructive">{{ t('community.loadError') }}</p>
        <Button type="button" variant="outline" size="sm" @click="loadPage()">{{ t('common.refresh') }}</Button>
      </div>

      <div :aria-busy="loading" class="overflow-hidden rounded-xl border bg-card">
        <ul v-if="reports.length" class="divide-y">
          <li v-for="(report, index) in reports" :key="index" class="flex flex-wrap items-start justify-between gap-3 p-4 sm:p-5">
            <div class="space-y-1">
              <p class="font-semibold">{{ localizedCategory(report.category_name, report.category_name_km, locale) }}</p>
              <p class="flex flex-wrap items-center gap-x-2 text-sm text-muted-foreground">
                <template v-if="report.district_name">
                  <span>{{ localizedCategory(report.district_name, report.district_name_km, locale) }}</span>
                  <span aria-hidden="true">·</span>
                </template>
                <span>{{ locale === 'km' ? report.province_name_km : report.province_name }}</span>
                <span aria-hidden="true">·</span>
                <time :datetime="report.reported_on">{{ dateFormatter.format(new Date(report.reported_on + 'T00:00:00Z')) }}</time>
              </p>
            </div>
            <StatusBadge :status="report.status" />
          </li>
        </ul>
        <p v-else-if="loading" role="status" class="p-8 text-center text-sm text-muted-foreground">{{ t('community.loading') }}</p>
        <p v-else-if="!failed" class="p-8 text-center text-sm text-muted-foreground">{{ t('community.empty') }}</p>
      </div>

      <nav v-if="page > 0 || hasMore" :aria-label="t('community.pagination')" class="flex flex-wrap items-center justify-between gap-2">
        <Button type="button" variant="outline" size="sm" :disabled="loading || page === 0" @click="loadPage(page - 1)">
          {{ t('community.previous') }}
        </Button>
        <p aria-live="polite" class="text-sm text-muted-foreground">{{ t('community.page', { page: page + 1 }) }}</p>
        <Button type="button" variant="outline" size="sm" :disabled="loading || !hasMore" @click="loadPage(page + 1)">
          {{ t('community.next') }}
        </Button>
      </nav>
    </div>
  </AppLayout>
</template>
