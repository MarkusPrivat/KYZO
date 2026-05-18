"""
API routes for user management and authentication for the Kyzo backend.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from apps.kyzo_backend.api.depends.role_depends import (
    require_admin,
    require_teacher_or_admin,
    require_student_teacher_or_admin
)
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.data import User
from apps.kyzo_backend.managers import UserManager
from apps.kyzo_backend.schemas import Token, UserCreate, UserRead, UserUpdate
from apps.kyzo_backend.services.auth_service import AuthService

router = APIRouter(
    prefix="/users",
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
        current_user: Annotated[User, Depends(require_student_teacher_or_admin)],
) -> User:
    """
    Retrieves the profile information of the currently authenticated user.

    This endpoint acts as a protected resource that requires a valid JWT access
    token. It leverages the RBAC dependency layer to ensure the user is
    authenticated, active, and belongs to a recognized system role.

    Args:
        current_user (User): The authenticated and active user instance
            resolved by the role dependency.

    Returns:
        User: The SQLAlchemy User model instance containing the account details,
            which is automatically serialized into the UserRead Pydantic schema.

    Security:
        - Bearer Auth (JWT)
        - Requires an active account
        - Authorized roles: STUDENT, TEACHER, ADMIN
    """
    return current_user


@router.get("/list-all", response_model=list[UserRead])
async def get_all_users(
        _current_user: Annotated[User, Depends(require_admin)],
        user_manager: UserManager = Depends(get_user_manager)
):
    """
    Retrieves a complete list of all registered users.

    This endpoint orchestrates the retrieval of the entire user base via the
    UserManager. It returns a collection of user profiles formatted according
    to the UserRead schema.

    Args:
        _current_user (User): The authenticated administrator's user record,
            used strictly to enforce administrative access.
        user_manager (UserManager): Injected manager instance for database
            operations.

    Returns:
        list[UserRead]: A list of all registered user profile records.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but lacks admin privileges.
            - 404 (Not Found): If the database contains no user records.
            - 500 (Internal Server Error): If a database transaction fails.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: ADMIN role only
    """
    return user_manager.get_all_users()


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        user_id: int,
        user_manager: Annotated[UserManager, Depends(get_user_manager)]
):
    """
    Retrieves the profile details of a specific user by their unique ID.

    This endpoint delegates the retrieval logic to the UserManager. If the user
    is found, the record is automatically serialized into the UserRead format.
    Error handling (404 for missing records or 500 for database issues) is
    managed internally by the UserManager.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        user_id (int): The unique database identifier of the target user.
        user_manager (UserManager): Injected manager instance for database
            operations.

    Returns:
        UserRead: The sanitized user profile data.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If the user_id does not exist in the database.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
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
    the AuthService. Upon successful authentication, it generates a signed
    JSON Web Token (JWT) that encodes the user's identification and identity
    scopes for subsequent authorized requests.

    Args:
        form_data (OAuth2PasswordRequestForm): FastAPI-provided container
            extracting 'username' (email) and 'password' from the form-data request body.
        auth_service (AuthService): Injected service handling the core authentication
            and cryptographic verification logic.

    Returns:
        Token: A Pydantic schema containing the generated 'access_token' string
            and the 'token_type' (bearer).

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the email is not found, the password
              is incorrect, or the account is otherwise invalid.
    """
    access_token = auth_service.authenticate_user(form_data)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
        user_data: UserCreate,
        user_manager: UserManager = Depends(get_user_manager)
):
    """
    TODO: Role base check for new teacher and admins
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
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        user_id: int,
        active: bool,
        user_manager: UserManager = Depends(get_user_manager)
):
    """
    TODO: Create a me endpoint version
    TODO: Teacher are not allowed to edit admins
    Toggles the activation status of a specific user.

    Updates the 'is_active' flag for the given user ID. This operation is
    handled by the UserManager, which ensures the user exists before
    committing the status change to the database.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        user_id (int): The unique database identifier of the target user.
        active (bool): The target status (True for active, False for inactive).
        user_manager (UserManager): Injected manager instance for database
            operations.

    Returns:
        UserRead: The updated user record reflecting the new status.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If the user_id does not exist in the database.
            - 500 (Internal Server Error): If the database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return user_manager.set_user_status(user_id, active)


@router.put("/{user_id}/edit", response_model=UserRead)
async def update_user(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        user_id: int,
        update_data: UserUpdate,
        user_manager: UserManager = Depends(get_user_manager)
):
    """
    TODO: Create a me endpoint version
    TODO: Teacher are not allowed to edit admins
    Updates an existing user's profile information.

    This endpoint coordinates a partial update. It delegates identity
    verification and data integrity checks (like email uniqueness) to the
    UserManager. If the email is being changed, the system ensures it is
    not already occupied by another account.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        user_id (int): Unique database identifier of the user to be updated.
        update_data (UserUpdate): Pydantic container for the fields to be modified.
        user_manager (UserManager): Injected manager instance for user database
            operations.

    Returns:
        UserRead: The updated and refreshed user record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If no user exists with the given ID.
            - 409 (Conflict): If the requested new email address is already taken.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return user_manager.update_user(user_id, update_data)
