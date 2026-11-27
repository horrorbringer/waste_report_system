<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Leaf, AlertCircle, Loader2 } from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { formatApiError } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')

async function handleSubmit() {
  error.value = ''
  if (password.value !== confirmPassword.value) {
    error.value = t('auth.errPasswordMismatch')
    return
  }
  if (password.value.length < 6) {
    error.value = t('auth.errPasswordShort')
    return
  }

  try {
    await auth.register(fullName.value, email.value, password.value)
    router.push('/reports/new')
  } catch (err: any) {
    error.value = formatApiError(err, t('auth.errRegisterFailed'))
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
          <CardTitle class="text-2xl">{{ t('auth.registerTitle') }}</CardTitle>
          <CardDescription>{{ t('auth.registerDesc') }}</CardDescription>
        </CardHeader>

        <CardContent class="space-y-4">
          <Alert v-if="error" variant="destructive">
            <AlertCircle class="h-4 w-4" />
            <AlertDescription>{{ error }}</AlertDescription>
          </Alert>

          <form class="space-y-4" @submit.prevent="handleSubmit">
            <div class="space-y-2">
              <Label for="fullName">{{ t('auth.fullName') }}</Label>
              <Input
                id="fullName"
                v-model="fullName"
                :placeholder="t('auth.fullNamePlaceholder')"
                required
              />
            </div>

            <div class="space-y-2">
              <Label for="email">{{ t('auth.email') }}</Label>
              <Input
                id="email"
                v-model="email"
                type="email"
                :placeholder="t('auth.emailPlaceholder')"
                required
              />
            </div>

            <div class="space-y-2">
              <Label for="password">{{ t('auth.password') }}</Label>
              <Input
                id="password"
                v-model="password"
                type="password"
                :placeholder="t('auth.passwordMinPlaceholder')"
                required
              />
            </div>

            <div class="space-y-2">
              <Label for="confirmPassword">{{ t('auth.confirmPassword') }}</Label>
              <Input
                id="confirmPassword"
                v-model="confirmPassword"
                type="password"
                :placeholder="t('auth.confirmPlaceholder')"
                required
              />
            </div>

            <Button type="submit" class="w-full gap-2" :disabled="auth.loading">
              <Loader2 v-if="auth.loading" class="h-4 w-4 animate-spin" />
              {{ auth.loading ? t('auth.creatingAccount') : t('auth.createAccount') }}
            </Button>
          </form>
        </CardContent>

        <CardFooter class="justify-center">
          <p class="text-sm text-muted-foreground">
            {{ t('auth.hasAccount') }}
            <RouterLink to="/login" class="font-medium text-primary hover:underline">
              {{ t('nav.signIn') }}
            </RouterLink>
          </p>
        </CardFooter>
      </Card>
    </div>
  </AppLayout>
</template>
