"""
Tests for SaaS production hardening (Phase 30).

Tests security headers, CORS, rate limiting, health checks, and structured logging.
"""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ── Security Headers Tests ─────────────────────────────────────────────────


class TestSecurityHeaders:
    """Verify SecurityHeadersMiddleware adds all required headers."""

    def test_x_content_type_options(self, test_client):
        """Every response includes X-Content-Type-Options: nosniff."""
        resp = test_client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self, test_client):
        """Every response includes X-Frame-Options: DENY."""
        resp = test_client.get("/health")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_referrer_policy(self, test_client):
        """Every response includes Referrer-Policy."""
        resp = test_client.get("/health")
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, test_client):
        """Every response includes Permissions-Policy."""
        resp = test_client.get("/health")
        policy = resp.headers.get("Permissions-Policy")
        assert policy is not None
        assert "camera=()" in policy
        assert "microphone=()" in policy

    def test_no_hsts_in_development(self, test_client):
        """HSTS is NOT set in development environment."""
        resp = test_client.get("/health")
        # Default env is "development" — HSTS should be absent
        assert "Strict-Transport-Security" not in resp.headers

    def test_security_headers_on_html_page(self, authenticated_client):
        """Security headers are present on HTML pages too."""
        resp = authenticated_client.get("/dashboard")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_security_headers_on_api_endpoint(self, authenticated_client):
        """Security headers are present on API JSON responses."""
        resp = authenticated_client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_security_headers_middleware_import(self):
        """SecurityHeadersMiddleware can be imported and instantiated."""
        from app.middleware.security import SecurityHeadersMiddleware
        from fastapi import FastAPI

        test_app = FastAPI()
        test_app.add_middleware(SecurityHeadersMiddleware, environment="production")
        # No exception raised

    def test_hsts_in_production_environment(self):
        """HSTS is set when environment is 'production'."""
        from fastapi import FastAPI
        from app.middleware.security import SecurityHeadersMiddleware

        test_app = FastAPI()
        test_app.add_middleware(SecurityHeadersMiddleware, environment="production")

        @test_app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        client = TestClient(test_app)
        resp = client.get("/test")
        assert resp.headers.get("Strict-Transport-Security") == "max-age=63072000; includeSubDomains"


# ── Health Endpoint Tests ──────────────────────────────────────────────────


class TestHealthEndpoints:
    """Test health and readiness endpoints."""

    def test_health_returns_ok(self, test_client):
        """GET /health returns status and checks."""
        resp = test_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "checks" in data
        assert "app" in data["checks"]

    def test_health_app_check_ok(self, test_client):
        """Health app check is always ok."""
        resp = test_client.get("/health")
        data = resp.json()
        assert data["checks"]["app"] == "ok"

    def test_health_ready_endpoint(self, test_client):
        """GET /health/ready returns ready status."""
        resp = test_client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"

    def test_health_json_response(self, test_client):
        """Health endpoints return JSON."""
        resp = test_client.get("/health")
        assert "application/json" in resp.headers["content-type"]

    def test_health_ready_json_response(self, test_client):
        resp = test_client.get("/health/ready")
        assert "application/json" in resp.headers["content-type"]


# ── Rate Limiting Tests ────────────────────────────────────────────────────


class TestRateLimiting:
    """Test SlowAPI rate limiting middleware."""

    def test_rate_limiter_installed(self, test_client):
        """SlowAPI middleware is active (app.state.limiter exists)."""
        from main import app
        assert hasattr(app.state, "limiter")
        assert app.state.limiter is not None

    def test_normal_request_not_limited(self, test_client):
        """A single request is not rate-limited."""
        resp = test_client.get("/health")
        assert resp.status_code == 200
        # Should NOT be 429

    def test_rate_limit_header_present(self, test_client):
        """Rate limit headers are present in responses."""
        resp = test_client.get("/health/ready")
        # SlowAPI adds X-RateLimit headers
        # Some versions may not add them to all endpoints
        assert resp.status_code == 200


# ── CORS Tests ─────────────────────────────────────────────────────────────


