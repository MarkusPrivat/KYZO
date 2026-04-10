from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.managers import TestManager
from apps.kyzo_backend.schemas import (TestRead,
                                       TestGenerate,
                                       TestQuestionFinalize,
                                       TestQuestionRead,
                                       TestQuestionStepRead,
                                       TestSessionRead)


router = APIRouter(
    prefix="/api/test",
    tags=["Test"]
)


def get_test_manager(db: Session = Depends(get_db)) -> TestManager:
    """
    Dependency provider for the TestManager.

    This function facilitates the injection of a TestManager instance into
    API routes. It automatically retrieves the database session via
    FastAPI's dependency system to ensure consistent database access.

    Args:
        db (Session): The SQLAlchemy database session injected by FastAPI.

    Returns:
        TestManager: An initialized instance of the TestManager.
    """
    return TestManager(db)


@router.post("/{test_id}/question/{test_question_id}/finalize", response_model=TestQuestionStepRead)
async def finalize_test_question(
        test_id: int,
        test_question_id: int,
        test_question_data: TestQuestionFinalize,
        test_manager: TestManager = Depends(get_test_manager)
):
    """
    Evaluates a student's answer and determines the next step in the test session.

    This endpoint marks a specific question as completed, calculates the points
    earned based on the student's choice, and automatically identifies the
    next question to be answered.

    Workflow:
    1. Validate the test and the specific test-question association.
    2. Guard: Prevent re-submission if the question is already answered (400).
    3. Evaluate: Compare choice with the correct answer and update the test score.
    4. Transition: Fetch the next pending question or signal that all are done.

    Args:
        test_id (int): The unique ID of the active test session.
        test_question_id (int): The ID of the specific question instance to finalize.
        test_question_data (TestQuestionFinalize): Data containing the student's choice
            and time spent.
        test_manager (TestManager): Injected manager to handle the business logic.

    Returns:
        TestQuestionStepRead: A composite object containing the 'next_question'
            (if available) and the 'all_done' status flag.

    Raises:
        HTTPException (404): If the test or the test-question record is not found.
        HTTPException (400): If the question was already finalized or the choice index
            is out of range.
        HTTPException (500): If a database error occurs during evaluation.
    """
    return test_manager.finalize_test_question(
        test_id,
        test_question_id,
        test_question_data
    )


@router.post("/{test_id}/finalize", response_model=TestRead)
async def finalize_test(
    test_id: int,
    test_manager: TestManager = Depends(get_test_manager)
):
    """
    Finalizes a test session and marks it as completed.

    This endpoint transitions the test status to 'is_done'. Once finalized,
    no further answers can be submitted. It serves as the official conclusion
    of the student's engagement with the current set of questions.

    Workflow:
    1. Verify the existence of the test ID.
    2. Guard: Ensure the test hasn't been finalized already (TEST_ALREADY_DONE).
    3. Guard: Ensure all questions have been answered.
    4. Update: Set 'is_done' to True and commit the session.

    Args:
        test_id (int): The unique identifier of the test to be finalized.
        test_manager (TestManager): Injected manager to handle the finalization logic.

    Returns:
        TestRead: The finalized test record with its terminal status.

    Raises:
        HTTPException (404): If the test ID does not exist.
        HTTPException (400): If the test is already processed or has unanswered questions.
        HTTPException (500): If a technical database error occurs.
    """
    return test_manager.finalize_test_session(test_id)



@router.post("/generate", response_model=TestRead, status_code=status.HTTP_201_CREATED)
async def generate_test(
        test_data: TestGenerate,
        num_of_questions: int,
        test_manager: TestManager = Depends(get_test_manager)
):
    """
    Generates a new randomized test session based on user and subject criteria.

    This endpoint orchestrates the creation of a test by selecting a specific
    number of questions. It performs rigorous validation of foreign keys and
    availability before persisting any data.

    Workflow:
    1. Validate existence of User, Subject, and optional Topic.
    2. Check if the database contains enough questions to satisfy the request.
    3. If 'num_of_questions' exceeds availability, return a 400 Bad Request.
    4. On success, persist the test session, link random questions, and return the record.

    Args:
        test_data (TestGenerate): Schema containing user, subject, and topic IDs.
        num_of_questions (int): Desired number of questions for the session.
        test_manager (TestManager): Injected manager to handle the generation logic.

    Returns:
        TestRead: The initialized test session record.

    Raises:
        HTTPException (400): If not enough questions are available in the pool.
        HTTPException (404): If the user, subject, or topic does not exist.
        HTTPException (500): If a database error occurs during the generation process.
    """
    return test_manager.generate_test_session(test_data, num_of_questions)



@router.get("/{test_id}", response_model=TestRead)
async def get_test_by_id(
    test_id: int,
    test_manager: TestManager = Depends(get_test_manager)
):
    """
    Retrieves a specific test session and its associated data by ID.

    This endpoint fetches the full test record, including its current score,
    completion status (is_done), and linked question metadata. It is typically
    used to resume a session or view finalized results.

    Workflow:
    1. Query the TestManager for the test record.
    2. Raise 404 Not Found if the record does not exist.
    3. Return the test object on success.

    Args:
        test_id (int): The unique database identifier of the test.
        test_manager (TestManager): Injected manager to handle the retrieval logic.

    Returns:
        TestRead: The complete test session record.

    Raises:
        HTTPException (404): If the test ID does not exist.
        HTTPException (500): If a technical error occurs during retrieval.
    """
    return test_manager.get_test_by_id(test_id)



@router.get("/question/{test_question_id}", response_model=TestQuestionRead)
async def get_test_question_by_id(
    test_question_id: int,
    test_manager: TestManager = Depends(get_test_manager)
):
    """
    Retrieves a specific test question record by its unique database ID.

    This endpoint is used to fetch the current state of a single question
    within a test session, including whether it has been answered (is_done)
    and the maximum points assigned.

    Workflow:
    1. Query the TestManager for the specific test question record.
    2. Raise 404 Not Found if the record does not exist.
    3. Return the test question object on success.

    Args:
        test_question_id (int): The unique ID of the test question entry.
        test_manager (TestManager): Injected manager to handle the retrieval logic.

    Returns:
        TestQuestionRead: The test question record details.

    Raises:
        HTTPException (404): If the test question ID does not exist.
        HTTPException (500): If a technical error occurs during retrieval.
    """
    return test_manager.get_test_question_by_id(test_question_id)


@router.get("/{test_id}/session", response_model=TestSessionRead)
async def run_test_session(
    test_id: int,
    test_manager: TestManager = Depends(get_test_manager)
):
    """
    Provides all data required to start, resume, or continue a test session.

    This endpoint acts as the primary orchestrator for the testing UI. It
    retrieves the test metadata and determines the next pending question
    to be answered, allowing for a seamless resume functionality.

    Workflow:
    1. Fetch the test by ID via TestManager.
    2. Check if the test is already marked as 'is_done' (returns 400).
    3. Identify the next unanswered question in the sequence.
    4. Return a composite object containing the test metadata, the next
       question, and a completion flag.

    Args:
        test_id (int): The unique identifier of the test session.
        test_manager (TestManager): Injected manager to handle the session logic.

    Returns:
        TestSessionRead: A composite object holding the test, the next
            question (if any), and the 'all_done' status.

    Raises:
        HTTPException (404): If the test ID does not exist.
        HTTPException (400): If the test session is already completed.
        HTTPException (500): If a database error occurs.
    """
    return test_manager.run_test_session(test_id)
