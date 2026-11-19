<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import {
  Compass,
  MapPin,
  Navigation,
  X,
  Check,
  RotateCcw,
  Sparkles,
  Loader2,
  Search,
  Layers,
  Map as MapIcon,
  Globe,
  Zap,
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const props = defineProps<{
  open: boolean
  initialLat?: number | string | null
  initialLng?: number | string | null
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'select-location', payload: { lat: number; lng: number; address?: string }): void
}>()

const { t } = useI18n()

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let marker: L.Marker | null = null
let currentTileLayer: L.TileLayer | null = null

type MapLayerKey = 'google_streets' | 'google_hybrid' | 'fast_osm'
const activeLayer = ref<MapLayerKey>('google_streets')
const isMapLoading = ref(false)

const selectedLat = ref<number>(11.5564)
const selectedLng = ref<number>(104.9282)
const detectedAddress = ref<string>('')
const resolvingAddress = ref<boolean>(false)
const locating = ref<boolean>(false)

// Place search state
const searchQuery = ref('')
const searching = ref(false)
const searchError = ref('')

// Popular Cambodia landmark shortcuts
const popularLandmarks = [
  { key: 'landmarkCentralMarket', lat: 11.5696, lng: 104.9211 },
  { key: 'landmarkIndependence', lat: 11.5564, lng: 104.9282 },
  { key: 'landmarkBkk1', lat: 11.5508, lng: 104.9265 },
  { key: 'landmarkRussianMarket', lat: 11.5407, lng: 104.9147 },
  { key: 'landmarkWatPhnom', lat: 11.5760, lng: 104.9230 },
  { key: 'landmarkToulKork', lat: 11.5833, lng: 104.8967 },
]

// Authentic Google Maps-style red teardrop pin with radial ground shadow
const pinIcon = L.divIcon({
  className: 'authentic-map-pin',
  html: `
    <div style="position: relative; width: 38px; height: 48px; transform: translate(-19px, -46px); pointer-events: auto;">
      <!-- Ground soft contact shadow -->
      <div style="position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 14px; height: 5px; background: rgba(0,0,0,0.35); border-radius: 50%; filter: blur(1.5px);"></div>
      <!-- Authentic Google Red Pin -->
      <svg width="38" height="46" viewBox="0 0 384 512" style="position: absolute; top: 0; left: 0; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.35));">
        <path fill="#EA4335" d="M172.268 501.67C26.97 291.031 0 269.413 0 192 0 85.961 85.961 0 192 0s192 85.961 192 192c0 77.413-26.97 99.031-172.268 309.67-9.535 13.774-29.93 13.773-39.464 0z"/>
        <circle cx="192" cy="192" r="82" fill="#FFFFFF"/>
        <circle cx="192" cy="192" r="48" fill="#B31412"/>
      </svg>
    </div>
  `,
  iconSize: [38, 48],
  iconAnchor: [19, 46],
  popupAnchor: [0, -46],
})

const layerConfigs: Record<MapLayerKey, { url: string; options: L.TileLayerOptions }> = {
  google_streets: {
    url: 'https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    options: {
      maxZoom: 20,
      subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
      attribution: '&copy; Google Maps',
    },
  },
  google_hybrid: {
    url: 'https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    options: {
      maxZoom: 20,
      subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
      attribution: '&copy; Google Satellite Imagery',
    },
  },
  fast_osm: {
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    options: {
      maxZoom: 19,
      subdomains: ['a', 'b', 'c', 'd'],
      attribution: '&copy; CARTO &copy; OpenStreetMap',
    },
  },
}

function attachTileLayer(layerKey: MapLayerKey) {
  if (!map) return
  if (currentTileLayer) {
    map.removeLayer(currentTileLayer)
    currentTileLayer = null
  }

  activeLayer.value = layerKey
  const cfg = layerConfigs[layerKey]
  isMapLoading.value = true

  currentTileLayer = L.tileLayer(cfg.url, cfg.options).addTo(map)

  currentTileLayer.on('loading', () => {
    isMapLoading.value = true
  })
  currentTileLayer.on('load', () => {
    isMapLoading.value = false
  })
  currentTileLayer.on('tileerror', () => {
    isMapLoading.value = false
  })
}

function setLayer(layerKey: MapLayerKey) {
  attachTileLayer(layerKey)
}

