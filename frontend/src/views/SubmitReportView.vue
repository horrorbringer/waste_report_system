<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { AlertCircle, ArrowLeft, Camera, CheckCircle2, Circle, ClipboardList, ImagePlus, Loader2, Lock, MapPin, Navigation, Upload, X } from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import MapLocationPicker from '@/components/MapLocationPicker.vue'
import { useCategoryStore } from '@/stores/categories'
import { useReportStore } from '@/stores/reports'
import { localizedCategory } from '@/i18n'
import { suggestReportArea } from '@/lib/cambodiaAreas'
import type { ReportUploadPolicy } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const categoryStore = useCategoryStore()
const reportStore = useReportStore()

const title = ref('')
const categoryId = ref('')
const description = ref('')
const locationText = ref('')
const latitude = ref<string | number>('')
const longitude = ref<string | number>('')
const mapDistrict = ref<number | null>(null)
const gpsAccuracy = ref<number | null>(null)
const locating = ref(false)
const locationError = ref('')
const mapPickerOpen = ref(false)
const coordinateFields = ref<HTMLDetailsElement | null>(null)

const uploadPolicy = ref<ReportUploadPolicy | null>(null)
const browseInput = ref<HTMLInputElement | null>(null)
const cameraInput = ref<HTMLInputElement | null>(null)
type Attachment = { file: File; preview: string }
const photos = ref<Attachment[]>([])
const previewPhoto = ref<Attachment | null>(null)
const photoError = ref('')
const photoDialogOpen = ref(false)
const dragDepth = ref(0)

const attempted = ref(false)
const submitting = ref(false)
const error = ref('')
const defaultExtensions = ['png', 'jpg', 'jpeg', 'webp', 'avif']
const bytesPerMb = 1024 * 1024
const quickTitles = ['quickTitle1', 'quickTitle2', 'quickTitle3', 'quickTitle4']

const selectedCategory = computed(() => categoryStore.categories.find((category) => String(category.id) === categoryId.value))
const selectedCategoryDescription = computed(() => {
  const category = selectedCategory.value
  return locale.value === 'km' && category?.description_km ? category.description_km : category?.description
})
const extensions = computed(() => uploadPolicy.value?.allowed_extensions ?? defaultExtensions)
const acceptPhoto = computed(() => extensions.value.map((ext) => '.' + ext).join(','))
const formatLabels = computed(() => [...new Set(extensions.value.map((ext) => ext === 'jpeg' ? 'JPG' : ext.toUpperCase()))].join(', '))
const maxPhotoSize = computed(() => uploadPolicy.value?.max_file_size_mb)
const maxPhotos = computed(() => uploadPolicy.value?.max_photos ?? 5)
const maxTotalPhotoSize = computed(() => uploadPolicy.value?.max_total_size_mb)
const photoBytes = computed(() => photos.value.reduce((total, photo) => total + photo.file.size, 0))
const photoHint = computed(() => maxPhotoSize.value
  ? t('submitReport.photoHint', { formats: formatLabels.value, size: maxPhotoSize.value })
  : t('submitReport.photoFormats', { formats: formatLabels.value }),
)

const coordinates = computed(() => ({
  lat: String(latitude.value).trim(),
  lng: String(longitude.value).trim(),
}))
const districtSuggestion = computed(() => {
  const areas = reportStore.reportAreas
  const { province, district } = suggestReportArea(locationText.value, mapDistrict.value, areas)
  return areas.find(({ code }) => code === province)?.districts.find(({ code }) => code === district)
})

const fieldErrors = computed(() => ({
  category: selectedCategory.value ? '' : t('submitReport.errNoCategory'),
  title: title.value.trim().length >= 3 ? '' : t('submitReport.errTitleLength'),
  description: description.value.trim().length >= 10 ? '' : t('submitReport.minCharsNote'),
  location: locationText.value.trim().length >= 3 ? '' : t('submitReport.errLocationLength'),
  lat: coordinates.value.lat && Math.abs(Number(coordinates.value.lat)) > 90 ? t('submitReport.errLatitude') : '',
  lng: coordinates.value.lng && Math.abs(Number(coordinates.value.lng)) > 180 ? t('submitReport.errLongitude') : '',
}))

const checklist = computed(() => [
  { label: 'submitReport.detailsSection', complete: !fieldErrors.value.category && !fieldErrors.value.title && !fieldErrors.value.description },
  { label: 'submitReport.locationSection', complete: !fieldErrors.value.location && !fieldErrors.value.lat && !fieldErrors.value.lng },
])

