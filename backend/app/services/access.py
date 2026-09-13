from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Property, PropertyAccess, User
from app.models.enums import PropertyAccessRole, UserRole

MANAGEMENT_ACCESS = {PropertyAccessRole.OWNER, PropertyAccessRole.MANAGER}


def require_account_role(user: User, allowed: set[UserRole]) -> None:
    if user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account role cannot perform this action",
        )


def get_property_membership(
    session: Session, user: User, property_id: UUID
) -> PropertyAccess:
    membership = session.scalar(
        select(PropertyAccess).where(
            PropertyAccess.property_id == property_id,
            PropertyAccess.user_id == user.id,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    return membership


def get_accessible_property(
    session: Session, user: User, property_id: UUID
) -> tuple[Property, PropertyAccess]:
    membership = get_property_membership(session, user, property_id)
    property_ = session.get(Property, property_id)
    if property_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    return property_, membership


def require_property_manager(
    session: Session, user: User, property_id: UUID
) -> tuple[Property, PropertyAccess]:
    property_, membership = get_accessible_property(session, user, property_id)
    if membership.access_role not in MANAGEMENT_ACCESS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Property manager access required",
        )
    return property_, membership
