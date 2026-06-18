"""
RecruitBot — Auth API Routes (Sprint 0.4)

Endpoints:
- POST /auth/register — create a new user
- POST /auth/login — authenticate and get JWT
- GET  /auth/me — get current user info (protected)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.auth import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.core.database import SYNC_DATABASE_URL

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── Sync DB session (auth is low-frequency, sync is simpler here) ──
_engine = create_engine(SYNC_DATABASE_URL, echo=False)
_Session = sessionmaker(bind=_engine)


# ── Request / Response Schemas ──

class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    role: str = Field(
        "candidate",
        description="User role: hiring_manager, recruiter, or candidate",
    )


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str


# ── Routes ──

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """Register a new user and return a JWT token."""
    # Validate role
    valid_roles = {"hiring_manager", "recruiter", "candidate"}
    if req.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{req.role}'. Must be one of: {', '.join(valid_roles)}",
        )

    session = _Session()
    try:
        # Check if email already exists
        existing = session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": req.email},
        ).fetchone()

        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        # Create user
        import uuid
        user_id = uuid.uuid4()
        hashed = hash_password(req.password)

        session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, first_name, last_name, role)
                VALUES (:id, :email, :hashed_password, :first_name, :last_name, :role)
            """),
            {
                "id": user_id,
                "email": req.email,
                "hashed_password": hashed,
                "first_name": req.first_name,
                "last_name": req.last_name,
                "role": req.role,
            },
        )
        session.commit()

        # Generate token
        token = create_access_token(
            user_id=str(user_id),
            email=req.email,
            role=req.role,
        )

        return TokenResponse(
            access_token=token,
            user={
                "id": str(user_id),
                "email": req.email,
                "first_name": req.first_name,
                "last_name": req.last_name,
                "role": req.role,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    finally:
        session.close()


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate user and return JWT token."""
    session = _Session()
    try:
        result = session.execute(
            text("""
                SELECT id, email, hashed_password, first_name, last_name, role, is_active
                FROM users WHERE email = :email
            """),
            {"email": req.email},
        ).fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_id, email, hashed_pw, first_name, last_name, role, is_active = result

        if not is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        if not verify_password(req.password, hashed_pw):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(
            user_id=str(user_id),
            email=email,
            role=role,
        )

        return TokenResponse(
            access_token=token,
            user={
                "id": str(user_id),
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    finally:
        session.close()


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """Get the current authenticated user's info."""
    session = _Session()
    try:
        result = session.execute(
            text("SELECT id, email, first_name, last_name, role FROM users WHERE id = :id"),
            {"id": user["id"]},
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            id=str(result[0]),
            email=result[1],
            first_name=result[2],
            last_name=result[3],
            role=result[4],
        )
    finally:
        session.close()
