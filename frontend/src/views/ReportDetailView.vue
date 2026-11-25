<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  AlertCircle,
  ArrowLeft,
  Calendar,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Compass,
  Copy,
  Download,
  Edit3,
  ExternalLink,
  FileText,
  History,
  ImageIcon,
  Info,
  Loader2,
  MapPin,
  Maximize2,
  Navigation,
  Share2,
  ShieldAlert,
  Sparkles,
  Tag,
  User as UserIcon,
} from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import ReportPublicationDialog from '@/components/ReportPublicationDialog.vue'
import ReportMiniMap from '@/components/ReportMiniMap.vue'
import { useAuthStore } from '@/stores/auth'
import { useReportStore } from '@/stores/reports'
import { formatDate, resolvePhotoUrl } from '@/lib/utils'
import { localizedCategory, translateRole, translateStatus } from '@/i18n'
import type { ReportStatus } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
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
import { Skeleton } from '@/components/ui/skeleton'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const reportStore = useReportStore()

const error = ref('')
const statusDialogOpen = ref(false)
const nextStatus = ref<ReportStatus>('In Progress')
const statusNote = ref('')
const savingStatus = ref(false)
const statusSuccess = ref('')
const zoomModalOpen = ref(false)
const activePhotoIndex = ref(0)
const copied = ref(false)
const coordsCopied = ref(false)

const notePresets = [
  'presetNote1',
  'presetNote2',
  'presetNote3',
]

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    const detail = await reportStore.fetchReportDetail(id)
    nextStatus.value = detail.status
  } catch (err: any) {
    if (err.response?.status === 403) {
      router.replace('/403')
    } else {
      error.value = err.response?.data?.detail || t('detail.errNotFound')
    }
  }
})

const report = computed(() => {
  const current = reportStore.currentReport
  return current?.id === Number(route.params.id) ? current : null
})

const photoPaths = computed(() => {
  if (report.value?.photo_paths?.length) return report.value.photo_paths
  return report.value?.photo_path ? [report.value.photo_path] : []
})
const selectedPhotoUrl = computed(() => resolvePhotoUrl(photoPaths.value[activePhotoIndex.value]))
const selectedPhotoAlt = computed(() => t('detail.galleryPhotoAlt', { title: report.value?.title, index: activePhotoIndex.value + 1 }))

const hasGps = computed(() => {
  return report.value?.latitude !== null && report.value?.longitude !== null
})

const mapsUrl = computed(() => {
  if (!hasGps.value || !report.value) return ''
  return `https://www.google.com/maps?q=${report.value.latitude},${report.value.longitude}`
})

const directionsUrl = computed(() => {
  if (!hasGps.value || !report.value) return ''
  return `https://www.google.com/maps/dir/?api=1&destination=${report.value.latitude},${report.value.longitude}`
})

const isMyReport = computed(() => {
  return auth.user && report.value && auth.user.id === report.value.user_id
})

const justSubmitted = computed(() => Boolean(
  report.value && isMyReport.value && window.history.state?.submittedReportId === report.value.id,
))

const currentStepIndex = computed(() => {
  if (!report.value) return 0
  if (report.value.status === 'Resolved') return 2
  if (report.value.status === 'In Progress') return 1
  return 0
})

function copyReportLink() {
  navigator.clipboard.writeText(window.location.href)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2500)
}

function copyCoordinates() {
  if (!hasGps.value || !report.value) return
  navigator.clipboard.writeText(`${report.value.latitude}, ${report.value.longitude}`)
  coordsCopied.value = true
  setTimeout(() => {
    coordsCopied.value = false
  }, 2000)
}

function openStatusDialog() {
  if (!report.value) return
  nextStatus.value = report.value.status
  statusNote.value = ''
  statusDialogOpen.value = true
}

function applyPresetNote(presetKey: string) {
  statusNote.value = t(`detail.${presetKey}`)
}

async function handleStatusSave() {
  if (!report.value) return
  savingStatus.value = true
  statusSuccess.value = ''
  try {
    await reportStore.updateReportStatus(
      report.value.id,
      nextStatus.value,
      statusNote.value
    )
    statusDialogOpen.value = false
    statusSuccess.value = t('detail.statusUpdatedMsg', {
      status: translateStatus(nextStatus.value, t),
    })
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('detail.errUpdateFailed')
  } finally {
    savingStatus.value = false
  }
}
</script>

