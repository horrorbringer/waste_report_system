<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  AlertTriangle,
  Calendar,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Cpu,
  Globe,
  HardHat,
  Leaf,
  MapPin,
  Package,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldCheck,
  Tag,
  Trash2,
  X,
} from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { localizedCategory } from '@/i18n'
import { useReportStore } from '@/stores/reports'
import type { CommunityReport, ReportStatus } from '@/types'

const { t, locale } = useI18n()
const reportStore = useReportStore()
const pageSize = 20
const reports = ref<CommunityReport[]>([])
const page = ref(0)
const hasMore = ref(false)
const loading = ref(false)
const failed = ref(false)

const searchQuery = ref('')
const statusFilter = ref<'ALL' | ReportStatus>('ALL')
const provinceFilter = ref<string>('ALL')

const dateFormatter = computed(() => new Intl.DateTimeFormat(locale.value === 'km' ? 'km-KH' : 'en-GB', {
  dateStyle: 'medium',
  timeZone: 'UTC',
}))

function getCategoryIcon(name: string) {
  const lower = name.toLowerCase()
  if (lower.includes('plastic')) return Package
  if (lower.includes('organic') || lower.includes('food') || lower.includes('garden')) return Leaf
  if (lower.includes('overflow') || lower.includes('bin') || lower.includes('dumpster')) return Trash2
  if (lower.includes('construction') || lower.includes('debris') || lower.includes('rubble')) return HardHat
  if (lower.includes('electronic') || lower.includes('e-waste')) return Cpu
  if (lower.includes('hazard') || lower.includes('chemical') || lower.includes('toxic')) return AlertTriangle
  return Tag
}

const availableProvinces = computed(() => {
  const map = new Map<string, string>()
  for (const item of reports.value) {
    const key = String(item.province)
    if (!map.has(key)) {
      map.set(key, locale.value === 'km' ? item.province_name_km : item.province_name)
    }
  }
  return Array.from(map.entries()).map(([code, name]) => ({ code, name }))
})

const filteredReports = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return reports.value.filter((item) => {
    if (statusFilter.value !== 'ALL' && item.status !== statusFilter.value) {
      return false
    }
    if (provinceFilter.value !== 'ALL' && String(item.province) !== provinceFilter.value) {
      return false
    }
    if (query) {
      const fields = [
        item.category_name,
        item.category_name_km ?? '',
        item.province_name,
        item.province_name_km,
        item.district_name ?? '',
        item.district_name_km ?? '',
      ]
      if (!fields.some((f) => f.toLowerCase().includes(query))) {
        return false
      }
    }
    return true
  })
})

const hasActiveFilters = computed(() => {
  return Boolean(searchQuery.value.trim()) || statusFilter.value !== 'ALL' || provinceFilter.value !== 'ALL'
})

const stats = computed(() => {
  const items = reports.value
  return {
    total: items.length,
    pending: items.filter((r) => r.status === 'Pending').length,
    inProgress: items.filter((r) => r.status === 'In Progress').length,
    resolved: items.filter((r) => r.status === 'Resolved').length,
  }
})

