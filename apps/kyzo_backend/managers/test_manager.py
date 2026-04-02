from typing import Any, cast, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, Session

from apps.kyzo_backend.config import QuestionMessages, TestMessages
from apps.kyzo_backend.data import TestQuestion, Test, Question
from apps.kyzo_backend.managers import QuestionManager, KnowledgeManager, UserManager
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
    ) -> tuple[bool, dict[str, Any] | str]:
        """
        Evaluates an individual test question and orchestrates the transition to the next state.

        Workflow:
        1. Retrieve the TestQuestion record with its underlying Question template.
        2. Guard: Ensure the question has not been previously answered (is_done check).
        3. Validate: Check if the student's choice index exists within the available options.
        4. Evaluation: Compare the student's choice with the correct answer.
        5. Persistence: Record points earned, the specific choice, and the time spent.
        6. Score Update: Increment the global test session's total score.
        7. Navigation: Commit changes and fetch the next random unanswered question.
        8. Feedback: Return a status dictionary for seamless frontend transition.

        Args:
            test_id (int): The unique identifier of the active test session.
            test_question_id (int): The ID of the specific question-test association.
            test_question_data (TestQuestionFinalize): Submission metrics (choice, timing).

        Returns:
            tuple[bool, dict[str, Any] | str]:
                - (True, dict): {
                    "next_question": TestQuestion | None,
                    "all_done": bool
                  }
                - (False, str): Descriptive error message if any step fails.
        """
        success_question, result_question = self.get_test_question_with_question_data_by_id(
            test_question_id
        )
        if not success_question:
            return False, result_question
        if result_question.is_done:
            return False, TestMessages.TEST_QUESTION_ALREADY_DONE

        question_ref = cast(Question, cast(object, result_question.question))

        if test_question_data.student_choice > len(question_ref.options):
            return False, TestMessages.ANSWER_OUT_OF_RANGE

        is_correct = test_question_data.student_choice == question_ref.answer
        points = result_question.points_max if is_correct else 0

        result_question.is_correct = is_correct
        result_question.points_earned = points
        result_question.student_choice = test_question_data.student_choice
        result_question.time_spent_milliseconds = test_question_data.time_spent_milliseconds
        result_question.is_done = True

        success_points, result_points = self._add_test_points(test_id, points)
        if not success_points:
            return False, result_points

        try:
            self._db.commit()

            success_next, next_question = self._get_next_question(test_id)

            return True, {
                "next_question": next_question if success_next else None,
                "all_done": not success_next
            }

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{TestMessages.TEST_QUESTION_FINALIZE_ERROR}: {str(error)}"




    def finalize_test_session(self, test_id: int) -> tuple[bool, Test | str]:
        """
        Finalizes an assessment and triggers the post-test processing logic.

        This method transitions a test from 'done' to 'processed'. It ensures that
        the test has been officially submitted by the student and has not been
        evaluated yet. In the future, this will be the entry point for
        calculating final scores and generating qualitative AI feedback.

        Args:
            test_id (int): The unique identifier of the test to be finalized.

        Returns:
            tuple[bool, Test | str]:
                - If successful: (True, Test): The finalized Test object with
                                updated 'is_processed' status.
                - If not (False, str): An error message if the test is missing,
                                       incomplete, or already evaluated.
        """
        try:
            success, result_test = self.get_test_by_id(test_id)
            if not success:
                return False, result_test

            if not result_test.is_done:
                return False, TestMessages.NOT_DONE

            if result_test.is_processed:
                return False, TestMessages.TEST_ALREADY_PROCESSED

            # TODO: AI Feedback Generation
            # Aufruf eines AI-Services, um die Performance zu analysieren

            result_test.is_processed = True

            self._db.commit()
            self._db.refresh(result_test)

            return True, result_test

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{TestMessages.TEST_FINALIZE_ERROR} {str(error)}"


    def generate_test_session(
            self,
            test_data: TestGenerate,
            num_of_questions: int
    ) -> tuple[bool, Test | str]:
        """
        Orchestrates the creation of a complete test session.

        This method follows a strict transactional workflow:
        1. Validates that all referenced entities (User, Subject, Topic) exist.
        2. Verifies that the question pool contains enough items to satisfy 'num_of_questions'.
        3. Initializes the Test header and flushes it to obtain a valid ID.
        4. Selects a random subset of questions and links them to the session.
        5. Commits all changes atomically or performs a rollback on failure.

        Args:
            test_data (TestGenerate): Schema containing user, subject, and difficulty details.
            num_of_questions (int): The target number of questions for this session.

        Returns:
            tuple[bool, Test | str]:
                - If successful: (True, Test): The fully populated and persisted Test object.
                - If error (False, str): A descriptive error message if validation,
                  availability checks, or database operations fail.
        """
        success_foreignkey, error_foreignkey = self._check_foreignkey_exist(
            test_data.user_id,
            test_data.subject_id,
            test_data.topic_id
        )
        if not success_foreignkey:
            return False, error_foreignkey

        available_questions = self.question_manager.count_questions(
            test_data.subject_id,
            test_data.topic_id
        )
        if isinstance(available_questions, str):
            return False, available_questions
        if available_questions < num_of_questions:
            return False, TestMessages.NO_ENOUGH_QUESTIONS.format(
                available_questions,
                available_questions
            )

        test_dict = test_data.model_dump()
        new_test = Test(**test_dict)

        try:
            self._db.add(new_test)
            self._db.flush()

            success_test_questions, result_test_questions = self._get_random_questions_for_test(
                new_test.id,
                test_data.subject_id,
                test_data.topic_id,
                num_of_questions
            )
            if not success_test_questions:
                self._db.rollback()
                return False, result_test_questions

            self._db.add_all(result_test_questions)
            self._db.commit()
            self._db.refresh(new_test)
            return True, new_test

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{TestMessages.CREATE_TEST_ERROR} {str(error)}"


    def get_test_by_id(self, test_id: int) -> tuple[bool, Test | str]:
        """
        Retrieves a complete test session by its unique identifier.

        This method utilizes eager loading (joinedload) to fetch the test header
        along with its associated question instances in a single database round-trip.
        This is critical for performance when rendering test summaries or active
        exam screens.

        Args:
            test_id (int): The unique database ID of the test session.

        Returns:
            tuple[bool, Test | str]:
                - If found: (True, Test): The Test object with its
                            'test_question' collection pre-loaded.
                - If not found/error: (False, str): An error message if
                                      the test is not found or a database
                                      exception occurs.
        """
        try:
            stmt = (
                select(Test)
                .options(joinedload(Test.test_question))
                .where(Test.id == test_id)
            )

            result_test = self._db.execute(stmt).unique().scalar_one_or_none()

            if not result_test:
                return False, TestMessages.TEST_NOT_FOUND

            return True, result_test

        except SQLAlchemyError as error:
            return False, f"{TestMessages.GET_TEST_ERROR} {str(error)}"


    def get_test_question_by_id(self, test_question_id: int) -> tuple[bool, TestQuestion | str]:
        """
        Retrieves a specific test-question instance by its unique ID.

        This method is primarily used during the evaluation phase to fetch the
        association between a test session and a question template. It provides
        the necessary context (points, status, etc.) to process a student's answer.

        Args:
            test_question_id (int): The unique identifier of the TestQuestion record.

        Returns:
            tuple[bool, TestQuestion | str]:
                - If found: (True, TestQuestion): The requested instance.
                - If not found/error: (False, str): Error message if the record is
                                    missing or a DB exception occurs.
        """
        try:
            stmt = (
                select(TestQuestion)
                .where(TestQuestion.id == test_question_id)
            )

            result_test_question = self._db.execute(stmt).scalar_one_or_none()

            if not result_test_question:
                return False, TestMessages.TEST_QUESTION_NOT_FOUND

            return True, result_test_question

        except SQLAlchemyError as error:
            return False, f"{TestMessages.GET_TEST_QUESTION_ERROR}: {str(error)}"


    def get_test_question_with_question_data_by_id(
            self,
            test_question_id: int
    ) -> tuple[bool, TestQuestion | str]:
        """
        Retrieves a test-question instance along with its underlying question template.

        This eager-loading approach (joinedload) is essential for the evaluation
        process, as it provides immediate access to the correct answer and
        validation logic stored in the 'Question' model without additional
        database round-trips.

        Args:
            test_question_id (int): The unique identifier of the TestQuestion record.

        Returns:
            tuple[bool, TestQuestion | str]:
                - If found: (True, TestQuestion): The instance with the 'question'
                            relationship pre-filled.
                - If not found/error: (False, str): If the record is missing,
                                      or a DB error occurs.
        """
        try:
            stmt = (
                select(TestQuestion)
                .options(joinedload(TestQuestion.question))
                .where(TestQuestion.id == test_question_id)
            )
            test_question = self._db.execute(stmt).scalar_one_or_none()

            if not test_question:
                return False, TestMessages.TEST_QUESTION_NOT_FOUND

            return True, test_question

        except SQLAlchemyError as error:
            return False, f"{TestMessages.GET_TEST_QUESTION_ERROR}: {str(error)}"


    def run_test_session(self, test_id: int) -> tuple[bool, dict | str]:
        """
        Provides all necessary data to start or resume a test session.

        This method combines the test metadata with the next pending question
        to allow the frontend to render the correct state immediately.

        Returns:
            tuple[bool, dict | str]:
                - (True, dict): A dictionary containing the 'test' object
                  and the 'next_question' object.
                - (False, str): If the test is already finalized or not found.
        """
        success_test, result_test = self.get_test_by_id(test_id)
        if not success_test:
            return False, result_test

        if result_test.is_done:
            return False, TestMessages.TEST_ALREADY_DONE

        success_question, next_question = self._get_next_question(test_id)

        return True, {
            "test": result_test,
            "next_question": next_question if success_question else None,
            "all_done": not success_question
        }


    def _add_test_points(self, test_id: int, points: int) -> tuple[bool, Test | str]:
        """
        Updates the cumulative score of a test session.

        This helper method fetches the test header and increments the 'score'
        field by the given amount. It ensures that the score is initialized
        to zero if it was previously null.

        Args:
            test_id (int): The unique identifier of the test.
            points (int): The number of points to add (can be 0).

        Returns:
            tuple[bool, Test | str]: (True, Test) if updated, (False, error) otherwise.
        """
        success_test, result_test = self.get_test_by_id(test_id)
        if not success_test:
            return False, result_test

        if result_test.score is None:
            result_test.score = 0
        result_test.score += points

        return True, result_test


    def _check_foreignkey_exist(
            self,
            user_id: int,
            subject_id: int,
            topic_id: Optional[int] = None
    ) -> tuple[bool, str | None]:
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
        success_user, result_user = self.user_manager.get_user_by_id(user_id)
        if not success_user:
            return False, result_user

        if topic_id is not None:
            success_topic, result_topic = self.knowledge_manager.get_topic_from_subject(
                subject_id,
                topic_id
            )
            if not success_topic:
                return False, result_topic

        else:
            success_subject, result_subject = self.knowledge_manager.get_subject_by_id(subject_id)
            if not success_subject:
                return False, result_subject

        return True, None


    def _get_next_question(self, test_id: int) -> tuple[bool, TestQuestion | str]:
        """
        Identifies a random unanswered question within a specific test session.

        By using a random order for the next pending question, the assessment
        feels more dynamic and prevents predictable patterns during retakes
        or resumed sessions.

        Args:
            test_id (int): The unique identifier of the active test.

        Returns:
            tuple[bool, TestQuestion | str]:
                - (True, TestQuestion): A random pending question instance.
                - (False, str): Message if all questions are completed
                  or the test was not found.
        """
        try:
            # pylint: disable=not-callable
            stmt = (
                select(TestQuestion)
                .where(TestQuestion.test_id == test_id)
                .where(TestQuestion.is_done is False)
                .order_by(func.random())
                .limit(1)
            )

            next_question = self._db.execute(stmt).scalar_one_or_none()

            if not next_question:
                return False, TestMessages.NO_MORE_QUESTIONS

            return True, next_question

        except SQLAlchemyError as error:
            return False, f"{TestMessages.NEXT_QUESTION_ERROR} {str(error)}"


    def _get_random_questions_for_test(
            self,
            test_id: int,
            subject_id: int,
            topic_id: Optional[int] = None,
            num_of_questions: int = 10
    ) -> tuple[bool, list[TestQuestion] | str]:
        """
        Selects a random set of questions and prepares them as TestQuestion instances.

        This method performs an efficient random selection at the database level,
        limits the result set to the requested test size, and maps the results
        to the TestQuestion association model.

        Args:
            test_id (int): The ID of the newly created test session.
            subject_id (int): The subject to pull questions from.
            topic_id (Optional[int], optional): Specific topic filter. Defaults to None.
            num_of_questions (int): Number of questions to retrieve. Defaults to 10.

        Returns:
            tuple[bool, list[TestQuestion] | str]:
                - If successful: (True, list[TestQuestion]): A list of initialized
                                 question instances.
                -  if error: (False, str): Error message if no questions exist or
                             a DB error occurs.
        """
        try:
            # pylint: disable=not-callable
            stmt = (
                select(Question)
                .where(Question.subject_id == subject_id)
                .order_by(func.random())
                .limit(num_of_questions)
            )

            if topic_id is not None:
                stmt = stmt.where(Question.topic_id == topic_id)

            questions = self._db.execute(stmt).scalars().all()

            if not questions:
                return False, QuestionMessages.QUESTION_NOT_FOUND

            test_questions = [
                TestQuestion(
                    test_id=test_id,
                    question_id=question.id,
                    points_max=1,
                    is_done=False
                )
                for question in questions
            ]

            return True, test_questions

        except SQLAlchemyError as error:
            return False, f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR}: {str(error)}"
