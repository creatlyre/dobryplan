import uuid

import pytest
from fastapi.testclient import TestClient

from app.database.models import BudgetSettings


def _seed_settings(test_db, calendar_id, rate_1=100, rate_2=80, rate_3=60, zus=1500, acc=500):
    settings = BudgetSettings(
        id=str(uuid.uuid4()),
        calendar_id=calendar_id,
        rate_1=rate_1,
        rate_2=rate_2,
        rate_3=rate_3,
        zus_costs=zus,
        accounting_costs=acc,
        initial_balance=10000,
    )
    test_db.add(settings)
    return settings


# ---------------------------------------------------------------------------
# POST /api/budget/income/hours/bulk
# ---------------------------------------------------------------------------

def test_bulk_hours_import_success(authenticated_client: TestClient, test_db, test_user_a):
    """Bulk import 3 months of hours returns 200 with 3 entries."""
    payload = {
        "year": 2024,
        "entries": [
            {"year": 2024, "month": 4, "rate_1_hours": 160, "rate_2_hours": 140, "rate_3_hours": 120},
            {"year": 2024, "month": 5, "rate_1_hours": 150, "rate_2_hours": None, "rate_3_hours": None},
            {"year": 2024, "month": 6, "rate_1_hours": 170, "rate_2_hours": 168, "rate_3_hours": 0},
        ],
    }
    resp = authenticated_client.post("/api/budget/income/hours/bulk", json=payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 3
    assert data[0]["month"] == 4
    assert data[0]["rate_1_hours"] == 160
    assert data[1]["month"] == 5
    assert data[1]["rate_1_hours"] == 150
    assert data[2]["month"] == 6
    assert data[2]["rate_2_hours"] == 168


def test_bulk_hours_import_upsert(authenticated_client: TestClient, test_db, test_user_a):
    """Second import for same month updates, not duplicates."""
    payload1 = {
        "year": 2024,
        "entries": [
            {"year": 2024, "month": 1, "rate_1_hours": 100, "rate_2_hours": 80, "rate_3_hours": 60},
        ],
    }
    resp1 = authenticated_client.post("/api/budget/income/hours/bulk", json=payload1)
    assert resp1.status_code == 200

    payload2 = {
        "year": 2024,
        "entries": [
            {"year": 2024, "month": 1, "rate_1_hours": 200, "rate_2_hours": 160, "rate_3_hours": 120},
        ],
    }
    resp2 = authenticated_client.post("/api/budget/income/hours/bulk", json=payload2)
    assert resp2.status_code == 200
    data = resp2.json()["data"]
    assert len(data) == 1
    assert data[0]["rate_1_hours"] == 200

    # Verify via GET that there's only one entry for month 1
    resp3 = authenticated_client.get("/api/budget/income?year=2024")
    assert resp3.status_code == 200
    months = resp3.json()["data"]["months"]
    jan = months[0]  # month 1
    assert jan["rate_1_hours"] == 200


def test_bulk_hours_import_empty(authenticated_client: TestClient, test_db, test_user_a):
    """Empty entries list returns 200 with empty data."""
    payload = {"year": 2024, "entries": []}
    resp = authenticated_client.post("/api/budget/income/hours/bulk", json=payload)
    assert resp.status_code == 200
    assert resp.json()["data"] == []


# ---------------------------------------------------------------------------
# Integration: Import → YoY Comparison (IMP-04)
# ---------------------------------------------------------------------------

def test_import_feeds_yoy_comparison(authenticated_client: TestClient, test_db, test_user_a):
    """IMP-04: Imported data appears in year-over-year comparison."""
    # 1. Create budget settings
    _seed_settings(test_db, test_user_a.calendar_id)

    # 2. Import hours for year 2024 (previous year)
    hours_2024 = {
        "year": 2024,
        "entries": [
            {"year": 2024, "month": m, "rate_1_hours": 160, "rate_2_hours": 160, "rate_3_hours": 0}
            for m in range(1, 13)
        ],
    }
    res = authenticated_client.post("/api/budget/income/hours/bulk", json=hours_2024)
    assert res.status_code == 200

    # 3. Import hours for year 2025 (selected year) with different hours
    hours_2025 = {
        "year": 2025,
        "entries": [
            {"year": 2025, "month": m, "rate_1_hours": 160, "rate_2_hours": 168, "rate_3_hours": 0}
            for m in range(1, 13)
        ],
    }
    res = authenticated_client.post("/api/budget/income/hours/bulk", json=hours_2025)
    assert res.status_code == 200

    # 4. Verify YoY comparison for 2025 shows both years
    res = authenticated_client.get("/api/budget/overview/comparison?year=2025")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["selected_year"] == 2025
    assert data["previous_year"] == 2024
    assert data["selected"]["total_net"] > 0, "Selected year should have income"
    assert data["previous"]["total_net"] > 0, "Previous year should have income"
    assert data["delta"]["total_net"] != 0, "Delta should be non-zero (different hours)"


def test_imported_expenses_in_yoy(authenticated_client: TestClient, test_db, test_user_a):
    """Imported one-time expenses appear in YoY totals."""
    _seed_settings(test_db, test_user_a.calendar_id, rate_1=100, rate_2=80, rate_3=60, zus=1500, acc=500)

    # Import one-time expenses for 2024
    res = authenticated_client.post("/api/budget/expenses/bulk", json={
        "expenses": [
            {"year": 2024, "month": 3, "name": "Laptop", "amount": 3500.0, "recurring": False},
            {"year": 2024, "month": 7, "name": "Vacation", "amount": 2000.0, "recurring": False},
        ]
    })
    assert res.status_code == 200

    # Verify in overview
    res = authenticated_client.get("/api/budget/overview?year=2024")
    assert res.status_code == 200
    months = res.json()["data"]["months"]
    assert months[2]["onetime_expenses"] == 3500.0  # March (index 2)
    assert months[6]["onetime_expenses"] == 2000.0  # July (index 6)
