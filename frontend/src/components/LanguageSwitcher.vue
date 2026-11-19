<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Languages } from 'lucide-vue-next'
import { setAppLocale, type SupportedLocale } from '@/i18n'

const { locale } = useI18n()

function selectLocale(next: SupportedLocale) {
  setAppLocale(next)
}
</script>

<template>
  <div
    class="inline-flex items-center rounded-lg border border-border bg-muted/40 p-0.5 text-xs"
    role="group"
    aria-label="Language switcher"
  >
    <Languages class="mx-1.5 hidden h-3.5 w-3.5 text-muted-foreground sm:block" />
    <button
      type="button"
      class="rounded-md px-2 py-1 font-medium transition-colors"
      :class="
        locale === 'en'
          ? 'bg-background text-foreground shadow-sm'
          : 'text-muted-foreground hover:text-foreground'
      "
      @click="selectLocale('en')"
    >
      EN
    </button>
    <button
      type="button"
      class="rounded-md px-2 py-1 font-medium transition-colors"
      :class="
        locale === 'km'
          ? 'bg-background text-foreground shadow-sm'
          : 'text-muted-foreground hover:text-foreground'
      "
      @click="selectLocale('km')"
    >
      ខ្មែរ
    </button>
  </div>
</template>
