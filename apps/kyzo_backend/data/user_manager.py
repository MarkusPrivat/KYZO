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

from apps.kyzo_backend.config.messages import UserMessages
from apps.kyzo_backend.data.models import User
from apps.kyzo_backend.data.schemas import UserCreate, UserUpdate


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


    def get_user_by_email(self, email: str | EmailStr) -> tuple[bool, User | None | str]:
        """
        Retrieves a single user from the database based on their unique email address.

        This method executes a SELECT statement. It distinguishes between a
        successful query that returns no results and a database-level error.

        Args:
            email (str | EmailStr): The email address to search for.
                                    Accepts both raw strings and Pydantic EmailStr.

        Returns:
            tuple[bool, User | None | str]:
                - (True, User): If a matching user was found.
                - (True, None): If no user exists with this email.
                - (False, str): If a SQLAlchemyError occurred during execution.
        """
        try:
            stmt = (select(User).where(User.email == email))
            user = self._db.execute(stmt).scalar()

            return True, user
        except SQLAlchemyError as error:
            return False, f"{UserMessages.GET_USER_ERROR}: {str(error)}"


    def get_user_by_id(self, user_id: int) -> tuple[bool, User | None | str]:
        """
        Retrieves a specific user record using their unique primary key (ID).

        This is the standard method for fetching user data for profile views,
        updates, or status changes. It leverages the database index on the
        primary key for maximum performance.

        Args:
            user_id (int): The unique database identifier of the user.

        Returns:
            tuple[bool, User | None | str]:
                - (True, User): If a user with this ID exists.
                - (True, None): If the ID does not exist in the database.
                - (False, str): If a database error occurs (e.g. connection loss).
        """
        try:
            stmt = (select(User).where(User.id == user_id))
            user = self._db.execute(stmt).scalar()

            return True, user
        except SQLAlchemyError as error:
            return False, f"{UserMessages.GET_USER_ERROR}: {str(error)}"


    def set_user_status(self, user_id: int, active: bool = True) -> tuple[bool, User | None | str]:
        """
        Toggles the account activation status for a specific user.

        This method performs a 'soft delete' or 'reactivation' by modifying
        the is_active flag. It first attempts to locate the user by ID.

        Args:
            user_id (int): The unique ID of the user to update.
            active (bool): The target status. Defaults to True (active).

        Returns:
            tuple[bool, User | None | str]:
                - (True, User): If the status was successfully updated.
                - (True, None): If no user with the given ID was found.
                - (False, str): If a database error occurred during the transaction.
        """
        try:
            success, user = self.get_user_by_id(user_id)

            if not success:
                return False, user
            if user is None:
                return True, None

            user.is_active = active
            self._db.commit()
            self._db.refresh(user)
            return True, user

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"Status update error: {str(error)}"


    def update_user(self, user_id: int, user_update: UserUpdate) -> tuple[bool, User | None | str]:
        """
        Updates specific fields of an existing user record.

        This method follows a partial update strategy. It first verifies the
        user's existence and then applies only the fields provided in the
        request body, preserving all other existing data.

        Args:
            user_id (int): The unique identifier of the user to update.
            user_update (UserUpdate): A schema containing optional fields for
                                      modification (e.g., name, grade).

        Returns:
            tuple[bool, User | None | str]:
                - (True, User): The updated user instance on success.
                - (True, None): If the user_id does not exist in the database.
                - (False, str): If a technical error or constraint violation occurred.
        """
        try:
            success, user = self.get_user_by_id(user_id)

            if not success:
                return False, user
            if user is None:
                return True, None

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
