from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import (KnowledgeMessages,
                                      QuestionMessages,
                                      TestMessages,
                                      UserMessages)
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


@router.post("/{test_id}/question/{test_question_id}/finalize", response_model=TestQuestionStepRead)
async def finalize_test_question(
        test_id: int,
        test_question_id: int,
        test_question_data: TestQuestionFinalize,
        db: Session = Depends(get_db)
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
        db (Session): Injected database session.

    Returns:
        TestQuestionStepRead: A composite object containing the 'next_question'
            (if available) and the 'all_done' status flag.

    Raises:
        HTTPException (404): If the test or the test-question record is not found.
        HTTPException (400): If the question was already finalized or the choice index
            is out of range.
        HTTPException (500): If a database error occurs during evaluation.
    """
    test_manager = TestManager(db)

    success_question, result_question = test_manager.finalize_test_question(
        test_id,
        test_question_id,
        test_question_data
    )
    if not success_question:
        if result_question in [TestMessages.TEST_NOT_FOUND,
                               TestMessages.TEST_QUESTION_NOT_FOUND]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result_question
            )

        if result_question in [TestMessages.TEST_QUESTION_ALREADY_DONE,
                               TestMessages.ANSWER_OUT_OF_RANGE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_question
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result_question
        )

    return result_question


@router.post("/{test_id}/finalize", response_model=TestRead)
async def finalize_test(test_id: int, db: Session = Depends(get_db)):
    """
    Finalizes a test session and marks it as completed.

    This endpoint transition the test status to 'is_processed'. Once finalized,
    no further answers can be submitted. It serves as the official conclusion
    of the student's engagement with the current set of questions.

    Workflow:
    1. Verify the existence of the test ID.
    2. Guard: Ensure the test hasn't been finalized already (TEST_ALREADY_PROCESSED).
    3. Guard: Ensure all questions have been answered (NOT_DONE).
    4. Update: Set 'is_processed' to True and commit the session.

    Args:
        test_id (int): The unique identifier of the test to be finalized.
        db (Session): Injected database session.

    Returns:
        TestRead: The finalized test record with its terminal status.

    Raises:
        HTTPException (404): If the test ID does not exist.
        HTTPException (400): If the test is already processed or has unanswered questions.
        HTTPException (500): If a technical database error occurs.
    """
    test_manager = TestManager(db)

    success_test, result_test = test_manager.finalize_test_session(test_id)
    if not success_test:
        if result_test == TestMessages.TEST_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result_test
            )

        if result_test in [TestMessages.NOT_DONE, TestMessages.TEST_ALREADY_PROCESSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_test
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result_test
        )

    return result_test


@router.post("/generate", response_model=TestRead, status_code=status.HTTP_201_CREATED)
async def generate_test(
        test_data: TestGenerate,
        num_of_questions: int,
        db: Session = Depends(get_db)):
    """
    Generates a new randomized test session based on user and subject criteria.

    This endpoint orchestrates the creation of a test by selecting a specific
    number of questions. It performs rigorous validation of foreign keys and
    availability.

    Workflow:
    1. Validate existence of User and Subject.
    2. Check if the database contains enough questions to satisfy the request.
    3. If 'num_of_questions' exceeds availability, return a 400 Bad Request
       using a prefix/suffix match on the dynamic error message.
    4. On success, persist the test session and return the record.

    Args:
        test_data (TestGenerate): Schema to generate a new test session.
        num_of_questions (int): Desired number of questions for the session.
        db (Session): Injected database session.

    Returns:
        TestRead: The initialized test session with generated questions.

    Raises:
        HTTPException (400): If not enough questions are available.
        HTTPException (404): If the user or subject does not exist.
        HTTPException (500): If a database or unexpected error occurs.
    """
    test_manager = TestManager(db)

    success_test, result_test = test_manager.generate_test_session(test_data, num_of_questions)
    if not success_test:

        msg_parts = TestMessages.NO_ENOUGH_QUESTIONS.split("{available_questions}")
        prefix = msg_parts[0]
        suffix = msg_parts[1]
        if (isinstance(result_test, str) and
                result_test.startswith(prefix) and
                result_test.endswith(suffix)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_test
            )

        if result_test in [UserMessages.USER_NOT_FOUND,
                           KnowledgeMessages.SUBJECT_NOT_FOUND,
                           KnowledgeMessages.SUBJECT_NOT_FOUND,
                           QuestionMessages.QUESTION_NOT_FOUND]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result_test
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result_test
        )

    return result_test


@router.get("/{test_id}", response_model=TestRead)
async def get_test_by_id(test_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a specific test session and its associated data by ID.

    This endpoint fetches the full test record, including its current score,
    status (is_processed), and linked question metadata. It is typically
    used to resume a session or view results.

    Workflow:
    1. Query the TestManager for the test record.
    2. If success is False:
        a. Return 404 Not Found if the error matches TEST_NOT_FOUND.
        b. Return 500 Internal Server Error for database or technical failures.
    3. Return the test object if found.

    Args:
        test_id (int): The unique database identifier of the test.
        db (Session): Injected database session.

    Returns:
        TestRead: The complete test session record.

    Raises:
        HTTPException: 404 if the test ID does not exist.
        HTTPException: 500 if a technical error occurs during retrieval.
    """
    test_manager = TestManager(db)

    success_test, result_test = test_manager.get_test_by_id(test_id)
    if not success_test:
        if result_test == TestMessages.TEST_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result_test
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result_test
        )

    return result_test


