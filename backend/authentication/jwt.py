import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from backend.authentication.schemas import TokenPayload
from backend.core.config import get_settings

settings = get_settings()


class TokenType(str, Enum):
    """Discriminates between access and refresh tokens."""

    ACCESS = "access"
    REFRESH = "refresh"


class InvalidTokenError(Exception):
    """Raised when a JWT is malformed, mis-typed, or fails verification."""


class TokenExpiredError(Exception):
    """Raised when a JWT's expiration claim has passed."""


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Build and sign a JWT with standard claims.

    Args:
        subject: The token subject, typically the user's ID.
        token_type: Whether this is an access or refresh token.
        expires_delta: How long the token remains valid.
        extra_claims: Additional claims to embed (e.g. role).

    Returns:
        The encoded, signed JWT string.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(
    subject: str, role: str, expires_delta: timedelta | None = None
) -> str:
    """Create a short-lived access token.

    Args:
        subject: The authenticated user's ID, as a string.
        role: The user's current role, embedded for downstream checks.
        expires_delta: Optional override for the token's lifetime.

    Returns:
        The encoded access token.
    """
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    return _create_token(subject, TokenType.ACCESS, delta, extra_claims={"role": role})


def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a long-lived refresh token.

    Args:
        subject: The authenticated user's ID, as a string.
        expires_delta: Optional override for the token's lifetime.

    Returns:
        The encoded refresh token.
    """
    delta = expires_delta or timedelta(days=settings.refresh_token_expire_days)
    return _create_token(subject, TokenType.REFRESH, delta)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT's signature and expiration.

    Args:
        token: The encoded JWT string.

    Returns:
        The decoded token claims.

    Raises:
        TokenExpiredError: If the token's expiration has passed.
        InvalidTokenError: If the token is malformed or the signature is
            invalid.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("The provided token has expired.") from exc
    except JWTError as exc:
        raise InvalidTokenError("The provided token is invalid or malformed.") from exc
    return TokenPayload(**payload)


def verify_token(token: str, expected_type: TokenType) -> TokenPayload:
    """Decode a token and assert it matches the expected token type.

    Args:
        token: The encoded JWT string.
        expected_type: The token type the caller requires (access/refresh).

    Returns:
        The decoded token claims.

    Raises:
        TokenExpiredError: If the token's expiration has passed.
        InvalidTokenError: If the token is malformed, invalid, or of the
            wrong type.
    """
    token_payload = decode_token(token)
    if token_payload.type != expected_type.value:
        raise InvalidTokenError(
            f"Expected a '{expected_type.value}' token but received "
            f"'{token_payload.type}'."
        )
    return token_payload