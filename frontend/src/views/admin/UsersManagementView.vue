<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  AlertCircle,
  Ban,
  CheckCircle2,
  KeyRound,
  Lock,
  Pencil,
  Plus,
  Search,
  Shield,
  ShieldCheck,
  Trash2,
  UserCheck,
  User as UserIcon,
  Users as UsersIcon,
  X,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/users'
import { formatApiError, formatDate } from '@/lib/utils'
import TablePagination from '@/components/TablePagination.vue'
import { translateRole } from '@/i18n'
import type { AdminUser, PermissionDefinition, RoleItem, UserRole } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const { t, locale } = useI18n()
const auth = useAuthStore()
const userStore = useUserStore()

const canManageUsers = computed(() => auth.hasPermission('users:manage'))
const canManageRoles = computed(() => auth.hasPermission('roles:manage'))
const activeTab = ref<'users' | 'roles'>(canManageUsers.value ? 'users' : 'roles')

const searchQuery = ref('')
const roleFilter = ref<'ALL' | UserRole>('ALL')

const dialogOpen = ref(false)
const editingUser = ref<AdminUser | null>(null)
const formName = ref('')
const formEmail = ref('')
const formRole = ref<UserRole>('resident')
const formIsActive = ref(true)
const formPassword = ref('')
const saving = ref(false)

const deleteDialogOpen = ref(false)
const userToDelete = ref<AdminUser | null>(null)
const deleting = ref(false)

// Role management state
const roleDialogOpen = ref(false)
const editingRole = ref<RoleItem | null>(null)
const roleName = ref('')
const roleSlug = ref('')
const roleDescription = ref('')
const rolePermissions = ref<string[]>([])
const roleSaving = ref(false)

const deleteRoleDialogOpen = ref(false)
const roleToDelete = ref<RoleItem | null>(null)
const deletingRole = ref(false)

const successMsg = ref('')
const errorMsg = ref('')
const dialogError = ref('')
const roleDialogError = ref('')

const groupedPermissions = computed(() => {
  const groups: Record<string, PermissionDefinition[]> = {}
  for (const perm of userStore.permissions) {
    if (!groups[perm.group]) groups[perm.group] = []
    groups[perm.group].push(perm)
  }
  return groups
})

function groupTitle(group: string): string {
  if (group === 'dashboard') return t('adminRoles.groupDashboard')
  if (group === 'reports') return t('adminRoles.groupReports')
  if (group === 'categories') return t('adminRoles.groupCategories')
  if (group === 'administration') return t('adminRoles.groupAdministration')
  return group
}

function getRoleDisplayName(slug: string): string {
  if (slug === 'admin' || slug === 'moderator' || slug === 'resident') {
    return translateRole(slug, t)
  }
  const found = userStore.roles.find((r) => r.slug === slug)
  return found ? found.name : slug
}

const pageLimit = 15
const pageOffset = ref(0)

async function loadUsers() {
  if (!canManageUsers.value) return
  await userStore.fetchUsers({
    search: searchQuery.value,
    role: roleFilter.value,
    limit: pageLimit,
    offset: pageOffset.value,
  })
}

onMounted(async () => {
  const tasks: Promise<unknown>[] = [userStore.fetchRoles(), userStore.fetchPermissions()]
  if (canManageUsers.value) tasks.push(loadUsers())
  await Promise.all(tasks)
})

let searchTimeout: ReturnType<typeof setTimeout> | null = null
watch(roleFilter, () => {
  pageOffset.value = 0
  loadUsers()
})
watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    pageOffset.value = 0
    loadUsers()
  }, 250)
})

function getInitials(name: string) {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('') || 'U'
}

function openCreateDialog() {
  editingUser.value = null
  formName.value = ''
  formEmail.value = ''
  formRole.value = 'resident'
  formIsActive.value = true
  formPassword.value = ''
  errorMsg.value = ''
  dialogError.value = ''
  dialogOpen.value = true
}

function openEditDialog(user: AdminUser) {
  editingUser.value = user
  formName.value = user.full_name
  formEmail.value = user.email
  formRole.value = user.role
  formIsActive.value = user.is_active
  formPassword.value = ''
  errorMsg.value = ''
  dialogError.value = ''
  dialogOpen.value = true
}

