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
    <header class="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="container flex h-16 items-center justify-between gap-4">
        <div class="flex items-center gap-6">
          <RouterLink to="/" class="flex items-center gap-2.5 font-display font-bold tracking-tight">
            <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <Leaf class="h-4 w-4" />
            </div>
            <span class="text-lg tracking-[-0.02em]">{{ t('brand.name') }}</span>
          </RouterLink>

          <nav class="hidden items-center gap-1 md:flex">
            <RouterLink to="/">
              <Button :variant="route.path === '/' ? 'secondary' : 'ghost'" size="sm">
                <Home class="h-4 w-4" />
                {{ t('nav.home') }}
              </Button>
            </RouterLink>

            <template v-if="auth.isAuthenticated">
              <RouterLink to="/reports/new">
                <Button :variant="route.path === '/reports/new' ? 'secondary' : 'ghost'" size="sm">
                  <PlusCircle class="h-4 w-4" />
                  {{ t('nav.reportWaste') }}
                </Button>
              </RouterLink>

              <RouterLink to="/my-reports">
                <Button :variant="route.path === '/my-reports' ? 'secondary' : 'ghost'" size="sm">
                  <ClipboardList class="h-4 w-4" />
                  {{ t('nav.myReports') }}
                </Button>
              </RouterLink>

              <RouterLink v-if="auth.isAdmin" to="/admin/dashboard">
                <Button variant="outline" size="sm" class="ml-1 border-primary/40 text-primary hover:bg-primary/10">
                  <ShieldCheck class="h-4 w-4" />
                  {{ t('nav.adminPortal') }}
                </Button>
              </RouterLink>
            </template>
          </nav>
        </div>

        <div class="flex items-center gap-2">
          <LanguageSwitcher />

          <template v-if="auth.isAuthenticated && auth.user">
            <div class="hidden items-center gap-2 sm:flex">
              <span class="text-sm font-medium">{{ auth.user.full_name }}</span>
              <Badge :variant="auth.isAdmin ? 'default' : 'secondary'">
                {{ translateRole(auth.user.role, t) }}
              </Badge>
            </div>
            <Button variant="ghost" size="sm" @click="handleLogout">
              <LogOut class="h-4 w-4" />
              <span class="hidden sm:inline">{{ t('nav.signOut') }}</span>
            </Button>
          </template>

          <template v-else>
            <RouterLink to="/login">
              <Button variant="ghost" size="sm">
                <LogIn class="h-4 w-4" />
                {{ t('nav.signIn') }}
              </Button>
            </RouterLink>
            <RouterLink to="/register">
              <Button size="sm">
                <UserPlus class="h-4 w-4" />
                {{ t('nav.getStarted') }}
              </Button>
            </RouterLink>
          </template>
        </div>
      </div>

      <!-- Mobile quick nav for logged-in users -->
      <div v-if="auth.isAuthenticated" class="flex items-center gap-2 overflow-x-auto border-t px-4 py-2 md:hidden">
        <RouterLink to="/reports/new">
          <Button :variant="route.path === '/reports/new' ? 'secondary' : 'ghost'" size="sm">
            <PlusCircle class="h-3.5 w-3.5" />
            {{ t('nav.reportShort') }}
          </Button>
        </RouterLink>
        <RouterLink to="/my-reports">
          <Button :variant="route.path === '/my-reports' ? 'secondary' : 'ghost'" size="sm">
            <ClipboardList class="h-3.5 w-3.5" />
            {{ t('nav.myReports') }}
          </Button>
        </RouterLink>
        <RouterLink v-if="auth.isAdmin" to="/admin/dashboard">
          <Button variant="outline" size="sm" class="border-primary/40 text-primary">
            <ShieldCheck class="h-3.5 w-3.5" />
            {{ t('nav.adminShort') }}
          </Button>
        </RouterLink>
      </div>
    </header>

    <main class="flex-1">
      <slot />
    </main>

    <footer class="border-t bg-muted/30 py-6">
      <div class="container flex flex-col items-center justify-between gap-2 text-xs text-muted-foreground sm:flex-row">
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
