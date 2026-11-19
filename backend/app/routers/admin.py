from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_admin
from app.models import Category, User, WasteReport
from app.schemas import (
    AdminDashboardStats,
    CategoryDistributionItem,
    PublicStatsResponse,
    StatusDistributionItem,
)
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
    _: User = Depends(require_admin),
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
