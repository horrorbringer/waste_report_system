<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Leaf,
  Camera,
  ClipboardCheck,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Clock,
  TrendingUp,
  Sparkles,
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
  ExternalLink,
  Navigation,
  Compass,
  Users,
  Map,
  Star,
  BarChart3,
  Radio,
  FileText,
  ChevronDown,
  Info,
  Building2,
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

const { t, locale } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const reportStore = useReportStore()
const categoryStore = useCategoryStore()

const activeFaq = ref<number | null>(0)

onMounted(async () => {
  reportStore.fetchPublicStats().catch(() => {})
  categoryStore.fetchCategories().catch(() => {})
})

// Calculate resolution rate
const resolutionPercent = computed(() => {
  const stats = reportStore.publicStats
  if (!stats || !stats.total_reports || stats.total_reports === 0) return 84
  const rate = Math.round((stats.resolved_reports / stats.total_reports) * 100)
  return Math.max(1, Math.min(100, rate))
})

// Calculate progress ratios for segmented pipeline
const pipelineRatios = computed(() => {
  const stats = reportStore.publicStats
  const total = stats?.total_reports || 10
  const resolved = stats?.resolved_reports ?? 7
  const inProgress = stats?.in_progress_reports ?? 2
  const pending = stats?.pending_reports ?? 1

  return {
    resolvedPct: Math.round((resolved / total) * 100),
    inProgressPct: Math.round((inProgress / total) * 100),
    pendingPct: Math.round((pending / total) * 100),
  }
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
      badge: 'border-sky-500/30 text-sky-600 bg-sky-500/10',
      hoverBorder: 'hover:border-sky-500/50',
    }
  }
  if (n.includes('organic') || n.includes('food')) {
    return {
      bg: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
      badge: 'border-emerald-500/30 text-emerald-600 bg-emerald-500/10',
      hoverBorder: 'hover:border-emerald-500/50',
    }
  }
  if (n.includes('overflow') || n.includes('bin')) {
    return {
      bg: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
      badge: 'border-amber-500/30 text-amber-600 bg-amber-500/10',
      hoverBorder: 'hover:border-amber-500/50',
    }
  }
  if (n.includes('construct') || n.includes('debris')) {
    return {
      bg: 'bg-slate-500/10 text-slate-700 dark:text-slate-300',
      badge: 'border-slate-500/30 text-slate-700 bg-slate-500/10',
      hoverBorder: 'hover:border-slate-500/50',
    }
  }
  if (n.includes('electro')) {
    return {
      bg: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
      badge: 'border-violet-500/30 text-violet-600 bg-violet-500/10',
      hoverBorder: 'hover:border-violet-500/50',
    }
  }
  if (n.includes('hazard')) {
    return {
      bg: 'bg-rose-500/10 text-rose-600 dark:text-rose-400',
      badge: 'border-rose-500/30 text-rose-600 bg-rose-500/10',
      hoverBorder: 'hover:border-rose-500/50',
    }
  }
  return {
    bg: 'bg-primary/10 text-primary',
    badge: 'border-primary/30 text-primary bg-primary/10',
    hoverBorder: 'hover:border-primary/50',
  }
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
  }
}
</script>

