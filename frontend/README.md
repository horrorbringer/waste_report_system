# EcoWatch Frontend (Vue 3 + shadcn-vue + shadcn-vue Charts)

Modern single-page web application for the **Community Waste Reporting System**, built with Vue 3, TypeScript, Tailwind CSS, **shadcn-vue**, and native **shadcn-vue Charts** (`@unovis/vue`).

## Tech Stack
- **Framework**: Vue 3 (`<script setup lang="ts">`) + Vite 6 + TypeScript
- **State & Routing**: Pinia + Vue Router 4 (with strict RBAC navigation guards)
- **UI System**: [shadcn-vue](https://shadcn-vue.com/) (Tailwind CSS + Radix Vue primitives + Lucide Icons)
- **Charts**: [shadcn-vue Charts](https://shadcn-vue.com/charts) powered by `@unovis/vue` & `@unovis/ts`
- **Typography**: Plus Jakarta Sans (display/KPIs), Inter (UI/body), JetBrains Mono (IDs/coordinates)
- **HTTP Client**: Axios with JWT Bearer token interceptor

## Folder Structure
```text
frontend/
├── index.html                   # Webfont imports & app mount
├── vite.config.ts               # Path alias (@) & proxy (/api, /uploads -> :8000)
├── tailwind.config.js           # shadcn-vue theme tokens & font families
├── components.json              # shadcn-vue configuration
└── src/
    ├── assets/index.css         # CSS variables, chart tokens & typography scale
    ├── components/
    │   ├── StatusBadge.vue      # Color-coded Pending / In Progress / Resolved badge
    │   └── ui/                  # shadcn-vue components (button, card, dialog, select, table, chart)
    ├── layouts/
    │   ├── AppLayout.vue        # Public & Resident navigation shell
    │   └── AdminLayout.vue      # Admin Console sidebar shell
    ├── router/index.ts          # Routes & RBAC beforeEach navigation guard
    ├── services/api.ts          # Axios instance & Bearer auth interceptor
    ├── stores/                  # Pinia stores (auth, reports, categories, settings)
    ├── types/index.ts           # Shared TypeScript interfaces
    └── views/
        ├── HomeView.vue         # Landing page + live community stats
        ├── LoginView.vue        # Sign in + quick demo account buttons
        ├── RegisterView.vue     # Resident registration
        ├── SubmitReportView.vue # Waste report form with GPS & photo preview
        ├── MyReportsView.vue    # Resident reports portfolio & filters
        ├── ReportDetailView.vue # Full report details & vertical status audit trail
        ├── ForbiddenView.vue    # 403 RBAC Access Denied page
        └── admin/
            ├── DashboardView.vue          # KPI cards + Unovis Donut & Bar Charts
            ├── ReportsManagementView.vue  # Search, filter & Status Update dialog
            ├── CategoryManagementView.vue # Waste category CRUD console
            └── SettingsView.vue           # Pluggable storage & policy settings
```

## Setup & Scripts
```bash
# Install dependencies
npm install

# Configure environment variables (optional for local dev; required for production API URL)
cp .env.example .env

# Start Vite dev server (http://localhost:5173)
# Proxies /api and /uploads to VITE_API_PROXY_TARGET (default http://127.0.0.1:8000)
npm run dev

# Type-check & build for production
npm run build

# Preview production bundle
npm run preview
```

## Role-Based Routes (RBAC)
| Path | Access | Purpose |
| :--- | :--- | :--- |
| `/`, `/login`, `/register` | Public | Landing page & authentication |
| `/reports/new`, `/my-reports`, `/reports/:id` | Resident & Admin | Submit & track personal waste reports |
| `/admin/dashboard` | Admin only | KPI tiles & native shadcn-vue analytics charts |
| `/admin/reports` | Admin only | Search, filter, and update report statuses |
| `/admin/categories` | Admin only | Create, edit, and delete waste categories |
| `/admin/settings` | Admin only | Configure Cloudinary / S3 (Sabay Cloud) / Local storage & policies |
| `/403` | Authenticated | Redirect target when a Resident attempts to access Admin routes |
