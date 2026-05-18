from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, Session

from apps.kyzo_backend.config import QuestionMessages, TestMessages, UserRole
from apps.kyzo_backend.data import TestQuestion, Test, User, Question
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
            test_question_data: TestQuestionFinalize,
            user: User
    ) -> dict[str, Any]:
        """
        Evaluates an individual test question and orchestrates the transition to the
        next state.

        Workflow:
        1. Retrieve records (Test session + TestQuestion with template).
        2. Guard: Validate if the user is authorized to access this test session.
        3. Guard: Ensure the question hasn't been answered yet.
        4. Validate: Check if the choice index is within the question's options range.
        5. Evaluation: Compare the choice with the correct answer and assign points.
        6. Persistence: Record points, choice, and timing metrics; mark as done.
        7. Score Update: Increment the global test session's total score.
        8. Navigation: Commit changes and fetch the next unanswered question.

        Args:
            test_id (int): The unique identifier of the active test session.
            test_question_id (int): The ID of the specific question-test association.
            test_question_data (TestQuestionFinalize): Submission metrics (choice, timing).
            user (User): The authenticated user entity executing the submission.

        Returns:
            dict[str, Any]: A dictionary indicating the next state:
                - "next_question" (TestQuestion | None):
                    The next unanswered question, if available.
                - "all_done" (bool):
                    True if no more questions remain in the session.

        Raises:
            HTTPException:
                - 400 (Bad Request): If the question is already finalized or the answer
                  choice is out of range.
                - 403 (Forbidden): If the user is neither an administrator nor the owner
                  of the session.
                - 404 (Not Found): If the test session or question does not exist.
                - 500 (Internal Server Error): If a database transaction or commit failure occurs.
        """
        test_session = self.get_test_by_id(test_id, user)

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

        self._add_points_to_test_session(test_session, earned_points)

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

    def finalize_test_session(self, test_id: int, user: User) -> Test:
        """
        Finalizes an assessment session and triggers post-test processing logic.

        This method transitions a test session from its active/completed state ('is_done')
        to its terminal archival state ('is_processed'). It serves as the domain-level
        entry point for official test submissions, locking the session against future
        mutations and preparing it for evaluation or feedback generation.

        Workflow:
        1. Retrieve record: Fetch the target test session by its unique ID.
        2. Guard (Access): Verify that the executing user has authorization to access
           and modify this specific test session.
        3. Guard (State): Ensure the student has actually finished answering all
           questions ('is_done' is True).
        4. Guard (Idempotency): Prevent re-processing if the session has already
           been finalized ('is_processed' is True).
        5. Process: Mark the session as processed, commit the transaction, and refresh.

        Args:
            test_id (int): The unique database identifier of the test session to finalize.
            user (User): The authenticated user entity initiating the finalization request.

        Returns:
            Test: The finalized and refreshed SQLAlchemy Test model instance with
                'is_processed' set to True.

        Raises:
            HTTPException:
                - 400 (Bad Request): If the test session is not yet completed by the user,
                  or if it has already been processed in a previous request.
                - 403 (Forbidden): If the user is neither an administrator nor the
                  verified owner of the test session.
                - 404 (Not Found): If no test session matches the provided test_id
                  (propagated from get_test_by_id).
                - 500 (Internal Server Error): If a technical database transaction failure
                  occurs during the commit.
        """
        test_session = self.get_test_by_id(test_id, user)

        if not test_session.is_done:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=TestMessages.NOT_DONE
            )

        if test_session.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=TestMessages.TEST_ALREADY_PROCESSED
            )

        try:
            # TODO: AI Feedback Generation
            # Aufruf eines AI-Services, um die Performance zu analysieren

            test_session.is_processed = True

            self._db.commit()
            self._db.refresh(test_session)

            return test_session

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{TestMessages.TEST_FINALIZE_ERROR} {str(error)}"
            ) from error

    def generate_test_session(
            self,
            test_data: TestGenerate,
            num_of_questions: int,
            user: User
    ) -> Test:
        """
        Orchestrates the creation of a complete randomized test session.

        This method follows a strict transactional workflow:
        1. Validates referenced database entities (User, Subject, Topic) via foreign keys.
        2. Guard (Access): Verifies resource ownership unless the requesting user is an Admin.
        3. Inventory Check: Checks the total pool volume of available questions matching filters.
        4. Guard (Availability): Aborts if requested question count exceeds available pool size.
        5. Assembly: Initializes the Test header, flushes to obtain a technical ID, links
           randomized question samples, and commits the full transaction.

        Args:
            test_data (TestGenerate): Pydantic data container containing target filters
                such as user_id, subject_id, and optional topic_id.
            num_of_questions (int): The required number of questions to slice into this session.
            user (User): The authenticated user entity initiating the generation request.

        Returns:
            Test: The fully populated and refreshed SQLAlchemy Test session model instance.

        Raises:
            HTTPException:
                - 400 (Bad Request): If the question pool does not hold enough unique questions
                  to satisfy the requested `num_of_questions`.
                - 403 (Forbidden): If a non-admin user attempts to create a test session
                  bound to another user's ID (via _validate_user_ownership).
                - 404 (Not Found): If referenced foreign keys (user, subject, topic) do not exist.
                - 500 (Internal Server Error): If a database transaction, insert, or sampling
                  failure occurs.
        """
        self._check_foreignkey_exist(
            test_data.user_id,
            test_data.subject_id,
            test_data.topic_id
        )

        if user != UserRole.ADMIN:
            self._validate_user_ownership(test_data, user)

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

    def get_test_by_id(
            self,
            test_id: int,
            user: User
    ) -> Test:
        """
        Retrieves a complete test session by its unique identifier after validating access.

        This method utilizes eager loading (joinedload) to fetch the core test header
        along with its associated question instances in a single database round-trip.
        Before returning the resource, it runs an ownership validation check against
        the requesting user.

        Args:
            test_id (int): The unique database identifier of the target test session.
            user (User): The authenticated user entity requesting the test session data.

        Returns:
            Test: The populated SQLAlchemy Test model instance with its 'test_question'
                collection fully preloaded.

        Raises:
            HTTPException:
                - 403 (Forbidden): If the user is neither an administrator nor the
                  assigned owner of the test session.
                - 404 (Not Found): If no test session matches the provided test_id.
                - 500 (Internal Server Error): If a technical database exception or
                  query failure occurs during retrieval.
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

            self._validate_test_session_access(result_test, user)
            return result_test

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{TestMessages.GET_TEST_ERROR} {str(error)}"
            ) from error

    def get_test_question_by_id(
            self,
            test_question_id: int,
            user: User
    ) -> TestQuestion:
        """
        Retrieves a specific test-question instance by its unique ID after verifying access rights.

        This method fetches the association record between a test session and a question template.
        It provides critical context (such as maximum points, student choices, and completion
        status) and applies strict role-based data ownership boundaries before returning the
        resource.

        Args:
            test_question_id (int): The unique database identifier of the TestQuestion record.
            user (User): The authenticated user entity requesting the record.

        Returns:
            TestQuestion: The requested SQLAlchemy TestQuestion instance.

        Raises:
            HTTPException:
                - 403 (Forbidden): If a student attempts to retrieve a test question
                  linked to a test session that does not belong to them.
                - 404 (Not Found): If no TestQuestion record matches the provided ID.
                - 500 (Internal Server Error): If a technical database or query execution
                  failure occurs.
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

            self._validate_test_question_access(result_test_question, user)

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

    def run_test_session(
            self,
            test_id: int,
            user: User
    ) -> dict:
        """
        Provides all necessary data to start or resume an active test session.

        This method retrieves the test session's metadata and dynamically calculates
        the next pending question to be answered. It serves as the primary data provider
        for the frontend to instantly render the correct state of an ongoing quiz or exam.

        Workflow:
        1. Retrieve record: Fetch the target test session by its unique ID.
        2. Guard (State): Ensure the test session hasn't already been completed ('is_done').
        3. Guard (Access): Verify that the executing user is authorized to access this session.
        4. Navigation: Query the next pending unanswered question belonging to the session.

        Args:
            test_id (int): The unique database identifier of the test session to execute.
            user (User): The authenticated user entity requesting the test execution.

        Returns:
            dict: A state dictionary containing the following keys:
                - "test" (Test): The core SQLAlchemy Test metadata object.
                - "next_question" (TestQuestion | None): The next pending question instance,
                  or None if no unanswered questions remain.
                - "all_done" (bool): A boolean flag indicating whether the session has
                  reached the end of its question pool.

        Raises:
            HTTPException:
                - 400 (Bad Request): If the test session is already flagged as completed.
                - 403 (Forbidden): If the user is neither an administrator nor the
                  assigned owner of the test session.
                - 404 (Not Found): If no test session matches the provided test_id.
                - 500 (Internal Server Error): If a database exception occurs while fetching
                  the session state or navigation steps.
        """
        test = self.get_test_by_id(test_id, user)

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

    @staticmethod
    def _add_points_to_test_session(test_session: Test, points: int) -> None:
        """
        Updates the cumulative score of a test session.

        This helper method manipulates the test tracking object and increments the
        'score' field by the given amount. It ensures that the score is safely
        initialized to zero if it was previously unassigned (Null).

        Args:
            test_session (Test): The concrete SQLAlchemy Test model instance to update.
            points (int): The number of points to add to the current score.
        """
        if test_session.score is None:
            test_session.score = 0
        test_session.score += points

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

    @staticmethod
    def _validate_test_session_access(test_session: Test, user: User) -> None:
        """
        Enforces access control boundaries for a test session resource.

        This internal guard verifies whether the executing user possesses the necessary
        clearance to read or write to the target test session.

        Access Rules:
        - ADMIN & TEACHER: Full access to inspect any test session.
        - Owners: Users can access test sessions that belong specifically to their own user ID.

        Args:
            test_session (Test): The test session entity to be evaluated.
            user (User): The authenticated user requesting access.

        Raises:
            HTTPException:
                - 403 (Forbidden): If the user is neither an administrator nor the
                  assigned owner of the test session.
        """
        if user.role in [UserRole.TEACHER, UserRole.ADMIN]:
            return

        if test_session.user_id == user.id:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this test session.",
        )

    def _validate_test_question_access(self, test_question: TestQuestion, user: User) -> None:
        """
        Enforces access control boundaries for an individual test question resource.

        This internal guard verifies whether the executing user possesses the necessary
        clearance to read or interact with a specific question-session link.

        Access Rules:
        - ADMIN & TEACHER: Full access to inspect any test question.
        - STUDENT: Can only access the question if they are the verified owner
          of the parent test session.

        Args:
            test_question (TestQuestion): The specific test-question link entity to evaluate.
            user (User): The authenticated user requesting access.

        Raises:
            HTTPException:
                - 403 (Forbidden): If a student attempts to access a test question
                  belonging to a test session owned by a different user.
        """
        if user.role in [UserRole.TEACHER, UserRole.ADMIN]:
            return

        test_session = self.get_test_by_id(test_question.test_id, user)

        if test_session.user_id == user.id:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this test question.",
        )

    @staticmethod
    def _validate_user_ownership(test_data: TestGenerate, user: User) -> None:
        """
        Enforces resource ownership during the test generation process.

        This internal guard verifies that the incoming request parameters align
        with the identity of the authenticated user. It prevents unauthorized
        users from generating test sessions on behalf of other accounts.

        Args:
            test_data (TestGenerate): Pydantic data container containing the
                parameters for the new test, including the target 'user_id'.
            user (User): The authenticated user entity executing the generation request.

        Raises:
            HTTPException:
                - 403 (Forbidden): If the 'user_id' provided in the request body
                  does not match the 'id' of the authenticated requester.
        """
        if test_data.user_id == user.id:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create test sessions for other users.",
        )

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
