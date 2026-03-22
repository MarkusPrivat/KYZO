"""
user_schemas.py - Pydantic data validation and serialization models for user management in Kyzo.

This module defines the complete set of Pydantic schemas required for user account
management within the Kyzo adaptive learning platform. These schemas enforce data
validation, type safety, and proper serialization for all user-related API operations.

Key Features:
------------
- **Comprehensive Validation**:
  * String length constraints
  * Email format verification
  * Numeric range validation
  * Required field enforcement

- **Security Considerations**:
  * Password field excluded from read operations
  * Sensitive operations require explicit field specification
  * Type safety throughout all operations

- **API Integration**:
  * Field descriptions for automatic OpenAPI documentation
  * Consistent data structure for frontend integration
  * Support for both complete and partial updates

- **Role Management**:
  * UserRole enum integration for access control
  * Default role assignment for new users
  * Role modification support
"""
from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field

from apps.kyzo_backend.config import UserRole
from .base_schemas import BaseSchema


class UserCreate(BaseSchema):
    """
    Validation schema for creating a new user account.

    This schema defines the required fields and constraints for user
    registration, ensuring data integrity before persistence.

    Attributes:
        name (str): The user's full name or display name (3-100 chars).
        email (EmailStr): A unique, valid email address for authentication.
        password (str): The raw password (min. 8 chars) to be hashed later.
        grade (int): The academic level, constrained between 1 and 13.
        role (UserRole): The system access level, defaults to 'student'.
    """
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="The display name of the user."
    )
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="A valid and unique email address for login."
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Plain text password, will be hashed before storage."
    )
    grade: int = Field(
        ...,
        ge=1,
        le=13,
        description="The school grade level (1-13)."
    )
    role: UserRole = Field(
        default=UserRole.STUDENT,
        description="The authorization level within the platform."
    )


class UserRead(BaseSchema):
    """
    Data transfer object (DTO) for returning user information.

    This schema defines the structure of user data sent back to clients,
    purposely excluding sensitive fields like password hashes.

    Attributes:
        id (int): The unique primary key from the database.
        name (str): The display name of the user.
        email (EmailStr): The user's registered email.
        grade (int): The associated school grade level.
        role (UserRole): The assigned system role.
        is_active (bool): Account status.
        created_at (datetime): The timestamp of account creation.
    """
    id: int = Field(..., description="Unique database ID of the user.")
    name: str = Field(..., description="The display name.")
    email: EmailStr = Field(..., description="The validated email address.")
    grade: int = Field(..., description="The school grade level.")
    role: UserRole = Field(..., description="The user's role in the system.")
    is_active: bool = Field(..., description="Whether the user account is active.")
    created_at: datetime = Field(..., description="When the user was created.")


class UserUpdate(BaseSchema):
    """
    Validation schema for modifying existing user information.

    This schema allows for partial updates (PATCH-style logic). All fields are
    wrapped in Optional and default to None, ensuring that only the data
    explicitly provided in the request body will be modified in the database.

    Attributes:
        name (Optional[str]): Updated display name (3-100 chars).
        email (Optional[EmailStr]): Updated unique email address.
        grade (Optional[int]): Updated school grade level (1-13).
        role (Optional[UserRole]): Updated authorization level.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = Field(None, max_length=255)
    grade: Optional[int] = Field(None, ge=1, le=13)
    role: Optional[UserRole] = Field(None)
