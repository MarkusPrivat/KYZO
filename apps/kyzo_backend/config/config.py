import enum
from typing import Any

from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class InputType(enum.Enum):
    """
    Specifies the source format of raw data used for question generation.

    Values:
        MANUAL: Content entered directly as text or via copy-paste.
        SCAN: Content extracted from document uploads like PDFs or images.
    """
    MANUAL = 'manual'
    SCAN = 'scan'


class FastAPISettings(BaseSettings):
    """
    Central configuration container for the Kyzo backend.

    This class leverages Pydantic Settings to automatically load and validate
    configuration from environment variables and a .env file. It manages
    paths, database URIs, security keys, and LLM parameters.

    Attributes:
        PROJECT_ROOT (Path): The absolute path to the repository's root directory.
        DATA_DIR (Path): Directory for persistent application data (SQLite, uploads).
        DATABASE_PATH (Path): Full path to the SQLite database file.
        SQLALCHEMY_DATABASE_URI (str): The connection string for the SQLAlchemy engine.
        FLASK_SECRET_KEY (str): Secret key used for cryptographic signing and sessions.
        OPENAI_API_KEY (str): Authentication token for the OpenAI API.
        OPENAI_MODEL (str): The specific OpenAI model ID (e.g., 'gpt-4o-mini').
        LLM_TEMPERATURE (float): Sampling temperature (0.0 to 2.0).
            Lower is more deterministic, higher is more creative.
        LLM_MAX_TOKENS (int): The maximum length of the generated AI response.
    """
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / 'apps' / 'kyzo_backend' / 'data'

    DATABASE_PATH: Path = DATA_DIR / 'kyzo-data.sqlite'
    SQLALCHEMY_DATABASE_URI: str = ""

    OPENAI_API_KEY: str = Field(...)

    OPENAI_MODEL: str = Field("gpt-4o-mini", description="The AI model used for generation")
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


    @field_validator("OPENAI_API_KEY")
    @classmethod
    def check_not_empty(cls, value: str) -> str:
        """
        Ensures that critical security keys are not provided as empty strings.

        Args:
            value (str): The value of the configuration field being validated.

        Returns:
            str: The validated string.

        Raises:
            ValueError: If the key is missing, empty, or contains only whitespace.
        """
        if not value or value.strip() == "":
            raise ValueError("Value cannot be empty!")
        return value


fastapi_settings = FastAPISettings()
