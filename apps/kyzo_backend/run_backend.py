import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.config.messages import UserMessages
from apps.kyzo_backend.data.database import create_database, get_db
from apps.kyzo_backend.data.schemas import UserCreate, UserRead, UserUpdate
from apps.kyzo_backend.data.user_manager import UserManager


create_database()
app = FastAPI(title="Kyzo Backend")


@app.get("/api/users/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the profile details of a specific user by their ID.

    This endpoint uses the UserManager to fetch the user record. It
    distinguishes between a database failure (500) and the case where
    the user simply doesn't exist (404).

    Args:
        user_id (int): The unique database identifier of the user.
        db (Session): Injected SQLAlchemy session.

    Returns:
        UserRead: The user profile data if found.

    Raises:
        HTTPException: 404 if the user is not in the database.
        HTTPException: 500 if a database error occurs.
    """
    user_manager = UserManager(db)

    success, result = user_manager.get_user_by_id(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )


    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=UserMessages.NOT_FOUND
        )

    return result


@app.post("/api/users/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user in the Kyzo database.

    This endpoint performs a dual-check:
    1. It verifies if the email address is already taken to prevent duplicates.
    2. It delegates the creation logic to the UserManager.

    Returns the newly created user object (excluding the password).

    Args:
        user_data (UserCreate): The validated registration data.
        db (Session): The database session injected by FastAPI.

    Raises:
        HTTPException: 400 if the email exists or the creation fails.
    """
    user_manager = UserManager(db)

    success_, existing_user = user_manager.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=UserMessages.EMAIL_ALREADY_EXIST
        )

    success, result = user_manager.add_user(user_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

    return result


@app.put("/api/users/{user_id}/status", response_model=UserRead)
async def set_user_status(user_id: int, active: bool, db: Session = Depends(get_db)):
    """
    Toggles the activation status of a specific user.

    This endpoint allows administrators or the system to enable or disable
    a user account (soft delete). It uses the UserManager to persist
    the status change in the database.

    Args:
        user_id (int): The unique ID of the user whose status should be changed.
        active (bool): The target status (True for active, False for inactive).
        db (Session): The database session injected via FastAPI dependency.

    Returns:
        UserRead: The updated user object with the new status.

    Raises:
        HTTPException: 404 if the user_id does not exist.
        HTTPException: 500 if a technical database error occurs.
    """
    user_manager = UserManager(db)

    success, result = user_manager.set_user_status(user_id, active)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=UserMessages.NOT_FOUND
        )

    return result


@app.put("/api/users/{user_id}/edit", response_model=UserRead)
async def update_user(user_id: int, update_data: UserUpdate, db: Session = Depends(get_db)):
    """
    Updates an existing user's profile information.

    This endpoint supports partial updates. Only the fields provided in
    the request body will be changed. It ensures the user exists before
    attempting any database modifications.

    Args:
        user_id (int): ID of the user to be updated.
        update_data (UserUpdate): Data to be updated (all fields optional).
        db (Session): Injected database session.

    Returns:
        UserRead: The updated user record.

    Raises:
        HTTPException: 404 if the user doesn't exist.
        HTTPException: 400/500 if a database or validation error occurs.
    """
    user_manager = UserManager(db)

    success, result = user_manager.update_user(user_id, update_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=UserMessages.NOT_FOUND
        )

    return result


if __name__ == "__main__":
    uvicorn.run("run_backend:app", host="127.0.0.1", port=8000, reload=True)
