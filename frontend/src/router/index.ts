import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
    roles?: UserRole[]
    permission?: string
    permissionsAny?: string[]
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
    meta: { requiresAuth: true, titleKey: 'routes.submitReport' },
  },
  {
    path: '/my-reports',
    name: 'my-reports',
    component: () => import('@/views/MyReportsView.vue'),
    meta: { requiresAuth: true, titleKey: 'routes.myReports' },
  },
  {
    path: '/reports/:id',
    name: 'report-detail',
    component: () => import('@/views/ReportDetailView.vue'),
    meta: { requiresAuth: true, titleKey: 'routes.reportDetail' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true, titleKey: 'routes.profile' },
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: () => useAuthStore().firstAdminRoute,
    meta: {
      requiresAuth: true,
      permissionsAny: [
        'dashboard:view',
        'reports:view_all',
        'categories:manage',
        'users:manage',
        'roles:manage',
        'settings:manage',
      ],
    },
    children: [
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
        meta: { requiresAuth: true, permission: 'dashboard:view', titleKey: 'routes.adminDashboard' },
      },
      {
        path: 'reports',
        name: 'admin-reports',
        component: () => import('@/views/admin/ReportsManagementView.vue'),
        meta: { requiresAuth: true, permission: 'reports:view_all', titleKey: 'routes.adminReports' },
      },
      {
        path: 'categories',
        name: 'admin-categories',
        component: () => import('@/views/admin/CategoryManagementView.vue'),
        meta: { requiresAuth: true, permission: 'categories:manage', titleKey: 'routes.adminCategories' },
      },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('@/views/admin/UsersManagementView.vue'),
        meta: {
          requiresAuth: true,
          permissionsAny: ['users:manage', 'roles:manage'],
          titleKey: 'routes.adminUsers',
        },
      },
      {
        path: 'settings',
        name: 'admin-settings',
        component: () => import('@/views/admin/SettingsView.vue'),
        meta: { requiresAuth: true, permission: 'settings:manage', titleKey: 'routes.adminSettings' },
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
    return auth.isStaff ? auth.firstAdminRoute : { name: 'my-reports' }
  }

  if (to.meta.roles && to.meta.roles.length > 0 && !auth.hasRole(to.meta.roles)) {
    return { name: 'forbidden' }
  }

  if (to.meta.permission && !auth.hasPermission(to.meta.permission)) {
    return { name: 'forbidden' }
  }

  if (to.meta.permissionsAny && to.meta.permissionsAny.length > 0 && !auth.hasAnyPermission(to.meta.permissionsAny)) {
    return { name: 'forbidden' }
  }

  return true
})

export default router
