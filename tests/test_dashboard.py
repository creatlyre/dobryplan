from datetime import datetime, timedelta

import pytest

from app.dashboard.service import DashboardService
from app.database.models import BudgetSettings, Expense


def _event_payload(title, start, end, category_id=None, visibility="shared"):
    payload = {
        "title": title,
        "description": "",
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
        "timezone": "UTC",
        "visibility": visibility,
    }
    if category_id:
        payload["category_id"] = category_id
    return payload


# ── DASH-01: Today's Events ─────────────────────────────────────────


class TestDashboardLoads:
    def test_dashboard_returns_200(self, authenticated_client):
        response = authenticated_client.get("/dashboard")
        assert response.status_code == 200

    def test_dashboard_contains_sections(self, authenticated_client):
        response = authenticated_client.get("/dashboard")
        html = response.text
        assert "today_events" in html or "Today" in html or "Dzisiejsze" in html
        assert "week_preview" in html or "7 Days" in html or "7 dni" in html
        assert "budget_snapshot" in html or "Budget" in html or "budżetu" in html.lower() or "bud" in html.lower()


class TestDashboardTodayEvents:
    def test_shows_today_events(self, authenticated_client):
        now = datetime.utcnow().replace(microsecond=0)
        start = now.replace(hour=14, minute=0, second=0)
        end = now.replace(hour=15, minute=0, second=0)
        authenticated_client.post("/api/events", json=_event_payload("Dashboard Test Event", start, end))

        response = authenticated_client.get("/dashboard")
        assert response.status_code == 200
        assert "Dashboard Test Event" in response.text

    def test_events_have_category_colors(self, authenticated_client):
        # Create a category
        cat_resp = authenticated_client.post(
            "/api/events/categories",
            json={"name": "Work", "color": "#ff5500"},
        )
        cat_id = cat_resp.json()["id"]

        now = datetime.utcnow().replace(microsecond=0)
        start = now.replace(hour=10, minute=0, second=0)
        end = now.replace(hour=11, minute=0, second=0)
        authenticated_client.post(
            "/api/events",
            json=_event_payload("Color Test", start, end, category_id=cat_id),
        )

        response = authenticated_client.get("/dashboard")
        assert "#ff5500" in response.text

    def test_max_five_events_with_overflow(self, authenticated_client):
        now = datetime.utcnow().replace(microsecond=0)
        for i in range(7):
            start = now.replace(hour=8 + i, minute=0, second=0)
            end = now.replace(hour=8 + i, minute=30, second=0)
            authenticated_client.post("/api/events", json=_event_payload(f"Ev{i}", start, end))

        response = authenticated_client.get("/dashboard")
        html = response.text
        # Should show overflow indicator (+2)
        assert "+2" in html

    def test_empty_events_state(self, authenticated_client):
        response = authenticated_client.get("/dashboard")
        html = response.text
        # Should contain the empty state text (no_events_today i18n key in some lang)
        assert "No events today" in html or "Brak wydarze" in html


# ── DASH-02: 7-Day Preview ──────────────────────────────────────────


class TestDashboardWeekPreview:
    def test_shows_upcoming_events(self, authenticated_client):
        tomorrow = datetime.utcnow().replace(microsecond=0) + timedelta(days=1)
        start = tomorrow.replace(hour=9, minute=0, second=0)
        end = tomorrow.replace(hour=10, minute=0, second=0)
        authenticated_client.post("/api/events", json=_event_payload("Tomorrow Meeting", start, end))

        response = authenticated_client.get("/dashboard")
        assert "Tomorrow Meeting" in response.text

    def test_truncates_at_three_per_day(self, authenticated_client):
        tomorrow = datetime.utcnow().replace(microsecond=0) + timedelta(days=1)
        for i in range(5):
            start = tomorrow.replace(hour=8 + i, minute=0, second=0)
            end = tomorrow.replace(hour=8 + i, minute=30, second=0)
            authenticated_client.post("/api/events", json=_event_payload(f"WkEv{i}", start, end))

        response = authenticated_client.get("/dashboard")
        # Should show +2 for overflow in the week preview
        assert "+2" in response.text


# ── DASH-03: Budget Snapshot ─────────────────────────────────────────


class TestDashboardBudgetSnapshot:
    def test_budget_no_data_shows_setup(self, authenticated_client):
        response = authenticated_client.get("/dashboard")
        html = response.text
        # Should contain budget setup CTA
        assert "budget/settings" in html.lower()

    def test_budget_with_data(self, authenticated_client, test_db, test_user_a):
        now = datetime.utcnow()
        # Set up budget settings
        settings = BudgetSettings(
            id="bs-1",
            calendar_id=test_user_a.calendar_id,
            rate_1=100.0,
            rate_2=0.0,
            rate_3=0.0,
            zus_costs=0.0,
            accounting_costs=0.0,
            initial_balance=1000.0,
        )
        test_db.add(settings)

        # Add monthly hours so has_data=True
        test_db.insert("monthly_hours", {
            "calendar_id": test_user_a.calendar_id,
            "year": now.year,
            "month": now.month,
            "rate_1_hours": 160.0,
            "rate_2_hours": 160.0,
            "rate_3_hours": 160.0,
        })

        response = authenticated_client.get("/dashboard")
        html = response.text
        # Should show balance info (budget snapshot has_data=True)
        assert "PLN" in html


# ── DASH-04: Quick-Add Buttons ───────────────────────────────────────


class TestDashboardQuickAdd:
    def test_quick_add_buttons_present(self, authenticated_client):
        response = authenticated_client.get("/dashboard")
        html = response.text
        assert "qaOpenModal" in html
        assert "/calendar?open=event-entry" in html
        assert "/calendar?open=expense" in html


# ── Navigation ───────────────────────────────────────────────────────


class TestDashboardNavigation:
    def test_dashboard_link_in_nav(self, authenticated_client):
        response = authenticated_client.get("/dashboard")
        html = response.text
        assert "/dashboard" in html

    def test_root_redirects_to_dashboard(self, authenticated_client):
        response = authenticated_client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/dashboard" in response.headers.get("location", "")


# ── DashboardService Unit Tests ──────────────────────────────────────


class TestDashboardServiceUnit:
    def test_get_today_events_empty(self, test_db, test_user_a):
        service = DashboardService(test_db)
        events = service.get_today_events(test_user_a.calendar_id, test_user_a.id)
        assert events == []

    def test_get_week_preview_structure(self, test_db, test_user_a):
        service = DashboardService(test_db)
        preview = service.get_week_preview(test_user_a.calendar_id, test_user_a.id)
        assert len(preview) == 7
        for day in preview:
            assert "date" in day
            assert "day_name" in day
            assert "events" in day
            assert "overflow" in day

    def test_get_budget_snapshot_no_data(self, test_db, test_user_a):
        service = DashboardService(test_db)
        snapshot = service.get_budget_snapshot(test_user_a.calendar_id)
        assert snapshot["has_data"] is False

    def test_get_event_categories_returns_dict(self, test_db, test_user_a):
        service = DashboardService(test_db)
        cat_map = service.get_event_categories(test_user_a.calendar_id)
        assert isinstance(cat_map, dict)

    def test_get_top_expense_categories_empty(self, test_db, test_user_a):
        service = DashboardService(test_db)
        cats = service.get_top_expense_categories(test_user_a.calendar_id)
        assert cats == []
