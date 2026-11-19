<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  AlertCircle,
  AlertTriangle,
  Apple,
  ArrowLeft,
  Camera,
  Check,
  CheckCircle2,
  ExternalLink,
  Hammer,
  HelpCircle,
  ImageIcon,
  Info,
  Map,
  MapPin,
  Maximize2,
  Navigation,
  Package,
  Recycle,
  Send,
  Sparkles,
  Trash2,
  Tv,
  Upload,
  X,
} from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import MapLocationPicker from '@/components/MapLocationPicker.vue'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import { useReportStore } from '@/stores/reports'
import { localizedCategory } from '@/i18n'
import type { Category } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
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

const { t, locale } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const categoryStore = useCategoryStore()
const reportStore = useReportStore()

const title = ref('')
const categoryId = ref('')
const description = ref('')
const locationText = ref('')
const latitude = ref<string | number>('')
const longitude = ref<string | number>('')
const gpsAccuracy = ref<number | null>(null)
const showCoordFields = ref(false)

const photoFile = ref<File | null>(null)
const photoPreview = ref<string | null>(null)
const photoName = ref('')
const photoSize = ref('')
const isDragging = ref(false)
const zoomModalOpen = ref(false)

const error = ref('')
const locating = ref(false)
const mapPickerOpen = ref(false)

const quickTitles = [
  { key: 'quickTitle1' },
  { key: 'quickTitle2' },
  { key: 'quickTitle3' },
  { key: 'quickTitle4' },
]

onMounted(async () => {
  window.addEventListener('paste', handlePaste)
  await categoryStore.fetchCategories()
  if (categoryStore.categories.length > 0 && !categoryId.value) {
    categoryId.value = String(categoryStore.categories[0].id)
  }
})

onUnmounted(() => {
  window.removeEventListener('paste', handlePaste)
  if (photoPreview.value) {
    URL.revokeObjectURL(photoPreview.value)
  }
})

const selectedCategory = computed<Category | undefined>(() => {
  return categoryStore.categories.find((c) => String(c.id) === String(categoryId.value))
})

const selectedCategoryDesc = computed(() => {
  if (!selectedCategory.value) return ''
  if (locale.value === 'km' && selectedCategory.value.description_km) {
    return selectedCategory.value.description_km
  }
  return selectedCategory.value.description || ''
})

const isFormValid = computed(() => {
  return (
    title.value.trim().length >= 3 &&
    description.value.trim().length >= 10 &&
    locationText.value.trim().length >= 3 &&
    Boolean(categoryId.value)
  )
})

const mapsUrl = computed(() => {
  const lat = String(latitude.value ?? '').trim()
  const lng = String(longitude.value ?? '').trim()
  if (lat && lng) {
    return `https://www.google.com/maps?q=${lat},${lng}`
  }
  return ''
})

function getCategoryIcon(name: string) {
  const n = (name || '').toLowerCase()
  if (n.includes('plastic')) return Recycle
  if (n.includes('organic') || n.includes('food')) return Apple
  if (n.includes('overflow') || n.includes('bin') || n.includes('dump')) return Trash2
  if (n.includes('construct') || n.includes('debris') || n.includes('rubble')) return Hammer
  if (n.includes('electro') || n.includes('appliance') || n.includes('e-waste')) return Tv
  if (n.includes('hazard') || n.includes('toxic') || n.includes('chemical')) return AlertTriangle
  return Package
}

