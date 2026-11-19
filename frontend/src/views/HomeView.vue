<script setup lang="ts">
import { onMounted } from 'vue'
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
} from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { useReportStore } from '@/stores/reports'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const { t } = useI18n()
const auth = useAuthStore()
const reportStore = useReportStore()

onMounted(() => {
  reportStore.fetchPublicStats().catch(() => {})
})
</script>

<template>
  <AppLayout>
    <!-- Hero Section -->
    <section class="relative overflow-hidden border-b bg-gradient-to-b from-primary/5 via-background to-background py-16 md:py-24">
      <div class="container">
        <div class="mx-auto max-w-3xl text-center">
          <Badge variant="outline" class="mb-5 gap-1.5 border-primary/25 bg-primary/5 px-3.5 py-1 text-[11px] font-semibold tracking-[0.14em] text-primary">
            <Leaf class="h-3.5 w-3.5" />
            {{ t('home.badge') }}
          </Badge>
          <h1 class="font-display text-4xl font-extrabold leading-[1.12] tracking-[-0.035em] sm:text-5xl md:text-[3.5rem]">
            {{ t('home.heroLine1') }}
            <span class="mt-1 block bg-gradient-to-r from-emerald-700 via-primary to-teal-600 bg-clip-text text-transparent">
              {{ t('home.heroLine2') }}
            </span>
          </h1>
          <p class="text-lead mx-auto mt-6 max-w-2xl">
            {{ t('home.heroDesc') }}
          </p>

          <div class="mt-8 flex flex-wrap items-center justify-center gap-3">
            <RouterLink v-if="auth.isAuthenticated" to="/reports/new">
              <Button size="lg" class="gap-2">
                {{ t('home.ctaSubmit') }}
                <ArrowRight class="h-4 w-4" />
              </Button>
            </RouterLink>
            <RouterLink v-else to="/register">
              <Button size="lg" class="gap-2">
                {{ t('home.ctaStart') }}
                <ArrowRight class="h-4 w-4" />
              </Button>
            </RouterLink>

            <RouterLink v-if="auth.isAdmin" to="/admin/dashboard">
              <Button variant="outline" size="lg" class="gap-2">
                <ShieldCheck class="h-4 w-4" />
                {{ t('home.ctaAdmin') }}
              </Button>
            </RouterLink>
            <RouterLink v-else-if="auth.isAuthenticated" to="/my-reports">
              <Button variant="outline" size="lg">{{ t('home.ctaMyReports') }}</Button>
            </RouterLink>
            <RouterLink v-else to="/login">
              <Button variant="outline" size="lg">{{ t('nav.signIn') }}</Button>
            </RouterLink>
          </div>
        </div>

        <!-- Live Community Impact Stats -->
        <div class="mx-auto mt-14 grid max-w-4xl grid-cols-2 gap-4 md:grid-cols-4">
          <Card>
            <CardContent class="p-5 text-center">
              <p class="text-eyebrow">{{ t('home.statTotal') }}</p>
              <p class="text-kpi mt-2.5">{{ reportStore.publicStats?.total_reports ?? '—' }}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent class="p-5 text-center">
              <p class="text-eyebrow text-amber-600">{{ t('home.statPending') }}</p>
              <p class="text-kpi mt-2.5 text-amber-600">
                {{ reportStore.publicStats?.pending_reports ?? '—' }}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent class="p-5 text-center">
              <p class="text-eyebrow text-blue-600">{{ t('home.statInProgress') }}</p>
              <p class="text-kpi mt-2.5 text-blue-600">
                {{ reportStore.publicStats?.in_progress_reports ?? '—' }}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent class="p-5 text-center">
              <p class="text-eyebrow text-emerald-600">{{ t('home.statResolved') }}</p>
              <p class="text-kpi mt-2.5 text-emerald-600">
                {{ reportStore.publicStats?.resolved_reports ?? '—' }}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>

    <!-- How It Works -->
    <section class="py-16">
      <div class="container">
        <div class="mx-auto mb-10 max-w-2xl text-center">
          <p class="text-eyebrow mb-2 text-primary">{{ t('home.workflowEyebrow') }}</p>
          <h2 class="heading-page">{{ t('home.workflowTitle') }}</h2>
          <p class="mt-2.5 text-sm leading-relaxed text-muted-foreground sm:text-base">
            {{ t('home.workflowDesc') }}
          </p>
        </div>

        <div class="grid gap-6 md:grid-cols-3">
          <Card>
            <CardHeader>
              <div class="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Camera class="h-5 w-5" />
              </div>
              <CardTitle>{{ t('home.step1Title') }}</CardTitle>
              <CardDescription>{{ t('home.step1Desc') }}</CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <div class="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600">
                <Clock class="h-5 w-5" />
              </div>
              <CardTitle>{{ t('home.step2Title') }}</CardTitle>
              <CardDescription>{{ t('home.step2Desc') }}</CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <div class="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600">
                <CheckCircle2 class="h-5 w-5" />
              </div>
              <CardTitle>{{ t('home.step3Title') }}</CardTitle>
              <CardDescription>{{ t('home.step3Desc') }}</CardDescription>
            </CardHeader>
          </Card>
        </div>

        <!-- Guidance Banner -->
        <Card class="mt-10 border-primary/20 bg-primary/5">
          <CardContent class="flex flex-col items-start justify-between gap-4 p-6 sm:flex-row sm:items-center">
            <div class="flex items-start gap-3">
              <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <TrendingUp class="h-4 w-4" />
              </div>
              <div>
                <h3 class="font-semibold">{{ t('home.rbacTitle') }}</h3>
                <p class="mt-1 text-sm text-muted-foreground">
                  {{ t('home.rbacDesc') }}
                </p>
              </div>
            </div>
            <RouterLink v-if="!auth.isAuthenticated" to="/login">
              <Button variant="outline" class="shrink-0 gap-2">
                <ClipboardCheck class="h-4 w-4" />
                {{ t('home.tryDemo') }}
              </Button>
            </RouterLink>
          </CardContent>
        </Card>
      </div>
    </section>
  </AppLayout>
</template>
