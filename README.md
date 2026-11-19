# EcoWatch — Community Waste Reporting System

A full-stack web platform for reporting neighborhood waste issues, managing cleanups, and tracking resolution progress with Role-Based Access Control (RBAC).

## Tech Stack
- **Backend**: FastAPI (Python 3.12), SQLAlchemy 2.0, Pydantic v2, JWT Auth (`PyJWT` + `bcrypt`), Pillow image verification
- **Database**: **PostgreSQL** (`psycopg` v3 driver + connection pooling)
- **File Storage**: **Cloudinary** (`cloudinary` Python SDK — HTTPS CDN delivery)
- **Frontend**: Vue 3 (Vite + TypeScript), Pinia, Vue Router
- **UI & Admin Console**: [shadcn-vue](https://shadcn-vue.com/) (Tailwind CSS + Radix Vue + Lucide Icons)
- **Analytics Charts**: [shadcn-vue Charts](https://shadcn-vue.com/charts) (`@unovis/vue`)

---

## Quick Start

### 1. Start PostgreSQL
Using Docker Compose (PostgreSQL 16):
```bash
docker compose up -d db
```
Or use any hosted PostgreSQL database (Neon, Supabase, Render, Railway) and place its connection URL in `backend/.env`.

### 2. Configure Environment Variables (`backend/.env`)
Copy `backend/.env.example` to `backend/.env` and fill in your PostgreSQL and Cloudinary credentials:
```bash
cp backend/.env.example backend/.env
```
Example `backend/.env`:
```env
SECRET_KEY=your-long-random-secret
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/waste_report_db

STORAGE_BACKEND=cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CLOUDINARY_FOLDER=waste_reports
```

### 3. Backend (FastAPI — Port 8000)
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Create PostgreSQL tables & seed categories, demo accounts, and sample reports
python seed.py

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
- API Docs (Swagger UI): `http://localhost:8000/docs`
- Health Check (shows active DB dialect & Cloudinary status): `http://localhost:8000/api/health`

### 4. Frontend (Vue 3 + shadcn-vue — Port 5173)
```bash
cd frontend
npm install
npm run dev
```
- Web App: `http://localhost:5173`

---

## Demo Accounts (Seeded)
| Role | Email | Password |
| :--- | :--- | :--- |
| Administrator | `admin@waste.local` | `Admin@123` |
| Resident | `resident@waste.local` | `Resident@123` |

## Running Tests
```bash
# Backend API, RBAC, PostgreSQL dialect & Cloudinary tests
cd backend
.\.venv\Scripts\python -m pytest tests/ -v

# Frontend TypeScript & production build check
cd frontend
npm run build
```
