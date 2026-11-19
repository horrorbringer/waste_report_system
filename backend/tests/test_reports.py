import io
from unittest.mock import MagicMock
import cloudinary.uploader
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import normalize_database_url, settings
from app.database import build_engine


def make_test_png_bytes() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (64, 64), color=(34, 197, 94))
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_postgres_url_normalization_and_engine_dialect():
    assert (
        normalize_database_url("postgres://user:pass@localhost:5432/waste_report_db")
        == "postgresql+psycopg://user:pass@localhost:5432/waste_report_db"
    )
    assert (
        normalize_database_url("postgresql://user:pass@localhost:5432/waste_report_db")
        == "postgresql+psycopg://user:pass@localhost:5432/waste_report_db"
    )
    pg_engine = build_engine("postgresql+psycopg://postgres:postgres@localhost:5432/waste_report_db")
    assert pg_engine.dialect.name == "postgresql"
    pg_engine.dispose()


def test_create_report_uploads_valid_photo_to_cloudinary(
    client: TestClient,
    seed_users_and_categories: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    cat_id = seed_users_and_categories["cat_plastic"].id
    png_bytes = make_test_png_bytes()

    mock_upload = MagicMock(
        return_value={
            "secure_url": "https://res.cloudinary.com/demo-cloud/image/upload/v1/waste_reports/sample.png"
        }
    )
    monkeypatch.setattr(cloudinary.uploader, "upload", mock_upload)

    res = client.post(
        "/api/reports",
        data={
            "title": "Plastic waste near park entrance",
            "description": "Bags of bottles and wrappers scattered beside the park bench.",
            "category_id": str(cat_id),
            "location_text": "Central Park East Gate",
            "latitude": "11.5564",
            "longitude": "104.9282",
        },
        files={"photo": ("waste.png", png_bytes, "image/png")},
        headers=seed_users_and_categories["resident1_headers"],
    )
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "Pending"
    assert (
        body["photo_path"]
        == "https://res.cloudinary.com/demo-cloud/image/upload/v1/waste_reports/sample.png"
    )
    assert len(body["status_history"]) == 1
    mock_upload.assert_called_once()
    call_kwargs = mock_upload.call_args.kwargs
    assert call_kwargs["folder"] == "waste_reports"
    assert call_kwargs["resource_type"] == "image"

    # Resident's "my reports" includes it
    my_res = client.get("/api/reports/my", headers=seed_users_and_categories["resident1_headers"])
    assert my_res.status_code == 200
    assert len(my_res.json()) == 1


def test_create_report_rejects_disallowed_file_before_cloudinary(
    client: TestClient,
    seed_users_and_categories: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    cat_id = seed_users_and_categories["cat_organic"].id
    mock_upload = MagicMock()
    monkeypatch.setattr(cloudinary.uploader, "upload", mock_upload)

    # Disallowed extension
    bad_ext = client.post(
        "/api/reports",
        data={
            "title": "Bad extension upload test",
            "description": "Trying to upload an executable script as report photo.",
            "category_id": str(cat_id),
            "location_text": "Street 5",
        },
        files={"photo": ("malware.exe", b"not an image", "application/octet-stream")},
        headers=seed_users_and_categories["resident1_headers"],
    )
    assert bad_ext.status_code == 400
    mock_upload.assert_not_called()

    # Fake PNG content
    fake_png = client.post(
        "/api/reports",
        data={
            "title": "Spoofed extension test",
            "description": "Plain text renamed to png should be rejected by Pillow verification.",
            "category_id": str(cat_id),
            "location_text": "Street 6",
        },
        files={"photo": ("fake.png", b"plain text not actually png", "image/png")},
        headers=seed_users_and_categories["resident1_headers"],
    )
    assert fake_png.status_code == 400
    mock_upload.assert_not_called()


def test_missing_cloudinary_credentials_returns_503(
    client: TestClient,
    seed_users_and_categories: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    cat_id = seed_users_and_categories["cat_plastic"].id
    monkeypatch.setattr(settings, "CLOUDINARY_CLOUD_NAME", "")
    monkeypatch.setattr(settings, "CLOUDINARY_API_KEY", "")
    monkeypatch.setattr(settings, "CLOUDINARY_API_SECRET", "")
    monkeypatch.setattr(settings, "CLOUDINARY_URL", "")

    res = client.post(
        "/api/reports",
        data={
            "title": "Missing cloudinary creds test",
            "description": "Uploading a valid image when Cloudinary credentials are unset.",
            "category_id": str(cat_id),
            "location_text": "Street 9",
        },
        files={"photo": ("waste.png", make_test_png_bytes(), "image/png")},
        headers=seed_users_and_categories["resident1_headers"],
    )
    assert res.status_code == 503


def test_create_report_validates_required_fields(client: TestClient, seed_users_and_categories: dict):
    cat_id = seed_users_and_categories["cat_plastic"].id

    res = client.post(
        "/api/reports",
        data={
            "title": "Hi",
            "description": "Short",
            "category_id": str(cat_id),
            "location_text": "",
        },
        headers=seed_users_and_categories["resident1_headers"],
    )
    assert res.status_code == 422
