<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  HardHat,
  Leaf,
  Package,
  Pencil,
  Plus,
  Search,
  Tag,
  Trash2,
  X,
} from 'lucide-vue-next'
import { useCategoryStore } from '@/stores/categories'
import type { Category } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
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

const { t, locale } = useI18n()
const categoryStore = useCategoryStore()

const searchQuery = ref('')

const dialogOpen = ref(false)
const editingId = ref<number | null>(null)
const formName = ref('')
const formNameKm = ref('')
const formDescription = ref('')
const formDescriptionKm = ref('')
const saving = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const deleteDialogOpen = ref(false)
const categoryToDelete = ref<Category | null>(null)
const deleting = ref(false)

onMounted(() => {
  categoryStore.fetchCategories()
})

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

const filteredCategories = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return categoryStore.categories
  return categoryStore.categories.filter((cat) => {
    return (
      cat.name.toLowerCase().includes(query) ||
      (cat.name_km ?? '').toLowerCase().includes(query) ||
      (cat.description ?? '').toLowerCase().includes(query) ||
      (cat.description_km ?? '').toLowerCase().includes(query)
    )
  })
})

function openCreateDialog() {
  editingId.value = null
  formName.value = ''
  formNameKm.value = ''
  formDescription.value = ''
  formDescriptionKm.value = ''
  errorMsg.value = ''
  dialogOpen.value = true
}

function openEditDialog(cat: Category) {
  editingId.value = cat.id
  formName.value = cat.name
  formNameKm.value = cat.name_km ?? ''
  formDescription.value = cat.description ?? ''
  formDescriptionKm.value = cat.description_km ?? ''
  errorMsg.value = ''
  dialogOpen.value = true
}

async function handleSave() {
  errorMsg.value = ''
  successMsg.value = ''
  if (formName.value.trim().length < 2) {
    errorMsg.value = t('adminCategories.errMinName')
    return
  }

  saving.value = true
  const payload = {
    name: formName.value.trim(),
    name_km: formNameKm.value.trim() || null,
    description: formDescription.value.trim() || null,
    description_km: formDescriptionKm.value.trim() || null,
  }

  try {
    if (editingId.value === null) {
      await categoryStore.createCategory(payload)
      successMsg.value = t('adminCategories.createdMsg', { name: payload.name })
    } else {
      await categoryStore.updateCategory(editingId.value, payload)
      successMsg.value = t('adminCategories.updatedMsg', { name: payload.name })
    }
    dialogOpen.value = false
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || t('adminCategories.errSaveFailed')
  } finally {
    saving.value = false
  }
}

function openDeleteDialog(cat: Category) {
  categoryToDelete.value = cat
  errorMsg.value = ''
  deleteDialogOpen.value = true
}

