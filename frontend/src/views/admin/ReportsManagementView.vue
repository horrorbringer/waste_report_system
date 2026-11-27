<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Search, Edit3, Eye, CheckCircle2, AlertCircle, FilterX, Trash2, CheckSquare, X, ImageIcon, Download } from 'lucide-vue-next'
import StatusBadge from '@/components/StatusBadge.vue'
import TablePagination from '@/components/TablePagination.vue'
import { useReportStore } from '@/stores/reports'
import { useCategoryStore } from '@/stores/categories'
import { formatApiError, formatDate, resolvePhotoUrl } from '@/lib/utils'
import { localizedCategory, translateStatus } from '@/i18n'
import type { ReportStatus, WasteReport } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const { t, locale } = useI18n()
const reportStore = useReportStore()
const categoryStore = useCategoryStore()

const searchQuery = ref('')
const statusFilter = ref('ALL')
const categoryFilter = ref('ALL')

// Status update dialog state
const dialogOpen = ref(false)
const selectedReport = ref<WasteReport | null>(null)
const newStatus = ref<ReportStatus>('In Progress')
const note = ref('')
const saving = ref(false)
const successMsg = ref('')
const errorMsg = ref('')

// Delete confirmation dialog state
const deleteDialogOpen = ref(false)
const reportToDelete = ref<WasteReport | null>(null)
const deleting = ref(false)

// Bulk selection & actions state
const selectedIds = ref<number[]>([])
const bulkStatusDialogOpen = ref(false)
const bulkDeleteDialogOpen = ref(false)
const bulkStatus = ref<ReportStatus>('In Progress')
const bulkNote = ref('')
const bulkProcessing = ref(false)
const selectedPhoto = ref<string | null>(null)
const selectedPhotoTitle = ref('')

function openPhotoPreview(photoPath: string, reportTitle: string) {
  selectedPhoto.value = resolvePhotoUrl(photoPath)
  selectedPhotoTitle.value = reportTitle
}

const allSelected = computed(() => {
  return reportStore.allReports.length > 0 && selectedIds.value.length === reportStore.allReports.length
})

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = reportStore.allReports.map((r) => r.id)
  }
}

function toggleSelectRow(id: number) {
  if (selectedIds.value.includes(id)) {
    selectedIds.value = selectedIds.value.filter((item) => item !== id)
  } else {
    selectedIds.value = [...selectedIds.value, id]
  }
}

function clearSelection() {
  selectedIds.value = []
}

const pageLimit = 15
const pageOffset = ref(0)

async function loadReports() {
  selectedIds.value = []
  await reportStore.fetchAllReports({
    status: statusFilter.value,
    category_id: categoryFilter.value,
    search: searchQuery.value,
    limit: pageLimit,
    offset: pageOffset.value,
  })
}

onMounted(async () => {
  await Promise.all([categoryStore.fetchCategories(), loadReports()])
})

let searchTimeout: ReturnType<typeof setTimeout> | null = null
watch([statusFilter, categoryFilter], () => {
  pageOffset.value = 0
  loadReports()
})
watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    pageOffset.value = 0
    loadReports()
  }, 250)
})

function resetFilters() {
  searchQuery.value = ''
  statusFilter.value = 'ALL'
  categoryFilter.value = 'ALL'
}

function openStatusModal(report: WasteReport) {
  selectedReport.value = report
  newStatus.value = report.status
  note.value = ''
  errorMsg.value = ''
  dialogOpen.value = true
}

async function handleStatusUpdate() {
  if (!selectedReport.value) return
  saving.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    await reportStore.updateReportStatus(selectedReport.value.id, newStatus.value, note.value)
    successMsg.value = t('adminReports.updatedSuccess', {
      id: selectedReport.value.id,
      status: translateStatus(newStatus.value, t),
    })
    dialogOpen.value = false
    await loadReports()
  } catch (err: any) {
    errorMsg.value = formatApiError(err, t('adminReports.errUpdateFailed'))
  } finally {
    saving.value = false
  }
}

function openDeleteModal(report: WasteReport) {
  reportToDelete.value = report
  errorMsg.value = ''
  deleteDialogOpen.value = true
}

async function handleDeleteReport() {
  if (!reportToDelete.value) return
  deleting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  const targetId = reportToDelete.value.id
  try {
    await reportStore.deleteReport(targetId)
    successMsg.value = t('adminReports.deletedSuccess', { id: targetId })
    deleteDialogOpen.value = false
    reportToDelete.value = null
  } catch (err: any) {
    errorMsg.value = formatApiError(err, t('adminReports.errDeleteFailed'))
  } finally {
    deleting.value = false
  }
}

