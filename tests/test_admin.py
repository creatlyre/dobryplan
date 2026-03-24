import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.admin.dependencies import get_admin_user
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.database.database import get_db
from app.database.models import Calendar, User, Subscription
from main import app
from tests.conftest import InMemoryStore


@pytest.fixture
def admin_db():
    store = InMemoryStore()
    # Create admin user
    cal = Calendar(id=str(uuid.uuid4()), name="Admin Cal")
    store.add(cal)
    admin = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        name="Admin User",
        is_admin=True,
        calendar_id=cal.id,
        created_at=datetime.utcnow() - timedelta(days=60),
        last_login=datetime.utcnow(),
    )
    store.add(admin)

    # Create regular users
    regular = User(
        id=str(uuid.uuid4()),
        email="regular@example.com",
        name="Regular User",
        is_admin=False,
        created_at=datetime.utcnow() - timedelta(days=10),
        last_login=datetime.utcnow(),
    )
    store.add(regular)

    another = User(
        id=str(uuid.uuid4()),
        email="another@example.com",
        name="Another User",
        is_admin=False,
        created_at=datetime.utcnow() - timedelta(days=5),
        last_login=datetime.utcnow(),
    )
    store.add(another)

    # Add a subscription for regular user
    sub = Subscription(
        id=str(uuid.uuid4()),
        user_id=regular.id,
        plan="pro",
        status="active",
    )
    store.add(sub)

    return store, admin, regular, another


@pytest.fixture
def admin_client(admin_db):
    store, admin, _, _ = admin_db

    def override_get_db():
        yield store

    async def override_get_current_user():
        return admin

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def non_admin_client(admin_db):
    store, _, regular, _ = admin_db

    def override_get_db():
        yield store

    async def override_get_current_user():
        return regular

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# --- Access control ---


class TestAdminAccessControl:
    def test_admin_list_users_forbidden(self, non_admin_client):
        resp = non_admin_client.get("/api/admin/users")
        assert resp.status_code == 403

    def test_admin_stats_forbidden(self, non_admin_client):
        resp = non_admin_client.get("/api/admin/stats")
        assert resp.status_code == 403

    def test_admin_user_detail_forbidden(self, non_admin_client, admin_db):
        _, _, regular, _ = admin_db
        resp = non_admin_client.get(f"/api/admin/users/{regular.id}")
        assert resp.status_code == 403

    def test_admin_change_plan_forbidden(self, non_admin_client, admin_db):
        _, _, regular, _ = admin_db
        resp = non_admin_client.patch(
            f"/api/admin/users/{regular.id}/plan", json={"plan": "free"}
        )
        assert resp.status_code == 403

    def test_admin_toggle_admin_forbidden(self, non_admin_client, admin_db):
        _, _, regular, _ = admin_db
        resp = non_admin_client.patch(
            f"/api/admin/users/{regular.id}/admin", json={"is_admin": True}
        )
        assert resp.status_code == 403


# --- User listing ---


class TestAdminListUsers:
    def test_admin_list_users(self, admin_client, admin_db):
        resp = admin_client.get("/api/admin/users")
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] == 3  # admin + regular + another
        assert len(data["users"]) == 3

    def test_admin_list_users_search(self, admin_client, admin_db):
        resp = admin_client.get("/api/admin/users?search=regular")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["users"][0]["email"] == "regular@example.com"

    def test_admin_list_users_pagination(self, admin_client, admin_db):
        resp = admin_client.get("/api/admin/users?offset=0&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["users"]) == 2
        assert data["total"] == 3


# --- User detail ---


class TestAdminUserDetail:
    def test_admin_get_user_detail(self, admin_client, admin_db):
        _, _, regular, _ = admin_db
        resp = admin_client.get(f"/api/admin/users/{regular.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == "regular@example.com"
        assert data["plan"] == "pro"

    def test_admin_get_user_detail_not_found(self, admin_client):
        resp = admin_client.get(f"/api/admin/users/{uuid.uuid4()}")
        assert resp.status_code == 404


# --- Plan change ---


class TestAdminChangePlan:
    def test_admin_change_plan(self, admin_client, admin_db):
        _, _, regular, _ = admin_db
        resp = admin_client.patch(
            f"/api/admin/users/{regular.id}/plan", json={"plan": "family_plus"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "family_plus"
        assert data["message"] == "Plan updated"

    def test_admin_change_plan_invalid(self, admin_client, admin_db):
        _, _, regular, _ = admin_db
        resp = admin_client.patch(
            f"/api/admin/users/{regular.id}/plan", json={"plan": "enterprise"}
        )
        assert resp.status_code == 400


# --- Admin toggle ---


class TestAdminToggle:
    def test_admin_toggle_admin(self, admin_client, admin_db):
        _, _, regular, _ = admin_db
        resp = admin_client.patch(
            f"/api/admin/users/{regular.id}/admin", json={"is_admin": True}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_admin"] is True
        assert data["message"] == "Admin status updated"

    def test_admin_toggle_admin_self(self, admin_client, admin_db):
        _, admin, _, _ = admin_db
        resp = admin_client.patch(
            f"/api/admin/users/{admin.id}/admin", json={"is_admin": False}
        )
        assert resp.status_code == 400
        assert "own admin status" in resp.json()["detail"].lower()


# --- Stats ---


class TestAdminStats:
    def test_admin_stats(self, admin_client, admin_db):
        resp = admin_client.get("/api/admin/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_count"] == 3
        assert isinstance(data["plan_distribution"], dict)
        assert isinstance(data["recent_signups"], int)
        assert data["recent_signups"] >= 2  # regular + another created within 30 days


# --- Admin Views (HTML) ---


class TestAdminViews:
    def test_admin_dashboard_page(self, admin_client):
        resp = admin_client.get("/admin", follow_redirects=False)
        assert resp.status_code == 200
        assert "Admin" in resp.text or "administratora" in resp.text

    def test_admin_users_page(self, admin_client):
        resp = admin_client.get("/admin/users")
        assert resp.status_code == 200
        assert "regular@example.com" in resp.text

    def test_admin_user_detail_page(self, admin_client, admin_db):
        _, _, regular, _ = admin_db
        resp = admin_client.get(f"/admin/users/{regular.id}")
        assert resp.status_code == 200
        assert "regular@example.com" in resp.text

    def test_non_admin_redirected_from_admin_pages(self, non_admin_client):
        resp = non_admin_client.get("/admin", follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers.get("location", "")

    def test_admin_nav_link_visible_for_admin(self, admin_client):
        resp = admin_client.get("/dashboard")
        assert resp.status_code == 200
        assert 'href="/admin"' in resp.text

    def test_admin_nav_link_hidden_for_non_admin(self, non_admin_client):
        resp = non_admin_client.get("/dashboard")
        # non_admin_client has overridden get_current_user so dashboard should work
        if resp.status_code == 200:
            assert 'href="/admin"' not in resp.text
