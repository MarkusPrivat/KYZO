"""
Service layer handling user authentication and JWT access token generation.
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import fastapi_settings
from apps.kyzo_backend.managers import UserManager


class AuthService:
    """
    Service responsible for handling user authentication and security operations.

    The AuthService coordinates between the user database and security protocols.
    It manages password verification using modern hashing algorithms and handles
    the generation of JSON Web Tokens (JWT) for secure API access.

    Attributes:
        db (Session): The database session used for user lookups.
        user_manager (UserManager): Internal manager for database interactions.
        password_hash (PasswordHash): The hashing algorithm provider (Argon2/Bcrypt).
        dummy_hash (str): A pre-computed hash used to mitigate timing attacks.
    """

    def __init__(self, db: Session):
        """
        Initializes the AuthService with database connectivity and security providers.

        This constructor sets up the internal UserManager and configures the
        password hashing engine. It also pre-calculates a dummy hash to be
        used in constant-time password verification attempts.

        Args:
            db (Session): The SQLAlchemy database session provided by
                FastAPI's dependency injection.
        """
        self.db = db
        self.user_manager = UserManager(self.db)
        self.password_hash = PasswordHash.recommended()
        self.dummy_hash = self.password_hash.hash("dummypassword")

    def authenticate_user(self, form_data: OAuth2PasswordRequestForm) -> str:
        """
        Orchestrates the complete user authentication flow.

        This method verifies user credentials by performing a database lookup
        and a cryptographic password check. It is designed to be resilient
        against timing attacks by ensuring that a constant-time password verification
        is attempted against a dummy hash even if the requested user does not exist.

        Args:
            form_data (OAuth2PasswordRequestForm): FastAPI's built-in container
                extracting the 'username' (mapped to email) and 'password' from the
                multipart form request.

        Returns:
            str: A signed, cryptographically secure JWT access token containing
                the user identity ('sub') and the assigned role ('scope').

        Raises:
            HTTPException:
                - 401 (Unauthorized): If the user is not found, the provided
                  password does not match the stored cryptographic hash, or the
                  account is otherwise disabled.
        """
        user_unauthorized = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

        user = self.user_manager.get_user_by_email(form_data.username)

        if not user:
            self.verify_password(form_data.password, self.dummy_hash)
            raise user_unauthorized

        if not self.verify_password(form_data.password, user.password_hash):
            raise user_unauthorized

        access_token = self._create_access_token(
            data={"sub": user.email, "scope": user.role.value},
            expires_delta=timedelta(
                minutes=fastapi_settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
        return access_token

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a plain-text password against a stored cryptographic hash.

        This method uses the configured hashing algorithm (e.g., Argon2 or Bcrypt)
        to safely compare the provided password with the hash stored in the
        database.

        Args:
            plain_password (str): The raw password string to be checked.
            hashed_password (str): The pre-calculated hash from the database.

        Returns:
            bool: True if the password matches the hash, False otherwise.
        """
        return self.password_hash.verify(plain_password, hashed_password)

    @staticmethod
    def _create_access_token(data: dict, expires_delta: timedelta) -> str:
        """
        Creates a signed JSON Web Token (JWT) with a defined expiration.

        This internal helper takes a data payload and signs it using the
        HS256 algorithm and the system's secret key. It explicitly requires
        an expiration delta to ensure no tokens are created with an
        infinite lifespan.

        Args:
            data (dict): The payload to encode (typically contains the 'sub' claim).
            expires_delta (timedelta): The duration for which the token remains valid.

        Returns:
            str: The encoded and signed JWT string.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})

        return jwt.encode(
            to_encode,
            fastapi_settings.AUTH_SECRET_KEY,
            algorithm=fastapi_settings.ALGORITHM
        )
