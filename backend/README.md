# EcoWatch Backend (FastAPI + PostgreSQL + Pluggable Storage)

REST API backend for the **Community Waste Reporting System**, featuring JWT authentication, Role-Based Access Control (RBAC), PostgreSQL persistence, encrypted admin settings, and pluggable cloud file storage (**Cloudinary**, **S3-Compatible / Sabay Cloud**, or **Local Disk**).

## Tech Stack
- **Framework**: FastAPI (Python 3.12+)
- **Database & ORM**: PostgreSQL (`psycopg` v3 with connection pooling) + SQLAlchemy 2.0
- **Validation**: Pydantic v2 + `pydantic-settings`
- **Security**: `PyJWT` (Bearer JWT), `bcrypt` password hashing, `cryptography` (Fernet encryption at rest for provider API secrets)
- **File Storage**: Pluggable provider architecture (`cloudinary`, `boto3` S3-compatible / Sabay Cloud, local disk) with Pillow binary image verification
- **Testing**: `pytest` + `httpx` (`TestClient`)

## Folder Structure
```text
backend/
├── app/
│   ├── main.py                  # FastAPI app, CORS, router registration, /api/health
│   ├── config.py                # Environment settings & PostgreSQL URL normalization
│   ├── database.py              # SQLAlchemy engine & session dependency
│   ├── models.py                # users, categories, waste_reports, status_history, system_settings
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── security.py              # bcrypt hashing, JWT tokens, Fernet encryption & masking
│   ├── deps.py                  # RBAC dependencies (get_current_user, require_role, require_admin)
│   ├── utils.py                 # Response serializers
│   ├── routers/
│   │   ├── auth.py              # /api/auth/*
│   │   ├── reports.py           # /api/reports/*
│   │   ├── categories.py        # /api/categories/*
│   │   ├── admin.py             # /api/stats/public & /api/admin/stats
│   │   └── settings.py          # /api/admin/settings & /storage/test
│   └── services/
│       ├── settings_service.py  # Encrypted DB settings with .env fallback
│       └── storage/             # Pluggable storage providers (Cloudinary, S3/Sabay, Local)
├── tests/                       # Automated pytest suite
├── seed.py                      # Database seeder (categories, demo users, sample reports)
├── requirements.txt
└── .env.example
```

## Setup & Running Locally

### 1. Create Virtual Environment & Install Dependencies
```bash
python -m venv .venv
.\.venv\Scripts\activate      # Windows PowerShell
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```
Edit `.env` with your PostgreSQL `DATABASE_URL` and optional default storage credentials. (Storage providers and credentials can also be updated dynamically at runtime in **Admin Console → Settings**.)

### 3. Seed Database & Start Server
```bash
# Ensure PostgreSQL is running (e.g. `docker compose up -d db` from repo root)
python seed.py
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/health`

## API Endpoints Overview
| Group | Method & Path | Access |
| :--- | :--- | :--- |
| **Auth** | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` | Public / Auth |
| **Reports** | `POST /api/reports`, `GET /api/reports/my`, `GET /api/reports/{id}` | Resident / Admin (owner check) |
| **Admin Reports** | `GET /api/reports`, `PATCH /api/reports/{id}/status` | Admin only |
| **Categories** | `GET /api/categories` (Public), `POST/PUT/DELETE /api/categories` | Admin only for writes |
| **Analytics** | `GET /api/stats/public` (Public), `GET /api/admin/stats` | Admin only |
| **Admin Settings** | `GET/PUT /api/admin/settings`, `POST /api/admin/settings/storage/test` | Admin only |

## Running Tests
```bash
.\.venv\Scripts\python -m pytest tests/ -v
```
