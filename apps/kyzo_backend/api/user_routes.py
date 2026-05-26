"""
API routes for user management and authentication for the Kyzo backend.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from apps.kyzo_backend.api.depends.role_depends import (
    require_admin,
    require_teacher_or_admin,
    require_student_teacher_or_admin
)
from apps.kyzo_backend.config import slowapi_limiter, UserRole
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


@router.get("/user/", response_model=UserRead)
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
@slowapi_limiter.limit("5/minute")
async def login_for_access_token(
        request: Request,
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
        request (Request): The incoming FastAPI HTTP request instance, required
            by SlowAPI to track client state and enforce the rate limit.
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
            - 429 (Too Many Requests): If the client exceeds the allowed rate limit
              (triggered automatically via SlowAPI).

    Security & Rate Limiting:
        - Public Endpoint (No authentication required to initiate)
        - Rate Limit: Enforced at **5 requests per minute** per client IP.
    """
    access_token = auth_service.authenticate_user(form_data)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register-staff", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_staff(
        user_data: UserCreate,
        current_user: Annotated[User, Depends(require_teacher_or_admin)],
        user_manager: Annotated[UserManager, Depends(get_user_manager)]
):
    """
    Registers a new managed user account (Student, Teacher, or Admin).

    This endpoint serves as an administrative guard for staff-managed user creation.
    It delegates the validation of the role-hierarchy and database persistence
    entirely to the UserManager.

    Args:
        user_data (UserCreate): Validated data container holding the details
            of the user to be created.
        current_user (User): The authenticated staff member (Teacher or Admin)
            initiating the creation request, injected by the role dependency.
        user_manager (UserManager): Injected manager instance handling the domain
            and database operations for user resources.

    Returns:
        UserRead: The newly created and persisted user database record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the authentication token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but lacks teacher/admin
              privileges, OR if a teacher attempts to create an admin account.
            - 409 (Conflict): If the target email address is already associated
              with an existing account.
            - 500 (Internal Server Error): If a technical error or database
              integrity violation occurs during creation.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles (Hierarchical checks enforced)
    """
    return user_manager.add_staff(user_data, current_user.role)


@router.post("/register-user", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
        user_data: UserCreate,
        user_manager: Annotated[UserManager, Depends(get_user_manager)]
):
    """
    Registers a new public student account in the system.

    This endpoint handles the public self-registration flow. It explicitly overrides
    any incoming role parameter to ensure that accounts created through this route
    are strictly assigned the STUDENT role, preventing unauthorized privilege escalation.
    The remaining persistence logic is delegated to the UserManager.

    Args:
        user_data (UserCreate): Validated registration data transfer object
            containing the new student's credentials.
        user_manager (UserManager): Injected manager instance handling user-related
            domain logic and database persistence operations.

    Returns:
        UserRead: The newly created student user record.

    Raises:
        HTTPException:
            - 409 (Conflict): If the provided email address is already associated
              with an existing account.
            - 500 (Internal Server Error): If a technical error or database
              integrity violation occurs during the registration process.

    Security:
        - Public Endpoint (No authentication required)
        - Enforced target role: STUDENT
    """
    user_data.role = UserRole.STUDENT
    return user_manager.add_user(user_data)


@router.put("/user/status", response_model=UserRead)
async def set_current_user_status(
        active: bool,
        current_user: Annotated[User, Depends(require_student_teacher_or_admin)],
        user_manager: Annotated[UserManager, Depends(get_user_manager)]
):
    """
    Allows the authenticated user to toggle their own account activation status.

    This endpoint is primarily used for account self-deactivation. When a user sets
    their status to 'False', they are immediately deactivated.

    CRITICAL WORKFLOW NOTE:
    Since a deactivated user cannot bypass the authentication dependencies on
    subsequent requests, this operation is irreversible by the user themselves.
    Once deactivated, they cannot call this endpoint again to re-activate ('True')
    their account; re-activation requires administrative intervention.

    Args:
        active (bool): The target activation state (typically 'False' for self-deactivation).
        current_user (User): The authenticated user record of the requester,
            injected by the global role dependency.
        user_manager (UserManager): Injected manager instance handling the domain
            and database operations for user resources.

    Returns:
        UserRead: The updated user record reflecting the new activation status.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the authentication token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but lacks any valid system role.
            - 404 (Not Found): If the current user's record does not exist in the database.
            - 500 (Internal Server Error): If a technical database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Open to all authenticated roles: STUDENT, TEACHER, ADMIN
    """
    return user_manager.set_user_status(current_user.id, active, current_user.role)