onMounted(() => {
  window.addEventListener('paste', handlePaste)
  reportStore.fetchReportAreas().catch(() => {})
  categoryStore.fetchCategories().then(() => {
    const requestedCategory = route.query.category
    if (!categoryId.value && typeof requestedCategory === 'string' &&
        categoryStore.categories.some((category) => String(category.id) === requestedCategory)) {
      categoryId.value = requestedCategory
    }
  }).catch(() => {
    error.value = t('submitReport.errCategories')
  })
  reportStore.fetchUploadPolicy().then((policy) => {
    uploadPolicy.value = policy
    if (photos.value.length) photoError.value = validatePhotos(photos.value.map(({ file }) => file))
  }).catch(() => {})
})

onUnmounted(() => {
  window.removeEventListener('paste', handlePaste)
  photos.value.forEach(({ preview }) => URL.revokeObjectURL(preview))
})

function validatePhoto(file: File) {
  const extension = file.name.includes('.') ? file.name.split('.').pop()?.toLowerCase() : undefined
  if (!extension || !extensions.value.includes(extension)) {
    return t('submitReport.errPhotoFormatNamed', { name: file.name, formats: formatLabels.value })
  }
  if (!file.size) return t('submitReport.errPhotoEmpty', { name: file.name })
  if (maxPhotoSize.value && file.size > maxPhotoSize.value * bytesPerMb) {
    return t('submitReport.errPhotoSizeNamed', { name: file.name, size: maxPhotoSize.value })
  }
  return ''
}

function validatePhotos(files: File[]) {
  if (files.length > maxPhotos.value) return t('submitReport.errPhotoCount', { count: maxPhotos.value })
  for (const file of files) {
    const problem = validatePhoto(file)
    if (problem) return problem
  }
  if (maxTotalPhotoSize.value && files.reduce((total, file) => total + file.size, 0) > maxTotalPhotoSize.value * bytesPerMb) {
    return t('submitReport.errPhotoTotal', { size: maxTotalPhotoSize.value })
  }
  return ''
}

function attachPhotos(files: File[]) {
  if (!files.length || submitting.value) return
  photoError.value = validatePhotos([...photos.value.map(({ file }) => file), ...files])
  if (photoError.value) return

  photos.value.push(...files.map((file) => ({ file, preview: URL.createObjectURL(file) })))
}

function removePhoto(photo: Attachment) {
  photos.value = photos.value.filter(({ preview }) => preview !== photo.preview)
  URL.revokeObjectURL(photo.preview)
  photoError.value = validatePhotos(photos.value.map(({ file }) => file))
}

function openPhotoPreview(photo: Attachment) {
  previewPhoto.value = photo
  photoDialogOpen.value = true
}

function formatPhotoSize(size: number) {
  if (size >= bytesPerMb) return (size / bytesPerMb).toFixed(1) + ' MB'
  return Math.max(1, Math.round(size / 1024)) + ' KB'
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  attachPhotos(Array.from(input.files ?? []))
  input.value = ''
}

function handleDrop(event: DragEvent) {
  dragDepth.value = 0
  attachPhotos(Array.from(event.dataTransfer?.files ?? []))
}

function handleDragEnter(event: DragEvent) {
  if (event.dataTransfer?.types.includes('Files')) dragDepth.value++
}

function handlePaste(event: ClipboardEvent) {
  const files = Array.from(event.clipboardData?.items ?? [])
    .filter((item) => item.type.startsWith('image/'))
    .map((item) => item.getAsFile())
    .filter((file): file is File => file !== null)
  attachPhotos(files)
}

function detectLocation() {
  locationError.value = ''
  if (!navigator.geolocation) {
    locationError.value = t('submitReport.errGeoUnsupported')
    return
  }

  locating.value = true
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      latitude.value = coords.latitude.toFixed(6)
      longitude.value = coords.longitude.toFixed(6)
      mapDistrict.value = null
      gpsAccuracy.value = Math.round(coords.accuracy)
      locating.value = false
    },
    () => {
      locationError.value = t('submitReport.errGeoFailed')
      locating.value = false
    },
    { enableHighAccuracy: true, timeout: 8000 },
  )
}

function selectMapLocation({ lat, lng, address, district }: { lat: number; lng: number; address?: string; district: number | null }) {
  latitude.value = lat
  longitude.value = lng
  mapDistrict.value = district
  gpsAccuracy.value = null
  locationError.value = ''
  if (address && locationText.value.trim().length < 5) locationText.value = address.slice(0, 300)
}

