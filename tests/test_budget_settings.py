"""Integration tests for budget settings API and views."""
import uuid
from datetime import datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import Calendar, User
from config import Settings
from main import app


# ── API Tests ──────────────────────────────────────────────


def test_get_budget_settings_empty(authenticated_client):
    """GET /api/budget/settings when no settings exist returns null data."""
    response = authenticated_client.get("/api/budget/settings")
    assert response.status_code == 200
    assert response.json()["data"] is None


def test_get_budget_settings_existing(authenticated_client, test_db, test_user_a):
    """GET /api/budget/settings when settings exist returns saved values."""
    test_db.insert("budget_settings", {
        "id": str(uuid.uuid4()),
        "calendar_id": test_user_a.calendar_id,
        "rate_1": 150.0,
        "rate_2": 200.0,
        "rate_3": 250.0,
        "monthly_costs": 1800.0,
        "initial_balance": 50000.0,
    })

    response = authenticated_client.get("/api/budget/settings")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data is not None
    assert data["rate_1"] == 150.0
    assert data["rate_2"] == 200.0
    assert data["rate_3"] == 250.0
    assert data["monthly_costs"] == 1800.0
    assert data["initial_balance"] == 50000.0


def test_save_budget_settings_create(authenticated_client):
    """PUT /api/budget/settings creates new settings when none exist."""
    payload = {
        "rate_1": 150.0,
        "rate_2": 200.0,
        "rate_3": 250.0,
        "monthly_costs": 1800.0,
        "initial_balance": 50000.0,
    }
    response = authenticated_client.put("/api/budget/settings", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["rate_1"] == 150.0
    assert data["rate_2"] == 200.0
    assert data["rate_3"] == 250.0
    assert data["monthly_costs"] == 1800.0
    assert data["initial_balance"] == 50000.0


def test_save_budget_settings_update(authenticated_client, test_db, test_user_a):
    """PUT /api/budget/settings updates existing settings."""
    test_db.insert("budget_settings", {
        "id": str(uuid.uuid4()),
        "calendar_id": test_user_a.calendar_id,
        "rate_1": 100.0,
        "rate_2": 100.0,
        "rate_3": 100.0,
        "monthly_costs": 1000.0,
        "initial_balance": 10000.0,
    })

    payload = {
        "rate_1": 200.0,
        "rate_2": 300.0,
        "rate_3": 400.0,
        "monthly_costs": 2000.0,
        "initial_balance": 60000.0,
    }
    response = authenticated_client.put("/api/budget/settings", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["rate_1"] == 200.0
    assert data["rate_2"] == 300.0
    assert data["rate_3"] == 400.0
    assert data["monthly_costs"] == 2000.0
    assert data["initial_balance"] == 60000.0


def test_save_budget_settings_validation_negative_rate(authenticated_client):
    """PUT with negative rate_1 returns 422 validation error."""
    payload = {
        "rate_1": -10.0,
        "rate_2": 200.0,
        "rate_3": 250.0,
        "monthly_costs": 1800.0,
        "initial_balance": 50000.0,
    }
    response = authenticated_client.put("/api/budget/settings", json=payload)
    assert response.status_code == 422


def test_save_budget_settings_validation_negative_balance(authenticated_client):
    """PUT with negative initial_balance returns 422."""
    payload = {
        "rate_1": 150.0,
        "rate_2": 200.0,
        "rate_3": 250.0,
        "monthly_costs": 1800.0,
        "initial_balance": -100.0,
    }
    response = authenticated_client.put("/api/budget/settings", json=payload)
    assert response.status_code == 422


def test_save_budget_settings_validation_zero_rate(authenticated_client):
    """PUT with rate_1=0 returns 422 (must be > 0)."""
    payload = {
        "rate_1": 0.0,
        "rate_2": 200.0,
        "rate_3": 250.0,
        "monthly_costs": 1800.0,
        "initial_balance": 50000.0,
    }
    response = authenticated_client.put("/api/budget/settings", json=payload)
    assert response.status_code == 422


def test_save_budget_settings_zero_balance_allowed(authenticated_client):
    """PUT with initial_balance=0 is valid (zero starting balance)."""
    payload = {
        "rate_1": 150.0,
        "rate_2": 200.0,
        "rate_3": 250.0,
        "monthly_costs": 1800.0,
        "initial_balance": 0.0,
    }
    response = authenticated_client.put("/api/budget/settings", json=payload)
    assert response.status_code == 200
    assert response.json()["data"]["initial_balance"] == 0.0


def test_save_budget_settings_rounds_to_two_decimals(authenticated_client):
    """PUT with extra decimal precision gets rounded to 2 decimals."""
    payload = {
        "rate_1": 150.999,
        "rate_2": 200.0,
        "rate_3": 250.0,
        "monthly_costs": 1800.0,
        "initial_balance": 50000.0,
    }
    response = authenticated_client.put("/api/budget/settings", json=payload)
    assert response.status_code == 200
    assert response.json()["data"]["rate_1"] == 151.0


# ── View Tests ─────────────────────────────────────────────


def test_budget_settings_page_renders(authenticated_client):
    """GET /budget/settings returns 200 HTML with budget content."""
    response = authenticated_client.get("/budget/settings")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "budget.section_rates" in response.text or "Stawki godzinowe" in response.text


def test_budget_settings_page_has_form_fields(authenticated_client):
    """Settings page contains all expected form input fields."""
    response = authenticated_client.get("/budget/settings")
    assert response.status_code == 200
    assert 'id="rate_1"' in response.text
    assert 'id="rate_2"' in response.text
    assert 'id="rate_3"' in response.text
    assert 'id="monthly_costs"' in response.text
    assert 'id="initial_balance"' in response.text


def test_budget_settings_nav_link_on_home(authenticated_client):
    """Home page nav bar contains budget settings link."""
    response = authenticated_client.get("/")
    assert response.status_code == 200
    assert "/budget/settings" in response.text


def test_budget_settings_page_unauthenticated(test_client):
    """GET /budget/settings without auth redirects or returns 401."""
    response = test_client.get("/budget/settings", follow_redirects=False)
    assert response.status_code in (401, 302, 307)
