from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from apps.kyzo_backend.config.config import UserRole


class BaseSchema(BaseModel):
    """
    Common base class for all Pydantic schemas in the Kyzo application.

    This class configures global settings like ORM compatibility and
    automatic whitespace stripping for all inheriting models.

    Attributes:
        model_config (ConfigDict): Configuration for Pydantic model behavior.
    """
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


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
        created_at (datetime): The timestamp of account creation.
    """
    id: int = Field(..., description="Unique database ID of the user.")
    name: str = Field(..., description="The display name.")
    email: EmailStr = Field(..., description="The validated email address.")
    grade: int = Field(..., description="The school grade level.")
    role: UserRole = Field(..., description="The user's role in the system.")
    created_at: datetime = Field(..., description="When the user was created.")
