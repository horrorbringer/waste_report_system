from collections.abc import Generator
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.main as main_module
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Category, User
from app.security import create_access_token, hash_password


@pytest.fixture()
def test_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    db_file = tmp_path / "test_waste.db"
    test_engine = create_engine(
        f"sqlite:///{db_file.as_posix()}", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Patch main module engine so FastAPI lifespan uses isolated test engine
    monkeypatch.setattr(main_module, "engine", test_engine)

    # Default tests to mocked Cloudinary credentials unless overridden
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "cloudinary")
    monkeypatch.setattr(settings, "CLOUDINARY_CLOUD_NAME", "demo-cloud")
    monkeypatch.setattr(settings, "CLOUDINARY_API_KEY", "demo-key")
    monkeypatch.setattr(settings, "CLOUDINARY_API_SECRET", "demo-secret")
    monkeypatch.setattr(settings, "CLOUDINARY_URL", "")
    monkeypatch.setattr(settings, "CLOUDINARY_FOLDER", "waste_reports")

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture()
def client(test_db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_users_and_categories(test_db: Session) -> dict:
    admin = User(
        full_name="Test Admin",
        email="admin@test.local",
        password_hash=hash_password("Admin@123"),
        role="admin",
    )
    resident1 = User(
        full_name="Resident One",
        email="resident1@test.local",
        password_hash=hash_password("Resident@123"),
        role="resident",
    )
    resident2 = User(
        full_name="Resident Two",
        email="resident2@test.local",
        password_hash=hash_password("Resident@123"),
        role="resident",
    )
    cat_plastic = Category(name="Plastic Waste", description="Plastic bottles and bags")
    cat_organic = Category(name="Organic Waste", description="Food and garden waste")

    test_db.add_all([admin, resident1, resident2, cat_plastic, cat_organic])
    test_db.commit()
    for obj in (admin, resident1, resident2, cat_plastic, cat_organic):
        test_db.refresh(obj)

    return {
        "admin": admin,
        "resident1": resident1,
        "resident2": resident2,
        "admin_headers": {"Authorization": f"Bearer {create_access_token(admin.id, admin.role)}"},
        "resident1_headers": {
            "Authorization": f"Bearer {create_access_token(resident1.id, resident1.role)}"
        },
        "resident2_headers": {
            "Authorization": f"Bearer {create_access_token(resident2.id, resident2.role)}"
        },
        "cat_plastic": cat_plastic,
        "cat_organic": cat_organic,
    }
