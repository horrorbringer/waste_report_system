<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowUpRight,
  Calendar,
  Compass,
  Filter,
  Grid,
  ImageIcon,
  Inbox,
  LayoutList,
  MapPin,
  PlusCircle,
  RefreshCw,
  RotateCcw,
  Search,
  Sparkles,
  Tag,
  Trash2,
  X,
} from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useReportStore } from '@/stores/reports'
import { useCategoryStore } from '@/stores/categories'
import { formatDate, resolvePhotoUrl } from '@/lib/utils'
import { localizedCategory, translateStatus } from '@/i18n'
import type { ReportStatus, WasteReport } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'

const { t, locale } = useI18n()
const reportStore = useReportStore()
const categoryStore = useCategoryStore()

const statusFilter = ref<'ALL' | ReportStatus>('ALL')
const selectedCategory = ref<string>('ALL')
const searchQuery = ref('')
const sortBy = ref<'newest' | 'oldest'>('newest')
const viewMode = ref<'grid' | 'list'>('grid')

const deleteDialogOpen = ref(false)
const reportToDelete = ref<WasteReport | null>(null)
const deleting = ref(false)

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
  } finally {
    deleting.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    reportStore.fetchMyReports(),
    categoryStore.fetchCategories(),
  ])
})

const myReports = computed(() => reportStore.myReports)

const statusFilters = computed(() => {
  const counts: Record<ReportStatus, number> = { Pending: 0, 'In Progress': 0, Resolved: 0 }
  for (const report of myReports.value) counts[report.status]++

  return [
    { value: 'ALL', label: 'common.all', count: myReports.value.length },
    { value: 'Pending', label: 'status.pending', count: counts.Pending },
    { value: 'In Progress', label: 'status.inProgress', count: counts['In Progress'] },
    { value: 'Resolved', label: 'status.resolved', count: counts.Resolved },
  ] as const
})

const filteredReports = computed(() => {
  let list = myReports.value.filter((r) => {
    const matchesStatus = statusFilter.value === 'ALL' || r.status === statusFilter.value
    const matchesCategory =
      selectedCategory.value === 'ALL' || String(r.category_id) === String(selectedCategory.value)

    const q = searchQuery.value.trim().toLowerCase()
    const matchesSearch =
      !q ||
      r.title.toLowerCase().includes(q) ||
      r.location_text.toLowerCase().includes(q) ||
      r.category_name.toLowerCase().includes(q) ||
      (r.category_name_km ?? '').toLowerCase().includes(q)

    return matchesStatus && matchesCategory && matchesSearch
  })

  return list.sort((a, b) => {
    const dateA = new Date(a.created_at).getTime()
    const dateB = new Date(b.created_at).getTime()
    return sortBy.value === 'newest' ? dateB - dateA : dateA - dateB
  })
})

function resetFilters() {
  statusFilter.value = 'ALL'
  selectedCategory.value = 'ALL'
  searchQuery.value = ''
  sortBy.value = 'newest'
}
</script>

