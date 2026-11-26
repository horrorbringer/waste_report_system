<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  AlertTriangle,
  Calendar,
  Camera,
  Check,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Cpu,
  ExternalLink,
  HardHat,
  ImageIcon,
  LayoutGrid,
  Leaf,
  List,
  Map as MapIcon,
  MapPin,
  MessageSquareText,
  Package,
  RotateCcw,
  Search,
  Share2,
  ShieldCheck,
  Tag,
  Trash2,
  X,
} from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import CommunityReportsMap from '@/components/CommunityReportsMap.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { localizedCategory } from '@/i18n'
import { resolvePhotoUrl } from '@/lib/utils'
import { useCategoryStore } from '@/stores/categories'
import { useReportStore } from '@/stores/reports'
import type { CommunityReport, ReportStatus } from '@/types'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const categoryStore = useCategoryStore()
const reportStore = useReportStore()

const pageSize = 20
const reports = ref<CommunityReport[]>([])
const page = ref(0)
const hasMore = ref(false)
const loading = ref(false)
const failed = ref(false)

const searchQuery = ref('')
const statusFilter = ref<'ALL' | ReportStatus>('ALL')
const categoryFilter = ref<string>('ALL')
const provinceFilter = ref<string>('ALL')
const sortOrder = ref<'newest' | 'oldest'>('newest')
const viewMode = ref<'grid' | 'list' | 'map'>('map')

const selectedReport = ref<CommunityReport | null>(null)
const detailOpen = ref(false)
const activePhotoIndex = ref(0)
const linkCopied = ref(false)

let searchDebounce: ReturnType<typeof setTimeout> | null = null

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

function getReportPhotos(report: CommunityReport): string[] {
  if (report.photo_paths?.length) return report.photo_paths
  return report.photo_path ? [report.photo_path] : []
}

function openReportDetail(report: CommunityReport) {
  selectedReport.value = report
  activePhotoIndex.value = 0
  detailOpen.value = true
  if (String(route.query.report ?? '') !== String(report.id)) {
    router.replace({ query: { ...route.query, report: String(report.id) } })
  }
}

function copyShareLink() {
  if (!selectedReport.value) return
  const url = `${window.location.origin}/community-reports?report=${selectedReport.value.id}`
  navigator.clipboard.writeText(url)
  linkCopied.value = true
  setTimeout(() => {
    linkCopied.value = false
  }, 2000)
}

watch(detailOpen, (isOpen) => {
  if (!isOpen && route.query.report) {
    const nextQuery = { ...route.query }
    delete nextQuery.report
    router.replace({ query: nextQuery })
  }
})

const selectedPhotos = computed(() => {
  if (!selectedReport.value) return []
  return getReportPhotos(selectedReport.value)
})

const hasActiveFilters = computed(() => {
  return (
    Boolean(searchQuery.value.trim()) ||
    statusFilter.value !== 'ALL' ||
    categoryFilter.value !== 'ALL' ||
    provinceFilter.value !== 'ALL' ||
    sortOrder.value !== 'newest'
  )
})

function resetFilters() {
  searchQuery.value = ''
  statusFilter.value = 'ALL'
  categoryFilter.value = 'ALL'
  provinceFilter.value = 'ALL'
  sortOrder.value = 'newest'
  loadPage(0)
}

async function loadPage(nextPage = page.value) {
  loading.value = true
  failed.value = false
  try {
    const result = await reportStore.fetchCommunityReports({
      limit: pageSize,
      offset: nextPage * pageSize,
      q: searchQuery.value,
      status: statusFilter.value,
      category_id: categoryFilter.value,
      province: provinceFilter.value,
      sort: sortOrder.value,
    })
    reports.value = result.items
    hasMore.value = result.has_more
    page.value = nextPage
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

watch([statusFilter, categoryFilter, provinceFilter, sortOrder], () => {
  loadPage(0)
})

watch(searchQuery, () => {
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    loadPage(0)
  }, 300)
})

onMounted(async () => {
  categoryStore.fetchCategories().catch(() => {})
  reportStore.fetchReportAreas().catch(() => {})
  await loadPage(0)

  const sharedId = Number(route.query.report)
  if (sharedId > 0) {
    const existing = reports.value.find((r) => r.id === sharedId)
    if (existing) {
      openReportDetail(existing)
    } else {
      try {
        const fetched = await reportStore.fetchCommunityReportById(sharedId)
        openReportDetail(fetched)
      } catch {
        // Ignore invalid or unpublished report ID in query
      }
    }
  }
})

