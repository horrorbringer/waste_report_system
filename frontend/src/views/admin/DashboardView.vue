<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AdminHotspotMap from '@/components/AdminHotspotMap.vue'
import { formatApiError } from '@/lib/utils'
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Edit3,
  ExternalLink,
  Eye,
  FileText,
  Filter,
  ImageIcon,
  Loader2,
  MapPin,
  Maximize2,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  TrendingUp,
  User as UserIcon,
  X,
} from 'lucide-vue-next'
import StatusBadge from '@/components/StatusBadge.vue'
import { StatusDonutChart, CategoryBarChart } from '@/components/ui/chart'
import { useReportStore } from '@/stores/reports'
import { formatDate, resolvePhotoUrl } from '@/lib/utils'
import { localizedCategory, translateStatus } from '@/i18n'
import type { ReportStatus, WasteReport } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'

const { t, locale } = useI18n()
const router = useRouter()
const reportStore = useReportStore()

const searchQuery = ref('')
const recentStatusFilter = ref<'ALL' | ReportStatus>('ALL')
const selectedPhoto = ref<string | null>(null)
const selectedPhotoTitle = ref('')

// Quick Status Update Dialog State
const statusDialogOpen = ref(false)
const targetReport = ref<WasteReport | null>(null)
const nextStatus = ref<ReportStatus>('In Progress')
const statusNote = ref('')
const savingStatus = ref(false)
const updateError = ref('')

// Delete Dialog State
const deleteDialogOpen = ref(false)
const reportToDelete = ref<WasteReport | null>(null)
const deleting = ref(false)

onMounted(() => {
  reportStore.fetchAdminStats()
})

const stats = computed(() => reportStore.adminStats)

const totalReports = computed(() => stats.value?.total_reports ?? 0)
const pendingCount = computed(() => stats.value?.pending_count ?? 0)
const inProgressCount = computed(() => stats.value?.in_progress_count ?? 0)
const resolvedCount = computed(() => stats.value?.resolved_count ?? 0)

const resolutionRate = computed(() => {
  if (!stats.value || totalReports.value === 0) return 0
  return Math.round((resolvedCount.value / totalReports.value) * 100)
})

const pendingPercent = computed(() => {
  if (totalReports.value === 0) return 0
  return Math.round((pendingCount.value / totalReports.value) * 100)
})

const inProgressPercent = computed(() => {
  if (totalReports.value === 0) return 0
  return Math.round((inProgressCount.value / totalReports.value) * 100)
})

const topCategoryName = computed(() => {
  const dist = stats.value?.category_distribution
  if (!dist || dist.length === 0) return null
  const sorted = [...dist].sort((a, b) => b.count - a.count)
  const top = sorted[0]
  if (!top || top.count === 0) return null
  return localizedCategory(top.category, top.category_km, locale.value)
})

const filteredRecentReports = computed(() => {
  const reports = stats.value?.recent_reports ?? []
  const query = searchQuery.value.trim().toLowerCase()

  return reports.filter((r) => {
    if (recentStatusFilter.value !== 'ALL' && r.status !== recentStatusFilter.value) {
      return false
    }
    if (!query) return true
    const titleMatch = r.title.toLowerCase().includes(query)
    const locationMatch = r.location_text.toLowerCase().includes(query)
    const reporterMatch = r.reporter_name.toLowerCase().includes(query)
    const catMatch = r.category_name.toLowerCase().includes(query)
    const catKmMatch = (r.category_name_km ?? '').toLowerCase().includes(query)
    return titleMatch || locationMatch || reporterMatch || catMatch || catKmMatch || String(r.id) === query
  })
})

function openPhotoPreview(photoPath: string, reportTitle: string) {
  selectedPhoto.value = resolvePhotoUrl(photoPath)
  selectedPhotoTitle.value = reportTitle
}

function openStatusDialog(report: WasteReport) {
  targetReport.value = report
  nextStatus.value = report.status
  statusNote.value = ''
  updateError.value = ''
  statusDialogOpen.value = true
}

