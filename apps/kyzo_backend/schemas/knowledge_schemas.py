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


class TopicCreate(BaseSchema):
    """
    Validation schema for creating a new topic within a subject.

    Each topic must be linked to an existing subject and defines a
    target academic level. This ensures that content like 'Fractional
    Arithmetic' can be correctly categorized by difficulty and curriculum.

    Attributes:
        subject_id (int): The foreign key ID of the parent subject (must be > 0).
        name (str): The name of the specific learning topic (2-150 chars).
        grade_expected (int): The target school grade level, constrained between 1 and 13.
    """
    subject_id: int = Field(
        ...,
        gt=0,
        description="The ID of the subject this topic belongs to."
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="The name of the specific learning topic."
    )
    grade_expected: int = Field(
        ...,
        ge=1,
        le=13,
        description="The school grade level (1-13) for which this topic is intended."
    )


class TopicRead(BaseSchema):
    """
    Data transfer object (DTO) for returning topic information.

    This schema provides a complete view of a topic, including its
    unique identifier, its parent subject, and its target grade level.

    Attributes:
        id (int): The unique primary key from the database.
        subject_id (int): The ID of the associated parent subject.
        name (str): The display name of the topic.
        grade_expected (int): The academic grade level for this topic.
        is_active (bool): Whether the topic is currently visible to users.
    """
    id: int = Field(..., description="Unique database ID of the topic.")
    subject_id: int = Field(..., description="The ID of the parent subject.")
    name: str = Field(..., description="The displayed name of the topic.")
    grade_expected: int = Field(..., description="The target school grade level (1-13).")
    is_active: bool = Field(..., description="Indicates if the topic is active and available.")


class TopicStatus(BaseSchema):
    """
    Validation schema for toggling the operational status of a topic.

    Similar to subjects, topics can be activated or deactivated.
    Deactivating a topic (is_active=False) hides it and its associated
    questions from the learning view without deleting the historical
    data or its relationship to the parent subject.

    Attributes:
        is_active (bool): The desired availability status of the topic.
    """
    is_active: bool = Field(..., description="Whether the topic is active")


class TopicUpdate(BaseSchema):
    """
    Validation schema for modifying existing topic information.

    Allows for partial updates of a topic's metadata. All fields are
    optional, meaning only the provided attributes will be updated.
    Includes the ability to reassign a topic to a different subject.

    Attributes:
        subject_id (Optional[int]): The new parent subject ID (must be > 0).
        name (Optional[str]): The updated name (2-150 chars).
        grade_expected (Optional[int]): The updated target grade level (1-13).
    """
    subject_id: Optional[int] = Field(
        None,
        gt=0,
        description="The new subject ID if the topic is being moved."
    )
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=150,
        description="The updated name of the topic."
    )
    grade_expected: Optional[int] = Field(
        None,
        ge=1,
        le=13,
        description="The updated target school grade level."
    )
