from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import ComponentCondition, PropertyAccessRole
from app.models.mixins import TimestampMixin


class Property(TimestampMixin, Base):
    __tablename__ = "properties"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(150))
    address_line_1: Mapped[str] = mapped_column(String(200))
    address_line_2: Mapped[str | None] = mapped_column(String(200))
    suburb: Mapped[str] = mapped_column(String(120), index=True)
    city: Mapped[str] = mapped_column(String(120), index=True)
    postal_code: Mapped[str | None] = mapped_column(String(20))


class PropertyAccess(Base):
    __tablename__ = "property_access"
    __table_args__ = (
        UniqueConstraint("property_id", "user_id", name="uq_property_access_member"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    property_id: Mapped[UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    access_role: Mapped[PropertyAccessRole] = mapped_column(
        Enum(
            PropertyAccessRole,
            name="property_access_role",
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ServiceCategory(TimestampMixin, Base):
    __tablename__ = "service_categories"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(default=True)


class Component(TimestampMixin, Base):
    __tablename__ = "components"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    property_id: Mapped[UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    category_code: Mapped[str] = mapped_column(
        ForeignKey("service_categories.code"), index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    installed_on: Mapped[date | None] = mapped_column(Date)
    condition: Mapped[ComponentCondition] = mapped_column(
        Enum(
            ComponentCondition,
            name="component_condition",
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=ComponentCondition.UNKNOWN,
    )
