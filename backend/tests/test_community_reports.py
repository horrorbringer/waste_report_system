from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.database import ensure_schema_columns
from app.models import WasteReport


def test_existing_reports_migrate_as_private():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE waste_reports (id INTEGER PRIMARY KEY)"))
        conn.execute(text("INSERT INTO waste_reports (id) VALUES (1)"))

    ensure_schema_columns(engine)
    ensure_schema_columns(engine)

    with engine.connect() as conn:
        entry = conn.execute(text("SELECT id, public_province, public_district, location_district FROM waste_reports")).one()
        assert entry == (1, None, None, None)
    engine.dispose()


def test_admin_publication_controls_only_the_redacted_feed(
    client: TestClient, test_db: Session, seed_users_and_categories: dict
):
    resident = seed_users_and_categories["resident1_headers"]
    other_resident = seed_users_and_categories["resident2_headers"]
    admin = seed_users_and_categories["admin_headers"]
    category_id = seed_users_and_categories["cat_plastic"].id
    created = client.post(
        "/api/reports",
        headers=resident,
        data={
            "title": "Waste at a private address",
            "description": "This description stays with the private report.",
            "category_id": category_id,
            "location_text": "Exact street address 123",
            "latitude": 11.54892,
            "longitude": 104.91130,
            "location_district": 1213,
        },
    )
    assert created.status_code == 201
    assert created.json()["public_district"] is None
    assert created.json()["location_district"] == 1213
    report_id = created.json()["id"]
    report_path = f"/api/reports/{report_id}"
    publication = f"{report_path}/publication"
    community = "/api/reports/community"

    assert client.get(community).json() == {"items": [], "has_more": False}
    assert client.put(publication, json={"district": 1213}).status_code == 401
    assert client.put(publication, headers=resident, json={"district": 1213}).status_code == 403
    assert client.put(publication, headers=admin, json={"district": "Exact street address"}).status_code == 422
    assert client.put(publication, headers=admin, json={}).status_code == 422
    assert client.put("/api/reports/999/publication", headers=admin, json={"district": 1213}).status_code == 404

    report = test_db.get(WasteReport, report_id)
    assert report is not None
    report.created_at = datetime(2026, 11, 23, 18, 30, tzinfo=timezone.utc)
    report.photo_path = "https://example.com/private-report-photo.png"
    test_db.commit()

    approved = client.put(publication, headers=admin, json={"district": 1213})
    assert approved.status_code == 200
    assert approved.json() == {"province": 12, "district": 1213}
    assert client.get(report_path, headers=resident).json()["public_district"] == 1213

    expected_entry = {
        "category_name": "Plastic Waste",
        "category_name_km": None,
        "province": 12,
        "province_name": "Phnom Penh Capital",
        "province_name_km": "រាជធានីភ្នំពេញ",
        "district": 1213,
        "district_name": "Boeng Keng Kang Khan",
        "district_name_km": "ខណ្ឌបឹងកេងកង",
        "reported_on": "2026-11-24",
        "status": "Pending",
    }
    feed = client.get(community)
    assert feed.status_code == 200
    assert feed.headers["cache-control"] == "no-store"
    assert feed.json() == {"items": [expected_entry], "has_more": False}
    assert client.get(report_path).status_code == 401
    assert client.get(report_path, headers=other_resident).status_code == 403

    updated = client.patch(
        f"{report_path}/status", headers=admin, json={"status": "Resolved", "note": "Private cleanup note"}
    )
    assert updated.status_code == 200
    assert client.get(community).json()["items"] == [{**expected_entry, "status": "Resolved"}]

    for _ in range(2):
        unpublished = client.put(publication, headers=admin, json={"district": None})
        assert unpublished.status_code == 200
    assert client.get(community).json() == {"items": [], "has_more": False}
    assert client.get(report_path, headers=resident).status_code == 200


def test_national_publication_accepts_province_only_and_checks_district_membership(
    client: TestClient, seed_users_and_categories: dict,
):
    resident = seed_users_and_categories["resident1_headers"]
    admin = seed_users_and_categories["admin_headers"]
    catalog = client.get("/api/reports/areas").json()
    assert {area["code"] for area in catalog} == set(range(1, 26))
    assert any(district["code"] == 1710 for district in next(area for area in catalog if area["code"] == 17)["districts"])

    created = client.post(
        "/api/reports", headers=resident, data={
            "title": "Waste in Siem Reap", "description": "Trash bags next to a crossing.",
            "category_id": seed_users_and_categories["cat_plastic"].id,
            "location_text": "Private address in Siem Reap", "location_district": 1710,
        },
    )
    assert created.status_code == 201
    report_path = f"/api/reports/{created.json()['id']}"
    publication = report_path + "/publication"
    assert created.json()["location_district"] == 1710
    assert created.json()["public_province"] is None
    assert client.put(publication, headers=admin, json={"province": 12, "district": 1710}).status_code == 422
    assert client.put(publication, headers=admin, json={"province": 99, "district": None}).status_code == 422
    assert client.get("/api/reports/community").json()["items"] == []

    approved = client.put(publication, headers=admin, json={"province": 17, "district": None})
    assert approved.json() == {"province": 17, "district": None}
    assert client.get(report_path, headers=resident).json()["public_province"] == 17
    entry = client.get("/api/reports/community").json()["items"][0]
    datetime.fromisoformat(entry.pop("reported_on"))
    assert entry == {
        "category_name": "Plastic Waste", "category_name_km": None,
        "province": 17, "province_name": "Siemreap Province", "province_name_km": "ខេត្តសៀមរាប",
        "district": None, "district_name": None, "district_name_km": None,
        "status": "Pending",
    }

    updated = client.put(publication, headers=admin, json={"province": 17, "district": 1710})
    assert updated.json() == {"province": 17, "district": 1710}
    entry = client.get("/api/reports/community").json()["items"][0]
    assert entry["district_name"] == "Siem Reap Municipality"
    assert set(entry) == {
        "category_name", "category_name_km", "province", "province_name", "province_name_km",
        "district", "district_name", "district_name_km", "reported_on", "status",
    }
    client.put(publication, headers=admin, json={"province": None, "district": None})
    assert client.get("/api/reports/community").json()["items"] == []


def test_community_feed_pages_approved_reports_only(
    client: TestClient, test_db: Session, seed_users_and_categories: dict
):
    resident_id = seed_users_and_categories["resident1"].id
    category_id = seed_users_and_categories["cat_plastic"].id
    for day, district in [(21, 1202), (22, 1213), (23, None)]:
        test_db.add(WasteReport(
            user_id=resident_id,
            category_id=category_id,
            title="Waste report",
            description="Private description",
            location_text="Private address",
            public_district=district,
            created_at=datetime(2026, 11, day, 12, tzinfo=timezone.utc),
        ))
    test_db.commit()

    first_page = client.get("/api/reports/community", params={"limit": 1}).json()
    second_page = client.get("/api/reports/community", params={"limit": 1, "offset": 1}).json()
    assert first_page["has_more"] is True
    assert [item["district"] for item in first_page["items"]] == [1213]
    assert first_page["items"][0]["province"] == 12
    assert second_page["has_more"] is False
    assert [item["district"] for item in second_page["items"]] == [1202]