async function handleToggleActive(user: AdminUser) {
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const nextActive = !user.is_active
    const updated = await userStore.updateUser(user.id, { is_active: nextActive })
    successMsg.value = nextActive
      ? t('adminUsers.activatedMsg', { email: updated.email })
      : t('adminUsers.suspendedMsg', { email: updated.email })
  } catch (err: any) {
    errorMsg.value = formatApiError(err, t('adminUsers.errSaveFailed'))
  }
}

async function handleSave() {
  errorMsg.value = ''
  dialogError.value = ''
  successMsg.value = ''
  saving.value = true

  try {
    if (!editingUser.value) {
      const created = await userStore.createUser({
        full_name: formName.value.trim(),
        email: formEmail.value.trim(),
        password: formPassword.value,
        role: formRole.value,
      })
      successMsg.value = t('adminUsers.createdMsg', { email: created.email })
    } else {
      const updated = await userStore.updateUser(editingUser.value.id, {
        full_name: formName.value.trim(),
        role: formRole.value,
        is_active: formIsActive.value,
        password: formPassword.value || null,
      })
      successMsg.value = t('adminUsers.updatedMsg', { email: updated.email })
    }
    dialogOpen.value = false
    await userStore.fetchRoles()
  } catch (err: any) {
    dialogError.value = formatApiError(err, t('adminUsers.errSaveFailed'))
  } finally {
    saving.value = false
  }
}

function openDeleteDialog(user: AdminUser) {
  userToDelete.value = user
  errorMsg.value = ''
  deleteDialogOpen.value = true
}

async function handleConfirmDelete() {
  if (!userToDelete.value) return
  deleting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  const target = userToDelete.value
  try {
    await userStore.deleteUser(target.id)
    successMsg.value = t('adminUsers.deletedMsg', { email: target.email })
    deleteDialogOpen.value = false
    userToDelete.value = null
  } catch (err: any) {
    errorMsg.value = formatApiError(err, t('adminUsers.errDeleteFailed'))
    deleteDialogOpen.value = false
  } finally {
    deleting.value = false
  }
}

function openCreateRoleDialog() {
  editingRole.value = null
  roleName.value = ''
  roleSlug.value = ''
  roleDescription.value = ''
  rolePermissions.value = []
  errorMsg.value = ''
  roleDialogError.value = ''
  roleDialogOpen.value = true
}

function openEditRoleDialog(role: RoleItem) {
  editingRole.value = role
  roleName.value = role.name
  roleSlug.value = role.slug
  roleDescription.value = role.description || ''
  rolePermissions.value = [...role.permissions]
  errorMsg.value = ''
  roleDialogError.value = ''
  roleDialogOpen.value = true
}

function isCoreLockedPermission(permKey: string): boolean {
  return editingRole.value?.slug === 'admin' && (permKey === 'users:manage' || permKey === 'roles:manage')
}

function toggleRolePermission(permKey: string) {
  if (isCoreLockedPermission(permKey)) return
  if (rolePermissions.value.includes(permKey)) {
    rolePermissions.value = rolePermissions.value.filter((p) => p !== permKey)
  } else {
    rolePermissions.value = [...rolePermissions.value, permKey]
  }
}

async function handleSaveRole() {
  errorMsg.value = ''
  roleDialogError.value = ''
  successMsg.value = ''
  roleSaving.value = true
  try {
    if (!editingRole.value) {
      const created = await userStore.createRole({
        name: roleName.value.trim(),
        slug: roleSlug.value.trim() || undefined,
        description: roleDescription.value.trim() || undefined,
        permissions: rolePermissions.value,
      })
      successMsg.value = t('adminRoles.createdMsg', { name: created.name })
    } else {
      const updated = await userStore.updateRole(editingRole.value.id, {
        name: roleName.value.trim(),
        description: roleDescription.value.trim(),
        permissions: rolePermissions.value,
      })
      successMsg.value = t('adminRoles.updatedMsg', { name: updated.name })
      if (auth.user?.role === updated.slug) {
        await auth.fetchMe()
      }
    }
    roleDialogOpen.value = false
  } catch (err: any) {
    roleDialogError.value = formatApiError(err, t('adminRoles.errSaveFailed'))
  } finally {
    roleSaving.value = false
  }
}

function openDeleteRoleDialog(role: RoleItem) {
  roleToDelete.value = role
  errorMsg.value = ''
  deleteRoleDialogOpen.value = true
}

