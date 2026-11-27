import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { AdminUser, PaginatedResponse, PermissionDefinition, RoleItem, UserRole } from '@/types'

export const useUserStore = defineStore('users', () => {
  const users = ref<AdminUser[]>([])
  const totalUsers = ref(0)
  const roles = ref<RoleItem[]>([])
  const permissions = ref<PermissionDefinition[]>([])
  const loading = ref(false)
  const rolesLoading = ref(false)

  async function fetchUsers(params?: { search?: string; role?: string; limit?: number; offset?: number }) {
    loading.value = true
    try {
      const cleanParams: Record<string, string | number> = {
        limit: params?.limit ?? 15,
        offset: params?.offset ?? 0,
      }
      if (params?.search?.trim()) cleanParams.search = params.search.trim()
      if (params?.role && params.role !== 'ALL') cleanParams.role = params.role
      const { data } = await api.get<PaginatedResponse<AdminUser>>('/admin/users', { params: cleanParams })
      users.value = data.items
      totalUsers.value = data.total
      return data
    } finally {
      loading.value = false
    }
  }

  async function createUser(payload: {
    full_name: string
    email: string
    password: string
    role: UserRole
  }) {
    const { data } = await api.post<AdminUser>('/admin/users', payload)
    users.value = [data, ...users.value]
    return data
  }

  async function updateUser(
    id: number,
    payload: { full_name?: string; role?: UserRole; is_active?: boolean; password?: string | null },
  ) {
    const body: Record<string, unknown> = {}
    if (payload.full_name !== undefined) body.full_name = payload.full_name
    if (payload.role !== undefined) body.role = payload.role
    if (payload.is_active !== undefined) body.is_active = payload.is_active
    if (payload.password) body.password = payload.password

    const { data } = await api.patch<AdminUser>(`/admin/users/${id}`, body)
    const idx = users.value.findIndex((u) => u.id === id)
    if (idx !== -1) users.value[idx] = data
    return data
  }

  async function deleteUser(id: number) {
    await api.delete(`/admin/users/${id}`)
    users.value = users.value.filter((u) => u.id !== id)
  }

  async function fetchRoles() {
    rolesLoading.value = true
    try {
      const { data } = await api.get<RoleItem[]>('/admin/roles')
      roles.value = data
      return data
    } finally {
      rolesLoading.value = false
    }
  }

  async function fetchPermissions() {
    const { data } = await api.get<PermissionDefinition[]>('/admin/permissions')
    permissions.value = data
    return data
  }

  async function createRole(payload: {
    name: string
    slug?: string
    description?: string
    permissions: string[]
  }) {
    const { data } = await api.post<RoleItem>('/admin/roles', payload)
    roles.value = [...roles.value, data]
    return data
  }

  async function updateRole(
    id: number,
    payload: { name?: string; description?: string; permissions?: string[] },
  ) {
    const { data } = await api.patch<RoleItem>(`/admin/roles/${id}`, payload)
    const idx = roles.value.findIndex((r) => r.id === id)
    if (idx !== -1) roles.value[idx] = data
    return data
  }

  async function deleteRole(id: number) {
    await api.delete(`/admin/roles/${id}`)
    roles.value = roles.value.filter((r) => r.id !== id)
  }

  return {
    users,
    totalUsers,
    roles,
    permissions,
    loading,
    rolesLoading,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    fetchRoles,
    fetchPermissions,
    createRole,
    updateRole,
    deleteRole,
  }
})
