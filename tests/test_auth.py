from datetime import datetime

from app.auth.supabase_auth import build_google_authorize_url

from app.users.repository import UserRepository


def test_oauth_callback_creates_user(test_db, test_client, monkeypatch):
    def mock_exchange_code_for_token(code: str, state: str):
        return {
            "access_token": "fake_access",
            "refresh_token": "fake_refresh",
            "token_expiry": datetime.utcnow(),
            "user_info": {
                "email": "newuser@example.com",
                "name": "New User",
                "google_id": "google_new",
            },
        }

    import app.auth.routes

    monkeypatch.setattr(app.auth.routes, "exchange_code_for_token", mock_exchange_code_for_token)

    response = test_client.get("/auth/callback?code=fake&state=fake", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers.get("location") == "/"
    assert "session=" in response.headers.get("set-cookie", "")

    user = UserRepository(test_db).get_user_by_email("newuser@example.com")
    assert user is not None
    assert user.calendar_id is not None


def test_invalid_session_redirects(test_client):
    # Root path now serves landing page for unauthenticated users
    response = test_client.get("/", follow_redirects=False)
    assert response.status_code == 200

    # Dashboard still requires auth and redirects
    response = test_client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers.get("location") == "/auth/login"


def test_parse_invalid_session_returns_401_not_500(test_client, monkeypatch):
    import app.auth.dependencies as auth_dependencies

    async def _fetch_none(_token: str):
        return None

    async def _refresh_none(_refresh: str):
        return None

    monkeypatch.setattr(auth_dependencies, "fetch_supabase_user", _fetch_none)
    monkeypatch.setattr(auth_dependencies, "refresh_supabase_access_token", _refresh_none)

    response = test_client.post(
        "/api/events/parse",
        json={"text": "dentist Thursday 14:00"},
        cookies={"session": "invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid session"


def test_build_google_authorize_url_includes_calendar_scopes():
    url = build_google_authorize_url("http://localhost:8000/auth/callback")
    assert "provider=google" in url
    assert "scopes=" in url
    assert "https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar" in url
    assert "prompt=consent" in url


def test_logout_post_redirects_to_login(test_client):
    """POST /auth/logout should redirect to /auth/login, not return JSON."""
    resp = test_client.post("/auth/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/auth/login"


def test_logout_get_redirects_to_login(test_client):
    """GET /auth/logout should also redirect to /auth/login."""
    resp = test_client.get("/auth/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login"


def test_logout_clears_session_cookie(test_client):
    """POST /auth/logout should clear session cookie."""
    resp = test_client.post("/auth/logout", follow_redirects=False)
    cookie_headers = [
        v for k, v in resp.headers.multi_items() if k.lower() == "set-cookie"
    ]
    cookie_str = " ".join(cookie_headers)
    assert "session=" in cookie_str


def test_logout_redirects_to_login(test_client):
    """POST /auth/logout should redirect to /auth/login, not return JSON."""
    resp = test_client.post("/auth/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/auth/login"


def test_logout_clears_cookies(test_client):
    """POST /auth/logout should clear session and refresh cookies."""
    resp = test_client.post("/auth/logout", follow_redirects=False)
    cookie_headers = [v for k, v in resp.headers.raw if k == b"set-cookie"]
    cookie_str = b" ".join(cookie_headers).decode()
    assert "session" in cookie_str.lower()
    assert "supabase_refresh" in cookie_str.lower()
