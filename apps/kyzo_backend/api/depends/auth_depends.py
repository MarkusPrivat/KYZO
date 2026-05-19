"""
Authentication dependencies for JWT validation and user session retrieval.
"""
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import fastapi_settings, UserRole
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.data import User
from apps.kyzo_backend.managers import UserManager
from apps.kyzo_backend.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{fastapi_settings.API_PREFIX_V1}/users/login",
    scopes={
        str(UserRole.STUDENT): "Student",
        str(UserRole.TEACHER): "Teacher",
        str(UserRole.ADMIN): "Admin"
    }
)


async def get_current_user(
        security_scopes: SecurityScopes,
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Session = Depends(get_db)
) -> User:
    """
    Validates the OAuth2 access token and retrieves the corresponding database user.

    This function serves as the foundational authentication dependency for all
    protected endpoints. It decodes the incoming JSON Web Token (JWT), verifies
    its cryptographic signature, extracts the subject (email), and ensures the
    user exists within the persistence layer.

    Args:
        security_scopes (SecurityScopes): Metadata containing the scopes required
            by the calling endpoint, used to build standard OAuth2 headers.
        token (str): The raw Bearer JWT extracted from the HTTP Authorization header.
        db (Session): The active SQLAlchemy database session for user profile lookups.

    Returns:
        User: The authenticated SQLAlchemy user model instance.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is malformed, expired, has an invalid
              signature, lacks a subject claim, or if no matching user is found
              in the database.
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
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

        scope: str = payload.get("scope", "")
        token_scopes = scope.split(" ")

        token_data = TokenData(
            email=email,
            scopes=token_scopes
        )

    except (InvalidTokenError, ValidationError) as error:
        raise credentials_exception from error

    user = UserManager(db).get_user_by_email(token_data.email)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
        current_user: Annotated[User, Security(get_current_user)],
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
