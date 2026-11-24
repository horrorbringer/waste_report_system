from app.models import StatusHistory, WasteReport
from app.schemas import ReportDetailResponse, ReportResponse, StatusHistoryResponse


def serialize_report(report: WasteReport) -> ReportResponse:
    return ReportResponse(
        id=report.id,
        user_id=report.user_id,
        reporter_name=report.user.full_name if report.user else "Unknown",
        reporter_email=report.user.email if report.user else "",
        category_id=report.category_id,
        category_name=report.category.name if report.category else "Uncategorized",
        category_name_km=report.category.name_km if report.category else None,
        title=report.title,
        description=report.description,
        location_text=report.location_text,
        latitude=report.latitude,
        longitude=report.longitude,
        photo_path=report.photo_path,
        status=report.status,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


def serialize_status_history(entry: StatusHistory) -> StatusHistoryResponse:
    return StatusHistoryResponse(
        id=entry.id,
        report_id=entry.report_id,
        changed_by=entry.changed_by,
        actor_name=entry.actor.full_name if entry.actor else "System",
        actor_role=entry.actor.role if entry.actor else "system",
        old_status=entry.old_status,
        new_status=entry.new_status,
        note=entry.note,
        changed_at=entry.changed_at,
    )


def serialize_report_detail(report: WasteReport) -> ReportDetailResponse:
    base = serialize_report(report)
    history = [serialize_status_history(entry) for entry in report.status_history]
    return ReportDetailResponse(
        **base.model_dump(),
        status_history=history,
        photo_paths=report.photo_paths or ([report.photo_path] if report.photo_path else []),
        location_district=report.location_district,
        public_district=report.public_district,
        public_province=report.public_province or (report.public_district // 100 if report.public_district else None),
    )
