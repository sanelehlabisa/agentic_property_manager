import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Component,
    MaintenanceRecord,
    Property,
    PropertyAccess,
    ServiceCategory,
    User,
)
from app.models.enums import PropertyAccessRole, UserRole
from app.schemas.property import (
    ComponentCreate,
    ComponentUpdate,
    ImportConfirmRequest,
    ImportPreviewResponse,
    ImportPreviewRow,
    MaintenanceRecordCreate,
    PropertyAccessCreate,
    PropertyCreate,
    PropertyRead,
    PropertyUpdate,
)
from app.services.access import (
    get_accessible_property,
    require_account_role,
    require_property_manager,
)

CATEGORY_ALIASES = {
    "pipe": "plumbing",
    "plumber": "plumbing",
    "geyser": "plumbing",
    "wiring": "electrical",
    "electrician": "electrical",
    "aircon": "hvac",
    "air conditioning": "hvac",
    "gutter": "roofing",
    "roof": "roofing",
    "garden": "gardening",
    "clean": "cleaning",
    "repair": "handyman",
}


def list_properties(session: Session, user: User) -> list[PropertyRead]:
    rows = session.execute(
        select(Property, PropertyAccess.access_role)
        .join(PropertyAccess, PropertyAccess.property_id == Property.id)
        .where(PropertyAccess.user_id == user.id)
        .order_by(Property.name)
    ).all()
    return [
        PropertyRead.model_validate(property_).model_copy(
            update={"access_role": access_role}
        )
        for property_, access_role in rows
    ]


def create_property(session: Session, user: User, data: PropertyCreate) -> PropertyRead:
    require_account_role(user, {UserRole.HOMEOWNER, UserRole.MANAGER})
    property_ = Property(**data.model_dump())
    session.add(property_)
    session.flush()
    access_role = (
        PropertyAccessRole.OWNER
        if user.role == UserRole.HOMEOWNER
        else PropertyAccessRole.MANAGER
    )
    session.add(
        PropertyAccess(
            property_id=property_.id,
            user_id=user.id,
            access_role=access_role,
        )
    )
    session.commit()
    session.refresh(property_)
    return PropertyRead.model_validate(property_).model_copy(
        update={"access_role": access_role}
    )


def update_property(
    session: Session, user: User, property_id: UUID, data: PropertyUpdate
) -> PropertyRead:
    property_, membership = require_property_manager(session, user, property_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(property_, field, value)
    session.commit()
    session.refresh(property_)
    return PropertyRead.model_validate(property_).model_copy(
        update={"access_role": membership.access_role}
    )


def delete_property(session: Session, user: User, property_id: UUID) -> None:
    property_, membership = get_accessible_property(session, user, property_id)
    if membership.access_role != PropertyAccessRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a property owner can delete a property",
        )
    session.delete(property_)
    session.commit()


def assign_property_access(
    session: Session, user: User, property_id: UUID, data: PropertyAccessCreate
) -> PropertyAccess:
    _, current_membership = require_property_manager(session, user, property_id)
    target = session.scalar(select(User).where(User.email == str(data.email).lower()))
    if target is None:
        raise HTTPException(
            status_code=404, detail="User must sign in before assignment"
        )

    expected_roles = {
        PropertyAccessRole.OWNER: UserRole.HOMEOWNER,
        PropertyAccessRole.MANAGER: UserRole.MANAGER,
        PropertyAccessRole.TENANT: UserRole.TENANT,
    }
    if target.role != expected_roles[data.access_role]:
        raise HTTPException(
            status_code=422, detail="Account role does not match access role"
        )
    if (
        data.access_role == PropertyAccessRole.OWNER
        and current_membership.access_role != PropertyAccessRole.OWNER
    ):
        raise HTTPException(
            status_code=403, detail="Only an owner can add another owner"
        )

    membership = session.scalar(
        select(PropertyAccess).where(
            PropertyAccess.property_id == property_id,
            PropertyAccess.user_id == target.id,
        )
    )
    if membership is None:
        membership = PropertyAccess(
            property_id=property_id,
            user_id=target.id,
            access_role=data.access_role,
        )
        session.add(membership)
    else:
        membership.access_role = data.access_role
    session.commit()
    session.refresh(membership)
    return membership


def list_property_access(
    session: Session, user: User, property_id: UUID
) -> list[tuple[PropertyAccess, User]]:
    require_property_manager(session, user, property_id)
    return list(
        session.execute(
            select(PropertyAccess, User)
            .join(User, User.id == PropertyAccess.user_id)
            .where(PropertyAccess.property_id == property_id)
            .order_by(PropertyAccess.access_role, User.name)
        ).all()
    )


def validate_category(session: Session, category_code: str) -> ServiceCategory:
    category = session.get(ServiceCategory, category_code)
    if category is None or not category.active:
        raise HTTPException(status_code=422, detail="Unknown service category")
    return category


