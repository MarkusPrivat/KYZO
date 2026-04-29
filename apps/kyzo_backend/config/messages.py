from dataclasses import dataclass


@dataclass(frozen=True)
class ImageProcessMessages:
    CORRUPT_FILE = "The uploaded PDF is corrupt or password protected."
    POPPLER_NOT_FOUND = "PDF processing service (Poppler) not configured on server."
    UNEXPECTED_ERROR = "Unexpected error:"


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
    UNEXPECTED_ERROR = "An unexpected error occurred during LLM processing:"


@dataclass(frozen=True)
class QuestionMessages:
    CREATE_QUESTION_ERROR = "Error adding question:"
    CREATE_QUESTION_INPUT_ERROR = "Error adding input questions:"
    GET_ALL_QUESTIONS_ERROR = "Error fetching questions:"
    GET_QUESTION_ERROR = "Error fetching question:"
    GET_QUESTION_INPUT_ERROR = "Error fetching question:"
    NO_QUESTION_TO_PROCESS = "There are no extracted questions to process."
    QUESTION_INPUT_ALREADY_PROCESSED = "This input has already been processed"
    QUESTION_INPUT_CONTENT_OR_FILE = "Please provide either text content OR a file, not both."
    QUESTION_INPUT_JSON_INVALID = "Invalid input_data_json:"
    QUESTION_INPUT_NOT_FOUND = "Question input not Found!"
    QUESTION_INPUT_PROCESSED = "{num_of_questions} Extracted Questions successfully generated"
    QUESTION_INPUT_TO_QUESTION = "{new_questions_count} Question generated from Question Input"
    QUESTION_NOT_FOUND = "No question found!"
    STATUS_UPDATE_ERROR = "Status update error:"
    UPDATE_QUESTION_ERROR = "Update question error:"
    UPDATE_QUESTION_INPUT_ERROR = "Update question input error:"


@dataclass(frozen=True)
class SchemasMessages:
    SUBJECT_NAME_LEN = "Subject name must have at least 3 characters."
    TOPIC_NAME_LEN = "Topic name must have at least 2 characters."
    IS_DONE_MUST_BE_TRUE = "The 'is_done' flag must be True to finalize a test."


@dataclass(frozen=True)
class TestMessages:
    ANSWER_OUT_OF_RANGE = "Answer not possible: Choice exceeds available options."
    CREATE_TEST_ERROR = "Error create Test session:"
    GET_TEST_ERROR = "Error fetching Test session:"
    GET_TEST_QUESTION_ERROR = "Error fetching Test question:"
    NEXT_QUESTION_ERROR = "Error retrieving next question:"
    NOT_DONE = "Test session not finished"
    NO_ENOUGH_QUESTIONS = "Only {available_questions} questions found"
    NO_MORE_QUESTIONS = "No more unanswered questions found."
    TEST_ALREADY_DONE = "This test session is already done and cannot be resumed."
    TEST_ALREADY_PROCESSED = "AI feedback already generated!"
    TEST_FINALIZE_ERROR = "Error during test finalization:"
    TEST_NOT_FOUND = "Test session not found."
    TEST_QUESTION_FINALIZE_ERROR = "Error during evaluation:"
    TEST_QUESTION_NOT_FOUND = "Question not found."
    TEST_QUESTION_ALREADY_DONE = "Question already answered."


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