async function handleBulkStatusUpdate() {
  if (!selectedIds.value.length) return
  bulkProcessing.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const affected = await reportStore.bulkUpdateStatus(selectedIds.value, bulkStatus.value, bulkNote.value)
    successMsg.value = t('adminReports.bulkStatusSuccess', {
      count: affected,
      status: translateStatus(bulkStatus.value, t),
    })
    bulkStatusDialogOpen.value = false
    bulkNote.value = ''
    await loadReports()
  } catch (err: any) {
    errorMsg.value = formatApiError(err, t('adminReports.errUpdateFailed'))
  } finally {
    bulkProcessing.value = false
  }
}

async function handleBulkDelete() {
  if (!selectedIds.value.length) return
  bulkProcessing.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const affected = await reportStore.bulkDeleteReports(selectedIds.value)
    successMsg.value = t('adminReports.bulkDeleteSuccess', { count: affected })
    bulkDeleteDialogOpen.value = false
    selectedIds.value = []
  } catch (err: any) {
    errorMsg.value = formatApiError(err, t('adminReports.errDeleteFailed'))
  } finally {
    bulkProcessing.value = false
  }
}

const exporting = ref(false)
async function handleExportCsv() {
  exporting.value = true
  errorMsg.value = ''
  try {
    await reportStore.exportReportsCsv({
      status: statusFilter.value,
      category_id: categoryFilter.value,
      search: searchQuery.value,
    })
  } catch (err: any) {
    errorMsg.value = formatApiError(err, t('adminReports.errExportFailed'))
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-eyebrow mb-1">{{ t('adminReports.eyebrow') }}</p>
        <h2 class="heading-page">{{ t('adminReports.title') }}</h2>
        <p class="mt-1 text-sm leading-relaxed text-muted-foreground">
          {{ t('adminReports.subtitle') }}
        </p>
      </div>
      <Button
        variant="outline"
        class="gap-2"
        :disabled="exporting || reportStore.allReports.length === 0"
        @click="handleExportCsv"
      >
        <Download class="h-4 w-4" />
        {{ exporting ? t('adminReports.exportingCsv') : t('adminReports.exportCsv') }}
      </Button>
    </div>

    <Alert v-if="successMsg" variant="success">
      <CheckCircle2 class="h-4 w-4" />
      <AlertDescription>{{ successMsg }}</AlertDescription>
    </Alert>

    <Alert v-if="errorMsg" variant="destructive">
      <AlertCircle class="h-4 w-4" />
      <AlertDescription>{{ errorMsg }}</AlertDescription>
    </Alert>

    <Card>
      <CardHeader>
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>{{ t('adminReports.tableTitle') }}</CardTitle>
            <CardDescription>
              {{ t('adminReports.matchingCount', { count: reportStore.totalAllReports }) }}
            </CardDescription>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <div class="relative w-full sm:w-64">
              <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                v-model="searchQuery"
                :placeholder="t('adminReports.searchPlaceholder')"
                class="pl-9"
              />
            </div>

            <div class="w-44">
              <Select v-model="statusFilter">
                <SelectTrigger>
                  <SelectValue :placeholder="t('status.allStatuses')" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">{{ t('status.allStatuses') }}</SelectItem>
                  <SelectItem value="Pending">{{ t('status.pending') }}</SelectItem>
                  <SelectItem value="In Progress">{{ t('status.inProgress') }}</SelectItem>
                  <SelectItem value="Resolved">{{ t('status.resolved') }}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="w-48">
              <Select v-model="categoryFilter">
                <SelectTrigger>
                  <SelectValue :placeholder="t('adminReports.allCategories')" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">{{ t('adminReports.allCategories') }}</SelectItem>
                  <SelectItem
                    v-for="cat in categoryStore.categories"
                    :key="cat.id"
                    :value="String(cat.id)"
                  >
                    {{ localizedCategory(cat.name, cat.name_km, locale) }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              v-if="searchQuery || statusFilter !== 'ALL' || categoryFilter !== 'ALL'"
              variant="ghost"
              size="sm"
              @click="resetFilters"
            >
              <FilterX class="h-4 w-4" />
              {{ t('common.reset') }}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent class="space-y-4">
        <!-- Bulk Action Bar -->
        <div
          v-if="selectedIds.length > 0"
          class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-primary/25 bg-primary/5 px-4 py-2.5"
        >
          <div class="flex items-center gap-2 text-xs font-semibold text-primary">
            <CheckSquare class="h-4 w-4" />
            <span>{{ t('adminReports.selectedCount', { count: selectedIds.length }) }}</span>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              class="h-8 gap-1.5 bg-background text-xs"
              @click="bulkStatusDialogOpen = true"
            >
              <Edit3 class="h-3.5 w-3.5 text-primary" />
              {{ t('adminReports.bulkStatusBtn') }}
            </Button>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              class="h-8 gap-1.5 text-xs"
              @click="bulkDeleteDialogOpen = true"
            >
              <Trash2 class="h-3.5 w-3.5" />
              {{ t('adminReports.bulkDeleteBtn') }}
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              class="h-8 gap-1 px-2 text-xs text-muted-foreground hover:text-foreground"
              @click="clearSelection"
            >
              <X class="h-3.5 w-3.5" />
              {{ t('adminReports.clearSelection') }}
            </Button>
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead class="w-[40px]">
                <input
                  type="checkbox"
                  class="h-4 w-4 rounded border-input accent-primary cursor-pointer"
                  :checked="allSelected"
                  :aria-label="t('adminReports.selectedCount', { count: reportStore.allReports.length })"
                  @change="toggleSelectAll"
                />
              </TableHead>
              <TableHead>{{ t('adminReports.colIssue') }}</TableHead>
              <TableHead>{{ t('adminDashboard.colCategory') }}</TableHead>
              <TableHead>{{ t('adminDashboard.colReporter') }}</TableHead>
              <TableHead>{{ t('adminDashboard.colStatus') }}</TableHead>
              <TableHead>{{ t('adminDashboard.colSubmitted') }}</TableHead>
              <TableHead class="text-right">{{ t('adminReports.colActions') }}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="report in reportStore.allReports"
              :key="report.id"
              :class="{ 'bg-primary/5': selectedIds.includes(report.id) }"
            >
              <TableCell>
                <input
                  type="checkbox"
                  class="h-4 w-4 rounded border-input accent-primary cursor-pointer"
                  :checked="selectedIds.includes(report.id)"
                  :aria-label="`Select report #${report.id}`"
                  @change="toggleSelectRow(report.id)"
                />
              </TableCell>
              <TableCell>
                <div class="flex items-center gap-3">
                  <button
                    v-if="report.photo_path"
                    type="button"
                    class="group relative h-10 w-10 shrink-0 overflow-hidden rounded-lg border bg-muted/30 transition hover:ring-2 hover:ring-primary/40 focus:outline-none"
                    @click="openPhotoPreview(report.photo_path, report.title)"
                  >
                    <img
                      :src="resolvePhotoUrl(report.photo_path)"
                      :alt="report.title"
                      class="h-full w-full object-cover transition duration-200 group-hover:scale-110"
                      loading="lazy"
                    />
                  </button>
                  <div
                    v-else
                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-dashed bg-muted/10 text-muted-foreground/40"
                  >
                    <ImageIcon class="h-4 w-4" />
                  </div>

                  <div class="min-w-0 max-w-[230px]">
                    <div class="flex items-center gap-1.5">
                      <span class="shrink-0 rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] font-semibold tabular-nums text-muted-foreground">
                        #{{ report.id }}
                      </span>
                      <RouterLink
                        :to="`/reports/${report.id}`"
                        class="truncate font-medium text-foreground hover:text-primary hover:underline"
                      >
                        {{ report.title }}
                      </RouterLink>
                    </div>
                    <p class="mt-0.5 truncate text-xs text-muted-foreground">{{ report.location_text }}</p>
                  </div>
                </div>
              </TableCell>
              <TableCell>
                <Badge variant="secondary" class="whitespace-nowrap">
                  {{ localizedCategory(report.category_name, report.category_name_km, locale) }}
                </Badge>
              </TableCell>
              <TableCell>
                <p class="whitespace-nowrap text-sm font-medium">{{ report.reporter_name }}</p>
                <p class="max-w-[150px] truncate text-xs text-muted-foreground">{{ report.reporter_email }}</p>
              </TableCell>
              <TableCell>
                <StatusBadge :status="report.status" />
              </TableCell>
              <TableCell class="whitespace-nowrap text-xs tabular-nums text-muted-foreground">
                {{ formatDate(report.created_at, locale) }}
              </TableCell>
              <TableCell class="whitespace-nowrap text-right">
                <!-- Grouped Row Action Pill -->
                <div class="inline-flex items-center rounded-lg border bg-background p-0.5 shadow-2xs">
                  <RouterLink
                    :to="`/reports/${report.id}`"
                    class="inline-flex h-7 items-center gap-1 rounded-md px-2 text-xs font-medium text-foreground transition-colors hover:bg-muted"
                    :title="t('common.view')"
                  >
                    <Eye class="h-3.5 w-3.5 text-muted-foreground" />
                    <span class="hidden xl:inline">{{ t('common.view') }}</span>
                  </RouterLink>
                  <span class="mx-0.5 h-4 w-px bg-border" aria-hidden="true" />
                  <button
                    type="button"
                    class="inline-flex h-7 items-center gap-1 rounded-md px-2 text-xs font-medium text-foreground transition-colors hover:bg-muted"
                    :title="t('adminReports.statusBtn')"
                    @click="openStatusModal(report)"
                  >
                    <Edit3 class="h-3.5 w-3.5 text-primary" />
                    <span class="hidden xl:inline">{{ t('adminReports.statusBtn') }}</span>
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

            <TableRow v-if="!reportStore.loading && reportStore.allReports.length === 0">
              <TableCell colspan="7" class="py-10 text-center text-muted-foreground">
                {{ t('adminReports.emptyFiltered') }}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
        <TablePagination
          :total="reportStore.totalAllReports"
          :limit="pageLimit"
          :offset="pageOffset"
          :loading="reportStore.loading"
          @update:offset="(val) => { pageOffset = val; loadReports() }"
        />
      </CardContent>
    </Card>

    <!-- Update Status Dialog -->
    <Dialog v-model:open="dialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{{ t('adminReports.dialogTitle', { id: selectedReport?.id }) }}</DialogTitle>
          <DialogDescription>
            {{ selectedReport?.title }}
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-2">
          <div class="space-y-2">
            <Label>{{ t('adminReports.cleanupStatus') }}</Label>
            <Select v-model="newStatus">
              <SelectTrigger>
                <SelectValue :placeholder="t('detail.selectStatus')" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Pending">{{ t('status.pending') }}</SelectItem>
                <SelectItem value="In Progress">{{ t('status.inProgress') }}</SelectItem>
                <SelectItem value="Resolved">{{ t('status.resolved') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label for="admin-note">{{ t('adminReports.auditNote') }}</Label>
            <Textarea
              id="admin-note"
              v-model="note"
              rows="3"
              :placeholder="t('adminReports.auditNotePlaceholder')"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="dialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button :disabled="saving" @click="handleStatusUpdate">
            {{ saving ? t('adminReports.updating') : t('adminReports.saveUpdate') }}
          </Button>
        </DialogFooter>
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
          <Button variant="outline" :disabled="deleting" @click="deleteDialogOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button variant="destructive" :disabled="deleting" @click="handleDeleteReport">
            {{ deleting ? t('adminReports.deleting') : t('adminReports.confirmDelete') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Bulk Status Update Dialog -->
    <Dialog v-model:open="bulkStatusDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ t('adminReports.bulkStatusTitle', { count: selectedIds.length }) }}</DialogTitle>
          <DialogDescription>
            {{ t('adminReports.subtitle') }}
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-2">
          <div class="space-y-2">
            <Label>{{ t('adminReports.cleanupStatus') }}</Label>
            <Select v-model="bulkStatus">
              <SelectTrigger>
                <SelectValue :placeholder="t('detail.selectStatus')" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Pending">{{ t('status.pending') }}</SelectItem>
                <SelectItem value="In Progress">{{ t('status.inProgress') }}</SelectItem>
                <SelectItem value="Resolved">{{ t('status.resolved') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label for="bulk-admin-note">{{ t('adminReports.auditNote') }}</Label>
            <Textarea
              id="bulk-admin-note"
              v-model="bulkNote"
              rows="3"
              :placeholder="t('adminReports.auditNotePlaceholder')"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" :disabled="bulkProcessing" @click="bulkStatusDialogOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button :disabled="bulkProcessing" @click="handleBulkStatusUpdate">
            {{ bulkProcessing ? t('adminReports.updating') : t('adminReports.saveUpdate') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Bulk Delete Confirmation Dialog -->
    <Dialog v-model:open="bulkDeleteDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ t('adminReports.bulkDeleteTitle', { count: selectedIds.length }) }}</DialogTitle>
          <DialogDescription>
            {{ t('adminReports.bulkDeleteDesc', { count: selectedIds.length }) }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" :disabled="bulkProcessing" @click="bulkDeleteDialogOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button variant="destructive" :disabled="bulkProcessing" @click="handleBulkDelete">
            {{ bulkProcessing ? t('adminReports.deleting') : t('adminReports.confirmDelete') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Photo Zoom Modal -->
    <Dialog :open="Boolean(selectedPhoto)" @update:open="selectedPhoto = null">
      <DialogContent class="max-w-3xl">
        <DialogHeader>
          <DialogTitle class="truncate text-sm font-semibold">{{ selectedPhotoTitle }}</DialogTitle>
        </DialogHeader>
        <div v-if="selectedPhoto" class="flex max-h-[70vh] items-center justify-center overflow-hidden rounded-lg bg-muted/20 p-2">
          <img :src="selectedPhoto" :alt="selectedPhotoTitle" class="max-h-[65vh] w-auto rounded object-contain" />
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>
