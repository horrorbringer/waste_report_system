from fastapi.testclient import TestClient


def test_resident_cannot_access_admin_endpoints(client: TestClient, seed_users_and_categories: dict):
    headers = seed_users_and_categories["resident1_headers"]

    # Admin dashboard stats
    assert client.get("/api/admin/stats", headers=headers).status_code == 403
    # Admin all reports list
    assert client.get("/api/reports", headers=headers).status_code == 403
    # Admin create category
    assert (
        client.post(
            "/api/categories",
            json={"name": "Unauthorized Category"},
            headers=headers,
        ).status_code
        == 403
    )


def test_resident_cannot_view_other_residents_report(
    client: TestClient, seed_users_and_categories: dict
):
    cat_id = seed_users_and_categories["cat_plastic"].id

    # Resident 1 creates a report
    create_res = client.post(
        "/api/reports",
        data={
            "title": "Plastic pile on Street 10",
            "description": "Large amount of discarded plastic bottles near corner store.",
            "category_id": str(cat_id),
            "location_text": "Street 10, Block A",
        },
        headers=seed_users_and_categories["resident1_headers"],
    )
    assert create_res.status_code == 201
    report_id = create_res.json()["id"]

    # Resident 1 can view own report
    assert (
        client.get(
            f"/api/reports/{report_id}",
            headers=seed_users_and_categories["resident1_headers"],
        ).status_code
        == 200
    )

    # Resident 2 CANNOT view Resident 1's report
    assert (
        client.get(
            f"/api/reports/{report_id}",
            headers=seed_users_and_categories["resident2_headers"],
        ).status_code
        == 403
    )

    # Resident 1 CANNOT update status
    assert (
        client.patch(
            f"/api/reports/{report_id}/status",
            json={"status": "Resolved", "note": "Trying to bypass RBAC"},
            headers=seed_users_and_categories["resident1_headers"],
        ).status_code
        == 403
    )

    # Admin CAN view Resident 1's report
    assert (
        client.get(
            f"/api/reports/{report_id}",
            headers=seed_users_and_categories["admin_headers"],
        ).status_code
        == 200
    )