<template>
  <AppLayout>
    <div class="container py-8 max-w-6xl">
      <!-- Header Section -->
      <div class="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p class="text-eyebrow mb-1.5 flex items-center gap-1.5">
            <span class="inline-block h-2 w-2 rounded-full bg-primary" />
            {{ t('myReports.eyebrow') }}
          </p>
          <h1 class="heading-page text-2xl font-bold tracking-tight md:text-3xl">
            {{ t('myReports.title') }}
          </h1>
          <p class="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {{ t('myReports.subtitle') }}
          </p>
        </div>

        <div class="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            class="h-9 gap-1.5 shadow-sm"
            :disabled="reportStore.loading"
            @click="reportStore.fetchMyReports()"
          >
            <RefreshCw class="h-3.5 w-3.5" :class="{ 'animate-spin': reportStore.loading }" />
            {{ t('common.refresh') }}
          </Button>

          <RouterLink to="/reports/new">
            <Button size="sm" class="h-9 gap-2 shadow-sm font-medium">
              <PlusCircle class="h-4 w-4" />
              {{ t('myReports.newReport') }}
            </Button>
          </RouterLink>
        </div>
      </div>

      <div class="mb-4 flex flex-wrap gap-1.5" role="group" :aria-label="t('myReports.statusFilter')">
        <Button
          v-for="filter in statusFilters"
          :key="filter.value"
          type="button"
          size="sm"
          :variant="statusFilter === filter.value ? 'secondary' : 'outline'"
          :aria-pressed="statusFilter === filter.value"
          class="h-9 gap-1.5 rounded-full px-2.5 font-medium aria-pressed:border-primary/30 aria-pressed:bg-primary/10 aria-pressed:text-primary"
          @click="statusFilter = filter.value"
        >
          {{ t(filter.label) }}
          <span class="text-xs tabular-nums text-muted-foreground">{{ filter.count }}</span>
        </Button>
      </div>

      <!-- Action & Search Toolbar -->
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-card p-3 shadow-sm">
        <!-- Left: Search Box -->
        <div class="relative min-w-64 flex-1 sm:max-w-xs">
          <Search class="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            v-model="searchQuery"
            :placeholder="t('myReports.searchPlaceholder')"
            class="h-8 pl-8 pr-7 text-xs"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            @click="searchQuery = ''"
          >
            <X class="h-3.5 w-3.5" />
          </button>
        </div>

        <!-- Right: Category, Sort & View Mode Switches -->
        <div class="flex flex-wrap items-center gap-2">
          <!-- Category Filter -->
          <Select v-model="selectedCategory">
            <SelectTrigger class="h-8 w-36 text-xs">
              <SelectValue :placeholder="t('myReports.allCategories')" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">{{ t('myReports.allCategories') }}</SelectItem>
              <SelectItem
                v-for="cat in categoryStore.categories"
                :key="cat.id"
                :value="String(cat.id)"
              >
                {{ localizedCategory(cat.name, cat.name_km, locale) }}
              </SelectItem>
            </SelectContent>
          </Select>

          <!-- Sort Filter -->
          <Select v-model="sortBy">
            <SelectTrigger class="h-8 w-32 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">{{ t('myReports.sortNewest') }}</SelectItem>
              <SelectItem value="oldest">{{ t('myReports.sortOldest') }}</SelectItem>
            </SelectContent>
          </Select>

          <!-- View Mode Toggle (Grid vs List) -->
          <div class="flex items-center rounded-lg border bg-muted/40 p-0.5">
            <button
              type="button"
              class="flex h-7 w-7 items-center justify-center rounded-md transition"
              :class="[
                viewMode === 'grid'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground',
              ]"
              :title="t('myReports.viewGrid')"
              @click="viewMode = 'grid'"
            >
              <Grid class="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              class="flex h-7 w-7 items-center justify-center rounded-md transition"
              :class="[
                viewMode === 'list'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground',
              ]"
              :title="t('myReports.viewList')"
              @click="viewMode = 'list'"
            >
              <LayoutList class="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State: Structured Skeletons -->
      <div v-if="reportStore.loading && myReports.length === 0" class="grid gap-4 md:grid-cols-2">
        <Card v-for="n in 4" :key="n" class="border-border/70 p-5 space-y-4">
          <div class="flex items-start justify-between">
            <div class="space-y-1.5 flex-1">
              <div class="flex gap-2">
                <Skeleton class="h-5 w-12 rounded-md" />
                <Skeleton class="h-5 w-24 rounded-md" />
              </div>
              <Skeleton class="h-5 w-3/4 rounded-md mt-2" />
            </div>
            <Skeleton class="h-6 w-20 rounded-full" />
          </div>
          <div class="space-y-2 pt-2 border-t border-border/50">
            <Skeleton class="h-4 w-4/5 rounded-md" />
            <Skeleton class="h-3.5 w-1/3 rounded-md" />
          </div>
          <div class="flex items-center justify-between pt-1">
            <Skeleton class="h-4 w-28 rounded-md" />
            <Skeleton class="h-8 w-20 rounded-lg" />
          </div>
        </Card>
      </div>

      <!-- Empty State: Zero Reports Ever -->
      <Card
        v-else-if="myReports.length === 0"
        class="border-dashed border-2 py-16 text-center shadow-sm"
      >
        <CardContent class="flex flex-col items-center">
          <div class="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Sparkles class="h-7 w-7" />
          </div>
          <h3 class="text-lg font-semibold text-foreground">{{ t('myReports.emptyTitle') }}</h3>
          <p class="mt-1.5 max-w-md text-sm leading-relaxed text-muted-foreground">
            {{ t('myReports.emptyFirst') }}
          </p>
          <RouterLink to="/reports/new" class="mt-5">
            <Button class="gap-2 shadow-sm font-medium">
              <PlusCircle class="h-4 w-4" />
              {{ t('myReports.submitFirstBtn') }}
            </Button>
          </RouterLink>
        </CardContent>
      </Card>

      <!-- Empty State: Filter Matched Nothing -->
      <Card
        v-else-if="filteredReports.length === 0"
        class="border-dashed border-2 py-14 text-center shadow-sm"
      >
        <CardContent class="flex flex-col items-center">
          <div class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Inbox class="h-6 w-6" />
          </div>
          <h3 class="text-base font-semibold text-foreground">{{ t('myReports.emptyTitle') }}</h3>
          <p class="mt-1 max-w-sm text-xs leading-relaxed text-muted-foreground">
            {{ t('myReports.emptyFiltered') }}
          </p>
          <Button variant="outline" size="sm" class="mt-4 gap-1.5 text-xs" @click="resetFilters">
            <RotateCcw class="h-3.5 w-3.5" />
            {{ t('myReports.resetFilters') }}
          </Button>
        </CardContent>
      </Card>

      <!-- Content Mode 1: Grid View -->
      <div
        v-else-if="viewMode === 'grid'"
        class="grid gap-4 sm:grid-cols-2 lg:grid-cols-2"
      >
        <RouterLink
          v-for="report in filteredReports"
          :key="report.id"
          :to="`/reports/${report.id}`"
          class="group block"
        >
          <Card class="h-full border-border/70 shadow-sm transition-all hover:border-primary/50 hover:shadow-md">
            <CardContent class="flex h-full flex-col justify-between p-4 sm:p-5">
              <div>
                <!-- Top Badges & ID -->
                <div class="mb-3 flex items-start justify-between gap-2">
                  <div class="flex items-center gap-1.5 overflow-hidden">
                    <Badge variant="outline" class="font-mono text-[11px] tabular-nums text-muted-foreground">
                      #{{ report.id }}
                    </Badge>
                    <Badge variant="secondary" class="gap-1 truncate text-xs font-normal">
                      <Tag class="h-3 w-3 text-primary" />
                      {{ localizedCategory(report.category_name, report.category_name_km, locale) }}
                    </Badge>
                  </div>
                  <StatusBadge :status="report.status" />
                </div>

                <!-- Main Card Body: Photo thumbnail + Title & Desc -->
                <div class="flex gap-3.5">
                  <!-- Thumbnail -->
                  <div
                    v-if="report.photo_path"
                    class="relative h-20 w-20 shrink-0 overflow-hidden rounded-lg border bg-muted/20"
                  >
                    <img
                      :src="resolvePhotoUrl(report.photo_path)"
                      :alt="report.title"
                      class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      loading="lazy"
                    />
                  </div>
                  <div
                    v-else
                    class="flex h-20 w-20 shrink-0 flex-col items-center justify-center rounded-lg border border-dashed bg-muted/10 text-muted-foreground/40"
                  >
                    <ImageIcon class="h-5 w-5 stroke-[1.5]" />
                  </div>

                  <!-- Text Body -->
                  <div class="min-w-0 flex-1">
                    <h3 class="line-clamp-2 text-sm font-semibold leading-snug text-foreground transition-colors group-hover:text-primary">
                      {{ report.title }}
                    </h3>
                    <p class="mt-1 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                      {{ report.description }}
                    </p>
                  </div>
                </div>
              </div>

              <!-- Footer: Location, GPS, Date & Action -->
              <div class="mt-4 flex flex-wrap items-center justify-between border-t border-border/60 pt-3 text-xs text-muted-foreground">
                <div class="min-w-0 flex-1 space-y-1 pr-2">
                  <div class="flex items-center gap-1.5 truncate">
                    <MapPin class="h-3.5 w-3.5 shrink-0 text-primary" />
                    <span class="truncate text-foreground/90 font-medium">{{ report.location_text }}</span>
                  </div>
                  <div class="flex items-center gap-2 text-[11px]">
                    <span class="inline-flex items-center gap-1 tabular-nums">
                      <Calendar class="h-3 w-3 text-muted-foreground" />
                      {{ formatDate(report.created_at, locale) }}
                    </span>
                    <span
                      v-if="report.latitude !== null && report.longitude !== null"
                      class="inline-flex items-center gap-1 rounded bg-muted px-1.5 py-0.2 text-[10px] font-mono text-foreground"
                    >
                      <Compass class="h-2.5 w-2.5 text-primary" />
                      {{ t('myReports.hasGps') }}
                    </span>
                  </div>
                </div>

                <div class="flex items-center gap-2 shrink-0">
                  <button
                    v-if="report.status === 'Pending'"
                    type="button"
                    class="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                    :aria-label="t('adminReports.deleteBtn')"
                    @click.prevent.stop="openDeleteModal(report)"
                  >
                    <Trash2 class="h-3.5 w-3.5" />
                  </button>
                  <span class="inline-flex shrink-0 items-center gap-1 text-xs font-medium text-primary transition-transform group-hover:translate-x-0.5">
                    {{ t('common.details') }}
                    <ArrowUpRight class="h-3.5 w-3.5" />
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </RouterLink>
      </div>

      <!-- Content Mode 2: Compact List View -->
      <Card v-else class="border-border/60 shadow-sm">
        <CardContent class="p-0">
          <div class="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow class="bg-muted/30">
                  <TableHead class="w-14 font-mono text-xs">ID</TableHead>
                  <TableHead class="w-14">Photo</TableHead>
                  <TableHead>Issue & Location</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead class="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow
                  v-for="report in filteredReports"
                  :key="report.id"
                  class="transition-colors hover:bg-muted/40"
                >
                  <TableCell class="font-mono text-xs tabular-nums text-muted-foreground">
                    #{{ report.id }}
                  </TableCell>

                  <!-- Photo Thumbnail -->
                  <TableCell>
                    <div
                      v-if="report.photo_path"
                      class="h-9 w-9 overflow-hidden rounded-md border bg-muted/20"
                    >
                      <img
                        :src="resolvePhotoUrl(report.photo_path)"
                        :alt="report.title"
                        class="h-full w-full object-cover"
                        loading="lazy"
                      />
                    </div>
                    <div
                      v-else
                      class="flex h-9 w-9 items-center justify-center rounded-md border border-dashed bg-muted/10 text-muted-foreground/40"
                    >
                      <ImageIcon class="h-3.5 w-3.5" />
                    </div>
                  </TableCell>

                  <!-- Title & Location -->
                  <TableCell>
                    <div class="max-w-[320px]">
                      <RouterLink
                        :to="`/reports/${report.id}`"
                        class="truncate text-xs font-semibold text-foreground hover:text-primary hover:underline block"
                      >
                        {{ report.title }}
                      </RouterLink>
                      <p class="truncate text-[11px] text-muted-foreground flex items-center gap-1 mt-0.5">
                        <MapPin class="h-3 w-3 shrink-0 text-primary" />
                        {{ report.location_text }}
                      </p>
                    </div>
                  </TableCell>

                  <!-- Category -->
                  <TableCell>
                    <Badge variant="secondary" class="whitespace-nowrap text-[11px] font-normal">
                      {{ localizedCategory(report.category_name, report.category_name_km, locale) }}
                    </Badge>
                  </TableCell>

                  <!-- Status -->
                  <TableCell>
                    <StatusBadge :status="report.status" />
                  </TableCell>

                  <!-- Submitted Date -->
                  <TableCell class="whitespace-nowrap text-xs tabular-nums text-muted-foreground">
                    {{ formatDate(report.created_at, locale) }}
                  </TableCell>

                  <!-- Action -->
                  <TableCell class="text-right">
                    <div class="inline-flex items-center justify-end gap-1">
                      <RouterLink :to="`/reports/${report.id}`">
                        <Button variant="ghost" size="sm" class="h-7 px-2.5 text-xs gap-1">
                          {{ t('common.details') }}
                          <ArrowUpRight class="h-3 w-3" />
                        </Button>
                      </RouterLink>
                      <Button
                        v-if="report.status === 'Pending'"
                        variant="ghost"
                        size="sm"
                        class="h-7 px-2 text-destructive hover:bg-destructive/10 hover:text-destructive"
                        :aria-label="t('adminReports.deleteBtn')"
                        @click="openDeleteModal(report)"
                      >
                        <Trash2 class="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <!-- Delete Pending Report Confirmation Dialog -->
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
  </AppLayout>
</template>
