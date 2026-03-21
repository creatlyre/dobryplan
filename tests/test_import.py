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
