export type UserRole = string
export type ReportStatus = 'Pending' | 'In Progress' | 'Resolved'

export interface User {
  id: number
  full_name: string
  email: string
  role: UserRole
  is_active?: boolean
  permissions?: string[]
  created_at: string
}

export interface AdminUser extends User {
  is_active: boolean
  report_count: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface PermissionDefinition {
  key: string
  group: string
  label: string
  description: string
}

export interface RoleItem {
  id: number
  slug: string
  name: string
  description: string | null
  permissions: string[]
  is_system: boolean
  user_count: number
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Category {
  id: number
  name: string
  name_km: string | null
  description: string | null
  description_km: string | null
  created_at: string
  report_count: number
}

export interface StatusHistory {
  id: number
  report_id: number
  changed_by: number
  actor_name: string
  actor_role: string
  old_status: string | null
  new_status: ReportStatus
  note: string | null
  changed_at: string
}

export interface WasteReport {
  id: number
  user_id: number
  reporter_name: string
  reporter_email: string
  category_id: number
  category_name: string
  category_name_km: string | null
  title: string
  description: string
  location_text: string
  latitude: number | null
  longitude: number | null
  photo_path: string | null
  resolution_photo_path?: string | null
  status: ReportStatus
  created_at: string
  updated_at: string
}

export interface ReportUploadPolicy {
  max_file_size_mb: number
  allowed_extensions: string[]
  max_photos: number
  max_total_size_mb: number
}

export interface WasteReportDetail extends WasteReport {
  status_history: StatusHistory[]
  photo_paths: string[]
  location_district: number | null
  public_district: number | null
  public_province: number | null
}

export interface ReportArea {
  code: number
  name: string
  name_km: string
}

export interface ReportProvince extends ReportArea {
  districts: ReportArea[]
}

export interface CommunityReport {
  id: number
  title: string
  description: string
  photo_path: string | null
  photo_paths: string[]
  category_id: number
  category_name: string
  category_name_km: string | null
  province: number
  province_name: string
  province_name_km: string
  district: number | null
  district_name: string | null
  district_name_km: string | null
  latitude: number | null
  longitude: number | null
  reported_on: string
  status: ReportStatus
  resolution_note: string | null
}

export interface CommunityReportsPage {
  items: CommunityReport[]
  has_more: boolean
}

export interface PublicStats {
  total_reports: number
  pending_reports: number
  in_progress_reports: number
  resolved_reports: number
  total_categories: number
}

export interface StatusDistributionItem {
  status: string
  count: number
}

export interface CategoryDistributionItem {
  category: string
  category_km: string | null
  count: number
}

export interface NearbyReportItem {
  id: number
  title: string
  status: ReportStatus
  location_text: string
  distance_meters: number
  created_at: string
}

export interface MapPinReport {
  id: number
  title: string
  status: ReportStatus
  latitude: number
  longitude: number
  location_text: string
  category_name: string
  category_name_km: string | null
  created_at: string
}

export interface AdminDashboardStats {
  total_reports: number
  pending_count: number
  in_progress_count: number
  resolved_count: number
  total_users: number
  total_categories: number
  status_distribution: StatusDistributionItem[]
  category_distribution: CategoryDistributionItem[]
  recent_reports: WasteReport[]
  map_pins?: MapPinReport[]
}

export type StorageProviderId = 'cloudinary' | 's3_compatible' | 'local'

export interface ProviderOption {
  id: StorageProviderId
  label: string
  description: string
  supports_cdn: boolean
}

export interface CloudinarySettings {
  cloud_name: string
  api_key: string
  api_secret_masked: string
  has_api_secret: boolean
  folder: string
}

export interface S3Settings {
  endpoint_url: string
  region: string
  bucket: string
  access_key_id: string
  secret_access_key_masked: string
  has_secret_access_key: boolean
  public_base_url: string
  folder: string
}

export interface StorageSettings {
  provider: StorageProviderId
  max_file_size_mb: number
  allowed_extensions: string[]
  cloudinary: CloudinarySettings
  s3: S3Settings
}

export interface GeneralSettings {
  site_name: string
  allow_registration: boolean
}

export interface AdminSettings {
  general: GeneralSettings
  storage: StorageSettings
  available_providers: ProviderOption[]
  last_updated_at: string | null
  last_updated_by: string | null
}

export interface AdminSettingsUpdatePayload {
  general: GeneralSettings
  storage: {
    provider: StorageProviderId
    max_file_size_mb: number
    allowed_extensions: string[]
    cloudinary: {
      cloud_name: string
      api_key: string
      api_secret?: string | null
      folder: string
    }
    s3: {
      endpoint_url: string
      region: string
      bucket: string
      access_key_id: string
      secret_access_key?: string | null
      public_base_url: string
      folder: string
    }
  }
}

export interface StorageTestResult {
  ok: boolean
  provider: string
  message: string
}
