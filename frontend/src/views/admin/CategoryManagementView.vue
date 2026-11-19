<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Pencil, Trash2, AlertCircle, CheckCircle2 } from 'lucide-vue-next'
import { useCategoryStore } from '@/stores/categories'
import type { Category } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const { t, locale } = useI18n()
const categoryStore = useCategoryStore()

const dialogOpen = ref(false)
const editingId = ref<number | null>(null)
const formName = ref('')
const formNameKm = ref('')
const formDescription = ref('')
const formDescriptionKm = ref('')
const saving = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

onMounted(() => {
  categoryStore.fetchCategories()
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

async function handleDelete(cat: Category) {
  errorMsg.value = ''
  successMsg.value = ''
  try {
    await categoryStore.deleteCategory(cat.id)
    successMsg.value = t('adminCategories.deletedMsg', { name: cat.name })
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || t('adminCategories.errDeleteFailed')
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

    <Card>
      <CardHeader>
        <CardTitle>{{ t('adminCategories.activeTitle') }}</CardTitle>
        <CardDescription>
          {{ t('adminCategories.configuredCount', { count: categoryStore.categories.length }) }}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{{ t('adminCategories.colName') }}</TableHead>
              <TableHead>{{ t('adminCategories.colNameKm') }}</TableHead>
              <TableHead>{{ t('adminCategories.colDesc') }}</TableHead>
              <TableHead>{{ t('adminCategories.colReports') }}</TableHead>
              <TableHead class="text-right">{{ t('adminCategories.colActions') }}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="cat in categoryStore.categories" :key="cat.id">
              <TableCell class="whitespace-nowrap font-medium">{{ cat.name }}</TableCell>
              <TableCell class="whitespace-nowrap text-sm text-foreground">
                {{ cat.name_km || '—' }}
              </TableCell>
              <TableCell class="max-w-md text-sm text-muted-foreground">
                {{ (locale === 'km' && cat.description_km ? cat.description_km : cat.description) || '—' }}
              </TableCell>
              <TableCell>
                <Badge variant="secondary" class="whitespace-nowrap tabular-nums">
                  {{ t('common.reportCount', { count: cat.report_count }) }}
                </Badge>
              </TableCell>
              <TableCell class="whitespace-nowrap text-right">
                <div class="flex items-center justify-end gap-1.5">
                  <Button variant="outline" size="sm" @click="openEditDialog(cat)">
                    <Pencil class="h-3.5 w-3.5" />
                    {{ t('common.edit') }}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="text-destructive hover:bg-destructive/10 hover:text-destructive"
                    :disabled="cat.report_count > 0"
                    :title="
                      cat.report_count > 0
                        ? t('adminCategories.cannotDeleteTooltip')
                        : t('adminCategories.deleteTooltip')
                    "
                    @click="handleDelete(cat)"
                  >
                    <Trash2 class="h-3.5 w-3.5" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
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
  </div>
</template>
