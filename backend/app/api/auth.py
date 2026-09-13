from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.auth import (
    AuthResponse,
    EmailAuthRequest,
    SessionResponse,
    UserRead,
)
from app.services.auth import authenticate_email

router = APIRouter(tags=["identity"])


@router.post("/auth/email", response_model=AuthResponse)
def email_authentication(
    request: EmailAuthRequest, session: DatabaseSession
) -> AuthResponse:
    return authenticate_email(session, request)


@router.get("/me", response_model=SessionResponse)
def current_session(user: CurrentUser) -> SessionResponse:
    return SessionResponse(user=UserRead.model_validate(user))
