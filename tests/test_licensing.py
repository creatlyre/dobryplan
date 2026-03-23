"""Tests for the Synco self-hosted license key system."""

import os

import pytest
from fastapi.testclient import TestClient

from app.licensing.keys import generate_license_key, validate_license_key


# --- Key generation tests ---


class TestGenerateLicenseKey:
    def test_format(self):
        key = generate_license_key("secret")
        assert key.startswith("SYNCO-")
        parts = key.split("-")
        assert len(parts) == 6
        assert parts[0] == "SYNCO"
        for part in parts[1:]:
            assert len(part) == 8, f"Part '{part}' is not 8 chars"

    def test_unique(self):
        k1 = generate_license_key("secret")
        k2 = generate_license_key("secret")
        assert k1 != k2

    def test_deterministic_validation(self):
        secret = "my-secret"
        key = generate_license_key(secret)
        assert validate_license_key(key, secret)


# --- Key validation tests ---


class TestValidateLicenseKey:
    def test_valid_key(self):
        secret = "test-secret-abc"
        key = generate_license_key(secret)
        assert validate_license_key(key, secret) is True

    def test_wrong_secret(self):
        key = generate_license_key("secret-a")
        assert validate_license_key(key, "secret-b") is False

    def test_malformed_random_string(self):
        assert validate_license_key("random-garbage", "secret") is False

    def test_malformed_empty_string(self):
        assert validate_license_key("", "secret") is False

    def test_malformed_synco_prefix_only(self):
        assert validate_license_key("SYNCO-", "secret") is False

    def test_malformed_partial_key(self):
        assert validate_license_key("SYNCO-aabb", "secret") is False

    def test_tampered_key(self):
        secret = "tamper-test"
        key = generate_license_key(secret)
        # Flip the first hex char after SYNCO-
        parts = key.split("-")
        char = parts[1][0]
        flipped = "a" if char != "a" else "b"
        parts[1] = flipped + parts[1][1:]
        tampered = "-".join(parts)
        assert validate_license_key(tampered, secret) is False

    def test_none_key(self):
        assert validate_license_key(None, "secret") is False

    def test_integer_key(self):
        assert validate_license_key(12345, "secret") is False


# --- Middleware tests ---


class TestLicenseCheckMiddleware:
    """Tests for the LicenseCheckMiddleware behavior."""

    def _make_app(self, environment="development", license_key="", license_secret=""):
        """Create a test FastAPI app with LicenseCheckMiddleware."""
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse, JSONResponse
        from app.licensing.middleware import LicenseCheckMiddleware

        test_app = FastAPI()
        test_app.add_middleware(
            LicenseCheckMiddleware,
            environment=environment,
            license_key=license_key,
            license_secret=license_secret,
        )

        @test_app.get("/page", response_class=HTMLResponse)
        async def page():
            return "<html><body><h1>Hello</h1></body></html>"

        @test_app.get("/api/data")
        async def api_data():
            return {"key": "value"}

        @test_app.get("/health")
        async def health():
            return {"status": "ok"}

        @test_app.get("/health/ready")
        async def health_ready():
            return {"status": "ready"}

        return test_app

    def test_skips_non_selfhosted(self):
        app = self._make_app(environment="production")
        client = TestClient(app)
        resp = client.get("/page")
        assert resp.status_code == 200
        assert "Invalid or missing license key" not in resp.text

    def test_valid_key_no_banner(self):
        secret = "test-mw-secret"
        key = generate_license_key(secret)
        app = self._make_app(
            environment="self-hosted", license_key=key, license_secret=secret
        )
        client = TestClient(app)
        resp = client.get("/page")
        assert resp.status_code == 200
        assert "Invalid or missing license key" not in resp.text

    def test_invalid_key_shows_banner(self):
        app = self._make_app(
            environment="self-hosted",
            license_key="SYNCO-bad-key",
            license_secret="secret",
        )
        client = TestClient(app)
        resp = client.get("/page")
        assert resp.status_code == 200
        assert "Invalid or missing license key" in resp.text

    def test_missing_key_shows_banner(self):
        app = self._make_app(
            environment="self-hosted", license_key="", license_secret="secret"
        )
        client = TestClient(app)
        resp = client.get("/page")
        assert resp.status_code == 200
        assert "Invalid or missing license key" in resp.text

    def test_skips_health_endpoints(self):
        app = self._make_app(
            environment="self-hosted", license_key="", license_secret="secret"
        )
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "Invalid or missing license key" not in resp.text
        resp2 = client.get("/health/ready")
        assert resp2.status_code == 200
        assert "Invalid or missing license key" not in resp2.text

    def test_skips_api_json(self):
        app = self._make_app(
            environment="self-hosted", license_key="", license_secret="secret"
        )
        client = TestClient(app)
        resp = client.get("/api/data")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"key": "value"}
