from typing import Optional

from pydantic import Field

from .base_schemas import BaseSchema


class SubjectCreate(BaseSchema):
    """
    Validation schema for creating a new academic subject.

    This schema ensures that only valid subject names (e.g., 'Mathematics',
    'Computer Science') are accepted. It enforces length constraints to
    maintain UI consistency and prevent database abuse.

    Attributes:
        name (str): The unique name of the subject (3-100 characters).
    """
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="The displayed subject name"
    )


class SubjectRead(BaseSchema):
    """
    Data transfer object (DTO) for returning subject information.

    This schema defines the structure of subject data sent back to clients.
    It includes the database identifier and the current operational status
    of the subject.

    Attributes:
        id (int): The unique primary key from the database.
        name (str): The official name of the subject (e.g., 'Mathematics').
        is_active (bool): Indicates if the subject is currently available
                         for students and AI-generation.
    """
    id: int = Field(..., description="Unique database ID of the subject.")
    name: str = Field(..., description="The displayed subject name.")
    is_active: bool = Field(..., description="Whether the subject is active.")


class SubjectStatus(BaseSchema):
    """
    Validation schema for toggling the operational status of a subject.

    This specialized schema is used for administrative tasks, such as
    activating or deactivating a subject (soft-delete). Deactivating a
    subject hides it from students without deleting its associated
    topics and questions.

    Attributes:
        is_active (bool): The desired status of the subject.
    """
    is_active: bool = Field(..., description="Whether the subject is active.")


class SubjectUpdate(BaseSchema):
    """
    Validation schema for modifying existing subject information.

    This schema allows for partial updates of a subject's metadata.
    By using Optional fields, it ensures that only the data explicitly
    provided in the request body will be updated, while other
    attributes remain unchanged.

    Attributes:
        name (Optional[str]): The updated name of the subject (3-100 chars).
                             Defaults to None if not provided.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=100)
