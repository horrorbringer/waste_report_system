<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Leaf,
  Camera,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Clock,
  TrendingUp,
  MapPin,
  Check,
  ChevronRight,
  HelpCircle,
  Layers,
  Recycle,
  Apple,
  Trash2,
  Hammer,
  Tv,
  AlertTriangle,
  Package,
  Building2,
  Search,
  PhoneCall,
  FileText,
  ChevronDown,
  Info,
  CalendarCheck,
  AlertCircle,
  ExternalLink,
  Loader2,
} from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { useReportStore } from '@/stores/reports'
import { useCategoryStore } from '@/stores/categories'
import { localizedCategory } from '@/i18n'
import type { Category } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

const { t, locale } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const reportStore = useReportStore()
const categoryStore = useCategoryStore()

const trackInput = ref('')
const trackError = ref('')
const isTracking = ref(false)
const demoLoading = ref<'resident' | 'admin' | null>(null)
const activeFaq = ref<number | null>(0)

onMounted(async () => {
  reportStore.fetchPublicStats().catch(() => {})
  categoryStore.fetchCategories().catch(() => {})
})

// Calculate resolution rate
const resolutionPercent = computed(() => {
  const stats = reportStore.publicStats
  if (!stats || !stats.total_reports || stats.total_reports === 0) return 0
  const rate = Math.round((stats.resolved_reports / stats.total_reports) * 100)
  return Math.max(0, Math.min(100, rate))
})

// Calculate progress ratios for segmented pipeline
const pipelineRatios = computed(() => {
  const stats = reportStore.publicStats
  const total = stats?.total_reports || 0
  if (total === 0) {
    return { resolvedPct: 0, inProgressPct: 0, pendingPct: 0 }
  }
  const resolved = stats?.resolved_reports ?? 0
  const inProgress = stats?.in_progress_reports ?? 0
  const pending = stats?.pending_reports ?? 0

  return {
    resolvedPct: Math.round((resolved / total) * 100),
    inProgressPct: Math.round((inProgress / total) * 100),
    pendingPct: Math.round((pending / total) * 100),
  }
})

async function handleTrackSubmit() {
  trackError.value = ''
  const clean = trackInput.value.replace('#', '').trim()
  const idNum = parseInt(clean, 10)
  if (!clean || isNaN(idNum) || idNum <= 0) {
    trackError.value = t('home.trackError')
    return
  }
  isTracking.value = true
  try {
    await router.push(`/reports/${idNum}`)
  } finally {
    isTracking.value = false
  }
}

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

function handleCategoryClick(cat: Category) {
  if (auth.isAuthenticated) {
    router.push({ path: '/reports/new', query: { category: String(cat.id) } })
  } else {
    router.push({ path: '/login', query: { redirect: `/reports/new?category=${cat.id}` } })
  }
}

function toggleFaq(index: number) {
  activeFaq.value = activeFaq.value === index ? null : index
}

async function quickLoginDemo(role: 'resident' | 'admin') {
  demoLoading.value = role
  const email = role === 'admin' ? 'admin@ecowatch.kh' : 'resident@ecowatch.kh'
  const password = 'password123'
  try {
    await auth.login(email, password)
    if (role === 'admin') {
      router.push('/admin/dashboard')
    } else {
      router.push('/my-reports')
    }
  } catch {
    router.push('/login')
  } finally {
    demoLoading.value = null
  }
}
</script>

