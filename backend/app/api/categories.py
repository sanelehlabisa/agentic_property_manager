from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DatabaseSession
from app.models import ServiceCategory
from app.schemas.property import ServiceCategoryRead

router = APIRouter(prefix="/service-categories", tags=["service categories"])


@router.get("", response_model=list[ServiceCategoryRead])
def list_service_categories(
    session: DatabaseSession, user: CurrentUser
) -> list[ServiceCategory]:
    return list(
        session.scalars(
            select(ServiceCategory)
            .where(ServiceCategory.active.is_(True))
            .order_by(ServiceCategory.name)
        )
    )
