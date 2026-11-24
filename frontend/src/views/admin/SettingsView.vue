<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
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
  Eye,
  EyeOff,
  RotateCcw,
  Check,
  ShieldCheck,
  Activity,
  Layers,
  Database,
  Cpu,
  FolderLock,
  Loader2,
} from 'lucide-vue-next'
import { useSettingsStore } from '@/stores/settings'
import { formatDate } from '@/lib/utils'
import type { AdminSettingsUpdatePayload, StorageProviderId, StorageTestResult } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Switch } from '@/components/ui/switch'

const { t, locale } = useI18n()
const settingsStore = useSettingsStore()

const ALL_FORMATS = ['png', 'jpg', 'jpeg', 'webp', 'avif'] as const
type SettingsTab = 'storage' | 'policy' | 'platform' | 'system'

const activeTab = ref<SettingsTab>('storage')
const showCloudinarySecret = ref(false)
const showS3Secret = ref(false)

const form = reactive({
  site_name: 'EcoWatch',
  allow_registration: true,
  provider: 'cloudinary' as StorageProviderId,
  max_file_size_mb: 5,
  allowed_extensions: [...ALL_FORMATS] as string[],
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
        form.allowed_extensions.length > 0 ? form.allowed_extensions : [...ALL_FORMATS],
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

// Track whether form has unsaved modifications
const isDirty = computed(() => {
  const s = settingsStore.settings
  if (!s) return false
  if (form.site_name !== s.general.site_name) return true
  if (form.allow_registration !== s.general.allow_registration) return true
  if (form.provider !== s.storage.provider) return true
  if (form.max_file_size_mb !== s.storage.max_file_size_mb) return true
  if (form.allowed_extensions.length !== s.storage.allowed_extensions.length) return true
  if (form.cloudinary.cloud_name !== s.storage.cloudinary.cloud_name) return true
  if (form.cloudinary.api_key !== s.storage.cloudinary.api_key) return true
  if (form.cloudinary.folder !== s.storage.cloudinary.folder) return true
  if (form.cloudinary.api_secret !== '') return true
  if (form.s3.endpoint_url !== s.storage.s3.endpoint_url) return true
  if (form.s3.bucket !== s.storage.s3.bucket) return true
  if (form.s3.access_key_id !== s.storage.s3.access_key_id) return true
  if (form.s3.secret_access_key !== '') return true
  return false
})

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
    setTimeout(() => {
      saveSuccess.value = ''
    }, 4000)
  } catch (err: any) {
    saveError.value = err.response?.data?.detail || t('adminSettings.errSaveFailed')
  }
}

