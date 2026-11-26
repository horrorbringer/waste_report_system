from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, SessionLocal, engine, ensure_schema_columns
from app.permissions import ensure_default_roles
from app.routers import admin, auth, categories, reports
from app.routers import settings as settings_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema_columns(engine)
    with SessionLocal() as db:
        ensure_default_roles(db)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API for submitting, reviewing, tracking, and resolving community waste reports.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local uploads folder so switching dynamically to Local Storage in Admin Settings works immediately
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(settings_router.router)


@app.get("/api/health", tags=["Health"])
def health_check() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "database_dialect": engine.dialect.name,
        "default_storage_backend": settings.STORAGE_BACKEND,
        "cloudinary_env_configured": settings.cloudinary_configured,
    }
