<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { AlertCircle, Camera, Loader2, MapPin, Navigation, Upload, X } from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import MapLocationPicker from '@/components/MapLocationPicker.vue'
import { useCategoryStore } from '@/stores/categories'
import { useReportStore } from '@/stores/reports'
import { localizedCategory } from '@/i18n'
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
const gpsAccuracy = ref<number | null>(null)
const locating = ref(false)
const locationError = ref('')
const mapPickerOpen = ref(false)
const coordinateFields = ref<HTMLDetailsElement | null>(null)

const uploadPolicy = ref<ReportUploadPolicy | null>(null)
const browseInput = ref<HTMLInputElement | null>(null)
const cameraInput = ref<HTMLInputElement | null>(null)
const photoFile = ref<File | null>(null)
const photoPreview = ref('')
const photoError = ref('')
const photoDialogOpen = ref(false)

const attempted = ref(false)
const submitting = ref(false)
const error = ref('')
const defaultExtensions = ['png', 'jpg', 'jpeg', 'webp']
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
const photoHint = computed(() => maxPhotoSize.value
  ? t('submitReport.photoHint', { formats: formatLabels.value, size: maxPhotoSize.value })
  : t('submitReport.photoFormats', { formats: formatLabels.value }),
)

const coordinates = computed(() => ({
  lat: String(latitude.value).trim(),
  lng: String(longitude.value).trim(),
}))

const fieldErrors = computed(() => ({
  category: selectedCategory.value ? '' : t('submitReport.errNoCategory'),
  title: title.value.trim().length >= 3 ? '' : t('submitReport.errTitleLength'),
  description: description.value.trim().length >= 10 ? '' : t('submitReport.minCharsNote'),
  location: locationText.value.trim().length >= 3 ? '' : t('submitReport.errLocationLength'),
  lat: coordinates.value.lat && Math.abs(Number(coordinates.value.lat)) > 90 ? t('submitReport.errLatitude') : '',
  lng: coordinates.value.lng && Math.abs(Number(coordinates.value.lng)) > 180 ? t('submitReport.errLongitude') : '',
}))

onMounted(() => {
  window.addEventListener('paste', handlePaste)
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
    if (photoFile.value) photoError.value = validatePhoto(photoFile.value)
  }).catch(() => {})
})

onUnmounted(() => {
  window.removeEventListener('paste', handlePaste)
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
})

function validatePhoto(file: File) {
  const extension = file.name.includes('.') ? file.name.split('.').pop()?.toLowerCase() : undefined
  if (!extension || !extensions.value.includes(extension)) {
    return t('submitReport.errInvalidFile', { formats: formatLabels.value })
  }
  if (maxPhotoSize.value && file.size > maxPhotoSize.value * 1024 * 1024) {
    return t('submitReport.errFileSize', { size: maxPhotoSize.value })
  }
  return ''
}

function attachPhoto(file: File) {
  photoError.value = validatePhoto(file)
  if (photoError.value) return

  clearPhoto()
  photoFile.value = file
  photoPreview.value = URL.createObjectURL(file)
}

function clearPhoto() {
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  photoFile.value = null
  photoPreview.value = ''
  photoError.value = ''
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) attachPhoto(file)
  input.value = ''
}

function handleDrop(event: DragEvent) {
  const file = event.dataTransfer?.files[0]
  if (file) attachPhoto(file)
}

