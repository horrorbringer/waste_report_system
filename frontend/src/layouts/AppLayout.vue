<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Leaf,
  PlusCircle,
  ClipboardList,
  ShieldCheck,
  LogOut,
  LogIn,
  UserPlus,
  Home,
  Users,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { translateRole } from '@/i18n'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

function handleLogout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <div class="flex min-h-screen flex-col bg-background">
    <!-- Main Top Header -->
    <header class="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div class="container flex h-14 sm:h-16 items-center justify-between gap-2 sm:gap-4 px-3 sm:px-6">
        <!-- Brand Logo & Desktop Navigation -->
        <div class="flex items-center gap-3 sm:gap-6 min-w-0">
          <RouterLink to="/" class="flex items-center gap-2 font-display font-bold tracking-tight shrink-0">
            <div class="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <Leaf class="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            </div>
            <span class="text-base sm:text-lg tracking-[-0.02em] font-extrabold truncate">{{ t('brand.name') }}</span>
          </RouterLink>

          <!-- Desktop Navigation Bar -->
          <nav class="hidden items-center gap-1 md:flex">
            <RouterLink to="/">
              <Button :variant="route.path === '/' ? 'secondary' : 'ghost'" size="sm" class="gap-1.5 text-xs">
                <Home class="h-3.5 w-3.5" />
                {{ t('nav.home') }}
              </Button>
            </RouterLink>

            <Button as-child :variant="route.name === 'community-reports' ? 'secondary' : 'ghost'" size="sm" class="gap-1.5 text-xs">
              <RouterLink :to="{ name: 'community-reports' }">
                <Users class="h-3.5 w-3.5" />
                {{ t('community.nav') }}
              </RouterLink>
            </Button>

            <template v-if="auth.isAuthenticated">
              <RouterLink to="/reports/new">
                <Button :variant="route.path === '/reports/new' ? 'secondary' : 'ghost'" size="sm" class="gap-1.5 text-xs">
                  <PlusCircle class="h-3.5 w-3.5 text-primary" />
                  {{ t('nav.reportWaste') }}
                </Button>
              </RouterLink>

              <RouterLink to="/my-reports">
                <Button :variant="route.path === '/my-reports' ? 'secondary' : 'ghost'" size="sm" class="gap-1.5 text-xs">
                  <ClipboardList class="h-3.5 w-3.5" />
                  {{ t('nav.myReports') }}
                </Button>
              </RouterLink>

              <RouterLink v-if="auth.isStaff" to="/admin/dashboard">
                <Button variant="outline" size="sm" class="ml-1 border-primary/40 text-primary hover:bg-primary/10 gap-1.5 text-xs">
                  <ShieldCheck class="h-3.5 w-3.5" />
                  {{ t('nav.adminPortal') }}
                </Button>
              </RouterLink>
            </template>
          </nav>
        </div>

        <!-- Right Side: Language Switcher, User Status, Auth Actions -->
        <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
          <LanguageSwitcher />

          <template v-if="auth.isAuthenticated && auth.user">
            <div class="hidden items-center gap-2 lg:flex">
              <span class="text-xs sm:text-sm font-medium truncate max-w-[120px]">{{ auth.user.full_name }}</span>
              <Badge :variant="auth.isStaff ? 'default' : 'secondary'" class="text-[10px] px-2 py-0.5">
                {{ translateRole(auth.user.role, t) }}
              </Badge>
            </div>
            <Button variant="ghost" size="sm" class="h-8 px-2 sm:px-3 text-xs gap-1" @click="handleLogout">
              <LogOut class="h-3.5 w-3.5" />
              <span class="hidden sm:inline">{{ t('nav.signOut') }}</span>
            </Button>
          </template>

          <template v-else>
            <RouterLink to="/login">
              <Button variant="ghost" size="sm" class="h-8 px-2 sm:px-3 text-xs gap-1">
                <LogIn class="h-3.5 w-3.5" />
                <span class="hidden sm:inline">{{ t('nav.signIn') }}</span>
              </Button>
            </RouterLink>
            <RouterLink to="/register">
              <Button size="sm" class="h-8 px-2.5 sm:px-3 text-xs font-semibold shadow-sm">
                <UserPlus class="h-3.5 w-3.5 sm:mr-1" />
                <span class="hidden sm:inline">{{ t('nav.getStarted') }}</span>
                <span class="sm:hidden">Join</span>
              </Button>
            </RouterLink>
          </template>
        </div>
      </div>
    </header>

    <!-- Main Content with bottom padding for mobile bar -->
    <main class="flex-1 pb-16 md:pb-0">
      <slot />
    </main>

    <!-- Mobile Bottom Navigation Bar (md:hidden) -->
    <nav class="fixed bottom-0 left-0 right-0 z-50 flex h-14 items-center justify-around border-t bg-background/95 px-2 backdrop-blur supports-[backdrop-filter]:bg-background/85 md:hidden shadow-lg">
      <RouterLink
        to="/"
        class="flex flex-col items-center justify-center gap-0.5 text-[10px] font-medium transition py-1"
        :class="route.path === '/' ? 'text-primary font-bold' : 'text-muted-foreground hover:text-foreground'"
      >
        <Home class="h-4 w-4" />
        <span>{{ t('nav.home') }}</span>
      </RouterLink>

      <RouterLink
        :to="{ name: 'community-reports' }"
        class="flex flex-col items-center justify-center gap-0.5 py-1 text-[10px] font-medium transition"
        :class="route.name === 'community-reports' ? 'font-bold text-primary' : 'text-muted-foreground hover:text-foreground'"
      >
        <Users class="h-4 w-4" />
        <span>{{ t('community.nav') }}</span>
      </RouterLink>

      <RouterLink
        :to="auth.isAuthenticated ? '/reports/new' : '/login?redirect=/reports/new'"
        class="relative -top-2 flex flex-col items-center justify-center gap-0.5"
      >
        <div class="flex h-11 w-11 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-md shadow-primary/30 transition hover:scale-105 active:scale-95">
          <PlusCircle class="h-6 w-6 stroke-[2.2]" />
        </div>
        <span class="text-[10px] font-bold text-primary">{{ t('nav.reportShort') }}</span>
      </RouterLink>

      <RouterLink
        v-if="auth.isAuthenticated"
        to="/my-reports"
        class="flex flex-col items-center justify-center gap-0.5 text-[10px] font-medium transition py-1"
        :class="route.path === '/my-reports' ? 'text-primary font-bold' : 'text-muted-foreground hover:text-foreground'"
      >
        <ClipboardList class="h-4 w-4" />
        <span>{{ t('nav.myReports') }}</span>
      </RouterLink>
      <RouterLink
        v-else
        to="/login"
        class="flex flex-col items-center justify-center gap-0.5 text-[10px] font-medium transition py-1"
        :class="route.path === '/login' ? 'text-primary font-bold' : 'text-muted-foreground hover:text-foreground'"
      >
        <LogIn class="h-4 w-4" />
        <span>{{ t('nav.signIn') }}</span>
      </RouterLink>

      <RouterLink
        v-if="auth.isStaff"
        to="/admin/dashboard"
        class="flex flex-col items-center justify-center gap-0.5 text-[10px] font-medium transition py-1"
        :class="route.path.startsWith('/admin') ? 'text-primary font-bold' : 'text-muted-foreground hover:text-foreground'"
      >
        <ShieldCheck class="h-4 w-4" />
        <span>{{ t('nav.adminShort') }}</span>
      </RouterLink>
      <button
        v-else-if="auth.isAuthenticated"
        type="button"
        class="flex flex-col items-center justify-center gap-0.5 text-[10px] font-medium text-muted-foreground hover:text-destructive transition py-1"
        @click="handleLogout"
      >
        <LogOut class="h-4 w-4" />
        <span>{{ t('nav.signOut') }}</span>
      </button>
      <RouterLink
        v-else
        to="/register"
        class="flex flex-col items-center justify-center gap-0.5 text-[10px] font-medium transition py-1"
        :class="route.path === '/register' ? 'text-primary font-bold' : 'text-muted-foreground hover:text-foreground'"
      >
        <UserPlus class="h-4 w-4" />
        <span>Join</span>
      </RouterLink>
    </nav>

    <!-- Footer -->
    <footer class="border-t bg-muted/30 py-6 mb-14 md:mb-0">
      <div class="container flex flex-col items-center justify-between gap-2 text-xs text-muted-foreground sm:flex-row px-4 text-center sm:text-left">
        <div class="flex items-center gap-2">
          <Leaf class="h-3.5 w-3.5 text-primary" />
          <span class="font-medium text-foreground">{{ t('brand.name') }}</span>
          <span>— {{ t('brand.subtitle') }}</span>
        </div>
        <p>{{ t('brand.tagline') }}</p>
      </div>
    </footer>
  </div>
</template>
