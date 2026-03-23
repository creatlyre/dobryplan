"""HMAC-based license key generation and validation for Synco self-hosted."""

import hmac
import secrets


def generate_license_key(secret: str) -> str:
    """Generate a Synco self-hosted license key.

    Format: SYNCO-XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX-CCCCCCCC
    where X = 32 hex chars (payload) and C = 8 hex chars (HMAC check).
    """
    payload = secrets.token_hex(16)  # 32 hex chars
    check = hmac.new(secret.encode(), bytes.fromhex(payload), "sha256").hexdigest()[:8]
    return (
        f"SYNCO-{payload[:8]}-{payload[8:16]}-{payload[16:24]}-{payload[24:32]}-{check}"
    )


def validate_license_key(key: str, secret: str) -> bool:
    """Validate a Synco license key against the secret.

    Returns True if valid, False for any invalid/malformed key.
    """
    if not isinstance(key, str):
        return False
    parts = key.split("-")
    if len(parts) != 6 or parts[0] != "SYNCO":
        return False
    try:
        payload_hex = "".join(parts[1:5])  # 32 hex chars
        provided_check = parts[5]
        if len(payload_hex) != 32 or len(provided_check) != 8:
            return False
        expected_check = hmac.new(
            secret.encode(), bytes.fromhex(payload_hex), "sha256"
        ).hexdigest()[:8]
        return hmac.compare_digest(expected_check, provided_check)
    except (ValueError, AttributeError):
        return False
