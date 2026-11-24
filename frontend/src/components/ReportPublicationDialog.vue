<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { DialogTrigger } from 'radix-vue'
import { Globe, Lock, MapPin } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { suggestReportArea } from '@/lib/cambodiaAreas'
import { useReportStore } from '@/stores/reports'

const props = defineProps<{
  reportId: number
  locationText: string
  locationDistrict: number | null
  publishedDistrict: number | null
  publishedProvince: number | null
}>()

const { t, locale } = useI18n()
const reportStore = useReportStore()
const open = ref(false)
const selectedProvince = ref<number | ''>('')
const selectedDistrict = ref<number | 'province-only' | ''>('')
const saving = ref(false)
const failed = ref(false)
const loadingAreas = ref(false)
const areasFailed = ref(false)
const publishedProvinceCode = computed(() => props.publishedProvince ?? (props.publishedDistrict ? Math.trunc(props.publishedDistrict / 100) : null))
const locationSuggestion = computed(() => suggestReportArea(props.locationText, props.locationDistrict, reportStore.reportAreas))
const provinceOptions = computed(() => [...reportStore.reportAreas].sort((a, b) =>
  areaLabel(a).localeCompare(areaLabel(b), locale.value),
))
const province = computed(() => reportStore.reportAreas.find(({ code }) => code === selectedProvince.value))
const districtOptions = computed(() => [...(province.value?.districts ?? [])].sort((a, b) =>
  areaLabel(a).localeCompare(areaLabel(b), locale.value),
))
const district = computed(() => districtOptions.value.find(({ code }) => code === selectedDistrict.value))
const publicArea = computed(() => {
  if (!province.value) return ''
  return district.value ? [areaLabel(district.value), areaLabel(province.value)].join(', ') : areaLabel(province.value)
})
const canSave = computed(() => {
  if (!province.value || (!district.value && selectedDistrict.value !== 'province-only')) return false
  return publishedProvinceCode.value !== province.value.code || props.publishedDistrict !== (district.value?.code ?? null)
})

function areaLabel(area: { name: string; name_km: string }) {
  return locale.value === 'km' ? area.name_km : area.name
}

function handleOpen(next: boolean) {
  if (saving.value) return
  open.value = next
  if (next) {
    failed.value = false
    selectedProvince.value = publishedProvinceCode.value ?? ''
    selectedDistrict.value = props.publishedDistrict ?? (publishedProvinceCode.value ? 'province-only' : '')
    loadAreas()
  }
}

async function loadAreas() {
  loadingAreas.value = true
  areasFailed.value = false
  try {
    await reportStore.fetchReportAreas()
    if (open.value && !publishedProvinceCode.value) {
      selectedProvince.value = locationSuggestion.value.province ?? ''
      selectedDistrict.value = locationSuggestion.value.district ?? ''
    }
  } catch {
    areasFailed.value = true
  } finally {
    loadingAreas.value = false
  }
}

async function save(province: number | null, district: number | null) {
  if (saving.value) return
  saving.value = true
  failed.value = false
  try {
    await reportStore.setReportPublication(props.reportId, province, district)
    open.value = false
  } catch {
    failed.value = true
  } finally {
    saving.value = false
  }
}

function publish() {
  if (canSave.value && province.value) save(province.value.code, district.value?.code ?? null)
}
</script>

<template>
  <Dialog :open="open" @update:open="handleOpen">
    <DialogTrigger as-child>
      <Button variant="outline" size="sm" class="gap-1.5">
        <Globe v-if="publishedProvinceCode" class="h-4 w-4 text-primary" />
        <Lock v-else class="h-4 w-4" />
        {{ t(publishedProvinceCode ? 'community.publicListing' : 'community.publish') }}
      </Button>
    </DialogTrigger>
    <DialogContent class="max-h-[calc(100dvh-2rem)] max-w-md overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{{ t('community.visibilityTitle') }}</DialogTitle>
        <DialogDescription>{{ t('community.visibilityDescription') }}</DialogDescription>
      </DialogHeader>

      <div class="flex items-start gap-2.5 rounded-lg border bg-muted/35 p-3 text-sm">
        <MapPin class="mt-0.5 h-4 w-4 shrink-0 text-primary" />
        <div class="min-w-0 space-y-1">
          <p class="font-medium">{{ t('community.reportedLocation') }}</p>
          <p class="break-words text-muted-foreground">{{ locationText }}</p>
        </div>
      </div>

      <form class="space-y-4" @submit.prevent="publish">
        <div v-if="areasFailed" class="space-y-2" role="alert">
          <p class="text-sm text-destructive">{{ t('community.areaLoadError') }}</p>
          <Button type="button" variant="outline" size="sm" @click="loadAreas">{{ t('common.refresh') }}</Button>
        </div>
        <div class="space-y-1.5">
          <Label for="public-province">{{ t('community.province') }}</Label>
          <select
            id="public-province"
            v-model="selectedProvince"
            required
            :disabled="saving || loadingAreas || areasFailed"
            class="block h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
            @change="selectedDistrict = ''"
          >
            <option disabled value="">{{ t(loadingAreas ? 'community.loadingAreas' : 'community.chooseProvince') }}</option>
            <option v-for="item in provinceOptions" :key="item.code" :value="item.code">{{ areaLabel(item) }}</option>
          </select>
        </div>
        <div class="space-y-1.5">
          <Label for="public-district">{{ t('community.district') }}</Label>
          <select
            id="public-district"
            v-model="selectedDistrict"
            required
            :disabled="saving || loadingAreas || !province"
            class="block h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
          >
            <option disabled value="">{{ t(province ? 'community.chooseDistrict' : 'community.chooseProvinceFirst') }}</option>
            <option v-if="province" value="province-only">{{ t('community.provinceOnly') }}</option>
            <option v-for="item in districtOptions" :key="item.code" :value="item.code">{{ areaLabel(item) }}</option>
          </select>
          <p v-if="!publishedProvinceCode && selectedProvince === locationSuggestion.province && (selectedDistrict || null) === locationSuggestion.district" class="text-sm text-muted-foreground">
            {{ t('community.confirmAreaSuggestion') }}
          </p>
        </div>
        <div v-if="publicArea && selectedDistrict" class="rounded-lg border border-primary/20 bg-accent/40 p-3 text-sm">
          <p class="text-xs font-medium text-muted-foreground">{{ t('community.publicAreaPreview') }}</p>
          <p class="mt-0.5 font-semibold text-foreground" aria-live="polite">{{ publicArea }}</p>
        </div>
        <p v-if="failed" role="alert" class="text-sm text-destructive">{{ t('community.saveError') }}</p>
        <DialogFooter class="gap-2 sm:justify-between sm:space-x-0">
          <Button v-if="publishedProvinceCode" type="button" variant="outline" :disabled="saving" @click="save(null, null)">
            {{ t('community.unpublish') }}
          </Button>
          <Button v-else type="button" variant="ghost" :disabled="saving" @click="handleOpen(false)">
            {{ t('common.cancel') }}
          </Button>
          <Button type="submit" :disabled="saving || loadingAreas || !canSave">
            {{ t(saving ? 'common.saving' : publishedProvinceCode ? 'community.changeArea' : 'community.publish') }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