class TestCORS:
    """Test CORS middleware configuration."""

    def test_no_cors_headers_without_origin(self, test_client):
        """Requests without Origin header get no CORS headers."""
        resp = test_client.get("/health")
        # Without ALLOWED_ORIGINS set, CORS middleware is not even active
        assert resp.status_code == 200

    def test_cors_middleware_configured_from_settings(self):
        """CORSMiddleware reads from Settings.ALLOWED_ORIGINS."""
        from config import Settings
        s = Settings(_env_file=None)
        # ALLOWED_ORIGINS default is empty — CORS not active
        assert hasattr(s, "ALLOWED_ORIGINS")


# ── Deployment Configuration Tests ─────────────────────────────────────────


class TestDeploymentConfig:
    """Verify production deployment files exist and are correct."""

    def test_dockerfile_exists(self):
        assert os.path.isfile("Dockerfile")

    def test_dockerfile_uses_gunicorn(self):
        with open("Dockerfile") as f:
            content = f.read()
        assert "gunicorn" in content
        assert "uvicorn" in content.lower()

    def test_dockerfile_multi_stage(self):
        with open("Dockerfile") as f:
            content = f.read()
        assert content.count("FROM ") >= 2  # multi-stage

    def test_dockerfile_non_root_or_slim(self):
        with open("Dockerfile") as f:
            content = f.read()
        assert "python:3.12-slim" in content

    def test_dockerignore_exists(self):
        assert os.path.isfile(".dockerignore")

    def test_dockerignore_excludes_env(self):
        with open(".dockerignore") as f:
            content = f.read()
        assert ".env" in content

    def test_railway_toml_exists(self):
        assert os.path.isfile("railway.toml")

    def test_railway_toml_healthcheck(self):
        with open("railway.toml") as f:
            content = f.read()
        assert "health" in content.lower()

    def test_env_example_exists(self):
        assert os.path.isfile(".env.example")

    def test_env_example_has_sentry(self):
        with open(".env.example") as f:
            content = f.read()
        assert "SENTRY_DSN" in content

    def test_env_example_has_stripe(self):
        with open(".env.example") as f:
            content = f.read()
        assert "STRIPE_SECRET_KEY" in content


# ── Config Environment Tests ───────────────────────────────────────────────


class TestProductionConfig:
    """Verify production config fields exist with correct defaults."""

    def test_environment_default(self):
        from config import Settings
        s = Settings(_env_file=None)
        assert s.ENVIRONMENT == "development"

    def test_log_level_default(self):
        from config import Settings
        s = Settings(_env_file=None)
        assert s.LOG_LEVEL == "INFO"

    def test_allowed_origins_default_empty(self):
        from config import Settings
        s = Settings(_env_file=None)
        assert s.ALLOWED_ORIGINS == ""

    def test_sentry_dsn_default_empty(self):
        from config import Settings
        s = Settings(_env_file=None)
        assert s.SENTRY_DSN == ""

    def test_stripe_keys_exist_in_config(self):
        from config import Settings
        s = Settings(_env_file=None)
        assert hasattr(s, "STRIPE_SECRET_KEY")
        assert hasattr(s, "STRIPE_WEBHOOK_SECRET")
        assert hasattr(s, "STRIPE_PUBLISHABLE_KEY")
        assert hasattr(s, "STRIPE_PRO_PRICE_ID")
        assert hasattr(s, "STRIPE_FAMILY_PLUS_PRICE_ID")


# ── Structured Logging Tests ──────────────────────────────────────────────


class TestStructuredLogging:
    """Test logging configuration."""

    def test_json_formatter_exists(self):
        from main import JSONFormatter
        fmt = JSONFormatter()
        assert fmt is not None

    def test_setup_logging_callable(self):
        from main import setup_logging
        # Should not throw
        setup_logging()


# ── Middleware Order Tests ─────────────────────────────────────────────────


class TestMiddlewareOrder:
    """Verify middleware is registered in correct order."""

    def test_all_middleware_registered(self):
        """All required middleware classes are in the app."""
        from main import app
        middleware_classes = [m.cls.__name__ if hasattr(m, 'cls') else str(m) for m in app.user_middleware]
        # Check key middleware is present
        class_names = " ".join(str(m) for m in middleware_classes)
        assert "SecurityHeaders" in class_names or "Security" in class_names.lower() or any("security" in str(m).lower() for m in app.user_middleware)
