<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Cloud,
  HardDrive,
  Server,
  Save,
  PlugZap,
  CheckCircle2,
  AlertCircle,
  Lock,
  SlidersHorizontal,
  Globe,
} from 'lucide-vue-next'
import { useSettingsStore } from '@/stores/settings'
import { formatDate } from '@/lib/utils'
import type { AdminSettingsUpdatePayload, StorageProviderId, StorageTestResult } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

const { t, locale } = useI18n()
const settingsStore = useSettingsStore()

const ALL_FORMATS = ['png', 'jpg', 'jpeg', 'webp'] as const

const form = reactive({
  site_name: 'EcoWatch',
  allow_registration: true,
  provider: 'cloudinary' as StorageProviderId,
  max_file_size_mb: 5,
  allowed_extensions: ['png', 'jpg', 'jpeg', 'webp'] as string[],
  cloudinary: {
    cloud_name: '',
    api_key: '',
    api_secret: '',
    api_secret_masked: '',
    has_api_secret: false,
    folder: 'waste_reports',
  },
  s3: {
    endpoint_url: '',
    region: 'us-east-1',
    bucket: '',
    access_key_id: '',
    secret_access_key: '',
    secret_access_key_masked: '',
    has_secret_access_key: false,
    public_base_url: '',
    folder: 'waste_reports',
  },
})

const saveSuccess = ref('')
const saveError = ref('')
const testResult = ref<StorageTestResult | null>(null)

function hydrateForm() {
  const s = settingsStore.settings
  if (!s) return
  form.site_name = s.general.site_name
  form.allow_registration = s.general.allow_registration
  form.provider = s.storage.provider
  form.max_file_size_mb = s.storage.max_file_size_mb
  form.allowed_extensions = [...s.storage.allowed_extensions]

  form.cloudinary.cloud_name = s.storage.cloudinary.cloud_name
  form.cloudinary.api_key = s.storage.cloudinary.api_key
  form.cloudinary.api_secret = ''
  form.cloudinary.api_secret_masked = s.storage.cloudinary.api_secret_masked
  form.cloudinary.has_api_secret = s.storage.cloudinary.has_api_secret
  form.cloudinary.folder = s.storage.cloudinary.folder

  form.s3.endpoint_url = s.storage.s3.endpoint_url
  form.s3.region = s.storage.s3.region
  form.s3.bucket = s.storage.s3.bucket
  form.s3.access_key_id = s.storage.s3.access_key_id
  form.s3.secret_access_key = ''
  form.s3.secret_access_key_masked = s.storage.s3.secret_access_key_masked
  form.s3.has_secret_access_key = s.storage.s3.has_secret_access_key
  form.s3.public_base_url = s.storage.s3.public_base_url
  form.s3.folder = s.storage.s3.folder
}

onMounted(async () => {
  await settingsStore.fetchSettings()
  hydrateForm()
})

function buildPayload(): AdminSettingsUpdatePayload {
  return {
    general: {
      site_name: form.site_name.trim() || 'EcoWatch',
      allow_registration: form.allow_registration,
    },
    storage: {
      provider: form.provider,
      max_file_size_mb: Number(form.max_file_size_mb) || 5,
      allowed_extensions:
        form.allowed_extensions.length > 0 ? form.allowed_extensions : ['png', 'jpg', 'jpeg', 'webp'],
      cloudinary: {
        cloud_name: form.cloudinary.cloud_name.trim(),
        api_key: form.cloudinary.api_key.trim(),
        api_secret: form.cloudinary.api_secret.trim() || null,
        folder: form.cloudinary.folder.trim() || 'waste_reports',
      },
      s3: {
        endpoint_url: form.s3.endpoint_url.trim(),
        region: form.s3.region.trim() || 'us-east-1',
        bucket: form.s3.bucket.trim(),
        access_key_id: form.s3.access_key_id.trim(),
        secret_access_key: form.s3.secret_access_key.trim() || null,
        public_base_url: form.s3.public_base_url.trim(),
        folder: form.s3.folder.trim() || 'waste_reports',
      },
    },
  }
}

function toggleExtension(ext: string) {
  if (form.allowed_extensions.includes(ext)) {
    if (form.allowed_extensions.length > 1) {
      form.allowed_extensions = form.allowed_extensions.filter((e) => e !== ext)
    }
  } else {
    form.allowed_extensions = [...form.allowed_extensions, ext]
  }
}

