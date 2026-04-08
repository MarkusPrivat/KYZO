"""
user_manager.py - Business logic layer for user management in the Kyzo application.

This module implements the UserManager class, which serves as the central service layer
for all user-related operations in the Kyzo adaptive learning platform. It handles
database interactions, transaction management, and business logic while maintaining
a clean separation between the API layer and data persistence.

Key Responsibilities:
---------------------
- User Lifecycle Management: Creation, retrieval, updates, and status changes
- Data Validation: Ensures all operations comply with business rules
- Transaction Safety: Implements proper commit/rollback behavior
- Error Handling: Converts database exceptions into HTTPExceptions with appropriate status codes
- Dependency Injection: Designed to work with injected database sessions

Core Features:
--------------
1. **Database Operations**:
   - CRUD operations for user entities with proper transaction handling
   - Efficient querying by ID, email, or retrieving all users
   - Atomic operations with automatic rollback on failure

2. **Business Logic**:
   - Account activation/deactivation (soft delete) with status validation
   - Partial updates for user profiles (PATCH-style operations)
   - Input validation through Pydantic schemas

3. **Error Management**:
   - Comprehensive exception handling for SQLAlchemy operations
   - Conversion of database errors to appropriate HTTPExceptions:
     * 404 Not Found for missing resources
     * 500 Internal Server Error for database failures
   - Consistent error message formatting using UserMessages
   - Transaction rollback on failures to maintain data integrity

4. **Integration**:
   - Works with SQLAlchemy ORM models for data persistence
   - Uses Pydantic schemas for data validation and transformation
   - Designed for FastAPI dependency injection and exception handling
   - Returns SQLAlchemy model instances directly for further processing

Public Methods:
---------------
- add_user(user_data: UserCreate): Creates a new user record
  * Returns: User instance
  * Raises: HTTPException(500) on database errors

- get_all_users(): Retrieves all user records
  * Returns: List of User instances
  * Raises: HTTPException(404) if no users found, HTTPException(500) on errors

- get_user_by_email(email): Retrieves a user by email address
  * Returns: User instance
  * Raises: HTTPException(404) if user not found, HTTPException(500) on errors

- get_user_by_id(user_id): Retrieves a user by primary key
  * Returns: User instance
  * Raises: HTTPException(404) if user not found, HTTPException(500) on errors

- set_user_status(user_id, active): Toggles account activation status
  * Returns: Updated User instance
  * Raises: HTTPException(404) if user not found, HTTPException(500) on errors

- update_user(user_id, user_update): Applies partial updates to user records
  * Returns: Updated User instance
  * Raises: HTTPException(404) if user not found, HTTPException(500) on errors

Error Handling Strategy:
------------------------
This implementation follows RESTful API best practices by:
1. Using appropriate HTTP status codes for different error scenarios
2. Providing detailed error messages through UserMessages constants
3. Ensuring database consistency through automatic rollback on failures
4. Converting all database exceptions to HTTPExceptions for consistent API responses
5. Separating client errors (4xx) from server errors (500)

The methods now return SQLAlchemy model instances directly rather than tuples,
with all error conditions communicated through HTTPExceptions. This approach
integrates seamlessly with FastAPI's exception handling system.
"""
from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from apps.kyzo_backend.config import UserMessages
from apps.kyzo_backend.data import User
from apps.kyzo_backend.schemas import UserCreate, UserUpdate


