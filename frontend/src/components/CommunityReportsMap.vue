<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import {
  Camera,
  LocateFixed,
  MapPin,
  ShieldCheck,
} from 'lucide-vue-next'
import StatusBadge from '@/components/StatusBadge.vue'
import { getAreaCoordinates } from '@/lib/cambodiaCenters'
import { localizedCategory, translateStatus } from '@/i18n'
import { resolvePhotoUrl } from '@/lib/utils'
import type { CommunityReport } from '@/types'

const props = defineProps<{
  reports: CommunityReport[]
}>()

const emit = defineEmits<{
  'select-report': [report: CommunityReport]
}>()

const { t, locale } = useI18n()
const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let markersLayer: L.LayerGroup | null = null
let currentTileLayer: L.TileLayer | null = null
let currentBounds: L.LatLngBounds | null = null

type MapLayerKey = 'google_streets' | 'google_hybrid' | 'osm'
const activeLayer = ref<MapLayerKey>('google_streets')
const activeReportId = ref<number | null>(null)
const hoveredReportId = ref<number | null>(null)
const pinnedPopupId = ref<number | null>(null)

const markerMap = new Map<number, { marker: L.Marker; coords: [number, number]; report: CommunityReport }>()
let closeHoverTimer: ReturnType<typeof setTimeout> | null = null

function getMarkerColor(status: CommunityReport['status']) {
  if (status === 'Resolved') return '#16a34a' // emerald-600
  if (status === 'In Progress') return '#2563eb' // blue-600
  return '#d97706' // amber-600
}

function createPinIcon(status: CommunityReport['status'], isActive: boolean) {
  const color = getMarkerColor(status)
  const scale = isActive ? 'scale(1.22)' : 'scale(1)'
  const halo = isActive
    ? `<span style="position:absolute;inset:-4px;border-radius:9999px;background:${color}33;pointer-events:none;"></span>`
    : ''

  return L.divIcon({
    className: 'ecowatch-pin-wrapper',
    html: `
      <div style="position:relative;width:32px;height:40px;display:flex;align-items:center;justify-content:center;transform:${scale};transform-origin:bottom center;transition:transform 0.18s ease;">
        ${halo}
        <svg width="32" height="40" viewBox="0 0 32 40" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter:drop-shadow(0 3px 6px rgba(15,23,42,0.35));">
          <path d="M16 1C7.716 1 1 7.716 1 16C1 26.5 16 39 16 39C16 39 31 26.5 31 16C31 7.716 24.284 1 16 1Z" fill="${color}" stroke="white" stroke-width="2.2"/>
          <circle cx="16" cy="15.5" r="5.5" fill="white"/>
          <circle cx="16" cy="15.5" r="2.5" fill="${color}"/>
        </svg>
      </div>
    `,
    iconSize: [32, 40],
    iconAnchor: [16, 40],
    popupAnchor: [0, -36],
  })
}

function setTileLayer(layerKey: MapLayerKey) {
  if (!map) return
  activeLayer.value = layerKey
  if (currentTileLayer) {
    map.removeLayer(currentTileLayer)
  }

  if (layerKey === 'google_streets') {
    currentTileLayer = L.tileLayer('https://mt{s}.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}', {
      subdomains: ['0', '1', '2', '3'],
      maxZoom: 20,
      attribution: '&copy; Google Maps',
    })
  } else if (layerKey === 'google_hybrid') {
    currentTileLayer = L.tileLayer('https://mt{s}.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}', {
      subdomains: ['0', '1', '2', '3'],
      maxZoom: 20,
      attribution: '&copy; Google Satellite',
    })
  } else {
    currentTileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap',
    })
  }

  currentTileLayer.addTo(map)
}

function fitAllMarkers() {
  if (!map || !currentBounds || !currentBounds.isValid()) return
  map.fitBounds(currentBounds, { padding: [50, 50], maxZoom: 15 })
}

