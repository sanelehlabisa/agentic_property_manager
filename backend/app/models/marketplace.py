from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import BidStatus, JobStatus
from app.models.mixins import TimestampMixin


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("budget >= 0", name="nonnegative_job_budget"),
        CheckConstraint(
            "((issue_report_id IS NOT NULL AND prediction_id IS NULL) OR "
            "(issue_report_id IS NULL AND prediction_id IS NOT NULL))",
            name="exactly_one_job_source",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    property_id: Mapped[UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    category_code: Mapped[str] = mapped_column(
        ForeignKey("service_categories.code"), index=True
    )
    issue_report_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("issue_reports.id"), unique=True
    )
    prediction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("predictions.id"), unique=True
    )
    description: Mapped[str] = mapped_column(Text)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    public_location: Mapped[str] = mapped_column(String(250), index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name="job_status",
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=JobStatus.OPEN,
        index=True,
    )
    approved_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProviderProfile(TimestampMixin, Base):
    __tablename__ = "provider_profiles"
    __table_args__ = (
        CheckConstraint("service_radius_km > 0", name="positive_service_radius"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="valid_provider_rating"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    business_name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(String(1000))
    phone: Mapped[str] = mapped_column(String(40))
    suburb: Mapped[str] = mapped_column(String(120), index=True)
    city: Mapped[str] = mapped_column(String(120), index=True)
    service_radius_km: Mapped[int] = mapped_column(default=25)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0"))


class ProviderService(TimestampMixin, Base):
    __tablename__ = "provider_services"
    __table_args__ = (
        UniqueConstraint(
            "provider_profile_id", "category_code", name="uq_provider_service_category"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    provider_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("provider_profiles.id", ondelete="CASCADE"), index=True
    )
    category_code: Mapped[str] = mapped_column(
        ForeignKey("service_categories.code"), index=True
    )
    description: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(default=True)


class Bid(TimestampMixin, Base):
    __tablename__ = "bids"
    __table_args__ = (
        UniqueConstraint("job_id", "provider_profile_id", name="uq_bid_provider_job"),
        CheckConstraint("amount > 0", name="positive_bid_amount"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    provider_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("provider_profiles.id"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    message: Mapped[str] = mapped_column(String(1000))
    available_on: Mapped[date] = mapped_column(Date)
    status: Mapped[BidStatus] = mapped_column(
        Enum(
            BidStatus,
            name="bid_status",
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=BidStatus.SUBMITTED,
        index=True,
    )
