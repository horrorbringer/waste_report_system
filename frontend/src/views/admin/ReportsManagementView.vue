<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Search, Edit3, Eye, CheckCircle2, AlertCircle, FilterX, Trash2 } from 'lucide-vue-next'
import StatusBadge from '@/components/StatusBadge.vue'
import { useReportStore } from '@/stores/reports'
import { useCategoryStore } from '@/stores/categories'
import { formatDate } from '@/lib/utils'
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

async function loadReports() {
  await reportStore.fetchAllReports({
    status: statusFilter.value,
    category_id: categoryFilter.value,
    search: searchQuery.value,
  })
}

onMounted(async () => {
  await Promise.all([categoryStore.fetchCategories(), loadReports()])
})

let searchTimeout: ReturnType<typeof setTimeout> | null = null
watch([statusFilter, categoryFilter], () => {
  loadReports()
})
watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
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
    errorMsg.value = err.response?.data?.detail || t('adminReports.errUpdateFailed')
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
    errorMsg.value = err.response?.data?.detail || t('adminReports.errDeleteFailed')
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <p class="text-eyebrow mb-1">{{ t('adminReports.eyebrow') }}</p>
      <h2 class="heading-page">{{ t('adminReports.title') }}</h2>
      <p class="mt-1 text-sm leading-relaxed text-muted-foreground">
        {{ t('adminReports.subtitle') }}
      </p>
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
              {{ t('adminReports.matchingCount', { count: reportStore.allReports.length }) }}
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

      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead class="w-[60px]">{{ t('adminDashboard.colId') }}</TableHead>
              <TableHead>{{ t('adminReports.colIssue') }}</TableHead>
              <TableHead>{{ t('adminDashboard.colCategory') }}</TableHead>
              <TableHead>{{ t('adminDashboard.colReporter') }}</TableHead>
              <TableHead>{{ t('adminDashboard.colStatus') }}</TableHead>
              <TableHead>{{ t('adminDashboard.colSubmitted') }}</TableHead>
              <TableHead class="text-right">{{ t('adminReports.colActions') }}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="report in reportStore.allReports" :key="report.id">
              <TableCell class="font-mono text-xs tabular-nums text-muted-foreground">#{{ report.id }}</TableCell>
              <TableCell>
                <div class="max-w-[220px]">
                  <p class="truncate font-medium">{{ report.title }}</p>
                  <p class="truncate text-xs text-muted-foreground">{{ report.location_text }}</p>
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
                <div class="flex items-center justify-end gap-1.5">
                  <RouterLink :to="`/reports/${report.id}`">
                    <Button variant="ghost" size="sm" class="px-2.5">
                      <Eye class="h-3.5 w-3.5" />
                      {{ t('common.view') }}
                    </Button>
                  </RouterLink>
                  <Button variant="outline" size="sm" class="px-2.5" @click="openStatusModal(report)">
                    <Edit3 class="h-3.5 w-3.5" />
                    {{ t('adminReports.statusBtn') }}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="px-2 text-destructive hover:bg-destructive/10 hover:text-destructive"
                    :aria-label="t('adminReports.deleteBtn')"
                    @click="openDeleteModal(report)"
                  >
                    <Trash2 class="h-3.5 w-3.5" />
                  </Button>
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
  </div>
</template>
