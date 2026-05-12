"""Shared FastAPI dependencies."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import decode_token
from app.database import get_db
from app.models import Company, User, UserRole

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the current authenticated user from the bearer token."""
    if not token:
        raise CredentialsException

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise CredentialsException
        user_id = payload.get("sub")
        if not user_id:
            raise CredentialsException
    except JWTError:
        raise CredentialsException

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise CredentialsException

    return user


def get_current_company(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Company:
    """Return the company tied to the current user."""
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company or not company.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company is not active",
        )
    return company


def require_role(*allowed_roles: UserRole):
    """Dependency factory enforcing a minimum role on a route."""

    def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
        return user

    return checker


# Roles allowed to mutate company workbench data. AUDITOR is read-only.
WRITER_ROLES = (UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER)


def require_writer():
    """Side-effect dependency: rejects auditor (or any future read-only role)."""
    return require_role(*WRITER_ROLES)

