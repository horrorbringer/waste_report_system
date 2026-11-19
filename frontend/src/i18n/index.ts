import { createI18n } from 'vue-i18n'
import en from './locales/en'
import km from './locales/km'

export type SupportedLocale = 'en' | 'km'

const STORAGE_KEY = 'cwrs_locale'

function resolveInitialLocale(): SupportedLocale {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'en' || saved === 'km') return saved
  const envDefault = import.meta.env.VITE_DEFAULT_LOCALE
  return envDefault === 'km' ? 'km' : 'en'
}

const initialLocale = resolveInitialLocale()
document.documentElement.lang = initialLocale

export const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
  fallbackLocale: 'en',
  messages: {
    en,
    km,
  },
})

export function setAppLocale(locale: SupportedLocale) {
  i18n.global.locale.value = locale
  localStorage.setItem(STORAGE_KEY, locale)
  document.documentElement.lang = locale
}

export function localizedCategory(
  nameEn: string,
  nameKm: string | null | undefined,
  locale: string
): string {
  if (locale === 'km' && nameKm && nameKm.trim()) {
    return nameKm
  }
  return nameEn
}

export function translateStatus(status: string, t: (key: string) => string): string {
  if (status === 'Pending') return t('status.pending')
  if (status === 'In Progress') return t('status.inProgress')
  if (status === 'Resolved') return t('status.resolved')
  return status
}

export function translateRole(role: string, t: (key: string) => string): string {
  if (role === 'admin') return t('roles.admin')
  if (role === 'resident') return t('roles.resident')
  return role
}