<template>
  <AppLayout>
    <!-- SECTION 1: Modern Split Hero with Civic Incident Showcase -->
    <section class="relative overflow-hidden border-b bg-gradient-to-b from-primary/[0.07] via-background/60 to-background pt-8 pb-12 sm:pt-12 sm:pb-16 md:pt-16 md:pb-24">
      <!-- Ambient decorative gradient orbs -->
      <div class="pointer-events-none absolute -top-24 left-1/2 -z-10 h-96 w-96 -translate-x-1/2 rounded-full bg-primary/15 blur-3xl" />
      <div class="pointer-events-none absolute top-48 right-10 -z-10 h-80 w-80 rounded-full bg-emerald-500/10 blur-3xl" />

      <div class="container px-4 sm:px-6">
        <div class="grid items-center gap-8 sm:gap-12 lg:grid-cols-12 lg:gap-8">
          <!-- Left Column: Copy & Actions -->
          <div class="space-y-4 sm:space-y-6 text-center lg:col-span-7 lg:text-left">
            <div class="flex flex-wrap items-center justify-center gap-2 lg:justify-start">
              <Badge variant="outline" class="gap-1.5 border-primary/30 bg-primary/10 px-3 py-1 text-[10px] sm:text-[11px] font-semibold tracking-wider text-primary shadow-sm">
                <Leaf class="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                {{ t('home.badge') }}
              </Badge>
              <Badge variant="outline" class="hidden sm:inline-flex gap-1 border-emerald-500/30 bg-emerald-500/5 px-2.5 py-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                <Building2 class="h-3 w-3" />
                Phnom Penh Municipality
              </Badge>
            </div>

            <h1 class="font-display text-3xl sm:text-5xl md:text-6xl font-black leading-tight sm:leading-[1.15] tracking-tight break-words">
              {{ t('home.heroLine1') }}
              <span class="mt-1 block bg-gradient-to-r from-emerald-600 via-primary to-teal-500 bg-clip-text text-transparent">
                {{ t('home.heroLine2') }}
              </span>
            </h1>

            <p class="mx-auto max-w-2xl text-xs sm:text-base leading-relaxed text-muted-foreground lg:mx-0">
              {{ t('home.heroDesc') }}
            </p>

            <!-- Action Buttons -->
            <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-2.5 sm:gap-3 pt-1 sm:pt-2 lg:justify-start">
              <RouterLink v-if="auth.isAuthenticated" to="/reports/new" class="w-full sm:w-auto">
                <Button size="lg" class="h-11 sm:h-12 w-full px-5 sm:px-6 gap-2 text-xs sm:text-sm font-semibold shadow-lg shadow-primary/20 transition-all hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5">
                  {{ t('home.ctaSubmit') }}
                  <ArrowRight class="h-4 w-4" />
                </Button>
              </RouterLink>
              <RouterLink v-else to="/register" class="w-full sm:w-auto">
                <Button size="lg" class="h-11 sm:h-12 w-full px-5 sm:px-6 gap-2 text-xs sm:text-sm font-semibold shadow-lg shadow-primary/20 transition-all hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5">
                  {{ t('home.ctaStart') }}
                  <ArrowRight class="h-4 w-4" />
                </Button>
              </RouterLink>

              <RouterLink v-if="auth.isAdmin" to="/admin/dashboard" class="w-full sm:w-auto">
                <Button variant="outline" size="lg" class="h-11 sm:h-12 w-full px-5 gap-2 text-xs sm:text-sm font-medium">
                  <ShieldCheck class="h-4 w-4 text-primary" />
                  {{ t('home.ctaAdmin') }}
                </Button>
              </RouterLink>
              <RouterLink v-else-if="auth.isAuthenticated" to="/my-reports" class="w-full sm:w-auto">
                <Button variant="outline" size="lg" class="h-11 sm:h-12 w-full px-5 gap-2 text-xs sm:text-sm font-medium">
                  <FileText class="h-4 w-4" />
                  {{ t('home.ctaMyReports') }}
                </Button>
              </RouterLink>
              <RouterLink v-else to="/login" class="w-full sm:w-auto">
                <Button variant="outline" size="lg" class="h-11 sm:h-12 w-full px-5 text-xs sm:text-sm font-medium">
                  {{ t('nav.signIn') }}
                </Button>
              </RouterLink>
            </div>

            <!-- Micro Trust Badges Row -->
            <div class="pt-2 flex flex-wrap items-center justify-center gap-x-4 sm:gap-x-6 gap-y-2 text-[11px] sm:text-xs text-muted-foreground lg:justify-start">
              <div class="flex items-center gap-1.5 font-medium">
                <MapPin class="h-3.5 w-3.5 text-primary shrink-0" />
                <span>{{ t('home.heroTrustGps') }}</span>
              </div>
              <div class="flex items-center gap-1.5 font-medium">
                <Clock class="h-3.5 w-3.5 text-primary shrink-0" />
                <span>{{ t('home.heroTrustResponse') }}</span>
              </div>
              <div class="flex items-center gap-1.5 font-medium">
                <Sparkles class="h-3.5 w-3.5 text-primary shrink-0" />
                <span>{{ t('home.heroTrustBilingual') }}</span>
              </div>
            </div>
          </div>

          <!-- Right Column: Interactive Live Civic Incident Preview Card -->
          <div class="relative mx-auto w-full max-w-md lg:col-span-5">
            <!-- Glow background -->
            <div class="absolute -inset-1 rounded-3xl bg-gradient-to-tr from-primary/30 via-emerald-500/20 to-teal-500/10 blur-xl opacity-75" />

            <Card class="relative border-border/80 bg-card/95 shadow-2xl backdrop-blur-md rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-primary/10">
              <!-- Live Incident Ribbon Header -->
              <div class="flex items-center justify-between border-b bg-muted/40 px-4 py-2.5 text-xs">
                <div class="flex items-center gap-2">
                  <span class="relative flex h-2 w-2">
                    <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                    <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                  </span>
                  <span class="font-semibold text-foreground">{{ t('home.livePreviewBadge') }} #108</span>
                </div>
                <Badge variant="outline" class="gap-1 border-blue-500/30 bg-blue-500/10 text-[10px] font-semibold text-blue-600 dark:text-blue-400">
                  <Radio class="h-2.5 w-2.5 animate-pulse" />
                  {{ t('home.livePreviewStatus') }}
                </Badge>
              </div>

              <!-- Incident Visual Card Body -->
              <CardContent class="p-5 space-y-4">
                <!-- Mock Incident Header & Badge -->
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <h3 class="font-semibold text-base text-foreground leading-snug">
                      {{ t('home.livePreviewTitle') }}
                    </h3>
                    <p class="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                      <MapPin class="h-3.5 w-3.5 text-primary shrink-0" />
                      <span>{{ t('home.livePreviewLocation') }}</span>
                    </p>
                  </div>
                  <Badge variant="secondary" class="shrink-0 gap-1 text-[11px] font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                    <Trash2 class="h-3 w-3" />
                    Overflow
                  </Badge>
                </div>

                <!-- Realistic Report Map & Geotag Banner -->
                <div class="relative h-32 w-full overflow-hidden rounded-xl border border-border/60 bg-slate-900/10 dark:bg-slate-900/60 flex items-center justify-center">
                  <!-- Simulated Map Visual Texture -->
                  <div class="absolute inset-0 opacity-40 bg-[radial-gradient(#10b981_1px,transparent_1px)] [background-size:12px_12px]" />
                  <div class="relative z-10 flex flex-col items-center gap-1 text-center p-3">
                    <div class="flex h-8 w-8 items-center justify-center rounded-full bg-red-500 text-white shadow-lg animate-bounce">
                      <MapPin class="h-4 w-4" />
                    </div>
                    <Badge variant="outline" class="font-mono text-[10px] bg-background/90 backdrop-blur-sm border-border/80">
                      11.5696° N, 104.9211° E (GPS Verified)
                    </Badge>
                  </div>

                  <!-- Floating micro tag -->
                  <div class="absolute bottom-2 left-2 z-10">
                    <Badge variant="secondary" class="bg-background/90 text-[10px] font-medium backdrop-blur-sm shadow-sm gap-1">
                      <Camera class="h-2.5 w-2.5 text-primary" />
                      Photo Attached
                    </Badge>
                  </div>
                </div>

                <!-- 3-Stage Resolution Progress Tracker -->
                <div class="space-y-2 pt-1">
                  <div class="flex items-center justify-between text-[11px] font-medium text-muted-foreground">
                    <span class="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                      <CheckCircle2 class="h-3 w-3" />
                      {{ t('home.livePreviewStep1') }}
                    </span>
                    <span class="text-blue-600 dark:text-blue-400 font-semibold flex items-center gap-1">
                      <Clock class="h-3 w-3" />
                      {{ t('home.livePreviewStep2') }}
                    </span>
                    <span class="text-primary font-bold flex items-center gap-1">
                      <Navigation class="h-3 w-3 animate-spin" />
                      {{ t('home.livePreviewStep3') }}
                    </span>
                  </div>
                  <!-- Multi-segmented track -->
                  <div class="h-1.5 w-full rounded-full bg-muted overflow-hidden flex">
                    <div class="h-full bg-emerald-500 w-[45%]" />
                    <div class="h-full bg-blue-500 w-[30%]" />
                    <div class="h-full bg-primary/40 w-[25%]" />
                  </div>
                </div>

                <!-- Card Quick Actions -->
                <div class="flex items-center justify-between border-t pt-3 text-xs">
                  <span class="text-muted-foreground text-[11px]">Average resolution: <strong>3.2 hours</strong></span>
                  <RouterLink to="/reports/9" class="inline-flex items-center gap-1 font-semibold text-primary hover:underline">
                    View incident
                    <ChevronRight class="h-3 w-3" />
                  </RouterLink>
                </div>
              </CardContent>
            </Card>

            <!-- Floating Micro Accent Badges -->
            <div class="absolute -bottom-4 -left-4 hidden sm:flex items-center gap-2 rounded-xl border bg-background/95 px-3 py-2 shadow-lg backdrop-blur-md">
              <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600">
                <CheckCircle2 class="h-4 w-4" />
              </div>
              <div class="text-[11px]">
                <p class="font-bold text-foreground">84% Cleaned</p>
                <p class="text-muted-foreground">Community Rate</p>
              </div>
            </div>

            <div class="absolute -top-3 -right-3 hidden sm:flex items-center gap-2 rounded-xl border bg-background/95 px-3 py-2 shadow-lg backdrop-blur-md">
              <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <TrendingUp class="h-4 w-4" />
              </div>
              <div class="text-[11px]">
                <p class="font-bold text-foreground">Fast Dispatch</p>
                <p class="text-muted-foreground">Direct City Hall link</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 2: Community Impact Dashboard & Resolution Pipeline -->
    <section class="border-b bg-card/40 py-8 sm:py-10">
      <div class="container px-4 sm:px-6 space-y-6 sm:space-y-8">
        <!-- 4 KPI Cards -->
        <div class="grid grid-cols-2 gap-2.5 sm:gap-4 lg:grid-cols-4">
          <Card class="border-border/60 shadow-sm transition hover:border-primary/40 hover:shadow-md">
            <CardContent class="p-3.5 sm:p-5">
              <div class="flex items-center justify-between">
                <p class="text-[10px] sm:text-xs font-semibold uppercase tracking-wider text-muted-foreground truncate">
                  {{ t('home.statTotal') }}
                </p>
                <div class="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-lg bg-primary/10 text-primary shrink-0">
                  <TrendingUp class="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                </div>
              </div>
              <p class="mt-1.5 sm:mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
                {{ reportStore.publicStats?.total_reports ?? '12' }}
              </p>
              <p class="mt-0.5 sm:mt-1 text-[10px] sm:text-[11px] text-muted-foreground truncate">Across all districts</p>
            </CardContent>
          </Card>

          <Card class="border-border/60 shadow-sm transition hover:border-amber-500/40 hover:shadow-md">
            <CardContent class="p-3.5 sm:p-5">
              <div class="flex items-center justify-between">
                <p class="text-[10px] sm:text-xs font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400 truncate">
                  {{ t('home.statPending') }}
                </p>
                <div class="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 shrink-0">
                  <Clock class="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                </div>
              </div>
              <p class="mt-1.5 sm:mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-amber-600 dark:text-amber-400">
                {{ reportStore.publicStats?.pending_reports ?? '2' }}
              </p>
              <p class="mt-0.5 sm:mt-1 text-[10px] sm:text-[11px] text-muted-foreground truncate">Awaiting triage</p>
            </CardContent>
          </Card>

          <Card class="border-border/60 shadow-sm transition hover:border-blue-500/40 hover:shadow-md">
            <CardContent class="p-3.5 sm:p-5">
              <div class="flex items-center justify-between">
                <p class="text-[10px] sm:text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400 truncate">
                  {{ t('home.statInProgress') }}
                </p>
                <div class="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 shrink-0">
                  <Radio class="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                </div>
              </div>
              <p class="mt-1.5 sm:mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-blue-600 dark:text-blue-400">
                {{ reportStore.publicStats?.in_progress_reports ?? '3' }}
              </p>
              <p class="mt-0.5 sm:mt-1 text-[10px] sm:text-[11px] text-muted-foreground truncate">Crew assigned</p>
            </CardContent>
          </Card>

          <Card class="border-border/60 shadow-sm transition hover:border-emerald-500/40 hover:shadow-md">
            <CardContent class="p-3.5 sm:p-5">
              <div class="flex items-center justify-between">
                <p class="text-[10px] sm:text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 truncate">
                  {{ t('home.statResolved') }}
                </p>
                <div class="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 shrink-0">
                  <CheckCircle2 class="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                </div>
              </div>
              <p class="mt-1.5 sm:mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-emerald-600 dark:text-emerald-400">
                {{ reportStore.publicStats?.resolved_reports ?? '7' }}
              </p>
              <p class="mt-0.5 sm:mt-1 text-[10px] sm:text-[11px] text-muted-foreground truncate">Cleaned & verified</p>
            </CardContent>
          </Card>
        </div>

        <!-- Resolution Pipeline Bar Banner -->
        <div class="rounded-2xl border bg-card p-4 sm:p-5 shadow-sm space-y-2.5 sm:space-y-3">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <p class="text-xs font-bold uppercase tracking-wider text-primary">
                {{ t('home.resolutionRate') }}
              </p>
              <p class="text-[11px] sm:text-xs text-muted-foreground">
                {{ t('home.resolutionRateDesc', { percent: resolutionPercent }) }}
              </p>
            </div>
            <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] sm:text-xs font-medium">
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

          <!-- Segmented Progress Bar -->
          <div class="h-3 w-full rounded-full bg-muted overflow-hidden flex">
            <div
              class="h-full bg-emerald-500 transition-all duration-500"
              :style="{ width: `${pipelineRatios.resolvedPct}%` }"
              title="Resolved"
            />
            <div
              class="h-full bg-blue-500 transition-all duration-500"
              :style="{ width: `${pipelineRatios.inProgressPct}%` }"
              title="In Progress"
            />
            <div
              class="h-full bg-amber-500 transition-all duration-500"
              :style="{ width: `${pipelineRatios.pendingPct}%` }"
              title="Pending"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 3: Waste Category Explorer ("What Can You Report?") -->
    <section class="py-16 bg-muted/20 border-b">
      <div class="container space-y-10">
        <div class="mx-auto max-w-2xl text-center space-y-2">
          <Badge variant="outline" class="gap-1 border-primary/30 text-primary bg-primary/5 text-xs font-semibold uppercase tracking-wider">
            <Layers class="h-3.5 w-3.5" />
            {{ t('home.categoriesEyebrow') }}
          </Badge>
          <h2 class="text-3xl font-extrabold tracking-tight sm:text-4xl text-foreground">
            {{ t('home.categoriesTitle') }}
          </h2>
          <p class="text-sm sm:text-base text-muted-foreground leading-relaxed">
            {{ t('home.categoriesDesc') }}
          </p>
        </div>

        <!-- Categories Grid -->
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="cat in categoryStore.categories"
            :key="cat.id"
            class="group relative flex flex-col justify-between rounded-2xl border bg-card p-5 shadow-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer"
            :class="getCategoryTheme(cat.name).hoverBorder"
            @click="handleCategoryClick(cat)"
          >
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex h-11 w-11 items-center justify-center rounded-xl transition group-hover:scale-105" :class="getCategoryTheme(cat.name).bg">
                  <component :is="getCategoryIcon(cat.name)" class="h-5 w-5" />
                </div>
                <Badge variant="outline" class="text-[10px] font-medium" :class="getCategoryTheme(cat.name).badge">
                  Category #{{ cat.id }}
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

            <div class="mt-5 pt-3 border-t flex items-center justify-between text-xs font-semibold text-primary">
              <span>{{ t('home.reportThisCategory') }}</span>
              <ArrowRight class="h-3.5 w-3.5 transition group-hover:translate-x-1" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 4: 3-Stage Civic Workflow ("How Community Reporting Works") -->
    <section class="py-16 md:py-20 border-b">
      <div class="container space-y-12">
        <div class="mx-auto max-w-2xl text-center space-y-2">
          <Badge variant="outline" class="gap-1 border-primary/30 text-primary bg-primary/5 text-xs font-semibold uppercase tracking-wider">
            <Navigation class="h-3.5 w-3.5" />
            {{ t('home.workflowEyebrow') }}
          </Badge>
          <h2 class="text-3xl font-extrabold tracking-tight sm:text-4xl text-foreground">
            {{ t('home.workflowTitle') }}
          </h2>
          <p class="text-sm sm:text-base text-muted-foreground leading-relaxed">
            {{ t('home.workflowDesc') }}
          </p>
        </div>

        <!-- 3 Step Cards with Connectors -->
        <div class="grid gap-6 md:grid-cols-3">
          <!-- Step 1 -->
          <Card class="relative border-border/70 shadow-sm transition hover:shadow-md">
            <CardHeader class="pb-3">
              <div class="flex items-center justify-between mb-2">
                <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-sm font-black text-primary-foreground shadow-md">
                  1
                </span>
                <Badge variant="outline" class="gap-1 text-[11px] font-medium text-primary">
                  <Camera class="h-3 w-3" />
                  Resident
                </Badge>
              </div>
              <CardTitle class="text-lg font-bold">{{ t('home.step1Title') }}</CardTitle>
              <CardDescription class="text-xs leading-relaxed mt-1">
                {{ t('home.step1Desc') }}
              </CardDescription>
            </CardHeader>
            <CardContent class="text-xs text-muted-foreground space-y-1.5 pt-1">
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-primary stroke-[3]" />
                <span>Google Map & GPS Pinpoint</span>
              </div>
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-primary stroke-[3]" />
                <span>Instant Photo Capture & Upload</span>
              </div>
            </CardContent>
          </Card>

          <!-- Step 2 -->
          <Card class="relative border-border/70 shadow-sm transition hover:shadow-md">
            <CardHeader class="pb-3">
              <div class="flex items-center justify-between mb-2">
                <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-sm font-black text-white shadow-md">
                  2
                </span>
                <Badge variant="outline" class="gap-1 text-[11px] font-medium text-blue-600 border-blue-500/30 bg-blue-500/5">
                  <Building2 class="h-3 w-3" />
                  City Hall
                </Badge>
              </div>
              <CardTitle class="text-lg font-bold">{{ t('home.step2Title') }}</CardTitle>
              <CardDescription class="text-xs leading-relaxed mt-1">
                {{ t('home.step2Desc') }}
              </CardDescription>
            </CardHeader>
            <CardContent class="text-xs text-muted-foreground space-y-1.5 pt-1">
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-blue-600 stroke-[3]" />
                <span>Urgency Triage & Route Planning</span>
              </div>
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-blue-600 stroke-[3]" />
                <span>Sanitation Truck Dispatch</span>
              </div>
            </CardContent>
          </Card>

          <!-- Step 3 -->
          <Card class="relative border-border/70 shadow-sm transition hover:shadow-md">
            <CardHeader class="pb-3">
              <div class="flex items-center justify-between mb-2">
                <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-600 text-sm font-black text-white shadow-md">
                  3
                </span>
                <Badge variant="outline" class="gap-1 text-[11px] font-medium text-emerald-600 border-emerald-500/30 bg-emerald-500/5">
                  <CheckCircle2 class="h-3 w-3" />
                  Community
                </Badge>
              </div>
              <CardTitle class="text-lg font-bold">{{ t('home.step3Title') }}</CardTitle>
              <CardDescription class="text-xs leading-relaxed mt-1">
                {{ t('home.step3Desc') }}
              </CardDescription>
            </CardHeader>
            <CardContent class="text-xs text-muted-foreground space-y-1.5 pt-1">
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-emerald-600 stroke-[3]" />
                <span>Cleaned Site & Status Resolved</span>
              </div>
              <div class="flex items-center gap-2">
                <Check class="h-3.5 w-3.5 text-emerald-600 stroke-[3]" />
                <span>Timestamped Audit History</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>

    <!-- SECTION 5: Civic Pillars of Trust ("Why EcoWatch?") -->
    <section class="py-16 bg-muted/20 border-b">
      <div class="container space-y-10">
        <div class="mx-auto max-w-2xl text-center space-y-2">
          <Badge variant="outline" class="gap-1 border-primary/30 text-primary bg-primary/5 text-xs font-semibold uppercase tracking-wider">
            <ShieldCheck class="h-3.5 w-3.5" />
            {{ t('home.pillarsEyebrow') }}
          </Badge>
          <h2 class="text-3xl font-extrabold tracking-tight sm:text-4xl text-foreground">
            {{ t('home.pillarsTitle') }}
          </h2>
        </div>

        <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <!-- Pillar 1 -->
          <Card class="border-border/60 shadow-sm transition hover:shadow-md">
            <CardContent class="p-6 space-y-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Compass class="h-5 w-5" />
              </div>
              <h3 class="font-bold text-base text-foreground">{{ t('home.pillar1Title') }}</h3>
              <p class="text-xs text-muted-foreground leading-relaxed">{{ t('home.pillar1Desc') }}</p>
            </CardContent>
          </Card>

          <!-- Pillar 2 -->
          <Card class="border-border/60 shadow-sm transition hover:shadow-md">
            <CardContent class="p-6 space-y-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-600">
                <Clock class="h-5 w-5" />
              </div>
              <h3 class="font-bold text-base text-foreground">{{ t('home.pillar2Title') }}</h3>
              <p class="text-xs text-muted-foreground leading-relaxed">{{ t('home.pillar2Desc') }}</p>
            </CardContent>
          </Card>

          <!-- Pillar 3 -->
          <Card class="border-border/60 shadow-sm transition hover:shadow-md">
            <CardContent class="p-6 space-y-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600">
                <Users class="h-5 w-5" />
              </div>
              <h3 class="font-bold text-base text-foreground">{{ t('home.pillar3Title') }}</h3>
              <p class="text-xs text-muted-foreground leading-relaxed">{{ t('home.pillar3Desc') }}</p>
            </CardContent>
          </Card>

          <!-- Pillar 4 -->
          <Card class="border-border/60 shadow-sm transition hover:shadow-md">
            <CardContent class="p-6 space-y-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/10 text-purple-600">
                <ShieldCheck class="h-5 w-5" />
              </div>
              <h3 class="font-bold text-base text-foreground">{{ t('home.pillar4Title') }}</h3>
              <p class="text-xs text-muted-foreground leading-relaxed">{{ t('home.pillar4Desc') }}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>

    <!-- SECTION 6: Resident Guidance & Interactive FAQ -->
    <section class="py-16 border-b">
      <div class="container max-w-3xl space-y-8">
        <div class="text-center space-y-2">
          <Badge variant="outline" class="gap-1 border-primary/30 text-primary bg-primary/5 text-xs font-semibold uppercase tracking-wider">
            <HelpCircle class="h-3.5 w-3.5" />
            {{ t('home.faqEyebrow') }}
          </Badge>
          <h2 class="text-3xl font-extrabold tracking-tight sm:text-4xl text-foreground">
            {{ t('home.faqTitle') }}
          </h2>
        </div>

        <div class="space-y-3">
          <!-- FAQ 1 -->
          <div class="rounded-2xl border bg-card transition shadow-sm overflow-hidden">
            <button
              type="button"
              class="flex w-full items-center justify-between p-5 text-left text-sm sm:text-base font-semibold text-foreground hover:bg-muted/30 transition"
              @click="toggleFaq(0)"
            >
              <span>{{ t('home.faq1Q') }}</span>
              <ChevronDown class="h-4 w-4 shrink-0 transition-transform duration-200" :class="{ 'rotate-180': activeFaq === 0 }" />
            </button>
            <div v-show="activeFaq === 0" class="px-5 pb-5 text-xs sm:text-sm text-muted-foreground leading-relaxed border-t pt-3">
              {{ t('home.faq1A') }}
            </div>
          </div>

          <!-- FAQ 2 -->
          <div class="rounded-2xl border bg-card transition shadow-sm overflow-hidden">
            <button
              type="button"
              class="flex w-full items-center justify-between p-5 text-left text-sm sm:text-base font-semibold text-foreground hover:bg-muted/30 transition"
              @click="toggleFaq(1)"
            >
              <span>{{ t('home.faq2Q') }}</span>
              <ChevronDown class="h-4 w-4 shrink-0 transition-transform duration-200" :class="{ 'rotate-180': activeFaq === 1 }" />
            </button>
            <div v-show="activeFaq === 1" class="px-5 pb-5 text-xs sm:text-sm text-muted-foreground leading-relaxed border-t pt-3">
              {{ t('home.faq2A') }}
            </div>
          </div>

          <!-- FAQ 3 -->
          <div class="rounded-2xl border bg-card transition shadow-sm overflow-hidden">
            <button
              type="button"
              class="flex w-full items-center justify-between p-5 text-left text-sm sm:text-base font-semibold text-foreground hover:bg-muted/30 transition"
              @click="toggleFaq(2)"
            >
              <span>{{ t('home.faq3Q') }}</span>
              <ChevronDown class="h-4 w-4 shrink-0 transition-transform duration-200" :class="{ 'rotate-180': activeFaq === 2 }" />
            </button>
            <div v-show="activeFaq === 2" class="px-5 pb-5 text-xs sm:text-sm text-muted-foreground leading-relaxed border-t pt-3">
              {{ t('home.faq3A') }}
            </div>
          </div>

          <!-- FAQ 4 -->
          <div class="rounded-2xl border bg-card transition shadow-sm overflow-hidden">
            <button
              type="button"
              class="flex w-full items-center justify-between p-5 text-left text-sm sm:text-base font-semibold text-foreground hover:bg-muted/30 transition"
              @click="toggleFaq(3)"
            >
              <span>{{ t('home.faq4Q') }}</span>
              <ChevronDown class="h-4 w-4 shrink-0 transition-transform duration-200" :class="{ 'rotate-180': activeFaq === 3 }" />
            </button>
            <div v-show="activeFaq === 3" class="px-5 pb-5 text-xs sm:text-sm text-muted-foreground leading-relaxed border-t pt-3">
              {{ t('home.faq4A') }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 7: High-Impact Bottom Call to Action & Quick Demo Fill -->
    <section class="py-16 md:py-24">
      <div class="container max-w-4xl">
        <div class="relative overflow-hidden rounded-3xl border border-primary/25 bg-gradient-to-tr from-primary/15 via-primary/5 to-teal-500/10 p-8 sm:p-12 text-center shadow-xl">
          <!-- Background decorative shapes -->
          <div class="pointer-events-none absolute -top-12 -right-12 h-48 w-48 rounded-full bg-primary/20 blur-2xl" />
          <div class="pointer-events-none absolute -bottom-12 -left-12 h-48 w-48 rounded-full bg-emerald-500/20 blur-2xl" />

          <div class="relative z-10 space-y-6">
            <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/30">
              <Leaf class="h-7 w-7" />
            </div>

            <h2 class="text-3xl font-black tracking-tight sm:text-4xl text-foreground">
              {{ t('home.bottomCtaTitle') }}
            </h2>

            <p class="mx-auto max-w-xl text-sm sm:text-base text-muted-foreground leading-relaxed">
              {{ t('home.bottomCtaDesc') }}
            </p>

            <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-2.5 sm:gap-3 pt-2">
              <RouterLink v-if="auth.isAuthenticated" to="/reports/new" class="w-full sm:w-auto">
                <Button size="lg" class="h-11 sm:h-12 w-full px-6 sm:px-7 gap-2 font-semibold shadow-lg shadow-primary/25 hover:shadow-xl hover:-translate-y-0.5 transition">
                  {{ t('home.ctaSubmit') }}
                  <ArrowRight class="h-4 w-4" />
                </Button>
              </RouterLink>
              <RouterLink v-else to="/register" class="w-full sm:w-auto">
                <Button size="lg" class="h-11 sm:h-12 w-full px-6 sm:px-7 gap-2 font-semibold shadow-lg shadow-primary/25 hover:shadow-xl hover:-translate-y-0.5 transition">
                  {{ t('home.ctaStart') }}
                  <ArrowRight class="h-4 w-4" />
                </Button>
              </RouterLink>

              <RouterLink v-if="!auth.isAuthenticated" to="/login" class="w-full sm:w-auto">
                <Button variant="outline" size="lg" class="h-11 sm:h-12 w-full px-6">
                  {{ t('nav.signIn') }}
                </Button>
              </RouterLink>
            </div>

            <!-- Quick Demo One-Click Access (When unauthenticated) -->
            <div v-if="!auth.isAuthenticated" class="pt-5 sm:pt-6 border-t border-border/60">
              <p class="text-xs font-semibold text-muted-foreground mb-2">
                {{ t('home.tryDemo') }} (One-click instant login):
              </p>
              <div class="flex flex-wrap items-center justify-center gap-2">
                <button
                  type="button"
                  class="inline-flex items-center gap-1.5 rounded-lg border bg-background/80 px-3 py-1.5 text-xs font-medium text-foreground transition hover:border-primary hover:text-primary shadow-sm"
                  @click="quickLoginDemo('resident')"
                >
                  <Users class="h-3.5 w-3.5 text-primary" />
                  Resident Demo
                </button>
                <button
                  type="button"
                  class="inline-flex items-center gap-1.5 rounded-lg border bg-background/80 px-3 py-1.5 text-xs font-medium text-foreground transition hover:border-primary hover:text-primary shadow-sm"
                  @click="quickLoginDemo('admin')"
                >
                  <ShieldCheck class="h-3.5 w-3.5 text-primary" />
                  Admin Demo
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </AppLayout>
</template>