function getCategoryTheme(name: string) {
  const n = (name || '').toLowerCase()
  if (n.includes('plastic')) {
    return {
      bg: 'bg-sky-500/10 text-sky-600 dark:text-sky-400',
      activeBorder: 'border-sky-500 ring-2 ring-sky-500/20 bg-sky-500/5',
      badge: 'border-sky-500/30 text-sky-600 bg-sky-500/10',
    }
  }
  if (n.includes('organic') || n.includes('food')) {
    return {
      bg: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
      activeBorder: 'border-emerald-500 ring-2 ring-emerald-500/20 bg-emerald-500/5',
      badge: 'border-emerald-500/30 text-emerald-600 bg-emerald-500/10',
    }
  }
  if (n.includes('overflow') || n.includes('bin')) {
    return {
      bg: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
      activeBorder: 'border-amber-500 ring-2 ring-amber-500/20 bg-amber-500/5',
      badge: 'border-amber-500/30 text-amber-600 bg-amber-500/10',
    }
  }
  if (n.includes('construct') || n.includes('debris')) {
    return {
      bg: 'bg-slate-500/10 text-slate-700 dark:text-slate-300',
      activeBorder: 'border-slate-500 ring-2 ring-slate-500/20 bg-slate-500/5',
      badge: 'border-slate-500/30 text-slate-700 bg-slate-500/10',
    }
  }
  if (n.includes('electro')) {
    return {
      bg: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
      activeBorder: 'border-violet-500 ring-2 ring-violet-500/20 bg-violet-500/5',
      badge: 'border-violet-500/30 text-violet-600 bg-violet-500/10',
    }
  }
  if (n.includes('hazard')) {
    return {
      bg: 'bg-rose-500/10 text-rose-600 dark:text-rose-400',
      activeBorder: 'border-rose-500 ring-2 ring-rose-500/20 bg-rose-500/5',
      badge: 'border-rose-500/30 text-rose-600 bg-rose-500/10',
    }
  }
  return {
    bg: 'bg-primary/10 text-primary',
    activeBorder: 'border-primary ring-2 ring-primary/20 bg-primary/5',
    badge: 'border-primary/30 text-primary bg-primary/10',
  }
}

function processIncomingFile(file: File) {
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  const allowedExts = ['png', 'jpg', 'jpeg', 'webp']

  if (!allowedTypes.includes(file.type.toLowerCase()) && !allowedExts.includes(ext)) {
    error.value = t('submitReport.errInvalidFile')
    return false
  }

  if (file.size > 10 * 1024 * 1024) {
    error.value = t('submitReport.errFileSize')
    return false
  }

  error.value = ''
  if (photoPreview.value) {
    URL.revokeObjectURL(photoPreview.value)
  }

  photoFile.value = file
  photoName.value = file.name
  if (file.size > 1024 * 1024) {
    photoSize.value = (file.size / (1024 * 1024)).toFixed(1) + ' MB'
  } else {
    photoSize.value = Math.round(file.size / 1024) + ' KB'
  }
  photoPreview.value = URL.createObjectURL(file)
  return true
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  processIncomingFile(file)
  input.value = ''
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) {
    processIncomingFile(file)
  }
}

function handlePaste(event: ClipboardEvent) {
  const items = event.clipboardData?.items
  if (!items) return
  for (let i = 0; i < items.length; i++) {
    if (items[i].type.startsWith('image/')) {
      const file = items[i].getAsFile()
      if (file) {
        processIncomingFile(file)
        break
      }
    }
  }
}

function clearPhoto() {
  if (photoPreview.value) {
    URL.revokeObjectURL(photoPreview.value)
  }
  photoFile.value = null
  photoPreview.value = null
  photoName.value = ''
  photoSize.value = ''
}

function detectLocation() {
  if (!navigator.geolocation) {
    error.value = t('submitReport.errGeoUnsupported')
    return
  }
  locating.value = true
  error.value = ''
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      latitude.value = pos.coords.latitude.toFixed(6)
      longitude.value = pos.coords.longitude.toFixed(6)
      gpsAccuracy.value = Math.round(pos.coords.accuracy)
      locating.value = false
    },
    () => {
      error.value = t('submitReport.errGeoFailed')
      locating.value = false
    },
    { enableHighAccuracy: true, timeout: 8000 }
  )
}

function clearLocationGps() {
  latitude.value = ''
  longitude.value = ''
  gpsAccuracy.value = null
}

function handleMapLocationSelect(payload: { lat: number; lng: number; address?: string }) {
  latitude.value = payload.lat
  longitude.value = payload.lng
  gpsAccuracy.value = 5
  if (payload.address && (!locationText.value.trim() || locationText.value.length < 5)) {
    locationText.value = payload.address
  }
}

function applyQuickTitle(key: string) {
  title.value = t(`submitReport.${key}`)
}

