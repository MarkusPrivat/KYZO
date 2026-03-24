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
    CREATE_SUBJECT_ERROR = "Error adding subject:"
    CREATE_TOPIC_ERROR = "Error adding topic:"
    GET_ALL_SUBJECTS_ERROR = "Error fetching subjects:"
    GET_ALL_TOPICS_FROM_SUBJECT_ERROR = "Error fetching topics from this subject:"
    GET_SUBJECT_ERROR = "Error fetching subject:"
    GET_TOPIC_FROM_SUBJECT_ERROR = "Error fetching topic from this subject:"
    GET_TOPIC_ERROR = "Error fetching topic:"
    NO_SUBJECTS = "No subjects in database!"
    NO_TOPICS_FOR_SUBJECTS = "No topics for this subject in database!"
    STATUS_UPDATE_ERROR = "Status update error:"
    SUBJECT_ALREADY_EXISTS = "Subject already exist"
    SUBJECT_NOT_FOUND = "Subject not found!"
    TOPIC_ALREADY_EXISTS = "Topic already exist"
    TOPIC_NOT_FOUND = "Topic not found!"
    UPDATE_SUBJECT_ERROR = "Update subject error:"
    UPDATE_TOPIC_ERROR = "Update topic error:"
