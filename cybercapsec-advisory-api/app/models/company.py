"""Company (tenant) and user models."""
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class CompanySize(str, PyEnum):
    SOLO = "solo"  # 1
    MICRO = "micro"  # 2-10
    SMALL = "small"  # 11-50
    MEDIUM = "medium"  # 51-200
    LARGE = "large"  # 201-1000
    ENTERPRISE = "enterprise"  # 1000+


class CompanyStage(str, PyEnum):
    IDEA = "idea"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C_PLUS = "series_c_plus"
    BOOTSTRAPPED = "bootstrapped"
    ESTABLISHED = "established"


class Sector(str, PyEnum):
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    EDTECH = "edtech"
    ECOMMERCE = "ecommerce"
    LOGISTICS = "logistics"
    AGRITECH = "agritech"
    SAAS = "saas"
    INSURTECH = "insurtech"
    PROPTECH = "proptech"
    OTHER = "other"


class SubscriptionTier(str, PyEnum):
    FREE = "free"
    STARTER = "starter"
    GROWTH = "growth"
    AUDIT_READY = "audit_ready"


class BillingCurrency(str, PyEnum):
    """Currencies Paystack supports for our markets."""
    NGN = "NGN"
    KES = "KES"
    ZAR = "ZAR"
    GHS = "GHS"
    USD = "USD"


# Country -> currency mapping. Sealed at signup, never changed.
COUNTRY_TO_CURRENCY: dict[str, BillingCurrency] = {
    "NG": BillingCurrency.NGN,
    "KE": BillingCurrency.KES,
    "ZA": BillingCurrency.ZAR,
    "GH": BillingCurrency.GHS,
}


def currency_for_country(country: str) -> BillingCurrency:
    """Map ISO-3166-1 alpha-2 country code to billing currency. USD fallback."""
    return COUNTRY_TO_CURRENCY.get(country.upper(), BillingCurrency.USD)


class Company(Base, UUIDPKMixin, TimestampMixin):
    """A customer organization (tenant)."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="NG")  # ISO-3166-1 alpha-2
    sector: Mapped[Sector] = mapped_column(Enum(Sector), nullable=False, default=Sector.OTHER)
    size: Mapped[CompanySize] = mapped_column(Enum(CompanySize), nullable=False, default=CompanySize.MICRO)
    stage: Mapped[CompanyStage] = mapped_column(Enum(CompanyStage), nullable=False, default=CompanyStage.SEED)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Subscription — Paystack-backed
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE
    )
    billing_currency: Mapped[BillingCurrency] = mapped_column(
        Enum(BillingCurrency), nullable=False, default=BillingCurrency.NGN
    )
    paystack_customer_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    paystack_subscription_code: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="company", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(  # type: ignore  # noqa
        "Assessment", back_populates="company", cascade="all, delete-orphan"
    )


class UserRole(str, PyEnum):
    OWNER = "owner"  # full access including billing
    ADMIN = "admin"  # full access except billing
    MEMBER = "member"  # standard user
    AUDITOR = "auditor"  # read-only access to evidence


class User(Base, UUIDPKMixin, TimestampMixin):
    """A user belonging to a company."""

    __tablename__ = "users"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    company: Mapped[Company] = relationship("Company", back_populates="users")
