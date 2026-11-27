import csv
import io
import math
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.cambodia_areas import Province, districts_by_code, provinces, provinces_by_code
from app.database import get_db
from app.deps import get_current_user, require_permission, require_resident_or_admin, user_has_permission
from app.models import Category, StatusHistory, User, WasteReport
from app.schemas import (
    AdminReportsPage,
    BulkActionResponse,
    BulkDeleteRequest,
    BulkStatusRequest,
    CommunityReport,
    CommunityReportsPage,
    NearbyReportItem,
    DistrictCode,
    ReportDetailResponse,
    ReportPublication,
    ReportResponse,
    ReportUpdateStatus,
    ReportUploadPolicy,
)
from app.services.settings_service import resolve_settings
from app.services.storage.registry import delete_report_photos, report_upload_policy, store_report_photos
from app.utils import serialize_report, serialize_report_detail

router = APIRouter(prefix="/api/reports", tags=["Reports"])

VALID_STATUSES = {"Pending", "In Progress", "Resolved"}
PHNOM_PENH_TIMEZONE = timezone(timedelta(hours=7))


@router.get("/areas")
def list_report_areas() -> list[Province]:
    return provinces


def _serialize_community_report(
    row: tuple,
    latest_notes: dict[int, str],
) -> CommunityReport:
    (
        report_id,
        title,
        description,
        photo_path,
        photo_paths,
        category_id,
        category_name,
        category_name_km,
        province_code,
        district_code,
        latitude,
        longitude,
        created_at,
        report_status,
    ) = row
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    province = provinces_by_code[province_code or district_code // 100]
    district = districts_by_code.get(district_code) if district_code is not None else None
    resolved_photos = photo_paths or ([photo_path] if photo_path else [])
    return CommunityReport(
        id=report_id,
        title=title,
        description=description,
        photo_path=photo_path,
        photo_paths=resolved_photos,
        category_id=category_id,
        category_name=category_name,
        category_name_km=category_name_km,
        province=province["code"],
        province_name=province["name"],
        province_name_km=province["name_km"],
        district=district_code,
        district_name=district["name"] if district else None,
        district_name_km=district["name_km"] if district else None,
        latitude=latitude,
        longitude=longitude,
        reported_on=created_at.astimezone(PHNOM_PENH_TIMEZONE).date(),
        status=report_status,
        resolution_note=latest_notes.get(report_id),
    )


def _fetch_latest_notes(db: Session, report_ids: list[int]) -> dict[int, str]:
    if not report_ids:
        return {}
    rows = db.execute(
        select(StatusHistory.report_id, StatusHistory.note)
        .where(
            StatusHistory.report_id.in_(report_ids),
            StatusHistory.note.is_not(None),
            StatusHistory.note != "",
        )
        .order_by(StatusHistory.changed_at.desc(), StatusHistory.id.desc())
    ).all()
    notes: dict[int, str] = {}
    for rid, note in rows:
        if rid not in notes and note:
            notes[rid] = note
    return notes


@router.get("/community", response_model=CommunityReportsPage)
def list_community_reports(
    response: Response,
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=100),
    status_filter: str | None = Query(default=None, alias="status"),
    category_id: int | None = Query(default=None),
    province: int | None = Query(default=None),
    sort: str = Query(default="newest"),
) -> CommunityReportsPage:
    response.headers["Cache-Control"] = "no-store"
    stmt = (
        select(
            WasteReport.id,
            WasteReport.title,
            WasteReport.description,
            WasteReport.photo_path,
            WasteReport.photo_paths,
            Category.id,
            Category.name,
            Category.name_km,
            WasteReport.public_province,
            WasteReport.public_district,
            WasteReport.latitude,
            WasteReport.longitude,
            WasteReport.created_at,
            WasteReport.status,
        )
        .join(WasteReport, WasteReport.category_id == Category.id)
        .where(or_(WasteReport.public_province.is_not(None), WasteReport.public_district.is_not(None)))
    )

    if status_filter and status_filter in VALID_STATUSES:
        stmt = stmt.where(WasteReport.status == status_filter)
    if category_id is not None:
        stmt = stmt.where(WasteReport.category_id == category_id)
    if province is not None:
        stmt = stmt.where(
            or_(
                WasteReport.public_province == province,
                WasteReport.public_district.between(province * 100, province * 100 + 99),
            )
        )
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                WasteReport.title.ilike(pattern),
                WasteReport.description.ilike(pattern),
                Category.name.ilike(pattern),
                Category.name_km.ilike(pattern),
            )
        )

    if sort == "oldest":
        stmt = stmt.order_by(WasteReport.created_at.asc(), WasteReport.id.asc())
    else:
        stmt = stmt.order_by(WasteReport.created_at.desc(), WasteReport.id.desc())

    reports = db.execute(stmt.offset(offset).limit(limit + 1)).all()
    page_rows = reports[:limit]
    latest_notes = _fetch_latest_notes(db, [row[0] for row in page_rows])
    items = [_serialize_community_report(row, latest_notes) for row in page_rows]
    return CommunityReportsPage(items=items, has_more=len(reports) > limit)


