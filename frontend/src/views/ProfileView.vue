<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { AlertCircle, CheckCircle2, KeyRound, Save, User as UserIcon } from 'lucide-vue-next'
import AppLayout from '@/layouts/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { formatApiError, formatDate } from '@/lib/utils'
import { translateRole } from '@/i18n'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

const { t, locale } = useI18n()
const auth = useAuthStore()

const fullName = ref(auth.user?.full_name || '')
const profileSaving = ref(false)
const profileSuccess = ref('')
const profileError = ref('')

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordSaving = ref(false)
const passwordSuccess = ref('')
const passwordError = ref('')

async function handleSaveProfile() {
  profileSuccess.value = ''
  profileError.value = ''
  profileSaving.value = true
  try {
    await auth.updateProfile(fullName.value.trim())
    profileSuccess.value = t('profile.profileUpdated')
  } catch (err: any) {
    profileError.value = formatApiError(err, t('profile.errProfileUpdate'))
  } finally {
    profileSaving.value = false
  }
}

async function handleChangePassword() {
  passwordSuccess.value = ''
  passwordError.value = ''
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = t('auth.errPasswordMismatch')
    return
  }
  if (newPassword.value.length < 6) {
    passwordError.value = t('auth.errPasswordShort')
    return
  }

  passwordSaving.value = true
  try {
    await auth.changePassword(currentPassword.value, newPassword.value)
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    passwordSuccess.value = t('profile.passwordUpdated')
  } catch (err: any) {
    passwordError.value = formatApiError(err, t('profile.errPasswordUpdate'))
  } finally {
    passwordSaving.value = false
  }
}
</script>

<template>
  <AppLayout>
    <div class="container max-w-3xl py-8 space-y-6">
      <div>
        <p class="text-eyebrow mb-1">{{ t('profile.eyebrow') }}</p>
        <h1 class="heading-page">{{ t('profile.title') }}</h1>
        <p class="mt-1 text-sm text-muted-foreground">{{ t('profile.subtitle') }}</p>
      </div>

      <!-- Profile Info Card -->
      <Card class="border-border/60 shadow-sm">
        <CardHeader>
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <CardTitle class="flex items-center gap-2 text-base">
                <UserIcon class="h-4 w-4 text-primary" />
                {{ t('profile.infoTitle') }}
              </CardTitle>
              <CardDescription class="text-xs">{{ t('profile.infoDesc') }}</CardDescription>
            </div>
            <Badge v-if="auth.user" variant="secondary">
              {{ translateRole(auth.user.role, t) }}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <form class="space-y-4" @submit.prevent="handleSaveProfile">
            <Alert v-if="profileSuccess" variant="success">
              <CheckCircle2 class="h-4 w-4" />
              <AlertDescription>{{ profileSuccess }}</AlertDescription>
            </Alert>
            <Alert v-if="profileError" variant="destructive">
              <AlertCircle class="h-4 w-4" />
              <AlertDescription>{{ profileError }}</AlertDescription>
            </Alert>

            <div class="grid gap-4 sm:grid-cols-2">
              <div class="space-y-1.5">
                <Label for="profile-name">{{ t('adminUsers.fieldFullName') }}</Label>
                <Input id="profile-name" v-model="fullName" required minlength="2" maxlength="120" />
              </div>
              <div class="space-y-1.5">
                <Label for="profile-email">{{ t('adminUsers.fieldEmail') }}</Label>
                <Input id="profile-email" :model-value="auth.user?.email || ''" disabled />
              </div>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-3 pt-1">
              <p v-if="auth.user?.created_at" class="text-xs text-muted-foreground">
                {{ t('profile.memberSince', { date: formatDate(auth.user.created_at, locale) }) }}
              </p>
              <Button type="submit" size="sm" class="gap-1.5" :disabled="profileSaving">
                <Save class="h-3.5 w-3.5" />
                {{ profileSaving ? t('common.saving') : t('adminUsers.saveBtn') }}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <!-- Change Password Card -->
      <Card class="border-border/60 shadow-sm">
        <CardHeader>
          <CardTitle class="flex items-center gap-2 text-base">
            <KeyRound class="h-4 w-4 text-primary" />
            {{ t('profile.passwordTitle') }}
          </CardTitle>
          <CardDescription class="text-xs">{{ t('profile.passwordDesc') }}</CardDescription>
        </CardHeader>
        <CardContent>
          <form class="space-y-4" @submit.prevent="handleChangePassword">
            <Alert v-if="passwordSuccess" variant="success">
              <CheckCircle2 class="h-4 w-4" />
              <AlertDescription>{{ passwordSuccess }}</AlertDescription>
            </Alert>
            <Alert v-if="passwordError" variant="destructive">
              <AlertCircle class="h-4 w-4" />
              <AlertDescription>{{ passwordError }}</AlertDescription>
            </Alert>

            <div class="space-y-1.5">
              <Label for="current-password">{{ t('profile.currentPassword') }}</Label>
              <Input id="current-password" v-model="currentPassword" type="password" required />
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div class="space-y-1.5">
                <Label for="new-password">{{ t('profile.newPassword') }}</Label>
                <Input id="new-password" v-model="newPassword" type="password" required minlength="6" />
              </div>
              <div class="space-y-1.5">
                <Label for="confirm-new-password">{{ t('auth.confirmPassword') }}</Label>
                <Input id="confirm-new-password" v-model="confirmPassword" type="password" required minlength="6" />
              </div>
            </div>

            <div class="flex justify-end pt-1">
              <Button type="submit" variant="outline" size="sm" class="gap-1.5" :disabled="passwordSaving">
                <KeyRound class="h-3.5 w-3.5" />
                {{ passwordSaving ? t('common.saving') : t('profile.updatePasswordBtn') }}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  </AppLayout>
</template>