function handlePaste(event: ClipboardEvent) {
  const image = Array.from(event.clipboardData?.items ?? []).find((item) => item.type.startsWith('image/'))
  const file = image?.getAsFile()
  if (file) attachPhoto(file)
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

function selectMapLocation({ lat, lng, address }: { lat: number; lng: number; address?: string }) {
  latitude.value = lat
  longitude.value = lng
  gpsAccuracy.value = null
  locationError.value = ''
  if (address && locationText.value.trim().length < 5) locationText.value = address.slice(0, 300)
}

function clearCoordinates() {
  latitude.value = ''
  longitude.value = ''
  gpsAccuracy.value = null
  locationError.value = ''
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
  if (photoFile.value) {
    photoError.value = validatePhoto(photoFile.value)
    if (photoError.value) {
      document.getElementById('report-photo')?.focus()
      return
    }
    formData.append('photo', photoFile.value)
  }

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
    if (err.response?.status === 400 && photoFile.value && typeof detail === 'string') {
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
    <div class="container max-w-2xl space-y-6 py-7 sm:py-10">
      <header class="space-y-2">
        <h1 class="heading-page text-3xl font-bold tracking-tight">{{ t('submitReport.title') }}</h1>
        <p class="text-sm text-muted-foreground">{{ t('submitReport.requiredFields') }}</p>
      </header>

      <form novalidate class="divide-y rounded-xl border bg-card" @submit.prevent="handleSubmit">
        <div class="space-y-5 p-4 sm:p-6">
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
        </div>

        <div class="space-y-3 p-4 sm:p-6">
          <div class="space-y-1.5">
            <Label for="location">{{ t('submitReport.fieldLocation') }}</Label>
            <Input id="location" v-model="locationText" required maxlength="300" class="h-10 aria-[invalid=true]:border-destructive"
              :placeholder="t('submitReport.fieldLocationPlaceholder')"
              :aria-invalid="attempted && !!fieldErrors.location || undefined"
              :aria-describedby="attempted && fieldErrors.location ? 'location-error location-help' : 'location-help'" />
            <p v-if="attempted && fieldErrors.location" id="location-error" class="text-sm text-destructive">{{ fieldErrors.location }}</p>
            <p id="location-help" class="text-sm text-muted-foreground">{{ t('submitReport.locationHint') }}</p>
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
                <Input id="lat" v-model="latitude" type="number" step="any" @input="gpsAccuracy = null"
                  :aria-invalid="attempted && !!fieldErrors.lat || undefined"
                  :aria-describedby="attempted && fieldErrors.lat ? 'lat-error' : undefined" />
                <p v-if="attempted && fieldErrors.lat" id="lat-error" class="text-sm text-destructive">{{ fieldErrors.lat }}</p>
              </div>
              <div class="space-y-1.5">
                <Label for="lng">{{ t('submitReport.longitude') }}</Label>
                <Input id="lng" v-model="longitude" type="number" step="any" @input="gpsAccuracy = null"
                  :aria-invalid="attempted && !!fieldErrors.lng || undefined"
                  :aria-describedby="attempted && fieldErrors.lng ? 'lng-error' : undefined" />
                <p v-if="attempted && fieldErrors.lng" id="lng-error" class="text-sm text-destructive">{{ fieldErrors.lng }}</p>
              </div>
            </div>
          </details>
        </div>

        <section id="report-photo" tabindex="-1" aria-labelledby="report-photo-title" class="space-y-3 p-4 sm:p-6" @dragover.prevent @drop.prevent="handleDrop">
          <div class="space-y-1">
            <h2 id="report-photo-title" class="text-sm font-medium">{{ t('submitReport.photoLabel') }}</h2>
            <p class="text-sm text-muted-foreground">{{ t('submitReport.photoSafetyHint') }} {{ photoHint }}</p>
          </div>
          <div v-if="photoFile" class="flex items-center gap-3 rounded-lg border p-2">
            <button type="button" class="shrink-0 rounded-md" :aria-label="t('submitReport.photoPreview')" @click="photoDialogOpen = true">
              <img :src="photoPreview" alt="" class="h-12 w-16 rounded-md object-cover" />
            </button>
            <p class="min-w-0 flex-1 truncate text-sm">{{ photoFile.name }}</p>
            <Button type="button" variant="ghost" size="sm" class="gap-1.5" @click="clearPhoto">
              <X class="h-4 w-4" />
              {{ t('submitReport.removePhoto') }}
            </Button>
          </div>
          <div class="flex flex-wrap gap-2">
            <Button type="button" variant="outline" class="min-h-10 gap-2" @click="browseInput?.click()">
              <Upload class="h-4 w-4" />
              {{ t(photoFile ? 'submitReport.replacePhoto' : 'submitReport.browseFiles') }}
            </Button>
            <Button type="button" variant="outline" class="min-h-10 gap-2 sm:hidden" @click="cameraInput?.click()">
              <Camera class="h-4 w-4" />
              {{ t('submitReport.takePhoto') }}
            </Button>
            <input ref="browseInput" type="file" :accept="acceptPhoto" hidden @change="handleFileChange" />
            <input ref="cameraInput" type="file" accept="image/*" capture="environment" hidden @change="handleFileChange" />
          </div>
          <p v-if="photoError" role="alert" class="text-sm text-destructive">{{ photoError }}</p>
        </section>

        <div class="space-y-3 p-4 sm:p-6">
          <Alert v-if="error" id="report-submit-error" tabindex="-1" variant="destructive">
            <AlertCircle class="h-4 w-4" />
            <AlertDescription>{{ error }}</AlertDescription>
          </Alert>
          <div class="flex flex-wrap items-center justify-end gap-2">
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

      <Dialog v-model:open="photoDialogOpen">
        <DialogContent class="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{{ t('submitReport.photoPreview') }}</DialogTitle>
            <DialogDescription>{{ photoFile?.name }}</DialogDescription>
          </DialogHeader>
          <img v-if="photoPreview" :src="photoPreview" :alt="photoFile?.name" class="max-h-[65vh] w-full rounded-lg object-contain" />
        </DialogContent>
      </Dialog>

      <MapLocationPicker
        v-model:open="mapPickerOpen"
        :initial-lat="latitude"
        :initial-lng="longitude"
        @select-location="selectMapLocation"
      />
    </div>
  </AppLayout>
</template>
