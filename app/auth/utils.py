import base64
import os
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config import Settings


def _get_legacy_cipher() -> Fernet:
    settings = Settings()
    key_material = settings.DB_ENCRYPTION_KEY.encode("utf-8")
    digest = hashlib.sha256(key_material).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    return Fernet(fernet_key)


def _get_cipher(salt: bytes) -> Fernet:
    settings = Settings()
    key_material = settings.DB_ENCRYPTION_KEY.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
    )
    fernet_key = base64.urlsafe_b64encode(kdf.derive(key_material))
    return Fernet(fernet_key)


def encrypt_token(token: str) -> str:
    salt = os.urandom(16)
    cipher = _get_cipher(salt)
    encrypted_token = cipher.encrypt(token.encode("utf-8")).decode("utf-8")
    salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8")
    return f"{salt_b64}:{encrypted_token}"


def decrypt_token(encrypted_token: str) -> str:
    if ":" in encrypted_token:
        try:
            salt_b64, actual_encrypted_token = encrypted_token.split(":", 1)
            salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
            cipher = _get_cipher(salt)
            return cipher.decrypt(actual_encrypted_token.encode("utf-8")).decode(
                "utf-8"
            )
        except Exception:
            # Fallback to legacy if parsing fails for some reason
            pass

    cipher = _get_legacy_cipher()
    return cipher.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
