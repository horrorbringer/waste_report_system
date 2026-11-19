from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user, require_admin, require_resident_or_admin
from app.models import Category, StatusHistory, User, WasteReport
from app.schemas import ReportDetailResponse, ReportResponse, ReportUpdateStatus
from app.services.storage.registry import validate_and_upload_image
from app.utils import serialize_report, serialize_report_detail

router = APIRouter(prefix="/api/reports", tags=["Reports"])

VALID_STATUSES = {"Pending", "In Progress", "Resolved"}


@router.post("", response_model=ReportDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    title: str = Form(...),
    description: str = Form(...),
    category_id: int = Form(...),
    location_text: str = Form(...),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    photo: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_resident_or_admin),
) -> ReportDetailResponse:
    clean_title = title.strip()
    clean_desc = description.strip()
    clean_location = location_text.strip()

    if len(clean_title) < 3 or len(clean_title) > 200:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title must be between 3 and 200 characters.",
        )
    if len(clean_desc) < 10 or len(clean_desc) > 2000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Description must be between 10 and 2000 characters.",
        )
    if len(clean_location) < 3 or len(clean_location) > 300:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Location must be between 3 and 300 characters.",
        )

    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected category does not exist.",
        )

    if latitude is not None and not (-90.0 <= latitude <= 90.0):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid latitude.")
    if longitude is not None and not (-180.0 <= longitude <= 180.0):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid longitude.")

    photo_path: str | None = None
    if photo is not None and photo.filename:
        photo_path = await validate_and_upload_image(photo, db)

    report = WasteReport(
        user_id=current_user.id,
        category_id=category.id,
        title=clean_title,
        description=clean_desc,
        location_text=clean_location,
        latitude=latitude,
        longitude=longitude,
        photo_path=photo_path,
        status="Pending",
    )
    db.add(report)
    db.flush()

    initial_history = StatusHistory(
        report_id=report.id,
        changed_by=current_user.id,
        old_status=None,
        new_status="Pending",
        note="Report submitted by resident.",
    )
    db.add(initial_history)
    db.commit()

    loaded = db.scalar(
        select(WasteReport)
        .options(
            joinedload(WasteReport.user),
            joinedload(WasteReport.category),
            joinedload(WasteReport.status_history).joinedload(StatusHistory.actor),
        )
        .where(WasteReport.id == report.id)
    )
    return serialize_report_detail(loaded)  # type: ignore[arg-type]


@router.get("/my", response_model=list[ReportResponse])
def list_my_reports(
    report_status: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_resident_or_admin),
) -> list[ReportResponse]:
    stmt = (
        select(WasteReport)
        .options(joinedload(WasteReport.user), joinedload(WasteReport.category))
        .where(WasteReport.user_id == current_user.id)
    )
    if report_status and report_status in VALID_STATUSES:
        stmt = stmt.where(WasteReport.status == report_status)
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                WasteReport.title.ilike(term),
                WasteReport.description.ilike(term),
                WasteReport.location_text.ilike(term),
            )
        )
    stmt = stmt.order_by(WasteReport.created_at.desc())
    reports = db.scalars(stmt).all()
    return [serialize_report(r) for r in reports]


@router.get("", response_model=list[ReportResponse])
def list_all_reports(
    report_status: str | None = Query(default=None, alias="status"),
    category_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[ReportResponse]:
    stmt = (
        select(WasteReport)
        .join(User, WasteReport.user_id == User.id)
        .options(joinedload(WasteReport.user), joinedload(WasteReport.category))
    )
    if report_status and report_status in VALID_STATUSES:
        stmt = stmt.where(WasteReport.status == report_status)
    if category_id is not None:
        stmt = stmt.where(WasteReport.category_id == category_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                WasteReport.title.ilike(term),
                WasteReport.description.ilike(term),
                WasteReport.location_text.ilike(term),
                User.full_name.ilike(term),
                User.email.ilike(term),
            )
        )

    stmt = stmt.order_by(WasteReport.created_at.desc()).offset(offset).limit(limit)
    reports = db.scalars(stmt).all()
    return [serialize_report(r) for r in reports]


@router.get("/{report_id}", response_model=ReportDetailResponse)
def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportDetailResponse:
    report = db.scalar(
        select(WasteReport)
        .options(
            joinedload(WasteReport.user),
            joinedload(WasteReport.category),
            joinedload(WasteReport.status_history).joinedload(StatusHistory.actor),
        )
        .where(WasteReport.id == report_id)
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    # RBAC + resource ownership check
    if report.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this report.",
        )

    return serialize_report_detail(report)


@router.patch("/{report_id}/status", response_model=ReportDetailResponse)
def update_report_status(
    report_id: int,
    payload: ReportUpdateStatus,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> ReportDetailResponse:
    report = db.get(WasteReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    old_status = report.status
    new_status = payload.status

    report.status = new_status
    report.updated_at = datetime.now(timezone.utc)

    history_entry = StatusHistory(
        report_id=report.id,
        changed_by=admin_user.id,
        old_status=old_status,
        new_status=new_status,
        note=payload.note.strip() if payload.note else None,
    )
    db.add(history_entry)
    db.commit()

    loaded = db.scalar(
        select(WasteReport)
        .options(
            joinedload(WasteReport.user),
            joinedload(WasteReport.category),
            joinedload(WasteReport.status_history).joinedload(StatusHistory.actor),
        )
        .where(WasteReport.id == report.id)
    )
    return serialize_report_detail(loaded)  # type: ignore[arg-type]
