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
    GET_ALL_USER_ERROR = "Error fetching users:"
    GET_USER_ERROR = "Error fetching user:"
    NO_USERS = "No users in database!"
    UPDATE_USER_ERROR = "Update user error:"
    USER_NOT_FOUND = "User not found!"


@dataclass(frozen=True)
class KnowledgeMessages:
    CREATE_ERROR = "Error adding subject:"
    GET_ALL_SUBJECTS_ERROR = "Error fetching subjects:"
    GET_SUBJECT_ERROR = "Error fetching subject:"
    STATUS_UPDATE_ERROR = "Status update error:"
    SUBJECT_ALREADY_EXISTS = "Subject already exist"
    UPDATE_SUBJECT_ERROR = "Update subject error:"
