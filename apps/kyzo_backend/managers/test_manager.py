from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, Session

from apps.kyzo_backend.config import QuestionMessages, TestMessages
from apps.kyzo_backend.data import TestQuestion, Test, Question
from apps.kyzo_backend.managers.question_manager import QuestionManager
from apps.kyzo_backend.managers.knowledge_manager import KnowledgeManager
from apps.kyzo_backend.managers.user_manager import UserManager
from apps.kyzo_backend.schemas import TestGenerate, TestQuestionFinalize


class TestManager:
    """
    Business logic layer for orchestrating assessment sessions.

    This manager handles the full lifecycle of a test—from initialization
    and question selection to real-time answer evaluation and final
    scoring. It acts as the core engine for the adaptive learning
    experience, bridging the gap between raw question templates and
    individual student progress.
    """

    def __init__(self, db: Session):
        """
        Initializes the TestManager with a database session and internal sub-managers.

        This constructor implements Dependency Injection for the database session
        and initializes specialized sub-managers (Knowledge, Question, User)
        to handle cross-domain operations. This composition allows the TestManager
        to orchestrate complex workflows—like test generation—while maintaining
        strict separation of concerns and high testability.

        Args:
            db (Session): An active SQLAlchemy session used for all
                transactional operations across the manager and its components.
        """
        self._db = db
        self.knowledge_manager = KnowledgeManager(self._db)
        self.question_manager = QuestionManager(self._db)
        self.user_manager = UserManager(self._db)

    def finalize_test_question(
            self,
            test_id: int,
            test_question_id: int,
            test_question_data: TestQuestionFinalize
    ) -> dict[str, Any]:
        """
        Evaluates an individual test question and orchestrates the transition to the next state.

        Workflow:
        1. Retrieve records (TestQuestion + Question template).
        2. Guard: Ensure the question hasn't been answered yet.
        3. Validate: Check if the choice index is within range.
        4. Evaluation: Compare choice with the correct answer and assign points.
        5. Persistence: Record points, choice, and time; mark as done.
        6. Score Update: Increment the global test session's total score.
        7. Navigation: Commit and fetch the next unanswered question.

        Args:
            test_id (int): The unique identifier of the active test session.
            test_question_id (int): The ID of the specific question-test association.
            test_question_data (TestQuestionFinalize): Submission metrics (choice, timing).

        Returns:
            dict[str, Any]: {
                "next_question": TestQuestion | None,
                "all_done": bool
            }

        Raises:
            HTTPException (400): If already answered or choice is out of range.
            HTTPException (404/500): Inherited from helper methods or DB failure.
        """
        test_question = self.get_test_question_with_data_by_id(test_question_id)

        if test_question.is_done:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=TestMessages.TEST_QUESTION_ALREADY_DONE
            )

        question_template = test_question.question

        if test_question_data.student_choice >= len(question_template.options):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=TestMessages.ANSWER_OUT_OF_RANGE
            )

        is_correct = test_question_data.student_choice == question_template.answer
        earned_points = test_question.points_max if is_correct else 0

        test_question.is_correct = is_correct
        test_question.points_earned = earned_points
        test_question.student_choice = test_question_data.student_choice
        test_question.time_spent_milliseconds = test_question_data.time_spent_milliseconds
        test_question.is_done = True

        self._add_test_points(test_id, earned_points)

        try:
            self._db.commit()

            next_question = self._get_next_question(test_id)

            return {
                "next_question": next_question,
                "all_done": next_question is None
            }

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{TestMessages.TEST_QUESTION_FINALIZE_ERROR} {str(error)}"
            ) from error

    def finalize_test_session(self, test_id: int) -> Test:
        """
        Finalizes an assessment and triggers the post-test processing logic.

        This method transitions a test from 'done' to 'processed'. It ensures that
        the test has been officially submitted by the student and has not been
        evaluated yet.

        Args:
            test_id (int): The unique identifier of the test to be finalized.

        Returns:
            Test: The finalized Test object with updated 'is_processed' status.

        Raises:
            HTTPException (400): If the test is not finished or already processed.
            HTTPException (404): If the test_id is not found.
            HTTPException (500): If a database error occurs.
        """
        test = self.get_test_by_id(test_id)

        if not test.is_done:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=TestMessages.NOT_DONE
            )

        if test.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=TestMessages.TEST_ALREADY_PROCESSED
            )

        try:
            # TODO: AI Feedback Generation
            # Aufruf eines AI-Services, um die Performance zu analysieren

            test.is_processed = True

            self._db.commit()
            self._db.refresh(test)

            return test

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{TestMessages.TEST_FINALIZE_ERROR} {str(error)}"
            ) from error

    def generate_test_session(
            self,
            test_data: TestGenerate,
            num_of_questions: int
    ) -> Test:
        """
        Orchestrates the creation of a complete test session.

        This method follows a strict transactional workflow:
        1. Validates referenced entities (User, Subject, Topic).
        2. Verifies question availability in the pool.
        3. Initializes the Test header and flushes to obtain an ID.
        4. Selects random questions and links them to the session.
        5. Commits the transaction or rolls back on database failure.

        Args:
            test_data (TestGenerate): Data containing IDs for user, subject, and topic.
            num_of_questions (int): The required number of questions for the test.

        Returns:
            Test: The fully populated and persisted Test object.

        Raises:
            HTTPException:
                - 400 (Bad Request): If not enough questions are available.
                - 404 (Not Found): If foreign keys or specific questions aren't found.
                - 500 (Internal Server Error): On database-level failures.
        """
        self._check_foreignkey_exist(
            test_data.user_id,
            test_data.subject_id,
            test_data.topic_id
        )

        available_questions = self.question_manager.count_questions(
            test_data.subject_id,
            test_data.topic_id
        )

        if available_questions < num_of_questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=TestMessages.NO_ENOUGH_QUESTIONS.format(
                    available_questions=available_questions
                )
            )

        test_dict = test_data.model_dump()
        new_test = Test(**test_dict)

        try:
            self._db.add(new_test)
            self._db.flush()

            # (Internal rollback happens inside this method if it fails)
            test_questions = self._get_random_questions_for_test(
                new_test.id,
                test_data.subject_id,
                test_data.topic_id,
                num_of_questions
            )

            self._db.add_all(test_questions)
            self._db.commit()
            self._db.refresh(new_test)
            return new_test

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{TestMessages.CREATE_TEST_ERROR} {str(error)}"
            ) from error

    def get_test_by_id(self, test_id: int) -> Test:
        """
        Retrieves a complete test session by its unique identifier.

        This method utilizes eager loading (joinedload) to fetch the test header
        along with its associated question instances in a single database round-trip.

        Args:
            test_id (int): The unique database ID of the test session.

        Returns:
            Test: The Test object with its 'test_question' collection pre-loaded.

        Raises:
            HTTPException (404): If the test is not found.
            HTTPException (500): If a database error occurs during retrieval.
        """
        try:
            stmt = (
                select(Test)
                .options(joinedload(Test.test_question))
                .where(Test.id == test_id)
            )

            result_test = self._db.execute(stmt).unique().scalar_one_or_none()

            if not result_test:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=TestMessages.TEST_NOT_FOUND
                )

            return result_test

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{TestMessages.GET_TEST_ERROR} {str(error)}"
            ) from error

    def get_test_question_by_id(self, test_question_id: int) -> TestQuestion:
        """
        Retrieves a specific test-question instance by its unique ID.

        This method is used during the evaluation phase to fetch the association
        between a test session and a question. It provides the necessary context
        (maximum points, completion status, etc.) to process an answer.

        Args:
            test_question_id (int): The unique identifier of the TestQuestion record.

        Returns:
            TestQuestion: The requested TestQuestion instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If no record exists with the given ID.
                - 500 (Internal Server Error): If a database exception occurs.
        """
        try:
            stmt = (
                select(TestQuestion)
                .where(TestQuestion.id == test_question_id)
            )

            result_test_question = self._db.execute(stmt).scalar_one_or_none()

            if not result_test_question:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=TestMessages.TEST_QUESTION_NOT_FOUND
                )

            return result_test_question

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{TestMessages.GET_TEST_QUESTION_ERROR}: {str(error)}"
            ) from error

    def get_test_question_with_data_by_id(
            self,
            test_question_id: int
    ) -> TestQuestion:
        """
        Retrieves a test-question instance along with its underlying question template.

        This eager-loading approach (joinedload) is essential for the evaluation
        process, as it provides immediate access to the correct answer and
        validation logic stored in the 'Question' model without additional
        database round-trips.

        Args:
            test_question_id (int): The unique identifier of the TestQuestion record.

        Returns:
            TestQuestion: The instance with the 'question' relationship pre-filled.

        Raises:
            HTTPException (404): If the TestQuestion ID does not exist.
            HTTPException (500): If a database error occurs.
        """
        try:
            stmt = (
                select(TestQuestion)
                .options(joinedload(TestQuestion.question))
                .where(TestQuestion.id == test_question_id)
            )
            test_question = self._db.execute(stmt).scalar_one_or_none()

            if not test_question:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=TestMessages.TEST_QUESTION_NOT_FOUND
                )

            return test_question

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{TestMessages.GET_TEST_QUESTION_ERROR}: {str(error)}"
            ) from error

    def run_test_session(self, test_id: int) -> dict:
        """
        Provides all necessary data to start or resume a test session.

        This method retrieves the test metadata and determines the next pending
        question to be answered. It allows the frontend to immediately render
        the current state of the session.

        Args:
            test_id (int): The unique identifier of the test session to run.

        Returns:
            dict: A dictionary containing:
                - "test": The Test metadata object.
                - "next_question": The next pending TestQuestion instance,
                  or None if all questions are completed.
                - "all_done": A boolean flag indicating if the session has
                  no more pending questions.

        Raises:
            HTTPException:
                - 400 (Bad Request): If the test is already marked as finalized.
                - 404 (Not Found): If the test_id does not exist (via get_test_by_id).
        """
        test = self.get_test_by_id(test_id)

        if test.is_done:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=TestMessages.TEST_ALREADY_DONE
            )

        next_question = self._get_next_question(test_id)

        return {
            "test": test,
            "next_question": next_question,
            "all_done": not next_question
        }

    def _add_test_points(self, test_id: int, points: int) -> Test:
        """
        Updates the cumulative score of a test session.

        This helper method fetches the test header and increments the 'score'
        field by the given amount. It ensures that the score is initialized
        to zero if it was previously null.

        Args:
            test_id (int): The unique identifier of the test.
            points (int): The number of points to add.

        Returns:
            Test: The updated Test instance.
        """
        test = self.get_test_by_id(test_id)

        if test.score is None:
            test.score = 0
        test.score += points

        return test

    def _check_foreignkey_exist(
            self,
            user_id: int,
            subject_id: int,
            topic_id: Optional[int] = None
    ) -> bool:
        """
        Validates the existence of all required relational entities.

        This internal guard method verifies that the provided IDs correspond
        to existing records in the User, Subject, and (optionally) Topic tables.
        It ensures that the 'Test' session will not violate any foreign key
        constraints upon insertion.

        Args:
            user_id (int): The unique identifier of the student.
            subject_id (int): The identifier of the chosen subject.
            topic_id (Optional[int], optional): The identifier of a specific
                topic. If provided, the method also validates that the topic
                belongs to the specified subject. Defaults to None.

        Returns:
            tuple[bool, str | None]:
                - If successful: (True, None): If all entities exist and relationships are valid.
                - if error: (False, str): A specific error message identifying which
                  entity was not found.
        """
        self.user_manager.get_user_by_id(user_id)

        if topic_id is not None:
            self.knowledge_manager.get_topic_from_subject(
                subject_id,
                topic_id
            )
        else:
            self.knowledge_manager.get_subject_by_id(subject_id)

        return True

    def _get_next_question(self, test_id: int) -> TestQuestion | None:
        """
        Identifies a random unanswered question within a specific test session.

        By using a random order for the next pending question, the assessment
        feels more dynamic and prevents predictable patterns.

        Args:
            test_id (int): The unique identifier of the active test.

        Returns:
            TestQuestion | None: A random pending question instance, or None if all
                                 questions are completed.

        Raises:
            HTTPException (500): If a database error occurs during selection.
        """
        try:
            # pylint: disable=not-callable
            stmt = (
                select(TestQuestion)
                .where(TestQuestion.test_id == test_id)
                .where(TestQuestion.is_done == False)
                .order_by(func.random())
                .limit(1)
            )

            next_question = self._db.execute(stmt).scalar_one_or_none()

            return next_question

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{TestMessages.NEXT_QUESTION_ERROR} {str(error)}"
            ) from error

    def _get_random_questions_for_test(
            self,
            test_id: int,
            subject_id: int,
            topic_id: Optional[int] = None,
            num_of_questions: int = 10
    ) -> list[TestQuestion]:
        """
        Retrieves a random set of questions and maps them to TestQuestion instances.

        This method performs a randomized selection at the database level based on
        subject and optional topic filters. It then transforms the resulting
        Question entities into TestQuestion association models.

        Note:
            To maintain database integrity, this method performs a session rollback
            if no questions are found or if a database error occurs. This ensures
            that the previously persisted test session record is removed upon failure.

        Args:
            test_id (int): The unique identifier of the existing test session.
            subject_id (int): ID of the subject to filter questions.
            topic_id (Optional[int], optional): Specific topic ID to narrow the selection.
                Defaults to None.
            num_of_questions (int): The number of random questions to retrieve.
                Defaults to 10.

        Returns:
            list[TestQuestion]: A list of initialized TestQuestion association objects.

        Raises:
            HTTPException:
                - 404 (Not Found): If no questions match the specified criteria.
                - 500 (Internal Server Error): If a database operation fails
                  (SQLAlchemyError).
        """
        try:
            # pylint: disable=not-callable
            stmt = select(Question).where(Question.subject_id == subject_id)

            if topic_id is not None:
                stmt = stmt.where(Question.topic_id == topic_id)

            stmt = stmt.order_by(func.random()).limit(num_of_questions)

            result = self._db.execute(stmt)
            questions = result.scalars().all()

            if not questions:
                self._db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=QuestionMessages.QUESTION_NOT_FOUND
                )

            test_questions = [
                TestQuestion(
                    test_id=test_id,
                    question_id=question.id,
                    points_max=1,
                    is_done=False
                )
                for question in questions
            ]

            return test_questions

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR}: {str(error)}"
            ) from error
