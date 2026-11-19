import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { AdminSettings, AdminSettingsUpdatePayload, StorageTestResult } from '@/types'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<AdminSettings | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const testing = ref(false)

  async function fetchSettings() {
    loading.value = true
    try {
      const { data } = await api.get<AdminSettings>('/admin/settings')
      settings.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function saveSettings(payload: AdminSettingsUpdatePayload) {
    saving.value = true
    try {
      const { data } = await api.put<AdminSettings>('/admin/settings', payload)
      settings.value = data
      return data
    } finally {
      saving.value = false
    }
  }

  async function testStorageConnection(payload?: AdminSettingsUpdatePayload) {
    testing.value = true
    try {
      const { data } = await api.post<StorageTestResult>('/admin/settings/storage/test', payload ?? null)
      return data
    } finally {
      testing.value = false
    }
  }

  return {
    settings,
    loading,
    saving,
    testing,
    fetchSettings,
    saveSettings,
    testStorageConnection,
  }
})
