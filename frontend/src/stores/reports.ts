import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type {
  AdminDashboardStats,
  PublicStats,
  ReportStatus,
  WasteReport,
  WasteReportDetail,
} from '@/types'

export const useReportStore = defineStore('reports', () => {
  const myReports = ref<WasteReport[]>([])
  const allReports = ref<WasteReport[]>([])
  const currentReport = ref<WasteReportDetail | null>(null)
  const adminStats = ref<AdminDashboardStats | null>(null)
  const publicStats = ref<PublicStats | null>(null)
  const loading = ref(false)

  async function fetchPublicStats() {
    const { data } = await api.get<PublicStats>('/stats/public')
    publicStats.value = data
    return data
  }

  async function fetchMyReports(params?: { status?: string; search?: string }) {
    loading.value = true
    try {
      const { data } = await api.get<WasteReport[]>('/reports/my', { params })
      myReports.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function fetchAllReports(params?: {
    status?: string
    category_id?: number | string
    search?: string
  }) {
    loading.value = true
    try {
      const cleanParams: Record<string, string | number> = {}
      if (params?.status && params.status !== 'ALL') cleanParams.status = params.status
      if (params?.category_id && params.category_id !== 'ALL') {
        cleanParams.category_id = Number(params.category_id)
      }
      if (params?.search?.trim()) cleanParams.search = params.search.trim()

      const { data } = await api.get<WasteReport[]>('/reports', { params: cleanParams })
      allReports.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function fetchReportDetail(id: number) {
    loading.value = true
    try {
      const { data } = await api.get<WasteReportDetail>(`/reports/${id}`)
      currentReport.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function submitReport(formData: FormData) {
    loading.value = true
    try {
      const { data } = await api.post<WasteReportDetail>('/reports', formData)
      return data
    } finally {
      loading.value = false
    }
  }

  async function updateReportStatus(id: number, status: ReportStatus, note: string) {
    const { data } = await api.patch<WasteReportDetail>(`/reports/${id}/status`, {
      status,
      note: note.trim() || null,
    })
    const idx = allReports.value.findIndex((r) => r.id === id)
    if (idx !== -1) {
      allReports.value[idx] = { ...allReports.value[idx], status: data.status, updated_at: data.updated_at }
    }
    if (currentReport.value?.id === id) {
      currentReport.value = data
    }
    return data
  }

  async function fetchAdminStats() {
    loading.value = true
    try {
      const { data } = await api.get<AdminDashboardStats>('/admin/stats')
      adminStats.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  return {
    myReports,
    allReports,
    currentReport,
    adminStats,
    publicStats,
    loading,
    fetchPublicStats,
    fetchMyReports,
    fetchAllReports,
    fetchReportDetail,
    submitReport,
    updateReportStatus,
    fetchAdminStats,
  }
})
