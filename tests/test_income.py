import uuid

import pytest
from fastapi.testclient import TestClient

from app.database.models import BudgetSettings, MonthlyHours, AdditionalEarning


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
# GET /api/budget/income
# ---------------------------------------------------------------------------

def test_get_income_empty(authenticated_client: TestClient, test_db, test_user_a):
    """With no settings and no hours, returns 12 months with null hours and 0 gross/net."""
    resp = authenticated_client.get("/api/budget/income?year=2026")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["year"] == 2026
    assert len(data["months"]) == 12
    m1 = data["months"][0]
    assert m1["month"] == 1
    assert m1["rate_1_hours"] is None
    assert m1["gross"] == 0
    assert m1["net"] == 0
    assert m1["additional_earnings"] == []


def test_get_income_with_settings_defaults(authenticated_client: TestClient, test_db, test_user_a):
    """With settings but no hours entered, defaults to 160h per rate."""
    _seed_settings(test_db, test_user_a.calendar_id)
    resp = authenticated_client.get("/api/budget/income?year=2026")
    assert resp.status_code == 200
    m1 = resp.json()["data"]["months"][0]
    # gross = 100*160 + 80*160 + 60*160 = 38400
    assert m1["gross"] == 38400.0
    # net = (100*160)*0.88 + (80*160)*0.88 + (60*160)*0.88 - (1500+500) = 33792 - 2000 = 31792
    assert m1["net"] == 31792.0


# ---------------------------------------------------------------------------
# PUT /api/budget/income/hours
# ---------------------------------------------------------------------------

