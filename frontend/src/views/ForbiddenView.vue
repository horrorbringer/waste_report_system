<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ShieldAlert, ArrowLeft } from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const { t } = useI18n()
</script>

<template>
  <AppLayout>
    <div class="container flex min-h-[calc(100vh-12rem)] items-center justify-center py-12">
      <Card class="w-full max-w-md text-center">
        <CardHeader>
          <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
            <ShieldAlert class="h-6 w-6" />
          </div>
          <CardTitle class="text-2xl">{{ t('forbidden.title') }}</CardTitle>
          <CardDescription>
            {{ t('forbidden.desc') }}
          </CardDescription>
        </CardHeader>
        <CardContent class="flex justify-center gap-3">
          <RouterLink to="/">
            <Button variant="outline" class="gap-2">
              <ArrowLeft class="h-4 w-4" />
              {{ t('forbidden.goHome') }}
            </Button>
          </RouterLink>
          <RouterLink to="/my-reports">
            <Button>{{ t('nav.myReports') }}</Button>
          </RouterLink>
        </CardContent>
      </Card>
    </div>
  </AppLayout>
</template>
