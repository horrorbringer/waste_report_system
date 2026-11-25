<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Compass, RotateCcw } from 'lucide-vue-next'

const props = defineProps<{
  latitude: number
  longitude: number
  title?: string
}>()

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let marker: L.Marker | null = null

const pinIcon = L.divIcon({
  className: 'ecowatch-mini-pin',
  html: `
    <div style="position:relative;display:flex;align-items:center;justify-content:center;width:32px;height:32px;">
      <span style="position:absolute;width:28px;height:28px;border-radius:9999px;background:rgba(16,185,129,0.25);"></span>
      <span style="position:relative;width:14px;height:14px;border-radius:9999px;background:#ef4444;border:2.5px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.35);"></span>
    </div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
})

function initMap() {
  if (!mapContainer.value || map) return

  map = L.map(mapContainer.value, {
    center: [props.latitude, props.longitude],
    zoom: 16,
    zoomControl: true,
    attributionControl: false,
    scrollWheelZoom: false,
  })

  L.tileLayer('https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
    subdomains: ['0', '1', '2', '3'],
    maxZoom: 20,
  }).addTo(map)

  marker = L.marker([props.latitude, props.longitude], { icon: pinIcon }).addTo(map)
  if (props.title) {
    marker.bindTooltip(props.title, { direction: 'top', offset: [0, -10] })
  }

  setTimeout(() => {
    map?.invalidateSize()
  }, 150)
}

function recenter() {
  if (!map) return
  map.setView([props.latitude, props.longitude], 16, { animate: true })
}

onMounted(() => {
  initMap()
})

watch(
  () => [props.latitude, props.longitude],
  ([lat, lng]) => {
    if (!map || !marker) return
    marker.setLatLng([lat, lng])
    map.setView([lat, lng], 16)
  },
)

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
    marker = null
  }
})
</script>

<template>
  <div class="relative h-56 w-full overflow-hidden rounded-xl border border-border/70 bg-muted/30">
    <div ref="mapContainer" class="h-full w-full z-0" />

    <!-- Coordinate Pill -->
    <div class="pointer-events-none absolute left-2.5 top-2.5 z-[400] inline-flex items-center gap-1.5 rounded-lg border border-border/80 bg-background/95 px-2.5 py-1 font-mono text-[11px] font-medium text-foreground shadow-sm backdrop-blur-xs">
      <Compass class="h-3 w-3 text-primary" />
      <span class="tabular-nums">{{ latitude.toFixed(5) }}, {{ longitude.toFixed(5) }}</span>
    </div>

    <!-- Recenter Button -->
    <button
      type="button"
      class="absolute bottom-2.5 right-2.5 z-[400] inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border/80 bg-background/95 text-foreground shadow-sm backdrop-blur-xs transition hover:bg-accent hover:text-primary"
      title="Recenter map"
      @click="recenter"
    >
      <RotateCcw class="h-3.5 w-3.5" />
    </button>
  </div>
</template>
