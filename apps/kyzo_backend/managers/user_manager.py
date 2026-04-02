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
- Error Handling: Converts database exceptions into user-friendly messages
- Dependency Injection: Designed to work with injected database sessions

Core Features:
--------------
1. **Database Operations**:
   - CRUD operations for user entities
   - Efficient querying by ID and email
   - Atomic transaction handling

2. **Business Logic**:
   - Account activation/deactivation (soft delete)
   - Partial updates for user profiles
   - Input validation through Pydantic schemas

3. **Error Management**:
   - Comprehensive exception handling for SQLAlchemy operations
   - Consistent error message formatting using UserMessages
   - Transaction rollback on failures

4. **Integration**:
   - Works with SQLAlchemy ORM models
   - Uses Pydantic schemas for data validation
   - Designed for FastAPI dependency injection

Public Methods:
---------------
- add_user(user_data: UserCreate): Creates a new user record
- get_user_by_email(email): Retrieves a user by email address
- get_user_by_id(user_id): Retrieves a user by primary key
- set_user_status(user_id, active): Toggles account activation status
- update_user(user_id, user_update): Applies partial updates to user records

Return Values:
--------------
All methods return a standardized tuple format:
- (bool, User | None | str):
  - bool: Success status (True/False)
  - User: The affected user object on success
  - None: When no user is found (but operation was valid)
  - str: Error message on failure
"""
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


    def add_user(self, user_data: UserCreate) -> tuple[bool, User | str]:
        """
        Persists a new user record in the database.

        This method converts the validated Pydantic schema into a SQLAlchemy
        model instance using model_dump(). It handles the entire transaction
        lifecycle, including commit, refresh, and rollback on failure.

        Args:
            user_data (UserCreate): Validated data transfer object containing
                                    the new user's attributes.

        Returns:
            tuple[bool, User | str]:
                - On success: (True, User-instance including generated ID)
                - On failure: (False, Error message string)
        """
        try:
            user_dict = user_data.model_dump()
            new_user = User(**user_dict)

            self._db.add(new_user)
            self._db.commit()
            self._db.refresh(new_user)
            return True, new_user

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{UserMessages.CREATE_ERROR}: {str(error)}"


    def get_all_users(self) -> tuple[bool, list[User] | str]:
        """
        Retrieves all user records from the database.

        This method queries the entire users table. It is intended for
        administrative overviews or system-wide user management.

        Returns:
            tuple[bool, list[User] | str]:
                - (True, [User, ...]) if successful (even if the list is empty).
                - (False, error_message) if a database error occurs.
        """
        try:
            stmt = select(User)
            all_users = self._db.execute(stmt).scalars().all()

            return True, list(all_users)
        except SQLAlchemyError as error:
            return False, f"{UserMessages.GET_ALL_USER_ERROR}: {str(error)}"


    def get_user_by_email(self, email: str | EmailStr) -> tuple[bool, User | str]:
        """
        Retrieves a single user from the database based on their unique email address.

        This method executes a SELECT statement. It is the primary way to
        authenticate users or check for existing accounts during registration.

        Args:
            email (str | EmailStr): The email address to search for.
                                    Accepts both raw strings and Pydantic EmailStr.

        Returns:
            tuple[bool, User | str]:
                - (True, User): If a matching user was found successfully.
                - (False, str): If no user exists or if a database-level error occurred.
        """
        try:
            stmt = (select(User).where(User.email == email))
            user = self._db.execute(stmt).scalar()

            if not user:
                return False, UserMessages.USER_NOT_FOUND

            return True, user
        except SQLAlchemyError as error:
            return False, f"{UserMessages.GET_USER_ERROR}: {str(error)}"


    def get_user_by_id(self, user_id: int) -> tuple[bool, User | str]:
        """
        Retrieves a specific user record using their unique primary key (ID).

        This is the standard method for fetching user data for profile views,
        updates, or status changes. It leverages the primary key index for
        high-performance lookups.

        Args:
            user_id (int): The unique database identifier of the user.

        Returns:
            tuple[bool, User | str]:
                - (True, User): If the user was successfully found.
                - (False, str): If the user does not exist or if a database error occurs.
        """
        try:
            stmt = (select(User).where(User.id == user_id))
            user = self._db.execute(stmt).scalar_one_or_none()

            if not user:
                return False, UserMessages.USER_NOT_FOUND

            return True, user
        except SQLAlchemyError as error:
            return False, f"{UserMessages.GET_USER_ERROR}: {str(error)}"


    def set_user_status(self, user_id: int, active: bool = True) -> tuple[bool, User | str]:
        """
        Toggles the account activation status for a specific user.

        Workflow:
        1. Fetch the user via get_user_by_id.
        2. If success is False, return the error (either 'Not Found' or DB error).
        3. Update the is_active flag and commit the transaction.

        Args:
            user_id (int): The unique ID of the user to update.
            active (bool): The target status. Defaults to True (active).

        Returns:
            tuple[bool, User | str]:
                - (True, User): The updated user object.
                - (False, str): Error message if the user doesn't exist or a DB error occurs.
        """
        try:
            success, user = self.get_user_by_id(user_id)

            if not success:
                return False, user

            user.is_active = active
            self._db.commit()
            self._db.refresh(user)
            return True, user

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"Status update error: {str(error)}"


    def update_user(self, user_id: int, user_update: UserUpdate) -> tuple[bool, User | str]:
        """
        Updates specific fields of an existing user record.

        Workflow:
        1. Fetch the existing user via get_user_by_id.
        2. Guard: If success is False, return the error (Not Found or DB error).
        3. Partial Update: Iterate through provided fields (exclude_unset=True).
        4. Data Normalization: Convert EmailStr to raw strings for SQLAlchemy.
        5. Persistence: Commit changes and refresh the instance.

        Args:
            user_id (int): The unique identifier of the user to update.
            user_update (UserUpdate): A schema containing optional fields for modification.

        Returns:
            tuple[bool, User | str]:
                - (True, User): The updated user instance.
                - (False, str): If the user doesn't exist or a database error occurs.
        """
        try:
            success, user = self.get_user_by_id(user_id)

            if not success:
                return False, user

            update_dict = user_update.model_dump(exclude_unset=True)

            for key, value in update_dict.items():
                if key == "email" and value is not None:
                    value = str(value) #EmailStr to str for SQLAlchemy
                setattr(user, key, value)

            self._db.commit()
            self._db.refresh(user)
            return True, user

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{UserMessages.UPDATE_USER_ERROR} {str(error)}"
