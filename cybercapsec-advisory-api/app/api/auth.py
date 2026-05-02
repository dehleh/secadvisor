"""Auth endpoints: signup, login, refresh, current-user."""
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.deps import get_current_user
from app.models import Company, SubscriptionTier, User, UserRole, currency_for_country
from app.schemas import (
    CompanyResponse,
    LoginRequest,
    SignupRequest,
    SignupResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserResponse,
)

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


def _slugify(name: str) -> str:
    """Generate a URL-safe slug from a company name."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:80] or "company"


def _build_token_response(user_id: str) -> TokenResponse:
    """Issue a fresh access + refresh token pair."""
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a company and its first owner user",
)
def signup(
    payload: SignupRequest,
    db: Annotated[Session, Depends(get_db)],
) -> SignupResponse:
    # Email uniqueness check
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Generate a unique slug
    base_slug = _slugify(payload.company_name)
    slug = base_slug
    suffix = 1
    while db.query(Company).filter(Company.slug == slug).first():
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    company = Company(
        name=payload.company_name,
        slug=slug,
        country=payload.country.upper(),
        sector=payload.sector,
        size=payload.size,
        stage=payload.stage,
        subscription_tier=SubscriptionTier.FREE,
        billing_currency=currency_for_country(payload.country),
    )
    db.add(company)
    db.flush()  # populate company.id without committing

    user = User(
        company_id=company.id,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        job_title=payload.job_title,
        role=UserRole.OWNER,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(company)

    return SignupResponse(
        user=UserResponse.model_validate(user),
        company=CompanyResponse.model_validate(company),
        tokens=_build_token_response(user.id),
    )


@router.post("/login", response_model=TokenResponse, summary="Authenticate and receive tokens")
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        # Same error for both cases — no user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    return _build_token_response(user.id)


@router.post("/refresh", response_model=TokenResponse, summary="Exchange a refresh token for a new pair")
def refresh(
    payload: TokenRefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id = decoded.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )
    return _build_token_response(user.id)


@router.get("/me", response_model=UserResponse, summary="Return the currently authenticated user")
def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(user)
