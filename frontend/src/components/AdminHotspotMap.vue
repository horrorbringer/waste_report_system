<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { localizedCategory, translateStatus } from '@/i18n'
import type { MapPinReport } from '@/types'

const props = defineProps<{
  pins: MapPinReport[]
}>()

const { t, locale } = useI18n()
const router = useRouter()

const mapEl = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let layerGroup: L.LayerGroup | null = null

function statusColor(status: string): string {
  if (status === 'Resolved') return '#10b981'
  if (status === 'In Progress') return '#3b82f6'
  return '#f59e0b'
}

function renderPins() {
  if (!map || !layerGroup) return
  layerGroup.clearLayers()

  if (!props.pins.length) {
    map.setView([11.5564, 104.9282], 12)
    return
  }

  const bounds = L.latLngBounds([])
  for (const pin of props.pins) {
    const color = statusColor(pin.status)
    const marker = L.circleMarker([pin.latitude, pin.longitude], {
      radius: 8,
      fillColor: color,
      color: '#ffffff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.9,
    })

    const container = document.createElement('div')
    container.className = 'space-y-1 text-xs min-w-[180px]'
    const titleEl = document.createElement('p')
    titleEl.className = 'font-semibold text-foreground'
    titleEl.textContent = `#${pin.id} · ${pin.title}`
    const metaEl = document.createElement('p')
    metaEl.className = 'text-muted-foreground'
    metaEl.textContent = `${localizedCategory(pin.category_name, pin.category_name_km, locale.value)} · ${translateStatus(pin.status, t)}`
    const locEl = document.createElement('p')
    locEl.className = 'text-[11px] text-muted-foreground truncate'
    locEl.textContent = pin.location_text
    const btnEl = document.createElement('button')
    btnEl.type = 'button'
    btnEl.className = 'mt-1 inline-flex items-center text-[11px] font-medium text-primary hover:underline'
    btnEl.textContent = t('adminReports.viewBtn')
    btnEl.onclick = () => router.push(`/reports/${pin.id}`)

    container.append(titleEl, metaEl, locEl, btnEl)
    marker.bindPopup(container)
    marker.addTo(layerGroup)
    bounds.extend([pin.latitude, pin.longitude])
  }

  map.fitBounds(bounds, { padding: [32, 32], maxZoom: 15 })
}

onMounted(() => {
  if (!mapEl.value) return
  map = L.map(mapEl.value, { scrollWheelZoom: false }).setView([11.5564, 104.9282], 12)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map)
  layerGroup = L.layerGroup().addTo(map)
  renderPins()
})

watch(() => [props.pins, locale.value], renderPins, { deep: true })

onUnmounted(() => {
  map?.remove()
  map = null
  layerGroup = null
})
</script>

<template>
  <div ref="mapEl" class="h-72 w-full rounded-xl border bg-muted/20 z-0" />
</template>