async function reverseGeocode(lat: number, lng: number) {
  resolvingAddress.value = true
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`,
      { headers: { 'User-Agent': 'EcoWatch-Community-App/1.0' } }
    )
    if (res.ok) {
      const data = await res.json()
      if (data && data.display_name) {
        detectedAddress.value = data.display_name
      }
    }
  } catch {
    // Gracefully ignore network timeout
  } finally {
    resolvingAddress.value = false
  }
}

function updateMarkerPosition(lat: number, lng: number, shouldGeocode = true) {
  selectedLat.value = Number(lat.toFixed(6))
  selectedLng.value = Number(lng.toFixed(6))

  if (marker) {
    marker.setLatLng([selectedLat.value, selectedLng.value])
  }

  if (shouldGeocode) {
    reverseGeocode(selectedLat.value, selectedLng.value)
  }
}

function jumpToLandmark(landmark: { lat: number; lng: number }) {
  updateMarkerPosition(landmark.lat, landmark.lng)
  map?.flyTo([landmark.lat, landmark.lng], 16, { duration: 0.8 })
}

async function searchLocation() {
  const query = searchQuery.value.trim()
  if (!query) return

  searching.value = true
  searchError.value = ''

  try {
    const qParam = encodeURIComponent(`${query}, Cambodia`)
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${qParam}&limit=3`,
      { headers: { 'User-Agent': 'EcoWatch-Community-App/1.0' } }
    )
    if (res.ok) {
      const data = await res.json()
      if (data && data.length > 0) {
        const best = data[0]
        const lat = parseFloat(best.lat)
        const lng = parseFloat(best.lon)
        updateMarkerPosition(lat, lng)
        detectedAddress.value = best.display_name
        map?.flyTo([lat, lng], 17, { duration: 1.0 })
      } else {
        searchError.value = 'Location not found. Try another landmark name.'
      }
    }
  } catch {
    searchError.value = 'Failed to search location.'
  } finally {
    searching.value = false
  }
}

function initMap() {
  if (!mapContainer.value) return
  if (map) {
    map.remove()
    map = null
    currentTileLayer = null
  }

  const rawLat = Number(props.initialLat)
  const rawLng = Number(props.initialLng)
  const hasCoords = !isNaN(rawLat) && !isNaN(rawLng) && rawLat !== 0 && rawLng !== 0

  const initialCenter: [number, number] = hasCoords
    ? [rawLat, rawLng]
    : [11.5564, 104.9282] // Phnom Penh Independence Monument

  selectedLat.value = initialCenter[0]
  selectedLng.value = initialCenter[1]

  map = L.map(mapContainer.value, {
    center: initialCenter,
    zoom: hasCoords ? 16 : 14,
    zoomControl: false,
  })

  // Attach active tile layer
  attachTileLayer(activeLayer.value)

  // Zoom control positioned bottom-left
  L.control.zoom({ position: 'bottomleft' }).addTo(map)

  // Add draggable custom marker
  marker = L.marker(initialCenter, {
    icon: pinIcon,
    draggable: true,
  }).addTo(map)

  // Marker dragend event
  marker.on('dragend', () => {
    if (!marker) return
    const pos = marker.getLatLng()
    updateMarkerPosition(pos.lat, pos.lng)
  })

  // Map click event
  map.on('click', (e: L.LeafletMouseEvent) => {
    updateMarkerPosition(e.latlng.lat, e.latlng.lng)
  })

  if (hasCoords) {
    reverseGeocode(selectedLat.value, selectedLng.value)
  }
}

function mountMapWhenReady(attempt = 0) {
  if (mapContainer.value && mapContainer.value.clientHeight > 50) {
    initMap()
    setTimeout(() => map?.invalidateSize(), 50)
    setTimeout(() => map?.invalidateSize(), 150)
    setTimeout(() => map?.invalidateSize(), 300)
    setTimeout(() => map?.invalidateSize(), 600)
  } else if (attempt < 20) {
    setTimeout(() => mountMapWhenReady(attempt + 1), 40)
  }
}

function locateUser() {
  if (!navigator.geolocation || !map) return
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude
      const lng = pos.coords.longitude
      updateMarkerPosition(lat, lng)
      map?.flyTo([lat, lng], 17, { duration: 1.0 })
      locating.value = false
    },
    () => {
      locating.value = false
    },
    { enableHighAccuracy: true, timeout: 8000 }
  )
}

