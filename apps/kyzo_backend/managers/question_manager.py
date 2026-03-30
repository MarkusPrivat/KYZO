import json
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import QuestionMessages, OpenAIMessages
from apps.kyzo_backend.data import Question, QuestionInput, QuestionOrigin, Topic
from apps.kyzo_backend.managers import KnowledgeManager
from apps.kyzo_backend.schemas import (QuestionCreate,
                                       QuestionStatus,
                                       QuestionUpdate,
                                       QuestionInputCreate,
                                       QuestionInputUpdate,
                                       QuestionInputExtractedQuestionsUpdate)
from apps.kyzo_backend.services import QuestionGenerator


class QuestionManager:
    """
    Business logic layer for managing educational content.

    This manager orchestrates operations related to subjects, topics,
    and learning materials, acting as a bridge between the database
    models and the API layer.
    """

    def __init__(self, db: Session):
        """
        Initializes the QuestionManager with a database session and AI services.

        This implementation utilizes Dependency Injection for the database session,
        decoupling business logic from connection management. This is critical for:
        1. **Testability**: Facilitates the use of mock sessions or in-memory databases (SQLite).
        2. **Consistency**: Ensures the manager operates within the same transaction
           context as other managers (e.g., KnowledgeManager).

        The manager also encapsulates the 'QuestionGenerator' to handle AI-driven
        content extraction tasks.

        Args:
            db (Session): An active SQLAlchemy session used for all persistence operations.
        """
        self._db = db
        self.question_generator = QuestionGenerator()


    def add_question(self, question_data: QuestionCreate) -> tuple[bool, Question | str]:
        """
        Creates and persists a new question in the database.

        This method serves as the primary entry point for adding educational
        content. It performs a hierarchical integrity check to ensure the
        specified subject and topic exist and are correctly linked.
        Nested structures (options and explanations) are automatically
        serialized into JSON format via Pydantic's model_dump.

        Args:
            question_data (QuestionCreate): Validated data transfer object
                                            containing all necessary question
                                            attributes and logical constraints.

        Returns:
            tuple[bool, Question | str]:
                - If successful: (True, Question object)
                - If failed: (False, Error message string)

        Raises:
            SQLAlchemyError: If the database transaction fails (handled internally
                            via rollback).
        """
        try:
            success, result = self._exist_subject_and_topic(
                question_data.subject_id,
                question_data.topic_id
            )

            if not success:
                return False, result

            question_dict = question_data.model_dump()
            new_question = Question(**question_dict)

            self._db.add(new_question)
            self._db.commit()
            self._db.refresh(new_question)
            return True, new_question

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{QuestionMessages.CREATE_QUESTION_ERROR} {str(error)}"

    def add_question_input(
            self,
            question_count: int,
            question_input_data: QuestionInputCreate) -> tuple[bool, str]:
        """
        Orchestrates the initial ingestion and AI-processing of raw content.

        This method performs a three-step workflow:
        1. **Validation**: Verifies that the subject and topic exist and are correctly linked.
        2. **Generation**: Invokes the `QuestionGenerator` (LLM) to extract a specified
           number of question drafts from the raw input.
        3. **Persistence**: Stores the raw material and the resulting AI drafts in a
           `QuestionInput` record for future user review.

        Args:
            question_count (int): The target number of questions the AI should generate.
            question_input_data (QuestionInputCreate): A validated DTO containing
                                                       source text and metadata.

        Returns:
            tuple[bool, str]:
                - If successful: (True, Success message confirming processed count)
                - If failed: (False, Detailed error message from validation or AI service)

        Note:
            This method does NOT create permanent 'Question' records. It populates
            the 'extracted_questions' buffer, which requires a subsequent call
            to `create_questions_from_question_input` for promotion to the global pool.
        """
        try:
            success, result = self._exist_subject_and_topic(
                question_input_data.subject_id,
                question_input_data.topic_id
            )
            if not success:
                return False, result

            success, result_extracted_questions = (
                self.question_generator.generate_extracted_questions_from_raw_input(
                    raw_input=question_input_data.raw_input,
                    question_count=question_count
                )
            )
            if not success:
                return False, f"{OpenAIMessages.GENERATION_FAILED} {result_extracted_questions}"

            question_input_dict = question_input_data.model_dump()

            if isinstance(result_extracted_questions, QuestionInputExtractedQuestionsUpdate):
                question_input_dict["extracted_questions"] = [
                    question.model_dump() for question
                    in result_extracted_questions.extracted_questions
                ]

            new_question_input = QuestionInput(**question_input_dict)

            self._db.add(new_question_input)
            self._db.commit()
            self._db.refresh(new_question_input)
            return True, QuestionMessages.QUESTION_INPUT_PROCESSED.format(
                question_count=question_count
            )

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{QuestionMessages.CREATE_QUESTION_INPUT_ERROR} {str(error)}"

    def count_questions(self, subject_id: int, topic_id: Optional[int] = None) -> int | str:
        """
        Retrieves the total count of questions filtered by subject and optionally by topic.

        This method performs a high-performance database count. It is designed to
        validate question availability before initializing a test session.
        If a topic_id is provided, the search is narrowed down to that specific topic;
        otherwise, it aggregates all questions within the subject.

        Args:
            subject_id (int): The unique identifier of the subject.
            topic_id (Optional[int], optional): The unique identifier of the topic.
                Defaults to None (subject-wide count).

        Returns:
            int | str: The number of questions found (int) if successful,
                or an error message (str) if a database exception occurs.
        """
        try:
            # pylint: disable=not-callable
            stmt = (select(func.count())
                    .select_from(Question)
                    .where(Question.subject_id == subject_id))

            if topic_id is not None:
                stmt = stmt.where(Question.topic_id == topic_id)

            count = self._db.execute(stmt).scalar() or 0

            return count

        except SQLAlchemyError as error:
            return f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR}: {str(error)}"

    def create_questions_from_question_input(
            self,
            question_input_id: int) -> tuple[bool, str]:
        """
        Promotes AI-generated drafts to the global question pool.

        This method executes the 'promotion' phase of the content pipeline. It
        converts validated draft items into permanent 'Question' records and
        establishes a link to their source for audit purposes.

        Workflow & Integrity:
        1. **Idempotency Check**: Verifies the 'is_processed' flag to prevent
           duplicate question creation from the same input job.
        2. **Batch Promotion**: Iterates through the 'extracted_questions' JSON buffer,
           mapping each draft to a new 'Question' model.
        3. **Traceability (Lineage)**: For every created question, a 'QuestionOrigin'
           record is generated, linking the new item to its source material.
        4. **State Finalization**: Marks the input record as 'processed' within
           the same database transaction.

        Args:
            question_input_id (int): The ID of the QuestionInput record containing the drafts.

        Returns:
            tuple[bool, str]:
                - If successful: (True, Success message with the count of promoted questions)
                - If failed: (False, Error message explaining the rejection)

        Note:
            Uses `self._db.flush()` within the loop to ensure IDs are available for
            the 'QuestionOrigin' linkage before the final `commit()`.
        """
        try:
            success, result_question_input = self.get_question_input_by_id(question_input_id)

            if not success or not result_question_input:
                return False, result_question_input or QuestionMessages.QUESTION_INPUT_NOT_FOUND

            if result_question_input.is_processed:
                return False, QuestionMessages.QUESTION_INPUT_ALREADY_PROCESSED

            if not result_question_input.extracted_questions:
                return False, QuestionMessages.NO_QUESTION_TO_PROCESS

            extracted_question_dict = self._get_questions_from_json(
                result_question_input.extracted_questions
            )
            new_questions_count = 0

            for question in extracted_question_dict:
                new_question = Question(
                    subject_id=result_question_input.subject_id,
                    topic_id=result_question_input.topic_id,
                    grade=result_question_input.grade,
                    question_text=question.get('question_text'),
                    options=question.get('options'),
                    answer=question.get('answer'),
                    explanations=question.get('explanations'),
                    difficulty=question.get('difficulty', 5),
                    is_llm_variant=True,
                    is_active=True
                )

                self._db.add(new_question)
                self._db.flush()

                origin_link = QuestionOrigin(
                    question_id=new_question.id,
                    question_input_id=result_question_input.id
                )
                self._db.add(origin_link)
                new_questions_count += 1

            result_question_input.is_processed = True

            self._db.commit()
            return True, QuestionMessages.QUESTION_INPUT_TO_QUESTION.format(
                new_questions_count=new_questions_count
            )

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{QuestionMessages.CREATE_QUESTION_ERROR}: {str(error)}"

    def get_all_questions(self) -> tuple[bool, list[Question] | str]:
        """
        Retrieves all questions from the database without any filters.

        This method provides a global overview of the entire question pool.
        It is primarily intended for administrative dashboards, content audits,
        or cross-subject analytics.

        Returns:
            tuple[bool, list[Question] | str]:
                - If successful: (True, List of all Question SQLAlchemy objects)
                - If no questions exist: (False, "No questions found" message)
                - If failed: (False, Detailed SQLAlchemy error message)

        Note:
            **Performance Warning**: This operation performs a full table scan.
            For production environments with large datasets, use paginated
            or scoped retrieval methods to avoid memory exhaustion.
        """
        try:
            stmt = select(Question)
            all_questions = self._db.execute(stmt).scalars().all()

            if not all_questions:
                return False, QuestionMessages.QUESTION_NOT_FOUND

            return True, list(all_questions)
        except SQLAlchemyError as error:
            return False, f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR} {str(error)}"

    def get_questions_for_subject_topic(
            self,
            subject_id: int,
            topic_id: Optional[int] = None
    ) -> tuple[bool, list[Question] | str]:
        """
        Retrieves all questions for a subject, optionally filtered by a specific topic.

        This unified method acts as the central retrieval point for question content.
        It supports both broad subject-wide assessments and granular, topic-specific
        drills by dynamically adjusting the query filter based on the provided arguments.

        Args:
            subject_id (int): The unique database identifier of the subject.
            topic_id (Optional[int], optional): The unique identifier of the topic.
                If None, retrieves all questions for the subject. Defaults to None.

        Returns:
            tuple[bool, list[Question] | str]:
                - (True, list[Question]): If questions were found.
                - (False, str): If no questions exist or a database error occurred.
        """
        try:
            stmt = select(Question).where(Question.subject_id == subject_id)

            if topic_id is not None:
                stmt = stmt.where(Question.topic_id == topic_id)

            all_questions = self._db.execute(stmt).scalars().all()

            if not all_questions:
                return False, QuestionMessages.QUESTION_NOT_FOUND

            return True, list(all_questions)

        except SQLAlchemyError as error:
            return False, f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR}: {str(error)}"


    def get_question_by_id(self, question_id: int) -> tuple[bool, Question | str | None]:
        """
        Retrieves a single question by its unique database identifier.

        This method is the primary tool for targeted operations such as
        editing a specific question, toggling its status, or fetching
        detailed content for a single-question view. It uses a scalar
        query to return the specific model instance.

        Args:
            question_id (int): The unique primary key of the question.

        Returns:
            tuple[bool, Question | str | None]:
                - If successful: (True, Question object or None if not found)
                - If no questions exist: (False, "No questions found" message)
                - If failed: (False, Error message string)

        Note:
            A 'success' (True) result with 'None' as the object indicates
            that the ID does not exist in the database.
        """
        try:
            stmt = select(Question).where(Question.id == question_id)
            question = self._db.execute(stmt).scalar()

            if not question:
                return False, QuestionMessages.QUESTION_NOT_FOUND

            return True, question
        except SQLAlchemyError as error:
            return False, f"{QuestionMessages.GET_QUESTION_ERROR} {error}"

    def get_question_input_by_id(
            self,
            question_input_id: int) -> tuple[bool, QuestionInput | None | str]:
        """
        Retrieves a specific QuestionInput record by its unique identifier.

        This is used to fetch the state of a generation job, including the
        raw input and any AI-extracted drafts stored in the JSON buffer.

        Args:
            question_input_id (int): The primary key of the QuestionInput record.

        Returns:
            tuple[bool, QuestionInput | None | str]:
                - If successful: (True, QuestionInput object or None if not found)
                - If failed: (False, Error message string)
        """
        try:
            stmt = select(QuestionInput).where(QuestionInput.id == question_input_id)
            question_input = self._db.execute(stmt).scalar()

            return True, question_input
        except SQLAlchemyError as error:
            return False, f"{QuestionMessages.GET_QUESTION_INPUT_ERROR} {str(error)}"


    def set_question_status(
            self,
            question_id: int,
            active: QuestionStatus) -> tuple[bool, Question | str]:
        """
        Toggles the operational visibility of a question.

        This method allows administrators to enable or disable a question
        without deleting it from the database. It first verifies the
        existence of the question using 'get_question_by_id' before
        applying the new status. This is crucial for maintaining
        historical data while controlling what students see in active sessions.

        Args:
            question_id (int): The unique identifier of the target question.
            active (QuestionStatus): A validated Pydantic schema containing
                                     the desired 'is_active' boolean state.

        Returns:
            tuple[bool, Question | str]:
                - If successful: (True, The updated Question object)
                - If failed: (False, Error message, e.g., if the question
                             was not found or a DB error occurred)

        Note:
            Deactivating a question (is_active=False) typically excludes it
            from the adaptive learning engine and public API responses.
        """
        try:
            success, result_question = self.get_question_by_id(question_id)

            if not success:
                return False, result_question

            result_question.is_active = active.is_active
            self._db.commit()
            self._db.refresh(result_question)
            return True, result_question
        except SQLAlchemyError as error:
            return False, f"{QuestionMessages.STATUS_UPDATE_ERROR} {str(error)}"


    def update_question(
            self,
            question_id: int,
            question_update: QuestionUpdate) -> tuple[bool, Question | str]:
        """
        Performs a partial update of an existing question's attributes.

        This method implements a PATCH-style update logic. It leverages Pydantic's
        'exclude_unset=True' to ensure that only fields explicitly provided in
        the request are modified. It maintains data integrity by verifying the
        question's existence before applying changes.

        Special Handling:
        - JSON Fields: Nested structures like 'options' and 'explanations' are
          overwritten as atomic units if provided, ensuring internal consistency.
        - Persistence: Uses SQLAlchemy's 'setattr' for dynamic mapping and
          enforces a transaction rollback on failure.

        Args:
            question_id (int): The unique database identifier of the question.
            question_update (QuestionUpdate): A validated schema containing
                                              the fields to be updated.

        Returns:
            tuple[bool, Question | str]:
                - If successful: (True, The updated Question object)
                - If failed: (False, Error message string)

        Note:
            Structural fields like 'id' or 'is_llm_variant' are typically
            omitted from this update path to preserve data lineage.
        """
        try:
            success, result_question = self.get_question_by_id(question_id)

            if not success:
                return False, result_question

            update_dict = question_update.model_dump(exclude_unset=True)

            for key, value in update_dict.items():
                setattr(result_question, key, value)

            self._db.commit()
            self._db.refresh(result_question)
            return True, result_question
        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{QuestionMessages.UPDATE_QUESTION_ERROR} {str(error)}"


    def update_question_input(
            self,
            question_input_id: int,
            question_input_update: QuestionInputUpdate) -> tuple[bool, QuestionInput | str]:
        """
        Performs a partial update on an existing QuestionInput record.

        This method follows the PATCH principle, allowing for granular adjustments
        to the input metadata (e.g., subject, topic, grade) or the raw source text.
        It is typically used to correct user errors before the final promotion
        of AI drafts to the global question pool.

        Args:
            question_input_id (int): The unique identifier of the target record.
            question_input_update (QuestionInputUpdate): A validated DTO containing
                                                         only the fields to be modified.

        Returns:
            tuple[bool, QuestionInput | str]:
                - If successful: (True, The updated QuestionInput model instance)
                - If failed: (False, An error message explaining the failure)

        Note:
            Uses Pydantic's `exclude_unset=True` to ensure that only fields explicitly
            provided in the request payload are overwritten in the database.
        """
        try:
            success, result_question_input = self.get_question_input_by_id(question_input_id)
            if not success:
                return False, result_question_input
            if not result_question_input:
                return False, QuestionMessages.QUESTION_INPUT_NOT_FOUND

            update_dict = question_input_update.model_dump(exclude_unset=True)

            for key, value in update_dict.items():
                setattr(result_question_input, key, value)

            self._db.commit()
            self._db.refresh(result_question_input)
            return True, result_question_input

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{QuestionMessages.UPDATE_QUESTION_INPUT_ERROR} {str(error)}"



    def _exist_subject_and_topic(self, subject_id: int, topic_id: int) -> tuple[bool, Topic | str]:
        """
        Internal helper to verify the hierarchical integrity of a subject and topic.

        This method delegates the validation logic to the 'KnowledgeManager' while
        reusing the current database session. It ensures that the requested topic
        is actually a child of the specified subject, preventing orphaned or
        misaligned question entries.

        Args:
            subject_id (int): The unique identifier of the parent subject.
            topic_id (int): The unique identifier of the topic to be verified.

        Returns:
            tuple[bool, Topic | str]:
                - If valid: (True, The retrieved Topic object)
                - If invalid: (False, An error message from KnowledgeMessages)

        Note:
            By sharing 'self._db', this helper maintains transaction consistency
            across different manager domains without creating overhead.
        """
        knowledge_manager = KnowledgeManager(self._db)

        success, result = knowledge_manager.get_topic_from_subject(subject_id, topic_id)
        if not success:
            return False, result

        return True, result

    @staticmethod
    def _get_questions_from_json(raw_data: Any) -> list[dict]:
        """
        Safely parses the 'extracted_questions' field into a list of dictionaries.

        This helper handles the various ways SQLAlchemy might return JSON data
        (as a string, dict, or list) and ensures a consistent iterable output.

        Args:
            raw_data (Any): The raw data from the JSON column.

        Returns:
            list[dict]: A list of question dictionaries, or an empty list if
                        parsing fails or no data is present.
        """
        if not raw_data:
            return []

        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return []

        if isinstance(raw_data, dict):
            return raw_data.get("extracted_questions", [])

        if isinstance(raw_data, list):
            return raw_data

        return []
