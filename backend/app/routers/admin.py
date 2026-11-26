import re
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user, require_permission, user_has_permission
from app.models import Category, Role, StatusHistory, User, WasteReport
from app.permissions import ALL_PERMISSIONS, VALID_PERMISSION_KEYS
from app.schemas import (
    AdminDashboardStats,
    AdminUserCreate,
    AdminUserResponse,
    AdminUserUpdate,
    CategoryDistributionItem,
    PermissionDefinition,
    PublicStatsResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    StatusDistributionItem,
)
from app.security import hash_password
from app.services.storage.registry import delete_report_photos
from app.utils import serialize_report

router = APIRouter(tags=["Analytics & Admin"])

ORDERED_STATUSES = ["Pending", "In Progress", "Resolved"]


@router.get("/api/stats/public", response_model=PublicStatsResponse)
def get_public_stats(db: Session = Depends(get_db)) -> PublicStatsResponse:
    total = int(db.scalar(select(func.count(WasteReport.id))) or 0)
    pending = int(
        db.scalar(select(func.count(WasteReport.id)).where(WasteReport.status == "Pending")) or 0
    )
    in_progress = int(
        db.scalar(select(func.count(WasteReport.id)).where(WasteReport.status == "In Progress")) or 0
    )
    resolved = int(
        db.scalar(select(func.count(WasteReport.id)).where(WasteReport.status == "Resolved")) or 0
    )
    categories_count = int(db.scalar(select(func.count(Category.id))) or 0)

    return PublicStatsResponse(
        total_reports=total,
        pending_reports=pending,
        in_progress_reports=in_progress,
        resolved_reports=resolved,
        total_categories=categories_count,
    )


@router.get("/api/admin/stats", response_model=AdminDashboardStats)
def get_admin_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("dashboard:view")),
) -> AdminDashboardStats:
    total_reports = int(db.scalar(select(func.count(WasteReport.id))) or 0)
    total_users = int(db.scalar(select(func.count(User.id))) or 0)
    total_categories = int(db.scalar(select(func.count(Category.id))) or 0)

    status_rows = db.execute(
        select(WasteReport.status, func.count(WasteReport.id)).group_by(WasteReport.status)
    ).all()
    status_map = {row[0]: int(row[1]) for row in status_rows}

    pending_count = status_map.get("Pending", 0)
    in_progress_count = status_map.get("In Progress", 0)
    resolved_count = status_map.get("Resolved", 0)

    status_distribution = [
        StatusDistributionItem(status=st, count=status_map.get(st, 0)) for st in ORDERED_STATUSES
    ]

    cat_rows = db.execute(
        select(Category.name, Category.name_km, func.count(WasteReport.id))
        .outerjoin(WasteReport, WasteReport.category_id == Category.id)
        .group_by(Category.id)
        .order_by(func.count(WasteReport.id).desc(), Category.name.asc())
    ).all()
    category_distribution = [
        CategoryDistributionItem(category=row[0], category_km=row[1], count=int(row[2] or 0))
        for row in cat_rows
    ]

    recent = db.scalars(
        select(WasteReport)
        .options(joinedload(WasteReport.user), joinedload(WasteReport.category))
        .order_by(WasteReport.created_at.desc())
        .limit(8)
    ).all()

    return AdminDashboardStats(
        total_reports=total_reports,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        total_users=total_users,
        total_categories=total_categories,
        status_distribution=status_distribution,
        category_distribution=category_distribution,
        recent_reports=[serialize_report(r) for r in recent],
    )


@router.get("/api/admin/users", response_model=list[AdminUserResponse])
def list_admin_users(
    search: str | None = Query(default=None, max_length=100),
    role: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("users:manage")),
) -> list[AdminUserResponse]:
    stmt = (
        select(User, func.count(WasteReport.id).label("report_count"))
        .outerjoin(WasteReport, WasteReport.user_id == User.id)
        .group_by(User.id)
        .order_by(User.created_at.desc(), User.id.desc())
    )

    if role and role.strip() and role.strip().upper() != "ALL":
        stmt = stmt.where(User.role == role.strip().lower())
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(or_(User.full_name.ilike(pattern), User.email.ilike(pattern)))

    rows = db.execute(stmt).all()
    return [
        AdminUserResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            report_count=int(report_count or 0),
        )
        for user, report_count in rows
    ]


def _validate_role_exists(db: Session, role_slug: str) -> str:
    clean_slug = role_slug.strip().lower()
    role_obj = db.scalar(select(Role).where(Role.slug == clean_slug))
    if role_obj is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{clean_slug}' does not exist.",
        )
    return clean_slug


@router.post("/api/admin/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("users:manage")),
) -> AdminUserResponse:
    normalized_email = payload.email.strip().lower()
    existing = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    role_slug = _validate_role_exists(db, payload.role)
    user = User(
        full_name=payload.full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=role_slug,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return AdminUserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        report_count=0,
    )