function resetFilters() {
  searchQuery.value = ''
  statusFilter.value = 'ALL'
  provinceFilter.value = 'ALL'
}

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
    <div class="container max-w-5xl space-y-6 py-8 sm:py-10">
      <!-- Civic Header Banner -->
      <header class="flex flex-col gap-4 rounded-2xl border border-border/80 bg-card p-6 shadow-xs sm:flex-row sm:items-center sm:justify-between">
        <div class="space-y-1.5">
          <div class="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-primary">
            <Globe class="h-3 w-3" />
            {{ t('community.eyebrow') }}
          </div>
          <h1 class="heading-page text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {{ t('community.title') }}
          </h1>
          <p class="max-w-xl text-sm leading-relaxed text-muted-foreground">
            {{ t('community.description') }}
          </p>
        </div>
        <div class="flex shrink-0 flex-wrap items-center gap-2.5">
          <Button
            type="button"
            variant="outline"
            size="sm"
            class="h-9 gap-1.5 text-xs font-medium"
            :disabled="loading"
            @click="loadPage()"
          >
            <RefreshCw class="h-3.5 w-3.5" :class="{ 'animate-spin': loading }" />
            {{ t('common.refresh') }}
          </Button>
          <Button as-child size="sm" class="h-9 gap-1.5 text-xs font-medium shadow-xs">
            <RouterLink :to="{ name: 'submit-report' }">
              <ClipboardList class="h-3.5 w-3.5" />
              {{ t('community.reportIssueBtn') }}
            </RouterLink>
          </Button>
        </div>
      </header>

      <!-- Summary KPI Strip -->
      <section v-if="!loading && reports.length" class="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div class="rounded-xl border bg-card px-4 py-3 shadow-xs">
          <p class="text-xs font-medium text-muted-foreground">{{ t('community.totalShown') }}</p>
          <p class="mt-1 text-2xl font-bold tabular-nums text-foreground">{{ stats.total }}</p>
        </div>
        <div class="rounded-xl border bg-card px-4 py-3 shadow-xs">
          <p class="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <span class="h-2 w-2 rounded-full bg-amber-500" />
            {{ t('status.pending') }}
          </p>
          <p class="mt-1 text-2xl font-bold tabular-nums text-foreground">{{ stats.pending }}</p>
        </div>
        <div class="rounded-xl border bg-card px-4 py-3 shadow-xs">
          <p class="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <span class="h-2 w-2 rounded-full bg-blue-500" />
            {{ t('status.inProgress') }}
          </p>
          <p class="mt-1 text-2xl font-bold tabular-nums text-foreground">{{ stats.inProgress }}</p>
        </div>
        <div class="rounded-xl border bg-card px-4 py-3 shadow-xs">
          <p class="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <span class="h-2 w-2 rounded-full bg-emerald-500" />
            {{ t('status.resolved') }}
          </p>
          <p class="mt-1 text-2xl font-bold tabular-nums text-foreground">{{ stats.resolved }}</p>
        </div>
      </section>

      <!-- Search & Filter Bar -->
      <div class="flex flex-col gap-3 rounded-xl border bg-card p-3.5 shadow-xs sm:flex-row sm:items-center sm:justify-between">
        <div class="relative flex-1">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            v-model="searchQuery"
            type="search"
            class="h-9 pl-9 pr-8 text-sm"
            :placeholder="t('community.searchPlaceholder')"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-sm text-muted-foreground hover:text-foreground"
            :aria-label="t('common.clear')"
            @click="searchQuery = ''"
          >
            <X class="h-3.5 w-3.5" />
          </button>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <!-- Status Filter Tabs -->
          <div class="inline-flex items-center rounded-lg border bg-muted/40 p-0.5 text-xs">
            <button
              type="button"
              class="rounded-md px-2.5 py-1 font-medium transition-colors"
              :class="statusFilter === 'ALL' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
              @click="statusFilter = 'ALL'"
            >
              {{ t('community.allStatuses') }}
            </button>
            <button
              type="button"
              class="rounded-md px-2.5 py-1 font-medium transition-colors"
              :class="statusFilter === 'Pending' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
              @click="statusFilter = 'Pending'"
            >
              {{ t('status.pending') }}
            </button>
            <button
              type="button"
              class="rounded-md px-2.5 py-1 font-medium transition-colors"
              :class="statusFilter === 'In Progress' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
              @click="statusFilter = 'In Progress'"
            >
              {{ t('status.inProgress') }}
            </button>
            <button
              type="button"
              class="rounded-md px-2.5 py-1 font-medium transition-colors"
              :class="statusFilter === 'Resolved' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
              @click="statusFilter = 'Resolved'"
            >
              {{ t('status.resolved') }}
            </button>
          </div>

          <!-- Province Filter -->
          <Select v-if="availableProvinces.length > 1" v-model="provinceFilter">
            <SelectTrigger class="h-9 w-[180px] text-xs">
              <SelectValue :placeholder="t('community.allProvinces')" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">{{ t('community.allProvinces') }}</SelectItem>
              <SelectItem v-for="prov in availableProvinces" :key="prov.code" :value="prov.code">
                {{ prov.name }}
              </SelectItem>
            </SelectContent>
          </Select>

          <Button
            v-if="hasActiveFilters"
            type="button"
            variant="ghost"
            size="sm"
            class="h-9 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
            @click="resetFilters"
          >
            <RotateCcw class="h-3.5 w-3.5" />
            {{ t('community.resetFilters') }}
          </Button>
        </div>
      </div>

      <!-- Error Alert -->
      <div v-if="failed" role="alert" class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4">
        <p class="text-sm font-medium text-destructive">{{ t('community.loadError') }}</p>
        <Button type="button" variant="outline" size="sm" @click="loadPage()">{{ t('common.refresh') }}</Button>
      </div>

      <!-- Loading Skeletons -->
      <div v-if="loading && !reports.length" class="space-y-3" :aria-busy="true">
        <div v-for="n in 4" :key="n" class="flex items-center justify-between rounded-xl border bg-card p-4 shadow-xs">
          <div class="flex items-center gap-3.5">
            <Skeleton class="h-10 w-10 rounded-lg" />
            <div class="space-y-2">
              <Skeleton class="h-4 w-44" />
              <Skeleton class="h-3.5 w-64" />
            </div>
          </div>
          <Skeleton class="h-6 w-20 rounded-full" />
        </div>
      </div>

      <!-- Reports Feed Cards -->
      <div v-else-if="filteredReports.length" class="space-y-3">
        <article
          v-for="(report, index) in filteredReports"
          :key="index"
          class="flex flex-col gap-3 rounded-xl border bg-card p-4 shadow-xs transition-colors hover:border-primary/40 sm:flex-row sm:items-center sm:justify-between sm:p-5"
        >
          <div class="flex items-start gap-3.5">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-primary/15 bg-primary/5 text-primary">
              <component :is="getCategoryIcon(report.category_name)" class="h-5 w-5" />
            </div>
            <div class="min-w-0 space-y-1">
              <div class="flex flex-wrap items-center gap-2">
                <h2 class="text-sm font-semibold text-foreground sm:text-base">
                  {{ localizedCategory(report.category_name, report.category_name_km, locale) }}
                </h2>
              </div>

              <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                <span class="inline-flex items-center gap-1 font-medium text-foreground/80">
                  <MapPin class="h-3.5 w-3.5 text-primary" />
                  <template v-if="report.district_name">
                    {{ localizedCategory(report.district_name, report.district_name_km, locale) }}
                    <span class="mx-0.5 text-muted-foreground/60">·</span>
                  </template>
                  {{ locale === 'km' ? report.province_name_km : report.province_name }}
                </span>

                <span class="inline-flex items-center gap-1 tabular-nums">
                  <Calendar class="h-3.5 w-3.5 text-muted-foreground/80" />
                  {{ t('community.reportedDateLabel') }}
                  <time :datetime="report.reported_on" class="font-medium text-foreground/80">
                    {{ dateFormatter.format(new Date(report.reported_on + 'T00:00:00Z')) }}
                  </time>
                </span>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-end sm:shrink-0">
            <StatusBadge :status="report.status" />
          </div>
        </article>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="!failed"
        class="flex flex-col items-center justify-center rounded-2xl border border-dashed bg-muted/10 px-6 py-12 text-center"
      >
        <div class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <Globe class="h-6 w-6" />
        </div>
        <p class="text-sm font-semibold text-foreground">
          {{ hasActiveFilters ? t('community.emptyFiltered') : t('community.empty') }}
        </p>
        <div class="mt-4 flex flex-wrap justify-center gap-2">
          <Button v-if="hasActiveFilters" type="button" variant="outline" size="sm" class="gap-1.5" @click="resetFilters">
            <RotateCcw class="h-3.5 w-3.5" />
            {{ t('community.resetFilters') }}
          </Button>
          <Button v-else as-child size="sm" class="gap-1.5">
            <RouterLink :to="{ name: 'submit-report' }">
              <ClipboardList class="h-3.5 w-3.5" />
              {{ t('community.reportIssueBtn') }}
            </RouterLink>
          </Button>
        </div>
      </div>

      <!-- Pagination Controls -->
      <nav
        v-if="page > 0 || hasMore"
        :aria-label="t('community.pagination')"
        class="flex flex-wrap items-center justify-between gap-2 rounded-xl border bg-card px-4 py-3 shadow-xs"
      >
        <Button type="button" variant="outline" size="sm" class="h-8 gap-1 text-xs" :disabled="loading || page === 0" @click="loadPage(page - 1)">
          <ChevronLeft class="h-3.5 w-3.5" />
          {{ t('community.previous') }}
        </Button>
        <p aria-live="polite" class="text-xs font-medium text-muted-foreground tabular-nums">
          {{ t('community.page', { page: page + 1 }) }}
        </p>
        <Button type="button" variant="outline" size="sm" class="h-8 gap-1 text-xs" :disabled="loading || !hasMore" @click="loadPage(page + 1)">
          {{ t('community.next') }}
          <ChevronRight class="h-3.5 w-3.5" />
        </Button>
      </nav>

      <!-- Privacy Anonymization Notice -->
      <footer class="flex items-start gap-2.5 rounded-xl border border-border/60 bg-muted/30 px-4 py-3 text-xs leading-relaxed text-muted-foreground">
        <ShieldCheck class="mt-0.5 h-4 w-4 shrink-0 text-primary" />
        <p>{{ t('community.privacyNote') }}</p>
      </footer>
    </div>
  </AppLayout>
</template>
