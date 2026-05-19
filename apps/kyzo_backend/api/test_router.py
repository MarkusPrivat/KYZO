"""
API router for test execution and lifecycle management.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.api.depends.role_depends import (
    require_student,
    require_student_or_admin,
    require_student_teacher_or_admin
)
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.data import User
from apps.kyzo_backend.managers import (
    KnowledgeManager,
    QuestionManager,
    TestManager,
    UserManager
)
from apps.kyzo_backend.schemas import (
    TestRead,
    TestGenerate,
    TestQuestionFinalize,
    TestQuestionRead,
    TestQuestionStepRead,
    TestSessionRead
)

router = APIRouter(
    prefix="/test",
    tags=["Test"]
)


def get_knowledge_manager(db: Session = Depends(get_db)) -> KnowledgeManager:
    """
    Dependency provider for the KnowledgeManager.
    """
    return KnowledgeManager(db)


def get_user_manager(db: Session = Depends(get_db)) -> UserManager:
    """
    Dependency provider for the UserManager.
    """
    return UserManager(db)


def get_question_manager(
    db: Session = Depends(get_db),
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
) -> QuestionManager:
    """
    Dependency provider for the QuestionManager, resolving nested manager dependencies.
    """
    return QuestionManager(
        db=db,
        knowledge_manager=knowledge_manager
    )


def get_test_manager(
    db: Session = Depends(get_db),
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
    question_manager: QuestionManager = Depends(get_question_manager),
    user_manager: UserManager = Depends(get_user_manager)
) -> TestManager:
    """
    FastAPI dependency provider that orchestrates and injects all required
    sub-managers into the TestManager instance.

    This provider resolves the entire top-level dependency graph for the test domain.
    By utilizing FastAPI's dependency caching mechanism, it guarantees that 'get_db'
    is evaluated exactly once per HTTP request. As a result, the TestManager and all
    of its injected sub-managers (Knowledge, Question, User) share the exact same
    SQLAlchemy Session instance, preserving strict database transaction boundaries
    (commit/rollback isolation).

    Args:
        db (Session): The core SQLAlchemy database session for the current request.
        knowledge_manager (KnowledgeManager): Injected manager for domain knowledge.
        question_manager (QuestionManager): Injected manager for educational questions
            (which internally shares the same knowledge_manager instance).
        user_manager (UserManager): Injected manager for user profile verification.

    Returns:
        TestManager: A fully composed TestManager instance, decoupled from internal
            instantiation logic and optimized for standalone unit testing.
    """
    return TestManager(
        db=db,
        knowledge_manager=knowledge_manager,
        question_manager=question_manager,
        user_manager=user_manager
    )


@router.post("/{test_id}/question/{test_question_id}/finalize", response_model=TestQuestionStepRead)
async def finalize_test_question(
        current_user: Annotated[User, Depends(require_student_or_admin)],
        test_id: int,
        test_question_id: int,
        test_question_data: TestQuestionFinalize,
        test_manager: TestManager = Depends(get_test_manager)
):
    """
    Evaluates a student's answer submission and determines the next step in the test session.

    This endpoint marks a specific question as completed, calculates the points
    earned based on the student's choice against the master template, updates the session's
    cumulative score, and automatically identifies the next pending question to be answered.

    Workflow:
    1. Retrieve records: Fetch the active test session and target test-question association.
    2. Guard (Access): Verify that the current user is either an administrator or the
       assigned owner of the test session (403).
    3. Guard (State): Prevent re-submission if the question is already marked as done (400).
    4. Validate: Check if the provided student choice index is within the valid options range (400).
    5. Evaluate & Persist: Score the answer, update metrics, and commit transaction.
    6. Transition: Fetch the next pending question or signal completion.

    Args:
        test_id (int): The unique database identifier of the active test session.
        test_question_id (int): The unique database identifier of the specific
            question instance to finalize.
        test_question_data (TestQuestionFinalize): Pydantic container containing
            the student's choice index and time spent metrics.
        current_user (User): The authenticated student or administrator executing
            the submission, injected by the global role dependency.
        test_manager (TestManager): Injected manager instance handling test session
            lifecycle, security boundaries, and evaluation logic.

    Returns:
        TestQuestionStepRead: A composite object containing the metadata for the
            'next_question' (if available) and the 'all_done' status flag.

    Raises:
        HTTPException:
            - 400 (Bad Request): If the question was already finalized or the
              submitted choice index is out of range for the template.
            - 401 (Unauthorized): If the authentication token is missing or invalid.
            - 403 (Forbidden): If the user lacks a valid role, OR if a student attempts
              to finalize a question in a test session that does not belong to them.
            - 404 (Not Found): If the test session or the test-question record is not found.
            - 500 (Internal Server Error): If a database transaction or commit failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: STUDENT or ADMIN roles (Session ownership enforced for students)
    """
    return test_manager.finalize_test_question(
        test_id,
        test_question_id,
        test_question_data,
        current_user
    )


@router.post("/{test_id}/finalize", response_model=TestRead)
async def finalize_test(
        current_user: Annotated[User, Depends(require_student_or_admin)],
        test_id: int,
        test_manager: Annotated[TestManager, Depends(get_test_manager)]
):
    """
    Finalizes an entire test session and marks it as completed.

    This endpoint transitions the state of a test session to 'is_done'. Once finalized,
    the session is locked and no further question answers can be submitted. It serves
    as the official conclusion of the user's engagement with the current test.

    Workflow:
    1. Retrieve record: Fetch the active test session by its unique ID.
    2. Guard (Access): Verify that the current user is either an administrator or the
       assigned owner of the test session (403).
    3. Guard (State): Ensure the test hasn't been finalized already (400).
    4. Guard (Completeness): Verify that all questions within the test have been answered (400).
    5. Update: Set the terminal 'is_done' flag to True and commit the transaction.

    Args:
        test_id (int): The unique database identifier of the test session to be finalized.
        current_user (User): The authenticated student or administrator executing
            the finalization, injected by the global role dependency.
        test_manager (TestManager): Injected manager instance handling test session
            lifecycle, security boundaries, and validation logic.

    Returns:
        TestRead: The finalized test database record showing its terminal status.

    Raises:
        HTTPException:
            - 400 (Bad Request): If the test session is already completed, or contains
              unanswered questions that prevent finalization.
            - 401 (Unauthorized): If the authentication token is missing or invalid.
            - 403 (Forbidden): If the user lacks a valid role, OR if a student attempts
              to finalize a test session that does not belong to them.
            - 404 (Not Found): If the requested test ID does not exist in the database.
            - 500 (Internal Server Error): If a technical error or database transaction
              failure occurs during finalization.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: STUDENT or ADMIN roles (Session ownership enforced for students)
    """
    return test_manager.finalize_test_session(test_id, current_user)


@router.post("/generate", response_model=TestRead, status_code=status.HTTP_201_CREATED)
async def generate_test(
        current_user: Annotated[User, Depends(require_student_or_admin)],
        test_data: TestGenerate,
        num_of_questions: int,
        test_manager: TestManager = Depends(get_test_manager)
):
    """
    Generates a new randomized test session based on user, subject, and topic criteria.

    This endpoint orchestrates the automatic generation of a quiz or exam session.
    It enforces data ownership boundaries, validates foreign key constraints, and
    randomly samples from the available question pool based on the requested pool criteria.

    Workflow:
    1. Guard (Access): Verify that the provided 'user_id' in the test_data matches
       the authenticated 'current_user.id' to prevent generation for other accounts (403).
    2. Validate: Verify the existence of the target User, Subject, and optional Topic (404).
    3. Inventory Check: Assess if the pool contains enough questions matching the filters.
    4. Guard (Availability): If 'num_of_questions' exceeds available matching templates,
       abort with a 400 Bad Request.
    5. Persistence: Create the Test header, link the randomly sampled questions, and
       commit the full generation transaction.

    Args:
        test_data (TestGenerate): Pydantic container containing the target user_id,
            subject_id, and optional topic_id filters.
        num_of_questions (int): The desired total number of questions for this session.
        current_user (User): The authenticated student or administrator executing
            the generation request, injected by the global role dependency.
        test_manager (TestManager): Injected manager instance handling test session
            generation, pooling boundaries, and transaction safety.

    Returns:
        TestRead: The newly initialized and persisted test session record with questions attached.

    Raises:
        HTTPException:
            - 400 (Bad Request): If not enough matching questions are available in the
              pool to satisfy the requested count.
            - 401 (Unauthorized): If the authentication token is missing or invalid.
            - 403 (Forbidden): If the user lacks a valid role, OR if a student attempts
              to generate a test session for a different user's ID.
            - 404 (Not Found): If the requested user, subject, or topic does not exist.
            - 500 (Internal Server Error): If a technical database error occurs during
              the random sampling or assembly transaction.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: STUDENT or ADMIN roles (Self-generation enforced for students)
    """
    return test_manager.generate_test_session(test_data, num_of_questions, current_user)


@router.get("/{test_id}", response_model=TestRead)
async def get_test_by_id(
        current_user: Annotated[User, Depends(require_student_teacher_or_admin)],
        test_id: int,
        test_manager: TestManager = Depends(get_test_manager)
):
    """
    Retrieves a specific test session and its preloaded question collection by ID.

    This endpoint fetches the comprehensive test record, including its cumulative score,
    completion states ('is_done', 'is_processed'), and linked question metadata. It serves
    as the primary data source for viewing completed exam summaries or loading ongoing states.

    Workflow:
    1. Query: Fetch the test session using eager loading for its associated questions.
    2. Guard (Access): Evaluate permissions via TestManager. Admins and Teachers bypass
       checks, while Students are validated against the session's 'user_id' (403).
    3. Return: Yield the complete composite test model instance.

    Args:
        test_id (int): The unique database identifier of the target test session.
        current_user (User): The authenticated user record executing the lookup,
            injected by the global role dependency.
        test_manager (TestManager): Injected manager instance handling test session
            retrieval, eager loading options, and security boundaries.

    Returns:
        TestRead: The complete test session record containing preloaded question associations.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the authentication token is missing or invalid.
            - 403 (Forbidden): If the user lacks a valid role, OR if a student attempts
              to inspect a test session that does not belong to their user ID.
            - 404 (Not Found): If no test session matches the provided test_id.
            - 500 (Internal Server Error): If a technical database exception or
              query failure occurs during retrieval.

    Security:
        - Bearer Auth (JWT)
        - Open to authenticated roles: STUDENT, TEACHER, ADMIN (Ownership enforced for students)
    """
    return test_manager.get_test_by_id(test_id, current_user)


@router.get("/question/{test_question_id}", response_model=TestQuestionRead)
async def get_test_question_by_id(
        current_user: Annotated[User, Depends(require_student_teacher_or_admin)],
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
        current_user (User): The authenticated user record, used strictly to
            verify that the requester holds a valid application role.
        test_question_id (int): The unique database identifier of the specific
            test question entry.
        test_manager (TestManager): Injected manager instance for test session
            lifecycle and evaluation logic.

    Returns:
        TestQuestionRead: The test question record details.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but does not match
              any recognized system roles.
            - 404 (Not Found): If the test question ID does not exist.
            - 500 (Internal Server Error): If a technical error occurs during retrieval.

    Security:
        - Bearer Auth (JWT)
        - Authorized roles: STUDENT, TEACHER, ADMIN
    """
    return test_manager.get_test_question_by_id(test_question_id, current_user)


