"""
subject_and_topic_schemas.py - Pydantic validation and serialization schemas
for academic content management in Kyzo.

This module defines comprehensive data validation and transfer schemas for
managing academic subjects and their nested topics within the Kyzo adaptive
learning platform. These schemas ensure data integrity, proper formatting, and
consistent API contracts for all curriculum-related operations.

Core Components:
----------------
The module provides schemas for both subjects (high-level academic disciplines) and topics
(specific learning units), covering the complete lifecycle from creation to updates:

1. Subject Schemas:
   - SubjectCreate: Validates new subject creation with name formatting
   - SubjectRead: Defines the structure for returning subject data
   - SubjectStatus: Handles subject activation/deactivation
   - SubjectUpdate: Supports partial updates to existing subjects

2. Topic Schemas:
   - TopicCreate: Validates new topic creation with subject association
   - TopicRead: Defines the structure for returning topic data
   - TopicStatus: Handles topic activation/deactivation
   - TopicUpdate: Supports partial updates to existing topics

Key Features:
------------
- **Data Validation**:
  * String length constraints (subjects: 3-100 chars, topics: 2-150 chars)
  * Grade level validation (1-13)
  * Required field enforcement
  * Automatic whitespace trimming

- **Data Formatting**:
  * Automatic conversion to Title Case for display consistency
  * Sanitization of input strings

- **Partial Updates**:
  * Optional fields in update schemas for granular modifications
  * Preservation of existing values for unspecified fields

- **Status Management**:
  * Soft-delete functionality via is_active flag
  * Administrative control over content visibility

- **Relationship Management**:
  * Subject-Topic hierarchy enforcement
  * Foreign key validation for parent subjects

- **Error Handling**:
  * Custom validation messages via SchemasMessages
  * Clear error feedback for invalid inputs
"""
from typing import Optional

from pydantic import Field, field_validator

from .base_schemas import BaseSchema
from ..config import SchemasMessages


class SubjectCreate(BaseSchema):
    """
    Validation schema for creating a new academic subject.

    This schema validates and sanitizes subject names (e.g., 'Mathematics').
    It enforces length constraints and automatic formatting to ensure
    database consistency and a clean UI presentation.

    Attributes:
        name (str): The unique name of the subject. Must contain 3 to 100
            characters. Leading/trailing whitespace is automatically
            stripped, and the value is converted to Title Case.
    """
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="The displayed subject name (automatically title-cased)."
    )

    @field_validator("name")
    @classmethod
    def format_subject_name(cls, value: str) -> str:
        """
        Validates and formats the subject name.

        Ensures that the name contains at least 3 non-whitespace characters
        and converts the string to Title Case (e.g., 'math' -> 'Math').

        Args:
            value (str): The raw string input from the request.

        Returns:
            str: The sanitized and formatted subject name.

        Raises:
            ValueError: If the name is too short after trimming whitespace.
        """
        if len(value) < 3:
            raise ValueError(SchemasMessages.SUBJECT_NAME_LEN)
        return value.title()


class SubjectRead(BaseSchema):
    """
    Data transfer object (DTO) for outgoing subject records.

    This schema is responsible for serializing database models into
    client-side JSON. It reflects the current state of a subject,
    including its unique identity and availability status.

    Attributes:
        id (int): The internal database primary key.
        name (str): The sanitized name of the subject (e.g., 'Mathematics').
        is_active (bool): Operational flag. If False, the subject is
            effectively 'soft-deleted' or hidden from the curriculum.
    """
    id: int = Field(..., description="Unique database ID of the subject.")
    name: str = Field(..., description="The displayed and formatted subject name.")
    is_active: bool = Field(..., description="Indicates if the subject is active and visible.")


class SubjectStatus(BaseSchema):
    """
    Schema for updating the operational visibility of a subject.

    This specialized DTO is used for administrative toggling between
    active and inactive states (soft-delete).

    Setting 'is_active' to False effectively hides the subject and all
    its nested topics and questions from the student-facing curriculum
    while preserving the underlying data for historical reporting.

    Attributes:
        is_active (bool): The target status. True enables the subject,
            False disables it across the platform.
    """
    is_active: bool = Field(
        ...,
        description="The desired visibility status of the subject."
    )


