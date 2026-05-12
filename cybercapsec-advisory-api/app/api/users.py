"""Team management endpoints (list / invite / update / change password).

Note: there is no SMTP infrastructure yet, so "invite" creates the user with
a generated temporary password returned in the response. The owner shares it
out-of-band; the new user changes it via /users/me/password on first login.
"""
import secrets
import string
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.database import get_db
from app.deps import get_current_company, get_current_user, require_role
from app.models import Company, User, UserRole
from app.schemas import (
    PasswordChangeRequest,
    UserInviteRequest,
    UserInviteResponse,
    UserSummaryOut,
    UserUpdateRequest,
)


router = APIRouter(prefix="/users", tags=["users"])


_ADMINS = (UserRole.OWNER, UserRole.ADMIN)


def _generate_temp_password() -> str:
    """A 16-char password drawn from a URL-safe alphabet (no ambiguous chars)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(16))


@router.get(
    "",
    response_model=list[UserSummaryOut],
    summary="List users in the current company",
)
def list_users(
    company: Annotated[Company, Depends(get_current_company)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserSummaryOut]:
    _ = user
    rows = (
        db.query(User)
        .filter(User.company_id == company.id)
        .order_by(User.created_at.asc())
        .all()
    )
    return [UserSummaryOut.model_validate(u) for u in rows]


@router.post(
    "",
    response_model=UserInviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a new user (creates account with temp password)",
)
def invite_user(
    payload: UserInviteRequest,
    company: Annotated[Company, Depends(get_current_company)],
    actor: Annotated[User, Depends(require_role(*_ADMINS))],
    db: Annotated[Session, Depends(get_db)],
) -> UserInviteResponse:
    if payload.role == UserRole.OWNER and actor.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can grant the owner role",
        )

    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    temp_password = _generate_temp_password()
    new_user = User(
        company_id=company.id,
        email=payload.email.lower(),
        hashed_password=hash_password(temp_password),
        full_name=payload.full_name,
        job_title=payload.job_title,
        role=payload.role,
        is_active=True,
        is_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserInviteResponse(
        user=UserSummaryOut.model_validate(new_user),
        temporary_password=temp_password,
    )


@router.patch(
    "/{user_id}",
    response_model=UserSummaryOut,
    summary="Update a user's profile, role, or active state",
)
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    company: Annotated[Company, Depends(get_current_company)],
    actor: Annotated[User, Depends(require_role(*_ADMINS))],
    db: Annotated[Session, Depends(get_db)],
) -> UserSummaryOut:
    target = (
        db.query(User)
        .filter(User.id == user_id, User.company_id == company.id)
        .first()
    )
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Role mutations
    if payload.role is not None and payload.role != target.role:
        if actor.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can change roles",
            )
        if target.role == UserRole.OWNER and payload.role != UserRole.OWNER:
            # Don't allow downgrading the last owner
            other_owners = (
                db.query(User)
                .filter(
                    User.company_id == company.id,
                    User.role == UserRole.OWNER,
                    User.id != target.id,
                )
                .count()
            )
            if other_owners == 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot remove the last owner",
                )
        target.role = payload.role

    if payload.full_name is not None:
        target.full_name = payload.full_name
    if payload.job_title is not None:
        target.job_title = payload.job_title
    if payload.is_active is not None:
        if not payload.is_active and target.role == UserRole.OWNER:
            other_owners = (
                db.query(User)
                .filter(
                    User.company_id == company.id,
                    User.role == UserRole.OWNER,
                    User.is_active.is_(True),
                    User.id != target.id,
                )
                .count()
            )
            if other_owners == 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot deactivate the last active owner",
                )
        target.is_active = payload.is_active

    db.commit()
    db.refresh(target)
    return UserSummaryOut.model_validate(target)


@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change your own password",
)
def change_my_password(
    payload: PasswordChangeRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    user.hashed_password = hash_password(payload.new_password)
    user.is_verified = True
    db.commit()
    return None
