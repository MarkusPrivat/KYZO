from dataclasses import dataclass


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


@dataclass(frozen=True)
class OpenAIMessages:
    LLM_CONNECTION_ERROR = "Server connection error:"
    GENERATION_FAILED = "AI generation failed:"


@dataclass(frozen=True)
class QuestionMessages:
    CREATE_QUESTION_ERROR = "Error adding question:"
    CREATE_QUESTION_INPUT_ERROR = "Error adding input questions:"
    GET_ALL_QUESTIONS_ERROR = "Error fetching questions:"
    GET_QUESTION_ERROR = "Error fetching question:"
    GET_QUESTION_INPUT_ERROR = "Error fetching question:"
    NO_QUESTION_TO_PROCESS = "There are no extracted questions to process."
    QUESTION_INPUT_ALREADY_PROCESSED= "This input has already been processed"
    QUESTION_INPUT_NOT_FOUND = "Question input not Found!"
    QUESTION_INPUT_PROCESSED = "{question_count} Extracted Questions successfully generated"
    QUESTION_INPUT_TO_QUESTION = "{new_questions_count} Question generated from Question Input"
    QUESTION_NOT_FOUND = "No question found!"
    STATUS_UPDATE_ERROR = "Status update error:"
    UPDATE_QUESTION_ERROR = "Update question error:"
    UPDATE_QUESTION_INPUT_ERROR = "Update question input error:"


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
