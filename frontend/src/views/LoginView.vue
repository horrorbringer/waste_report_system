<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Leaf, AlertCircle, ShieldCheck, User as UserIcon } from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref('')

async function handleSubmit() {
  error.value = ''
  try {
    const user = await auth.login(email.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : null
    if (redirect) {
      router.push(redirect)
    } else if (user.role === 'admin') {
      router.push('/admin/dashboard')
    } else {
      router.push('/my-reports')
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('auth.errLoginFailed')
  }
}

function fillDemo(role: 'admin' | 'resident') {
  if (role === 'admin') {
    email.value = 'admin@waste.local'
    password.value = 'Admin@123'
  } else {
    email.value = 'resident@waste.local'
    password.value = 'Resident@123'
  }
}
</script>

<template>
  <AppLayout>
    <div class="container flex min-h-[calc(100vh-10rem)] items-center justify-center py-12">
      <Card class="w-full max-w-md">
        <CardHeader class="space-y-1 text-center">
          <div class="mx-auto mb-2 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Leaf class="h-6 w-6" />
          </div>
          <CardTitle class="text-2xl">{{ t('auth.loginTitle') }}</CardTitle>
          <CardDescription>{{ t('auth.loginDesc') }}</CardDescription>
        </CardHeader>

        <CardContent class="space-y-4">
          <Alert v-if="error" variant="destructive">
            <AlertCircle class="h-4 w-4" />
            <AlertDescription>{{ error }}</AlertDescription>
          </Alert>

          <form class="space-y-4" @submit.prevent="handleSubmit">
            <div class="space-y-2">
              <Label for="email">{{ t('auth.email') }}</Label>
              <Input
                id="email"
                v-model="email"
                type="email"
                :placeholder="t('auth.emailPlaceholder')"
                required
                autocomplete="email"
              />
            </div>

            <div class="space-y-2">
              <Label for="password">{{ t('auth.password') }}</Label>
              <Input
                id="password"
                v-model="password"
                type="password"
                :placeholder="t('auth.passwordPlaceholder')"
                required
                autocomplete="current-password"
              />
            </div>

            <Button type="submit" class="w-full" :disabled="auth.loading">
              {{ auth.loading ? t('auth.signingIn') : t('nav.signIn') }}
            </Button>
          </form>

          <!-- Demo Quick Fill Helpers -->
          <div class="rounded-lg border bg-muted/40 p-3">
            <p class="mb-2 text-xs font-medium text-muted-foreground">{{ t('auth.quickDemoLabel') }}</p>
            <div class="grid grid-cols-2 gap-2">
              <Button type="button" variant="outline" size="sm" @click="fillDemo('resident')">
                <UserIcon class="h-3.5 w-3.5" />
                {{ t('auth.residentDemo') }}
              </Button>
              <Button type="button" variant="outline" size="sm" @click="fillDemo('admin')">
                <ShieldCheck class="h-3.5 w-3.5" />
                {{ t('auth.adminDemo') }}
              </Button>
            </div>
          </div>
        </CardContent>

        <CardFooter class="justify-center">
          <p class="text-sm text-muted-foreground">
            {{ t('auth.noAccount') }}
            <RouterLink to="/register" class="font-medium text-primary hover:underline">
              {{ t('auth.createOne') }}
            </RouterLink>
          </p>
        </CardFooter>
      </Card>
    </div>
  </AppLayout>
</template>