class UserManager:
    """
    Service layer for managing user-related business logic and database operations.

    This class acts as an intermediary between the FastAPI routes and the
    SQLAlchemy models. It handles data persistence, retrieval, and status
    updates while managing database transactions (commit/rollback).

    Attributes:
        _db (Session): The injected SQLAlchemy database session.
    """

    def __init__(self, db: Session):
        """
        Initializes the UserManager with an externally provided database session.

        This approach follows the Dependency Injection principle to decouple
        the business logic from the session creation. It is essential for
        unit testing, as it allows passing a mock session or an in-memory
        SQLite database without modifying the Manager's code.

        Args:
            db (Session): The active SQLAlchemy session to be used for transactions.
        """
        self._db = db

    def add_user(self, user_data: UserCreate) -> User:
        """
        Persists a new user record in the database after verifying availability.

        This method performs an existence check for the email, converts the
        Pydantic schema into a SQLAlchemy model, and handles the full
        transaction lifecycle (commit, refresh, and rollback on failure).

        Args:
            user_data (UserCreate): Validated data transfer object containing
                                    the new user's attributes.

        Returns:
            User: The successfully created and persisted SQLAlchemy User instance
                  including its generated unique ID.

        Raises:
            HTTPException:
                - 409 (Conflict): If the email address is already registered.
                - 500 (Internal Server Error): If a database integrity error or
                  connection issue occurs during persistence.
        """
        try:
            if self._is_email_taken(user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=UserMessages.EMAIL_ALREADY_EXIST
                )

            user_dict = user_data.model_dump()
            new_user = User(**user_dict)

            self._db.add(new_user)
            self._db.commit()
            self._db.refresh(new_user)
            return new_user

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{UserMessages.CREATE_ERROR}: {str(error)}"
            ) from error

    def get_all_users(self) -> list[User]:
        """
        Retrieves all user records from the database.

        This method queries the entire users table and returns a list of all
        registered users. It is primarily intended for administrative
        overviews or system-wide management.

        Returns:
            list[User]: A list containing all SQLAlchemy User instances.

        Raises:
            HTTPException:
                - 404 (Not Found): If the database is empty and no users are found.
                - 500 (Internal Server Error): If a database transaction fails.
        """
        try:
            stmt = select(User)
            all_users = self._db.execute(stmt).scalars().all()

            if not all_users:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=UserMessages.NO_USERS
                )

            return list(all_users)

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{UserMessages.GET_ALL_USER_ERROR} {str(error)}"
            ) from error

    def get_user_by_email(self, email: str | EmailStr) -> User:
        """
        Retrieves a single user from the database based on their unique email address.

        This is the primary method for authentication processes or for
        verifying account existence during registration.

        Args:
            email (str | EmailStr): The email address to search for. Supports
                                    raw strings and Pydantic's EmailStr type.

        Returns:
            User: The SQLAlchemy User instance if a match is found.

        Raises:
            HTTPException:
                - 404 (Not Found): If no user is registered with this email.
                - 500 (Internal Server Error): If a database transaction fails.
        """
        try:
            stmt = (select(User).where(User.email == email))
            user = self._db.execute(stmt).scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=UserMessages.USER_NOT_FOUND
                )

            return user
        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{UserMessages.GET_USER_ERROR} {str(error)}"
            ) from error

    def get_user_by_id(self, user_id: int) -> User:
        """
        Retrieves a specific user record using their unique primary key (ID).

        This is the standard method for fetching user data for profile views,
        updates, or status changes. It leverages the primary key index for
        high-performance lookups.

        Returns:
            User: The SQLAlchemy User instance if found.

        Raises:
            HTTPException:
                - 404 (Not Found) if no user exists with the given ID.
                - 500 (Internal Server Error) if a database transaction fails.
        """
        try:
            stmt = (select(User).where(User.id == user_id))
            user = self._db.execute(stmt).scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=UserMessages.USER_NOT_FOUND
                )

            return user

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{UserMessages.GET_USER_ERROR} {str(error)}"
            ) from error

    def set_user_status(self, user_id: int, active: bool = True) -> User:
        """
        Toggles the account activation status for a specific user.

        Args:
            user_id (int): The unique ID of the user to update.
            active (bool): The target status. Defaults to True (active).

        Returns:
            User: The updated SQLAlchemy User instance.

        Raises:
            HTTPException:
                - 404 (Not Found) if user exists not (raised by get_user_by_id).
                - 500 (Internal Server Error) if the database update fails.
        """
        user = self.get_user_by_id(user_id)

        try:
            user.is_active = active
            self._db.commit()
            self._db.refresh(user)
            return user

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{UserMessages.UPDATE_USER_ERROR} {str(error)}"
            ) from error

    def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        """
        Updates specific fields of an existing user record.

        This method performs a partial update (PATCH-style) by only modifying
        fields that were explicitly provided in the request. It handles
        normalization and ensures database consistency.

        Args:
            user_id (int): The unique identifier of the user to update.
            user_update (UserUpdate): Schema containing optional fields for modification.

        Returns:
            User: The updated SQLAlchemy User instance.

        Raises:
            HTTPException:
                - 404 (Not Found) if user exists not (via get_user_by_id).
                - 500 (Internal Server Error) if the database transaction fails.
        """
        user = self.get_user_by_id(user_id)

        try:
            update_data = user_update.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                if key == "email" and value is not None:
                    if value != user.email and self._is_email_taken(value):
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=UserMessages.EMAIL_ALREADY_EXIST
                        )
                    value = str(value)  # EmailStr to str for SQLAlchemy
                setattr(user, key, value)

            self._db.commit()
            self._db.refresh(user)
            return user

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{UserMessages.UPDATE_USER_ERROR} {str(error)}"
            ) from error

    def _is_email_taken(self, email: str | EmailStr) -> bool:
        """
        Checks the database for the existence of a specific email address.

        This helper method is used to verify if an email is already associated
        with an account, without raising a 404 error if it's not found.

        Args:
            email (str | EmailStr): The email address to check.

        Returns:
            bool: True if the email exists in the database, False otherwise.

        Raises:
            HTTPException: 500 if a database technical error occurs.
        """
        try:
            stmt = select(User.id).where(User.email == email)
            result = self._db.execute(stmt).scalar_one_or_none()

            return result is not None

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{UserMessages.GET_USER_ERROR} {str(error)}"
            ) from error