async function handleConfirmDelete() {
  if (!categoryToDelete.value) return
  deleting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  const target = categoryToDelete.value
  try {
    await categoryStore.deleteCategory(target.id)
    successMsg.value = t('adminCategories.deletedMsg', { name: target.name })
    deleteDialogOpen.value = false
    categoryToDelete.value = null
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || t('adminCategories.errDeleteFailed')
    deleteDialogOpen.value = false
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-eyebrow mb-1">{{ t('adminCategories.eyebrow') }}</p>
        <h2 class="heading-page">{{ t('adminCategories.title') }}</h2>
        <p class="mt-1 text-sm leading-relaxed text-muted-foreground">
          {{ t('adminCategories.subtitle') }}
        </p>
      </div>
      <Button class="gap-2" @click="openCreateDialog">
        <Plus class="h-4 w-4" />
        {{ t('adminCategories.addCategory') }}
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

    <Card class="border-border/60 shadow-sm">
      <CardHeader class="pb-3">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle class="text-base font-semibold">{{ t('adminCategories.activeTitle') }}</CardTitle>
            <CardDescription class="text-xs">
              {{ t('adminCategories.configuredCount', { count: categoryStore.categories.length }) }}
            </CardDescription>
          </div>
          <div class="relative w-full sm:w-64">
            <Search class="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              v-model="searchQuery"
              :placeholder="t('adminReports.searchPlaceholder')"
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
        </div>
      </CardHeader>

      <CardContent class="p-0">
        <div class="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow class="bg-muted/30">
                <TableHead>{{ t('adminCategories.colName') }}</TableHead>
                <TableHead>{{ t('adminCategories.colNameKm') }}</TableHead>
                <TableHead>{{ t('adminCategories.colDesc') }}</TableHead>
                <TableHead>{{ t('adminCategories.colReports') }}</TableHead>
                <TableHead class="text-right">{{ t('adminCategories.colActions') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <!-- Loading Skeletons -->
              <template v-if="categoryStore.loading && categoryStore.categories.length === 0">
                <TableRow v-for="n in 4" :key="`cat-skel-${n}`">
                  <TableCell>
                    <div class="flex items-center gap-2.5">
                      <Skeleton class="h-8 w-8 rounded-lg" />
                      <Skeleton class="h-4 w-32" />
                    </div>
                  </TableCell>
                  <TableCell><Skeleton class="h-4 w-28" /></TableCell>
                  <TableCell><Skeleton class="h-4 w-64" /></TableCell>
                  <TableCell><Skeleton class="h-5 w-16 rounded-full" /></TableCell>
                  <TableCell class="text-right"><Skeleton class="ml-auto h-8 w-20 rounded-lg" /></TableCell>
                </TableRow>
              </template>

              <TableRow
                v-for="cat in filteredCategories"
                v-else
                :key="cat.id"
                class="transition-colors hover:bg-muted/40"
              >
                <TableCell class="whitespace-nowrap">
                  <div class="flex items-center gap-2.5">
                    <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-primary/15 bg-primary/5 text-primary">
                      <component :is="getCategoryIcon(cat.name)" class="h-4 w-4" />
                    </span>
                    <span class="font-medium text-foreground">{{ cat.name }}</span>
                  </div>
                </TableCell>
                <TableCell class="whitespace-nowrap text-sm text-foreground">
                  {{ cat.name_km || '—' }}
                </TableCell>
                <TableCell class="max-w-md text-xs leading-relaxed text-muted-foreground">
                  {{ (locale === 'km' && cat.description_km ? cat.description_km : cat.description) || '—' }}
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" class="whitespace-nowrap font-mono text-xs tabular-nums">
                    {{ t('common.reportCount', { count: cat.report_count }) }}
                  </Badge>
                </TableCell>
                <TableCell class="whitespace-nowrap text-right">
                  <!-- Grouped Action Pill -->
                  <div class="inline-flex items-center rounded-lg border bg-background p-0.5 shadow-2xs">
                    <button
                      type="button"
                      class="inline-flex h-7 items-center gap-1 rounded-md px-2.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
                      :title="t('common.edit')"
                      @click="openEditDialog(cat)"
                    >
                      <Pencil class="h-3.5 w-3.5 text-primary" />
                      <span>{{ t('common.edit') }}</span>
                    </button>
                    <span class="mx-0.5 h-4 w-px bg-border" aria-hidden="true" />
                    <button
                      type="button"
                      class="inline-flex h-7 items-center justify-center rounded-md px-2 text-xs font-medium text-destructive transition-colors hover:bg-destructive/10 disabled:cursor-not-allowed disabled:opacity-40"
                      :disabled="cat.report_count > 0"
                      :title="
                        cat.report_count > 0
                          ? t('adminCategories.cannotDeleteTooltip')
                          : t('adminCategories.deleteTooltip')
                      "
                      @click="openDeleteDialog(cat)"
                    >
                      <Trash2 class="h-3.5 w-3.5" />
                    </button>
                  </div>
                </TableCell>
              </TableRow>

              <TableRow v-if="!categoryStore.loading && filteredCategories.length === 0">
                <TableCell colspan="5" class="py-10 text-center text-sm text-muted-foreground">
                  {{ t('adminReports.emptyFiltered') }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>

    <!-- Create / Edit Bilingual Category Dialog -->
    <Dialog v-model:open="dialogOpen">
      <DialogContent class="max-w-xl">
        <DialogHeader>
          <DialogTitle>
            {{ editingId === null ? t('adminCategories.dialogAddTitle') : t('adminCategories.dialogEditTitle') }}
          </DialogTitle>
          <DialogDescription>
            {{ t('adminCategories.dialogDesc') }}
          </DialogDescription>
        </DialogHeader>

        <form class="space-y-4 py-2" @submit.prevent="handleSave">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="space-y-2">
              <Label for="cat-name">{{ t('adminCategories.fieldNameEn') }}</Label>
              <Input id="cat-name" v-model="formName" placeholder="e.g. Plastic Waste" required />
            </div>

            <div class="space-y-2">
              <Label for="cat-name-km">{{ t('adminCategories.fieldNameKm') }}</Label>
              <Input id="cat-name-km" v-model="formNameKm" placeholder="ឧទាហរណ៍៖ សំណល់ប្លាស្ទិក" />
            </div>
          </div>

          <div class="space-y-2">
            <Label for="cat-desc">{{ t('adminCategories.fieldDescEn') }}</Label>
            <Textarea
              id="cat-desc"
              v-model="formDescription"
              rows="2"
              placeholder="Explain what types of waste belong in this category..."
            />
          </div>

          <div class="space-y-2">
            <Label for="cat-desc-km">{{ t('adminCategories.fieldDescKm') }}</Label>
            <Textarea
              id="cat-desc-km"
              v-model="formDescriptionKm"
              rows="2"
              placeholder="ពន្យល់អំពីប្រភេទសំណល់ដែលស្ថិតក្នុងចំណាត់ថ្នាក់នេះ..."
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" @click="dialogOpen = false">
              {{ t('common.cancel') }}
            </Button>
            <Button type="submit" :disabled="saving">
              {{
                saving
                  ? t('common.saving')
                  : editingId === null
                    ? t('adminCategories.createBtn')
                    : t('adminCategories.saveChangesBtn')
              }}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <!-- Delete Category Confirmation Dialog -->
    <Dialog v-model:open="deleteDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ t('adminCategories.deleteTooltip') }}</DialogTitle>
          <DialogDescription>
            {{ categoryToDelete?.name }} {{ categoryToDelete?.name_km ? `(${categoryToDelete.name_km})` : '' }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" size="sm" :disabled="deleting" @click="deleteDialogOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button variant="destructive" size="sm" :disabled="deleting" @click="handleConfirmDelete">
            {{ deleting ? t('adminReports.deleting') : t('adminReports.deleteBtn') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
