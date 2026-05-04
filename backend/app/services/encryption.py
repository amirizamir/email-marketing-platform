from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

_settings = get_settings()
_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is not None:
        return _fernet
    key = _settings.encryption_key
    if not key:
        # Development-only: derive a stable key from secret (not ideal for production)
        from hashlib import sha256
        import base64

        raw = sha256(_settings.secret_key.encode()).digest()
        key = base64.urlsafe_b64encode(raw).decode()
    if isinstance(key, str) and len(key) != 44:
        from hashlib import sha256
        import base64

        raw = sha256(key.encode()).digest()
        key = base64.urlsafe_b64encode(raw).decode()
    _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_secret(plain: str) -> str:
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_secret(token: str) -> str:
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Invalid encryption or corrupted secret") from e