function updatePinStyles() {
  for (const [id, entry] of markerMap.entries()) {
    const isHighlighted = id === activeReportId.value || id === hoveredReportId.value
    entry.marker.setIcon(createPinIcon(entry.report.status, isHighlighted))
    entry.marker.setZIndexOffset(isHighlighted ? 500 : 0)
  }
}

function handleSidebarHover(reportId: number | null) {
  hoveredReportId.value = reportId
  updatePinStyles()
}

function focusReport(report: CommunityReport) {
  activeReportId.value = report.id
  pinnedPopupId.value = report.id
  updatePinStyles()
  const entry = markerMap.get(report.id)
  if (map && entry) {
    map.flyTo(entry.coords, Math.max(map.getZoom(), 15), { duration: 0.45 })
    entry.marker.openPopup()
  }
}

function getCoverPhoto(report: CommunityReport): string | null {
  if (report.photo_paths?.length) return resolvePhotoUrl(report.photo_paths[0])
  return report.photo_path ? resolvePhotoUrl(report.photo_path) : null
}

function renderMarkers() {
  if (!map || !markersLayer) return
  markersLayer.clearLayers()
  markerMap.clear()

  if (!props.reports.length) {
    currentBounds = null
    return
  }

  const bounds = L.latLngBounds([])
  const fallbackCounts = new Map<string, number>()

  for (const report of props.reports) {
    let lat: number
    let lng: number
    const rawLat = report.latitude !== null ? Number(report.latitude) : null
    const rawLng = report.longitude !== null ? Number(report.longitude) : null
    const hasValidCambodiaGps =
      rawLat !== null &&
      rawLng !== null &&
      rawLat >= 9.5 &&
      rawLat <= 15.0 &&
      rawLng >= 102.0 &&
      rawLng <= 108.0

    if (hasValidCambodiaGps) {
      lat = rawLat!
      lng = rawLng!
    } else {
      const [baseLat, baseLng] = getAreaCoordinates(report.province, report.district)
      const key = `${report.province}-${report.district ?? 'prov'}`
      const count = fallbackCounts.get(key) ?? 0
      fallbackCounts.set(key, count + 1)
      const angle = count * 1.4
      const radius = count === 0 ? 0 : 0.004 * Math.ceil(count / 4)
      lat = baseLat + radius * Math.cos(angle)
      lng = baseLng + radius * Math.sin(angle)
    }

    const color = getMarkerColor(report.status)
    const icon = createPinIcon(report.status, report.id === activeReportId.value)

    const areaName = report.district_name
      ? `${localizedCategory(report.district_name, report.district_name_km, locale.value)}, ${locale.value === 'km' ? report.province_name_km : report.province_name}`
      : (locale.value === 'km' ? report.province_name_km : report.province_name)

    const categoryLabel = localizedCategory(report.category_name, report.category_name_km, locale.value)
    const statusLabel = translateStatus(report.status, t)
    const coverPhoto = getCoverPhoto(report)

    const popupEl = document.createElement('div')
    popupEl.style.cssText = 'width:215px;font-family:inherit;overflow:hidden;border-radius:10px;background:#ffffff;'

    if (coverPhoto) {
      const imgWrap = document.createElement('div')
      imgWrap.style.cssText = 'position:relative;width:100%;height:84px;overflow:hidden;background:#f1f5f9;'
      const img = document.createElement('img')
      img.src = coverPhoto
      img.alt = report.title
      img.style.cssText = 'width:100%;height:100%;object-fit:cover;display:block;'
      imgWrap.appendChild(img)

      const statusChip = document.createElement('span')
      statusChip.style.cssText = `position:absolute;top:6px;left:6px;padding:1px 7px;border-radius:9999px;background:${color};color:white;font-size:10px;font-weight:700;box-shadow:0 1px 4px rgba(0,0,0,0.25);`
      statusChip.textContent = statusLabel
      imgWrap.appendChild(statusChip)

      popupEl.appendChild(imgWrap)
    }

    const bodyEl = document.createElement('div')
    bodyEl.style.cssText = 'padding:9px 10px;'

    const metaDiv = document.createElement('div')
    metaDiv.style.cssText = `font-size:10px;font-weight:600;color:${color};margin-bottom:2px;`
    metaDiv.textContent = coverPhoto ? categoryLabel : `${statusLabel} • ${categoryLabel}`
    bodyEl.appendChild(metaDiv)

    const titleDiv = document.createElement('div')
    titleDiv.style.cssText = 'font-size:12px;font-weight:700;line-height:1.3;color:#0f172a;margin-bottom:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;'
    titleDiv.textContent = report.title
    bodyEl.appendChild(titleDiv)

    const areaDiv = document.createElement('div')
    areaDiv.style.cssText = 'font-size:10px;color:#64748b;margin-bottom:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
    areaDiv.textContent = areaName
    bodyEl.appendChild(areaDiv)

    const actionsRow = document.createElement('div')
    actionsRow.style.cssText = 'display:flex;gap:5px;'

    const btn = document.createElement('button')
    btn.type = 'button'
    btn.style.cssText = 'flex:1;padding:5px 8px;border-radius:6px;background:#0f172a;color:white;font-size:11px;font-weight:600;border:none;cursor:pointer;transition:opacity 0.15s;'
    btn.textContent = t('community.viewDetails')
    btn.addEventListener('mouseenter', () => { btn.style.opacity = '0.9' })
    btn.addEventListener('mouseleave', () => { btn.style.opacity = '1' })
    btn.addEventListener('click', () => emit('select-report', report))
    actionsRow.appendChild(btn)

    if (hasValidCambodiaGps) {
      const mapsLink = document.createElement('a')
      mapsLink.href = `https://www.google.com/maps?q=${lat},${lng}`
      mapsLink.target = '_blank'
      mapsLink.rel = 'noopener noreferrer'
      mapsLink.style.cssText = 'padding:5px 8px;border-radius:6px;background:#f8fafc;color:#0f172a;font-size:11px;font-weight:600;text-decoration:none;border:1px solid #e2e8f0;'
      mapsLink.textContent = 'Maps'
      actionsRow.appendChild(mapsLink)
    }

    bodyEl.appendChild(actionsRow)
    popupEl.appendChild(bodyEl)

    const marker = L.marker([lat, lng], { icon }).bindPopup(popupEl, {
      maxWidth: 230,
      autoPanPaddingTopLeft: L.point(16, 48),
      autoPanPaddingBottomRight: L.point(16, 48),
      className: 'ecowatch-popup',
      closeButton: true,
    })

    // Keep popup open while hovering over the popup card itself
    popupEl.addEventListener('mouseenter', () => {
      if (closeHoverTimer) {
        clearTimeout(closeHoverTimer)
        closeHoverTimer = null
      }
    })
    popupEl.addEventListener('mouseleave', () => {
      if (pinnedPopupId.value !== report.id) {
        closeHoverTimer = setTimeout(() => {
          marker.closePopup()
          if (hoveredReportId.value === report.id) {
            hoveredReportId.value = null
            updatePinStyles()
          }
        }, 220)
      }
    })

    marker.on('mouseover', () => {
      if (closeHoverTimer) {
        clearTimeout(closeHoverTimer)
        closeHoverTimer = null
      }
      hoveredReportId.value = report.id
      updatePinStyles()
      marker.openPopup()
    })

    marker.on('mouseout', () => {
      if (pinnedPopupId.value !== report.id) {
        closeHoverTimer = setTimeout(() => {
          marker.closePopup()
          if (hoveredReportId.value === report.id) {
            hoveredReportId.value = null
            updatePinStyles()
          }
        }, 250)
      }
    })

    marker.on('click', () => {
      activeReportId.value = report.id
      pinnedPopupId.value = report.id
      updatePinStyles()
      marker.openPopup()
    })

    marker.on('popupclose', () => {
      if (pinnedPopupId.value === report.id) {
        pinnedPopupId.value = null
      }
      if (activeReportId.value === report.id) {
        activeReportId.value = null
      }
      if (hoveredReportId.value === report.id) {
        hoveredReportId.value = null
      }
      updatePinStyles()
    })

    markersLayer.addLayer(marker)
    markerMap.set(report.id, { marker, coords: [lat, lng], report })
    bounds.extend([lat, lng])
  }

  currentBounds = bounds
  fitAllMarkers()
}

