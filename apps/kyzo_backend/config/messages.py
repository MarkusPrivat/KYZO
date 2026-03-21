from dataclasses import dataclass


@dataclass(frozen=True)
class UserMessages:
    """
    Centralized store for user-related feedback and error messages.

    This class provides standardized strings for API responses and logging,
    ensuring consistency across the UserManager and FastAPI routes.
    All attributes are immutable (frozen).
    """
    CREATE_ERROR: str = "Error adding user:"
    GET_USER_ERROR: str = "Error fetching user:"
    NOT_FOUND: str = "User not found!"
    UPDATE_USER_ERROR: str = "Update error:"