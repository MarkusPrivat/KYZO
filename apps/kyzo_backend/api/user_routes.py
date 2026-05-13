from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .auth_depends import get_current_active_user
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.data import User
from apps.kyzo_backend.schemas import Token, UserCreate, UserRead, UserUpdate
from apps.kyzo_backend.managers import UserManager
from apps.kyzo_backend.services.auth_service import AuthService



router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)

def get_user_manager(db: Session = Depends(get_db)) -> UserManager:
    """
    Dependency provider for the UserManager.

    This function facilitates the injection of a UserManager instance into
    API routes. It automatically retrieves the database session via
    FastAPI's dependency system.

    Args:
        db (Session): The SQLAlchemy database session.

    Returns:
        UserManager: A new instance of the UserManager initialized with the DB session.
    """
    return UserManager(db)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Dependency provider for the AuthService.

    This function serves as a bridge for FastAPI's dependency injection system.
    It ensures that each request receives a fresh instance of AuthService,
    automatically initialized with the current database session.

    Args:
        db (Session): The SQLAlchemy database session provided by 'get_db'.

    Returns:
        AuthService: An initialized instance of the authentication service.
    """
    return AuthService(db)



@router.get("/users/me/", response_model=UserRead)
async def get_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Retrieves the profile information of the currently authenticated user.

    This endpoint acts as a protected resource that requires a valid
    JWT access token. It leverages the dependency injection system to
    verify the token and ensure the user's account is active.

    Returns:
        User: The SQLAlchemy User model containing the account details,
              automatically serialized into a 'UserRead' Pydantic schema.

    Security:
        - Bearer Auth (JWT)
        - Requires an active account
    """
    return current_user


@router.get("/list-all", response_model=list[UserRead])
async def get_all_users(user_manager: UserManager = Depends(get_user_manager)):
    """
    Retrieves a complete list of all registered users.

    This endpoint orchestrates the retrieval of the entire user base
    via the UserManager. It returns a collection of user profiles
    formatted according to the UserRead schema.

    Args:
        user_manager (UserManager): Injected manager via FastAPI Depends.

    Returns:
        list[UserRead]: A list of all user profile records.

    Raises:
        HTTPException:
            - 404 (Not Found): If the database contains no user records.
            - 500 (Internal Server Error): If a database transaction fails.
    """
    return user_manager.get_all_users()


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, user_manager: UserManager = Depends(get_user_manager)):
    """
    Retrieves the profile details of a specific user by their unique ID.

    This endpoint delegates the retrieval logic to the UserManager. If the user
    is found, the record is automatically serialized into the UserRead format.
    Error handling (404 for missing records or 500 for database issues) is
    managed internally by the UserManager.

    Args:
        user_id (int): The unique database identifier of the user.
        user_manager (UserManager): Injected manager instance via FastAPI Depends.

    Returns:
        UserRead: The sanitized user profile data.

    Raises:
        HTTPException:
            - 404 (Not Found): If the user_id does not exist.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return user_manager.get_user_by_id(user_id)


@router.post("/login")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> Token:
    """
    Authenticates a user and returns an OAuth2 access token.

    This endpoint validates the user's credentials (email and password) via
    the AuthService. Upon successful authentication, it generates a JSON Web
    Token (JWT) that can be used for subsequent authorized requests.

    Args:
        form_data (OAuth2PasswordRequestForm): FastAPI-provided container
            extracting 'username' (email) and 'password' from the request body.
        auth_service (AuthService): Injected service to handle the auth logic.

    Returns:
        Token: A container containing the 'access_token' string and 'token_type'.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the credentials are invalid or the
              user does not exist.
    """
    access_token = auth_service.authenticate_user(
        form_data.username,
        form_data.password
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
        user_data: UserCreate,
        user_manager: UserManager = Depends(get_user_manager)):
    """
    Registers a new user account in the system.

    This endpoint delegates the entire registration process to the UserManager,
    including existence checks, data normalization, and persistence.

    Args:
        user_data (UserCreate): The validated registration data.
        user_manager (UserManager): Injected manager for user-related operations.

    Returns:
        UserRead: The newly created user record.

    Raises:
        HTTPException:
            - 409 (Conflict): If the email is already associated with an account.
            - 500 (Internal Server Error): If a database or system error occurs.
    """
    return user_manager.add_user(user_data)


@router.put("/{user_id}/status", response_model=UserRead)
async def set_user_status(
        user_id: int,
        active: bool,
        user_manager: UserManager = Depends(get_user_manager)):
    """
    Toggles the activation status of a specific user.

    Updates the 'is_active' flag for the given user ID. This operation is
    handled by the UserManager, which ensures the user exists before
    committing the status change to the database.

    Args:
        user_id (int): The unique ID of the user to be updated.
        active (bool): The target status (True for active, False for inactive).
        user_manager (UserManager): Injected manager instance via FastAPI Depends.

    Returns:
        UserRead: The updated user record with the new status.

    Raises:
        HTTPException:
            - 404 (Not Found): If the user ID does not exist.
            - 500 (Internal Server Error): If the database update fails.
    """
    return user_manager.set_user_status(user_id, active)


@router.put("/{user_id}/edit", response_model=UserRead)
async def update_user(
        user_id: int,
        update_data: UserUpdate,
        user_manager: UserManager = Depends(get_user_manager)):
    """
    Updates an existing user's profile information.

    This endpoint coordinates a partial update. It delegates identity
    verification and data integrity checks (like email uniqueness) to the
    UserManager. If the email is being changed, the system ensures it is
    not already occupied by another account.

    Args:
        user_id (int): Unique identifier of the user to be updated.
        update_data (UserUpdate): Container for the fields to be modified.
        user_manager (UserManager): Injected manager instance for user logic.

    Returns:
        UserRead: The updated and refreshed user record.

    Raises:
        HTTPException:
            - 404 (Not Found): If no user exists with the given ID.
            - 409 (Conflict): If the requested new email address is already taken.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return user_manager.update_user(user_id, update_data)
