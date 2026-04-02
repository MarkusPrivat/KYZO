from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import UserMessages
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.schemas import UserCreate, UserRead, UserUpdate
from apps.kyzo_backend.managers import UserManager


router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)



@router.get("/list-all", response_model=list[UserRead])
async def get_all_users(db: Session = Depends(get_db)):
    """
    Retrieves a complete list of all registered users.

    This endpoint is primarily for administrative purposes to oversee
    the user base. It returns the public profile data (UserRead) for
    every account in the system.

    Args:
        db (Session): Injected database session.

    Returns:
        list[UserRead]: A list of all user profiles.

    Raises:
        HTTPException: 404 if no users exist in the database.
        HTTPException: 500 if a database error occurs.
    """
    user_manager = UserManager(db)

    success, result = user_manager.get_all_users()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=UserMessages.NO_USERS
        )

    return result


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the profile details of a specific user by their ID.

    Workflow:
    1. Request the user record from the UserManager.
    2. If unsuccessful (success=False):
        a. Return 404 Not Found if the specific 'USER_NOT_FOUND' message is returned.
        b. Return 500 Internal Server Error for any other database-level failures.
    3. Return the user record if found.

    Args:
        user_id (int): The unique database identifier of the user.
        db (Session): Injected SQLAlchemy session via FastAPI.

    Returns:
        UserRead: The user profile data (serialized via Pydantic).

    Raises:
        HTTPException: 404 if the user ID does not exist.
        HTTPException: 500 if a SQLAlchemyError or connection issue occurs.
    """
    user_manager = UserManager(db)

    success, result = user_manager.get_user_by_id(user_id)

    if not success:
        if result == UserMessages.USER_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(result)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result)
        )

    return result


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user in the Kyzo database.

    Workflow:
    1. Check for existing accounts: Uses the UserManager to look up the email.
    2. Conflict Handling: If a user is found (success=True), registration is blocked.
    3. Error Handling: Differentiates between 'Not Found' (allowed) and DB errors.
    4. Creation: Delegates the password hashing and persistence to the UserManager.

    Args:
        user_data (UserCreate): The validated registration data (email, password, etc.).
        db (Session): The database session injected via FastAPI Dependency.

    Returns:
        User: The newly created user record, serialized via UserRead schema.

    Raises:
        HTTPException:
            - 409 (Conflict) if the email is already registered.
            - 400 (Bad Request) if the creation logic fails.
            - 500 (Internal Server Error) for database exceptions.
    """
    user_manager = UserManager(db)

    success_lookup, result_lookup = user_manager.get_user_by_email(user_data.email)

    if success_lookup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=UserMessages.EMAIL_ALREADY_EXIST
        )

    if not success_lookup and result_lookup != UserMessages.USER_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result_lookup)
        )

    success_create, result_create = user_manager.add_user(user_data)
    if not success_create:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(result_create)
        )

    return result_create


@router.put("/{user_id}/status", response_model=UserRead)
async def set_user_status(user_id: int, active: bool, db: Session = Depends(get_db)):
    """
    Toggles the activation status of a specific user.

    Workflow:
    1. Call the UserManager to update the 'is_active' flag.
    2. If unsuccessful (success=False):
        a. Return 404 if the user was not found.
        b. Return 500 for any other technical database error.
    3. Return the updated user object.

    Args:
        user_id (int): The unique ID of the user to be updated.
        active (bool): The target status (True/False).
        db (Session): Injected database session.

    Returns:
        UserRead: The updated user record.

    Raises:
        HTTPException: 404 if the user ID does not exist.
        HTTPException: 500 if a database error occurs.
    """
    user_manager = UserManager(db)

    success, result = user_manager.set_user_status(user_id, active)

    if not success:
        if result == UserMessages.USER_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(result)
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result)
        )

    return result


@router.put("/{user_id}/edit", response_model=UserRead)
async def update_user(user_id: int, update_data: UserUpdate, db: Session = Depends(get_db)):
    """
    Updates an existing user's profile information.

    Workflow:
    1. Send update data to the UserManager.
    2. If success is False:
        a. Return 404 Not Found if the error matches USER_NOT_FOUND.
        b. Return 500 Internal Server Error for database-level failures.
    3. Return the updated user object.

    Args:
        user_id (int): ID of the user to be updated.
        update_data (UserUpdate): Data to be updated (partial updates supported).
        db (Session): Injected database session via FastAPI.

    Returns:
        UserRead: The updated user record.

    Raises:
        HTTPException: 404 if the user ID doesn't exist.
        HTTPException: 500 if a technical database error occurs.
    """
    user_manager = UserManager(db)

    success, result = user_manager.update_user(user_id, update_data)

    if not success:
        if result == UserMessages.USER_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(result)
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result)
        )

    return result