function confirmSelection() {
  emit('select-location', {
    lat: selectedLat.value,
    lng: selectedLng.value,
    address: detectedAddress.value || undefined,
  })
  emit('update:open', false)
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      searchQuery.value = ''
      searchError.value = ''
      nextTick(() => {
        mountMapWhenReady(0)
      })
    } else {
      if (map) {
        map.remove()
        map = null
        marker = null
        currentTileLayer = null
      }
    }
  }
)

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
    currentTileLayer = null
  }
})
</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent
      class="max-w-4xl w-[95vw] sm:w-full max-h-[90vh] flex flex-col overflow-hidden p-0 gap-0 border border-border shadow-2xl rounded-2xl"
    >
      <!-- Header with responsive padding -->
      <div class="shrink-0 border-b bg-card px-4 sm:px-5 py-2.5 sm:py-3 pr-12 sm:pr-14">
        <DialogHeader>
          <div class="flex items-center gap-2 sm:gap-2.5">
            <div class="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-xl bg-primary/10 text-primary shrink-0">
              <MapPin class="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            </div>
            <div class="min-w-0">
              <DialogTitle class="text-sm sm:text-base font-semibold leading-tight truncate">
                {{ t('submitReport.mapDialogTitle') }}
              </DialogTitle>
              <DialogDescription class="text-[11px] sm:text-xs text-muted-foreground truncate">
                {{ t('submitReport.mapDialogDesc') }}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
      </div>

      <!-- Search & Popular Landmark Bar -->
      <div class="shrink-0 border-b bg-muted/30 px-3 sm:px-5 py-2 sm:py-2.5 space-y-1.5 sm:space-y-2">
        <form class="flex items-center gap-1.5 sm:gap-2" @submit.prevent="searchLocation">
          <div class="relative flex-1">
            <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              v-model="searchQuery"
              :placeholder="t('submitReport.mapSearchPlaceholder')"
              class="h-8 sm:h-8.5 pl-8 pr-7 text-xs bg-background/90"
            />
            <button
              v-if="searchQuery"
              type="button"
              class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              @click="searchQuery = ''"
            >
              <X class="h-3 w-3" />
            </button>
          </div>
          <Button
            type="submit"
            size="sm"
            variant="secondary"
            class="h-8 sm:h-8.5 px-2.5 sm:px-3 text-xs gap-1 shrink-0"
            :disabled="searching || !searchQuery.trim()"
          >
            <Loader2 v-if="searching" class="h-3 w-3 animate-spin" />
            <Search v-else class="h-3 w-3" />
            <span class="hidden sm:inline">Search</span>
          </Button>
        </form>

        <!-- Popular Cambodia Landmarks -->
        <div class="flex items-center gap-1 sm:gap-1.5 overflow-x-auto pb-0.5 text-[10px] sm:text-[11px] scrollbar-none">
          <span class="text-muted-foreground font-medium shrink-0">
            {{ t('submitReport.quickLandmarks') }}
          </span>
          <button
            v-for="l in popularLandmarks"
            :key="l.key"
            type="button"
            class="shrink-0 rounded-md border bg-background/80 px-1.5 sm:px-2 py-0.5 font-medium text-foreground transition hover:border-primary hover:bg-primary/5 hover:text-primary"
            @click="jumpToLandmark(l)"
          >
            {{ t(`submitReport.${l.key}`) }}
          </button>
        </div>

        <p v-if="searchError" class="text-[11px] text-destructive">
          {{ searchError }}
        </p>
      </div>

      <!-- Map Viewport with guaranteed explicit height -->
      <div class="relative w-full h-[290px] sm:h-[380px] bg-slate-100 dark:bg-slate-900 overflow-hidden">
        <div ref="mapContainer" class="h-full w-full z-0" />

        <!-- Floating Coordinates Badge (Top-left on map, responsive sizing) -->
        <div class="absolute top-2.5 left-2.5 sm:top-3 sm:left-3 z-[400] pointer-events-none">
          <Badge
            variant="outline"
            class="pointer-events-auto gap-1 border-border/70 bg-background/95 px-2 py-0.5 sm:px-2.5 sm:py-1 font-mono text-[10px] sm:text-[11px] tabular-nums shadow-md backdrop-blur-sm"
          >
            <Compass class="h-2.5 w-2.5 sm:h-3 sm:w-3 text-primary" />
            <span>{{ selectedLat }}, {{ selectedLng }}</span>
          </Badge>
        </div>

        <!-- Floating Loading Badge -->
        <div
          v-if="isMapLoading"
          class="absolute top-2.5 left-1/2 -translate-x-1/2 z-[400] flex items-center gap-1.5 rounded-full border border-border/80 bg-background/95 px-2.5 py-0.5 sm:px-3 sm:py-1 text-[10px] sm:text-[11px] font-medium shadow-md backdrop-blur-sm text-muted-foreground"
        >
          <Loader2 class="h-3 w-3 animate-spin text-primary" />
          <span>Loading...</span>
        </div>

        <!-- Floating Layer Mode Selector (Top-right on map, responsive labels) -->
        <div class="absolute top-2.5 right-2.5 sm:top-3 sm:right-3 z-[400]">
          <div class="inline-flex rounded-lg border border-border/80 bg-background/95 p-0.5 text-xs font-medium shadow-md backdrop-blur-sm">
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-md px-1.5 sm:px-2 py-0.5 sm:py-1 text-[10px] sm:text-[11px] transition"
              :class="
                activeLayer === 'google_streets'
                  ? 'bg-primary text-primary-foreground font-semibold shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              "
              @click="setLayer('google_streets')"
            >
              <MapIcon class="h-3 w-3" />
              <span class="hidden sm:inline">{{ t('submitReport.mapLayerStreets') }}</span>
              <span class="sm:hidden">Map</span>
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-md px-1.5 sm:px-2 py-0.5 sm:py-1 text-[10px] sm:text-[11px] transition"
              :class="
                activeLayer === 'google_hybrid'
                  ? 'bg-primary text-primary-foreground font-semibold shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              "
              @click="setLayer('google_hybrid')"
            >
              <Globe class="h-3 w-3" />
              <span class="hidden sm:inline">{{ t('submitReport.mapLayerSatellite') }}</span>
              <span class="sm:hidden">Sat</span>
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-md px-1.5 sm:px-2 py-0.5 sm:py-1 text-[10px] sm:text-[11px] transition"
              :class="
                activeLayer === 'fast_osm'
                  ? 'bg-primary text-primary-foreground font-semibold shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              "
              @click="setLayer('fast_osm')"
            >
              <Zap class="h-3 w-3 text-amber-500" />
              <span class="hidden sm:inline">Fast OSM</span>
              <span class="sm:hidden">OSM</span>
            </button>
          </div>
        </div>

        <!-- Floating "Locate Me" Button (Bottom-right on map) -->
        <div class="absolute bottom-2.5 right-2.5 sm:bottom-3 sm:right-3 z-[400]">
          <Button
            type="button"
            size="sm"
            variant="secondary"
            class="h-7 sm:h-8 gap-1 rounded-lg bg-background/95 px-2.5 sm:px-3 text-[11px] sm:text-xs font-medium shadow-md backdrop-blur-sm hover:bg-background border"
            :disabled="locating"
            @click="locateUser"
          >
            <Navigation class="h-3 w-3 sm:h-3.5 sm:w-3.5 text-primary" :class="{ 'animate-spin': locating }" />
            <span class="hidden sm:inline">{{ t('submitReport.locateMe') }}</span>
            <span class="sm:hidden">GPS</span>
          </Button>
        </div>
      </div>

      <!-- Footer Info & Action Bar (Shrink-0 so never cut off) -->
      <div class="shrink-0 flex flex-col gap-2 border-t bg-card px-3 sm:px-5 py-2.5 sm:py-3 sm:flex-row sm:items-center sm:justify-between">
        <!-- Reverse Geocoded Address Preview -->
        <div class="min-w-0 flex-1">
          <div v-if="resolvingAddress" class="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Loader2 class="h-3 w-3 animate-spin text-primary" />
            <span class="text-[11px] sm:text-xs">{{ t('submitReport.detectingAddress') }}</span>
          </div>
          <div v-else-if="detectedAddress" class="space-y-0.5">
            <span class="text-[9px] sm:text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              {{ t('submitReport.addressDetected') }}
            </span>
            <p class="truncate text-[11px] sm:text-xs font-medium text-foreground" :title="detectedAddress">
              {{ detectedAddress }}
            </p>
          </div>
          <div v-else class="text-[10px] sm:text-[11px] text-muted-foreground">
            Click anywhere on the map or drag the pin to set exact coordinates.
          </div>
        </div>

        <!-- Confirm / Cancel Buttons (Full-width on mobile) -->
        <div class="flex items-center justify-end gap-2 shrink-0 w-full sm:w-auto">
          <Button
            type="button"
            variant="outline"
            size="sm"
            class="h-8 sm:h-8.5 px-3 text-xs flex-1 sm:flex-initial"
            @click="emit('update:open', false)"
          >
            {{ t('common.cancel') }}
          </Button>

          <Button
            type="button"
            size="sm"
            class="h-8 sm:h-8.5 px-4 gap-1.5 text-xs font-semibold shadow-sm flex-1 sm:flex-initial"
            @click="confirmSelection"
          >
            <Check class="h-3.5 w-3.5 stroke-[3]" />
            {{ t('submitReport.confirmLocation') }}
          </Button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

<style>
/* Leaflet layer fix within Radix dialog */
.leaflet-pane {
  z-index: 10 !important;
}
.leaflet-top,
.leaflet-bottom {
  z-index: 20 !important;
}
.authentic-map-pin {
  background: transparent !important;
  border: none !important;
  cursor: grab;
}
.authentic-map-pin:active {
  cursor: grabbing;
}
</style>
