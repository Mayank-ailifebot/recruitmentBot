"""
RecruitBot — Auth Dependencies (Sprint 0.4)

FastAPI dependencies for protecting routes:
- get_current_user: extracts and validates JWT from Authorization header
- require_role: enforces role-based access on specific endpoints

Usage:
    @router.get("/protected")
    async def protected(user = Depends(get_current_user)):
        ...

    @router.post("/admin-only")
    async def admin_only(user = Depends(require_role("recruiter"))):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from typing import List

from app.core.auth import decode_access_token

# ── Bearer token extractor ──
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Extract and validate the current user from the JWT bearer token.
    Returns a dict with: id, email, role.
    """
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")

    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing required fields",
        )

    return {
        "id": user_id,
        "email": email,
        "role": role,
    }


def require_role(*allowed_roles: str):
    """
    Factory for role-based access control dependency.

    Usage:
        @router.get("/hiring-only")
        async def hiring_only(user = Depends(require_role("hiring_manager", "recruiter"))):
            ...
    """

    async def role_checker(
        user: dict = Depends(get_current_user),
    ) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user['role']}' not authorized. Required: {', '.join(allowed_roles)}",
            )
        return user

    return role_checker
