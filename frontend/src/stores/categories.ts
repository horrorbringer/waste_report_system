import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Category } from '@/types'

export interface CategoryPayload {
  name: string
  name_km: string | null
  description: string | null
  description_km: string | null
}

export const useCategoryStore = defineStore('categories', () => {
  const categories = ref<Category[]>([])
  const loading = ref(false)

  async function fetchCategories() {
    loading.value = true
    try {
      const { data } = await api.get<Category[]>('/categories')
      categories.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function createCategory(payload: CategoryPayload) {
    const { data } = await api.post<Category>('/categories', payload)
    categories.value.push(data)
    categories.value.sort((a, b) => a.name.localeCompare(b.name))
    return data
  }

  async function updateCategory(id: number, payload: CategoryPayload) {
    const { data } = await api.put<Category>(`/categories/${id}`, payload)
    const idx = categories.value.findIndex((c) => c.id === id)
    if (idx !== -1) categories.value[idx] = data
    return data
  }

  async function deleteCategory(id: number) {
    await api.delete(`/categories/${id}`)
    categories.value = categories.value.filter((c) => c.id !== id)
  }

  return {
    categories,
    loading,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
  }
})