<template>
  <AppLayout>
    <!-- SECTION 1: Civic Municipal Hero with Real Incident Tracker -->
    <section class="border-b bg-muted/20 py-8 sm:py-12 md:py-16">
      <div class="container px-4 sm:px-6">
        <div class="grid items-center gap-8 lg:grid-cols-12 lg:gap-12">
          <!-- Left Column: Official Municipal Headline & CTAs -->
          <div class="space-y-4 sm:space-y-6 text-center lg:col-span-7 lg:text-left">
            <!-- Authoritative Municipal Badges -->
            <div class="flex flex-wrap items-center justify-center gap-2 lg:justify-start">
              <Badge variant="outline" class="gap-1.5 border-border bg-background px-3 py-1 text-[11px] font-semibold tracking-wider text-foreground shadow-xs">
                <Leaf class="h-3.5 w-3.5 text-primary" />
                {{ t('home.badge') }}
              </Badge>
              <Badge variant="secondary" class="gap-1.5 px-3 py-1 text-[11px] font-medium">
                <Building2 class="h-3 w-3 text-muted-foreground" />
                Phnom Penh Municipality
              </Badge>
            </div>

            <!-- Solid High-Contrast Headline (Zero Rainbow Text) -->
            <h1 class="font-display text-3xl font-extrabold tracking-tight sm:text-5xl md:text-5xl text-foreground leading-[1.15]">
              {{ t('home.heroLine1') }}
              <span class="block text-primary mt-1">
                {{ t('home.heroLine2') }}
              </span>
            </h1>

            <p class="mx-auto max-w-2xl text-sm sm:text-base leading-relaxed text-muted-foreground lg:mx-0">
              {{ t('home.heroDesc') }}
            </p>

            <!-- Direct Action Buttons -->
            <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3 pt-2 lg:justify-start">
              <RouterLink v-if="auth.isAuthenticated" to="/reports/new" class="w-full sm:w-auto">
                <Button size="lg" class="h-11 sm:h-12 w-full px-6 gap-2 text-sm font-semibold shadow-xs">
                  <Camera class="h-4 w-4" />
                  {{ t('home.ctaSubmit') }}
                  <ArrowRight class="h-4 w-4" />
                </Button>
              </RouterLink>
              <RouterLink v-else to="/register" class="w-full sm:w-auto">
                <Button size="lg" class="h-11 sm:h-12 w-full px-6 gap-2 text-sm font-semibold shadow-xs">
                  <Camera class="h-4 w-4" />
                  {{ t('home.ctaStart') }}
                  <ArrowRight class="h-4 w-4" />
                </Button>
              </RouterLink>

              <RouterLink v-if="auth.isAdmin" to="/admin/dashboard" class="w-full sm:w-auto">
                <Button variant="outline" size="lg" class="h-11 sm:h-12 w-full px-5 gap-2 text-sm font-medium">
                  <ShieldCheck class="h-4 w-4 text-primary" />
                  {{ t('home.ctaAdmin') }}
                </Button>
              </RouterLink>
              <RouterLink v-else-if="auth.isAuthenticated" to="/my-reports" class="w-full sm:w-auto">
                <Button variant="outline" size="lg" class="h-11 sm:h-12 w-full px-5 gap-2 text-sm font-medium">
                  <FileText class="h-4 w-4" />
                  {{ t('home.ctaMyReports') }}
                </Button>
              </RouterLink>
              <RouterLink v-else to="/login" class="w-full sm:w-auto">
                <Button variant="outline" size="lg" class="h-11 sm:h-12 w-full px-6 text-sm font-medium">
                  {{ t('nav.signIn') }}
                </Button>
              </RouterLink>
            </div>

            <!-- Crisp Verification Attributes -->
            <div class="pt-3 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground lg:justify-start border-t border-border/60">
              <div class="flex items-center gap-1.5 font-medium">
                <MapPin class="h-3.5 w-3.5 text-primary shrink-0" />
                <span>{{ t('home.heroTrustGps') }}</span>
              </div>
              <div class="flex items-center gap-1.5 font-medium">
                <Clock class="h-3.5 w-3.5 text-primary shrink-0" />
                <span>{{ t('home.heroTrustResponse') }}</span>
              </div>
              <div class="flex items-center gap-1.5 font-medium">
                <Building2 class="h-3.5 w-3.5 text-primary shrink-0" />
                <span>{{ t('home.heroTrustBilingual') }}</span>
              </div>
            </div>
          </div>

          <!-- Right Column: Real Municipal Action & Status Tracking Tool -->
          <div class="mx-auto w-full max-w-md lg:col-span-5">
            <Card class="border border-border bg-card shadow-sm rounded-xl overflow-hidden">
              <!-- Portal Header Strip -->
              <div class="flex items-center justify-between border-b bg-muted/40 px-4 py-3">
                <div class="flex items-center gap-2">
                  <Building2 class="h-4 w-4 text-primary" />
                  <span class="text-xs font-bold text-foreground">
                    {{ t('home.portalCardBadge') }}
                  </span>
                </div>
                <div class="flex items-center gap-1.5 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                  <span class="h-2 w-2 rounded-full bg-emerald-500" />
                  {{ t('home.portalCardStatus') }}
                </div>
              </div>

              <CardContent class="p-5 space-y-5">
                <!-- Utility 1: Direct Report Tracking Tool -->
                <div class="space-y-2.5">
                  <label for="track-id-input" class="text-xs font-semibold uppercase tracking-wider text-foreground flex items-center justify-between">
                    <span>{{ t('home.trackInputLabel') }}</span>
                    <span class="text-[11px] font-normal text-muted-foreground">e.g. #9</span>
                  </label>
                  <form @submit.prevent="handleTrackSubmit" class="flex items-stretch gap-2">
                    <div class="relative flex-1">
                      <span class="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-xs font-mono">#</span>
                      <input
                        id="track-id-input"
                        v-model="trackInput"
                        type="number"
                        min="1"
                        step="1"
                        :placeholder="t('home.trackInputPlaceholder')"
                        class="h-10 w-full rounded-lg border border-input bg-background pl-7 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                      />
                    </div>
                    <Button type="submit" class="h-10 px-4 gap-1.5 text-xs font-semibold shrink-0" :disabled="isTracking">
                      <Loader2 v-if="isTracking" class="h-3.5 w-3.5 animate-spin" />
                      <Search v-else class="h-3.5 w-3.5" />
                      {{ t('home.trackButton') }}
                    </Button>
                  </form>
                  <p v-if="trackError" class="text-xs text-destructive font-medium flex items-center gap-1 pt-0.5">
                    <AlertCircle class="h-3.5 w-3.5" />
                    {{ trackError }}
                  </p>
                  <div class="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
                    <span>{{ t('home.trackHelper') }}</span>
                    <RouterLink to="/reports/9" class="font-medium text-primary hover:underline inline-flex items-center gap-0.5">
                      {{ t('home.trackRecentSample') }} #9
                      <ChevronRight class="h-3 w-3" />
                    </RouterLink>
                  </div>
                </div>

                <!-- Utility 2: Official Sanitation Hotline & Operating Strip -->
                <div class="rounded-lg border border-border/80 bg-muted/30 p-3 space-y-1.5">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold text-foreground flex items-center gap-1.5">
                      <PhoneCall class="h-3.5 w-3.5 text-primary" />
                      {{ t('home.hotlineTitle') }}
                    </span>
                    <Badge variant="outline" class="text-[10px] font-medium bg-background">
                      {{ t('home.hotlineHours') }}
                    </Badge>
                  </div>
                  <p class="font-mono text-sm font-bold text-primary">
                    {{ t('home.hotlinePhone') }}
                  </p>
                  <p class="text-[11px] text-muted-foreground leading-snug">
                    Direct connection to Phnom Penh Department of Public Works and Transport & municipal collection operators.
                  </p>
                </div>

                <!-- Utility 3: Quick Evaluator Account Switcher -->
                <div class="border-t pt-4 space-y-2">
                  <p class="text-[11px] font-semibold text-muted-foreground">
                    {{ t('home.quickDemoLabel') }}
                  </p>
                  <div class="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      :disabled="demoLoading !== null"
                      class="flex items-center justify-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-xs font-medium text-foreground transition hover:border-primary hover:text-primary disabled:opacity-50"
                      @click="quickLoginDemo('resident')"
                    >
                      <Loader2 v-if="demoLoading === 'resident'" class="h-3.5 w-3.5 animate-spin text-primary" />
                      <FileText v-else class="h-3.5 w-3.5 text-primary" />
                      <span>Resident Portal</span>
                    </button>
                    <button
                      type="button"
                      :disabled="demoLoading !== null"
                      class="flex items-center justify-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-xs font-medium text-foreground transition hover:border-primary hover:text-primary disabled:opacity-50"
                      @click="quickLoginDemo('admin')"
                    >
                      <Loader2 v-if="demoLoading === 'admin'" class="h-3.5 w-3.5 animate-spin text-primary" />
                      <ShieldCheck v-else class="h-3.5 w-3.5 text-primary" />
                      <span>Admin Console</span>
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 2: Municipal Operational Summary & Public Resolution Progress -->
    <section class="border-b bg-card py-8 sm:py-10">
      <div class="container px-4 sm:px-6 space-y-6">
        <!-- 4 Metric Cards in Clean Civic Bordered Grid -->
        <div class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          <Card class="border border-border/80 shadow-xs">
            <CardContent class="p-4 sm:p-5">
              <div class="flex items-center justify-between text-muted-foreground">
                <p class="text-[11px] font-bold uppercase tracking-wider truncate">
                  {{ t('home.statTotal') }}
                </p>
                <TrendingUp class="h-4 w-4 text-primary shrink-0" />
              </div>
              <div v-if="reportStore.loading && !reportStore.publicStats" class="mt-2 space-y-1.5">
                <Skeleton class="h-8 w-16" />
                <Skeleton class="h-3 w-28" />
              </div>
              <div v-else>
                <p class="mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
                  {{ reportStore.publicStats?.total_reports ?? '—' }}
                </p>
                <p class="mt-0.5 text-[11px] text-muted-foreground">All Phnom Penh districts</p>
              </div>
            </CardContent>
          </Card>

          <Card class="border border-border/80 shadow-xs">
            <CardContent class="p-4 sm:p-5">
              <div class="flex items-center justify-between text-amber-600 dark:text-amber-400">
                <p class="text-[11px] font-bold uppercase tracking-wider truncate">
                  {{ t('home.statPending') }}
                </p>
                <Clock class="h-4 w-4 shrink-0" />
              </div>
              <div v-if="reportStore.loading && !reportStore.publicStats" class="mt-2 space-y-1.5">
                <Skeleton class="h-8 w-16" />
                <Skeleton class="h-3 w-24" />
              </div>
              <div v-else>
                <p class="mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-amber-600 dark:text-amber-400">
                  {{ reportStore.publicStats?.pending_reports ?? '—' }}
                </p>
                <p class="mt-0.5 text-[11px] text-muted-foreground">Awaiting inspection</p>
              </div>
            </CardContent>
          </Card>

          <Card class="border border-border/80 shadow-xs">
            <CardContent class="p-4 sm:p-5">
              <div class="flex items-center justify-between text-blue-600 dark:text-blue-400">
                <p class="text-[11px] font-bold uppercase tracking-wider truncate">
                  {{ t('home.statInProgress') }}
                </p>
                <Building2 class="h-4 w-4 shrink-0" />
              </div>
              <div v-if="reportStore.loading && !reportStore.publicStats" class="mt-2 space-y-1.5">
                <Skeleton class="h-8 w-16" />
                <Skeleton class="h-3 w-32" />
              </div>
              <div v-else>
                <p class="mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-blue-600 dark:text-blue-400">
                  {{ reportStore.publicStats?.in_progress_reports ?? '—' }}
                </p>
                <p class="mt-0.5 text-[11px] text-muted-foreground">Sanitation crew assigned</p>
              </div>
            </CardContent>
          </Card>

          <Card class="border border-border/80 shadow-xs">
            <CardContent class="p-4 sm:p-5">
              <div class="flex items-center justify-between text-emerald-600 dark:text-emerald-400">
                <p class="text-[11px] font-bold uppercase tracking-wider truncate">
                  {{ t('home.statResolved') }}
                </p>
                <CheckCircle2 class="h-4 w-4 shrink-0" />
              </div>
              <div v-if="reportStore.loading && !reportStore.publicStats" class="mt-2 space-y-1.5">
                <Skeleton class="h-8 w-16" />
                <Skeleton class="h-3 w-24" />
              </div>
              <div v-else>
                <p class="mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-emerald-600 dark:text-emerald-400">
                  {{ reportStore.publicStats?.resolved_reports ?? '—' }}
                </p>
                <p class="mt-0.5 text-[11px] text-muted-foreground">Cleared & verified</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Resolution Pipeline Status Bar -->
        <div class="rounded-xl border border-border bg-muted/20 p-4 sm:p-5 space-y-3">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <p class="text-xs font-bold uppercase tracking-wider text-foreground">
                {{ t('home.resolutionRate') }}
              </p>
              <p class="text-xs text-muted-foreground mt-0.5">
                {{ t('home.resolutionRateDesc', { percent: resolutionPercent }) }}
              </p>
            </div>
            <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-medium">
              <span class="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                <span class="h-2 w-2 rounded-full bg-emerald-500" />
                Resolved ({{ pipelineRatios.resolvedPct }}%)
              </span>
              <span class="flex items-center gap-1.5 text-blue-600 dark:text-blue-400">
                <span class="h-2 w-2 rounded-full bg-blue-500" />
                In Progress ({{ pipelineRatios.inProgressPct }}%)
              </span>
              <span class="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
                <span class="h-2 w-2 rounded-full bg-amber-500" />
                Pending ({{ pipelineRatios.pendingPct }}%)
              </span>
            </div>
          </div>

          <!-- Solid Progress Bar -->
          <div class="h-2.5 w-full rounded-full bg-muted overflow-hidden flex">
            <div
              class="h-full bg-emerald-500 transition-all duration-300"
              :style="{ width: `${pipelineRatios.resolvedPct}%` }"
              title="Resolved"
            />
            <div
              class="h-full bg-blue-500 transition-all duration-300"
              :style="{ width: `${pipelineRatios.inProgressPct}%` }"
              title="In Progress"
            />
            <div
              class="h-full bg-amber-500 transition-all duration-300"
              :style="{ width: `${pipelineRatios.pendingPct}%` }"
              title="Pending"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 3: Official Waste Classifications ("What Can You Report?") -->
    <section class="py-12 sm:py-16 border-b">
      <div class="container px-4 sm:px-6 space-y-8">
        <div class="max-w-2xl space-y-2">
          <Badge variant="outline" class="gap-1 border-border text-foreground text-xs font-semibold uppercase tracking-wider">
            <Layers class="h-3 w-3 text-primary" />
            {{ t('home.categoriesEyebrow') }}
          </Badge>
          <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            {{ t('home.categoriesTitle') }}
          </h2>
          <p class="text-sm text-muted-foreground leading-relaxed">
            {{ t('home.categoriesDesc') }}
          </p>
        </div>

        <!-- Loading Skeletons for Categories -->
        <div v-if="categoryStore.loading && categoryStore.categories.length === 0" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="n in 6" :key="n" class="rounded-xl border border-border bg-card p-5 space-y-3">
            <div class="flex items-center justify-between">
              <Skeleton class="h-10 w-10 rounded-lg" />
              <Skeleton class="h-4 w-12" />
            </div>
            <div class="space-y-2">
              <Skeleton class="h-5 w-3/4" />
              <Skeleton class="h-3.5 w-full" />
              <Skeleton class="h-3.5 w-2/3" />
            </div>
            <div class="pt-3 border-t border-border/40 flex justify-between">
              <Skeleton class="h-4 w-28" />
              <Skeleton class="h-4 w-4 rounded-full" />
            </div>
          </div>
        </div>

        <!-- Practical Municipal Grid (Click to report directly) -->
        <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="cat in categoryStore.categories"
            :key="cat.id"
            class="group relative flex flex-col justify-between rounded-xl border border-border bg-card p-5 shadow-xs transition hover:border-primary hover:bg-muted/10 cursor-pointer"
            @click="handleCategoryClick(cat)"
          >
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-foreground transition group-hover:bg-primary group-hover:text-primary-foreground">
                  <component :is="getCategoryIcon(cat.name)" class="h-5 w-5" />
                </div>
                <Badge variant="outline" class="text-[11px] font-mono font-medium text-muted-foreground">
                  #{{ cat.id }}
                </Badge>
              </div>

              <div>
                <h3 class="font-bold text-base text-foreground group-hover:text-primary transition-colors">
                  {{ localizedCategory(cat.name, cat.name_km, locale) }}
                </h3>
                <p class="mt-1 text-xs text-muted-foreground leading-relaxed line-clamp-2">
                  {{ (locale === 'km' && cat.description_km) ? cat.description_km : (cat.description || 'Community waste collection item') }}
                </p>
              </div>
            </div>

            <div class="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-xs font-semibold text-primary">
              <span>{{ t('home.reportThisCategory') }}</span>
              <ArrowRight class="h-3.5 w-3.5 transition group-hover:translate-x-1" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 4: Citizen Reporting Workflow (3 Concrete Steps) -->
    <section class="py-12 sm:py-16 border-b bg-muted/20">
      <div class="container px-4 sm:px-6 space-y-8">
        <div class="max-w-2xl space-y-2">
          <Badge variant="outline" class="gap-1 border-border text-foreground text-xs font-semibold uppercase tracking-wider">
            <CalendarCheck class="h-3 w-3 text-primary" />
            {{ t('home.workflowEyebrow') }}
          </Badge>
          <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            {{ t('home.workflowTitle') }}
          </h2>
          <p class="text-sm text-muted-foreground leading-relaxed">
            {{ t('home.workflowDesc') }}
          </p>
        </div>

        <div class="grid gap-5 md:grid-cols-3">
          <!-- Step 1 -->
          <Card class="border border-border bg-card shadow-xs">
            <CardHeader class="pb-3">
              <div class="flex items-center justify-between mb-2">
                <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-black text-primary-foreground">
                  1
                </span>
                <Badge variant="outline" class="text-[11px] font-medium text-muted-foreground">
                  Resident Action
                </Badge>
              </div>
              <CardTitle class="text-base font-bold text-foreground">{{ t('home.step1Title') }}</CardTitle>
              <CardDescription class="text-xs leading-relaxed mt-1">
                {{ t('home.step1Desc') }}
              </CardDescription>
            </CardHeader>
            <CardContent class="text-xs text-muted-foreground space-y-1.5 pt-1 border-t border-border/50">
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-primary stroke-[3]" />
                <span>Google Map Pin & GPS Autofill</span>
              </div>
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-primary stroke-[3]" />
                <span>Camera Photo Upload</span>
              </div>
            </CardContent>
          </Card>

          <!-- Step 2 -->
          <Card class="border border-border bg-card shadow-xs">
            <CardHeader class="pb-3">
              <div class="flex items-center justify-between mb-2">
                <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-black text-white">
                  2
                </span>
                <Badge variant="outline" class="text-[11px] font-medium text-blue-600 border-blue-500/30">
                  Municipal Dispatch
                </Badge>
              </div>
              <CardTitle class="text-base font-bold text-foreground">{{ t('home.step2Title') }}</CardTitle>
              <CardDescription class="text-xs leading-relaxed mt-1">
                {{ t('home.step2Desc') }}
              </CardDescription>
            </CardHeader>
            <CardContent class="text-xs text-muted-foreground space-y-1.5 pt-1 border-t border-border/50">
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-blue-600 stroke-[3]" />
                <span>Priority Triage & Team Routing</span>
              </div>
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-blue-600 stroke-[3]" />
                <span>Official Status Updates</span>
              </div>
            </CardContent>
          </Card>

          <!-- Step 3 -->
          <Card class="border border-border bg-card shadow-xs">
            <CardHeader class="pb-3">
              <div class="flex items-center justify-between mb-2">
                <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-sm font-black text-white">
                  3
                </span>
                <Badge variant="outline" class="text-[11px] font-medium text-emerald-600 border-emerald-500/30">
                  Verification
                </Badge>
              </div>
              <CardTitle class="text-base font-bold text-foreground">{{ t('home.step3Title') }}</CardTitle>
              <CardDescription class="text-xs leading-relaxed mt-1">
                {{ t('home.step3Desc') }}
              </CardDescription>
            </CardHeader>
            <CardContent class="text-xs text-muted-foreground space-y-1.5 pt-1 border-t border-border/50">
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-emerald-600 stroke-[3]" />
                <span>Cleaned Site & Status Resolved</span>
              </div>
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-emerald-600 stroke-[3]" />
                <span>Public Timestamped Audit History</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>

    <!-- SECTION 5: Citizen Guidelines & Operational Principles (Grounded Civic Content) -->
    <section class="py-12 sm:py-16 border-b">
      <div class="container px-4 sm:px-6 space-y-8">
        <div class="max-w-2xl space-y-2">
          <Badge variant="outline" class="gap-1 border-border text-foreground text-xs font-semibold uppercase tracking-wider">
            <ShieldCheck class="h-3 w-3 text-primary" />
            {{ t('home.pillarsEyebrow') }}
          </Badge>
          <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            {{ t('home.pillarsTitle') }}
          </h2>
        </div>

        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <!-- Standard 1 -->
          <div class="rounded-xl border border-border bg-card p-5 space-y-2.5">
            <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-muted text-foreground">
              <MapPin class="h-4 w-4 text-primary" />
            </div>
            <h3 class="font-bold text-sm text-foreground">{{ t('home.pillar1Title') }}</h3>
            <p class="text-xs text-muted-foreground leading-relaxed">{{ t('home.pillar1Desc') }}</p>
          </div>

          <!-- Standard 2 -->
          <div class="rounded-xl border border-border bg-card p-5 space-y-2.5">
            <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-muted text-foreground">
              <Clock class="h-4 w-4 text-blue-600" />
            </div>
            <h3 class="font-bold text-sm text-foreground">{{ t('home.pillar2Title') }}</h3>
            <p class="text-xs text-muted-foreground leading-relaxed">{{ t('home.pillar2Desc') }}</p>
          </div>

          <!-- Standard 3 -->
          <div class="rounded-xl border border-border bg-card p-5 space-y-2.5">
            <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-muted text-foreground">
              <Leaf class="h-4 w-4 text-emerald-600" />
            </div>
            <h3 class="font-bold text-sm text-foreground">{{ t('home.pillar3Title') }}</h3>
            <p class="text-xs text-muted-foreground leading-relaxed">{{ t('home.pillar3Desc') }}</p>
          </div>

          <!-- Standard 4 -->
          <div class="rounded-xl border border-border bg-card p-5 space-y-2.5">
            <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-muted text-foreground">
              <ShieldCheck class="h-4 w-4 text-purple-600" />
            </div>
            <h3 class="font-bold text-sm text-foreground">{{ t('home.pillar4Title') }}</h3>
            <p class="text-xs text-muted-foreground leading-relaxed">{{ t('home.pillar4Desc') }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 6: Resident Guidance FAQ (Clean Municipal Style) -->
    <section class="py-12 sm:py-16 border-b bg-muted/20">
      <div class="container max-w-3xl px-4 sm:px-6 space-y-6">
        <div class="space-y-2 text-center">
          <Badge variant="outline" class="gap-1 border-border text-foreground text-xs font-semibold uppercase tracking-wider">
            <HelpCircle class="h-3 w-3 text-primary" />
            {{ t('home.faqEyebrow') }}
          </Badge>
          <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            {{ t('home.faqTitle') }}
          </h2>
        </div>

        <div class="space-y-2.5 pt-2">
          <!-- FAQ 1 -->
          <div class="rounded-xl border border-border bg-card overflow-hidden">
            <button
              type="button"
              class="flex w-full items-center justify-between p-4 sm:p-5 text-left text-sm font-semibold text-foreground hover:bg-muted/40 transition"
              @click="toggleFaq(0)"
            >
              <span>{{ t('home.faq1Q') }}</span>
              <ChevronDown class="h-4 w-4 shrink-0 transition-transform duration-200" :class="{ 'rotate-180': activeFaq === 0 }" />
            </button>
            <Transition name="accordion">
              <div v-show="activeFaq === 0" class="px-4 sm:px-5 pb-4 text-xs sm:text-sm text-muted-foreground leading-relaxed border-t border-border/60 pt-3">
                {{ t('home.faq1A') }}
              </div>
            </Transition>
          </div>

          <!-- FAQ 2 -->
          <div class="rounded-xl border border-border bg-card overflow-hidden">
            <button
              type="button"
              class="flex w-full items-center justify-between p-4 sm:p-5 text-left text-sm font-semibold text-foreground hover:bg-muted/40 transition"
              @click="toggleFaq(1)"
            >
              <span>{{ t('home.faq2Q') }}</span>
              <ChevronDown class="h-4 w-4 shrink-0 transition-transform duration-200" :class="{ 'rotate-180': activeFaq === 1 }" />
            </button>
            <Transition name="accordion">
              <div v-show="activeFaq === 1" class="px-4 sm:px-5 pb-4 text-xs sm:text-sm text-muted-foreground leading-relaxed border-t border-border/60 pt-3">
                {{ t('home.faq2A') }}
              </div>
            </Transition>
          </div>

          <!-- FAQ 3 -->
          <div class="rounded-xl border border-border bg-card overflow-hidden">
            <button
              type="button"
              class="flex w-full items-center justify-between p-4 sm:p-5 text-left text-sm font-semibold text-foreground hover:bg-muted/40 transition"
              @click="toggleFaq(2)"
            >
              <span>{{ t('home.faq3Q') }}</span>
              <ChevronDown class="h-4 w-4 shrink-0 transition-transform duration-200" :class="{ 'rotate-180': activeFaq === 2 }" />
            </button>
            <Transition name="accordion">
              <div v-show="activeFaq === 2" class="px-4 sm:px-5 pb-4 text-xs sm:text-sm text-muted-foreground leading-relaxed border-t border-border/60 pt-3">
                {{ t('home.faq3A') }}
              </div>
            </Transition>
          </div>

          <!-- FAQ 4 -->
          <div class="rounded-xl border border-border bg-card overflow-hidden">
            <button
              type="button"
              class="flex w-full items-center justify-between p-4 sm:p-5 text-left text-sm font-semibold text-foreground hover:bg-muted/40 transition"
              @click="toggleFaq(3)"
            >
              <span>{{ t('home.faq4Q') }}</span>
              <ChevronDown class="h-4 w-4 shrink-0 transition-transform duration-200" :class="{ 'rotate-180': activeFaq === 3 }" />
            </button>
            <Transition name="accordion">
              <div v-show="activeFaq === 3" class="px-4 sm:px-5 pb-4 text-xs sm:text-sm text-muted-foreground leading-relaxed border-t border-border/60 pt-3">
                {{ t('home.faq4A') }}
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 7: Grounded Bottom Callout (No Glows, No Slop) -->
    <section class="py-12 sm:py-16">
      <div class="container max-w-4xl px-4 sm:px-6">
        <div class="rounded-2xl border border-border bg-card p-6 sm:p-10 text-center shadow-xs space-y-5">
          <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Leaf class="h-6 w-6" />
          </div>

          <div class="space-y-2">
            <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
              {{ t('home.bottomCtaTitle') }}
            </h2>
            <p class="mx-auto max-w-xl text-xs sm:text-sm text-muted-foreground leading-relaxed">
              {{ t('home.bottomCtaDesc') }}
            </p>
          </div>

          <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3 pt-2">
            <RouterLink v-if="auth.isAuthenticated" to="/reports/new" class="w-full sm:w-auto">
              <Button size="lg" class="h-11 w-full px-6 gap-2 text-sm font-semibold">
                {{ t('home.ctaSubmit') }}
                <ArrowRight class="h-4 w-4" />
              </Button>
            </RouterLink>
            <RouterLink v-else to="/register" class="w-full sm:w-auto">
              <Button size="lg" class="h-11 w-full px-6 gap-2 text-sm font-semibold">
                {{ t('home.ctaStart') }}
                <ArrowRight class="h-4 w-4" />
              </Button>
            </RouterLink>

            <RouterLink v-if="!auth.isAuthenticated" to="/login" class="w-full sm:w-auto">
              <Button variant="outline" size="lg" class="h-11 w-full px-6 text-sm font-medium">
                {{ t('nav.signIn') }}
              </Button>
            </RouterLink>
          </div>

          <!-- Quick Evaluator Access -->
          <div v-if="!auth.isAuthenticated" class="pt-4 border-t border-border/60">
            <p class="text-[11px] font-semibold text-muted-foreground mb-2">
              {{ t('home.tryDemo') }}:
            </p>
            <div class="flex flex-wrap items-center justify-center gap-2">
              <button
                type="button"
                class="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted/40 px-3 py-1.5 text-xs font-medium text-foreground transition hover:border-primary hover:text-primary"
                @click="quickLoginDemo('resident')"
              >
                <FileText class="h-3 w-3 text-primary" />
                Resident Portal Demo
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted/40 px-3 py-1.5 text-xs font-medium text-foreground transition hover:border-primary hover:text-primary"
                @click="quickLoginDemo('admin')"
              >
                <ShieldCheck class="h-3 w-3 text-primary" />
                Admin Console Demo
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </AppLayout>
</template>
