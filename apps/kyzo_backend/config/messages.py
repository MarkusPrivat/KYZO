from dataclasses import dataclass


@dataclass(frozen=True)
class UserMessages:
    """
    Centralized store for user-related feedback and error messages.

    This class provides standardized strings for API responses and logging,
    ensuring consistency across the UserManager and FastAPI routes.
    All attributes are immutable (frozen).
    """
    CREATE_ERROR = "Error adding user:"
    EMAIL_ALREADY_EXIST = "Email already registered!"
    GET_USER_ERROR = "Error fetching user:"
    NOT_FOUND = "User not found!"
    UPDATE_USER_ERROR = "Update error:"