async function handleConfirmDeleteRole() {
  if (!roleToDelete.value) return
  deletingRole.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const deletedName = roleToDelete.value.name
    await userStore.deleteRole(roleToDelete.value.id)
    deleteRoleDialogOpen.value = false
    roleToDelete.value = null
    successMsg.value = t('adminRoles.deletedMsg', { name: deletedName })
  } catch (err: any) {
    deleteRoleDialogOpen.value = false
    errorMsg.value = formatApiError(err, t('adminRoles.errDeleteFailed'))
  } finally {
    deletingRole.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-eyebrow mb-1">{{ t('adminUsers.eyebrow') }}</p>
        <h2 class="heading-page">{{ t('adminUsers.title') }}</h2>
        <p class="mt-1 text-sm leading-relaxed text-muted-foreground">
          {{ t('adminUsers.subtitle') }}
        </p>
      </div>
      <Button v-if="activeTab === 'users' && canManageUsers" class="gap-2" @click="openCreateDialog">
        <Plus class="h-4 w-4" />
        {{ t('adminUsers.addUser') }}
      </Button>
      <Button v-else-if="activeTab === 'roles' && canManageRoles" class="gap-2" @click="openCreateRoleDialog">
        <Plus class="h-4 w-4" />
        {{ t('adminRoles.addRole') }}
      </Button>
    </div>

    <!-- Section Switcher -->
    <div v-if="canManageUsers && canManageRoles" class="inline-flex items-center rounded-lg border bg-muted/40 p-1 text-sm">
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-md px-3.5 py-1.5 font-medium transition-colors"
        :class="activeTab === 'users' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
        @click="activeTab = 'users'"
      >
        <UsersIcon class="h-4 w-4" />
        {{ t('adminRoles.tabUsers') }}
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-md px-3.5 py-1.5 font-medium transition-colors"
        :class="activeTab === 'roles' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
        @click="activeTab = 'roles'"
      >
        <KeyRound class="h-4 w-4" />
        {{ t('adminRoles.tabRoles') }}
      </button>
    </div>

    <Alert v-if="successMsg" variant="success">
      <CheckCircle2 class="h-4 w-4" />
      <AlertDescription>{{ successMsg }}</AlertDescription>
    </Alert>

    <Alert v-if="errorMsg" variant="destructive">
      <AlertCircle class="h-4 w-4" />
      <AlertDescription>{{ errorMsg }}</AlertDescription>
    </Alert>

    <Card v-if="activeTab === 'users' && canManageUsers" class="border-border/60 shadow-sm">
      <CardHeader class="pb-3">
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle class="text-base font-semibold">{{ t('adminUsers.tableTitle') }}</CardTitle>
            <CardDescription class="text-xs">
              {{ t('adminUsers.matchingCount', { count: userStore.totalUsers }) }}
            </CardDescription>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <!-- Role Filter Tabs -->
            <div class="inline-flex flex-wrap items-center rounded-lg border bg-muted/40 p-0.5 text-xs">
              <button
                type="button"
                class="rounded-md px-2.5 py-1 font-medium transition-colors"
                :class="roleFilter === 'ALL' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
                @click="roleFilter = 'ALL'"
              >
                {{ t('adminUsers.allRoles') }}
              </button>
              <button
                v-for="roleItem in userStore.roles"
                :key="roleItem.slug"
                type="button"
                class="rounded-md px-2.5 py-1 font-medium transition-colors"
                :class="roleFilter === roleItem.slug ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
                @click="roleFilter = roleItem.slug"
              >
                {{ getRoleDisplayName(roleItem.slug) }}
              </button>
            </div>

            <!-- Search Input -->
            <div class="relative w-56 sm:w-64">
              <Search class="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <Input
                v-model="searchQuery"
                :placeholder="t('adminUsers.searchPlaceholder')"
                class="h-8 pl-8 pr-7 text-xs"
              />
              <button
                v-if="searchQuery"
                type="button"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                @click="searchQuery = ''"
              >
                <X class="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent class="p-0">
        <div class="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow class="bg-muted/30">
                <TableHead>{{ t('adminUsers.colUser') }}</TableHead>
                <TableHead>{{ t('adminUsers.colRole') }}</TableHead>
                <TableHead>{{ t('adminUsers.colReports') }}</TableHead>
                <TableHead>{{ t('adminUsers.colJoined') }}</TableHead>
                <TableHead class="text-right">{{ t('adminUsers.colActions') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <!-- Loading Skeletons -->
              <template v-if="userStore.loading && userStore.users.length === 0">
                <TableRow v-for="n in 4" :key="`user-skel-${n}`">
                  <TableCell>
                    <div class="flex items-center gap-3">
                      <Skeleton class="h-9 w-9 rounded-full" />
                      <div class="space-y-1.5">
                        <Skeleton class="h-4 w-36" />
                        <Skeleton class="h-3 w-44" />
                      </div>
                    </div>
                  </TableCell>
                  <TableCell><Skeleton class="h-5 w-20 rounded-full" /></TableCell>
                  <TableCell><Skeleton class="h-5 w-16 rounded-full" /></TableCell>
                  <TableCell><Skeleton class="h-4 w-24" /></TableCell>
                  <TableCell class="text-right"><Skeleton class="ml-auto h-8 w-20 rounded-lg" /></TableCell>
                </TableRow>
              </template>

              <TableRow
                v-for="user in userStore.users"
                v-else
                :key="user.id"
                class="transition-colors hover:bg-muted/40"
                :class="!user.is_active ? 'opacity-65' : ''"
              >
                <TableCell>
                  <div class="flex items-center gap-3">
                    <div
                      class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                      :class="user.role === 'admin' ? 'bg-primary/15 text-primary' : user.role === 'moderator' ? 'bg-sky-500/15 text-sky-700 dark:text-sky-300' : 'bg-muted text-muted-foreground'"
                    >
                      {{ getInitials(user.full_name) }}
                    </div>
                    <div class="min-w-0">
                      <div class="flex items-center gap-1.5">
                        <span class="truncate text-sm font-medium text-foreground">{{ user.full_name }}</span>
                        <Badge
                          v-if="auth.user?.id === user.id"
                          variant="outline"
                          class="border-primary/30 px-1.5 py-0 text-[10px] font-semibold text-primary"
                        >
                          {{ t('adminUsers.youBadge') }}
                        </Badge>
                        <Badge
                          v-if="!user.is_active"
                          variant="destructive"
                          class="px-1.5 py-0 text-[10px] font-semibold"
                        >
                          {{ t('adminUsers.statusSuspended') }}
                        </Badge>
                      </div>
                      <p class="truncate text-xs text-muted-foreground">{{ user.email }}</p>
                    </div>
                  </div>
                </TableCell>

                <TableCell>
                  <Badge
                    :variant="user.role === 'admin' ? 'default' : user.role === 'moderator' ? 'outline' : 'secondary'"
                    class="gap-1 whitespace-nowrap text-xs"
                    :class="user.role === 'moderator' ? 'border-sky-500/40 bg-sky-500/10 text-sky-700 dark:text-sky-300' : user.role !== 'admin' && user.role !== 'resident' ? 'border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300' : ''"
                  >
                    <ShieldCheck v-if="user.role === 'admin'" class="h-3 w-3" />
                    <Shield v-else-if="user.role !== 'resident'" class="h-3 w-3" />
                    <UserIcon v-else class="h-3 w-3" />
                    {{ getRoleDisplayName(user.role) }}
                  </Badge>
                </TableCell>

                <TableCell>
                  <Badge variant="outline" class="whitespace-nowrap font-mono text-xs tabular-nums">
                    {{ t('common.reportCount', { count: user.report_count }) }}
                  </Badge>
                </TableCell>

                <TableCell class="whitespace-nowrap text-xs tabular-nums text-muted-foreground">
                  {{ formatDate(user.created_at, locale) }}
                </TableCell>

                <TableCell class="whitespace-nowrap text-right">
                  <!-- Grouped Action Pill -->
                  <div class="inline-flex items-center rounded-lg border bg-background p-0.5 shadow-2xs">
                    <button
                      type="button"
                      class="inline-flex h-7 items-center gap-1 rounded-md px-2.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
                      :title="t('common.edit')"
                      @click="openEditDialog(user)"
                    >
                      <Pencil class="h-3.5 w-3.5 text-primary" />
                      <span>{{ t('common.edit') }}</span>
                    </button>
                    <span class="mx-0.5 h-4 w-px bg-border" aria-hidden="true" />
                    <button
                      type="button"
                      class="inline-flex h-7 items-center justify-center rounded-md px-2 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40"
                      :class="user.is_active ? 'text-amber-600 hover:bg-amber-500/10' : 'text-emerald-600 hover:bg-emerald-500/10'"
                      :disabled="auth.user?.id === user.id"
                      :title="
                        auth.user?.id === user.id
                          ? t('adminUsers.selfSuspendTooltip')
                          : user.is_active
                            ? t('adminUsers.suspendUser')
                            : t('adminUsers.activateUser')
                      "
                      @click="handleToggleActive(user)"
                    >
                      <Ban v-if="user.is_active" class="h-3.5 w-3.5" />
                      <UserCheck v-else class="h-3.5 w-3.5" />
                    </button>
                    <span class="mx-0.5 h-4 w-px bg-border" aria-hidden="true" />
                    <button
                      type="button"
                      class="inline-flex h-7 items-center justify-center rounded-md px-2 text-xs font-medium text-destructive transition-colors hover:bg-destructive/10 disabled:cursor-not-allowed disabled:opacity-40"
                      :disabled="auth.user?.id === user.id"
                      :title="auth.user?.id === user.id ? t('adminUsers.selfDeleteTooltip') : t('adminReports.deleteBtn')"
                      @click="openDeleteDialog(user)"
                    >
                      <Trash2 class="h-3.5 w-3.5" />
                    </button>
                  </div>
                </TableCell>
              </TableRow>

              <TableRow v-if="!userStore.loading && userStore.users.length === 0">
                <TableCell colspan="5" class="py-10 text-center text-sm text-muted-foreground">
                  {{ t('adminUsers.emptyFiltered') }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
        <TablePagination
          :total="userStore.totalUsers"
          :limit="pageLimit"
          :offset="pageOffset"
          :loading="userStore.loading"
          @update:offset="(val) => { pageOffset = val; loadUsers() }"
        />
      </CardContent>
    </Card>

    <!-- Create / Edit User Dialog -->
    <Dialog v-model:open="dialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>
            {{ editingUser ? t('adminUsers.editTitle') : t('adminUsers.createTitle') }}
          </DialogTitle>
          <DialogDescription>
            {{ t('adminUsers.dialogDesc') }}
          </DialogDescription>
        </DialogHeader>

        <form class="space-y-4 py-2" @submit.prevent="handleSave">
          <Alert v-if="dialogError" variant="destructive">
            <AlertCircle class="h-4 w-4" />
            <AlertDescription>{{ dialogError }}</AlertDescription>
          </Alert>

          <div class="space-y-1.5">
            <Label for="user-name">{{ t('adminUsers.fieldFullName') }}</Label>
            <Input id="user-name" v-model="formName" required minlength="2" maxlength="120" />
          </div>

          <div class="space-y-1.5">
            <Label for="user-email">{{ t('adminUsers.fieldEmail') }}</Label>
            <Input
              id="user-email"
              v-model="formEmail"
              type="email"
              required
              :disabled="Boolean(editingUser)"
            />
          </div>

          <div class="space-y-1.5">
            <Label>{{ t('adminUsers.fieldRole') }}</Label>
            <Select v-model="formRole">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="roleItem in userStore.roles" :key="roleItem.slug" :value="roleItem.slug">
                  {{ getRoleDisplayName(roleItem.slug) }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-1.5">
            <Label for="user-password">
              {{ editingUser ? t('adminUsers.fieldNewPassword') : t('adminUsers.fieldPassword') }}
            </Label>
            <Input
              id="user-password"
              v-model="formPassword"
              type="password"
              :required="!editingUser"
              minlength="6"
            />
            <p v-if="editingUser" class="text-[11px] text-muted-foreground">
              {{ t('adminUsers.passwordKeepHint') }}
            </p>
          </div>

          <label
            v-if="editingUser"
            class="flex items-center gap-2.5 rounded-lg border bg-muted/20 px-3 py-2 text-xs font-medium"
            :class="auth.user?.id === editingUser.id ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'"
          >
            <input
              v-model="formIsActive"
              type="checkbox"
              class="h-4 w-4 rounded border-input accent-primary"
              :disabled="auth.user?.id === editingUser.id"
            />
            <span>{{ t('adminUsers.fieldAccountActive') }}</span>
          </label>

          <DialogFooter>
            <Button type="button" variant="outline" :disabled="saving" @click="dialogOpen = false">
              {{ t('common.cancel') }}
            </Button>
            <Button type="submit" :disabled="saving">
              {{
                saving
                  ? t('common.saving')
                  : editingUser
                    ? t('adminUsers.saveBtn')
                    : t('adminUsers.createBtn')
              }}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <!-- Delete User Confirmation Dialog -->
    <Dialog v-model:open="deleteDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ t('adminUsers.deleteTitle', { name: userToDelete?.full_name }) }}</DialogTitle>
          <DialogDescription>
            {{ t('adminUsers.deleteDesc') }}
          </DialogDescription>
        </DialogHeader>
        <div v-if="userToDelete" class="rounded-lg border bg-muted/40 p-3 text-sm">
          <p class="font-medium text-foreground">{{ userToDelete.full_name }}</p>
          <p class="mt-0.5 text-xs text-muted-foreground">{{ userToDelete.email }}</p>
        </div>
        <DialogFooter>
          <Button variant="outline" size="sm" :disabled="deleting" @click="deleteDialogOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button variant="destructive" size="sm" :disabled="deleting" @click="handleConfirmDelete">
            {{ deleting ? t('adminReports.deleting') : t('adminReports.deleteBtn') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Roles & Permissions Card -->
    <Card v-if="activeTab === 'roles' && canManageRoles" class="border-border/60 shadow-sm">
      <CardHeader class="pb-3">
        <CardTitle class="text-base font-semibold">{{ t('adminRoles.tableTitle') }}</CardTitle>
        <CardDescription class="text-xs">
          {{ t('adminRoles.tableDesc', { count: userStore.roles.length }) }}
        </CardDescription>
      </CardHeader>
      <CardContent class="p-0">
        <div v-if="userStore.rolesLoading" class="space-y-3 p-6">
          <Skeleton v-for="i in 3" :key="i" class="h-12 w-full rounded-lg" />
        </div>
        <div v-else class="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow class="bg-muted/30 hover:bg-muted/30">
                <TableHead class="w-[260px]">{{ t('adminRoles.colRole') }}</TableHead>
                <TableHead>{{ t('adminRoles.colPermissions') }}</TableHead>
                <TableHead class="w-[110px]">{{ t('adminRoles.colUsers') }}</TableHead>
                <TableHead class="w-[110px] text-right">{{ t('adminRoles.colActions') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="role in userStore.roles" :key="role.id" class="transition-colors hover:bg-muted/40">
                <TableCell class="align-top">
                  <div class="space-y-1">
                    <div class="flex items-center gap-2">
                      <span class="font-medium text-foreground">{{ getRoleDisplayName(role.slug) }}</span>
                      <Badge
                        :variant="role.is_system ? 'secondary' : 'outline'"
                        class="px-1.5 py-0 text-[10px]"
                      >
                        {{ role.is_system ? t('adminRoles.systemBadge') : t('adminRoles.customBadge') }}
                      </Badge>
                    </div>
                    <p class="font-mono text-[11px] text-muted-foreground">{{ role.slug }}</p>
                    <p v-if="role.description" class="text-xs text-muted-foreground leading-snug">
                      {{ role.description }}
                    </p>
                  </div>
                </TableCell>
                <TableCell class="align-top">
                  <div v-if="role.permissions.length === 0" class="text-xs text-muted-foreground">
                    {{ t('adminRoles.noPermissions') }}
                  </div>
                  <div v-else class="flex flex-wrap gap-1.5">
                    <Badge
                      v-for="perm in role.permissions"
                      :key="perm"
                      variant="outline"
                      class="font-mono text-[11px] font-normal"
                    >
                      {{ perm }}
                    </Badge>
                  </div>
                </TableCell>
                <TableCell class="align-top">
                  <Badge variant="outline" class="font-mono text-xs tabular-nums">
                    {{ role.user_count }}
                  </Badge>
                </TableCell>
                <TableCell class="text-right align-top">
                  <div class="inline-flex items-center overflow-hidden rounded-lg border bg-background shadow-2xs">
                    <Button
                      variant="ghost"
                      size="icon"
                      class="h-8 w-8 rounded-none border-r"
                      :title="t('common.edit')"
                      @click="openEditRoleDialog(role)"
                    >
                      <Pencil class="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      class="h-8 w-8 rounded-none text-destructive hover:bg-destructive/10 hover:text-destructive"
                      :disabled="role.is_system || role.user_count > 0"
                      :title="
                        role.is_system
                          ? t('adminRoles.cannotDeleteSystem')
                          : role.user_count > 0
                            ? t('adminRoles.cannotDeleteAssigned', { count: role.user_count })
                            : t('common.delete')
                      "
                      @click="openDeleteRoleDialog(role)"
                    >
                      <Trash2 class="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>

    <!-- Create / Edit Role Dialog -->
    <Dialog v-model:open="roleDialogOpen">
      <DialogContent class="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {{ editingRole ? t('adminRoles.editTitle') : t('adminRoles.createTitle') }}
          </DialogTitle>
          <DialogDescription>
            {{ editingRole ? t('adminRoles.editDesc') : t('adminRoles.createDesc') }}
          </DialogDescription>
        </DialogHeader>

        <form class="space-y-4" @submit.prevent="handleSaveRole">
          <Alert v-if="roleDialogError" variant="destructive">
            <AlertCircle class="h-4 w-4" />
            <AlertDescription>{{ roleDialogError }}</AlertDescription>
          </Alert>

          <div class="grid gap-4 sm:grid-cols-2">
            <div class="space-y-1.5">
              <Label for="role-name">{{ t('adminRoles.fieldName') }}</Label>
              <Input
                id="role-name"
                v-model="roleName"
                required
                minlength="2"
                maxlength="80"
                :placeholder="t('adminRoles.fieldNamePlaceholder')"
              />
            </div>

            <div class="space-y-1.5">
              <Label for="role-slug">{{ t('adminRoles.fieldSlug') }}</Label>
              <Input
                id="role-slug"
                v-model="roleSlug"
                :disabled="Boolean(editingRole)"
                maxlength="40"
                placeholder="field_dispatcher"
                class="font-mono text-xs"
              />
              <p v-if="!editingRole" class="text-[11px] text-muted-foreground">
                {{ t('adminRoles.fieldSlugHint') }}
              </p>
            </div>
          </div>

          <div class="space-y-1.5">
            <Label for="role-description">{{ t('adminRoles.fieldDescription') }}</Label>
            <Input
              id="role-description"
              v-model="roleDescription"
              maxlength="300"
              :placeholder="t('adminRoles.fieldDescriptionPlaceholder')"
            />
          </div>

          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <Label>{{ t('adminRoles.fieldPermissions') }}</Label>
              <span class="text-xs text-muted-foreground">
                {{ t('adminRoles.permCount', { count: rolePermissions.length }) }}
              </span>
            </div>

            <Alert v-if="editingRole?.slug === 'admin'" variant="default" class="py-2 text-xs">
              <Lock class="h-3.5 w-3.5" />
              <AlertDescription>{{ t('adminRoles.adminCoreLocked') }}</AlertDescription>
            </Alert>

            <div class="grid gap-3 sm:grid-cols-2">
              <div
                v-for="(perms, groupName) in groupedPermissions"
                :key="groupName"
                class="rounded-lg border bg-muted/20 p-3 space-y-2.5"
              >
                <p class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {{ groupTitle(String(groupName)) }}
                </p>
                <label
                  v-for="perm in perms"
                  :key="perm.key"
                  class="flex items-start gap-2.5 text-sm"
                  :class="isCoreLockedPermission(perm.key) ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'"
                >
                  <input
                    type="checkbox"
                    class="mt-0.5 h-4 w-4 rounded border-input accent-primary"
                    :checked="rolePermissions.includes(perm.key)"
                    :disabled="isCoreLockedPermission(perm.key)"
                    @change="toggleRolePermission(perm.key)"
                  />
                  <div class="min-w-0">
                    <p class="text-xs font-medium leading-tight text-foreground">{{ perm.label }}</p>
                    <p class="mt-0.5 text-[11px] leading-snug text-muted-foreground">{{ perm.description }}</p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" :disabled="roleSaving" @click="roleDialogOpen = false">
              {{ t('common.cancel') }}
            </Button>
            <Button type="submit" :disabled="roleSaving">
              {{
                roleSaving
                  ? t('common.saving')
                  : editingRole
                    ? t('adminRoles.saveRole')
                    : t('adminRoles.createRoleBtn')
              }}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <!-- Delete Role Confirmation Dialog -->
    <Dialog v-model:open="deleteRoleDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ t('adminRoles.deleteTitle') }}</DialogTitle>
          <DialogDescription>
            {{ t('adminRoles.deleteConfirm', { name: roleToDelete?.name }) }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" size="sm" :disabled="deletingRole" @click="deleteRoleDialogOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button variant="destructive" size="sm" :disabled="deletingRole" @click="handleConfirmDeleteRole">
            {{ deletingRole ? t('adminReports.deleting') : t('adminReports.deleteBtn') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