@router.get("/community/{report_id}", response_model=CommunityReport)
def get_community_report(
    report_id: int,
    response: Response,
    db: Session = Depends(get_db),
) -> CommunityReport:
    response.headers["Cache-Control"] = "no-store"
    row = db.execute(
        select(
            WasteReport.id,
            WasteReport.title,
            WasteReport.description,
            WasteReport.photo_path,
            WasteReport.photo_paths,
            Category.id,
            Category.name,
            Category.name_km,
            WasteReport.public_province,
            WasteReport.public_district,
            WasteReport.latitude,
            WasteReport.longitude,
            WasteReport.created_at,
            WasteReport.status,
        )
        .join(WasteReport, WasteReport.category_id == Category.id)
        .where(
            WasteReport.id == report_id,
            or_(WasteReport.public_province.is_not(None), WasteReport.public_district.is_not(None)),
        )
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published report not found.")
    latest_notes = _fetch_latest_notes(db, [report_id])
    return _serialize_community_report(row, latest_notes)


@router.get("/upload-policy", response_model=ReportUploadPolicy)
def get_report_upload_policy(
    db: Session = Depends(get_db),
    _: User = Depends(require_resident_or_admin),
) -> ReportUploadPolicy:
    return report_upload_policy(resolve_settings(db))


@router.post("", response_model=ReportDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    title: str = Form(...),
    description: str = Form(...),
    category_id: int = Form(...),
    location_text: str = Form(...),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    location_district: DistrictCode | None = Form(default=None),
    photo: UploadFile | None = File(default=None),
    photos: list[UploadFile] | None = File(default=None),
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

    files = ([photo] if photo is not None and photo.filename else []) + (photos or [])
    async with store_report_photos(files, db) as photo_paths:
        report = WasteReport(
            user_id=current_user.id,
            category_id=category.id,
            title=clean_title,
            description=clean_desc,
            location_text=clean_location,
            latitude=latitude,
            longitude=longitude,
            location_district=location_district,
            photo_path=photo_paths[0] if photo_paths else None,
            photo_paths=photo_paths or None,
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


def _apply_admin_report_filters(
    stmt,
    report_status: str | None,
    category_id: int | None,
    search: str | None,
):
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
    return stmt


def _build_admin_reports_stmt(
    report_status: str | None,
    category_id: int | None,
    search: str | None,
):
    stmt = (
        select(WasteReport)
        .join(User, WasteReport.user_id == User.id)
        .options(joinedload(WasteReport.user), joinedload(WasteReport.category))
    )
    return _apply_admin_report_filters(stmt, report_status, category_id, search).order_by(
        WasteReport.created_at.desc()
    )


@router.get("", response_model=AdminReportsPage)
def list_all_reports(
    report_status: str | None = Query(default=None, alias="status"),
    category_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=15, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("reports:view_all")),
) -> AdminReportsPage:
    count_stmt = _apply_admin_report_filters(
        select(func.count(WasteReport.id)).join(User, WasteReport.user_id == User.id),
        report_status,
        category_id,
        search,
    )
    total = int(db.scalar(count_stmt) or 0)
    stmt = _build_admin_reports_stmt(report_status, category_id, search).offset(offset).limit(limit)
    reports = db.scalars(stmt).all()
    return AdminReportsPage(
        items=[serialize_report(r) for r in reports],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/export")
def export_reports_csv(
    report_status: str | None = Query(default=None, alias="status"),
    category_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("reports:view_all")),
) -> Response:
    """Export filtered waste reports as a UTF-8 BOM CSV file."""
    reports = db.scalars(_build_admin_reports_stmt(report_status, category_id, search)).all()

    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf)
    writer.writerow(
        [
            "ID",
            "Title",
            "Status",
            "Category",
            "Reporter Name",
            "Reporter Email",
            "Location",
            "Province Code",
            "District Code",
            "Latitude",
            "Longitude",
            "Created At",
        ]
    )
    for r in reports:
        writer.writerow(
            [
                r.id,
                r.title,
                r.status,
                r.category.name if r.category else "",
                r.user.full_name if r.user else "",
                r.user.email if r.user else "",
                r.location_text,
                r.public_province or "",
                r.public_district or r.location_district or "",
                r.latitude if r.latitude is not None else "",
                r.longitude if r.longitude is not None else "",
                r.created_at.isoformat() if r.created_at else "",
            ]
        )

    filename = f"waste_reports_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=buf.getvalue().encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius = 6_371_000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * earth_radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/nearby", response_model=list[NearbyReportItem])
