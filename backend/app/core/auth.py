"""
RecruitBot — Authentication Service (Sprint 0.4)

JWT-based auth with password hashing.
Designed to be swapped with an OIDC provider (Auth0, Keycloak)
later — only token issuance changes; validation logic stays the same.

Uses bcrypt directly (passlib has compatibility issues with bcrypt>=5.0).

Usage:
    from app.core.auth import create_access_token, verify_password, hash_password
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from jose import jwt, JWTError
import bcrypt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token with user identity and role claims.

    The token payload structure:
        sub: user UUID
        email: user email
        role: hiring_manager | recruiter | candidate
        exp: expiration timestamp
        iat: issued-at timestamp
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    )

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY or "dev-secret-change-me",
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises JWTError on invalid/expired tokens.
    """
    settings = get_settings()
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY or "dev-secret-change-me",
        algorithms=[settings.JWT_ALGORITHM],
    )
