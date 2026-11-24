import io
from pathlib import Path
from unittest.mock import MagicMock
import boto3
import cloudinary.api
import cloudinary.uploader
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.models import SystemSetting


def make_test_png_bytes() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (32, 32), color=(16, 185, 129))
    img.save(buf, format="PNG")
    return buf.getvalue()


def _base_settings_payload(provider: str = "cloudinary", cld_secret: str | None = "super-secret-key-9876"):
    return {
        "general": {
            "site_name": "EcoWatch City",
            "allow_registration": True,
        },
        "storage": {
            "provider": provider,
            "max_file_size_mb": 8,
            "allowed_extensions": ["png", "jpg", "webp"],
            "cloudinary": {
                "cloud_name": "city-cloud",
                "api_key": "cld-api-key-123",
                "api_secret": cld_secret,
                "folder": "city_waste",
            },
            "s3": {
                "endpoint_url": "https://storage.sabay.local",
                "region": "ap-southeast-1",
                "bucket": "waste-bucket",
                "access_key_id": "s3-access-key",
                "secret_access_key": "s3-super-secret-4321",
                "public_base_url": "https://cdn.sabay.local",
                "folder": "reports",
            },
        },
    }


def test_settings_endpoints_enforce_admin_rbac(
    client: TestClient, seed_users_and_categories: dict
):
    res_headers = seed_users_and_categories["resident1_headers"]

    assert client.get("/api/admin/settings", headers=res_headers).status_code == 403
    assert (
        client.put("/api/admin/settings", json=_base_settings_payload(), headers=res_headers).status_code
        == 403
    )
    assert client.post("/api/admin/settings/storage/test", headers=res_headers).status_code == 403


def test_resident_upload_policy_reflects_admin_settings(
    client: TestClient, seed_users_and_categories: dict
):
    path = "/api/reports/upload-policy"
    assert client.get(path).status_code == 401

    payload = _base_settings_payload()
    payload["storage"]["max_file_size_mb"] = 7
    payload["storage"]["allowed_extensions"] = ["webp"]
    saved = client.put(
        "/api/admin/settings", json=payload, headers=seed_users_and_categories["admin_headers"]
    )
    assert saved.status_code == 200

    policy = client.get(path, headers=seed_users_and_categories["resident1_headers"])
    assert policy.status_code == 200
    assert policy.json() == {"max_file_size_mb": 7, "allowed_extensions": ["webp"]}


def test_admin_settings_encrypts_and_preserves_secrets(
    client: TestClient, test_db: Session, seed_users_and_categories: dict
):
    admin_headers = seed_users_and_categories["admin_headers"]

    # Save settings with plaintext secrets
    put_res = client.put(
        "/api/admin/settings",
        json=_base_settings_payload("cloudinary", "super-secret-key-9876"),
        headers=admin_headers,
    )
    assert put_res.status_code == 200
    body = put_res.json()
    assert body["general"]["site_name"] == "EcoWatch City"
    assert body["storage"]["provider"] == "cloudinary"
    assert body["storage"]["max_file_size_mb"] == 8
    # Secret must be masked in API response
    assert body["storage"]["cloudinary"]["has_api_secret"] is True
    assert body["storage"]["cloudinary"]["api_secret_masked"] == "••••••••9876"
    assert "super-secret-key-9876" not in str(body)

    # Verify stored value in DB is encrypted (not plaintext)
    db_row = test_db.get(SystemSetting, "cloudinary.api_secret")
    assert db_row is not None
    assert db_row.is_secret is True
    assert db_row.value is not None
    assert db_row.value != "super-secret-key-9876"
    assert "9876" not in db_row.value

    # Updating unrelated setting with blank api_secret preserves existing encrypted secret
    updated_payload = _base_settings_payload("cloudinary", "")
    updated_payload["storage"]["cloudinary"]["folder"] = "updated_folder"
    put_res2 = client.put("/api/admin/settings", json=updated_payload, headers=admin_headers)
    assert put_res2.status_code == 200
    assert put_res2.json()["storage"]["cloudinary"]["folder"] == "updated_folder"
    assert put_res2.json()["storage"]["cloudinary"]["api_secret_masked"] == "••••••••9876"


