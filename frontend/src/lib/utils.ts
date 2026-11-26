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

const FRIENDLY_FIELD_LABELS: Record<string, string> = {
  full_name: 'Full name',
  email: 'Email address',
  password: 'Password',
  role: 'Role',
  name: 'Name',
  slug: 'Role key',
  description: 'Description',
  title: 'Title',
  location_text: 'Location',
  category_id: 'Category',
  status: 'Status',
  note: 'Note',
}

function humanizeFieldName(raw: unknown): string {
  const key = String(raw ?? '').trim()
  if (!key) return 'This field'
  if (FRIENDLY_FIELD_LABELS[key]) return FRIENDLY_FIELD_LABELS[key]
  return key.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
}

function formatValidationItem(item: Record<string, any>): string {
  const loc = Array.isArray(item.loc) ? item.loc : []
  const rawField = loc.filter((part) => part !== 'body' && part !== 'query' && part !== 'path').pop()
  const field = humanizeFieldName(rawField)
  const type = String(item.type || '')
  const ctx = (item.ctx || {}) as Record<string, any>

  if (type === 'missing') return `${field} is required.`
  if (type === 'string_too_short' && ctx.min_length) {
    return `${field} must be at least ${ctx.min_length} characters.`
  }
  if (type === 'string_too_long' && ctx.max_length) {
    return `${field} must be ${ctx.max_length} characters or fewer.`
  }
  if (type === 'string_pattern_mismatch') {
    if (rawField === 'email') return 'Please enter a valid email address (e.g. name@example.com).'
    if (rawField === 'slug') {
      return 'Role key can only use lowercase letters, numbers, underscores (_), and hyphens (-).'
    }
    return `${field} format is invalid.`
  }
  if (type === 'literal_error' || type === 'enum') {
    return `Please select a valid ${field.toLowerCase()}.`
  }

  const rawMsg = String(item.msg || '').replace(/^Value error,\s*/i, '').trim()
  if (rawMsg) return `${field}: ${rawMsg}`
  return `${field} is invalid.`
}

/**
 * Convert Axios / FastAPI error responses (including 422 validation arrays)
 * into clean, non-technical messages suitable for end users.
 */
export function formatApiError(err: any, fallback: string): string {
  if (!err?.response) {
    return 'Cannot connect to the server right now. Please check your connection and try again.'
  }

  const detail = err.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim()
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    if (typeof first === 'string') return first
    if (first && typeof first === 'object') {
      return formatValidationItem(first)
    }
  }

  const statusCode = err.response?.status
  if (statusCode === 401) return 'Your session has expired. Please sign in again.'
  if (statusCode === 403) return 'You do not have permission to perform this action.'
  if (statusCode === 404) return 'The requested item could not be found.'
  if (statusCode && statusCode >= 500) return 'Something went wrong on the server. Please try again.'

  return fallback
}
