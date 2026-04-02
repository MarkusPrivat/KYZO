from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import (KnowledgeMessages,
                                      QuestionMessages,
                                      TestMessages,
                                      UserMessages)
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.managers import TestManager
from apps.kyzo_backend.schemas import (TestRead, TestGenerate)


router = APIRouter(
    prefix="/api/test/",
    tags=["Test"]
)

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