class SubjectUpdate(BaseSchema):
    """
    Validation schema for partial updates of an existing subject.

    This schema allows for granular modifications. Since all attributes
    are optional, only the fields explicitly provided in the request body
    will be overwritten in the database. Omitted fields remain unchanged.

    Attributes:
        name (Optional[str]): The new name for the subject. Must be
            3-100 characters. If provided, it is automatically sanitized
            and converted to Title Case.
    """
    name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="Optional new name for the subject."
    )

    @field_validator("name")
    @classmethod
    def format_subject_name(cls, value: Optional[str]) -> Optional[str]:
        """
        Validates and formats the name if it is part of the update.

        Args:
            value (Optional[str]): The provided name string or None.

        Returns:
            Optional[str]: The sanitized 'Title Case' string or None.

        Raises:
            ValueError: If the provided name is too short after trimming.
        """
        if value is not None:
            if len(value) < 3:
                raise ValueError(SchemasMessages.SUBJECT_NAME_LEN)
            return value.title()
        return value


class TopicCreate(BaseSchema):
    """
    Validation schema for creating a new learning topic.

    Each topic represents a granular unit of knowledge (e.g., 'Linear Equations')
    nested within a broader academic subject. This schema ensures proper
    categorization by enforcing links to parent subjects and target grade levels.

    Attributes:
        subject_id (int): The unique ID of the parent subject. Must be positive.
        name (str): The specific topic name (2-150 chars). Automatically
            formatted to Title Case and stripped of whitespace.
        grade_expected (int): The target school grade level (K-12/13),
            constrained between 1 and 13.
    """
    subject_id: int = Field(
        ...,
        gt=0,
        description="The unique database ID of the parent subject."
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="The name of the specific topic (e.g., 'Photosynthesis')."
    )
    grade_expected: int = Field(
        ...,
        ge=1,
        le=13,
        description="The intended academic grade level (range: 1-13)."
    )

    @field_validator("name")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """
        Validates and formats the topic name.

        Ensures the name contains sufficient content after stripping and
        standardizes the string to Title Case.

        Args:
            value (str): The raw string input.

        Returns:
            str: The sanitized and title-cased topic name.

        Raises:
            ValueError: If the name is shorter than 2 characters after trimming.
        """
        if len(value) < 2:
            raise ValueError(SchemasMessages.TOPIC_NAME_LEN)
        return value.title()


class TopicRead(BaseSchema):
    """
    Data transfer object (DTO) for outgoing topic records.

    This schema serializes database models for the client, providing
    a detailed view of a learning unit. It includes the mapping to
    the parent subject and the intended academic level.

    Attributes:
        id (int): The internal database primary key.
        subject_id (int): The foreign key ID of the parent subject.
        name (str): The sanitized name of the topic (Title Case).
        grade_expected (int): The target school grade level (1-13).
        is_active (bool): Operational flag. If False, the topic and its
            questions are hidden from the curriculum view.
    """
    id: int = Field(..., description="Unique database ID of the topic.")
    subject_id: int = Field(..., description="The ID of the parent subject.")
    name: str = Field(..., description="The displayed and formatted topic name.")
    grade_expected: int = Field(
        ...,
        description="The target school grade level (1-13)."
    )
    is_active: bool = Field(
        ...,
        description="Indicates if the topic is active and available."
    )

class TopicStatus(BaseSchema):
    """
    Schema for updating the operational visibility of a topic.

    This specialized DTO allows for administrative toggling of a topic's
    availability. Deactivating a topic (is_active=False) performs a
    'soft-delete', hiding the unit and its associated questions from
    the student-facing platform.

    Attributes:
        is_active (bool): The target availability status. If False, the
            topic remains in the database for historical analytics but
            is excluded from active learning sessions.
    """
    is_active: bool = Field(
        ...,
        description="The desired visibility status of the topic."
    )


class TopicUpdate(BaseSchema):
    """
    Validation schema for partial updates of an existing learning topic.

    This schema supports granular modifications. Since all attributes are
    optional, only the data explicitly provided in the request body will
    be overwritten in the database.

    This allows for operations like reassigning a topic to another subject
    or correcting its name without affecting other metadata.

    Attributes:
        subject_id (Optional[int]): The new parent subject ID. Must be > 0.
        name (Optional[str]): The updated name (2-150 chars). If provided,
            it is automatically sanitized and converted to Title Case.
        grade_expected (Optional[int]): The updated target school grade
            level (1-13).
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
        description="The updated topic name (will be title-cased)."
    )
    grade_expected: Optional[int] = Field(
        None,
        ge=1,
        le=13,
        description="The updated target school grade level."
    )

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: Optional[str]) -> Optional[str]:
        """
        Validates and formats the topic name if it is part of the update.

        Args:
            value (Optional[str]): The provided name string or None.

        Returns:
            Optional[str]: The sanitized 'Title Case' string or None.

        Raises:
            ValueError: If the provided name is too short after trimming.
        """
        if value is not None:
            if len(value) < 2:
                raise ValueError(SchemasMessages.TOPIC_NAME_LEN)
            return value.title()
        return value
