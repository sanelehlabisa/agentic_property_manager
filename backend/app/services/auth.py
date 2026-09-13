from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User
from app.schemas.auth import AuthResponse, EmailAuthRequest, UserRead


def authenticate_email(session: Session, request: EmailAuthRequest) -> AuthResponse:
    email = str(request.email).strip().lower()
    user = session.scalar(select(User).where(func.lower(User.email) == email))

    if user is None and (request.name is None or request.role is None):
        return AuthResponse(requires_onboarding=True)

    if user is None:
        user = User(email=email, name=request.name.strip(), role=request.role)
        session.add(user)
        session.commit()
        session.refresh(user)

    return AuthResponse(
        requires_onboarding=False,
        token=str(user.id),
        user=UserRead.model_validate(user),
    )