def test_save_hours(authenticated_client: TestClient, test_db, test_user_a):
    resp = authenticated_client.put("/api/budget/income/hours", json={
        "year": 2026, "month": 1, "rate_1_hours": 100, "rate_2_hours": None, "rate_3_hours": None
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["rate_1_hours"] == 100
    assert data["rate_2_hours"] is None
    assert data["rate_3_hours"] is None


def test_save_hours_updates_calculations(authenticated_client: TestClient, test_db, test_user_a):
    """Saving hours for month 1 affects only that month's calculations."""
    _seed_settings(test_db, test_user_a.calendar_id)
    authenticated_client.put("/api/budget/income/hours", json={
        "year": 2026, "month": 1, "rate_1_hours": 100, "rate_2_hours": None, "rate_3_hours": None
    })
    resp = authenticated_client.get("/api/budget/income?year=2026")
    m1 = resp.json()["data"]["months"][0]
    m2 = resp.json()["data"]["months"][1]
    # Month 1: gross = 100*100 + 80*160 + 60*160 = 10000 + 12800 + 9600 = 32400
    assert m1["gross"] == 32400.0
    # Month 2 still uses defaults
    assert m2["gross"] == 38400.0


def test_save_hours_null_values(authenticated_client: TestClient, test_db, test_user_a):
    """Saving all null hours persists nulls (defaults apply in calc)."""
    authenticated_client.put("/api/budget/income/hours", json={
        "year": 2026, "month": 1, "rate_1_hours": 100, "rate_2_hours": None, "rate_3_hours": None
    })
    # Now set back to null
    resp = authenticated_client.put("/api/budget/income/hours", json={
        "year": 2026, "month": 1, "rate_1_hours": None, "rate_2_hours": None, "rate_3_hours": None
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["rate_1_hours"] is None


def test_hours_validation_negative(authenticated_client: TestClient):
    resp = authenticated_client.put("/api/budget/income/hours", json={
        "year": 2026, "month": 1, "rate_1_hours": -10
    })
    assert resp.status_code == 422


def test_hours_validation_bad_month(authenticated_client: TestClient):
    resp = authenticated_client.put("/api/budget/income/hours", json={
        "year": 2026, "month": 0, "rate_1_hours": 100
    })
    assert resp.status_code == 422

    resp = authenticated_client.put("/api/budget/income/hours", json={
        "year": 2026, "month": 13, "rate_1_hours": 100
    })
    assert resp.status_code == 422


def test_hours_rounds_to_half(authenticated_client: TestClient, test_db, test_user_a):
    """Hours are rounded to nearest 0.5 step."""
    resp = authenticated_client.put("/api/budget/income/hours", json={
        "year": 2026, "month": 1, "rate_1_hours": 100.3
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["rate_1_hours"] == 100.5


# ---------------------------------------------------------------------------
# POST /api/budget/income/earnings
# ---------------------------------------------------------------------------

def test_add_earning(authenticated_client: TestClient, test_db, test_user_a):
    resp = authenticated_client.post("/api/budget/income/earnings", json={
        "year": 2026, "month": 3, "name": "Pensja partnerki", "amount": 3500.00
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "Pensja partnerki"
    assert data["amount"] == 3500.00
    assert data["month"] == 3


def test_add_earning_appears_in_income(authenticated_client: TestClient, test_db, test_user_a):
    authenticated_client.post("/api/budget/income/earnings", json={
        "year": 2026, "month": 3, "name": "500+", "amount": 800.00
    })
    resp = authenticated_client.get("/api/budget/income?year=2026")
    m3 = resp.json()["data"]["months"][2]
    assert len(m3["additional_earnings"]) == 1
    assert m3["additional_earnings"][0]["name"] == "500+"
    assert m3["additional_earnings"][0]["amount"] == 800.00


# ---------------------------------------------------------------------------
# DELETE /api/budget/income/earnings/{id}
# ---------------------------------------------------------------------------

def test_delete_earning(authenticated_client: TestClient, test_db, test_user_a):
    # Create
    resp = authenticated_client.post("/api/budget/income/earnings", json={
        "year": 2026, "month": 5, "name": "Bonus", "amount": 1000.00
    })
    earning_id = resp.json()["data"]["id"]
    # Delete
    resp = authenticated_client.delete(f"/api/budget/income/earnings/{earning_id}")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    # Verify gone
    resp = authenticated_client.get("/api/budget/income?year=2026")
    m5 = resp.json()["data"]["months"][4]
    assert len(m5["additional_earnings"]) == 0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_earning_validation_empty_name(authenticated_client: TestClient):
    resp = authenticated_client.post("/api/budget/income/earnings", json={
        "year": 2026, "month": 1, "name": "", "amount": 100
    })
    assert resp.status_code == 422


def test_earning_validation_negative_amount(authenticated_client: TestClient):
    resp = authenticated_client.post("/api/budget/income/earnings", json={
        "year": 2026, "month": 1, "name": "Test", "amount": -100
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def test_income_page_renders(authenticated_client: TestClient):
    resp = authenticated_client.get("/budget/income")
    assert resp.status_code == 200
    assert "budget/income" in resp.text or "api/budget/income" in resp.text


def test_income_page_unauthenticated(test_client: TestClient):
    resp = test_client.get("/budget/income", follow_redirects=False)
    assert resp.status_code in (302, 303, 401, 403)


def test_settings_sidebar_links_to_income(authenticated_client: TestClient):
    resp = authenticated_client.get("/budget/settings")
    assert resp.status_code == 200
    assert 'href="/budget/income"' in resp.text


# ---------------------------------------------------------------------------
# Recurring (stable) earnings — month=0
# ---------------------------------------------------------------------------

def test_add_recurring_earning(authenticated_client: TestClient, test_db, test_user_a):
    """month=0 creates a recurring earning."""
    resp = authenticated_client.post("/api/budget/income/earnings", json={
        "year": 2026, "month": 0, "name": "Vale", "amount": 300.00
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "Vale"
    assert data["month"] == 0


def test_recurring_earning_appears_in_all_months(authenticated_client: TestClient, test_db, test_user_a):
    """Recurring earnings show in every month's recurring_earnings list."""
    authenticated_client.post("/api/budget/income/earnings", json={
        "year": 2026, "month": 0, "name": "Pensja partnerki", "amount": 4000.00
    })
    resp = authenticated_client.get("/api/budget/income?year=2026")
    data = resp.json()["data"]
    # Should appear in top-level recurring_earnings
    assert len(data["recurring_earnings"]) == 1
    assert data["recurring_earnings"][0]["name"] == "Pensja partnerki"
    # Should appear in each month's recurring_earnings
    for m in data["months"]:
        assert len(m["recurring_earnings"]) == 1
        assert m["recurring_earnings"][0]["name"] == "Pensja partnerki"
    # Should NOT appear in per-month additional_earnings
    for m in data["months"]:
        assert len(m["additional_earnings"]) == 0


def test_recurring_earning_does_not_mix_with_monthly(authenticated_client: TestClient, test_db, test_user_a):
    """Recurring (month=0) and per-month earnings stay separate."""
    authenticated_client.post("/api/budget/income/earnings", json={
        "year": 2026, "month": 0, "name": "Vale", "amount": 300.00
    })
    authenticated_client.post("/api/budget/income/earnings", json={
        "year": 2026, "month": 3, "name": "Bonus", "amount": 1000.00
    })
    resp = authenticated_client.get("/api/budget/income?year=2026")
    data = resp.json()["data"]
    assert len(data["recurring_earnings"]) == 1
    m3 = data["months"][2]
    assert len(m3["additional_earnings"]) == 1
    assert m3["additional_earnings"][0]["name"] == "Bonus"
    assert len(m3["recurring_earnings"]) == 1
    assert m3["recurring_earnings"][0]["name"] == "Vale"


def test_delete_recurring_earning(authenticated_client: TestClient, test_db, test_user_a):
    resp = authenticated_client.post("/api/budget/income/earnings", json={
        "year": 2026, "month": 0, "name": "Vale", "amount": 300.00
    })
    earning_id = resp.json()["data"]["id"]
    resp = authenticated_client.delete(f"/api/budget/income/earnings/{earning_id}")
    assert resp.status_code == 200
    resp = authenticated_client.get("/api/budget/income?year=2026")
    assert len(resp.json()["data"]["recurring_earnings"]) == 0