def list_components(session: Session, user: User, property_id: UUID) -> list[Component]:
    get_accessible_property(session, user, property_id)
    return list(
        session.scalars(
            select(Component)
            .where(Component.property_id == property_id)
            .order_by(Component.name)
        )
    )


def create_component(
    session: Session, user: User, property_id: UUID, data: ComponentCreate
) -> Component:
    require_property_manager(session, user, property_id)
    validate_category(session, data.category_code)
    component = Component(property_id=property_id, **data.model_dump())
    session.add(component)
    session.commit()
    session.refresh(component)
    return component


def update_component(
    session: Session, user: User, component_id: UUID, data: ComponentUpdate
) -> Component:
    component = session.get(Component, component_id)
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    require_property_manager(session, user, component.property_id)
    if data.category_code is not None:
        validate_category(session, data.category_code)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(component, field, value)
    session.commit()
    session.refresh(component)
    return component


def delete_component(session: Session, user: User, component_id: UUID) -> None:
    component = session.get(Component, component_id)
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    require_property_manager(session, user, component.property_id)
    session.delete(component)
    session.commit()


def list_maintenance_records(
    session: Session, user: User, component_id: UUID
) -> list[MaintenanceRecord]:
    component = session.get(Component, component_id)
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    get_accessible_property(session, user, component.property_id)
    return list(
        session.scalars(
            select(MaintenanceRecord)
            .where(MaintenanceRecord.component_id == component_id)
            .order_by(MaintenanceRecord.completed_on.desc())
        )
    )


def create_maintenance_record(
    session: Session, user: User, component_id: UUID, data: MaintenanceRecordCreate
) -> MaintenanceRecord:
    component = session.get(Component, component_id)
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    require_property_manager(session, user, component.property_id)
    record = MaintenanceRecord(component_id=component_id, **data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def preview_import(
    session: Session, user: User, property_id: UUID, csv_text: str
) -> ImportPreviewResponse:
    require_property_manager(session, user, property_id)
    categories = set(session.scalars(select(ServiceCategory.code)))
    components = list(
        session.scalars(select(Component).where(Component.property_id == property_id))
    )
    components_by_name = {component.name.lower(): component for component in components}
    rows: list[ImportPreviewRow] = []

    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    for row_number, raw in enumerate(reader, start=2):
        normalized = {
            str(key).strip().lower(): (value or "").strip()
            for key, value in raw.items()
        }
        errors: list[str] = []
        date_text = normalized.get("completed_on") or normalized.get("date", "")
        cost_text = normalized.get("cost") or normalized.get("amount", "")
        description = normalized.get("description", "")
        category_code = (
            normalized.get("category_code") or normalized.get("category") or ""
        ).lower()
        component_name = (
            normalized.get("component_name") or normalized.get("component") or None
        )

        completed_on: date | None = None
        try:
            completed_on = date.fromisoformat(date_text)
        except ValueError:
            errors.append("Date must use YYYY-MM-DD")

        cost: Decimal | None = None
        try:
            cost = Decimal(cost_text)
            if cost < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            errors.append("Cost must be a non-negative number")
            cost = None

        component = (
            components_by_name.get(component_name.lower()) if component_name else None
        )
        if component is not None:
            category_code = component.category_code
        if not category_code:
            lower_description = description.lower()
            category_code = next(
                (
                    code
                    for keyword, code in CATEGORY_ALIASES.items()
                    if keyword in lower_description
                ),
                "",
            )
        if category_code not in categories:
            errors.append("Choose a valid category")
            category_code = None
        if component_name and component is None:
            errors.append("Component was not found on this property")

        rows.append(
            ImportPreviewRow(
                row_number=row_number,
                completed_on=completed_on,
                cost=cost,
                description=description,
                category_code=category_code,
                component_id=str(component.id) if component else None,
                component_name=component_name,
                errors=errors,
            )
        )

    return ImportPreviewResponse(
        rows=rows,
        valid_count=sum(not row.errors for row in rows),
        error_count=sum(bool(row.errors) for row in rows),
    )


def confirm_import(
    session: Session, user: User, property_id: UUID, data: ImportConfirmRequest
) -> list[MaintenanceRecord]:
    require_property_manager(session, user, property_id)
    records: list[MaintenanceRecord] = []
    for row in data.rows:
        try:
            component_id = UUID(row.component_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid component ID") from exc
        component = session.get(Component, component_id)
        if component is None or component.property_id != property_id:
            raise HTTPException(
                status_code=422, detail="Component is not on this property"
            )
        records.append(
            MaintenanceRecord(
                component_id=component_id,
                completed_on=row.completed_on,
                cost=row.cost,
                provider_name=row.provider_name,
                notes=row.description,
            )
        )
    session.add_all(records)
    session.commit()
    for record in records:
        session.refresh(record)
    return records
