from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    session: DatabaseSession,
    user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
) -> User:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        parsed_user_id = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid demo session",
        ) from exc

    user = session.get(User, parsed_user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Demo session no longer exists",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
