"""
API router for question management and orchestrating the AI-driven question generation.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, status, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from apps.kyzo_backend.api.depends.role_depends import require_teacher_or_admin
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.data import User
from apps.kyzo_backend.managers import KnowledgeManager, QuestionManager
from apps.kyzo_backend.schemas import (
    QuestionInputCreate,
    QuestionInputUpdate,
    QuestionInputRead,
    QuestionUpdate,
    QuestionRead,
    QuestionStatus
)

router = APIRouter(
    prefix="/questions",
    tags=["Questions"]
)


def get_knowledge_manager(db: Session = Depends(get_db)) -> KnowledgeManager:
    """
    Dependency provider for the KnowledgeManager.
    """
    return KnowledgeManager(db)


def get_question_manager(
    db: Session = Depends(get_db),
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
) -> QuestionManager:
    """
    Dependency provider for the QuestionManager, resolving nested manager dependencies.

    This function coordinates the injection of a QuestionManager instance into API routes.
    By fetching the required KnowledgeManager via FastAPI's dependency system, it eliminates
    tight coupling within the manager's constructor while ensuring that both managers
    share the exact same database session context for transaction safety.

    Args:
        db (Session): The SQLAlchemy database session provided by 'get_db'.
        knowledge_manager (KnowledgeManager): The resolved downstream manager instance
            required for cross-domain educational content operations.

    Returns:
        QuestionManager: A fully initialized QuestionManager instance ready for
            business logic operations.
    """
    return QuestionManager(
        db=db,
        knowledge_manager=knowledge_manager
    )


def parse_question_input(input_data_json: str = Form(...)) -> QuestionInputCreate:
    """
    Parses and validates a JSON string from a multipart form field into a Pydantic model.

    This dependency is required because FastAPI cannot natively mix 'Form' fields
    and 'BaseModel' JSON bodies in a single multipart/form-data request. It manually
    triggers Pydantic's validation logic.

    Args:
        input_data_json (str): The raw JSON string containing metadata for question
                               creation (e.g., subject_id, topic_id, grade).

    Returns:
        QuestionInputCreate: The validated Pydantic data transfer object.

    Raises:
        HTTPException:
            - 422 (Unprocessable Entity): If the provided JSON string is malformed
              or fails to meet the schema requirements defined in QuestionInputCreate.
    """
    try:
        return QuestionInputCreate.model_validate_json(input_data_json)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error.errors()
        ) from error


@router.post("/input/add", status_code=status.HTTP_201_CREATED, response_model=str)
async def add_question(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        num_of_questions: int,
        input_data: QuestionInputCreate = Depends(parse_question_input),
        files: Optional[list[UploadFile]] = File(
            default=None,
            description="Optional: Select one or more images (JPG, PNG) or PDF files."
        ),
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Initiates the question generation pipeline from either raw text or uploaded files.

    This endpoint coordinates the full creation flow: metadata validation,
    OCR processing for files (if provided), and AI-driven question extraction
    via an automated multi-provider fallback logic.

    OCR Architecture:
        - Primary: Gemini 3.1
        - Fallback: gemma-4-26b-a4b

    Question Generation Architecture:
        - Primary: Gemini 3.1
        - Fallback: GPT-4o-mini

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        num_of_questions (int): The target number of questions to generate.
        input_data (QuestionInputCreate): Injected metadata (via Form/Query parsing)
            including subject_id, topic_id, grade, and optional raw text content.
        files (Optional[list[UploadFile]]): Multipart file uploads for OCR. Can be
            None if raw text is provided via input_data.
        question_manager (QuestionManager): Injected manager instance to handle the
            orchestration of file processing, LLM services, and database persistence.

    Returns:
        str: A localized success message confirming the count of generated questions.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 400 (Bad Request): If validation fails (e.g., neither text nor files provided).
            - 404 (Not Found): If the specified subject_id or topic_id does not exist.
            - 502 (Bad Gateway): If the external AI service providers fail or time out.
            - 500 (Internal Server Error): For database or unexpected pipeline processing failures.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return await question_manager.add_question_input_with_file(
        num_of_questions=num_of_questions,
        question_input_data=input_data,
        files=files
    )


@router.post(
    "/inputs/{question_input_id}/finalize",
    status_code=status.HTTP_201_CREATED,
    response_model=str
)
async def finalize_input(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        question_input_id: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Promotes AI-generated drafts to the permanent global question pool.

    This endpoint finalizes a generation job by transforming drafts into
    permanent Question records and locking the source input.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        question_input_id (int): The unique database identifier of the QuestionInput
            record to be finalized.
        question_manager (QuestionManager): Injected manager instance for question
            pool and generation business logic.

    Returns:
        str: A localized success message confirming the number of questions added
            to the pool.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 400 (Bad Request): If the input is already processed or contains no drafts.
            - 404 (Not Found): If the question_input_id does not exist.
            - 500 (Internal Server Error): If a database transaction fails.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return question_manager.create_questions_from_question_input(question_input_id)


@router.post("/inputs/{question_input_id}/ai-generate", response_model=str)
async def extract_questions_from_raw_input(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        question_input_id: int,
        num_of_questions: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Manually triggers AI question generation for a specific raw input record.

    This serves as a recovery or re-processing mechanism. It allows re-running
    the extraction for an existing record with an automated multi-provider
    fallback logic.

    Question Generation Architecture:
        - Primary: Gemini 3.1
        - Fallback: GPT-4o-mini

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        question_input_id (int): The unique database identifier of the QuestionInput
            record to process.
        num_of_questions (int): Target number of questions to be generated.
        question_manager (QuestionManager): Injected manager instance for question
            pool and generation business logic.

    Returns:
        str: A localized success message confirming the count of generated questions.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 400 (Bad Request): If the record is already processed.
            - 404 (Not Found): If the record ID does not exist.
            - 502 (Bad Gateway): If all configured AI services fail or are unavailable.
            - 500 (Internal Server Error): For unexpected internal or database errors.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return question_manager.extract_questions_from_raw_input(
        question_input_id=question_input_id,
        num_of_questions=num_of_questions,
    )


@router.get("/list-all", response_model=list[QuestionRead])
async def get_questions(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Retrieves the complete list of all questions available in the global pool.

    This endpoint returns every question across all subjects and topics.
    It is primarily used for administrative overview or broad content audits.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        question_manager (QuestionManager): Injected manager instance for question
            pool and generation business logic.

    Returns:
        list[QuestionRead]: A list of all questions, formatted according to the
                           QuestionRead schema.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If the question pool is currently empty.
            - 500 (Internal Server Error): If a database error occurs during retrieval.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return question_manager.get_all_questions()


@router.get("/subjects/{subject_id}", response_model=list[QuestionRead])
async def get_questions_for_subject(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        subject_id: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Retrieves all questions filtered by a specific subject.

    This endpoint is ideal for subject-specific browsing, general study
    overviews, or broad quiz generation within a single discipline.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        subject_id (int): The unique database identifier of the subject to filter by.
        question_manager (QuestionManager): Injected manager instance for question
            pool and generation business logic.

    Returns:
        list[QuestionRead]: A list of questions belonging to the specified subject.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If no questions are found for the given subject ID.
            - 500 (Internal Server Error): If a database error occurs during retrieval.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return question_manager.get_questions_for_subject_topic(subject_id)


@router.get("/subjects/{subject_id}/topics/{topic_id}", response_model=list[QuestionRead])
async def get_questions_for_subject_topic(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        subject_id: int,
        topic_id: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Retrieves questions filtered by both subject and a specific topic.

    This is the most granular retrieval endpoint, ideal for targeted practice
    sessions or specific classroom modules.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        subject_id (int): The unique database identifier of the parent subject.
        topic_id (int): The unique database identifier of the specific topic.
        question_manager (QuestionManager): Injected manager instance for question
            pool and generation business logic.

    Returns:
        list[QuestionRead]: A list of questions matching both criteria.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If no questions exist for this specific combination.
            - 500 (Internal Server Error): If a database error occurs during the query.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return question_manager.get_questions_for_subject_topic(
        subject_id,
        topic_id
    )


@router.get("/{question_id}", response_model=QuestionRead)
async def get_question_by_id(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        question_id: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Retrieves a single question from the global pool by its unique identifier.

    This endpoint is used when the specific ID of a question is already known,
    e.g., when loading a single question for detailed viewing or editing.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        question_id (int): The unique primary key identifier of the question.
        question_manager (QuestionManager): Injected manager instance for question
            pool and generation business logic.

    Returns:
        QuestionRead: The complete question data matching the ID.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If no question exists with the provided ID.
            - 500 (Internal Server Error): If a database error occurs during retrieval.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return question_manager.get_question_by_id(question_id)


@router.get("/inputs/{question_input_id}", response_model=QuestionInputRead)
async def get_question_input_by_id(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        question_input_id: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Retrieves a specific question generation job and its AI-generated drafts.

    This endpoint allows for monitoring the status of a generation request
    and fetching raw drafts for review before promotion.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        question_input_id (int): The unique database identifier of the generation job.
        question_manager (QuestionManager): Injected manager instance for question
            pool and generation business logic.

    Returns:
        QuestionInputRead: The full record including raw input, drafts, and status.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If the specified ID does not exist.
            - 500 (Internal Server Error): If a database error occurs during retrieval.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return question_manager.get_question_input_by_id(question_input_id)


@router.put("/{question_id}/status", response_model=QuestionRead)
async def set_question_status(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        question_id: int,
        active: QuestionStatus,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Toggles the visibility or operational status of a specific question.

    Use this to enable or disable questions in the live pool without deletion.
    This preserves data integrity and historical records for analytics.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        question_id (int): The unique primary key identifier of the question to update.
        active (QuestionStatus): Pydantic enum or container containing the desired
            activation state.
        question_manager (QuestionManager): Injected manager instance for question
            pool and generation business logic.

    Returns:
        QuestionRead: The updated question record reflecting the new status.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If the question_id does not exist.
            - 500 (Internal Server Error): If the status update or database
              transaction fails.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return question_manager.set_question_status(
        question_id,
        active
    )


@router.put("/inputs/{question_input_id}/edit", response_model=QuestionInputRead)
async def update_question_input(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        question_input_id: int,
        question_input_update: QuestionInputUpdate,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Updates an existing question generation job before finalization.

    This endpoint acts as the 'Review & Edit' hub. It allows users to correct
    metadata or the source text after the AI has generated drafts. This ensures
    high-quality content before promotion to the global pool.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        question_input_id (int): The unique database identifier of the QuestionInput record.
        question_input_update (QuestionInputUpdate): Pydantic container for the
            partial data to update (e.g., core metadata or source text).
        question_manager (QuestionManager): Injected manager instance for question
            pool and generation business logic.

    Returns:
        QuestionInputRead: The updated record including all current drafts.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If the specific QuestionInput ID does not exist.
            - 500 (Internal Server Error): If a database or internal processing
              error occurs during the update.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return question_manager.update_question_input(
        question_input_id,
        question_input_update
    )


@router.put("/{question_id}/edit", response_model=QuestionRead)
async def update_question_by_id(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        question_id: int,
        question_update: QuestionUpdate,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Updates the content or properties of an existing question.

    This endpoint allows for granular changes to a question that is already
    in the live pool, such as fixing typos, updating answer options,
    or adjusting difficulty levels.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        question_id (int): The unique database identifier of the question to be updated.
        question_update (QuestionUpdate): Pydantic DTO container containing the
            fields to update.
        question_manager (QuestionManager): Injected manager instance for question
            pool and generation business logic.

    Returns:
        QuestionRead: The updated question record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If no question is found with the provided ID.
            - 500 (Internal Server Error): If the update fails due to a database
              error or transaction failure.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return question_manager.update_question(
        question_id,
        question_update
    )