function handleDiscard() {
  hydrateForm()
  testResult.value = null
  saveError.value = ''
  saveSuccess.value = ''
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
  <div class="space-y-6 max-w-6xl pb-16">
    <!-- Standard Header with Status Badges & Quick Save -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
      <div>
        <div class="flex items-center gap-2 mb-1.5">
          <Badge variant="outline" class="gap-1.5 border-primary/30 text-primary text-xs font-semibold">
            <ShieldCheck class="h-3.5 w-3.5" />
            {{ t('adminSettings.eyebrow') }}
          </Badge>
          <Badge variant="secondary" class="font-mono text-[11px] gap-1">
            <Lock class="h-3 w-3 text-muted-foreground" />
            AES-128 Encrypted
          </Badge>
        </div>
        <h1 class="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          {{ t('adminSettings.title') }}
        </h1>
        <p class="mt-1 text-sm text-muted-foreground max-w-2xl leading-relaxed">
          {{ t('adminSettings.subtitle') }}
        </p>
      </div>

      <div class="flex items-center gap-2.5">
        <Button
          v-if="isDirty"
          variant="outline"
          size="sm"
          class="gap-1.5 text-xs"
          @click="handleDiscard"
        >
          <RotateCcw class="h-3.5 w-3.5" />
          {{ t('adminSettings.resetBtn') }}
        </Button>
        <Button
          :disabled="settingsStore.saving"
          size="default"
          class="gap-2 shadow-sm font-semibold min-w-32"
          @click="handleSave"
        >
          <Loader2 v-if="settingsStore.saving" class="h-4 w-4 animate-spin" />
          <Save v-else class="h-4 w-4" />
          {{ settingsStore.saving ? t('common.saving') : t('adminSettings.saveAll') }}
        </Button>
      </div>
    </div>

    <!-- Alert Notifications -->
    <Transition name="fade">
      <Alert v-if="saveSuccess" variant="success" class="shadow-xs">
        <CheckCircle2 class="h-4 w-4" />
        <AlertDescription class="font-medium">{{ saveSuccess }}</AlertDescription>
      </Alert>
    </Transition>

    <Transition name="fade">
      <Alert v-if="saveError" variant="destructive" class="shadow-xs">
        <AlertCircle class="h-4 w-4" />
        <AlertDescription class="font-medium">{{ saveError }}</AlertDescription>
      </Alert>
    </Transition>

    <!-- Standard Segmented Tab Navigation -->
    <div class="flex flex-wrap items-center gap-1.5 rounded-xl border bg-muted/40 p-1 text-xs">
      <button
        type="button"
        class="flex items-center gap-2 rounded-lg px-3.5 py-2 font-medium transition"
        :class="
          activeTab === 'storage'
            ? 'bg-background text-foreground shadow-xs font-semibold'
            : 'text-muted-foreground hover:text-foreground'
        "
        @click="activeTab = 'storage'"
      >
        <HardDrive class="h-4 w-4 text-primary" />
        <span>{{ t('adminSettings.tabStorage') }}</span>
        <Badge variant="outline" class="ml-1 text-[10px] font-mono capitalize">
          {{ form.provider }}
        </Badge>
      </button>

      <button
        type="button"
        class="flex items-center gap-2 rounded-lg px-3.5 py-2 font-medium transition"
        :class="
          activeTab === 'policy'
            ? 'bg-background text-foreground shadow-xs font-semibold'
            : 'text-muted-foreground hover:text-foreground'
        "
        @click="activeTab = 'policy'"
      >
        <SlidersHorizontal class="h-4 w-4 text-primary" />
        <span>{{ t('adminSettings.tabPolicy') }}</span>
        <span class="text-[11px] text-muted-foreground">({{ form.max_file_size_mb }}MB)</span>
      </button>

      <button
        type="button"
        class="flex items-center gap-2 rounded-lg px-3.5 py-2 font-medium transition"
        :class="
          activeTab === 'platform'
            ? 'bg-background text-foreground shadow-xs font-semibold'
            : 'text-muted-foreground hover:text-foreground'
        "
        @click="activeTab = 'platform'"
      >
        <Globe class="h-4 w-4 text-primary" />
        <span>{{ t('adminSettings.tabPlatform') }}</span>
      </button>

      <button
        type="button"
        class="flex items-center gap-2 rounded-lg px-3.5 py-2 font-medium transition"
        :class="
          activeTab === 'system'
            ? 'bg-background text-foreground shadow-xs font-semibold'
            : 'text-muted-foreground hover:text-foreground'
        "
        @click="activeTab = 'system'"
      >
        <Server class="h-4 w-4 text-primary" />
        <span>{{ t('adminSettings.tabSystem') }}</span>
      </button>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="settingsStore.loading && !settingsStore.settings" class="space-y-4">
      <div class="h-64 animate-pulse rounded-xl bg-muted/40" />
      <div class="h-48 animate-pulse rounded-xl bg-muted/30" />
    </div>

    <!-- Main Tab Content Panes -->
    <div v-else class="space-y-6">
      <!-- ================= TAB 1: STORAGE & CDN ================= -->
      <div v-show="activeTab === 'storage'" class="space-y-6">
        <!-- 1. Active Provider Selector Card -->
        <Card class="border-border/80 shadow-xs">
          <CardHeader>
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <CardTitle class="text-base font-bold">{{ t('adminSettings.storageCardTitle') }}</CardTitle>
                <CardDescription class="text-xs leading-relaxed mt-1">
                  {{ t('adminSettings.storageCardDesc') }}
                </CardDescription>
              </div>
              <Badge variant="outline" class="gap-1 font-mono text-xs">
                <FolderLock class="h-3 w-3 text-primary" />
                {{ t('adminSettings.encryptedBadge') }}
              </Badge>
            </div>
          </CardHeader>

          <CardContent class="space-y-6">
            <!-- 3 Provider Radio Cards -->
            <div class="grid gap-3.5 sm:grid-cols-3">
              <div
                v-for="option in settingsStore.settings?.available_providers ?? []"
                :key="option.id"
                class="group relative flex flex-col justify-between rounded-xl border p-4 text-left transition cursor-pointer select-none"
                :class="
                  form.provider === option.id
                    ? 'border-primary bg-primary/5 ring-2 ring-primary/20 shadow-xs'
                    : 'border-border bg-card hover:border-primary/40 hover:bg-muted/20'
                "
                @click="
                  form.provider = option.id;
                  testResult = null
                "
              >
                <div>
                  <div class="flex items-center justify-between gap-2">
                    <div
                      class="flex h-9 w-9 items-center justify-center rounded-lg transition"
                      :class="
                        form.provider === option.id
                          ? 'bg-primary text-primary-foreground shadow-xs'
                          : 'bg-muted text-muted-foreground group-hover:text-foreground'
                      "
                    >
                      <component :is="providerIcon(option.id)" class="h-4 w-4" />
                    </div>
                    <div class="flex items-center gap-1.5">
                      <Badge v-if="option.supports_cdn" variant="secondary" class="text-[10px] font-mono">
                        CDN
                      </Badge>
                      <span
                        v-if="form.provider === option.id"
                        class="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground"
                      >
                        <Check class="h-3 w-3 stroke-[3]" />
                      </span>
                    </div>
                  </div>
                  <h3 class="mt-3 font-semibold text-sm text-foreground">{{ option.label }}</h3>
                  <p class="mt-1 text-xs text-muted-foreground leading-relaxed">{{ option.description }}</p>
                </div>

                <div class="mt-4 pt-2 border-t border-border/50 text-[11px] font-medium" :class="form.provider === option.id ? 'text-primary' : 'text-muted-foreground'">
                  {{ form.provider === option.id ? 'Active Backend' : 'Click to select' }}
                </div>
              </div>
            </div>

            <!-- Provider Specific Configuration Forms -->
            <!-- CLOUDINARY CONFIG -->
            <div v-if="form.provider === 'cloudinary'" class="rounded-xl border border-border/80 bg-muted/20 p-5 space-y-4">
              <div class="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
                <div class="flex items-center gap-2">
                  <Cloud class="h-4 w-4 text-primary" />
                  <h4 class="font-bold text-sm text-foreground">{{ t('adminSettings.cloudinaryTitle') }}</h4>
                </div>
                <Badge v-if="form.cloudinary.has_api_secret" variant="outline" class="font-mono text-[11px] text-emerald-600 dark:text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                  <Lock class="h-3 w-3 mr-1" />
                  {{ t('adminSettings.secretStored', { masked: form.cloudinary.api_secret_masked || '••••••••' }) }}
                </Badge>
              </div>

              <div class="grid gap-4 sm:grid-cols-2">
                <div class="space-y-1.5">
                  <Label for="cld-cloud" class="text-xs font-semibold">{{ t('adminSettings.cloudName') }}</Label>
                  <Input id="cld-cloud" v-model="form.cloudinary.cloud_name" placeholder="e.g. dxy123abc" class="h-9 text-xs" />
                  <p class="text-[11px] text-muted-foreground">Found on your Cloudinary dashboard overview.</p>
                </div>

                <div class="space-y-1.5">
                  <Label for="cld-folder" class="text-xs font-semibold">{{ t('adminSettings.uploadFolder') }}</Label>
                  <Input id="cld-folder" v-model="form.cloudinary.folder" placeholder="waste_reports" class="h-9 text-xs" />
                  <p class="text-[11px] text-muted-foreground">Cloud asset root folder for citizen report evidence.</p>
                </div>

                <div class="space-y-1.5">
                  <Label for="cld-key" class="text-xs font-semibold">{{ t('adminSettings.apiKey') }}</Label>
                  <Input
                    id="cld-key"
                    v-model="form.cloudinary.api_key"
                    placeholder="e.g. 987654321012345"
                    class="h-9 font-mono text-xs"
                  />
                  <p class="text-[11px] text-muted-foreground">Public client identifier.</p>
                </div>

                <div class="space-y-1.5">
                  <Label for="cld-secret" class="text-xs font-semibold">{{ t('adminSettings.apiSecret') }}</Label>
                  <div class="relative">
                    <Input
                      id="cld-secret"
                      v-model="form.cloudinary.api_secret"
                      :type="showCloudinarySecret ? 'text' : 'password'"
                      :placeholder="
                        form.cloudinary.has_api_secret
                          ? t('adminSettings.keepSecretPlaceholder')
                          : t('adminSettings.enterCldSecretPlaceholder')
                      "
                      class="h-9 font-mono text-xs pr-9"
                    />
                    <button
                      type="button"
                      class="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      :title="showCloudinarySecret ? t('adminSettings.hideSecret') : t('adminSettings.showSecret')"
                      @click="showCloudinarySecret = !showCloudinarySecret"
                    >
                      <EyeOff v-if="showCloudinarySecret" class="h-4 w-4" />
                      <Eye v-else class="h-4 w-4" />
                    </button>
                  </div>
                  <p class="text-[11px] text-muted-foreground">Fernet-encrypted before saving into database.</p>
                </div>
              </div>
            </div>

            <!-- S3 COMPATIBLE CONFIG -->
            <div v-else-if="form.provider === 's3_compatible'" class="rounded-xl border border-border/80 bg-muted/20 p-5 space-y-4">
              <div class="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
                <div class="flex items-center gap-2">
                  <HardDrive class="h-4 w-4 text-blue-600" />
                  <div>
                    <h4 class="font-bold text-sm text-foreground">{{ t('adminSettings.s3Title') }}</h4>
                    <p class="text-[11px] text-muted-foreground">{{ t('adminSettings.s3Hint') }}</p>
                  </div>
                </div>
                <Badge v-if="form.s3.has_secret_access_key" variant="outline" class="font-mono text-[11px] text-emerald-600 dark:text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                  <Lock class="h-3 w-3 mr-1" />
                  {{ t('adminSettings.secretStored', { masked: form.s3.secret_access_key_masked || '••••••••' }) }}
                </Badge>
              </div>

              <div class="grid gap-4 sm:grid-cols-2">
                <div class="space-y-1.5 sm:col-span-2">
                  <Label for="s3-endpoint" class="text-xs font-semibold">{{ t('adminSettings.endpointUrl') }}</Label>
                  <Input
                    id="s3-endpoint"
                    v-model="form.s3.endpoint_url"
                    placeholder="https://fsgw.sabay.com (base gateway host only — not /graphql)"
                    class="h-9 font-mono text-xs"
                  />
                </div>

                <div class="space-y-1.5">
                  <Label for="s3-bucket" class="text-xs font-semibold">{{ t('adminSettings.bucketName') }}</Label>
                  <Input id="s3-bucket" v-model="form.s3.bucket" placeholder="community-waste-media" class="h-9 text-xs" />
                </div>

                <div class="space-y-1.5">
                  <Label for="s3-region" class="text-xs font-semibold">{{ t('adminSettings.region') }}</Label>
                  <Input id="s3-region" v-model="form.s3.region" placeholder="ap-southeast-1" class="h-9 text-xs" />
                </div>

                <div class="space-y-1.5">
                  <Label for="s3-access" class="text-xs font-semibold">{{ t('adminSettings.accessKeyId') }}</Label>
                  <Input
                    id="s3-access"
                    v-model="form.s3.access_key_id"
                    placeholder="AKIA..."
                    class="h-9 font-mono text-xs"
                  />
                </div>

                <div class="space-y-1.5">
                  <Label for="s3-secret" class="text-xs font-semibold">{{ t('adminSettings.secretAccessKey') }}</Label>
                  <div class="relative">
                    <Input
                      id="s3-secret"
                      v-model="form.s3.secret_access_key"
                      :type="showS3Secret ? 'text' : 'password'"
                      :placeholder="
                        form.s3.has_secret_access_key
                          ? t('adminSettings.keepSecretPlaceholder')
                          : t('adminSettings.enterS3SecretPlaceholder')
                      "
                      class="h-9 font-mono text-xs pr-9"
                    />
                    <button
                      type="button"
                      class="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      :title="showS3Secret ? t('adminSettings.hideSecret') : t('adminSettings.showSecret')"
                      @click="showS3Secret = !showS3Secret"
                    >
                      <EyeOff v-if="showS3Secret" class="h-4 w-4" />
                      <Eye v-else class="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <div class="space-y-1.5">
                  <Label for="s3-cdn" class="text-xs font-semibold">{{ t('adminSettings.publicCdnUrl') }}</Label>
                  <Input
                    id="s3-cdn"
                    v-model="form.s3.public_base_url"
                    placeholder="https://cdn.example.com"
                    class="h-9 font-mono text-xs"
                  />
                </div>

                <div class="space-y-1.5">
                  <Label for="s3-folder" class="text-xs font-semibold">{{ t('adminSettings.folderPrefix') }}</Label>
                  <Input id="s3-folder" v-model="form.s3.folder" placeholder="waste_reports" class="h-9 text-xs" />
                </div>
              </div>
            </div>

            <!-- LOCAL DISK NOTICE -->
            <div v-else class="rounded-xl border border-border/80 bg-muted/20 p-5 space-y-2">
              <div class="flex items-center gap-2 text-foreground font-semibold text-sm">
                <Server class="h-4 w-4 text-primary" />
                <span>Local Server Disk (`backend/uploads/`)</span>
              </div>
              <p class="text-xs leading-relaxed text-muted-foreground">
                {{ t('adminSettings.localInfo') }}
              </p>
            </div>
          </CardContent>

          <!-- Standard Connection Diagnostic Footer -->
          <CardFooter class="border-t bg-muted/10 p-4 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            <p class="text-xs text-muted-foreground">
              {{ t('adminSettings.testHint') }}
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              class="gap-2 text-xs font-semibold shrink-0"
              :disabled="settingsStore.testing"
              @click="handleTestConnection"
            >
              <Loader2 v-if="settingsStore.testing" class="h-3.5 w-3.5 animate-spin" />
              <PlugZap v-else class="h-3.5 w-3.5 text-primary" />
              {{ settingsStore.testing ? t('adminSettings.testing') : t('adminSettings.testBtn') }}
            </Button>
          </CardFooter>
        </Card>

        <!-- Test Connection Result Notification -->
        <Transition name="fade">
          <Alert v-if="testResult" :variant="testResult.ok ? 'success' : 'destructive'" class="shadow-xs">
            <CheckCircle2 v-if="testResult.ok" class="h-4 w-4" />
            <AlertCircle v-else class="h-4 w-4" />
            <AlertTitle class="font-bold">
              {{ testResult.ok ? t('adminSettings.testOkTitle') : t('adminSettings.testFailTitle') }}
            </AlertTitle>
            <AlertDescription class="text-xs mt-1 leading-relaxed">
              {{ testResult.message }}
            </AlertDescription>
          </Alert>
        </Transition>
      </div>

      <!-- ================= TAB 2: UPLOAD POLICY ================= -->
      <div v-show="activeTab === 'policy'" class="space-y-6">
        <Card class="border-border/80 shadow-xs">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-base font-bold">
              <SlidersHorizontal class="h-4 w-4 text-primary" />
              {{ t('adminSettings.policyTitle') }}
            </CardTitle>
            <CardDescription class="text-xs leading-relaxed mt-1">
              {{ t('adminSettings.policyDesc') }}
            </CardDescription>
          </CardHeader>

          <CardContent class="space-y-6">
            <!-- Max File Size with Visual Range Gauge -->
            <div class="space-y-3 rounded-xl border border-border/80 bg-muted/20 p-5">
              <div class="flex items-center justify-between">
                <div>
                  <Label for="max-size" class="text-sm font-semibold text-foreground">
                    {{ t('adminSettings.maxSizeLabel') }}
                  </Label>
                  <p class="text-xs text-muted-foreground mt-0.5">
                    {{ t('adminSettings.maxSizeRange') }}
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <Input
                    id="max-size"
                    v-model.number="form.max_file_size_mb"
                    type="number"
                    min="1"
                    max="25"
                    class="w-20 font-mono text-center font-bold text-sm h-9"
                  />
                  <span class="text-xs font-bold text-muted-foreground">MB</span>
                </div>
              </div>

              <!-- Visual Slider Bar -->
              <div class="space-y-1 pt-1">
                <input
                  v-model.number="form.max_file_size_mb"
                  type="range"
                  min="1"
                  max="25"
                  step="1"
                  class="w-full accent-primary h-2 bg-muted rounded-lg cursor-pointer"
                />
                <div class="flex justify-between text-[10px] text-muted-foreground font-mono">
                  <span>1 MB (Light)</span>
                  <span>5 MB (Standard)</span>
                  <span>10 MB (HD)</span>
                  <span>25 MB (Max)</span>
                </div>
              </div>
            </div>

            <!-- Allowed Image File Formats -->
            <div class="space-y-3 rounded-xl border border-border/80 bg-muted/20 p-5">
              <div>
                <Label class="text-sm font-semibold text-foreground">
                  {{ t('adminSettings.permittedFormats') }}
                </Label>
                <p class="text-xs text-muted-foreground mt-0.5">
                  Only image payloads matching these extensions and verified via Pillow magic bytes are accepted.
                </p>
              </div>

              <div class="flex flex-wrap gap-2.5 pt-1">
                <button
                  v-for="ext in ALL_FORMATS"
                  :key="ext"
                  type="button"
                  class="flex items-center gap-2 rounded-lg border px-3.5 py-2 text-xs font-mono font-bold transition shadow-2xs"
                  :class="
                    form.allowed_extensions.includes(ext)
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border bg-card text-muted-foreground hover:border-primary/50 hover:text-foreground'
                  "
                  @click="toggleExtension(ext)"
                >
                  <Check v-if="form.allowed_extensions.includes(ext)" class="h-3.5 w-3.5 stroke-[3]" />
                  <span>.{{ ext.toUpperCase() }}</span>
                </button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- ================= TAB 3: PLATFORM & ACCESS ================= -->
      <div v-show="activeTab === 'platform'" class="space-y-6">
        <Card class="border-border/80 shadow-xs">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-base font-bold">
              <Globe class="h-4 w-4 text-primary" />
              {{ t('adminSettings.generalTitle') }}
            </CardTitle>
            <CardDescription class="text-xs leading-relaxed mt-1">
              {{ t('adminSettings.generalDesc') }}
            </CardDescription>
          </CardHeader>

          <CardContent class="space-y-6">
            <!-- Platform Display Name -->
            <div class="space-y-2 rounded-xl border border-border/80 bg-muted/20 p-5">
              <Label for="site-name" class="text-xs font-semibold text-foreground">
                {{ t('adminSettings.siteNameLabel') }}
              </Label>
              <Input
                id="site-name"
                v-model="form.site_name"
                placeholder="EcoWatch"
                class="h-9 max-w-md text-sm font-semibold"
              />
              <p class="text-[11px] text-muted-foreground">
                Displayed in the public header, system notifications, and report receipts.
              </p>
            </div>

            <!-- Public Registration Switch Card -->
            <div class="flex items-center justify-between gap-4 rounded-xl border border-border/80 bg-muted/20 p-5">
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <p class="text-sm font-bold text-foreground">
                    {{ t('adminSettings.allowRegTitle') }}
                  </p>
                  <Badge
                    :variant="form.allow_registration ? 'default' : 'secondary'"
                    class="text-[10px] font-mono"
                  >
                    {{ form.allow_registration ? 'Enabled (Public)' : 'Disabled (Invite Only)' }}
                  </Badge>
                </div>
                <p class="text-xs text-muted-foreground max-w-xl leading-relaxed">
                  {{ t('adminSettings.allowRegDesc') }}
                </p>
              </div>
              <Switch
                :checked="form.allow_registration"
                @update:checked="form.allow_registration = $event"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- ================= TAB 4: SYSTEM DIAGNOSTICS ================= -->
      <div v-show="activeTab === 'system'" class="space-y-6">
        <Card class="border-border/80 shadow-xs">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-base font-bold">
              <Activity class="h-4 w-4 text-primary" />
              {{ t('adminSettings.tabSystem') }}
            </CardTitle>
            <CardDescription class="text-xs leading-relaxed mt-1">
              Real-time runtime state, database backend details, and cryptographic integrity parameters.
            </CardDescription>
          </CardHeader>

          <CardContent class="space-y-4">
            <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <!-- Parameter 1: Database Engine -->
              <div class="rounded-xl border border-border/80 bg-card p-4 space-y-1.5">
                <div class="flex items-center justify-between text-muted-foreground">
                  <span class="text-xs font-semibold uppercase tracking-wider">Database Dialect</span>
                  <Database class="h-4 w-4 text-primary" />
                </div>
                <p class="text-base font-bold font-mono text-foreground">PostgreSQL 16</p>
                <p class="text-[11px] text-muted-foreground">psycopg v3 connection pool</p>
              </div>

              <!-- Parameter 2: Encryption Engine -->
              <div class="rounded-xl border border-border/80 bg-card p-4 space-y-1.5">
                <div class="flex items-center justify-between text-muted-foreground">
                  <span class="text-xs font-semibold uppercase tracking-wider">Secrets Cipher</span>
                  <Lock class="h-4 w-4 text-emerald-600" />
                </div>
                <p class="text-base font-bold font-mono text-foreground">Fernet (AES-128-CBC)</p>
                <p class="text-[11px] text-muted-foreground">HMAC-SHA256 authenticated</p>
              </div>

              <!-- Parameter 3: Active Storage Provider -->
              <div class="rounded-xl border border-border/80 bg-card p-4 space-y-1.5">
                <div class="flex items-center justify-between text-muted-foreground">
                  <span class="text-xs font-semibold uppercase tracking-wider">Storage Runtime</span>
                  <component :is="providerIcon(form.provider)" class="h-4 w-4 text-blue-600" />
                </div>
                <p class="text-base font-bold font-mono text-foreground capitalize">{{ form.provider }}</p>
                <p class="text-[11px] text-muted-foreground">HTTPS CDN delivery pipeline</p>
              </div>

              <!-- Parameter 4: Image Processor -->
              <div class="rounded-xl border border-border/80 bg-card p-4 space-y-1.5">
                <div class="flex items-center justify-between text-muted-foreground">
                  <span class="text-xs font-semibold uppercase tracking-wider">Image Validator</span>
                  <Layers class="h-4 w-4 text-purple-600" />
                </div>
                <p class="text-base font-bold font-mono text-foreground">Pillow (PIL)</p>
                <p class="text-[11px] text-muted-foreground">Magic header inspection & MIME verify</p>
              </div>

              <!-- Parameter 5: API Server -->
              <div class="rounded-xl border border-border/80 bg-card p-4 space-y-1.5">
                <div class="flex items-center justify-between text-muted-foreground">
                  <span class="text-xs font-semibold uppercase tracking-wider">API Framework</span>
                  <Cpu class="h-4 w-4 text-amber-600" />
                </div>
                <p class="text-base font-bold font-mono text-foreground">FastAPI 0.115</p>
                <p class="text-[11px] text-muted-foreground">Python 3.12 (Uvicorn ASGI)</p>
              </div>

              <!-- Parameter 6: Auth Scheme -->
              <div class="rounded-xl border border-border/80 bg-card p-4 space-y-1.5">
                <div class="flex items-center justify-between text-muted-foreground">
                  <span class="text-xs font-semibold uppercase tracking-wider">Access Control</span>
                  <ShieldCheck class="h-4 w-4 text-primary" />
                </div>
                <p class="text-base font-bold font-mono text-foreground">JWT + RBAC</p>
                <p class="text-[11px] text-muted-foreground">Bcrypt password hashing</p>
              </div>
            </div>

            <!-- Audit Trail Banner -->
            <div class="rounded-xl border border-border/70 bg-muted/20 p-4 text-xs text-muted-foreground flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mt-4">
              <div>
                <span v-if="settingsStore.settings?.last_updated_at">
                  {{ t('adminSettings.lastUpdated') }}
                  <span class="font-bold tabular-nums text-foreground">
                    {{ formatDate(settingsStore.settings.last_updated_at, locale) }}
                  </span>
                  <span v-if="settingsStore.settings?.last_updated_by">
                    {{ t('adminSettings.byUser') }}
                    <span class="font-bold text-foreground">{{ settingsStore.settings.last_updated_by }}</span>
                  </span>
                </span>
                <span v-else>{{ t('adminSettings.usingEnvDefaults') }}</span>
              </div>
              <Badge variant="outline" class="font-mono text-[10px] w-fit">
                Live Dynamic Sync
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Sticky Bottom Unsaved Changes Floating Bar -->
    <Transition name="fade">
      <div
        v-if="isDirty"
        class="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 rounded-2xl border border-border bg-card/95 px-5 py-3 shadow-xl backdrop-blur-md"
      >
        <div class="flex items-center gap-2 text-xs font-semibold text-foreground">
          <span class="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
          <span>{{ t('adminSettings.unsavedChanges') }}</span>
        </div>
        <div class="h-4 w-px bg-border" />
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            class="h-8 text-xs font-medium"
            @click="handleDiscard"
          >
            {{ t('adminSettings.resetBtn') }}
          </Button>
          <Button
            size="sm"
            class="h-8 gap-1.5 text-xs font-semibold shadow-xs"
            :disabled="settingsStore.saving"
            @click="handleSave"
          >
            <Loader2 v-if="settingsStore.saving" class="h-3 w-3 animate-spin" />
            <Save v-else class="h-3 w-3" />
            {{ t('adminSettings.saveAll') }}
          </Button>
        </div>
      </div>
    </Transition>
  </div>
</template>