onMounted(() => {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value, {
    center: [11.5564, 104.9282],
    zoom: 12,
    scrollWheelZoom: false,
  })

  setTileLayer(activeLayer.value)
  markersLayer = L.layerGroup().addTo(map)
  renderMarkers()
  setTimeout(() => map?.invalidateSize(), 150)
})

watch(() => [props.reports, locale.value], () => {
  renderMarkers()
})

onUnmounted(() => {
  if (closeHoverTimer) clearTimeout(closeHoverTimer)
  map?.remove()
  map = null
  markersLayer = null
  currentTileLayer = null
})
</script>

<template>
  <div class="isolate grid overflow-hidden rounded-xl border bg-card shadow-xs lg:grid-cols-[1fr_16.5rem]">
    <!-- Map Canvas -->
    <div class="relative">
      <div ref="mapContainer" class="h-[320px] w-full sm:h-[380px]" />

      <!-- Top-Right Controls: Layer Switcher & Recenter -->
      <div class="absolute right-3 top-3 z-[400] flex flex-wrap items-center gap-1.5">
        <div class="inline-flex items-center rounded-lg border bg-background/95 p-0.5 text-[11px] font-medium shadow-sm backdrop-blur-xs">
          <button
            type="button"
            class="rounded-md px-2 py-1 transition-colors"
            :class="activeLayer === 'google_streets' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
            @click="setTileLayer('google_streets')"
          >
            {{ t('submitReport.mapLayerStreets') }}
          </button>
          <button
            type="button"
            class="rounded-md px-2 py-1 transition-colors"
            :class="activeLayer === 'google_hybrid' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
            @click="setTileLayer('google_hybrid')"
          >
            {{ t('submitReport.mapLayerSatellite') }}
          </button>
          <button
            type="button"
            class="rounded-md px-2 py-1 transition-colors"
            :class="activeLayer === 'osm' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
            @click="setTileLayer('osm')"
          >
            {{ t('submitReport.mapLayerOsm') }}
          </button>
        </div>

        <button
          type="button"
          class="inline-flex h-7 w-7 items-center justify-center rounded-lg border bg-background/95 text-foreground shadow-sm backdrop-blur-xs transition-colors hover:bg-accent"
          :title="t('community.resetFilters')"
          @click="fitAllMarkers"
        >
          <LocateFixed class="h-3.5 w-3.5 text-primary" />
        </button>
      </div>

      <!-- Bottom-Left Privacy Notice -->
      <div class="pointer-events-none absolute bottom-3 left-3 z-[400] inline-flex max-w-[65%] items-center gap-1.5 rounded-lg border bg-background/90 px-2.5 py-1.5 text-[11px] text-muted-foreground shadow-sm backdrop-blur-xs">
        <ShieldCheck class="h-3.5 w-3.5 shrink-0 text-primary" />
        <span class="truncate">{{ t('community.mapApproximateNote') }}</span>
      </div>

      <!-- Bottom-Right Status Legend -->
      <div class="pointer-events-none absolute bottom-3 right-3 z-[400] hidden items-center gap-2.5 rounded-lg border bg-background/90 px-2.5 py-1.5 text-[11px] font-medium text-foreground shadow-sm backdrop-blur-xs sm:inline-flex">
        <span class="inline-flex items-center gap-1">
          <span class="h-2.5 w-2.5 rounded-full bg-amber-600" />
          {{ t('status.pending') }}
        </span>
        <span class="inline-flex items-center gap-1">
          <span class="h-2.5 w-2.5 rounded-full bg-blue-600" />
          {{ t('status.inProgress') }}
        </span>
        <span class="inline-flex items-center gap-1">
          <span class="h-2.5 w-2.5 rounded-full bg-emerald-600" />
          {{ t('status.resolved') }}
        </span>
      </div>
    </div>

    <!-- Side Pin List -->
    <aside class="flex max-h-[220px] flex-col border-t bg-card lg:max-h-[380px] lg:border-l lg:border-t-0">
      <div class="flex items-center justify-between border-b px-3 py-2">
        <h2 class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          {{ t('community.totalShown') }}
        </h2>
        <span class="rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-semibold tabular-nums text-foreground">
          {{ reports.length }}
        </span>
      </div>

      <ul class="flex-1 divide-y overflow-y-auto">
        <li
          v-for="report in reports"
          :key="report.id"
          class="cursor-pointer px-3 py-2 transition-colors hover:bg-muted/40"
          :class="{ 'bg-primary/5 ring-1 ring-inset ring-primary/30': activeReportId === report.id || hoveredReportId === report.id }"
          @click="focusReport(report)"
          @mouseenter="handleSidebarHover(report.id)"
          @mouseleave="handleSidebarHover(null)"
        >
          <div class="flex items-center gap-2.5">
            <div class="relative h-10 w-12 shrink-0 overflow-hidden rounded-md border bg-muted">
              <img
                v-if="getCoverPhoto(report)"
                :src="getCoverPhoto(report)!"
                :alt="report.title"
                class="h-full w-full object-cover"
                loading="lazy"
              />
              <div v-else class="flex h-full w-full items-center justify-center text-muted-foreground/50">
                <Camera class="h-3.5 w-3.5" />
              </div>
            </div>

            <div class="min-w-0 flex-1 space-y-0.5">
              <div class="flex items-center justify-between gap-1">
                <span class="font-mono text-[10px] font-semibold text-muted-foreground">#{{ report.id }}</span>
                <StatusBadge :status="report.status" class="origin-right scale-[0.8]" />
              </div>
              <p class="line-clamp-1 text-[11px] font-semibold text-foreground">
                {{ report.title }}
              </p>
              <div class="flex items-center justify-between gap-1.5 text-[10px] text-muted-foreground">
                <p class="flex min-w-0 items-center gap-0.5 truncate">
                  <MapPin class="h-2.5 w-2.5 shrink-0 text-primary" />
                  <span class="truncate">
                    <template v-if="report.district_name">
                      {{ localizedCategory(report.district_name, report.district_name_km, locale) }}
                    </template>
                    <template v-else>
                      {{ locale === 'km' ? report.province_name_km : report.province_name }}
                    </template>
                  </span>
                </p>
                <button
                  type="button"
                  class="shrink-0 font-medium text-primary hover:underline"
                  @click.stop="emit('select-report', report)"
                >
                  {{ t('community.viewDetails') }} →
                </button>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </aside>
  </div>
</template>

<style>
.ecowatch-popup .leaflet-popup-content-wrapper {
  padding: 0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 30px -6px rgba(15, 23, 42, 0.25), 0 4px 12px -2px rgba(15, 23, 42, 0.12);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.ecowatch-popup .leaflet-popup-content {
  margin: 0;
  width: auto !important;
}

.ecowatch-popup .leaflet-popup-close-button {
  position: absolute !important;
  top: 6px !important;
  right: 6px !important;
  width: 22px !important;
  height: 22px !important;
  padding: 0 !important;
  border-radius: 9999px;
  background: rgba(15, 23, 42, 0.6) !important;
  color: #ffffff !important;
  display: flex !important;
  align-items: center;
  justify-content: center;
  font-size: 14px !important;
  line-height: 1 !important;
  backdrop-filter: blur(4px);
  z-index: 10;
}

.ecowatch-popup .leaflet-popup-close-button:hover {
  background: rgba(15, 23, 42, 0.85) !important;
}
</style>
