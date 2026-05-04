import enum

from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class InputType(enum.Enum):
    """
    Specifies the source format of raw data used for question generation.

    Values:
        MANUAL: Content entered directly as text or via copy-paste.
        SCAN: Content extracted from document uploads like PDFs or images.
    """
    MANUAL = 'manual'
    SCAN = 'scan'


class LLMProvider(enum.Enum):
    """
    Supported Large Language Model providers for the application.

    Attributes:
        OPENAI: Represents the OpenAI service suite (e.g., GPT models).
        GOOGLE: Represents the Google GenAI service suite (e.g., Gemma or Gemini models).
    """
    OPENAI = "openai"
    GOOGLE = "gemma"


class UserRole(enum.Enum):
    """
    Defines the authorization levels and responsibilities for users.

    Values:
        STUDENT: Standard user who takes tests and tracks personal progress.
        TEACHER: Privileged user who can manage content and view student analytics.
        ADMIN: System administrator with full access to all platform settings.
    """
    STUDENT = 'student'
    TEACHER = 'teacher'
    ADMIN = 'admin'


class FastAPISettings(BaseSettings):
    """
    Central configuration container for the Kyzo backend.

    This class leverages Pydantic Settings to automatically load and validate
    configuration from environment variables and a .env file. It manages
    file system paths, database URIs, security credentials, and multi-provider
    LLM parameters (OpenAI & Google/Gemma).

    Attributes:
        PROJECT_ROOT (Path): The absolute path to the repository's root directory.
        DATA_DIR (Path): Directory for persistent application data (SQLite, uploads).
        DATABASE_PATH (Path): Full path to the SQLite database file.
        SQLALCHEMY_DATABASE_URI (str): The connection string for the SQLAlchemy engine.
        OPENAI_API_KEY (str): Authentication token for the OpenAI API.
        GEMINI_API_KEY (str): Authentication token for the Google GenAI/Gemini API.
        OPENAI_MODEL (str): Model ID for OpenAI-specific tasks (e.g., 'gpt-4o-mini').
        GEMINI_MODEL (str): Model ID for Google/Gemma tasks (e.g., 'gemma-4-26b-a4b-it').
        LLM_TEMPERATURE (float): Global sampling temperature (0.0 to 2.0).
            Lower is more deterministic (ideal for OCR), higher is more creative.
        LLM_MAX_TOKENS (int): The maximum length of the generated AI response,
            applied across all configured providers.
    """
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / 'apps' / 'kyzo_backend' / 'data'

    DATABASE_PATH: Path = DATA_DIR / 'kyzo-data.sqlite'
    SQLALCHEMY_DATABASE_URI: str = ""

    OPENAI_API_KEY: str = Field(...)
    OPENAI_MODEL: str = Field("gpt-4o-mini", description="The AI model used for generation")

    GEMINI_API_KEY: str = Field(...)
    GEMINI_MODEL: str = Field("gemma-4-26b-a4b-it", description="The AI model used for generation")

    LLM_TEMPERATURE: float = Field(0.0, ge=0.0, le=2.0, description="Creativity level of the AI")
    LLM_MAX_TOKENS: int = Field(5000, description="Limit for the AI response size")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **values: Any):
        """
        Initializes the configuration settings and performs post-init setup.

        This constructor triggers the Pydantic settings loading process, ensures
        that the required local data directories exist on the file system, and
        dynamically constructs the SQLAlchemy database URI if not already
        provided via environment variables.

        Args:
            **values (Any): Arbitrary keyword arguments passed to the Pydantic
                model constructor, typically used for overriding settings
                during testing.

        Note:
            The directory creation (mkdir) is performed with 'parents=True'
            to ensure the entire path leading to DATA_DIR is available.
        """
        super().__init__(**values)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.DATABASE_PATH.as_posix()}"

    @field_validator("OPENAI_API_KEY", "GEMINI_API_KEY")
    @classmethod
    def check_not_empty(cls, value: str, info) -> str:
        """
        Ensures that critical security keys are not provided as empty strings.

        This validator checks multiple fields defined in the decorator to ensure
        they are present and contain non-whitespace characters.

        Args:
            value (str): The value of the configuration field being validated.
            info: Pydantic validation info (contains the field name).

        Returns:
            str: The validated string.

        Raises:
            ValueError: If the key is missing, empty, or contains only whitespace.
        """
        if not value or value.strip() == "":
            raise ValueError(f"The {info.field_name} cannot be empty!")
        return value


fastapi_settings = FastAPISettings()
