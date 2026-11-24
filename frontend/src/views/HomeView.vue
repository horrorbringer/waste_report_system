<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Apple, ArrowRight, Camera, ChevronDown, Hammer, Package, Recycle, Search,
  Trash2, Tv, TriangleAlert,
} from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { useReportStore } from '@/stores/reports'
import { useCategoryStore } from '@/stores/categories'
import { localizedCategory } from '@/i18n'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'

const { t, locale } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const reportStore = useReportStore()
const categoryStore = useCategoryStore()

const trackInput = ref('')
const trackError = ref(false)
const isTracking = ref(false)

const questions = [
  { question: 'home.faq1Q', answer: 'home.faq1A' },
  { question: 'home.faq2Q', answer: 'home.faq2A' },
  { question: 'home.faq3Q', answer: 'home.faq3A' },
  { question: 'home.faq4Q', answer: 'home.faq4A' },
]

const stats = computed(() => {
  const summary = reportStore.publicStats
  return [
    { label: 'home.statTotal', count: summary?.total_reports, color: '' },
    { label: 'home.statPending', count: summary?.pending_reports, color: 'bg-amber-500' },
    { label: 'home.statInProgress', count: summary?.in_progress_reports, color: 'bg-blue-500' },
    { label: 'home.statResolved', count: summary?.resolved_reports, color: 'bg-emerald-500' },
  ]
})

const resolutionPercent = computed(() => {
  const stats = reportStore.publicStats
  return stats?.total_reports ? Math.round(stats.resolved_reports / stats.total_reports * 100) : 0
})

onMounted(() => {
  reportStore.fetchPublicStats().catch(() => {})
  categoryStore.fetchCategories().catch(() => {})
})