@router.put("/{user_id}/status", response_model=UserRead)
async def set_user_status(
        current_user: Annotated[User, Depends(require_teacher_or_admin)],
        user_id: int,
        active: bool,
        user_manager: UserManager = Depends(get_user_manager)
):
    """
    Toggles the activation status of a specific user.

    Updates the 'is_active' flag for the given user ID. This operation is
    handled by the UserManager, which ensures the user exists before
    committing the status change to the database.

    Args:
        current_user (User): The authenticated teacher's or administrator's user
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
    return user_manager.set_user_status(user_id, active, current_user.role)


@router.put("/user/edit", response_model=UserRead)
async def update_current_user(
        update_data: UserUpdate,
        current_user: Annotated[User, Depends(require_student_teacher_or_admin)],
        user_manager: Annotated[UserManager, Depends(get_user_manager)]
):
    """
    Updates the authenticated user's own profile information.

    This endpoint orchestrates a partial profile update (PATCH-like behavior via PUT)
    for the currently logged-in user. It allows any authenticated user—regardless of
    their system role—to update their account details.

    Data integrity checks—such as ensuring email uniqueness if the email is modified—and
    database persistence are delegated entirely to the UserManager.

    Args:
        update_data (UserUpdate): Pydantic data transfer object containing the
            specific profile fields to be modified.
        current_user (User): The authenticated user record of the requester
            initiating the self-update, injected by the global role dependency.
        user_manager (UserManager): Injected manager instance handling the domain
            and database operations for user resources.

    Returns:
        UserRead: The updated and refreshed user record reflecting the modifications.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the authentication token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but lacks any valid system role.
            - 409 (Conflict): If the requested new email address is already registered
              by another account in the system.
            - 500 (Internal Server Error): If a technical error or database transaction
              failure occurs during the update process.

    Security:
        - Bearer Auth (JWT)
        - Open to all authenticated roles: STUDENT, TEACHER, ADMIN
    """
    return user_manager.update_user(current_user.id, update_data)


@router.put("/{user_id}/edit", response_model=UserRead)
async def update_user(
        current_user: Annotated[User, Depends(require_teacher_or_admin)],
        user_id: int,
        update_data: UserUpdate,
        user_manager: Annotated[UserManager, Depends(get_user_manager)]
):
    """
    Administratively updates another user's profile information.

    This endpoint coordinates a partial update for a specific user record identified
    by their unique database ID. It enforces strict staff-level access boundaries
    and delegates identity verification, role-hierarchy enforcement, and data integrity
    checks (such as email uniqueness) entirely to the UserManager.

    Args:
        user_id (int): The unique database identifier of the target user whose
            profile is to be updated.
        update_data (UserUpdate): Pydantic data transfer object containing the
            specific profile fields to be modified.
        current_user (User): The authenticated staff member (Teacher or Admin)
            initiating the administrative update, injected by the global role dependency.
        user_manager (UserManager): Injected manager instance handling the domain
            and database operations for user resources.

    Returns:
        UserRead: The updated and refreshed user database record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the authentication token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but lacks staff privileges,
              OR if a teacher attempts to modify an account above their privilege level.
            - 404 (Not Found): If no user record matches the provided user_id.
            - 409 (Conflict): If the requested new email address is already occupied
              by another account in the system.
            - 500 (Internal Server Error): If a technical error or database transaction
              failure occurs during the update process.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles (Hierarchical checks enforced)
    """
    return user_manager.update_user(user_id, update_data, current_user.role)
