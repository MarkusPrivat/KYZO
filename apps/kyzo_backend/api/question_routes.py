from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, status, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import LLMProvider
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.managers import QuestionManager
from apps.kyzo_backend.schemas import (QuestionInputCreate,
                                       QuestionInputUpdate,
                                       QuestionInputRead,
                                       QuestionUpdate,
                                       QuestionRead,
                                       QuestionStatus
                                       )

router = APIRouter(
    prefix="/api/questions",
    tags=["Questions"]
)


def get_question_manager(db: Session = Depends(get_db)) -> QuestionManager:
    """
    Dependency provider for the QuestionManager.

    This function facilitates the injection of a QuestionManager instance into
    API routes. It automatically retrieves the database session via
    FastAPI's dependency system and passes it to the manager.

    Args:
        db (Session): The SQLAlchemy database session provided by get_db.

    Returns:
        QuestionManager: An initialized instance ready for business logic operations.
    """
    return QuestionManager(db)


def parse_question_input(input_data_json: str = Form(...)) -> QuestionInputCreate:
    try:
        return QuestionInputCreate.model_validate_json(input_data_json)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error.errors()
        ) from error


@router.post("/input/add", status_code=status.HTTP_201_CREATED, response_model=str)
async def add_question(
        num_of_questions: int,
        llm_provider: LLMProvider,
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
    OCR processing for files (images/PDFs), AI-driven question extraction
    via the chosen provider, and database persistence.

    Args:
        num_of_questions (int): The target number of questions to generate.
        llm_provider (LLMProvider): The AI service to use (e.g., 'openai' or 'google').
        input_data (QuestionInputCreate): Metadata including subject_id, topic_id,
                                          grade, and optional raw text content.
        files (list[UploadFile]): One or more files for OCR. If no raw text is provided
                                  in input_data, files are mandatory.
        question_manager (QuestionManager): Injected manager to handle the orchestration
                                            of file, AI, and database services.

    Returns:
        str: A localized success message confirming the count of generated questions.

    Raises:
        HTTPException:
            - 400 (Bad Request): If validation fails (e.g., neither text nor files provided).
            - 404 (Not Found): If the subject or topic IDs do not exist.
            - 502 (Bad Gateway): If the external AI service (Google/OpenAI) fails.
            - 500 (Internal Error): For database or unexpected processing failures.
    """
    return await question_manager.add_question_input_with_file(
        num_of_questions=num_of_questions,
        llm_provider=llm_provider,
        question_input_data=input_data,
        files=files
    )


@router.post(
    "/inputs/{question_input_id}/finalize",
    status_code=status.HTTP_201_CREATED,
    response_model=str
)
async def finalize_input(
        question_input_id: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Promotes AI-generated drafts to the permanent global question pool.

    This endpoint finalizes a generation job by transforming drafts into
    permanent Question records and locking the source input.

    Args:
        question_input_id (int): The ID of the QuestionInput record to be finalized.
        question_manager (QuestionManager): Injected manager for business logic.

    Returns:
        str: A success message confirming the number of questions added to the pool.

    Raises:
        HTTPException (400): If the input is already processed or contains no drafts.
        HTTPException (404): If the question_input_id is not found.
        HTTPException (500): If the database transaction fails.
    """
    return question_manager.create_questions_from_question_input(question_input_id)


@router.post("/inputs/{question_input_id}/ai-generate", response_model=str)
async def extract_questions_from_raw_input(
        question_input_id: int,
        num_of_questions: int,
        llm_provider: LLMProvider,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Manually triggers AI question generation for a specific raw input record.

    This serves as a recovery or re-processing mechanism. It allows re-running
    the extraction for an existing record, providing flexibility to switch
    between different AI providers or adjust the target question count.

    Args:
        question_input_id (int): The unique ID of the QuestionInput to process.
        num_of_questions (int): Number of questions to be generated (Target count).
        llm_provider (LLMProvider): The AI service to use (e.g., 'openai' or 'google').
        question_manager (QuestionManager): Injected manager for business logic.

    Returns:
        str: Success message with the count of generated questions.

    Raises:
        HTTPException:
            - 400: If the record is already processed.
            - 404: If the record ID does not exist.
            - 502: If the chosen AI service is unavailable.
            - 500: For unexpected internal or database errors.
    """
    return question_manager.extract_questions_from_raw_input(
        question_input_id=question_input_id,
        num_of_questions=num_of_questions,
        llm_provider=llm_provider
    )


@router.get("/list-all", response_model=list[QuestionRead])
async def get_questions(
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Retrieves the complete list of all questions available in the global pool.

    This endpoint returns every question across all subjects and topics.
    It is primarily used for administrative overview or broad content audits.

    Args:
        question_manager (QuestionManager): Injected manager for business logic.

    Returns:
        list[QuestionRead]: A list of all questions, formatted according to the
                           QuestionRead schema.

    Raises:
        HTTPException (404): If the question pool is currently empty.
        HTTPException (500): If a database error occurs during retrieval.
    """
    return question_manager.get_all_questions()


@router.get("/subjects/{subject_id}", response_model=list[QuestionRead])
async def get_questions_for_subject(
        subject_id: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Retrieves all questions filtered by a specific subject.

    This endpoint is ideal for subject-specific browsing, general study
    overviews, or broad quiz generation within a single discipline.

    Args:
        subject_id (int): The unique ID of the subject to filter by.
        question_manager (QuestionManager): Injected manager for business logic.

    Returns:
        list[QuestionRead]: A list of questions belonging to the specified subject.

    Raises:
        HTTPException (404): If no questions are found for the given subject ID.
        HTTPException (500): If a database error occurs during retrieval.
    """
    return question_manager.get_questions_for_subject_topic(subject_id)


@router.get("/subjects/{subject_id}/topics/{topic_id}", response_model=list[QuestionRead])
async def get_questions_for_subject_topic(
        subject_id: int,
        topic_id: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Retrieves questions filtered by both subject and a specific topic.

    This is the most granular retrieval endpoint, ideal for targeted practice
    sessions or specific classroom modules.

    Args:
        subject_id (int): The unique ID of the subject.
        topic_id (int): The unique ID of the topic within that subject.
        question_manager (QuestionManager): Injected manager for business logic.

    Returns:
        list[QuestionRead]: A list of questions matching both criteria.

    Raises:
        HTTPException (404): If no questions exist for this specific combination.
        HTTPException (500): If a database error occurs during the query.
    """
    return question_manager.get_questions_for_subject_topic(
        subject_id,
        topic_id
    )


@router.get("/{question_id}", response_model=QuestionRead)
async def get_question_by_id(
        question_id: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Retrieves a single question from the global pool by its unique identifier.

    This endpoint is used when the specific ID of a question is already known,
    e.g., when loading a single question for detailed viewing or editing.

    Args:
        question_id (int): The unique primary key of the question.
        question_manager (QuestionManager): Injected manager for business logic.

    Returns:
        QuestionRead: The complete question data matching the ID.

    Raises:
        HTTPException (404): If no question exists with the provided ID.
        HTTPException (500): If a database error occurs during retrieval.
    """
    return question_manager.get_question_by_id(question_id)


@router.get("/inputs/{question_input_id}", response_model=QuestionInputRead)
async def get_question_input_by_id(
        question_input_id: int,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Retrieves a specific question generation job and its AI-generated drafts.

    This endpoint allows for monitoring the status of a generation request
    and fetching raw drafts for review before promotion.

    Args:
        question_input_id (int): The unique identifier of the generation job.
        question_manager (QuestionManager): Injected manager for business logic.

    Returns:
        QuestionInputRead: The full record including raw input, drafts, and status.

    Raises:
        HTTPException (404): If the specified ID does not exist.
        HTTPException (500): If a database error occurs.
    """
    return question_manager.get_question_input_by_id(question_input_id)


@router.put("/{question_id}/status", response_model=QuestionRead)
async def set_question_status(
        question_id: int,
        active: QuestionStatus,
        question_manager: QuestionManager = Depends(get_question_manager)
):
    """
    Toggles the visibility or operational status of a specific question.

    Use this to enable or disable questions in the live pool without deletion.
    This preserves data integrity and historical records for analytics.

    Args:
        question_id (int): The unique ID of the question to update.
        active (QuestionStatus): Schema containing the desired 'is_active' state.
        question_manager (QuestionManager): Injected manager for business logic.

    Returns:
        QuestionRead: The updated question record reflecting the new status.

    Raises:
        HTTPException (404): If the question_id does not exist.
        HTTPException (500): If the status update fails.
    """
    return question_manager.set_question_status(
        question_id,
        active
    )


@router.put("/inputs/{question_input_id}/edit", response_model=QuestionInputRead)
async def update_question_input(
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
        question_input_id (int): The unique ID of the QuestionInput record.
        question_input_update (QuestionInputUpdate): The partial data to update.
        question_manager (QuestionManager): Injected manager for business logic.

    Returns:
        QuestionInputRead: The updated record including all current drafts.

    Raises:
        HTTPException (404): If the specific QuestionInput ID does not exist.
        HTTPException (500): If a database or internal processing error occurs.
    """
    return question_manager.update_question_input(
        question_input_id,
        question_input_update
    )


@router.put("/{question_id}/edit", response_model=QuestionRead)
async def update_question_by_id(
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
        question_id (int): The unique identifier of the question to be updated.
        question_update (QuestionUpdate): The DTO containing the fields to update.
        question_manager (QuestionManager): Injected manager for business logic.

    Returns:
        QuestionRead: The updated question record.

    Raises:
        HTTPException (404): If no question is found with the provided ID.
        HTTPException (500): If the update fails due to a database error.
    """
    return question_manager.update_question(
        question_id,
        question_update
    )