async function handleStatusSave() {
  if (!targetReport.value) return
  savingStatus.value = true
  updateError.value = ''
  try {
    await reportStore.updateReportStatus(
      targetReport.value.id,
      nextStatus.value,
      statusNote.value
    )
    statusDialogOpen.value = false
    await reportStore.fetchAdminStats()
  } catch (err: any) {
    updateError.value = formatApiError(err, t('detail.errUpdateFailed'))
  } finally {
    savingStatus.value = false
  }
}

function openDeleteModal(report: WasteReport) {
  reportToDelete.value = report
  deleteDialogOpen.value = true
}

async function handleDeleteReport() {
  if (!reportToDelete.value) return
  deleting.value = true
  try {
    await reportStore.deleteReport(reportToDelete.value.id)
    deleteDialogOpen.value = false
    reportToDelete.value = null
    await reportStore.fetchAdminStats()
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Section with Live Status & Quick Action Buttons -->
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-eyebrow mb-1.5 flex items-center gap-1.5">
          <span class="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          {{ t('adminDashboard.eyebrow') }}
        </p>
        <h2 class="heading-page text-2xl font-bold tracking-tight md:text-3xl">
          {{ t('adminDashboard.title') }}
        </h2>
        <p class="mt-1 text-sm leading-relaxed text-muted-foreground">
          {{ t('adminDashboard.subtitle') }}
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2.5">
        <!-- Urgent Pending Action Shortcut -->
        <RouterLink
          v-if="pendingCount > 0"
          to="/admin/reports?status=Pending"
        >
          <Button
            size="sm"
            variant="outline"
            class="h-9 gap-1.5 border-amber-500/30 bg-amber-500/10 text-amber-700 hover:bg-amber-500/20 dark:text-amber-300"
          >
            <Clock class="h-3.5 w-3.5 text-amber-500" />
            {{ t('adminDashboard.quickTriage', { count: pendingCount }) }}
          </Button>
        </RouterLink>

        <!-- Live Refresh Button -->
        <Button
          variant="outline"
          size="sm"
          class="h-9 gap-1.5 shadow-sm"
          :disabled="reportStore.loading"
          @click="reportStore.fetchAdminStats()"
        >
          <RefreshCw class="h-3.5 w-3.5" :class="{ 'animate-spin': reportStore.loading }" />
          {{ t('common.refresh') }}
        </Button>

        <!-- Manage All Reports -->
        <RouterLink to="/admin/reports">
          <Button size="sm" class="h-9 gap-1.5 shadow-sm font-medium">
            {{ t('adminDashboard.manageAll') }}
            <ArrowRight class="h-3.5 w-3.5" />
          </Button>
        </RouterLink>
      </div>
    </div>

    <!-- Enhanced KPI Cards Grid with Themed Icon Badges -->
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <!-- KPI 1: Total Reports -->
      <Card class="border-border/60 shadow-sm transition hover:shadow-md">
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <span class="text-xs font-medium text-muted-foreground">{{ t('home.statTotal') }}</span>
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <FileText class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div v-if="reportStore.loading && !stats" class="space-y-2">
            <Skeleton class="h-8 w-20" />
            <Skeleton class="h-3 w-32" />
          </div>
          <div v-else>
            <div class="text-3xl font-bold tracking-tight font-display text-foreground">
              {{ totalReports }}
            </div>
            <div class="mt-2.5 flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {{ t('adminDashboard.acrossCategories', { count: stats?.total_categories ?? 0 }) }}
              </span>
              <span class="font-medium text-foreground">
                {{ stats?.total_users ?? 0 }} residents
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- KPI 2: Pending Triage -->
      <Card class="border-border/60 shadow-sm transition hover:shadow-md">
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <span class="text-xs font-medium text-amber-600 dark:text-amber-400">
            {{ t('home.statPending') }}
          </span>
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Clock class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div v-if="reportStore.loading && !stats" class="space-y-2">
            <Skeleton class="h-8 w-16" />
            <Skeleton class="h-3 w-28" />
          </div>
          <div v-else>
            <div class="text-3xl font-bold tracking-tight font-display text-amber-600 dark:text-amber-400">
              {{ pendingCount }}
            </div>
            <div class="mt-2.5 flex items-center justify-between text-xs">
              <span class="text-muted-foreground">{{ t('adminDashboard.awaitingTriage') }}</span>
              <span class="font-mono tabular-nums text-amber-600 dark:text-amber-400 font-medium">
                {{ pendingPercent }}%
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- KPI 3: In Progress -->
      <Card class="border-border/60 shadow-sm transition hover:shadow-md">
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <span class="text-xs font-medium text-blue-600 dark:text-blue-400">
            {{ t('home.statInProgress') }}
          </span>
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
            <Loader2 class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div v-if="reportStore.loading && !stats" class="space-y-2">
            <Skeleton class="h-8 w-16" />
            <Skeleton class="h-3 w-28" />
          </div>
          <div v-else>
            <div class="text-3xl font-bold tracking-tight font-display text-blue-600 dark:text-blue-400">
              {{ inProgressCount }}
            </div>
            <div class="mt-2.5 flex items-center justify-between text-xs">
              <span class="text-muted-foreground">{{ t('adminDashboard.cleanupUnderway') }}</span>
              <span class="font-mono tabular-nums text-blue-600 dark:text-blue-400 font-medium">
                {{ inProgressPercent }}%
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- KPI 4: Resolution Progress with Micro-Bar -->
      <Card class="border-border/60 shadow-sm transition hover:shadow-md">
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <span class="text-xs font-medium text-emerald-600 dark:text-emerald-400">
            {{ t('home.statResolved') }}
          </span>
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div v-if="reportStore.loading && !stats" class="space-y-2">
            <Skeleton class="h-8 w-16" />
            <Skeleton class="h-3 w-28" />
          </div>
          <div v-else>
            <div class="flex items-baseline justify-between">
              <div class="text-3xl font-bold tracking-tight font-display text-emerald-600 dark:text-emerald-400">
                {{ resolvedCount }}
              </div>
              <span class="font-mono text-sm font-semibold tabular-nums text-emerald-600 dark:text-emerald-400">
                {{ resolutionRate }}%
              </span>
            </div>
            <!-- Resolution Progress Bar -->
            <div class="mt-2.5 h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                class="h-full rounded-full bg-emerald-500 transition-all duration-500"
                :style="{ width: `${resolutionRate}%` }"
              />
            </div>
            <p class="mt-1.5 text-[11px] text-muted-foreground">
              {{ t('adminDashboard.resolutionRate', { rate: resolutionRate }) }}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Waste Hotspot Map -->
    <Card class="border-border/60 shadow-sm">
      <CardHeader class="pb-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <CardTitle class="text-base font-semibold">{{ t('adminDashboard.hotspotMapTitle') }}</CardTitle>
            <CardDescription class="text-xs">
              {{ t('adminDashboard.hotspotMapDesc', { count: stats?.map_pins?.length ?? 0 }) }}
            </CardDescription>
          </div>
          <div class="flex items-center gap-3 text-[11px] text-muted-foreground">
            <span class="inline-flex items-center gap-1.5">
              <span class="h-2.5 w-2.5 rounded-full bg-amber-500" />
              {{ t('status.pending') }}
            </span>
            <span class="inline-flex items-center gap-1.5">
              <span class="h-2.5 w-2.5 rounded-full bg-blue-500" />
              {{ t('status.inProgress') }}
            </span>
            <span class="inline-flex items-center gap-1.5">
              <span class="h-2.5 w-2.5 rounded-full bg-emerald-500" />
              {{ t('status.resolved') }}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <AdminHotspotMap :pins="stats?.map_pins ?? []" />
      </CardContent>
    </Card>

    <!-- Enhanced Recent Submissions Table with Status Filter, Search & Grouped Actions -->
    <Card class="border-border/60 shadow-sm">
      <CardHeader class="pb-3">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle class="text-base font-semibold">
              {{ t('adminDashboard.recentTitle') }}
            </CardTitle>
            <CardDescription class="text-xs">
              {{ t('adminDashboard.recentDesc') }}
            </CardDescription>
          </div>

          <!-- Status Filter Pills, Search & View All -->
          <div class="flex flex-wrap items-center gap-2">
            <div class="inline-flex items-center rounded-lg border bg-muted/40 p-0.5 text-xs">
              <button
                type="button"
                class="rounded-md px-2 py-1 font-medium transition-colors"
                :class="recentStatusFilter === 'ALL' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
                @click="recentStatusFilter = 'ALL'"
              >
                {{ t('community.allStatuses') }}
              </button>
              <button
                type="button"
                class="rounded-md px-2 py-1 font-medium transition-colors"
                :class="recentStatusFilter === 'Pending' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
                @click="recentStatusFilter = 'Pending'"
              >
                {{ t('status.pending') }}
              </button>
              <button
                type="button"
                class="rounded-md px-2 py-1 font-medium transition-colors"
                :class="recentStatusFilter === 'In Progress' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
                @click="recentStatusFilter = 'In Progress'"
              >
                {{ t('status.inProgress') }}
              </button>
              <button
                type="button"
                class="rounded-md px-2 py-1 font-medium transition-colors"
                :class="recentStatusFilter === 'Resolved' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
                @click="recentStatusFilter = 'Resolved'"
              >
                {{ t('status.resolved') }}
              </button>
            </div>

            <div class="relative w-52 sm:w-60">
              <Search class="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <Input
                v-model="searchQuery"
                :placeholder="t('adminDashboard.searchRecent')"
                class="h-8 pl-8 pr-7 text-xs"
              />
              <button
                v-if="searchQuery"
                type="button"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                @click="searchQuery = ''"
              >
                <X class="h-3.5 w-3.5" />
              </button>
            </div>

            <RouterLink to="/admin/reports">
              <Button variant="outline" size="sm" class="h-8 gap-1 text-xs">
                {{ t('adminDashboard.viewAll') }}
                <ArrowRight class="h-3 w-3" />
              </Button>
            </RouterLink>
          </div>
        </div>
      </CardHeader>

      <CardContent class="p-0">
        <div class="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow class="bg-muted/30">
                <TableHead>{{ t('adminDashboard.colReport') }}</TableHead>
                <TableHead>{{ t('adminDashboard.colCategory') }}</TableHead>
                <TableHead>{{ t('adminDashboard.colReporter') }}</TableHead>
                <TableHead>{{ t('adminDashboard.colStatus') }}</TableHead>
                <TableHead>{{ t('adminDashboard.colSubmitted') }}</TableHead>
                <TableHead class="text-right">{{ t('adminDashboard.colAction') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <!-- Loading Skeleton Rows -->
              <template v-if="reportStore.loading && !stats">
                <TableRow v-for="n in 4" :key="`skel-${n}`">
                  <TableCell>
                    <div class="flex items-center gap-3">
                      <Skeleton class="h-10 w-10 shrink-0 rounded-lg" />
                      <div class="space-y-1.5">
                        <Skeleton class="h-4 w-44" />
                        <Skeleton class="h-3 w-32" />
                      </div>
                    </div>
                  </TableCell>
                  <TableCell><Skeleton class="h-5 w-24 rounded-full" /></TableCell>
                  <TableCell><Skeleton class="h-4 w-24" /></TableCell>
                  <TableCell><Skeleton class="h-5 w-20 rounded-full" /></TableCell>
                  <TableCell><Skeleton class="h-4 w-24" /></TableCell>
                  <TableCell class="text-right"><Skeleton class="ml-auto h-8 w-24 rounded-lg" /></TableCell>
                </TableRow>
              </template>

              <TableRow
                v-for="report in filteredRecentReports"
                v-else
                :key="report.id"
                class="transition-colors hover:bg-muted/40"
              >
                <!-- Combined Thumbnail + #ID + Title & Location -->
                <TableCell>
                  <div class="flex items-center gap-3">
                    <div v-if="report.photo_path" class="group relative shrink-0">
                      <button
                        type="button"
                        class="relative h-10 w-10 overflow-hidden rounded-lg border bg-muted/30 transition hover:ring-2 hover:ring-primary/40 focus:outline-none"
                        @click="openPhotoPreview(report.photo_path, report.title)"
                      >
                        <img
                          :src="resolvePhotoUrl(report.photo_path)"
                          :alt="report.title"
                          class="h-full w-full object-cover transition duration-200 group-hover:scale-110"
                          loading="lazy"
                        />
                      </button>
                    </div>
                    <div
                      v-else
                      class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-dashed bg-muted/10 text-muted-foreground/40"
                    >
                      <ImageIcon class="h-4 w-4" />
                    </div>

                    <div class="min-w-0 max-w-[260px]">
                      <div class="flex items-center gap-1.5">
                        <span class="shrink-0 rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] font-semibold tabular-nums text-muted-foreground">
                          #{{ report.id }}
                        </span>
                        <RouterLink
                          :to="`/reports/${report.id}`"
                          class="truncate text-sm font-medium text-foreground hover:text-primary hover:underline"
                        >
                          {{ report.title }}
                        </RouterLink>
                      </div>
                      <p class="mt-0.5 flex items-center gap-1 truncate text-xs text-muted-foreground">
                        <MapPin class="h-3 w-3 shrink-0 text-primary" />
                        <span class="truncate">{{ report.location_text }}</span>
                      </p>
                    </div>
                  </div>
                </TableCell>

                <!-- Category Badge -->
                <TableCell>
                  <Badge variant="secondary" class="whitespace-nowrap text-xs font-normal">
                    {{ localizedCategory(report.category_name, report.category_name_km, locale) }}
                  </Badge>
                </TableCell>

                <!-- Reporter -->
                <TableCell class="whitespace-nowrap text-xs">
                  <div class="flex items-center gap-1.5">
                    <UserIcon class="h-3.5 w-3.5 text-muted-foreground" />
                    <span>{{ report.reporter_name }}</span>
                  </div>
                </TableCell>

                <!-- Status Badge -->
                <TableCell>
                  <StatusBadge :status="report.status" />
                </TableCell>

                <!-- Submitted Date -->
                <TableCell class="whitespace-nowrap text-xs tabular-nums text-muted-foreground">
                  {{ formatDate(report.created_at, locale) }}
                </TableCell>

                <!-- Grouped Action Pill -->
                <TableCell class="whitespace-nowrap text-right">
                  <div class="inline-flex items-center rounded-lg border bg-background p-0.5 shadow-2xs">
                    <RouterLink
                      :to="`/reports/${report.id}`"
                      class="inline-flex h-7 items-center gap-1 rounded-md px-2 text-xs font-medium text-foreground transition-colors hover:bg-muted"
                      :title="t('common.inspect')"
                    >
                      <Eye class="h-3.5 w-3.5 text-muted-foreground" />
                      <span class="hidden xl:inline">{{ t('common.inspect') }}</span>
                    </RouterLink>
                    <span class="mx-0.5 h-4 w-px bg-border" aria-hidden="true" />
                    <button
                      type="button"
                      class="inline-flex h-7 items-center gap-1 rounded-md px-2 text-xs font-medium text-foreground transition-colors hover:bg-muted"
                      :title="t('adminDashboard.quickStatus')"
                      @click="openStatusDialog(report)"
                    >
                      <Edit3 class="h-3.5 w-3.5 text-primary" />
                      <span class="hidden xl:inline">{{ t('adminDashboard.quickStatus') }}</span>
                    </button>
                    <span class="mx-0.5 h-4 w-px bg-border" aria-hidden="true" />
                    <button
                      type="button"
                      class="inline-flex h-7 items-center justify-center rounded-md px-2 text-xs font-medium text-destructive transition-colors hover:bg-destructive/10"
                      :title="t('adminReports.deleteBtn')"
                      :aria-label="t('adminReports.deleteBtn')"
                      @click="openDeleteModal(report)"
                    >
                      <Trash2 class="h-3.5 w-3.5" />
                    </button>
                  </div>
                </TableCell>
              </TableRow>

              <!-- Empty State -->
              <TableRow v-if="(!reportStore.loading || stats) && filteredRecentReports.length === 0">
                <TableCell colspan="6" class="py-12 text-center text-muted-foreground">
                  <div class="flex flex-col items-center justify-center gap-2">
                    <FileText class="h-8 w-8 text-muted-foreground/30" />
                    <p class="text-sm font-medium">{{ t('adminDashboard.noReports') }}</p>
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>

    <!-- Interactive Pipeline Segmented Bar (Across All Statuses) -->
    <div v-if="totalReports > 0" class="rounded-xl border bg-card p-4 shadow-sm">
      <div class="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs">
        <span class="font-semibold text-foreground flex items-center gap-1.5">
          <TrendingUp class="h-3.5 w-3.5 text-primary" />
          {{ t('adminDashboard.resolutionProgress') }}
        </span>
        <div class="flex flex-wrap items-center gap-4 text-xs">
          <span class="flex items-center gap-1.5 text-amber-600 dark:text-amber-400 font-medium">
            <span class="h-2 w-2 rounded-full bg-amber-500" />
            {{ t('status.pending') }}: {{ pendingCount }} ({{ pendingPercent }}%)
          </span>
          <span class="flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-medium">
            <span class="h-2 w-2 rounded-full bg-blue-500" />
            {{ t('status.inProgress') }}: {{ inProgressCount }} ({{ inProgressPercent }}%)
          </span>
          <span class="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
            <span class="h-2 w-2 rounded-full bg-emerald-500" />
            {{ t('status.resolved') }}: {{ resolvedCount }} ({{ resolutionRate }}%)
          </span>
        </div>
      </div>
      <!-- Continuous Segmented Bar -->
      <div class="flex h-3 w-full overflow-hidden rounded-full bg-muted/60 p-0.5">
        <div
          v-if="pendingCount > 0"
          class="h-full bg-amber-500 transition-all duration-300 first:rounded-l-full last:rounded-r-full"
          :style="{ width: `${(pendingCount / totalReports) * 100}%` }"
          :title="`Pending: ${pendingCount}`"
        />
        <div
          v-if="inProgressCount > 0"
          class="h-full bg-blue-500 transition-all duration-300 first:rounded-l-full last:rounded-r-full"
          :style="{ width: `${(inProgressCount / totalReports) * 100}%` }"
          :title="`In Progress: ${inProgressCount}`"
        />
        <div
          v-if="resolvedCount > 0"
          class="h-full bg-emerald-500 transition-all duration-300 first:rounded-l-full last:rounded-r-full"
          :style="{ width: `${(resolvedCount / totalReports) * 100}%` }"
          :title="`Resolved: ${resolvedCount}`"
        />
      </div>
    </div>

    <!-- Native shadcn-vue Charts Section -->
    <div class="grid gap-6 lg:grid-cols-7">
      <!-- Status Donut Chart (3 cols) -->
      <Card class="border-border/60 shadow-sm lg:col-span-3">
        <CardHeader class="pb-3">
          <div class="flex items-center justify-between">
            <CardTitle class="text-base font-semibold">
              {{ t('adminDashboard.statusChartTitle') }}
            </CardTitle>
            <Badge variant="outline" class="text-[11px] font-normal text-muted-foreground">
              Total: {{ totalReports }}
            </Badge>
          </div>
          <CardDescription class="text-xs">
            {{ t('adminDashboard.statusChartDesc') }}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <StatusDonutChart :data="stats?.status_distribution ?? []" />
        </CardContent>
      </Card>

      <!-- Category Bar Chart (4 cols) -->
      <Card class="border-border/60 shadow-sm lg:col-span-4">
        <CardHeader class="pb-3">
          <div class="flex items-center justify-between">
            <CardTitle class="text-base font-semibold">
              {{ t('adminDashboard.categoryChartTitle') }}
            </CardTitle>
            <Badge v-if="topCategoryName" variant="secondary" class="gap-1 text-[11px] font-normal">
              <Sparkles class="h-3 w-3 text-primary" />
              {{ t('adminDashboard.topCategory', { name: topCategoryName }) }}
            </Badge>
          </div>
          <CardDescription class="text-xs">
            {{ t('adminDashboard.categoryChartDesc') }}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CategoryBarChart :data="stats?.category_distribution ?? []" />
        </CardContent>
      </Card>
    </div>

    <!-- Quick Status Update Dialog Directly from Dashboard -->
    <Dialog v-model:open="statusDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle class="text-base">
            {{ t('adminReports.dialogTitle', { id: targetReport?.id }) }}
          </DialogTitle>
          <DialogDescription class="text-xs">
            {{ targetReport?.title }}
          </DialogDescription>
        </DialogHeader>

        <Alert v-if="updateError" variant="destructive" class="my-2">
          <AlertCircle class="h-4 w-4" />
          <AlertDescription>{{ updateError }}</AlertDescription>
        </Alert>

        <div class="space-y-4 py-2">
          <div class="space-y-1.5">
            <Label class="text-xs">{{ t('adminReports.cleanupStatus') }}</Label>
            <Select v-model="nextStatus">
              <SelectTrigger class="h-9 text-xs">
                <SelectValue :placeholder="t('detail.selectStatus')" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Pending">{{ t('status.pending') }}</SelectItem>
                <SelectItem value="In Progress">{{ t('status.inProgress') }}</SelectItem>
                <SelectItem value="Resolved">{{ t('status.resolved') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-1.5">
            <Label for="dash-status-note" class="text-xs">
              {{ t('adminReports.auditNote') }}
            </Label>
            <Textarea
              id="dash-status-note"
              v-model="statusNote"
              rows="3"
              :placeholder="t('adminReports.auditNotePlaceholder')"
              class="text-xs leading-relaxed"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" @click="statusDialogOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button size="sm" :disabled="savingStatus" class="min-w-24 gap-1.5" @click="handleStatusSave">
            {{ savingStatus ? t('adminReports.updating') : t('adminReports.saveUpdate') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Photo Zoom Modal -->
    <Dialog :open="Boolean(selectedPhoto)" @update:open="selectedPhoto = null">
      <DialogContent class="max-w-3xl">
        <DialogHeader>
          <DialogTitle class="text-sm font-semibold truncate">{{ selectedPhotoTitle }}</DialogTitle>
        </DialogHeader>
        <div v-if="selectedPhoto" class="flex max-h-[70vh] items-center justify-center overflow-hidden rounded-lg bg-muted/20 p-2">
          <img :src="selectedPhoto" :alt="selectedPhotoTitle" class="max-h-[65vh] w-auto object-contain rounded" />
        </div>
      </DialogContent>
    </Dialog>

    <!-- Delete Report Confirmation Dialog -->
    <Dialog v-model:open="deleteDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ t('adminReports.deleteTitle', { id: reportToDelete?.id }) }}</DialogTitle>
          <DialogDescription>
            {{ t('adminReports.deleteDesc') }}
          </DialogDescription>
        </DialogHeader>
        <div v-if="reportToDelete" class="rounded-lg border bg-muted/40 p-3 text-sm">
          <p class="font-medium text-foreground">{{ reportToDelete.title }}</p>
          <p class="mt-0.5 text-xs text-muted-foreground">{{ reportToDelete.location_text }}</p>
        </div>
        <DialogFooter>
          <Button variant="outline" size="sm" :disabled="deleting" @click="deleteDialogOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button variant="destructive" size="sm" :disabled="deleting" @click="handleDeleteReport">
            {{ deleting ? t('adminReports.deleting') : t('adminReports.confirmDelete') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>