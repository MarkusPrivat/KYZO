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