onUnmounted(() => {
  if (searchDebounce) clearTimeout(searchDebounce)
})
</script>

<template>
  <AppLayout>
    <div class="container max-w-5xl space-y-6 py-8 sm:py-10">
      <!-- Clean Header -->
      <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div class="space-y-1.5">
          <h1 class="heading-page text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {{ t('community.title') }}
          </h1>
          <p class="max-w-xl text-sm leading-relaxed text-muted-foreground">
            {{ t('community.description') }}
          </p>
        </div>
        <Button as-child size="sm" class="h-9 w-fit shrink-0 gap-1.5 text-xs font-medium shadow-xs">
          <RouterLink :to="{ name: 'submit-report' }">
            <ClipboardList class="h-3.5 w-3.5" />
            {{ t('community.reportIssueBtn') }}
          </RouterLink>
        </Button>
      </header>

      <!-- Search, Filters & View Switcher -->
      <div class="space-y-2.5">
        <div class="flex flex-col gap-2.5 sm:flex-row sm:items-center sm:justify-between">
          <!-- Search Input -->
          <div class="relative flex-1">
            <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              v-model="searchQuery"
              type="search"
              class="h-9 bg-card pl-9 pr-8 text-sm"
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

          <!-- Status Filter Tabs & View Mode Switcher -->
          <div class="flex flex-wrap items-center gap-2">
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

            <!-- 3-Way View Mode Switcher (Map / Grid / List) -->
            <div class="inline-flex items-center rounded-lg border bg-muted/40 p-0.5" role="group">
              <button
                type="button"
                class="inline-flex h-7 w-7 items-center justify-center rounded-md transition-colors"
                :class="viewMode === 'map' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
                :aria-label="t('community.viewMap')"
                :aria-pressed="viewMode === 'map'"
                @click="viewMode = 'map'"
              >
                <MapIcon class="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                class="inline-flex h-7 w-7 items-center justify-center rounded-md transition-colors"
                :class="viewMode === 'grid' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
                :aria-label="t('myReports.viewGrid')"
                :aria-pressed="viewMode === 'grid'"
                @click="viewMode = 'grid'"
              >
                <LayoutGrid class="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                class="inline-flex h-7 w-7 items-center justify-center rounded-md transition-colors"
                :class="viewMode === 'list' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
                :aria-label="t('myReports.viewList')"
                :aria-pressed="viewMode === 'list'"
                @click="viewMode = 'list'"
              >
                <List class="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- Secondary Filters Row: Category, Province, Sort & Reset -->
        <div class="flex flex-wrap items-center gap-2">
          <!-- Category Filter -->
          <Select v-if="categoryStore.categories.length" v-model="categoryFilter">
            <SelectTrigger class="h-8 w-[180px] bg-card text-xs">
              <SelectValue :placeholder="t('myReports.allCategories')" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">{{ t('myReports.allCategories') }}</SelectItem>
              <SelectItem v-for="cat in categoryStore.categories" :key="cat.id" :value="String(cat.id)">
                {{ localizedCategory(cat.name, cat.name_km, locale) }}
              </SelectItem>
            </SelectContent>
          </Select>

          <!-- Province Filter -->
          <Select v-if="reportStore.reportAreas.length" v-model="provinceFilter">
            <SelectTrigger class="h-8 w-[180px] bg-card text-xs">
              <SelectValue :placeholder="t('community.allProvinces')" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">{{ t('community.allProvinces') }}</SelectItem>
              <SelectItem v-for="prov in reportStore.reportAreas" :key="prov.code" :value="String(prov.code)">
                {{ locale === 'km' ? prov.name_km : prov.name }}
              </SelectItem>
            </SelectContent>
          </Select>

          <!-- Sort Order -->
          <Select v-model="sortOrder">
            <SelectTrigger class="h-8 w-[150px] bg-card text-xs">
              <SelectValue :placeholder="t('myReports.sortBy')" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">{{ t('myReports.sortNewest') }}</SelectItem>
              <SelectItem value="oldest">{{ t('myReports.sortOldest') }}</SelectItem>
            </SelectContent>
          </Select>

          <Button
            v-if="hasActiveFilters"
            type="button"
            variant="ghost"
            size="sm"
            class="h-8 gap-1.5 px-2.5 text-xs text-muted-foreground hover:text-foreground"
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
      <div v-if="loading && !reports.length && viewMode === 'map'" class="grid overflow-hidden rounded-xl border bg-card shadow-xs lg:grid-cols-[1fr_16.5rem]" :aria-busy="true">
        <Skeleton class="h-[320px] w-full rounded-none sm:h-[380px]" />
        <div class="hidden space-y-3 border-l p-4 lg:block">
          <Skeleton class="h-4 w-24" />
          <div v-for="n in 5" :key="n" class="flex items-center gap-2.5 pt-2">
            <Skeleton class="h-12 w-14 shrink-0 rounded-md" />
            <div class="flex-1 space-y-1.5">
              <Skeleton class="h-3.5 w-full" />
              <Skeleton class="h-3 w-2/3" />
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="loading && !reports.length && viewMode === 'grid'" class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3" :aria-busy="true">
        <div v-for="n in 6" :key="n" class="overflow-hidden rounded-xl border bg-card shadow-xs">
          <Skeleton class="aspect-[16/10] w-full rounded-none" />
          <div class="space-y-2.5 p-4">
            <Skeleton class="h-4 w-3/4" />
            <Skeleton class="h-3 w-full" />
            <Skeleton class="h-3 w-2/3" />
          </div>
        </div>
      </div>
      <div v-else-if="loading && !reports.length && viewMode === 'list'" class="divide-y overflow-hidden rounded-xl border bg-card shadow-xs" :aria-busy="true">
        <div v-for="n in 4" :key="n" class="flex items-center justify-between gap-4 p-4">
          <div class="flex items-center gap-3.5">
            <Skeleton class="h-16 w-20 shrink-0 rounded-lg" />
            <div class="space-y-2">
              <Skeleton class="h-4 w-48" />
              <Skeleton class="h-3 w-64" />
            </div>
          </div>
          <Skeleton class="h-6 w-20 rounded-full" />
        </div>
      </div>

      <!-- Map View -->
      <CommunityReportsMap
        v-else-if="reports.length && viewMode === 'map'"
        :reports="reports"
        @select-report="openReportDetail"
      />

      <!-- Photo-First Cards Grid -->
      <div v-else-if="reports.length && viewMode === 'grid'" class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <article
          v-for="report in reports"
          :key="report.id"
          role="button"
          tabindex="0"
          class="group flex cursor-pointer flex-col overflow-hidden rounded-xl border bg-card shadow-xs transition-all hover:border-primary/40 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          @click="openReportDetail(report)"
          @keydown.enter.prevent="openReportDetail(report)"
          @keydown.space.prevent="openReportDetail(report)"
        >
          <!-- Cover Image or Category Placeholder -->
          <div class="relative aspect-[16/10] w-full overflow-hidden bg-muted">
            <img
              v-if="getReportPhotos(report).length"
              :src="resolvePhotoUrl(getReportPhotos(report)[0])"
              :alt="report.title"
              class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
            />
            <div v-else class="flex h-full w-full flex-col items-center justify-center gap-1.5 text-muted-foreground/60">
              <ImageIcon class="h-8 w-8" />
              <span class="text-[11px]">{{ t('community.noPhoto') }}</span>
            </div>

            <!-- Top Overlay Badges -->
            <div class="pointer-events-none absolute inset-x-2.5 top-2.5 flex items-start justify-between gap-2">
              <Badge variant="secondary" class="gap-1 bg-background/90 text-[11px] font-medium text-foreground shadow-xs backdrop-blur-xs">
                <component :is="getCategoryIcon(report.category_name)" class="h-3 w-3 text-primary" />
                {{ localizedCategory(report.category_name, report.category_name_km, locale) }}
              </Badge>
              <StatusBadge :status="report.status" class="shadow-xs" />
            </div>

            <!-- Bottom-right Multi-Photo Indicator -->
            <div
              v-if="getReportPhotos(report).length > 1"
              class="pointer-events-none absolute bottom-2 right-2 inline-flex items-center gap-1 rounded-md bg-black/65 px-2 py-0.5 text-[11px] font-medium text-white backdrop-blur-xs"
            >
              <Camera class="h-3 w-3" />
              {{ getReportPhotos(report).length }}
            </div>
          </div>

          <!-- Card Body -->
          <div class="flex flex-1 flex-col justify-between gap-3 p-4">
            <div class="space-y-1.5">
              <h2 class="line-clamp-1 text-base font-semibold tracking-tight text-foreground transition-colors group-hover:text-primary">
                {{ report.title }}
              </h2>
              <p class="line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                {{ report.description }}
              </p>
            </div>

            <!-- Footer Location & Date -->
            <div class="flex flex-wrap items-center justify-between gap-2 border-t pt-3 text-[11px] text-muted-foreground">
              <span class="inline-flex min-w-0 items-center gap-1 font-medium text-foreground/80">
                <MapPin class="h-3.5 w-3.5 shrink-0 text-primary" />
                <span class="truncate">
                  <template v-if="report.district_name">
                    {{ localizedCategory(report.district_name, report.district_name_km, locale) }},
                  </template>
                  {{ locale === 'km' ? report.province_name_km : report.province_name }}
                </span>
              </span>
              <span class="inline-flex shrink-0 items-center gap-1 tabular-nums">
                <Calendar class="h-3 w-3" />
                <time :datetime="report.reported_on">
                  {{ dateFormatter.format(new Date(report.reported_on + 'T00:00:00Z')) }}
                </time>
              </span>
            </div>
          </div>
        </article>
      </div>

      <!-- Compact List View -->
      <div v-else-if="reports.length" class="overflow-hidden rounded-xl border bg-card shadow-xs">
        <ul class="divide-y">
          <li
            v-for="report in reports"
            :key="report.id"
            role="button"
            tabindex="0"
            class="group flex cursor-pointer flex-col gap-3 p-4 transition-colors hover:bg-muted/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary sm:flex-row sm:items-center sm:justify-between"
            @click="openReportDetail(report)"
            @keydown.enter.prevent="openReportDetail(report)"
            @keydown.space.prevent="openReportDetail(report)"
          >
            <div class="flex min-w-0 items-start gap-3.5 sm:items-center">
              <!-- Thumbnail or Category Placeholder -->
              <div class="relative h-16 w-20 shrink-0 overflow-hidden rounded-lg border bg-muted sm:w-24">
                <img
                  v-if="getReportPhotos(report).length"
                  :src="resolvePhotoUrl(getReportPhotos(report)[0])"
                  :alt="report.title"
                  class="h-full w-full object-cover transition-transform duration-200 group-hover:scale-105"
                  loading="lazy"
                />
                <div v-else class="flex h-full w-full items-center justify-center text-muted-foreground/60">
                  <component :is="getCategoryIcon(report.category_name)" class="h-5 w-5" />
                </div>
                <span
                  v-if="getReportPhotos(report).length > 1"
                  class="absolute bottom-1 right-1 inline-flex items-center gap-0.5 rounded bg-black/65 px-1 py-0.5 text-[10px] font-medium text-white"
                >
                  <Camera class="h-2.5 w-2.5" />
                  {{ getReportPhotos(report).length }}
                </span>
              </div>

              <!-- Details -->
              <div class="min-w-0 space-y-1">
                <div class="flex flex-wrap items-center gap-2">
                  <h2 class="truncate text-sm font-semibold text-foreground transition-colors group-hover:text-primary sm:text-base">
                    {{ report.title }}
                  </h2>
                  <Badge variant="secondary" class="gap-1 text-[11px] font-medium">
                    <component :is="getCategoryIcon(report.category_name)" class="h-3 w-3 text-primary" />
                    {{ localizedCategory(report.category_name, report.category_name_km, locale) }}
                  </Badge>
                </div>
                <p class="line-clamp-1 text-xs text-muted-foreground">
                  {{ report.description }}
                </p>
                <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
                  <span class="inline-flex items-center gap-1 font-medium text-foreground/80">
                    <MapPin class="h-3 w-3 text-primary" />
                    <template v-if="report.district_name">
                      {{ localizedCategory(report.district_name, report.district_name_km, locale) }},
                    </template>
                    {{ locale === 'km' ? report.province_name_km : report.province_name }}
                  </span>
                  <span class="inline-flex items-center gap-1 tabular-nums">
                    <Calendar class="h-3 w-3" />
                    <time :datetime="report.reported_on">
                      {{ dateFormatter.format(new Date(report.reported_on + 'T00:00:00Z')) }}
                    </time>
                  </span>
                </div>
              </div>
            </div>

            <div class="flex items-center justify-end gap-2 sm:shrink-0">
              <StatusBadge :status="report.status" />
              <ChevronRight class="hidden h-4 w-4 text-muted-foreground/60 transition-transform group-hover:translate-x-0.5 group-hover:text-foreground sm:block" />
            </div>
          </li>
        </ul>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="!failed"
        class="flex flex-col items-center justify-center rounded-xl border bg-card px-6 py-12 text-center shadow-xs"
      >
        <p class="text-sm font-medium text-muted-foreground">
          {{ hasActiveFilters ? t('community.emptyFiltered') : t('community.empty') }}
        </p>
        <Button
          v-if="hasActiveFilters"
          type="button"
          variant="outline"
          size="sm"
          class="mt-3 gap-1.5 text-xs"
          @click="resetFilters"
        >
          <RotateCcw class="h-3.5 w-3.5" />
          {{ t('community.resetFilters') }}
        </Button>
      </div>

      <!-- Pagination Controls -->
      <nav
        v-if="page > 0 || hasMore"
        :aria-label="t('community.pagination')"
        class="flex items-center justify-between gap-2"
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

      <!-- Subtle Privacy Caption -->
      <p class="text-center text-xs text-muted-foreground">
        {{ t('community.privacyNote') }}
      </p>

      <!-- Public Report Detail Dialog -->
      <Dialog v-model:open="detailOpen">
        <DialogContent v-if="selectedReport" class="max-h-[90vh] max-w-2xl overflow-y-auto">
          <DialogHeader class="space-y-2 text-left">
            <div class="flex flex-wrap items-center justify-between gap-2 pr-6">
              <div class="flex flex-wrap items-center gap-2">
                <Badge variant="outline" class="font-mono text-xs tabular-nums text-muted-foreground">
                  #{{ selectedReport.id }}
                </Badge>
                <Badge variant="secondary" class="gap-1 text-xs font-medium">
                  <component :is="getCategoryIcon(selectedReport.category_name)" class="h-3 w-3 text-primary" />
                  {{ localizedCategory(selectedReport.category_name, selectedReport.category_name_km, locale) }}
                </Badge>
                <StatusBadge :status="selectedReport.status" />
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                class="h-7 gap-1.5 px-2.5 text-xs"
                @click="copyShareLink"
              >
                <Check v-if="linkCopied" class="h-3 w-3 text-emerald-600 stroke-[3]" />
                <Share2 v-else class="h-3 w-3 text-primary" />
                {{ linkCopied ? t('community.linkCopied') : t('community.shareReport') }}
              </Button>
            </div>
            <DialogTitle class="text-lg font-bold leading-snug sm:text-xl">
              {{ selectedReport.title }}
            </DialogTitle>
            <DialogDescription class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span class="inline-flex items-center gap-1 font-medium text-foreground/80">
                <MapPin class="h-3.5 w-3.5 text-primary" />
                <template v-if="selectedReport.district_name">
                  {{ localizedCategory(selectedReport.district_name, selectedReport.district_name_km, locale) }},
                </template>
                {{ locale === 'km' ? selectedReport.province_name_km : selectedReport.province_name }}
              </span>
              <span class="inline-flex items-center gap-1 tabular-nums">
                <Calendar class="h-3.5 w-3.5" />
                <time :datetime="selectedReport.reported_on">
                  {{ dateFormatter.format(new Date(selectedReport.reported_on + 'T00:00:00Z')) }}
                </time>
              </span>
            </DialogDescription>
          </DialogHeader>

          <!-- Photo Gallery -->
          <div
            v-if="selectedPhotos.length"
            class="space-y-2.5"
            tabindex="0"
            @keydown.left.prevent="activePhotoIndex > 0 && activePhotoIndex--"
            @keydown.right.prevent="activePhotoIndex < selectedPhotos.length - 1 && activePhotoIndex++"
          >
            <div class="group relative flex h-[280px] items-center justify-center overflow-hidden rounded-xl border bg-zinc-950/95 sm:h-[360px]">
              <img
                :src="resolvePhotoUrl(selectedPhotos[activePhotoIndex])"
                :alt="selectedReport.title"
                class="max-h-full max-w-full object-contain transition-opacity duration-200"
              />

              <!-- Top-Right Counter & Open Original -->
              <div class="absolute right-2.5 top-2.5 flex items-center gap-1.5">
                <span
                  v-if="selectedPhotos.length > 1"
                  class="rounded-md bg-black/65 px-2 py-1 text-[11px] font-medium tabular-nums text-white backdrop-blur-xs"
                >
                  {{ activePhotoIndex + 1 }} / {{ selectedPhotos.length }}
                </span>
                <a
                  :href="resolvePhotoUrl(selectedPhotos[activePhotoIndex])"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex h-7 w-7 items-center justify-center rounded-md bg-black/65 text-white backdrop-blur-xs transition hover:bg-black/85"
                  :title="t('common.openInNewTab')"
                >
                  <ExternalLink class="h-3.5 w-3.5" />
                </a>
              </div>

              <!-- Prev / Next Arrows -->
              <template v-if="selectedPhotos.length > 1">
                <Button
                  type="button"
                  variant="secondary"
                  size="icon"
                  class="absolute left-2.5 top-1/2 h-8 w-8 -translate-y-1/2 rounded-full bg-black/60 text-white shadow-sm backdrop-blur-xs transition hover:bg-black/80 disabled:opacity-30"
                  :disabled="activePhotoIndex === 0"
                  :aria-label="t('detail.previousPhoto')"
                  @click="activePhotoIndex--"
                >
                  <ChevronLeft class="h-4 w-4" />
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  size="icon"
                  class="absolute right-2.5 top-1/2 h-8 w-8 -translate-y-1/2 rounded-full bg-black/60 text-white shadow-sm backdrop-blur-xs transition hover:bg-black/80 disabled:opacity-30"
                  :disabled="activePhotoIndex === selectedPhotos.length - 1"
                  :aria-label="t('detail.nextPhoto')"
                  @click="activePhotoIndex++"
                >
                  <ChevronRight class="h-4 w-4" />
                </Button>
              </template>
            </div>

            <!-- Thumbnail Strip -->
            <div v-if="selectedPhotos.length > 1" class="flex gap-2 overflow-x-auto pb-1">
              <button
                v-for="(path, idx) in selectedPhotos"
                :key="path"
                type="button"
                class="h-14 w-20 shrink-0 overflow-hidden rounded-lg border-2 bg-muted transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                :class="idx === activePhotoIndex ? 'border-primary ring-1 ring-primary' : 'border-transparent opacity-60 hover:opacity-100'"
                @click="activePhotoIndex = idx"
              >
                <img :src="resolvePhotoUrl(path)" alt="" class="h-full w-full object-cover" />
              </button>
            </div>
          </div>

          <!-- Description -->
          <div class="space-y-1.5 rounded-xl border bg-muted/20 p-4">
            <h3 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {{ t('detail.description') }}
            </h3>
            <p class="whitespace-pre-line text-sm leading-relaxed text-foreground">
              {{ selectedReport.description }}
            </p>
          </div>

          <!-- Latest Municipal Update / Resolution Note -->
          <div
            v-if="selectedReport.resolution_note"
            class="space-y-1.5 rounded-xl border border-primary/20 bg-primary/5 p-4"
          >
            <div class="flex items-center gap-1.5 text-xs font-semibold text-primary">
              <MessageSquareText class="h-3.5 w-3.5" />
              <span>{{ t('community.municipalUpdate') }}</span>
            </div>
            <p class="whitespace-pre-line text-sm leading-relaxed text-foreground">
              {{ selectedReport.resolution_note }}
            </p>
          </div>

          <!-- Privacy Notice -->
          <div class="flex items-start gap-2 text-xs text-muted-foreground">
            <ShieldCheck class="mt-0.5 h-4 w-4 shrink-0 text-primary" />
            <p>{{ t('community.privacyNote') }}</p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  </AppLayout>
</template>
