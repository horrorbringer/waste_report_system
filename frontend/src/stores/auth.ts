import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '@/services/api'
import type { TokenResponse, User, UserRole } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('cwrs_token'))
  const user = ref<User | null>(
    localStorage.getItem('cwrs_user') ? JSON.parse(localStorage.getItem('cwrs_user')!) : null
  )
  const loading = ref(false)

  const STAFF_PERMISSIONS = [
    'dashboard:view',
    'reports:view_all',
    'reports:update_status',
    'reports:delete_any',
    'categories:manage',
    'users:manage',
    'roles:manage',
    'settings:manage',
  ]

  const isAuthenticated = computed(() => Boolean(token.value && user.value))
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isModerator = computed(() => user.value?.role === 'moderator')
  const permissions = computed<string[]>(() => user.value?.permissions ?? [])
  const isResident = computed(() => user.value?.role === 'resident')

  function hasRole(roles: UserRole[]): boolean {
    if (!user.value) return false
    return roles.includes(user.value.role)
  }

  function hasPermission(permission: string): boolean {
    if (!user.value) return false
    if (user.value.role === 'admin') return true
    return permissions.value.includes(permission)
  }

  function hasAnyPermission(perms: string[]): boolean {
    if (!user.value) return false
    if (user.value.role === 'admin') return true
    return perms.some((p) => permissions.value.includes(p))
  }

  const isStaff = computed(() => hasAnyPermission(STAFF_PERMISSIONS))

  function setSession(data: TokenResponse) {
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('cwrs_token', data.access_token)
    localStorage.setItem('cwrs_user', JSON.stringify(data.user))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('cwrs_token')
    localStorage.removeItem('cwrs_user')
  }

  async function login(email: string, password: string): Promise<User> {
    loading.value = true
    try {
      const { data } = await api.post<TokenResponse>('/auth/login', { email, password })
      setSession(data)
      return data.user
    } finally {
      loading.value = false
    }
  }

  async function register(full_name: string, email: string, password: string): Promise<User> {
    loading.value = true
    try {
      const { data } = await api.post<TokenResponse>('/auth/register', {
        full_name,
        email,
        password,
      })
      setSession(data)
      return data.user
    } finally {
      loading.value = false
    }
  }

  async function fetchMe(): Promise<User | null> {
    if (!token.value) return null
    try {
      const { data } = await api.get<User>('/auth/me')
      user.value = data
      localStorage.setItem('cwrs_user', JSON.stringify(data))
      return data
    } catch {
      logout()
      return null
    }
  }

  return {
    token,
    user,
    loading,
    isAuthenticated,
    isAdmin,
    isModerator,
    isStaff,
    isResident,
    permissions,
    hasRole,
    hasPermission,
    hasAnyPermission,
    login,
    register,
    logout,
    fetchMe,
  }
})
