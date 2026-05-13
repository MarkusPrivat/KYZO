from typing import Annotated

import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import fastapi_settings
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.data import User
from apps.kyzo_backend.managers import UserManager
from apps.kyzo_backend.schemas import TokenData


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """
    Validates the access token and retrieves the associated user.

    This function acts as a core dependency for protected routes. It decodes
    the JWT, verifies its integrity, and ensures the user exists in the database.

    Args:
        token (str): The Bearer token provided in the Authorization header.
        db (Session): The database session for user lookup.

    Returns:
        User: The authenticated SQLAlchemy user instance.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid or the user
                       cannot be found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            fastapi_settings.AUTH_SECRET_KEY,
            algorithms=[fastapi_settings.ALGORITHM]
        )

        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception

        token_data = TokenData(email=email)

    except InvalidTokenError as error:
        raise credentials_exception from error

    user = UserManager(db).get_user_by_email(token_data.email)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Ensures that the authenticated user is currently active.

    Use this dependency for routes that require an authenticated user
    whose account has not been disabled.

    Args:
        current_user (User): The user resolved by get_current_user.

    Returns:
        User: The active user instance.

    Raises:
        HTTPException: 400 Bad Request if the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