<template>
  <AppLayout>
    <div class="container max-w-6xl py-8">
      <!-- Breadcrumb & Top Action Header -->
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" class="gap-1.5" @click="router.back()">
          <ArrowLeft class="h-4 w-4" />
          {{ t('common.back') }}
        </Button>

        <div class="flex flex-wrap items-center gap-2">
          <!-- Copy / Share Link Button -->
          <Button
            variant="outline"
            size="sm"
            class="h-8 gap-1.5 text-xs shadow-sm transition"
            @click="copyReportLink"
          >
            <Check v-if="copied" class="h-3.5 w-3.5 text-emerald-600 stroke-[3]" />
            <Share2 v-else class="h-3.5 w-3.5" />
            {{ copied ? t('detail.linkCopied') : t('detail.copyLink') }}
          </Button>

          <!-- Admin Quick Status Trigger -->
          <ReportPublicationDialog
            v-if="auth.isAdmin && report"
            :report-id="report.id"
            :location-text="report.location_text"
            :location-district="report.location_district"
            :published-district="report.public_district"
            :published-province="report.public_province"
          />

          <Button
            v-if="auth.isAdmin && report"
            size="sm"
            class="h-8 gap-1.5 shadow-sm font-medium"
            @click="openStatusDialog"
          >
            <Edit3 class="h-3.5 w-3.5" />
            {{ t('detail.updateStatus') }}
          </Button>
        </div>
      </div>

      <!-- Alerts -->
      <Alert v-if="error" variant="destructive" class="mb-6 shadow-sm">
        <AlertCircle class="h-4 w-4" />
        <AlertDescription>{{ error }}</AlertDescription>
      </Alert>

      <Alert v-if="statusSuccess" variant="success" class="mb-6 shadow-sm">
        <CheckCircle2 class="h-4 w-4" />
        <AlertDescription>{{ statusSuccess }}</AlertDescription>
      </Alert>

      <Alert v-if="justSubmitted && report" variant="success" role="status" class="mb-6">
        <CheckCircle2 class="h-4 w-4" />
        <AlertTitle>{{ t('submitReport.confirmationTitle') }}</AlertTitle>
        <AlertDescription>
          <p>{{ t('submitReport.confirmationReference', { id: report.id }) }}</p>
          <RouterLink :to="{ name: 'my-reports' }" class="mt-1 inline-flex font-medium underline">
            {{ t('home.ctaMyReports') }}
          </RouterLink>
        </AlertDescription>
      </Alert>

      <div
        v-else-if="report && report.status === 'Resolved'"
        class="mb-6 flex items-center gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs text-emerald-800 dark:text-emerald-200 shadow-sm"
      >
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 class="h-5 w-5" />
        </div>
        <p class="font-medium leading-relaxed">
          {{ t('detail.resolvedBanner') }}
        </p>
      </div>

      <div
        v-else-if="report && isMyReport"
        class="mb-6 flex items-center gap-3 rounded-xl border border-primary/20 bg-primary/5 p-3.5 text-xs text-muted-foreground shadow-sm"
      >
        <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Sparkles class="h-4 w-4" />
        </div>
        <p class="leading-relaxed">
          {{ t('detail.residentThankYou') }}
        </p>
      </div>

      <!-- Polished Realistic Loading Skeleton -->
      <div v-if="reportStore.loading && !report" class="space-y-6">
        <!-- Top Hero Skeleton -->
        <Card class="border-border/60 shadow-xs">
          <CardContent class="p-6 space-y-5">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div class="space-y-2">
                <div class="flex items-center gap-2">
                  <Skeleton class="h-5 w-12 rounded-md" />
                  <Skeleton class="h-5 w-28 rounded-md" />
                  <Skeleton class="h-5 w-20 rounded-md" />
                </div>
                <Skeleton class="h-7 w-72 sm:w-96 rounded-md" />
              </div>
              <Skeleton class="h-9 w-32 rounded-lg" />
            </div>
            <!-- Progress Stepper Skeleton -->
            <div class="pt-4 border-t space-y-3">
              <div class="grid grid-cols-3 gap-3">
                <div v-for="n in 3" :key="n" class="space-y-1.5">
                  <Skeleton class="h-4 w-20 rounded-md" />
                  <Skeleton class="h-3 w-32 rounded-md" />
                </div>
              </div>
              <Skeleton class="h-2 w-full rounded-full" />
            </div>
          </CardContent>
        </Card>

        <!-- 2-Column Content Skeleton -->
        <div class="grid gap-6 lg:grid-cols-12">
          <!-- Left Column (8 cols) -->
          <div class="space-y-6 lg:col-span-8">
            <!-- Map & Location Skeleton -->
            <Card class="border-border/60 shadow-xs">
              <CardHeader class="pb-3">
                <Skeleton class="h-5 w-40 rounded-md" />
              </CardHeader>
              <CardContent class="space-y-3">
                <Skeleton class="h-56 w-full rounded-xl" />
                <div class="space-y-2 pt-2">
                  <Skeleton class="h-4 w-3/4 rounded-md" />
                  <Skeleton class="h-3.5 w-1/2 rounded-md" />
                </div>
              </CardContent>
            </Card>

            <!-- Activity Log Skeleton -->
            <Card class="border-border/60 shadow-xs">
              <CardHeader class="pb-3">
                <Skeleton class="h-5 w-48 rounded-md" />
              </CardHeader>
              <CardContent class="space-y-4">
                <div v-for="n in 2" :key="n" class="flex gap-3">
                  <Skeleton class="h-8 w-8 rounded-full shrink-0" />
                  <div class="space-y-1.5 flex-1">
                    <Skeleton class="h-4 w-32 rounded-md" />
                    <Skeleton class="h-3.5 w-full rounded-md" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <!-- Right Column (4 cols) -->
          <div class="space-y-6 lg:col-span-4">
            <!-- Photo Skeleton -->
            <Card class="border-border/60 shadow-xs">
              <CardHeader class="pb-3">
                <Skeleton class="h-5 w-32 rounded-md" />
              </CardHeader>
              <CardContent>
                <Skeleton class="h-64 w-full rounded-xl" />
              </CardContent>
            </Card>

            <!-- Details Meta Skeleton -->
            <Card class="border-border/60 shadow-xs">
              <CardHeader class="pb-3">
                <Skeleton class="h-5 w-28 rounded-md" />
              </CardHeader>
              <CardContent class="space-y-3">
                <Skeleton class="h-4 w-full rounded-md" />
                <Skeleton class="h-4 w-3/4 rounded-md" />
                <Skeleton class="h-4 w-2/3 rounded-md" />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <!-- Main Report Details Grid -->
      <div v-else-if="report" class="space-y-6">
        <!-- HERO CARD: Title, Badges, Reporter & Progress Stepper -->
        <Card class="border-border/60 shadow-sm">
          <CardContent class="p-6">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div class="space-y-2">
                <!-- Badges Row -->
                <div class="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" class="font-mono text-xs tabular-nums text-muted-foreground">
                    #{{ report.id }}
                  </Badge>
                  <Badge variant="secondary" class="gap-1 font-medium">
                    <Tag class="h-3 w-3 text-primary" />
                    {{ localizedCategory(report.category_name, report.category_name_km, locale) }}
                  </Badge>
                  <StatusBadge :status="report.status" />
                </div>

                <!-- Report Title -->
                <h1 class="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                  {{ report.title }}
                </h1>

                <!-- Reporter & Date Meta -->
                <div class="flex flex-wrap items-center gap-x-5 gap-y-1 pt-1 text-xs text-muted-foreground">
                  <span class="inline-flex items-center gap-1.5 font-medium text-foreground">
                    <UserIcon class="h-3.5 w-3.5 text-muted-foreground" />
                    {{ report.reporter_name }}
                  </span>
                  <span class="inline-flex items-center gap-1.5 tabular-nums">
                    <Calendar class="h-3.5 w-3.5" />
                    {{ formatDate(report.created_at, locale) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Resolution Progress Stepper (Visual 3-Stage Track) -->
            <div class="mt-6 border-t border-border/60 pt-5">
              <div class="grid grid-cols-3 gap-2 text-center text-xs">
                <!-- Step 1: Submitted -->
                <div class="space-y-1.5">
                  <div
                    class="mx-auto flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold shadow-sm transition"
                    :class="[
                      currentStepIndex >= 0
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground',
                    ]"
                  >
                    <Check class="h-3.5 w-3.5 stroke-[3]" />
                  </div>
                  <p class="font-medium text-foreground">{{ t('detail.stepSubmitted') }}</p>
                  <p class="text-[11px] text-muted-foreground">{{ t('detail.stepLoggedSub') }}</p>
                </div>

                <!-- Step 2: In Progress -->
                <div class="space-y-1.5">
                  <div
                    class="mx-auto flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold shadow-sm transition"
                    :class="[
                      currentStepIndex >= 1
                        ? 'bg-blue-600 text-white'
                        : 'bg-muted text-muted-foreground',
                    ]"
                  >
                    <Loader2 v-if="currentStepIndex === 1" class="h-3.5 w-3.5 animate-spin" />
                    <Check v-else-if="currentStepIndex > 1" class="h-3.5 w-3.5 stroke-[3]" />
                    <span v-else>2</span>
                  </div>
                  <p class="font-medium text-foreground">{{ t('detail.stepUnderway') }}</p>
                  <p class="text-[11px] text-muted-foreground">{{ t('detail.stepUnderwaySub') }}</p>
                </div>

                <!-- Step 3: Resolved -->
                <div class="space-y-1.5">
                  <div
                    class="mx-auto flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold shadow-sm transition"
                    :class="[
                      currentStepIndex >= 2
                        ? 'bg-emerald-600 text-white'
                        : 'bg-muted text-muted-foreground',
                    ]"
                  >
                    <CheckCircle2 class="h-3.5 w-3.5" />
                  </div>
                  <p class="font-medium text-foreground">{{ t('detail.stepResolved') }}</p>
                  <p class="text-[11px] text-muted-foreground">{{ t('detail.stepResolvedSub') }}</p>
                </div>
              </div>

              <!-- Connecting Bar -->
              <div class="relative mx-8 mt-2 h-1 overflow-hidden rounded-full bg-muted">
                <div
                  class="h-full bg-primary transition-all duration-500"
                  :style="{
                    width: currentStepIndex === 2 ? '100%' : currentStepIndex === 1 ? '50%' : '15%',
                  }"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- 2-COLUMN BODY: Left (8 cols) Details & Evidence + Right (4 cols) Timeline -->
        <div class="grid gap-6 lg:grid-cols-12">
          <!-- Left Column (8 cols): Description, Photo, Location -->
          <div class="space-y-6 lg:col-span-8">
            <!-- 1. Description Card -->
            <Card class="border-border/60 shadow-sm">
              <CardHeader class="pb-2">
                <CardTitle class="text-base font-semibold">
                  {{ t('detail.description') }}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p class="whitespace-pre-line text-sm leading-relaxed text-foreground">
                  {{ report.description }}
                </p>
              </CardContent>
            </Card>

            <!-- 2. Attached Photo Evidence Card -->
            <Card class="border-border/60 shadow-sm">
              <CardHeader class="pb-2">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <CardTitle class="text-base font-semibold">
                    {{ t('detail.attachedPhotos') }}
                  </CardTitle>
                  <div v-if="selectedPhotoUrl" class="flex flex-wrap items-center gap-2">
                    <!-- Zoom Button -->
                    <Button
                      variant="outline"
                      size="sm"
                      class="h-7 gap-1 px-2.5 text-xs shadow-none"
                      @click="zoomModalOpen = true"
                    >
                      <Maximize2 class="h-3 w-3" />
                      {{ t('detail.viewFullscreen') }}
                    </Button>
                    <!-- Open in New Tab -->
                    <a
                      :href="selectedPhotoUrl"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="inline-flex h-7 items-center gap-1 rounded-md border bg-background px-2.5 text-xs font-medium text-primary shadow-none hover:underline"
                    >
                      <ExternalLink class="h-3 w-3" />
                      {{ t('common.openInNewTab') }}
                    </a>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <!-- Photo Container -->
                <div v-if="selectedPhotoUrl" class="space-y-3">
                  <button
                    type="button"
                    class="flex w-full cursor-zoom-in items-center justify-center overflow-hidden rounded-xl border bg-black/5 p-2 dark:bg-black/20"
                    :aria-label="t('detail.viewFullscreen')"
                    @click="zoomModalOpen = true"
                  >
                    <img :src="selectedPhotoUrl" :alt="selectedPhotoAlt" class="max-h-[480px] max-w-full rounded-lg object-contain" loading="lazy" />
                  </button>
                  <div v-if="photoPaths.length > 1" class="flex flex-wrap items-center gap-2" role="group" :aria-label="t('detail.attachedPhotos')">
                    <button
                      v-for="(path, index) in photoPaths"
                      :key="path"
                      type="button"
                      class="h-14 w-16 overflow-hidden rounded-lg border-2 bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring aria-pressed:border-primary"
                      :aria-label="t('detail.showGalleryPhoto', { index: index + 1 })"
                      :aria-pressed="index === activePhotoIndex"
                      @click="activePhotoIndex = index"
                    >
                      <img :src="resolvePhotoUrl(path)" alt="" class="h-full w-full object-cover" loading="lazy" />
                    </button>
                  </div>
                </div>

                <!-- Empty Photo State -->
                <div
                  v-else
                  class="flex flex-col items-center justify-center rounded-xl border border-dashed bg-muted/10 py-10 text-center"
                >
                  <div class="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-muted text-muted-foreground">
                    <ImageIcon class="h-5 w-5" />
                  </div>
                  <p class="text-xs font-medium text-foreground">{{ t('detail.noPhotoAttached') }}</p>
                  <p class="mt-1 text-[11px] text-muted-foreground">{{ t('detail.noPhotoDesc') }}</p>
                </div>
              </CardContent>
            </Card>

            <!-- 3. Location & Navigation Card -->
            <Card class="border-border/60 shadow-sm">
              <CardHeader class="pb-2">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <div class="flex items-center gap-2">
                    <MapPin class="h-4 w-4 text-primary" />
                    <CardTitle class="text-base font-semibold">
                      {{ t('detail.reportedLocation') }}
                    </CardTitle>
                  </div>

                  <!-- Google Maps Action Shortcuts -->
                  <div v-if="hasGps" class="flex flex-wrap items-center gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      class="h-7 gap-1 px-2.5 text-xs shadow-none"
                      @click="copyCoordinates"
                    >
                      <Check v-if="coordsCopied" class="h-3 w-3 text-emerald-600 stroke-[3]" />
                      <Copy v-else class="h-3 w-3 text-primary" />
                      {{ coordsCopied ? t('detail.coordsCopied') : t('detail.copyCoords') }}
                    </Button>
                    <a
                      :href="mapsUrl"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="inline-flex h-7 items-center gap-1 rounded-md border bg-background px-2.5 text-xs font-medium text-foreground hover:bg-accent"
                    >
                      <ExternalLink class="h-3 w-3 text-primary" />
                      {{ t('detail.openInMaps') }}
                    </a>
                    <a
                      :href="directionsUrl"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="inline-flex h-7 items-center gap-1 rounded-md bg-primary px-2.5 text-xs font-medium text-primary-foreground shadow-sm hover:bg-primary/90"
                    >
                      <Navigation class="h-3 w-3" />
                      {{ t('detail.getDirections') }}
                    </a>
                  </div>
                </div>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="rounded-xl border bg-muted/20 p-4">
                  <p class="text-sm font-medium leading-relaxed text-foreground">
                    {{ report.location_text }}
                  </p>

                  <!-- GPS Coordinates Badge -->
                  <div
                    v-if="hasGps"
                    class="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-border/50 pt-2.5"
                  >
                    <Badge variant="outline" class="font-mono text-[11px] tabular-nums">
                      <Compass class="mr-1 h-3 w-3 text-primary" />
                      GPS: {{ report.latitude }}, {{ report.longitude }}
                    </Badge>
                    <span class="text-[11px] text-muted-foreground">
                      Coordinates verified for municipal response
                    </span>
                  </div>
                </div>

                <!-- Interactive Mini Leaflet Map Preview -->
                <ReportMiniMap
                  v-if="hasGps"
                  :latitude="Number(report.latitude)"
                  :longitude="Number(report.longitude)"
                  :title="report.title"
                />
              </CardContent>
            </Card>
          </div>

          <!-- Right Column (4 cols): Incident Overview & Status Timeline -->
          <div class="space-y-6 lg:col-span-4">
            <!-- Incident Quick Summary Card -->
            <Card class="border-border/60 shadow-sm">
              <CardHeader class="pb-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <FileText class="h-4 w-4 text-primary" />
                    <CardTitle class="text-sm font-semibold">
                      {{ t('detail.summaryTitle') }}
                    </CardTitle>
                  </div>
                  <Badge variant="outline" class="font-mono text-xs tabular-nums text-muted-foreground">
                    #{{ report.id }}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent class="space-y-3 text-xs">
                <div class="flex items-center justify-between border-b pb-2">
                  <span class="text-muted-foreground">{{ t('detail.categoryLabel') }}</span>
                  <Badge variant="secondary" class="font-medium">
                    {{ localizedCategory(report.category_name, report.category_name_km, locale) }}
                  </Badge>
                </div>
                <div class="flex items-center justify-between border-b pb-2">
                  <span class="text-muted-foreground">{{ t('detail.reporterLabel') }}</span>
                  <span class="font-medium text-foreground">{{ report.reporter_name }}</span>
                </div>
                <div class="flex items-center justify-between border-b pb-2">
                  <span class="text-muted-foreground">{{ t('detail.submittedLabel') }}</span>
                  <span class="tabular-nums text-foreground">{{ formatDate(report.created_at, locale) }}</span>
                </div>
                <div v-if="hasGps" class="flex items-center justify-between border-b pb-2">
                  <span class="text-muted-foreground">GPS</span>
                  <span class="font-mono tabular-nums text-foreground">{{ Number(report.latitude).toFixed(4) }}, {{ Number(report.longitude).toFixed(4) }}</span>
                </div>
                <!-- Share Link Button -->
                <div class="pt-1">
                  <Button
                    variant="outline"
                    size="sm"
                    class="w-full gap-2 text-xs font-medium"
                    @click="copyReportLink"
                  >
                    <Check v-if="copied" class="h-3.5 w-3.5 text-emerald-600 stroke-[3]" />
                    <Share2 v-else class="h-3.5 w-3.5 text-primary" />
                    {{ copied ? t('detail.linkCopied') : t('detail.copyLink') }}
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card class="border-border/60 shadow-sm">
              <CardHeader class="pb-3">
                <div class="flex items-center gap-2">
                  <History class="h-4 w-4 text-primary" />
                  <CardTitle class="text-base font-semibold">
                    {{ t('detail.statusHistory') }}
                  </CardTitle>
                </div>
                <CardDescription class="text-xs">
                  {{ t('detail.statusHistoryDesc') }}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ol class="relative ml-2 space-y-6 border-l-2 border-border/70 pl-5">
                  <li
                    v-for="(entry, idx) in report.status_history"
                    :key="entry.id"
                    class="relative"
                  >
                    <!-- Timeline Node Indicator -->
                    <span
                      class="absolute -left-[27px] top-1 flex h-3.5 w-3.5 items-center justify-center rounded-full ring-4 ring-background"
                      :class="idx === 0 ? 'bg-primary' : 'bg-muted-foreground/30'"
                    />

                    <!-- Status transition badge -->
                    <div class="flex flex-wrap items-center gap-2">
                      <StatusBadge :status="entry.new_status" />
                      <span v-if="entry.old_status" class="text-xs text-muted-foreground">
                        {{ t('detail.fromStatus', { status: translateStatus(entry.old_status, t) }) }}
                      </span>
                    </div>

                    <!-- Administrative Note Callout Box -->
                    <div
                      v-if="entry.note"
                      class="mt-2.5 rounded-lg border border-border/60 bg-muted/40 p-3 text-xs leading-relaxed text-foreground shadow-sm"
                    >
                      <p class="font-medium text-foreground/90">
                        {{ entry.note }}
                      </p>
                    </div>

                    <!-- Actor info & Date -->
                    <p class="mt-2 text-[11px] text-muted-foreground">
                      {{ t('detail.byActor') }}
                      <span class="font-medium text-foreground">{{ entry.actor_name }}</span>
                      <span class="ml-1 text-[10px] text-muted-foreground/75">
                        ({{ translateRole(entry.actor_role, t) }})
                      </span>
                      •
                      <span class="tabular-nums">{{ formatDate(entry.changed_at, locale) }}</span>
                    </p>
                  </li>
                </ol>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <!-- Admin Status Update Dialog with Quick Preset Notes -->
      <Dialog v-model:open="statusDialogOpen">
        <DialogContent class="max-w-md">
          <DialogHeader>
            <DialogTitle>{{ t('detail.dialogTitle') }}</DialogTitle>
            <DialogDescription class="text-xs">
              {{ t('detail.dialogDesc') }}
            </DialogDescription>
          </DialogHeader>

          <div class="space-y-4 py-2">
            <!-- Status Selector -->
            <div class="space-y-1.5">
              <Label class="text-xs">{{ t('detail.newStatus') }}</Label>
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

            <!-- Quick Note Preset Chips -->
            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <Label for="status-note" class="text-xs">{{ t('detail.adminNote') }}</Label>
              </div>
              <p class="text-[11px] text-muted-foreground">
                {{ t('detail.quickNoteTemplates') }}
              </p>
              <div class="flex flex-col gap-1.5">
                <button
                  v-for="preset in notePresets"
                  :key="preset"
                  type="button"
                  class="rounded-md border border-border/70 bg-muted/20 px-2.5 py-1 text-left text-[11px] text-muted-foreground transition hover:border-primary hover:bg-primary/5 hover:text-foreground"
                  @click="applyPresetNote(preset)"
                >
                  + {{ t(`detail.${preset}`) }}
                </button>
              </div>

              <!-- Note Textarea -->
              <Textarea
                id="status-note"
                v-model="statusNote"
                rows="3"
                :placeholder="t('detail.adminNotePlaceholder')"
                class="mt-2 text-xs leading-relaxed"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" size="sm" @click="statusDialogOpen = false">
              {{ t('common.cancel') }}
            </Button>
            <Button size="sm" :disabled="savingStatus" class="min-w-28" @click="handleStatusSave">
              {{ savingStatus ? t('common.saving') : t('detail.saveStatusUpdate') }}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <!-- High-Resolution Fullscreen Photo Zoom Modal -->
      <Dialog v-model:open="zoomModalOpen">
        <DialogContent class="max-w-4xl">
          <DialogHeader>
            <DialogTitle class="text-sm font-semibold truncate">
              {{ report?.title }}
            </DialogTitle>
            <DialogDescription class="text-xs">
              {{ report?.location_text }}
            </DialogDescription>
          </DialogHeader>
          <div v-if="selectedPhotoUrl" class="flex max-h-[70vh] items-center justify-center overflow-hidden rounded-lg bg-muted/20 p-2">
            <img
              :src="selectedPhotoUrl"
              :alt="selectedPhotoAlt"
              class="max-h-[65vh] max-w-full rounded object-contain shadow-sm"
            />
          </div>
          <div v-if="photoPaths.length > 1" class="flex items-center justify-between gap-3">
            <Button type="button" variant="outline" size="icon" :disabled="activePhotoIndex === 0" :aria-label="t('detail.previousPhoto')" @click="activePhotoIndex--">
              <ChevronLeft class="h-4 w-4" />
            </Button>
            <p class="text-sm text-muted-foreground" aria-live="polite">{{ t('detail.photoPosition', { index: activePhotoIndex + 1, count: photoPaths.length }) }}</p>
            <Button type="button" variant="outline" size="icon" :disabled="activePhotoIndex === photoPaths.length - 1" :aria-label="t('detail.nextPhoto')" @click="activePhotoIndex++">
              <ChevronRight class="h-4 w-4" />
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  </AppLayout>
</template>
