<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const isNavigating = ref(false)

onMounted(() => {
  if (auth.token) {
    auth.fetchMe()
  }

  // Smooth route transition progress bar
  router.beforeEach((to, from, next) => {
    if (to.path !== from.path) {
      isNavigating.value = true
    }
    next()
  })

  router.afterEach(() => {
    setTimeout(() => {
      isNavigating.value = false
    }, 120)
  })
})
</script>

<template>
  <div class="relative min-h-screen">
    <!-- Top Route Loading Progress Bar -->
    <div
      v-if="isNavigating"
      class="fixed top-0 left-0 right-0 z-50 h-0.5 bg-primary/20 overflow-hidden pointer-events-none"
    >
      <div class="absolute inset-y-0 bg-primary animate-route-bar" />
    </div>

    <!-- Smooth Page Route Transitions -->
    <RouterView v-slot="{ Component, route }">
      <Transition name="page" mode="out-in">
        <component :is="Component" :key="route.fullPath" />
      </Transition>
    </RouterView>
  </div>
</template>