async function handleTrackSubmit() {
  const normalized = trackInput.value.trim().replace(/[០-៩]/g, (digit) =>
    String(digit.charCodeAt(0) - '០'.charCodeAt(0)),
  )
  const id = Number(normalized.replace(/^#\s*/, ''))
  if (!/^#?\s*[0-9]+$/.test(normalized) || !Number.isSafeInteger(id) || id <= 0) {
    trackError.value = true
    document.getElementById('track-id-input')?.focus()
    return
  }

  isTracking.value = true
  try {
    await router.push({ name: 'report-detail', params: { id } })
  } finally {
    isTracking.value = false
  }
}

function focusTracking() {
  document.getElementById('track-id-input')?.focus()
}

function categoryIcon(name: string) {
  const label = name.toLowerCase()
  if (label.includes('plastic')) return Recycle
  if (/organic|food/.test(label)) return Apple
  if (/overflow|bin|dump/.test(label)) return Trash2
  if (/construct|debris|rubble/.test(label)) return Hammer
  if (/electro|appliance|e-waste/.test(label)) return Tv
  if (/hazard|toxic|chemical/.test(label)) return TriangleAlert
  return Package
}
</script>

<template>
  <AppLayout>
    <section class="border-b bg-muted/20 py-10 sm:py-16">
      <div class="container grid max-w-6xl items-center gap-8 lg:grid-cols-[1.35fr_1fr] lg:gap-14">
        <div class="space-y-5">
          <h1 class="font-display text-3xl font-extrabold leading-tight tracking-tight sm:text-5xl">
            {{ t('home.heroLine1') }}
            <span class="block text-primary">{{ t('home.heroLine2') }}</span>
          </h1>
          <p class="max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            {{ t('home.heroDesc') }}
          </p>
          <div class="grid gap-2 sm:flex sm:flex-wrap sm:gap-3">
            <Button as-child size="lg" class="min-h-11 gap-2">
              <RouterLink :to="{ name: 'submit-report' }">
                <Camera class="h-4 w-4" />
                {{ t('home.ctaSubmit') }}
              </RouterLink>
            </Button>
            <Button type="button" size="lg" variant="outline" class="min-h-11 gap-2" @click="focusTracking">
              <Search class="h-4 w-4" />
              {{ t('home.trackTitle') }}
            </Button>
          </div>
        </div>

        <Card class="scroll-mt-20" id="track-report">
          <CardContent class="space-y-4 p-5 sm:p-6">
            <div class="space-y-1">
              <h2 class="text-lg font-semibold">{{ t('home.trackTitle') }}</h2>
              <p id="track-help" class="text-sm leading-relaxed text-muted-foreground">
                {{ t(auth.isAuthenticated ? 'home.trackHelper' : 'home.trackSignInRequired') }}
              </p>
            </div>

            <form class="space-y-2" @submit.prevent="handleTrackSubmit">
              <label for="track-id-input" class="block text-sm font-medium">{{ t('home.trackInputLabel') }}</label>
              <div class="flex gap-2">
                <Input
                  id="track-id-input"
                  v-model="trackInput"
                  type="text"
                  inputmode="numeric"
                  :placeholder="t('home.trackInputPlaceholder')"
                  :aria-invalid="trackError || undefined"
                  :aria-describedby="trackError ? 'track-help track-error' : 'track-help'"
                  class="min-w-0 flex-1"
                  @input="trackError = false"
                />
                <Button type="submit" :disabled="isTracking">
                  {{ t('home.trackButton') }}
                </Button>
              </div>
              <p v-if="trackError" id="track-error" role="alert" class="text-sm text-destructive">
                {{ t('home.trackError') }}
              </p>
            </form>

            <RouterLink v-if="auth.isAuthenticated" :to="{ name: 'my-reports' }" class="inline-flex text-sm font-medium text-primary hover:underline">
              {{ t('home.ctaMyReports') }}
            </RouterLink>
          </CardContent>
        </Card>
      </div>
    </section>

    <section v-if="reportStore.publicStats" class="border-b py-7 sm:py-9">
      <div class="container max-w-6xl space-y-4">
        <div class="flex flex-wrap items-baseline justify-between gap-2">
          <h2 class="text-lg font-semibold">{{ t('home.statsTitle') }}</h2>
          <p class="text-sm text-muted-foreground">{{ t('home.resolutionRateDesc', { percent: resolutionPercent }) }}</p>
        </div>
        <div v-if="reportStore.publicStats.total_reports" class="flex h-2 overflow-hidden rounded-full bg-muted" aria-hidden="true">
          <div
            v-for="stat in stats.slice(1)"
            :key="stat.label"
            :class="stat.color"
            :style="{ flexGrow: stat.count ?? 0 }"
          />
        </div>
        <dl class="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div v-for="stat in stats" :key="stat.label">
            <dt class="flex items-center gap-2 text-sm text-muted-foreground">
              <span v-if="stat.color" class="h-2 w-2 shrink-0 rounded-full" :class="stat.color" aria-hidden="true" />
              {{ t(stat.label) }}
            </dt>
            <dd class="mt-1 text-2xl font-semibold tabular-nums">{{ stat.count }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <section v-if="categoryStore.categories.length" class="border-b py-8 sm:py-11">
      <div class="container max-w-6xl space-y-4">
        <h2 class="text-xl font-semibold">{{ t('home.categoriesTitle') }}</h2>
        <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          <RouterLink
            v-for="cat in categoryStore.categories"
            :key="cat.id"
            :to="{ name: 'submit-report', query: { category: cat.id } }"
            class="group flex min-h-12 items-center gap-3 rounded-lg border bg-card px-3 py-2 text-sm font-medium transition hover:border-primary hover:text-primary"
          >
            <component :is="categoryIcon(cat.name)" class="h-4 w-4 shrink-0 text-primary" />
            <span class="flex-1">{{ localizedCategory(cat.name, cat.name_km, locale) }}</span>
            <ArrowRight class="h-4 w-4 shrink-0 text-muted-foreground group-hover:text-primary" />
          </RouterLink>
        </div>
      </div>
    </section>

    <section class="border-b bg-muted/20 py-8 sm:py-11">
      <div class="container grid max-w-6xl items-start gap-6 md:grid-cols-[1fr_1.4fr] md:gap-12">
        <div class="space-y-3">
          <h2 class="text-xl font-semibold">{{ t('home.helpTitle') }}</h2>
          <p class="text-sm leading-relaxed text-muted-foreground">{{ t('home.helpIntro') }}</p>
          <div class="space-y-1 text-sm">
            <p class="font-medium">{{ t('home.hotlineTitle') }}</p>
            <p class="text-muted-foreground">{{ t('home.hotlinePhone') }} · {{ t('home.hotlineHours') }}</p>
          </div>
        </div>
        <div class="divide-y rounded-lg border bg-card px-4">
          <details v-for="item in questions" :key="item.question" class="group">
            <summary class="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 py-2 text-sm font-medium [&::-webkit-details-marker]:hidden">
              {{ t(item.question) }}
              <ChevronDown class="h-4 w-4 shrink-0 text-muted-foreground group-open:rotate-180" />
            </summary>
            <p class="pb-3 text-sm leading-relaxed text-muted-foreground">{{ t(item.answer) }}</p>
          </details>
        </div>
      </div>
    </section>

    <div v-if="!auth.isAuthenticated" class="container flex max-w-6xl flex-wrap items-center gap-x-5 gap-y-2 py-5 text-sm">
      <p class="text-muted-foreground">{{ t('home.quickDemoLabel') }}</p>
      <RouterLink :to="{ name: 'login', query: { demo: 'resident' } }" class="font-medium text-primary hover:underline">
        {{ t('auth.residentDemo') }}
      </RouterLink>
      <RouterLink :to="{ name: 'login', query: { demo: 'admin' } }" class="font-medium text-primary hover:underline">
        {{ t('auth.adminDemo') }}
      </RouterLink>
    </div>
  </AppLayout>
</template>