function providerIcon(id: string) {
  if (id === 'cloudinary') return Cloud
  if (id === 's3_compatible') return HardDrive
  return Server
}

async function handleSave() {
  saveSuccess.value = ''
  saveError.value = ''
  try {
    await settingsStore.saveSettings(buildPayload())
    hydrateForm()
    saveSuccess.value = t('adminSettings.savedMsg')
  } catch (err: any) {
    saveError.value = err.response?.data?.detail || t('adminSettings.errSaveFailed')
  }
}

async function handleTestConnection() {
  testResult.value = null
  saveError.value = ''
  try {
    testResult.value = await settingsStore.testStorageConnection(buildPayload())
  } catch (err: any) {
    testResult.value = {
      ok: false,
      provider: form.provider,
      message: err.response?.data?.detail || t('adminSettings.testFailTitle'),
    }
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-eyebrow mb-1">{{ t('adminSettings.eyebrow') }}</p>
        <h2 class="heading-page">{{ t('adminSettings.title') }}</h2>
        <p class="mt-1 text-sm leading-relaxed text-muted-foreground">
          {{ t('adminSettings.subtitle') }}
        </p>
      </div>
      <Button :disabled="settingsStore.saving" class="gap-2" @click="handleSave">
        <Save class="h-4 w-4" />
        {{ settingsStore.saving ? t('common.saving') : t('adminSettings.saveAll') }}
      </Button>
    </div>

    <Alert v-if="saveSuccess" variant="success">
      <CheckCircle2 class="h-4 w-4" />
      <AlertDescription>{{ saveSuccess }}</AlertDescription>
    </Alert>

    <Alert v-if="saveError" variant="destructive">
      <AlertCircle class="h-4 w-4" />
      <AlertDescription>{{ saveError }}</AlertDescription>
    </Alert>

    <div v-if="settingsStore.loading && !settingsStore.settings" class="h-64 animate-pulse rounded-xl bg-muted/40" />

    <form v-else class="space-y-6" @submit.prevent="handleSave">
      <!-- 1. Pluggable File Storage Provider -->
      <Card>
        <CardHeader>
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <CardTitle>{{ t('adminSettings.storageCardTitle') }}</CardTitle>
              <CardDescription>{{ t('adminSettings.storageCardDesc') }}</CardDescription>
            </div>
            <Badge variant="outline" class="gap-1.5 font-mono text-xs">
              <Lock class="h-3 w-3 text-primary" />
              {{ t('adminSettings.encryptedBadge') }}
            </Badge>
          </div>
        </CardHeader>

        <CardContent class="space-y-6">
          <!-- Provider Selection Grid -->
          <div class="grid gap-3 md:grid-cols-3">
            <button
              v-for="option in settingsStore.settings?.available_providers ?? []"
              :key="option.id"
              type="button"
              class="flex flex-col items-start rounded-xl border p-4 text-left transition-all"
              :class="
                form.provider === option.id
                  ? 'border-primary bg-primary/5 ring-1 ring-primary'
                  : 'border-border bg-background hover:border-muted-foreground/40 hover:bg-muted/30'
              "
              @click="
                form.provider = option.id;
                testResult = null
              "
            >
              <div class="flex w-full items-center justify-between gap-2">
                <div
                  class="flex h-9 w-9 items-center justify-center rounded-lg"
                  :class="
                    form.provider === option.id
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground'
                  "
                >
                  <component :is="providerIcon(option.id)" class="h-4 w-4" />
                </div>
                <div class="flex items-center gap-1.5">
                  <Badge v-if="option.supports_cdn" variant="secondary" class="text-[10px]">CDN</Badge>
                  <Badge v-if="form.provider === option.id" variant="default" class="text-[10px]">
                    {{ t('common.active') }}
                  </Badge>
                </div>
              </div>
              <p class="mt-3 font-display text-sm font-semibold">{{ option.label }}</p>
              <p class="mt-1 text-xs leading-relaxed text-muted-foreground">{{ option.description }}</p>
            </button>
          </div>

          <!-- Cloudinary Config Panel -->
          <div
            v-if="form.provider === 'cloudinary'"
            class="space-y-4 rounded-xl border bg-muted/20 p-5"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <h4 class="font-display text-sm font-semibold">{{ t('adminSettings.cloudinaryTitle') }}</h4>
              <Badge v-if="form.cloudinary.has_api_secret" variant="resolved" class="font-mono text-[11px]">
                {{ t('adminSettings.secretStored', { masked: form.cloudinary.api_secret_masked || '••••••••' }) }}
              </Badge>
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div class="space-y-2">
                <Label for="cld-cloud">{{ t('adminSettings.cloudName') }}</Label>
                <Input id="cld-cloud" v-model="form.cloudinary.cloud_name" placeholder="e.g. dxy123abc" />
              </div>
              <div class="space-y-2">
                <Label for="cld-folder">{{ t('adminSettings.uploadFolder') }}</Label>
                <Input id="cld-folder" v-model="form.cloudinary.folder" placeholder="waste_reports" />
              </div>
              <div class="space-y-2">
                <Label for="cld-key">{{ t('adminSettings.apiKey') }}</Label>
                <Input
                  id="cld-key"
                  v-model="form.cloudinary.api_key"
                  placeholder="e.g. 987654321012345"
                  class="font-mono text-xs"
                />
              </div>
              <div class="space-y-2">
                <Label for="cld-secret">{{ t('adminSettings.apiSecret') }}</Label>
                <Input
                  id="cld-secret"
                  v-model="form.cloudinary.api_secret"
                  type="password"
                  :placeholder="
                    form.cloudinary.has_api_secret
                      ? t('adminSettings.keepSecretPlaceholder')
                      : t('adminSettings.enterCldSecretPlaceholder')
                  "
                  class="font-mono text-xs"
                />
              </div>
            </div>
          </div>

          <!-- S3-Compatible (Sabay Cloud / AWS / R2 / MinIO) Config Panel -->
          <div
            v-else-if="form.provider === 's3_compatible'"
            class="space-y-4 rounded-xl border bg-muted/20 p-5"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h4 class="font-display text-sm font-semibold">{{ t('adminSettings.s3Title') }}</h4>
                <p class="text-xs text-muted-foreground">{{ t('adminSettings.s3Hint') }}</p>
              </div>
              <Badge v-if="form.s3.has_secret_access_key" variant="resolved" class="font-mono text-[11px]">
                {{ t('adminSettings.secretStored', { masked: form.s3.secret_access_key_masked || '••••••••' }) }}
              </Badge>
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div class="space-y-2 sm:col-span-2">
                <Label for="s3-endpoint">{{ t('adminSettings.endpointUrl') }}</Label>
                <Input
                  id="s3-endpoint"
                  v-model="form.s3.endpoint_url"
                  placeholder="https://fsgw.sabay.com (base S3 gateway host only — not /graphql)"
                  class="font-mono text-xs"
                />
              </div>
              <div class="space-y-2">
                <Label for="s3-bucket">{{ t('adminSettings.bucketName') }}</Label>
                <Input id="s3-bucket" v-model="form.s3.bucket" placeholder="community-waste-media" />
              </div>
              <div class="space-y-2">
                <Label for="s3-region">{{ t('adminSettings.region') }}</Label>
                <Input id="s3-region" v-model="form.s3.region" placeholder="ap-southeast-1" />
              </div>
              <div class="space-y-2">
                <Label for="s3-access">{{ t('adminSettings.accessKeyId') }}</Label>
                <Input
                  id="s3-access"
                  v-model="form.s3.access_key_id"
                  placeholder="AKIA..."
                  class="font-mono text-xs"
                />
              </div>
              <div class="space-y-2">
                <Label for="s3-secret">{{ t('adminSettings.secretAccessKey') }}</Label>
                <Input
                  id="s3-secret"
                  v-model="form.s3.secret_access_key"
                  type="password"
                  :placeholder="
                    form.s3.has_secret_access_key
                      ? t('adminSettings.keepSecretPlaceholder')
                      : t('adminSettings.enterS3SecretPlaceholder')
                  "
                  class="font-mono text-xs"
                />
              </div>
              <div class="space-y-2">
                <Label for="s3-cdn">{{ t('adminSettings.publicCdnUrl') }}</Label>
                <Input
                  id="s3-cdn"
                  v-model="form.s3.public_base_url"
                  placeholder="https://cdn.example.com"
                  class="font-mono text-xs"
                />
              </div>
              <div class="space-y-2">
                <Label for="s3-folder">{{ t('adminSettings.folderPrefix') }}</Label>
                <Input id="s3-folder" v-model="form.s3.folder" placeholder="waste_reports" />
              </div>
            </div>
          </div>

          <!-- Local Disk Panel -->
          <div v-else class="rounded-xl border bg-muted/20 p-5 text-sm leading-relaxed text-muted-foreground">
            {{ t('adminSettings.localInfo') }}
          </div>

          <!-- Test Connection Bar -->
          <div class="flex flex-wrap items-center justify-between gap-3 border-t pt-4">
            <p class="text-xs text-muted-foreground">{{ t('adminSettings.testHint') }}</p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              class="gap-2"
              :disabled="settingsStore.testing"
              @click="handleTestConnection"
            >
              <PlugZap class="h-4 w-4" />
              {{ settingsStore.testing ? t('adminSettings.testing') : t('adminSettings.testBtn') }}
            </Button>
          </div>

          <Alert v-if="testResult" :variant="testResult.ok ? 'success' : 'destructive'">
            <CheckCircle2 v-if="testResult.ok" class="h-4 w-4" />
            <AlertCircle v-else class="h-4 w-4" />
            <AlertTitle>
              {{ testResult.ok ? t('adminSettings.testOkTitle') : t('adminSettings.testFailTitle') }}
            </AlertTitle>
            <AlertDescription>{{ testResult.message }}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <!-- 2. Upload Validation Policy + General Platform Settings -->
      <div class="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <SlidersHorizontal class="h-4 w-4 text-primary" />
              {{ t('adminSettings.policyTitle') }}
            </CardTitle>
            <CardDescription>{{ t('adminSettings.policyDesc') }}</CardDescription>
          </CardHeader>
          <CardContent class="space-y-5">
            <div class="space-y-2">
              <Label for="max-size">{{ t('adminSettings.maxSizeLabel') }}</Label>
              <div class="flex items-center gap-3">
                <Input
                  id="max-size"
                  v-model.number="form.max_file_size_mb"
                  type="number"
                  min="1"
                  max="25"
                  class="w-28 font-mono tabular-nums"
                />
                <span class="text-xs text-muted-foreground">{{ t('adminSettings.maxSizeRange') }}</span>
              </div>
            </div>

            <div class="space-y-2">
              <Label>{{ t('adminSettings.permittedFormats') }}</Label>
              <div class="flex flex-wrap gap-2">
                <Button
                  v-for="ext in ALL_FORMATS"
                  :key="ext"
                  type="button"
                  size="sm"
                  :variant="form.allowed_extensions.includes(ext) ? 'default' : 'outline'"
                  class="font-mono uppercase"
                  @click="toggleExtension(ext)"
                >
                  .{{ ext }}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Globe class="h-4 w-4 text-primary" />
              {{ t('adminSettings.generalTitle') }}
            </CardTitle>
            <CardDescription>{{ t('adminSettings.generalDesc') }}</CardDescription>
          </CardHeader>
          <CardContent class="space-y-5">
            <div class="space-y-2">
              <Label for="site-name">{{ t('adminSettings.siteNameLabel') }}</Label>
              <Input id="site-name" v-model="form.site_name" placeholder="EcoWatch" />
            </div>

            <label
              class="flex cursor-pointer items-start justify-between gap-4 rounded-lg border bg-muted/20 p-3.5"
            >
              <div>
                <p class="text-sm font-medium">{{ t('adminSettings.allowRegTitle') }}</p>
                <p class="mt-0.5 text-xs text-muted-foreground">{{ t('adminSettings.allowRegDesc') }}</p>
              </div>
              <input
                v-model="form.allow_registration"
                type="checkbox"
                class="mt-1 h-4 w-4 rounded border-input accent-primary"
              />
            </label>
          </CardContent>
        </Card>
      </div>

      <!-- Audit Footer -->
      <div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-card px-5 py-3.5 text-xs text-muted-foreground">
        <div>
          <span v-if="settingsStore.settings?.last_updated_at">
            {{ t('adminSettings.lastUpdated') }}
            <span class="font-medium tabular-nums text-foreground">
              {{ formatDate(settingsStore.settings.last_updated_at, locale) }}
            </span>
            <span v-if="settingsStore.settings?.last_updated_by">
              {{ t('adminSettings.byUser') }}
              <span class="font-medium text-foreground">{{ settingsStore.settings.last_updated_by }}</span>
            </span>
          </span>
          <span v-else>{{ t('adminSettings.usingEnvDefaults') }}</span>
        </div>
        <Button type="submit" :disabled="settingsStore.saving" class="gap-2">
          <Save class="h-4 w-4" />
          {{ settingsStore.saving ? t('common.saving') : t('adminSettings.saveAll') }}
        </Button>
      </div>
    </form>
  </div>
</template>
