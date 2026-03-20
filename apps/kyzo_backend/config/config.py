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
    Uses Pydantic Settings to automatically load from environment variables.
    """
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / 'apps' / 'kyzo_backend' / 'data'

    DATABASE_PATH: Path = DATA_DIR / 'kyzo-data.sqlite'
    SQLALCHEMY_DATABASE_URI: str = ""

    FLASK_SECRET_KEY: str = Field(...)
    OPENAI_API_KEY: str = Field(...)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignoriert weitere Variablen in der .env
    )

    def __init__(self, **values: Any):
        """
        Initializes the settings, ensures data directories exist, and
        constructs the final SQLAlchemy database URI.

        Args:
            **values (Any): Arbitrary keyword arguments passed to the Pydantic model.
        """
        super().__init__(**values)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.DATABASE_PATH.as_posix()}"


    @field_validator("FLASK_SECRET_KEY", "OPENAI_API_KEY")
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