function clearCoordinates() {
  latitude.value = ''
  longitude.value = ''
  clearCoordinateMetadata()
  locationError.value = ''
}

function clearCoordinateMetadata() {
  gpsAccuracy.value = null
  mapDistrict.value = null
}

async function handleSubmit() {
  if (submitting.value) return

  attempted.value = true
  error.value = ''
  const firstInvalidField = Object.entries(fieldErrors.value).find(([, message]) => message)?.[0]
  if (firstInvalidField) {
    if (coordinateFields.value && (firstInvalidField === 'lat' || firstInvalidField === 'lng')) {
      coordinateFields.value.open = true
    }
    await nextTick()
    document.getElementById(firstInvalidField)?.focus()
    return
  }

  const formData = new FormData()
  formData.append('category_id', categoryId.value)
  formData.append('title', title.value.trim())
  formData.append('description', description.value.trim())
  formData.append('location_text', locationText.value.trim())
  if (coordinates.value.lat) formData.append('latitude', coordinates.value.lat)
  if (coordinates.value.lng) formData.append('longitude', coordinates.value.lng)
  if (mapDistrict.value) formData.append('location_district', String(mapDistrict.value))
  photoError.value = validatePhotos(photos.value.map(({ file }) => file))
  if (photoError.value) {
    document.getElementById('report-photo')?.focus()
    return
  }
  for (const { file } of photos.value) formData.append('photos', file)

  submitting.value = true
  try {
    const created = await reportStore.submitReport(formData)
    await router.replace({
      name: 'report-detail',
      params: { id: created.id },
      state: { submittedReportId: created.id },
    })
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (err.response?.status === 413) {
      photoError.value = t('submitReport.errUploadTooLarge')
      document.getElementById('report-photo')?.focus()
    } else if (err.response?.status === 400 && photos.value.length && typeof detail === 'string') {
      photoError.value = detail
      document.getElementById('report-photo')?.focus()
    } else {
      error.value = typeof detail === 'string' ? detail : t('submitReport.errSubmitFailed')
      await nextTick()
      document.getElementById('report-submit-error')?.focus()
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppLayout>
    <div class="container max-w-6xl space-y-5 py-6 sm:space-y-6 sm:py-9">
      <RouterLink :to="{ name: 'my-reports' }" class="inline-flex min-h-8 items-center gap-2 text-sm font-medium text-muted-foreground hover:text-primary">
        <ArrowLeft class="h-4 w-4" /> {{ t('nav.myReports') }}
      </RouterLink>
      <header class="flex items-start gap-4 rounded-2xl border border-primary/15 bg-accent/60 p-5 sm:p-7">
        <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground sm:h-12 sm:w-12">
          <ClipboardList class="h-5 w-5" />
        </div>
        <div class="min-w-0 space-y-1.5">
          <h1 class="heading-page text-2xl font-bold tracking-tight sm:text-3xl">{{ t('submitReport.title') }}</h1>
          <p class="max-w-xl text-sm leading-relaxed text-muted-foreground">{{ t('submitReport.formIntro') }}</p>
        </div>
      </header>

      <div class="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_17rem] lg:gap-6">
        <form novalidate class="min-w-0 space-y-5" :aria-busy="submitting" @submit.prevent="handleSubmit">
          <section aria-labelledby="report-details-title" class="space-y-5 rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
            <div class="flex items-start justify-between gap-3">
              <div class="flex min-w-0 items-center gap-2.5">
                <ClipboardList class="h-4 w-4 shrink-0 text-primary" />
                <h2 id="report-details-title" class="text-base font-semibold">{{ t('submitReport.detailsSection') }}</h2>
              </div>
              <p class="text-right text-xs text-muted-foreground">{{ t('submitReport.requiredFields') }}</p>
            </div>
            <div class="space-y-1.5">
              <Label for="category">{{ t('submitReport.fieldCategory') }}</Label>
              <select
                id="category"
                v-model="categoryId"
                required
                :aria-invalid="attempted && !!fieldErrors.category || undefined"
                :aria-describedby="attempted && fieldErrors.category ? 'category-error' : selectedCategoryDescription ? 'category-help' : undefined"
                class="block h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring aria-[invalid=true]:border-destructive"
              >
                <option value="" disabled>{{ t('submitReport.fieldCategoryPlaceholder') }}</option>
                <option v-for="category in categoryStore.categories" :key="category.id" :value="String(category.id)">
                  {{ localizedCategory(category.name, category.name_km, locale) }}
                </option>
              </select>
              <p v-if="attempted && fieldErrors.category" id="category-error" class="text-sm text-destructive">{{ fieldErrors.category }}</p>
              <p v-else-if="selectedCategoryDescription" id="category-help" class="text-sm text-muted-foreground">{{ selectedCategoryDescription }}</p>
            </div>

            <div class="space-y-1.5">
              <Label for="title">{{ t('submitReport.fieldTitle') }}</Label>
              <Input id="title" v-model="title" required maxlength="200" class="h-10 aria-[invalid=true]:border-destructive"
                :placeholder="t('submitReport.fieldTitlePlaceholder')"
                :aria-invalid="attempted && !!fieldErrors.title || undefined"
                :aria-describedby="attempted && fieldErrors.title ? 'title-error' : undefined" />
              <p v-if="attempted && fieldErrors.title" id="title-error" class="text-sm text-destructive">{{ fieldErrors.title }}</p>
              <details class="text-sm">
                <summary class="w-fit cursor-pointer rounded-sm py-1 text-muted-foreground">{{ t('submitReport.quickTitlesLabel') }}</summary>
                <div class="mt-1 flex flex-wrap gap-2">
                  <Button v-for="key in quickTitles" :key="key" type="button" variant="outline" size="sm" class="h-auto whitespace-normal text-start" @click="title = t('submitReport.' + key)">
                    {{ t('submitReport.' + key) }}
                  </Button>
                </div>
              </details>
            </div>

            <div class="space-y-1.5">
              <Label for="description">{{ t('submitReport.fieldDesc') }}</Label>
              <Textarea id="description" v-model="description" required maxlength="2000" rows="4"
                class="aria-[invalid=true]:border-destructive"
                :placeholder="t('submitReport.fieldDescPlaceholder')"
                :aria-invalid="attempted && !!fieldErrors.description || undefined"
                :aria-describedby="attempted && fieldErrors.description ? 'description-error' : undefined" />
              <p v-if="attempted && fieldErrors.description" id="description-error" class="text-sm text-destructive">{{ fieldErrors.description }}</p>
            </div>
          </section>

          <section aria-labelledby="report-location-title" class="space-y-3 rounded-2xl border bg-card p-4 shadow-sm sm:space-y-4 sm:p-6">
            <div class="flex items-center gap-2.5">
              <MapPin class="h-4 w-4 shrink-0 text-primary" />
              <h2 id="report-location-title" class="text-base font-semibold">{{ t('submitReport.locationSection') }}</h2>
            </div>
            <div class="space-y-1.5">
              <Label for="location">{{ t('submitReport.fieldLocation') }}</Label>
              <Input id="location" v-model="locationText" required maxlength="300" class="h-10 aria-[invalid=true]:border-destructive"
                :placeholder="t('submitReport.fieldLocationPlaceholder')"
                :aria-invalid="attempted && !!fieldErrors.location || undefined"
                :aria-describedby="attempted && fieldErrors.location ? 'location-error location-help' : 'location-help'" />
              <p v-if="attempted && fieldErrors.location" id="location-error" class="text-sm text-destructive">{{ fieldErrors.location }}</p>
              <p id="location-help" class="text-sm text-muted-foreground">{{ t('submitReport.locationHint') }}</p>
              <p v-if="districtSuggestion" class="text-sm text-muted-foreground">
                {{ t('community.detectedDistrict', { district: locale === 'km' ? districtSuggestion.name_km : districtSuggestion.name }) }}
              </p>
            </div>

            <div class="flex flex-wrap gap-2">
              <Button type="button" variant="outline" class="min-h-10 gap-2" @click="mapPickerOpen = true">
                <MapPin class="h-4 w-4" />
                {{ t('submitReport.pickOnMap') }}
              </Button>
              <Button type="button" variant="outline" class="min-h-10 gap-2" :disabled="locating" @click="detectLocation">
                <Loader2 v-if="locating" class="h-4 w-4 animate-spin" />
                <Navigation v-else class="h-4 w-4" />
                {{ locating ? t('submitReport.locating') : t('submitReport.useGps') }}
              </Button>
            </div>
            <p v-if="locationError" role="alert" class="text-sm text-destructive">{{ locationError }}</p>
            <div v-if="coordinates.lat && coordinates.lng" class="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
              <span class="text-primary">{{ t('submitReport.gpsSuccess') }}</span>
              <span v-if="gpsAccuracy !== null" class="text-muted-foreground">{{ t('submitReport.gpsAccuracy', { meters: gpsAccuracy }) }}</span>
              <a :href="'https://www.google.com/maps?q=' + coordinates.lat + ',' + coordinates.lng" target="_blank" rel="noopener noreferrer" class="underline">
                {{ t('submitReport.viewMaps') }}
              </a>
              <button type="button" class="text-muted-foreground underline" @click="clearCoordinates">{{ t('submitReport.clearGps') }}</button>
            </div>

            <details ref="coordinateFields" class="text-sm">
              <summary class="w-fit cursor-pointer rounded-sm py-1 text-muted-foreground">{{ t('submitReport.manualCoordinates') }}</summary>
              <div class="mt-2 grid grid-cols-2 gap-3">
                <div class="space-y-1.5">
                  <Label for="lat">{{ t('submitReport.latitude') }}</Label>
                  <Input id="lat" v-model="latitude" type="number" step="any" @input="clearCoordinateMetadata"
                    :aria-invalid="attempted && !!fieldErrors.lat || undefined"
                    :aria-describedby="attempted && fieldErrors.lat ? 'lat-error' : undefined" />
                  <p v-if="attempted && fieldErrors.lat" id="lat-error" class="text-sm text-destructive">{{ fieldErrors.lat }}</p>
                </div>
                <div class="space-y-1.5">
                  <Label for="lng">{{ t('submitReport.longitude') }}</Label>
                  <Input id="lng" v-model="longitude" type="number" step="any" @input="clearCoordinateMetadata"
                    :aria-invalid="attempted && !!fieldErrors.lng || undefined"
                    :aria-describedby="attempted && fieldErrors.lng ? 'lng-error' : undefined" />
                  <p v-if="attempted && fieldErrors.lng" id="lng-error" class="text-sm text-destructive">{{ fieldErrors.lng }}</p>
                </div>
              </div>
            </details>
          </section>

          <section id="report-photo" tabindex="-1" aria-labelledby="report-photo-title" class="space-y-4 rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
            <div class="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
              <div class="flex items-center gap-2.5">
                <Camera class="h-4 w-4 shrink-0 text-primary" />
                <h2 id="report-photo-title" class="text-base font-semibold">{{ t('submitReport.photosSection') }}</h2>
              </div>
              <p class="text-xs font-medium tabular-nums text-muted-foreground" aria-live="polite">
                {{ t('submitReport.photoCount', { count: photos.length, max: maxPhotos }) }}
              </p>
            </div>

            <div
              class="flex flex-col items-center gap-2 rounded-xl border border-dashed px-4 py-5 text-center transition-colors sm:py-7"
              :class="dragDepth > 0 ? 'border-primary bg-primary/10' : 'border-primary/35 bg-accent/35'"
              @dragenter.prevent="handleDragEnter"
              @dragover.prevent
              @dragleave.prevent="dragDepth = Math.max(0, dragDepth - 1)"
              @drop.prevent="handleDrop"
            >
              <span class="flex h-10 w-10 items-center justify-center rounded-lg border border-primary/15 bg-background text-primary">
                <ImagePlus class="h-5 w-5" />
              </span>
              <p class="text-sm font-semibold">{{ t('submitReport.photoDropTitle') }}</p>
              <div class="space-y-0.5 text-xs leading-relaxed text-muted-foreground">
                <p>{{ photoHint }}</p>
                <p v-if="maxTotalPhotoSize">{{ t('submitReport.photoTotalHint', { size: maxTotalPhotoSize }) }}</p>
              </div>
              <div class="mt-1 flex flex-wrap justify-center gap-2">
                <Button type="button" variant="outline" class="min-h-10 gap-2 bg-background" :disabled="submitting || photos.length >= maxPhotos" @click="browseInput?.click()">
                  <Upload class="h-4 w-4" /> {{ t('submitReport.browseFiles') }}
                </Button>
                <Button type="button" variant="outline" class="min-h-10 gap-2 bg-background sm:hidden" :disabled="submitting || photos.length >= maxPhotos" @click="cameraInput?.click()">
                  <Camera class="h-4 w-4" /> {{ t('submitReport.takePhoto') }}
                </Button>
                <input ref="browseInput" type="file" :accept="acceptPhoto" multiple hidden @change="handleFileChange" />
                <input ref="cameraInput" type="file" accept="image/*" capture="environment" hidden @change="handleFileChange" />
              </div>
            </div>

            <p v-if="photoError" role="alert" class="text-sm text-destructive">{{ photoError }}</p>
            <ul v-if="photos.length" class="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <li v-for="(photo, index) in photos" :key="photo.preview" class="relative min-w-0 overflow-hidden rounded-xl border bg-muted/25">
                <button type="button" class="block aspect-[4/3] w-full overflow-hidden bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary" :aria-label="t('submitReport.previewNamed', { name: photo.file.name })" @click="openPhotoPreview(photo)">
                  <img :src="photo.preview" alt="" class="h-full w-full object-cover" />
                </button>
                <span v-if="index === 0" class="pointer-events-none absolute left-2 top-2 rounded bg-background px-1.5 py-0.5 text-[11px] font-medium text-foreground shadow-sm">
                  {{ t('submitReport.coverPhoto') }}
                </span>
                <Button type="button" variant="outline" class="absolute right-1.5 top-1.5 h-8 w-8 bg-background p-0" :disabled="submitting" :aria-label="t('submitReport.removeNamed', { name: photo.file.name })" @click="removePhoto(photo)">
                  <X class="h-4 w-4" />
                </Button>
                <div class="flex min-w-0 flex-wrap justify-between gap-x-2 gap-y-0.5 px-2.5 py-2 text-xs">
                  <span class="min-w-0 truncate font-medium" :title="photo.file.name">{{ photo.file.name }}</span>
                  <span class="shrink-0 text-muted-foreground">{{ formatPhotoSize(photo.file.size) }}</span>
                </div>
              </li>
            </ul>
            <p class="text-xs leading-relaxed text-muted-foreground">
              {{ photos.length ? t('submitReport.photoTotalSelected', { size: formatPhotoSize(photoBytes) }) : t('submitReport.photoSafetyHint') }}
            </p>
          </section>

          <div class="space-y-3 rounded-2xl border bg-card p-4 sm:p-5">
            <Alert v-if="error" id="report-submit-error" tabindex="-1" variant="destructive">
              <AlertCircle class="h-4 w-4" />
              <AlertDescription>{{ error }}</AlertDescription>
            </Alert>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-end">
              <Button as-child variant="ghost" class="min-h-11">
                <RouterLink :to="{ name: 'my-reports' }">{{ t('common.cancel') }}</RouterLink>
              </Button>
              <Button type="submit" :disabled="submitting" class="min-h-11 gap-2">
                <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
                {{ t(submitting ? 'submitReport.submitting' : 'submitReport.submitBtn') }}
              </Button>
            </div>
          </div>
        </form>

        <aside class="hidden lg:sticky lg:top-24 lg:block">
          <div class="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
            <h2 class="text-sm font-semibold">{{ t('submitReport.checklistTitle') }}</h2>
            <ul class="space-y-3 text-sm">
              <li v-for="item in checklist" :key="item.label" class="flex items-center gap-2.5">
                <CheckCircle2 v-if="item.complete" class="h-4 w-4 shrink-0 text-primary" />
                <Circle v-else class="h-4 w-4 shrink-0 text-muted-foreground" />
                <span :class="item.complete ? 'text-foreground' : 'text-muted-foreground'">{{ t(item.label) }}</span>
                <span class="sr-only">{{ t(item.complete ? 'submitReport.sectionComplete' : 'submitReport.sectionIncomplete') }}</span>
              </li>
            </ul>
            <p class="flex items-start gap-2 border-t pt-4 text-xs leading-relaxed text-muted-foreground">
              <Lock class="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" /> {{ t('submitReport.privacyHint') }}
            </p>
          </div>
        </aside>
      </div>

      <Dialog v-model:open="photoDialogOpen">
        <DialogContent class="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{{ t('submitReport.photoPreview') }}</DialogTitle>
            <DialogDescription>{{ previewPhoto?.file.name }}</DialogDescription>
          </DialogHeader>
          <img v-if="previewPhoto" :src="previewPhoto.preview" :alt="previewPhoto.file.name" class="max-h-[65vh] w-full rounded-lg object-contain" />
        </DialogContent>
      </Dialog>

      <MapLocationPicker
        v-model:open="mapPickerOpen"
        :report-areas="reportStore.reportAreas"
        :initial-lat="latitude"
        :initial-lng="longitude"
        @select-location="selectMapLocation"
      />
    </div>
  </AppLayout>
</template>