@router.get("/{test_id}/session", response_model=TestSessionRead)
async def run_test_session(
        current_user: Annotated[User, Depends(require_student)],
        test_id: int,
        test_manager: TestManager = Depends(get_test_manager)
):
    """
    Provides all data required to start, resume, or continue an active test session.

    This endpoint acts as the primary orchestrator for the testing UI. It retrieves
    the test metadata, enforces data ownership, and dynamically determines the next
    pending question to be answered, allowing for a seamless resume functionality.

    Workflow:
    1. Retrieve record: Fetch the active test session by its unique ID.
    2. Guard (State): Ensure the test session has not already been completed ('is_done').
    3. Guard (Access): Verify that the authenticated student is the actual owner
       of this test session (403).
    4. Navigation: Query the next pending unanswered question belonging to the session.
    5. Return: Deliver a composite object containing the test metadata, the next
       question, and a completion flag.

    Args:
        test_id (int): The unique database identifier of the target test session.
        current_user (User): The authenticated student executing the test session,
            injected by the global role dependency.
        test_manager (TestManager): Injected manager instance handling test session
            lifecycle, security boundaries, and navigation.

    Returns:
        TestSessionRead: A composite object holding the core test metadata, the next
            question instance (if any), and the 'all_done' status flag.

    Raises:
        HTTPException:
            - 400 (Bad Request): If the test session is already flagged as completed.
            - 401 (Unauthorized): If the authentication token is missing or invalid.
            - 403 (Forbidden): If the user lacks the student role, OR if a student
              attempts to access a test session that does not belong to them.
            - 404 (Not Found): If no test session matches the provided test_id.
            - 500 (Internal Server Error): If a technical error or database exception
              occurs while assembling the session state.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: STUDENT role (Session ownership strictly enforced)
    """
    return test_manager.run_test_session(test_id, current_user)
