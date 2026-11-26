<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Leaf,
  LayoutDashboard,
  FileText,
  Tags,
  Users,
  Settings,
  Home,
  ClipboardList,
  LogOut,
  Menu,
  X,
  ShieldCheck,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const { t } = useI18n()
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const mobileMenuOpen = ref(false)

const navItems = computed(() => {
  const items = []
  if (auth.hasPermission('dashboard:view')) {
    items.push({ label: t('nav.dashboard'), to: '/admin/dashboard', icon: LayoutDashboard })
  }
  if (auth.hasPermission('reports:view_all')) {
    items.push({ label: t('nav.manageReports'), to: '/admin/reports', icon: FileText })
  }
  if (auth.hasPermission('categories:manage')) {
    items.push({ label: t('nav.categories'), to: '/admin/categories', icon: Tags })
  }
  if (auth.hasAnyPermission(['users:manage', 'roles:manage'])) {
    items.push({ label: t('nav.users'), to: '/admin/users', icon: Users })
  }
  if (auth.hasPermission('settings:manage')) {
    items.push({ label: t('nav.settings'), to: '/admin/settings', icon: Settings })
  }
  return items
})

const pageTitle = computed(() => {
  const key = route.meta.titleKey
  return key ? t(key) : t('brand.adminConsole')
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="flex min-h-screen bg-muted/20">
    <!-- Desktop Sidebar (Sticky to Viewport) -->
    <aside class="hidden w-64 shrink-0 flex-col border-r bg-card md:flex md:sticky md:top-0 md:h-screen md:max-h-screen">
      <!-- Fixed Brand Header -->
      <div class="flex h-16 shrink-0 items-center gap-2.5 border-b px-6">
        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
          <Leaf class="h-4 w-4" />
        </div>
        <div class="flex flex-col">
          <span class="font-display text-[15px] font-bold leading-none tracking-[-0.02em]">
            {{ t('brand.name') }}
          </span>
          <span class="mt-1 text-[11px] font-medium text-muted-foreground">
            {{ t('brand.adminConsole') }}
          </span>
        </div>
      </div>

      <!-- Scrollable Navigation Region -->
      <div class="flex-1 overflow-y-auto p-4 space-y-6">
        <div>
          <p class="text-eyebrow mb-2.5 px-3">
            {{ t('nav.administration') }}
          </p>
          <nav class="space-y-1">
            <RouterLink
              v-for="item in navItems"
              :key="item.to"
              :to="item.to"
              class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
              :class="
                route.path === item.to
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              "
            >
              <component :is="item.icon" class="h-4 w-4 shrink-0" />
              <span>{{ item.label }}</span>
            </RouterLink>
          </nav>
        </div>

        <div>
          <p class="text-eyebrow mb-2.5 px-3">
            {{ t('nav.portalShortcuts') }}
          </p>
          <nav class="space-y-1">
            <RouterLink
              to="/my-reports"
              class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <ClipboardList class="h-4 w-4 shrink-0" />
              <span>{{ t('nav.myReports') }}</span>
            </RouterLink>
            <RouterLink
              to="/"
              class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <Home class="h-4 w-4 shrink-0" />
              <span>{{ t('nav.publicSite') }}</span>
            </RouterLink>
          </nav>
        </div>
      </div>

      <!-- Sticky Pinned Bottom User Profile Card -->
      <div class="sticky bottom-0 z-10 shrink-0 border-t bg-card/95 p-4 backdrop-blur-xs">
        <div class="rounded-xl border border-border/80 bg-muted/40 p-3 shadow-xs">
          <div class="flex items-center gap-2.5">
            <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
              <ShieldCheck class="h-4 w-4" />
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-foreground">{{ auth.user?.full_name || 'System Administrator' }}</p>
              <p class="truncate text-xs text-muted-foreground">{{ auth.user?.email || 'admin@waste.local' }}</p>
            </div>
          </div>
          <Button variant="outline" size="sm" class="mt-3 w-full gap-1.5 text-xs font-medium" @click="handleLogout">
            <LogOut class="h-3.5 w-3.5" />
            {{ t('nav.signOut') }}
          </Button>
        </div>
      </div>
    </aside>

    <!-- Main Content Column -->
    <div class="flex min-w-0 flex-1 flex-col">
      <!-- Mobile Header -->
      <header class="flex h-14 items-center justify-between border-b bg-card px-4 md:hidden">
        <div class="flex items-center gap-2">
          <Leaf class="h-5 w-5 text-primary" />
          <span class="font-display font-semibold">{{ t('brand.name') }}</span>
        </div>
        <div class="flex items-center gap-2">
          <LanguageSwitcher />
          <Button variant="ghost" size="icon" @click="mobileMenuOpen = !mobileMenuOpen">
            <X v-if="mobileMenuOpen" class="h-5 w-5" />
            <Menu v-else class="h-5 w-5" />
          </Button>
        </div>
      </header>

      <!-- Mobile Dropdown Navigation -->
      <div v-if="mobileMenuOpen" class="border-b bg-card p-3 md:hidden">
        <nav class="space-y-1">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium"
            :class="route.path === item.to ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'"
            @click="mobileMenuOpen = false"
          >
            <component :is="item.icon" class="h-4 w-4" />
            {{ item.label }}
          </RouterLink>
          <RouterLink
            to="/"
            class="flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground"
            @click="mobileMenuOpen = false"
          >
            <Home class="h-4 w-4" />
            {{ t('nav.publicSite') }}
          </RouterLink>
          <Button variant="outline" size="sm" class="mt-2 w-full" @click="handleLogout">
            <LogOut class="h-4 w-4" />
            {{ t('nav.signOut') }}
          </Button>
        </nav>
      </div>

      <!-- Desktop Top Bar (Sticky) -->
      <header class="hidden h-16 items-center justify-between border-b bg-card/95 px-8 backdrop-blur-xs md:flex md:sticky md:top-0 md:z-20">
        <div>
          <h1 class="text-lg font-semibold tracking-tight">{{ pageTitle }}</h1>
        </div>
        <div class="flex items-center gap-3">
          <LanguageSwitcher />
          <Badge variant="outline" class="gap-1.5 whitespace-nowrap border-primary/30 text-primary">
            <ShieldCheck class="h-3.5 w-3.5" />
            {{ t('roles.rbacAdmin') }}
          </Badge>
        </div>
      </header>

      <main class="flex-1 p-4 md:p-8">
        <RouterView />
      </main>
    </div>
  </div>
</template>