def find_nearby_unresolved_reports(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lng: float = Query(..., ge=-180.0, le=180.0),
    radius_meters: int = Query(default=200, ge=25, le=2000),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[NearbyReportItem]:
    """Find unresolved waste reports near a GPS coordinate to warn about potential duplicates."""
    lat_delta = radius_meters / 111_000.0
    lng_delta = radius_meters / max(111_000.0 * math.cos(math.radians(lat)), 10_000.0)

    candidates = db.scalars(
        select(WasteReport)
        .where(
            WasteReport.status != "Resolved",
            WasteReport.latitude.is_not(None),
            WasteReport.longitude.is_not(None),
            WasteReport.latitude.between(lat - lat_delta, lat + lat_delta),
            WasteReport.longitude.between(lng - lng_delta, lng + lng_delta),
        )
        .order_by(WasteReport.created_at.desc())
        .limit(30)
    ).all()

    nearby: list[NearbyReportItem] = []
    for r in candidates:
        if r.latitude is None or r.longitude is None:
            continue
        dist = _haversine_meters(lat, lng, r.latitude, r.longitude)
        if dist <= radius_meters:
            nearby.append(
                NearbyReportItem(
                    id=r.id,
                    title=r.title,
                    status=r.status,
                    location_text=r.location_text,
                    distance_meters=int(round(dist)),
                    created_at=r.created_at,
                )
            )
    nearby.sort(key=lambda item: item.distance_meters)
    return nearby[:5]


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
    if report.user_id != current_user.id and not user_has_permission(db, current_user, "reports:view_all"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this report.",
        )

    return serialize_report_detail(report)


@router.put("/{report_id}/publication", response_model=ReportPublication)
def set_report_publication(
    report_id: int,
    payload: ReportPublication,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("reports:update_status")),
) -> ReportPublication:
    result = db.execute(
        update(WasteReport)
        .where(WasteReport.id == report_id)
        .values(public_district=payload.district, public_province=payload.province, updated_at=WasteReport.updated_at)
    )
    if not result.rowcount:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    db.commit()
    return payload


@router.patch("/{report_id}/status", response_model=ReportDetailResponse)
def update_report_status(
    report_id: int,
    payload: ReportUpdateStatus,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_permission("reports:update_status")),
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


@router.post("/{report_id}/resolution-photo", response_model=ReportDetailResponse)
async def upload_resolution_photo(
    report_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("reports:update_status")),
) -> ReportDetailResponse:
    """Attach or replace an 'after cleanup' resolution photo for a report."""
    report = db.get(WasteReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    old_resolution_photo = report.resolution_photo_path
    async with store_report_photos([photo], db) as stored_paths:
        if not stored_paths:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Photo upload failed.")
        report.resolution_photo_path = stored_paths[0]
        report.updated_at = datetime.now(timezone.utc)
        db.commit()

    if old_resolution_photo:
        delete_report_photos([old_resolution_photo], db)

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


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    report = db.get(WasteReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if not user_has_permission(db, current_user, "reports:delete_any"):
        if report.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this report.",
            )
        if report.status != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending reports can be deleted by the owner.",
            )

    photo_urls = list(report.photo_paths or ([report.photo_path] if report.photo_path else []))
    if report.resolution_photo_path:
        photo_urls.append(report.resolution_photo_path)
    db.delete(report)
    db.commit()
    delete_report_photos(photo_urls, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/bulk-status", response_model=BulkActionResponse)
def bulk_update_report_status(
    payload: BulkStatusRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_permission("reports:update_status")),
) -> BulkActionResponse:
    reports = db.scalars(select(WasteReport).where(WasteReport.id.in_(payload.report_ids))).all()
    if not reports:
        return BulkActionResponse(affected=0)

    now = datetime.now(timezone.utc)
    clean_note = payload.note.strip() if payload.note else None
    for report in reports:
        old_status = report.status
        report.status = payload.status
        report.updated_at = now
        db.add(
            StatusHistory(
                report_id=report.id,
                changed_by=admin_user.id,
                old_status=old_status,
                new_status=payload.status,
                note=clean_note,
            )
        )
    db.commit()
    return BulkActionResponse(affected=len(reports))


@router.post("/bulk-delete", response_model=BulkActionResponse)
def bulk_delete_reports(
    payload: BulkDeleteRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("reports:delete_any")),
) -> BulkActionResponse:
    reports = db.scalars(select(WasteReport).where(WasteReport.id.in_(payload.report_ids))).all()
    if not reports:
        return BulkActionResponse(affected=0)

    photo_urls: list[str] = []
    for report in reports:
        photo_urls.extend(report.photo_paths or ([report.photo_path] if report.photo_path else []))
        if report.resolution_photo_path:
            photo_urls.append(report.resolution_photo_path)
        db.delete(report)

    db.commit()
    delete_report_photos(photo_urls, db)
    return BulkActionResponse(affected=len(reports))
