from sqlalchemy import select
from sqlalchemy.orm import Session

ALL_PERMISSIONS: list[dict[str, str]] = [
    {
        "key": "dashboard:view",
        "group": "dashboard",
        "label": "View Admin Dashboard",
        "description": "Access admin analytics, charts, and summary metrics.",
    },
    {
        "key": "reports:view_all",
        "group": "reports",
        "label": "View All Reports",
        "description": "View all submitted reports across all residents.",
    },
    {
        "key": "reports:update_status",
        "group": "reports",
        "label": "Update Report Status & Area",
        "description": "Change report status, add review notes, and set published area.",
    },
    {
        "key": "reports:delete_any",
        "group": "reports",
        "label": "Delete Any Report",
        "description": "Delete any waste report (single or bulk).",
    },
    {
        "key": "categories:manage",
        "group": "categories",
        "label": "Manage Categories",
        "description": "Create, edit, and delete waste categories.",
    },
    {
        "key": "users:manage",
        "group": "administration",
        "label": "Manage Users",
        "description": "View, create, edit, and delete user accounts.",
    },
    {
        "key": "roles:manage",
        "group": "administration",
        "label": "Manage Roles & Permissions",
        "description": "Create, edit, and delete roles and adjust their permissions.",
    },
    {
        "key": "settings:manage",
        "group": "administration",
        "label": "Manage System Settings",
        "description": "Configure storage providers, API keys, and registration settings.",
    },
]

VALID_PERMISSION_KEYS: set[str] = {p["key"] for p in ALL_PERMISSIONS}

DEFAULT_ROLES: list[dict[str, object]] = [
    {
        "slug": "resident",
        "name": "Resident",
        "description": "Standard community member who can submit and manage their own pending reports.",
        "permissions": [],
        "is_system": True,
    },
    {
        "slug": "moderator",
        "name": "Moderator",
        "description": "Operations staff who can review reports, update statuses, and manage categories.",
        "permissions": [
            "dashboard:view",
            "reports:view_all",
            "reports:update_status",
            "reports:delete_any",
            "categories:manage",
        ],
        "is_system": True,
    },
    {
        "slug": "admin",
        "name": "Administrator",
        "description": "Full system administrator with unrestricted access to all features and settings.",
        "permissions": [p["key"] for p in ALL_PERMISSIONS],
        "is_system": True,
    },
]


def ensure_default_roles(db: Session) -> None:
    """Seed built-in system roles if they do not exist yet."""
    from app.models import Role

    existing_slugs = set(db.scalars(select(Role.slug)).all())
    added = False
    for role_data in DEFAULT_ROLES:
        if role_data["slug"] not in existing_slugs:
            db.add(
                Role(
                    slug=str(role_data["slug"]),
                    name=str(role_data["name"]),
                    description=str(role_data["description"]),
                    permissions=list(role_data["permissions"]),  # type: ignore[arg-type]
                    is_system=bool(role_data["is_system"]),
                )
            )
            added = True
    if added:
        db.commit()


def get_role_permissions(db: Session, role_slug: str) -> list[str]:
    """Resolve permission keys for a given role slug."""
    from app.models import Role

    if role_slug == "admin":
        return [p["key"] for p in ALL_PERMISSIONS]

    role = db.scalar(select(Role).where(Role.slug == role_slug))
    if role is not None:
        return [p for p in (role.permissions or []) if p in VALID_PERMISSION_KEYS]

    # Fallback to defaults if role table hasn't been seeded yet
    for item in DEFAULT_ROLES:
        if item["slug"] == role_slug:
            return list(item["permissions"])  # type: ignore[arg-type]
    return []