@router.get("/question/{test_question_id}", response_model=TestQuestionRead)
async def get_test_question_by_id(test_question_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a specific test question record by its unique database ID.

    This endpoint is used to fetch the current state of a single question
    within a test session, including whether it has been answered (is_done)
    and the points achieved.

    Workflow:
    1. Query the TestManager for the specific test question.
    2. If success is False:
        a. Return 404 Not Found if the error matches TEST_QUESTION_NOT_FOUND.
        b. Return 500 Internal Server Error for database or technical failures.
    3. Return the test question object if found.

    Args:
        test_question_id (int): The unique ID of the test question entry.
        db (Session): Injected database session.

    Returns:
        TestQuestionRead: The test question record details.

    Raises:
        HTTPException: 404 if the test question ID does not exist.
        HTTPException: 500 if a technical error occurs during retrieval.
    """
    test_manager = TestManager(db)

    success_question, result_question = test_manager.get_test_question_by_id(test_question_id)

    if not success_question:
        if result_question == TestMessages.TEST_QUESTION_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result_question
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result_question
        )

    return result_question


router.get("/{test_id}/session", response_model=TestSessionRead)
async def run_test_session(test_id: int, db: Session = Depends(get_db)):
    """
    Provides all data required to start, resume, or continue a test session.

    This endpoint acts as the primary orchestrator for the testing UI. It
    retrieves the test metadata and determines the next pending question
    to be answered, allowing for a seamless resume-functionality.

    Workflow:
    1. Fetch the test by ID via TestManager.
    2. Check if the test is already marked as 'is_done' (returns 400).
    3. Identify the next unanswered question in the sequence.
    4. Return a composite object containing the test, the next question,
       and a progress flag.

    Args:
        test_id (int): The unique identifier of the test session.
        db (Session): Injected database session.

    Returns:
        TestSessionRead: A composite object holding the test and the next question.

    Raises:
        HTTPException (404): If the test or its questions cannot be found.
        HTTPException (400): If the test session is already completed.
        HTTPException (500): If a database error occurs.
    """
    test_manager = TestManager(db)

    success_session, result_session = test_manager.run_test_session(test_id)

    if not success_session:
        if result_session == TestMessages.TEST_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result_session
            )

        if result_session == TestMessages.TEST_ALREADY_DONE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result_session
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result_session
        )

    return result_session
