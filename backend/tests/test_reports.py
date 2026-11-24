import io
from pathlib import Path
from random import Random
from unittest.mock import MagicMock
import cloudinary.uploader
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.config import normalize_database_url, settings
from app.database import build_engine
from app.models import WasteReport
from app.services.storage.local_provider import LocalStorageProvider


def make_test_png_bytes() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (64, 64), color=(34, 197, 94))
    img.save(buf, format="PNG")
    return buf.getvalue()


def report_form(category_id: int) -> dict[str, str]:
    return {
        "title": "Waste beside the intersection",
        "description": "Several bags of waste beside the pedestrian crossing.",
        "category_id": str(category_id),
        "location_text": "Intersection near Central Market",
    }


def test_multiple_photos_include_avif_and_preserve_the_cover(
    client: TestClient, test_db: Session, seed_users_and_categories: dict,
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(settings, "ALLOWED_EXTENSIONS", {"png", "avif"})
    resident = seed_users_and_categories["resident1_headers"]
    category_id = seed_users_and_categories["cat_plastic"].id
    avif = io.BytesIO()
    Image.new("RGB", (12, 12), (20, 110, 40)).save(avif, format="AVIF")
    png = make_test_png_bytes()

    response = client.post(
        "/api/reports", data=report_form(category_id), headers=resident,
        files=[("photos", ("cover.avif", avif.getvalue(), "image/avif")), ("photos", ("details.png", png, "image/png"))],
    )
    assert response.status_code == 201
    report = response.json()
    cover, detail = report["photo_paths"]
    assert report["photo_path"] == cover
    assert cover.endswith(".avif") and detail.endswith(".png")
    assert (tmp_path / Path(cover).name).read_bytes() == avif.getvalue()
    assert (tmp_path / Path(detail).name).read_bytes() == png
    assert client.get(f"/api/reports/{report['id']}", headers=resident).json()["photo_paths"] == [cover, detail]
    assert client.get("/api/reports/my", headers=resident).json()[0]["photo_path"] == cover

    legacy = WasteReport(
        user_id=seed_users_and_categories["resident1"].id, category_id=category_id,
        title="Older report", description="A report created before galleries.", location_text="A street",
        photo_path="/uploads/legacy.png",
    )
    test_db.add(legacy)
    test_db.commit()
    assert client.get(f"/api/reports/{legacy.id}", headers=resident).json()["photo_paths"] == ["/uploads/legacy.png"]


def test_batch_validation_and_failed_storage_leave_no_report_or_files(
    client: TestClient, seed_users_and_categories: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    uploads = tmp_path / "images"
    uploads.mkdir()
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "UPLOAD_DIR", uploads)
    resident = seed_users_and_categories["resident1_headers"]
    data = report_form(seed_users_and_categories["cat_plastic"].id)
    png = make_test_png_bytes()
    valid = ("photos", ("photo.png", png, "image/png"))
    for files in ([valid] * 6, [valid, ("photos", ("broken.avif", b"bad image", "image/avif"))]):
        assert client.post("/api/reports", data=data, files=files, headers=resident).status_code == 400
        assert not list(uploads.iterdir())

    save_image = LocalStorageProvider.upload
    attempts = 0

    def fail_second_upload(provider, contents, public_id, extension, content_type):
        nonlocal attempts
        attempts += 1
        path = save_image(provider, contents, public_id, extension, content_type)
        if attempts == 2:
            raise OSError("Storage failed after writing")
        return path

    monkeypatch.setattr(LocalStorageProvider, "upload", fail_second_upload)
    with pytest.raises(OSError, match="Storage failed"):
        client.post("/api/reports", data=data, files=[valid, valid], headers=resident)
    assert attempts == 2
    assert not list(uploads.iterdir())
    assert client.get("/api/reports/my", headers=resident).json() == []


def test_vercel_policy_applies_a_combined_photo_limit(
    client: TestClient, seed_users_and_categories: dict, monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(settings, "MAX_FILE_SIZE", 5 * 1024 * 1024)
    resident = seed_users_and_categories["resident1_headers"]
    size = client.get("/api/reports/upload-policy", headers=resident).json()
    assert size["max_file_size_mb"] == size["max_total_size_mb"] == 4

    buffer = io.BytesIO()
    Image.frombytes("RGB", (900, 900), Random(42).randbytes(900 * 900 * 3)).save(buffer, format="PNG")
    photo = ("photos", ("photo.png", buffer.getvalue(), "image/png"))
    response = client.post(
        "/api/reports", data=report_form(seed_users_and_categories["cat_plastic"].id),
        files=[photo, photo], headers=resident,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "All photos together must be 4 MB or smaller."


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
