from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.property import (
    ComponentCreate,
    ComponentRead,
    ComponentUpdate,
    ImportConfirmRequest,
    ImportPreviewRequest,
    ImportPreviewResponse,
    MaintenanceRecordCreate,
    MaintenanceRecordRead,
    PropertyAccessCreate,
    PropertyAccessRead,
    PropertyCreate,
    PropertyRead,
    PropertyUpdate,
)
from app.services import properties as service
from app.services.access import get_accessible_property

router = APIRouter(tags=["properties"])


@router.get("/properties", response_model=list[PropertyRead])
def get_properties(session: DatabaseSession, user: CurrentUser) -> list[PropertyRead]:
    return service.list_properties(session, user)


@router.post(
    "/properties", response_model=PropertyRead, status_code=status.HTTP_201_CREATED
)
def post_property(
    data: PropertyCreate, session: DatabaseSession, user: CurrentUser
) -> PropertyRead:
    return service.create_property(session, user, data)


@router.get("/properties/{property_id}", response_model=PropertyRead)
def get_property(
    property_id: UUID, session: DatabaseSession, user: CurrentUser
) -> PropertyRead:
    property_, membership = get_accessible_property(session, user, property_id)
    return PropertyRead.model_validate(property_).model_copy(
        update={"access_role": membership.access_role}
    )


@router.patch("/properties/{property_id}", response_model=PropertyRead)
def patch_property(
    property_id: UUID,
    data: PropertyUpdate,
    session: DatabaseSession,
    user: CurrentUser,
) -> PropertyRead:
    return service.update_property(session, user, property_id, data)


@router.delete("/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_property(
    property_id: UUID, session: DatabaseSession, user: CurrentUser
) -> Response:
    service.delete_property(session, user, property_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/properties/{property_id}/access", response_model=list[PropertyAccessRead])
def get_property_access(
    property_id: UUID, session: DatabaseSession, user: CurrentUser
) -> list[PropertyAccessRead]:
    rows = service.list_property_access(session, user, property_id)
    return [
        PropertyAccessRead(
            id=membership.id,
            user_id=member.id,
            email=member.email,
            name=member.name,
            access_role=membership.access_role,
        )
        for membership, member in rows
    ]


@router.post(
    "/properties/{property_id}/access",
    response_model=PropertyAccessRead,
    status_code=status.HTTP_201_CREATED,
)
def post_property_access(
    property_id: UUID,
    data: PropertyAccessCreate,
    session: DatabaseSession,
    user: CurrentUser,
) -> PropertyAccessRead:
    membership = service.assign_property_access(session, user, property_id, data)
    member = session.get_one(type(user), membership.user_id)
    return PropertyAccessRead(
        id=membership.id,
        user_id=member.id,
        email=member.email,
        name=member.name,
        access_role=membership.access_role,
    )


@router.get("/properties/{property_id}/components", response_model=list[ComponentRead])
def get_components(property_id: UUID, session: DatabaseSession, user: CurrentUser):
    return service.list_components(session, user, property_id)


@router.post(
    "/properties/{property_id}/components",
    response_model=ComponentRead,
    status_code=status.HTTP_201_CREATED,
)
def post_component(
    property_id: UUID,
    data: ComponentCreate,
    session: DatabaseSession,
    user: CurrentUser,
):
    return service.create_component(session, user, property_id, data)


@router.patch("/components/{component_id}", response_model=ComponentRead)
def patch_component(
    component_id: UUID,
    data: ComponentUpdate,
    session: DatabaseSession,
    user: CurrentUser,
):
    return service.update_component(session, user, component_id, data)


@router.delete("/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_component(
    component_id: UUID, session: DatabaseSession, user: CurrentUser
) -> Response:
    service.delete_component(session, user, component_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/components/{component_id}/maintenance-records",
    response_model=list[MaintenanceRecordRead],
)
def get_maintenance_records(
    component_id: UUID, session: DatabaseSession, user: CurrentUser
):
    return service.list_maintenance_records(session, user, component_id)


@router.post(
    "/components/{component_id}/maintenance-records",
    response_model=MaintenanceRecordRead,
    status_code=status.HTTP_201_CREATED,
)
def post_maintenance_record(
    component_id: UUID,
    data: MaintenanceRecordCreate,
    session: DatabaseSession,
    user: CurrentUser,
):
    return service.create_maintenance_record(session, user, component_id, data)


@router.post(
    "/properties/{property_id}/maintenance-imports/preview",
    response_model=ImportPreviewResponse,
)
def post_import_preview(
    property_id: UUID,
    data: ImportPreviewRequest,
    session: DatabaseSession,
    user: CurrentUser,
) -> ImportPreviewResponse:
    return service.preview_import(session, user, property_id, data.csv_text)


@router.post(
    "/properties/{property_id}/maintenance-imports/confirm",
    response_model=list[MaintenanceRecordRead],
    status_code=status.HTTP_201_CREATED,
)
def post_import_confirmation(
    property_id: UUID,
    data: ImportConfirmRequest,
    session: DatabaseSession,
    user: CurrentUser,
):
    return service.confirm_import(session, user, property_id, data)
