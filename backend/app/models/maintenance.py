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
from app.models.enums import (
    PredictionStatus,
    PredictionUrgency,
    ReportStatus,
    ReportUrgency,
)
from app.models.mixins import TimestampMixin


class MaintenanceRule(TimestampMixin, Base):
    __tablename__ = "maintenance_rules"
    __table_args__ = (
        UniqueConstraint("category_code", name="uq_maintenance_rule_category"),
        CheckConstraint("interval_months > 0", name="positive_interval_months"),
        CheckConstraint("warning_days >= 0", name="nonnegative_warning_days"),
        CheckConstraint("default_cost >= 0", name="nonnegative_default_cost"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    category_code: Mapped[str] = mapped_column(
        ForeignKey("service_categories.code"), index=True
    )
    interval_months: Mapped[int]
    warning_days: Mapped[int]
    default_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(default=True)


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    __table_args__ = (
        CheckConstraint("cost >= 0", name="nonnegative_maintenance_cost"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    component_id: Mapped[UUID] = mapped_column(
        ForeignKey("components.id", ondelete="CASCADE"), index=True
    )
    completed_on: Mapped[date] = mapped_column(Date, index=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    provider_name: Mapped[str | None] = mapped_column(String(150))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Prediction(TimestampMixin, Base):
    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint("estimated_cost >= 0", name="nonnegative_estimated_cost"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    component_id: Mapped[UUID] = mapped_column(
        ForeignKey("components.id", ondelete="CASCADE"), index=True
    )
    maintenance_rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_rules.id"), index=True
    )
    due_date: Mapped[date] = mapped_column(Date, index=True)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    urgency: Mapped[PredictionUrgency] = mapped_column(
        Enum(
            PredictionUrgency,
            name="prediction_urgency",
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        )
    )
    explanation: Mapped[str] = mapped_column(String(500))
    status: Mapped[PredictionStatus] = mapped_column(
        Enum(
            PredictionStatus,
            name="prediction_status",
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=PredictionStatus.ACTIVE,
        index=True,
    )


class IssueReport(TimestampMixin, Base):
    __tablename__ = "issue_reports"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    property_id: Mapped[UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    reporter_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    component_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("components.id", ondelete="SET NULL"), index=True
    )
    category_code: Mapped[str] = mapped_column(
        ForeignKey("service_categories.code"), index=True
    )
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    urgency: Mapped[ReportUrgency] = mapped_column(
        Enum(
            ReportUrgency,
            name="report_urgency",
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=ReportUrgency.MEDIUM,
    )
    status: Mapped[ReportStatus] = mapped_column(
        Enum(
            ReportStatus,
            name="report_status",
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=ReportStatus.PENDING_APPROVAL,
        index=True,
    )
    review_reason: Mapped[str | None] = mapped_column(String(500))
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
