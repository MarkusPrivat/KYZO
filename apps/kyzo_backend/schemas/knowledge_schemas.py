from typing import Optional

from pydantic import Field

from .base_schemas import BaseSchema


class SubjectCreate(BaseSchema):
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="The displayed subject name"
    )


class SubjectRead(BaseSchema):
    id: int = Field(..., description="Unique database ID of the subject.")
    name: str = Field(..., description="The displayed subject name.")
    is_active: bool = Field(..., description="Whether the subject is active.")


class SubjectStatus(BaseSchema):
    is_active: bool = Field(..., description="Whether the subject is active.")


class SubjectUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
