# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Company credential encryption.

Company access passwords are encrypted at rest with Fernet — a reversible,
authenticated symmetric cipher. Reversibility is required: the admin must be
able to read a password back and hand it to the company, and the later
company-facing sign-in must verify it against this same key.

The key lives only in the environment (FERNET_KEY). When it is missing or
malformed, every operation fails closed: nothing is written and no plaintext
is ever stored or logged.
"""
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from src.config import settings

logger = logging.getLogger(__name__)


class EncryptionUnavailableError(Exception):
    """Raised when the Fernet key is missing or malformed.

    Callers must turn this into a clear configuration error (503) and write
    nothing — the system must never silently fall back to plaintext.
    """


class DecryptionError(Exception):
    """Raised when a stored token cannot be decrypted (wrong key or corruption)."""


_cipher: Optional[Fernet] = None


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _get_cipher() -> Fernet:
    """Build (and cache) the Fernet cipher from the environment key.

    Raises EncryptionUnavailableError rather than defaulting to anything — a
    missing key must stop the write, not degrade it.
    """
    global _cipher
    if _cipher is not None:
        return _cipher

    key = (settings.FERNET_KEY or "").strip()
    if not key:
        raise EncryptionUnavailableError(
            "FERNET_KEY is not configured. Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        _cipher = Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise EncryptionUnavailableError(
            f"FERNET_KEY is not a valid Fernet key: {exc}"
        ) from exc
    return _cipher


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def encrypt_password(plaintext: str) -> str:
    """Encrypt a company access password for storage.

    Returns the Fernet token (str). Raises EncryptionUnavailableError when the
    key is unusable — the caller must abort the write.
    """
    if plaintext is None:
        raise ValueError("A company password is required")
    cipher = _get_cipher()
    token = cipher.encrypt(plaintext.encode("utf-8"))
    # Never log the plaintext — not even at debug level.
    logger.debug("Encrypted a company credential")
    return token.decode("utf-8")


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def decrypt_password(token: str) -> str:
    """Decrypt a stored company access password on demand (reveal/copy).

    Raises EncryptionUnavailableError when the key is unusable and
    DecryptionError when the token cannot be read (e.g. a rotated key).
    """
    cipher = _get_cipher()
    try:
        return cipher.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise DecryptionError(
            "Stored company password could not be decrypted with the current key."
        ) from exc


def is_encryption_configured() -> bool:
    """True when a usable Fernet key is present (used for a fast pre-check)."""
    try:
        _get_cipher()
        return True
    except EncryptionUnavailableError:
        return False


def reset_cipher_cache() -> None:
    """Drop the cached cipher (used when the key changes at runtime)."""
    global _cipher
    _cipher = None

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