@router.patch("/api/admin/users/{user_id}", response_model=AdminUserResponse)
def update_admin_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_permission("users:manage")),
) -> AdminUserResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if payload.role is not None:
        role_slug = _validate_role_exists(db, payload.role)
        if user.id == current_admin.id and role_slug != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove your own admin role.",
            )
        user.role = role_slug

    if payload.full_name is not None:
        clean_name = payload.full_name.strip()
        if len(clean_name) < 2:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Full name is too short.")
        user.full_name = clean_name

    if payload.password:
        user.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(user)

    report_count = int(db.scalar(select(func.count(WasteReport.id)).where(WasteReport.user_id == user.id)) or 0)
    return AdminUserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        report_count=report_count,
    )


@router.delete("/api/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_permission("users:manage")),
) -> Response:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own active admin account.",
        )

    has_history = db.scalar(select(StatusHistory.id).where(StatusHistory.changed_by == user.id).limit(1))
    if has_history is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a user who has audit history entries.",
        )

    photo_urls: list[str] = []
    for report in user.reports:
        photo_urls.extend(report.photo_paths or ([report.photo_path] if report.photo_path else []))

    db.delete(user)
    db.commit()
    delete_report_photos(photo_urls, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _slugify_role(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return slug[:40]


def _sanitize_permissions(perms: list[str]) -> list[str]:
    unknown = [p for p in perms if p not in VALID_PERMISSION_KEYS]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown permission key(s): {', '.join(unknown)}",
        )
    # Preserve canonical order and deduplicate
    selected = set(perms)
    return [p["key"] for p in ALL_PERMISSIONS if p["key"] in selected]


@router.get("/api/admin/permissions", response_model=list[PermissionDefinition])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PermissionDefinition]:
    if not (
        user_has_permission(db, current_user, "roles:manage")
        or user_has_permission(db, current_user, "users:manage")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    return [PermissionDefinition(**p) for p in ALL_PERMISSIONS]


@router.get("/api/admin/roles", response_model=list[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RoleResponse]:
    if not (
        user_has_permission(db, current_user, "roles:manage")
        or user_has_permission(db, current_user, "users:manage")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    roles = db.scalars(select(Role).order_by(Role.is_system.desc(), Role.id.asc())).all()
    counts_rows = db.execute(select(User.role, func.count(User.id)).group_by(User.role)).all()
    counts = {row[0]: int(row[1] or 0) for row in counts_rows}

    return [
        RoleResponse(
            id=r.id,
            slug=r.slug,
            name=r.name,
            description=r.description,
            permissions=list(r.permissions or []),
            is_system=r.is_system,
            user_count=counts.get(r.slug, 0),
            created_at=r.created_at,
        )
        for r in roles
    ]


@router.post("/api/admin/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("roles:manage")),
) -> RoleResponse:
    slug = (payload.slug.strip().lower() if payload.slug else _slugify_role(payload.name))
    if len(slug) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role slug must be at least 2 characters.",
        )

    existing = db.scalar(select(Role).where(Role.slug == slug))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A role with key '{slug}' already exists.",
        )

    clean_perms = _sanitize_permissions(payload.permissions)
    role = Role(
        slug=slug,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description and payload.description.strip() else None,
        permissions=clean_perms,
        is_system=False,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return RoleResponse(
        id=role.id,
        slug=role.slug,
        name=role.name,
        description=role.description,
        permissions=list(role.permissions or []),
        is_system=role.is_system,
        user_count=0,
        created_at=role.created_at,
    )


@router.patch("/api/admin/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("roles:manage")),
) -> RoleResponse:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    if payload.name is not None:
        clean_name = payload.name.strip()
        if len(clean_name) < 2:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Role name is too short.")
        role.name = clean_name

    if payload.description is not None:
        role.description = payload.description.strip() if payload.description.strip() else None

    if payload.permissions is not None:
        clean_perms = _sanitize_permissions(payload.permissions)
        if role.slug == "admin":
            missing_core = {"roles:manage", "users:manage"} - set(clean_perms)
            if missing_core:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Administrator role must retain users:manage and roles:manage permissions.",
                )
        role.permissions = clean_perms

    db.commit()
    db.refresh(role)
    user_count = int(db.scalar(select(func.count(User.id)).where(User.role == role.slug)) or 0)
    return RoleResponse(
        id=role.id,
        slug=role.slug,
        name=role.name,
        description=role.description,
        permissions=list(role.permissions or []),
        is_system=role.is_system,
        user_count=user_count,
        created_at=role.created_at,
    )


@router.delete("/api/admin/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("roles:manage")),
) -> Response:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Built-in system roles cannot be deleted.",
        )

    assigned = int(db.scalar(select(func.count(User.id)).where(User.role == role.slug)) or 0)
    if assigned > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role '{role.name}' while {assigned} user(s) are assigned to it.",
        )

    db.delete(role)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