async function handleSubmit() {
  error.value = ''
  if (!categoryId.value) {
    error.value = t('submitReport.errNoCategory')
    return
  }

  const cleanTitle = title.value.trim()
  const cleanDesc = description.value.trim()
  const cleanLocation = locationText.value.trim()

  if (cleanTitle.length < 3) {
    error.value = 'Title must be at least 3 characters.'
    return
  }
  if (cleanDesc.length < 10) {
    error.value = t('submitReport.minCharsNote')
    return
  }
  if (cleanLocation.length < 3) {
    error.value = 'Location must be at least 3 characters.'
    return
  }

  const formData = new FormData()
  formData.append('title', cleanTitle)
  formData.append('description', cleanDesc)
  formData.append('category_id', categoryId.value)
  formData.append('location_text', cleanLocation)

  const latStr = String(latitude.value ?? '').trim()
  const lngStr = String(longitude.value ?? '').trim()
  if (latStr !== '') formData.append('latitude', latStr)
  if (lngStr !== '') formData.append('longitude', lngStr)
  if (photoFile.value) formData.append('photo', photoFile.value)

  try {
    const created = await reportStore.submitReport(formData)
    router.push(`/reports/${created.id}`)
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('submitReport.errSubmitFailed')
  }
}
</script>

<template>
  <AppLayout>
    <div class="container max-w-6xl py-8">
      <!-- Breadcrumb & Top Navigation -->
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" class="gap-1.5" @click="router.back()">
          <ArrowLeft class="h-4 w-4" />
          {{ t('common.back') }}
        </Button>
        <Badge variant="outline" class="gap-1 px-3 py-1 text-xs text-muted-foreground">
          <Sparkles class="h-3.5 w-3.5 text-primary" />
          {{ t('brand.tagline') }}
        </Badge>
      </div>

      <!-- Page Header -->
      <div class="mb-8">
        <p class="text-eyebrow mb-1.5 flex items-center gap-1.5">
          <span class="inline-block h-2 w-2 rounded-full bg-primary" />
          {{ t('submitReport.eyebrow') }}
        </p>
        <h1 class="heading-page text-3xl font-bold tracking-tight">
          {{ t('submitReport.title') }}
        </h1>
        <p class="mt-1.5 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          {{ t('submitReport.subtitle') }}
        </p>
      </div>

      <!-- Main Layout: 8 cols Form + 4 cols Preview & Tips -->
      <div class="grid gap-8 lg:grid-cols-12">
        <!-- Left: Submission Form (8 cols) -->
        <div class="space-y-6 lg:col-span-8">
          <Alert v-if="error" variant="destructive" class="shadow-sm">
            <AlertCircle class="h-4 w-4" />
            <AlertDescription>{{ error }}</AlertDescription>
          </Alert>

          <form class="space-y-6" @submit.prevent="handleSubmit">
            <!-- SECTION 1: Category Selection -->
            <Card class="border-border/60 shadow-sm transition hover:border-border">
              <CardHeader class="pb-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                      1
                    </span>
                    <CardTitle class="text-base font-semibold">
                      {{ t('submitReport.step1') }}
                    </CardTitle>
                  </div>
                  <Badge variant="outline" class="text-[11px] font-normal text-muted-foreground">
                    Required *
                  </Badge>
                </div>
                <CardDescription class="text-xs">
                  {{ t('submitReport.step1Desc') }}
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <!-- Visual Category Cards Grid -->
                <div class="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
                  <button
                    v-for="cat in categoryStore.categories"
                    :key="cat.id"
                    type="button"
                    class="group relative flex flex-col items-start rounded-xl border p-3 text-left transition-all hover:bg-muted/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                    :class="[
                      String(categoryId) === String(cat.id)
                        ? getCategoryTheme(cat.name).activeBorder
                        : 'border-border/70 bg-card hover:border-muted-foreground/30',
                    ]"
                    @click="categoryId = String(cat.id)"
                  >
                    <!-- Icon & check indicator -->
                    <div class="mb-2 flex w-full items-center justify-between">
                      <div
                        class="flex h-8 w-8 items-center justify-center rounded-lg transition-transform group-hover:scale-105"
                        :class="getCategoryTheme(cat.name).bg"
                      >
                        <component :is="getCategoryIcon(cat.name)" class="h-4 w-4" />
                      </div>
                      <div
                        v-if="String(categoryId) === String(cat.id)"
                        class="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-sm"
                      >
                        <Check class="h-3 w-3 stroke-[3]" />
                      </div>
                    </div>
                    <!-- Localized Name -->
                    <span class="text-xs font-medium leading-tight text-foreground">
                      {{ localizedCategory(cat.name, cat.name_km, locale) }}
                    </span>
                  </button>
                </div>

                <!-- Fallback accessible dropdown -->
                <div class="pt-1">
                  <Select v-model="categoryId">
                    <SelectTrigger class="h-9 text-xs">
                      <SelectValue :placeholder="t('submitReport.fieldCategoryPlaceholder')" />
                    </SelectTrigger>
                    <SelectContent>
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

                <!-- Dynamic guidance callout for selected category -->
                <div
                  v-if="selectedCategoryDesc"
                  class="flex items-start gap-2.5 rounded-lg border border-border/80 bg-muted/30 p-3 text-xs text-muted-foreground"
                >
                  <Info class="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  <p class="leading-relaxed">
                    <strong class="font-medium text-foreground">
                      {{ localizedCategory(selectedCategory?.name || '', selectedCategory?.name_km, locale) }}:
                    </strong>
                    {{ selectedCategoryDesc }}
                  </p>
                </div>
              </CardContent>
            </Card>

            <!-- SECTION 2: Issue Overview (Title & Description) -->
            <Card class="border-border/60 shadow-sm transition hover:border-border">
              <CardHeader class="pb-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                      2
                    </span>
                    <CardTitle class="text-base font-semibold">
                      {{ t('submitReport.step2') }}
                    </CardTitle>
                  </div>
                  <Badge variant="outline" class="text-[11px] font-normal text-muted-foreground">
                    Required *
                  </Badge>
                </div>
                <CardDescription class="text-xs">
                  {{ t('submitReport.step2Desc') }}
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <!-- Title Field with Character Meter -->
                <div class="space-y-1.5">
                  <div class="flex items-center justify-between">
                    <Label for="title" class="text-xs font-medium">
                      {{ t('submitReport.fieldTitle') }}
                    </Label>
                    <span
                      class="text-[11px] font-mono tabular-nums"
                      :class="title.length >= 3 ? 'text-muted-foreground' : 'text-amber-500'"
                    >
                      {{ t('submitReport.charsCount', { count: title.length, max: 200 }) }}
                    </span>
                  </div>
                  <Input
                    id="title"
                    v-model="title"
                    :placeholder="t('submitReport.fieldTitlePlaceholder')"
                    required
                    minlength="3"
                    maxlength="200"
                    class="h-10 text-sm"
                  />
                  <!-- Quick suggestion chips -->
                  <div class="pt-1">
                    <p class="mb-1.5 text-[11px] text-muted-foreground">
                      {{ t('submitReport.quickTitlesLabel') }}
                    </p>
                    <div class="flex flex-wrap gap-1.5">
                      <button
                        v-for="chip in quickTitles"
                        :key="chip.key"
                        type="button"
                        class="inline-flex items-center rounded-full border border-border/80 bg-background px-2.5 py-0.5 text-[11px] text-muted-foreground transition hover:border-primary hover:bg-primary/5 hover:text-primary"
                        @click="applyQuickTitle(chip.key)"
                      >
                        + {{ t(`submitReport.${chip.key}`) }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Description Field with Character Progress -->
                <div class="space-y-1.5">
                  <div class="flex items-center justify-between">
                    <Label for="description" class="text-xs font-medium">
                      {{ t('submitReport.fieldDesc') }}
                    </Label>
                    <div class="flex items-center gap-2">
                      <span
                        v-if="description.length >= 10"
                        class="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400"
                      >
                        <Check class="h-3 w-3 stroke-[3]" />
                        Valid length
                      </span>
                      <span
                        v-else
                        class="text-[11px] text-muted-foreground"
                      >
                        {{ t('submitReport.minCharsNote') }}
                      </span>
                      <span class="text-[11px] font-mono tabular-nums text-muted-foreground">
                        {{ t('submitReport.charsCount', { count: description.length, max: 2000 }) }}
                      </span>
                    </div>
                  </div>
                  <Textarea
                    id="description"
                    v-model="description"
                    rows="4"
                    :placeholder="t('submitReport.fieldDescPlaceholder')"
                    required
                    minlength="10"
                    maxlength="2000"
                    class="resize-y text-sm leading-relaxed"
                  />
                </div>
              </CardContent>
            </Card>

            <!-- SECTION 3: Location & GPS Assist -->
            <Card class="border-border/60 shadow-sm transition hover:border-border">
              <CardHeader class="pb-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                      3
                    </span>
                    <CardTitle class="text-base font-semibold">
                      {{ t('submitReport.step3') }}
                    </CardTitle>
                  </div>
                  <Badge variant="outline" class="text-[11px] font-normal text-muted-foreground">
                    Required *
                  </Badge>
                </div>
                <CardDescription class="text-xs">
                  {{ t('submitReport.step3Desc') }}
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <!-- Location Address Input & One-click GPS Button -->
                <div class="space-y-1.5">
                  <div class="flex flex-wrap items-center justify-between gap-2">
                    <Label for="location" class="flex items-center gap-1.5 text-xs font-medium">
                      <MapPin class="h-3.5 w-3.5 text-primary" />
                      {{ t('submitReport.fieldLocation') }}
                    </Label>
                    <div class="flex flex-wrap items-center gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        class="h-8 gap-1.5 text-xs font-medium shadow-sm transition hover:border-primary hover:text-primary"
                        @click="mapPickerOpen = true"
                      >
                        <Map class="h-3.5 w-3.5 text-primary" />
                        {{ t('submitReport.pickOnMap') }}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        class="h-8 gap-1.5 text-xs font-medium shadow-sm transition hover:border-primary hover:text-primary"
                        :disabled="locating"
                        @click="detectLocation"
                      >
                        <Navigation class="h-3.5 w-3.5 text-primary" :class="{ 'animate-spin': locating }" />
                        {{ locating ? t('submitReport.locating') : t('submitReport.useGps') }}
                      </Button>
                    </div>
                  </div>
                  <Input
                    id="location"
                    v-model="locationText"
                    :placeholder="t('submitReport.fieldLocationPlaceholder')"
                    required
                    minlength="3"
                    maxlength="300"
                    class="h-10 text-sm"
                  />
                </div>

                <!-- GPS Status Bar (When coordinates exist) -->
                <div
                  v-if="latitude && longitude"
                  class="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3 text-xs"
                >
                  <div class="flex items-center gap-2">
                    <div class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                      <CheckCircle2 class="h-3.5 w-3.5" />
                    </div>
                    <div>
                      <p class="font-medium text-emerald-800 dark:text-emerald-200">
                        {{ t('submitReport.gpsSuccess') }}
                        <span v-if="gpsAccuracy" class="ml-1 text-[11px] font-normal text-muted-foreground">
                          ({{ t('submitReport.gpsAccuracy', { meters: gpsAccuracy }) }})
                        </span>
                      </p>
                      <p class="font-mono text-[11px] tabular-nums text-muted-foreground">
                        {{ latitude }}, {{ longitude }}
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="inline-flex items-center gap-1 rounded-md border bg-background px-2 py-1 text-[11px] font-medium text-foreground transition hover:border-primary hover:text-primary"
                      @click="mapPickerOpen = true"
                    >
                      <Map class="h-3 w-3 text-primary" />
                      {{ t('submitReport.pickOnMap') }}
                    </button>
                    <a
                      v-if="mapsUrl"
                      :href="mapsUrl"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="inline-flex items-center gap-1 rounded-md border bg-background px-2 py-1 text-[11px] font-medium text-muted-foreground transition hover:text-foreground"
                    >
                      <ExternalLink class="h-3 w-3" />
                      {{ t('submitReport.viewMaps') }}
                    </a>
                    <button
                      type="button"
                      class="text-[11px] text-muted-foreground underline-offset-4 hover:text-destructive hover:underline"
                      @click="clearLocationGps"
                    >
                      {{ t('submitReport.clearGps') }}
                    </button>
                  </div>
                </div>

                <!-- Toggle manual coordinate inputs -->
                <div class="pt-1">
                  <button
                    type="button"
                    class="text-[11px] font-medium text-primary hover:underline"
                    @click="showCoordFields = !showCoordFields"
                  >
                    {{ showCoordFields ? '− Hide coordinates' : '+ Fine-tune coordinates manually (optional)' }}
                  </button>

                  <div v-if="showCoordFields" class="mt-3 grid grid-cols-2 gap-3 rounded-lg border bg-muted/20 p-3">
                    <div class="space-y-1">
                      <Label for="lat" class="text-xs text-muted-foreground">{{ t('submitReport.latitude') }}</Label>
                      <Input id="lat" v-model="latitude" type="number" step="any" placeholder="11.5564" class="h-8 text-xs font-mono" />
                    </div>
                    <div class="space-y-1">
                      <Label for="lng" class="text-xs text-muted-foreground">{{ t('submitReport.longitude') }}</Label>
                      <Input id="lng" v-model="longitude" type="number" step="any" placeholder="104.9282" class="h-8 text-xs font-mono" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <!-- SECTION 4: Photo Evidence (Drag & Drop + Mobile Camera + Paste) -->
            <Card class="border-border/60 shadow-sm transition hover:border-border">
              <CardHeader class="pb-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                      4
                    </span>
                    <CardTitle class="text-base font-semibold">
                      {{ t('submitReport.step4') }}
                    </CardTitle>
                  </div>
                  <Badge variant="secondary" class="text-[11px] font-normal">
                    Optional
                  </Badge>
                </div>
                <CardDescription class="text-xs">
                  {{ t('submitReport.step4Desc') }}
                </CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <!-- Dropzone (when no photo is selected) -->
                <div
                  v-if="!photoPreview"
                  class="group relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-9 text-center transition-all"
                  :class="[
                    isDragging
                      ? 'border-primary bg-primary/10 scale-[1.01]'
                      : 'border-muted-foreground/25 bg-muted/10 hover:border-primary/50 hover:bg-muted/20',
                  ]"
                  @dragover.prevent="isDragging = true"
                  @dragleave.prevent="isDragging = false"
                  @drop.prevent="handleDrop"
                >
                  <div class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary transition-transform group-hover:scale-110">
                    <ImageIcon class="h-6 w-6" />
                  </div>
                  <p class="text-sm font-semibold text-foreground">
                    {{ t('submitReport.dragDropTitle') }}
                  </p>
                  <p class="mt-1 text-xs text-muted-foreground">
                    {{ t('submitReport.dragDropSubtitle') }}
                  </p>

                  <!-- Action Buttons inside Dropzone -->
                  <div class="mt-4 flex flex-wrap items-center justify-center gap-2">
                    <!-- Standard Browse -->
                    <label class="cursor-pointer">
                      <span
                        class="inline-flex h-9 items-center gap-1.5 rounded-lg border border-input bg-background px-3.5 text-xs font-medium shadow-sm transition hover:bg-accent hover:text-accent-foreground"
                      >
                        <Upload class="h-3.5 w-3.5" />
                        {{ t('submitReport.browseFiles') }}
                      </span>
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        class="hidden"
                        @change="handleFileChange"
                      />
                    </label>

                    <!-- Mobile Camera Direct Button -->
                    <label class="cursor-pointer sm:hidden">
                      <span
                        class="inline-flex h-9 items-center gap-1.5 rounded-lg border border-input bg-background px-3.5 text-xs font-medium shadow-sm transition hover:bg-accent"
                      >
                        <Camera class="h-3.5 w-3.5 text-primary" />
                        {{ t('submitReport.takePhoto') }}
                      </span>
                      <input
                        type="file"
                        accept="image/*"
                        capture="environment"
                        class="hidden"
                        @change="handleFileChange"
                      />
                    </label>
                  </div>

                  <!-- Paste Hint -->
                  <p class="mt-3 text-[11px] text-muted-foreground/80">
                    {{ t('submitReport.pasteHint') }}
                  </p>
                </div>

                <!-- Rich Photo Preview Card (when photo is uploaded) -->
                <div v-else class="space-y-3">
                  <div class="relative overflow-hidden rounded-xl border border-border/80 bg-muted/30 p-2 shadow-sm">
                    <!-- Preview Image Thumbnail with aspect-ratio containment -->
                    <div class="group relative flex max-h-80 items-center justify-center overflow-hidden rounded-lg bg-black/5 dark:bg-black/20">
                      <img
                        :src="photoPreview"
                        :alt="photoName || 'Report evidence'"
                        class="max-h-80 w-full object-contain"
                      />
                      <!-- Floating Zoom Action -->
                      <button
                        type="button"
                        class="absolute bottom-3 right-3 flex h-8 items-center gap-1.5 rounded-lg bg-background/90 px-2.5 text-xs font-medium text-foreground shadow-md backdrop-blur-sm transition hover:bg-background"
                        @click="zoomModalOpen = true"
                      >
                        <Maximize2 class="h-3.5 w-3.5" />
                        Preview
                      </button>
                    </div>

                    <!-- File Details & Action Controls -->
                    <div class="mt-2.5 flex flex-wrap items-center justify-between gap-2 px-1">
                      <div class="flex items-center gap-2 overflow-hidden">
                        <Badge variant="outline" class="font-mono text-[11px] tabular-nums">
                          {{ photoSize }}
                        </Badge>
                        <span class="truncate text-xs font-medium text-foreground" :title="photoName">
                          {{ photoName || 'photo_evidence' }}
                        </span>
                      </div>

                      <div class="flex items-center gap-2">
                        <!-- Replace Photo -->
                        <label class="cursor-pointer">
                          <span class="inline-flex h-7 items-center gap-1 rounded-md border bg-background px-2.5 text-xs font-medium text-muted-foreground transition hover:text-foreground">
                            <Upload class="h-3 w-3" />
                            {{ t('submitReport.replacePhoto') }}
                          </span>
                          <input
                            type="file"
                            accept="image/png,image/jpeg,image/webp"
                            class="hidden"
                            @change="handleFileChange"
                          />
                        </label>

                        <!-- Remove Photo -->
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          class="h-7 gap-1 px-2 text-xs text-destructive hover:bg-destructive/10 hover:text-destructive"
                          @click="clearPhoto"
                        >
                          <X class="h-3.5 w-3.5" />
                          {{ t('submitReport.removePhoto') }}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <!-- Bottom Action Controls -->
            <div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-card p-4 shadow-sm">
              <div class="text-xs text-muted-foreground">
                <span v-if="!isFormValid" class="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
                  <AlertCircle class="h-3.5 w-3.5" />
                  Please complete required title, description, and location.
                </span>
                <span v-else class="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 class="h-3.5 w-3.5" />
                  All required fields filled. Ready to submit!
                </span>
              </div>

              <div class="flex items-center gap-3">
                <RouterLink to="/my-reports">
                  <Button type="button" variant="outline" class="h-10">
                    {{ t('common.cancel') }}
                  </Button>
                </RouterLink>
                <Button
                  type="submit"
                  size="default"
                  class="h-10 min-w-36 gap-2 font-medium shadow-sm transition"
                  :disabled="reportStore.loading || !isFormValid"
                >
                  <Send class="h-4 w-4" :class="{ 'animate-pulse': reportStore.loading }" />
                  {{ reportStore.loading ? t('submitReport.submitting') : t('submitReport.submitBtn') }}
                </Button>
              </div>
            </div>
          </form>
        </div>

        <!-- Right: Sticky Live Preview & Civic Guidance (4 cols) -->
        <div class="space-y-6 lg:col-span-4">
          <!-- 1. Live Report Preview Card -->
          <Card class="border-border/60 shadow-sm">
            <CardHeader class="pb-3">
              <div class="flex items-center gap-2">
                <Sparkles class="h-4 w-4 text-primary" />
                <CardTitle class="text-sm font-semibold">
                  {{ t('submitReport.previewHeading') }}
                </CardTitle>
              </div>
              <CardDescription class="text-xs">
                {{ t('submitReport.previewDesc') }}
              </CardDescription>
            </CardHeader>
            <CardContent class="space-y-3">
              <div class="overflow-hidden rounded-xl border bg-muted/20 p-3.5 transition-all">
                <!-- Preview Top: Category badge & status -->
                <div class="mb-2 flex items-center justify-between gap-2">
                  <Badge
                    variant="outline"
                    class="text-[11px] font-medium"
                    :class="selectedCategory ? getCategoryTheme(selectedCategory.name).badge : ''"
                  >
                    {{ selectedCategory ? localizedCategory(selectedCategory.name, selectedCategory.name_km, locale) : 'Category' }}
                  </Badge>
                  <StatusBadge status="Pending" />
                </div>

                <!-- Preview Title -->
                <p class="font-semibold leading-snug text-foreground">
                  {{ title.trim() || t('submitReport.untitledReport') }}
                </p>

                <!-- Preview Location -->
                <p class="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                  <MapPin class="h-3 w-3 shrink-0 text-primary" />
                  <span class="truncate">{{ locationText.trim() || t('submitReport.noLocationYet') }}</span>
                </p>

                <!-- Preview Thumbnail / Placeholder -->
                <div class="mt-3 overflow-hidden rounded-lg border bg-background">
                  <img
                    v-if="photoPreview"
                    :src="photoPreview"
                    alt="Preview evidence"
                    class="h-32 w-full object-cover"
                  />
                  <div
                    v-else
                    class="flex h-24 flex-col items-center justify-center gap-1 text-muted-foreground/50"
                  >
                    <ImageIcon class="h-6 w-6 stroke-[1.5]" />
                    <span class="text-[10px]">{{ t('submitReport.noPhotoYet') }}</span>
                  </div>
                </div>

                <!-- Reporter preview footer -->
                <div class="mt-3 flex items-center justify-between border-t border-border/50 pt-2 text-[10px] text-muted-foreground">
                  <span>{{ authStore.user?.full_name || 'Resident Reporter' }}</span>
                  <span>Just now</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- 2. Civic Reporting Best Practices -->
          <Card class="border-border/60 shadow-sm">
            <CardHeader class="pb-3">
              <div class="flex items-center gap-2">
                <HelpCircle class="h-4 w-4 text-primary" />
                <CardTitle class="text-sm font-semibold">
                  {{ t('submitReport.tipsHeading') }}
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent class="space-y-3.5 text-xs">
              <div class="flex items-start gap-2.5">
                <div class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  📸
                </div>
                <div>
                  <p class="font-medium text-foreground">{{ t('submitReport.tipPhotoTitle') }}</p>
                  <p class="mt-0.5 leading-relaxed text-muted-foreground">{{ t('submitReport.tipPhotoText') }}</p>
                </div>
              </div>

              <div class="flex items-start gap-2.5">
                <div class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  📍
                </div>
                <div>
                  <p class="font-medium text-foreground">{{ t('submitReport.tipLocationTitle') }}</p>
                  <p class="mt-0.5 leading-relaxed text-muted-foreground">{{ t('submitReport.tipLocationText') }}</p>
                </div>
              </div>

              <div class="flex items-start gap-2.5">
                <div class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-rose-500/10 text-rose-600">
                  ⚠️
                </div>
                <div>
                  <p class="font-medium text-foreground">{{ t('submitReport.tipSafetyTitle') }}</p>
                  <p class="mt-0.5 leading-relaxed text-muted-foreground">{{ t('submitReport.tipSafetyText') }}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- 3. What Happens Next Timeline -->
          <Card class="border-border/60 shadow-sm">
            <CardHeader class="pb-3">
              <CardTitle class="text-sm font-semibold">
                {{ t('submitReport.processHeading') }}
              </CardTitle>
            </CardHeader>
            <CardContent class="text-xs text-muted-foreground">
              <ol class="space-y-2.5">
                <li class="flex items-center gap-2">
                  <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted font-mono text-[10px] font-semibold text-foreground">
                    1
                  </span>
                  <span>{{ t('submitReport.processStep1') }}</span>
                </li>
                <li class="flex items-center gap-2">
                  <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted font-mono text-[10px] font-semibold text-foreground">
                    2
                  </span>
                  <span>{{ t('submitReport.processStep2') }}</span>
                </li>
                <li class="flex items-center gap-2">
                  <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted font-mono text-[10px] font-semibold text-foreground">
                    3
                  </span>
                  <span>{{ t('submitReport.processStep3') }}</span>
                </li>
              </ol>
            </CardContent>
          </Card>
        </div>
      </div>

      <!-- Photo Zoom Lightbox Dialog -->
      <Dialog v-model:open="zoomModalOpen">
        <DialogContent class="max-w-3xl">
          <DialogHeader>
            <DialogTitle class="text-sm font-semibold">{{ photoName || 'Photo Preview' }}</DialogTitle>
            <DialogDescription class="text-xs">{{ photoSize }}</DialogDescription>
          </DialogHeader>
          <div v-if="photoPreview" class="flex max-h-[70vh] items-center justify-center overflow-hidden rounded-lg bg-muted/20 p-2">
            <img :src="photoPreview" :alt="photoName || 'Evidence'" class="max-h-[65vh] w-auto object-contain" />
          </div>
        </DialogContent>
      </Dialog>
      <!-- Map Location Picker Dialog -->
      <MapLocationPicker
        v-model:open="mapPickerOpen"
        :initial-lat="latitude"
        :initial-lng="longitude"
        @select-location="handleMapLocationSelect"
      />
    </div>
  </AppLayout>
</template>