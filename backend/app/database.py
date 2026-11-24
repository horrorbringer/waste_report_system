from collections.abc import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def build_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(database_url, connect_args={"check_same_thread": False})
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


engine = build_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_schema_columns(target_engine: Engine) -> None:
    """Safely add newly introduced columns on existing databases (PostgreSQL & SQLite)."""
    inspector = inspect(target_engine)
    alter_statements: list[str] = []
    if inspector.has_table("categories"):
        existing_cols = {col["name"] for col in inspector.get_columns("categories")}
        if "name_km" not in existing_cols:
            alter_statements.append("ALTER TABLE categories ADD COLUMN name_km VARCHAR(150)")
        if "description_km" not in existing_cols:
            alter_statements.append("ALTER TABLE categories ADD COLUMN description_km VARCHAR(600)")

    if inspector.has_table("waste_reports"):
        report_columns = {col["name"] for col in inspector.get_columns("waste_reports")}
        if_not_exists = " IF NOT EXISTS" if target_engine.dialect.name == "postgresql" else ""
        report_fields = {
            "public_district": "INTEGER", "public_province": "INTEGER", "location_district": "INTEGER", "photo_paths": "JSON"
        }
        for column, column_type in report_fields.items():
            if column not in report_columns:
                alter_statements.append(
                    f"ALTER TABLE waste_reports ADD COLUMN{if_not_exists} {column} {column_type}"
                )

    if alter_statements:
        with target_engine.begin() as conn:
            for stmt in alter_statements:
                conn.execute(text(stmt))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
