import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateStr: string, locale: string = 'en'): string {
  const date = new Date(dateStr)
  const intlLocale = locale === 'km' ? 'km-KH' : 'en-US'
  return new Intl.DateTimeFormat(intlLocale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function resolvePhotoUrl(path?: string | null): string {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  const apiBase = import.meta.env.VITE_API_BASE_URL || ''
  if (/^https?:\/\//i.test(apiBase)) {
    const origin = new URL(apiBase).origin
    return `${origin}${path.startsWith('/') ? '' : '/'}${path}`
  }
  return path
}
