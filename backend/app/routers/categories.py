from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models import Category, User, WasteReport
from app.schemas import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryResponse]:
    stmt = (
        select(Category, func.count(WasteReport.id).label("report_count"))
        .outerjoin(WasteReport, WasteReport.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.name.asc())
    )
    rows = db.execute(stmt).all()
    return [
        CategoryResponse(
            id=cat.id,
            name=cat.name,
            name_km=cat.name_km,
            description=cat.description,
            description_km=cat.description_km,
            created_at=cat.created_at,
            report_count=int(count or 0),
        )
        for cat, count in rows
    ]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> CategoryResponse:
    clean_name = payload.name.strip()
    existing = db.scalar(select(Category).where(func.lower(Category.name) == clean_name.lower()))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{clean_name}' already exists.",
        )

    category = Category(
        name=clean_name,
        name_km=payload.name_km.strip() if payload.name_km and payload.name_km.strip() else None,
        description=payload.description.strip() if payload.description and payload.description.strip() else None,
        description_km=(
            payload.description_km.strip()
            if payload.description_km and payload.description_km.strip()
            else None
        ),
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return CategoryResponse(
        id=category.id,
        name=category.name,
        name_km=category.name_km,
        description=category.description,
        description_km=category.description_km,
        created_at=category.created_at,
        report_count=0,
    )


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> CategoryResponse:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    clean_name = payload.name.strip()
    duplicate = db.scalar(
        select(Category).where(
            func.lower(Category.name) == clean_name.lower(),
            Category.id != category_id,
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{clean_name}' already exists.",
        )

    category.name = clean_name
    category.name_km = payload.name_km.strip() if payload.name_km and payload.name_km.strip() else None
    category.description = (
        payload.description.strip() if payload.description and payload.description.strip() else None
    )
    category.description_km = (
        payload.description_km.strip()
        if payload.description_km and payload.description_km.strip()
        else None
    )
    db.commit()
    db.refresh(category)

    report_count = db.scalar(
        select(func.count(WasteReport.id)).where(WasteReport.category_id == category.id)
    )
    return CategoryResponse(
        id=category.id,
        name=category.name,
        name_km=category.name_km,
        description=category.description,
        description_km=category.description_km,
        created_at=category.created_at,
        report_count=int(report_count or 0),
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    linked_count = db.scalar(
        select(func.count(WasteReport.id)).where(WasteReport.category_id == category.id)
    )
    if linked_count and linked_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete category with {linked_count} associated report(s).",
        )

    db.delete(category)
    db.commit()
