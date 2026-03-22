"""
base_schema.py - Foundation for Pydantic data models in the Kyzo application.

This module defines the BaseSchema class, which serves as the root for all Pydantic
data validation schemas across the Kyzo platform. It establishes consistent
configuration and behavior for all schema classes used by various service managers.

Core Functionality:
-------------------
- **ORM Compatibility**: Enables seamless conversion between Pydantic models and
  SQLAlchemy ORM objects through the `from_attributes=True` configuration.
- **Data Cleaning**: Automatically strips whitespace from string inputs to prevent
  formatting issues and ensure data consistency.
- **Inheritance Foundation**: Designed to be extended by domain-specific schemas in
  each manager module (e.g., user_schemas, knowledge_schema ,...).

Configuration Details:
----------------------
- `from_attributes=True`: Allows creating Pydantic models from ORM objects and
  other attribute-based sources.
- `str_strip_whitespace=True`: Automatically removes leading/trailing whitespace
  from all string fields during validation.

Usage Pattern:
--------------
All domain-specific schemas should inherit from this base class to ensure
consistent behavior across the application:

from .base_schema import BaseSchema

class NewSchema(BaseSchema):
"""
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Common base class for all Pydantic schemas in the Kyzo application.

    This class configures global settings like ORM compatibility and
    automatic whitespace stripping for all inheriting models.

    Attributes:
        model_config (ConfigDict): Configuration for Pydantic model behavior.
    """
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
