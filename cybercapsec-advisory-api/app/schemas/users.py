"""Team management schemas."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.company import UserRole


class UserSummaryOut(BaseModel):
    """User row for team listings."""
    id: str
    email: EmailStr
    full_name: str
    job_title: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserInviteRequest(BaseModel):
    """Owner/admin creates a new user.

    No SMTP yet, so the API returns a temporary password the owner can copy
    and pass to the new user out-of-band. The user can change it after login.
    """
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    job_title: str | None = Field(default=None, max_length=255)
    role: UserRole = UserRole.MEMBER


class UserInviteResponse(BaseModel):
    user: UserSummaryOut
    temporary_password: str = Field(
        description="One-time password to share with the invitee out-of-band. "
        "They should change it on first login."
    )


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    job_title: str | None = Field(default=None, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
