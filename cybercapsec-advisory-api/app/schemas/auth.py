"""Authentication-related Pydantic schemas."""
from pydantic import BaseModel, EmailStr, Field

from app.models.company import CompanySize, CompanyStage, Sector, UserRole


class TokenResponse(BaseModel):
    """Returned on login / refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SignupRequest(BaseModel):
    """Initial signup creates a user AND a company (one-shot onboarding)."""
    # User
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    job_title: str | None = Field(default=None, max_length=255)

    # Company
    company_name: str = Field(min_length=2, max_length=255)
    country: str = Field(default="NG", min_length=2, max_length=2)
    sector: Sector = Sector.OTHER
    size: CompanySize = CompanySize.MICRO
    stage: CompanyStage = CompanyStage.SEED


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    job_title: str | None
    role: UserRole
    company_id: str
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}


class CompanyResponse(BaseModel):
    id: str
    name: str
    slug: str
    country: str
    sector: Sector
    size: CompanySize
    stage: CompanyStage
    website: str | None
    description: str | None
    subscription_tier: str
    is_active: bool

    model_config = {"from_attributes": True}


class SignupResponse(BaseModel):
    user: UserResponse
    company: CompanyResponse
    tokens: TokenResponse