def test_dynamic_storage_provider_switching_runtime(
    client: TestClient,
    seed_users_and_categories: dict,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    admin_headers = seed_users_and_categories["admin_headers"]
    res_headers = seed_users_and_categories["resident1_headers"]
    cat_id = seed_users_and_categories["cat_plastic"].id

    # 1. Switch to S3-Compatible (e.g. Sabay Cloud / R2 / AWS S3) via Admin Settings
    save_s3 = client.put(
        "/api/admin/settings",
        json=_base_settings_payload("s3_compatible"),
        headers=admin_headers,
    )
    assert save_s3.status_code == 200

    mock_s3_client = MagicMock()
    monkeypatch.setattr(boto3, "client", MagicMock(return_value=mock_s3_client))

    upload_s3 = client.post(
        "/api/reports",
        data={
            "title": "S3 provider runtime test",
            "description": "Verifying dynamic S3-compatible provider upload from Admin Settings.",
            "category_id": str(cat_id),
            "location_text": "Street 200",
        },
        files={"photo": ("waste.png", make_test_png_bytes(), "image/png")},
        headers=res_headers,
    )
    assert upload_s3.status_code == 201
    assert upload_s3.json()["photo_path"].startswith("https://cdn.sabay.local/reports/")
    mock_s3_client.put_object.assert_called_once()

    # Test S3 connection endpoint
    test_s3 = client.post("/api/admin/settings/storage/test", headers=admin_headers)
    assert test_s3.status_code == 200
    assert test_s3.json()["ok"] is True
    mock_s3_client.head_bucket.assert_called_once_with(Bucket="waste-bucket")

    # 2. Switch dynamically to Local Disk storage via Admin Settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path / "local_uploads")
    save_local = client.put(
        "/api/admin/settings",
        json=_base_settings_payload("local"),
        headers=admin_headers,
    )
    assert save_local.status_code == 200

    upload_local = client.post(
        "/api/reports",
        data={
            "title": "Local provider runtime test",
            "description": "Verifying dynamic switch to local storage without server restart.",
            "category_id": str(cat_id),
            "location_text": "Street 201",
        },
        files={"photo": ("waste.png", make_test_png_bytes(), "image/png")},
        headers=res_headers,
    )
    assert upload_local.status_code == 201
    assert upload_local.json()["photo_path"].startswith("/uploads/")


def test_cloudinary_connection_test_endpoint(
    client: TestClient,
    seed_users_and_categories: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    admin_headers = seed_users_and_categories["admin_headers"]
    monkeypatch.setattr(cloudinary.api, "ping", MagicMock(return_value={"status": "ok"}))

    res = client.post(
        "/api/admin/settings/storage/test",
        json=_base_settings_payload("cloudinary"),
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert res.json()["provider"] == "cloudinary"


def test_admin_can_disable_public_registration(
    client: TestClient, seed_users_and_categories: dict
):
    admin_headers = seed_users_and_categories["admin_headers"]
    payload = _base_settings_payload("cloudinary")
    payload["general"]["allow_registration"] = False

    assert client.put("/api/admin/settings", json=payload, headers=admin_headers).status_code == 200

    reg_res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Blocked User",
            "email": "blocked@example.com",
            "password": "Password123",
        },
    )
    assert reg_res.status_code == 403


def test_sabay_s3_endpoint_normalization_and_404_diagnostics(
    client: TestClient,
    seed_users_and_categories: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    from botocore.exceptions import ClientError

    admin_headers = seed_users_and_categories["admin_headers"]

    # 1. Accidentally entering Sabay GraphQL URL returns clear guidance
    bad_payload = _base_settings_payload("s3_compatible")
    bad_payload["storage"]["s3"]["endpoint_url"] = "https://cloudgateway.sabay.com/graphql"
    res_graphql = client.post(
        "/api/admin/settings/storage/test", json=bad_payload, headers=admin_headers
    )
    assert res_graphql.status_code == 200
    assert res_graphql.json()["ok"] is False
    assert "GraphQL" in res_graphql.json()["message"]

    # 2. Pasting full Sabay bucket URL (https://fsgw.sabay.com/waste-bucket) auto-strips /waste-bucket
    full_url_payload = _base_settings_payload("s3_compatible")
    full_url_payload["storage"]["s3"]["endpoint_url"] = "https://fsgw.sabay.com/waste-bucket"
    full_url_payload["storage"]["s3"]["bucket"] = "waste-bucket"
    mock_client = MagicMock()
    mock_boto = MagicMock(return_value=mock_client)
    monkeypatch.setattr(boto3, "client", mock_boto)

    res_ok = client.post(
        "/api/admin/settings/storage/test", json=full_url_payload, headers=admin_headers
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["ok"] is True
    assert mock_boto.call_args.kwargs["endpoint_url"] == "https://fsgw.sabay.com"

    # 3. 404 HeadBucket lists available buckets if credentials work
    mock_client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
        "HeadBucket",
    )
    mock_client.list_buckets.return_value = {"Buckets": [{"Name": "bucket03"}]}
    res_404 = client.post(
        "/api/admin/settings/storage/test", json=full_url_payload, headers=admin_headers
    )
    assert res_404.status_code == 200
    assert res_404.json()["ok"] is False
    assert "bucket03" in res_404.json()["message"]
