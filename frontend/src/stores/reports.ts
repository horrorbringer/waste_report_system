import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type {
  AdminDashboardStats,
  CommunityReport,
  CommunityReportsPage,
  ReportProvince,
  PublicStats,
  ReportStatus,
  ReportUploadPolicy,
  WasteReport,
  WasteReportDetail,
} from '@/types'

export const useReportStore = defineStore('reports', () => {
  const myReports = ref<WasteReport[]>([])
  const allReports = ref<WasteReport[]>([])
  const currentReport = ref<WasteReportDetail | null>(null)
  const adminStats = ref<AdminDashboardStats | null>(null)
  const publicStats = ref<PublicStats | null>(null)
  const reportAreas = ref<ReportProvince[]>([])
  let areasRequest: Promise<ReportProvince[]> | null = null
  const loading = ref(false)

  async function fetchPublicStats() {
    const { data } = await api.get<PublicStats>('/stats/public')
    publicStats.value = data
    return data
  }

  async function fetchCommunityReports(params: {
    limit?: number
    offset?: number
    q?: string
    status?: string
    category_id?: number | string
    province?: number | string
    sort?: 'newest' | 'oldest'
  }) {
    const cleanParams: Record<string, string | number> = {
      limit: params.limit ?? 20,
      offset: params.offset ?? 0,
    }
    if (params.q?.trim()) cleanParams.q = params.q.trim()
    if (params.status && params.status !== 'ALL') cleanParams.status = params.status
    if (params.category_id && params.category_id !== 'ALL') cleanParams.category_id = Number(params.category_id)
    if (params.province && params.province !== 'ALL') cleanParams.province = Number(params.province)
    if (params.sort) cleanParams.sort = params.sort

    const { data } = await api.get<CommunityReportsPage>('/reports/community', { params: cleanParams })
    return data
  }

  async function fetchCommunityReportById(id: number) {
    const { data } = await api.get<CommunityReport>(`/reports/community/${id}`)
    return data
  }

  function fetchReportAreas() {
    if (reportAreas.value.length) return Promise.resolve(reportAreas.value)
    if (!areasRequest) {
      areasRequest = api.get<ReportProvince[]>('/reports/areas').then(({ data }) => {
        reportAreas.value = data
        return data
      }).finally(() => { areasRequest = null })
    }
    return areasRequest
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

  async function fetchUploadPolicy() {
    const { data } = await api.get<ReportUploadPolicy>('/reports/upload-policy')
    return data
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

  async function setReportPublication(id: number, province: number | null, district: number | null) {
    const { data } = await api.put<{ province: number | null; district: number | null }>(`/reports/${id}/publication`, { province, district })
    if (currentReport.value?.id === id) {
      currentReport.value.public_province = data.province
      currentReport.value.public_district = data.district
    }
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
    reportAreas,
    loading,
    fetchPublicStats,
    fetchCommunityReports,
    fetchCommunityReportById,
    fetchReportAreas,
    fetchMyReports,
    fetchAllReports,
    fetchReportDetail,
    fetchUploadPolicy,
    submitReport,
    updateReportStatus,
    setReportPublication,
    fetchAdminStats,
  }
})
