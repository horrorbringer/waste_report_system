import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
    roles?: UserRole[]
    titleKey?: string
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { titleKey: 'routes.home' },
  },
  {
    path: '/community-reports',
    name: 'community-reports',
    component: () => import('@/views/CommunityReportsView.vue'),
    meta: { titleKey: 'community.title' },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guestOnly: true, titleKey: 'routes.login' },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { guestOnly: true, titleKey: 'routes.register' },
  },
  {
    path: '/reports/new',
    name: 'submit-report',
    component: () => import('@/views/SubmitReportView.vue'),
    meta: { requiresAuth: true, roles: ['resident', 'admin'], titleKey: 'routes.submitReport' },
  },
  {
    path: '/my-reports',
    name: 'my-reports',
    component: () => import('@/views/MyReportsView.vue'),
    meta: { requiresAuth: true, roles: ['resident', 'admin'], titleKey: 'routes.myReports' },
  },
  {
    path: '/reports/:id',
    name: 'report-detail',
    component: () => import('@/views/ReportDetailView.vue'),
    meta: { requiresAuth: true, roles: ['resident', 'admin'], titleKey: 'routes.reportDetail' },
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/admin/dashboard',
    meta: { requiresAuth: true, roles: ['admin'] },
    children: [
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
        meta: { requiresAuth: true, roles: ['admin'], titleKey: 'routes.adminDashboard' },
      },
      {
        path: 'reports',
        name: 'admin-reports',
        component: () => import('@/views/admin/ReportsManagementView.vue'),
        meta: { requiresAuth: true, roles: ['admin'], titleKey: 'routes.adminReports' },
      },
      {
        path: 'categories',
        name: 'admin-categories',
        component: () => import('@/views/admin/CategoryManagementView.vue'),
        meta: { requiresAuth: true, roles: ['admin'], titleKey: 'routes.adminCategories' },
      },
      {
        path: 'settings',
        name: 'admin-settings',
        component: () => import('@/views/admin/SettingsView.vue'),
        meta: { requiresAuth: true, roles: ['admin'], titleKey: 'routes.adminSettings' },
      },
    ],
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@/views/ForbiddenView.vue'),
    meta: { titleKey: 'routes.forbidden' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (auth.token && !auth.user) {
    await auth.fetchMe()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return auth.isAdmin ? { name: 'admin-dashboard' } : { name: 'my-reports' }
  }

  if (to.meta.roles && to.meta.roles.length > 0 && !auth.hasRole(to.meta.roles)) {
    return { name: 'forbidden' }
  }

  return true
})

export default router
