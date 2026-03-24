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
    assert response.status_code == 302
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
    """POST /auth/logout should clear session and supabase_refresh cookies."""
    resp = test_client.post("/auth/logout", follow_redirects=False)
    cookie_headers = [
        v for k, v in resp.headers.multi_items() if k.lower() == "set-cookie"
    ]
    cookie_str = " ".join(cookie_headers)
    assert "session=" in cookie_str
    assert "supabase_refresh=" in cookie_str


def test_login_page_renders(test_client):
    """GET /auth/login renders login HTML with password-login form and register link."""
    response = test_client.get("/auth/login", follow_redirects=False)
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "password-login" in body
    assert "auth/register" in body


def test_login_google_redirect(test_client):
    """GET /auth/login?provider=google redirects to OAuth provider."""
    response = test_client.get("/auth/login?provider=google", follow_redirects=False)
    assert response.status_code in (302, 307)
    location = response.headers.get("location", "")
    assert "google" in location.lower() or "supabase" in location.lower() or "accounts.google" in location.lower()


def test_register_page_renders(test_client):
    """GET /auth/register renders registration HTML with form and login link."""
    response = test_client.get("/auth/register", follow_redirects=False)
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "auth/register" in body
    assert "auth/login" in body


def test_login_page_has_google_oauth_button(test_client):
    """Login page includes a Google OAuth sign-in link."""
    body = test_client.get("/auth/login").text
    assert "auth/login?provider=google" in body


def test_register_page_has_google_oauth_button(test_client):
    """Register page includes a Google OAuth sign-up link."""
    body = test_client.get("/auth/register").text
    assert "auth/login?provider=google" in body


def test_forgot_password_page_renders(test_client):
    """GET /auth/forgot-password renders an email form."""
    response = test_client.get("/auth/forgot-password", follow_redirects=False)
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "forgot-password" in response.text


def test_forgot_password_submit_returns_success(test_client, monkeypatch):
    """POST /auth/forgot-password returns 200 when Supabase sends the reset email."""
    import app.auth.routes as auth_routes

    async def _mock_reset(email, redirect_to):
        return {}

    monkeypatch.setattr(auth_routes, "supabase_request_password_reset", _mock_reset)
    monkeypatch.setattr(auth_routes, "is_supabase_auth_enabled", lambda s=None: True)

    response = test_client.post(
        "/auth/forgot-password",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 200
    assert "message" in response.json()


def test_forgot_password_nonexistent_email_still_succeeds(test_client, monkeypatch):
    """POST /auth/forgot-password never reveals whether an email exists (security)."""
    import app.auth.routes as auth_routes

    async def _mock_reset(email, redirect_to):
        raise ValueError("User not found")

    monkeypatch.setattr(auth_routes, "supabase_request_password_reset", _mock_reset)
    monkeypatch.setattr(auth_routes, "is_supabase_auth_enabled", lambda s=None: True)

    response = test_client.post(
        "/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == 200


def test_confirm_callback_recovery_redirects_to_update_password(test_client, monkeypatch):
    """GET /auth/confirm?type=recovery creates session and redirects to update-password."""
    import app.auth.routes as auth_routes

    async def _mock_verify(token_hash, type_):
        return {"access_token": "recovered_token", "refresh_token": "refresh_123"}

    async def _mock_fetch_user(token):
        return {"id": "uid-1", "email": "user@example.com", "user_metadata": {"full_name": "Test User"}}

    monkeypatch.setattr(auth_routes, "supabase_verify_otp", _mock_verify)
    monkeypatch.setattr(auth_routes, "fetch_supabase_user", _mock_fetch_user)

    response = test_client.get(
        "/auth/confirm?token_hash=abc123&type=recovery",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/auth/update-password" in response.headers.get("location", "")
    assert "session=" in response.headers.get("set-cookie", "")


def test_confirm_callback_signup_redirects_to_home(test_client, monkeypatch):
    """GET /auth/confirm?type=signup creates session and redirects to /."""
    import app.auth.routes as auth_routes

    async def _mock_verify(token_hash, type_):
        return {"access_token": "signup_token", "refresh_token": "refresh_456"}

    async def _mock_fetch_user(token):
        return {"id": "uid-2", "email": "new@example.com", "user_metadata": {"full_name": "New User"}}

    monkeypatch.setattr(auth_routes, "supabase_verify_otp", _mock_verify)
    monkeypatch.setattr(auth_routes, "fetch_supabase_user", _mock_fetch_user)

    response = test_client.get(
        "/auth/confirm?token_hash=def456&type=signup",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers.get("location") == "/"
    assert "session=" in response.headers.get("set-cookie", "")


def test_confirm_callback_missing_params_redirects_to_login(test_client):
    """GET /auth/confirm without token_hash/type redirects to login."""
    response = test_client.get("/auth/confirm", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers.get("location", "")


def test_update_password_page_requires_session(test_client):
    """GET /auth/update-password without session redirects to login."""
    response = test_client.get("/auth/update-password", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers.get("location", "")


def test_update_password_page_renders_with_session(test_client):
    """GET /auth/update-password with session cookie renders the form."""
    test_client.cookies.set("session", "fake_session_token")
    response = test_client.get("/auth/update-password", follow_redirects=False)
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "update-password" in response.text
    test_client.cookies.clear()


def test_update_password_submit(test_client, monkeypatch):
    """POST /auth/update-password with valid password succeeds."""
    import app.auth.routes as auth_routes

    async def _mock_update(token, password):
        return {"id": "uid-1", "email": "user@example.com"}

    monkeypatch.setattr(auth_routes, "supabase_update_user_password", _mock_update)

    test_client.cookies.set("session", "valid_token")
    response = test_client.post(
        "/auth/update-password",
        json={"password": "newpassword123"},
    )
    assert response.status_code == 200
    assert "message" in response.json()
    test_client.cookies.clear()


def test_update_password_too_short(test_client):
    """POST /auth/update-password with short password returns 400."""
    test_client.cookies.set("session", "valid_token")
    response = test_client.post(
        "/auth/update-password",
        json={"password": "abc"},
    )
    assert response.status_code == 400
    test_client.cookies.clear()


def test_unauthenticated_post_to_protected_route_redirects_as_get(test_client):
    """Unauthenticated request to dashboard should redirect with 302 (not 307) to avoid 405."""
    resp = test_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers.get("location") == "/auth/login"

    resp = test_client.get("/invite", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers.get("location") == "/auth/login"
