from fastapi.testclient import TestClient


def test_admin_status_update_and_dashboard_stats(
    client: TestClient, seed_users_and_categories: dict
):
    cat_id = seed_users_and_categories["cat_plastic"].id
    admin_headers = seed_users_and_categories["admin_headers"]
    res1_headers = seed_users_and_categories["resident1_headers"]

    # Resident submits a report
    create = client.post(
        "/api/reports",
        data={
            "title": "Overflowing dumpster on Main St",
            "description": "Dumpster has not been collected since Monday and waste is spilling.",
            "category_id": str(cat_id),
            "location_text": "Main St 45",
        },
        headers=res1_headers,
    )
    assert create.status_code == 201
    report_id = create.json()["id"]

    # Admin updates status Pending -> In Progress
    upd1 = client.patch(
        f"/api/reports/{report_id}/status",
        json={"status": "In Progress", "note": "Cleanup truck dispatched."},
        headers=admin_headers,
    )
    assert upd1.status_code == 200
    assert upd1.json()["status"] == "In Progress"
    assert len(upd1.json()["status_history"]) == 2
    assert upd1.json()["status_history"][0]["old_status"] == "Pending"
    assert upd1.json()["status_history"][0]["new_status"] == "In Progress"
    assert upd1.json()["status_history"][0]["note"] == "Cleanup truck dispatched."

    # Admin updates status In Progress -> Resolved
    upd2 = client.patch(
        f"/api/reports/{report_id}/status",
        json={"status": "Resolved", "note": "Area cleaned and sanitized."},
        headers=admin_headers,
    )
    assert upd2.status_code == 200
    assert upd2.json()["status"] == "Resolved"
    assert len(upd2.json()["status_history"]) == 3

    # Admin dashboard counts match database
    stats = client.get("/api/admin/stats", headers=admin_headers)
    assert stats.status_code == 200
    data = stats.json()
    assert data["total_reports"] == 1
    assert data["resolved_count"] == 1
    assert data["pending_count"] == 0
    assert data["in_progress_count"] == 0


def test_admin_category_management(client: TestClient, seed_users_and_categories: dict):
    admin_headers = seed_users_and_categories["admin_headers"]

    # Create new bilingual category (EN + KM)
    create = client.post(
        "/api/categories",
        json={
            "name": "Bulk Furniture",
            "name_km": "គ្រឿងសង្ហារិមធំៗ",
            "description": "Old mattresses and broken chairs",
            "description_km": "ពូកចាស់ៗ និងកៅអីខូច",
        },
        headers=admin_headers,
    )
    assert create.status_code == 201
    assert create.json()["name_km"] == "គ្រឿងសង្ហារិមធំៗ"
    cat_id = create.json()["id"]

    # Update category (bilingual)
    update = client.put(
        f"/api/categories/{cat_id}",
        json={
            "name": "Bulky Waste",
            "name_km": "សំណល់ខ្នាតធំ",
            "description": "Large household furniture items",
            "description_km": "សម្ភារៈគ្រឿងសង្ហារិមក្នុងផ្ទះខ្នាតធំ",
        },
        headers=admin_headers,
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Bulky Waste"
    assert update.json()["name_km"] == "សំណល់ខ្នាតធំ"

    # Delete unused category
    delete = client.delete(f"/api/categories/{cat_id}", headers=admin_headers)
    assert delete.status_code == 204
