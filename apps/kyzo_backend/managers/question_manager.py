from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import QuestionMessages
from apps.kyzo_backend.data import Question, Topic
from apps.kyzo_backend.managers import KnowledgeManager
from apps.kyzo_backend.schemas import QuestionCreate, QuestionStatus, QuestionUpdate


class QuestionManager:
    """
    Business logic layer for managing educational content.

    This manager orchestrates operations related to subjects, topics,
    and learning materials, acting as a bridge between the database
    models and the API layer.
    """

    def __init__(self, db: Session):
        """
        Initializes the KnowledgeManager with a database session.

        This approach follows the Dependency Injection principle to decouple
        the business logic from the session creation. It is essential for
        unit testing, as it allows passing a mock session or an in-memory
        SQLite database without modifying the Manager's code.

        Args:
            db (Session): An active SQLAlchemy database session used
                         for all persistence operations.
        """
        self._db = db


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


    def get_all_questions(self) -> tuple[bool, list[Question] | str]:
        """
        Retrieves all questions from the database without any filters.

        This method provides a global overview of the entire question pool.
        It is typically used for administrative dashboards, content audits,
        or cross-subject analytics. It returns the raw SQLAlchemy objects
        which can be serialized via Pydantic in the API layer.

        Returns:
            tuple[bool, list[Question] | str]:
                - If successful: (True, List of all Question objects)
                - If failed: (False, Error message string)

        Note:
            For large datasets, this operation can be performance-intensive.
            Consider using scoped retrieval methods (by subject or topic)
            for student-facing features.
        """
        try:
            stmt = select(Question)
            all_questions = self._db.execute(stmt).scalars().all()

            return True, list(all_questions)
        except SQLAlchemyError as error:
            return False, f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR} {str(error)}"


    def get_all_questions_for_subject(self, subject_id: int) -> tuple[bool, list[Question] | str]:
        """
        Retrieves all questions associated with a specific subject.

        This method filters the question pool at the curriculum level. It is
        ideal for generating subject-wide practice exams or administrative
        reports. By filtering directly via 'subject_id', it ensures efficient
        data retrieval without the need for complex joins across the topic hierarchy.

        Args:
            subject_id (int): The unique database identifier of the subject.

        Returns:
            tuple[bool, list[Question] | str]:
                - If successful: (True, List of Question objects for the subject)
                - If failed: (False, Error message string)

        Note:
            The returned list includes all questions, regardless of their
            topic assignment or active status, within the given subject.
        """
        try:
            stmt = select(Question).where(Question.subject_id == subject_id)
            all_questions = self._db.execute(stmt).scalars().all()

            return True, list(all_questions)
        except SQLAlchemyError as error:
            return False, f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR} {str(error)}"


    def get_all_questions_for_subject_topic(
            self,
            subject_id: int,
            topic_id: int) -> tuple[bool, list[Question] | str]:
        """
        Retrieves all questions belonging to a specific topic within a subject.

        This is the most granular retrieval method, primarily used for targeted
        learning sessions where a student focuses on a single curriculum unit.
        It enforces the dual-key relationship (subject and topic) to ensure
        data consistency and curriculum alignment.

        Args:
            subject_id (int): The unique database identifier of the subject.
            topic_id (int): The unique database identifier of the topic.

        Returns:
            tuple[bool, list[Question] | str]:
                - If successful: (True, List of Question objects for this specific unit)
                - If failed: (False, Error message string)

        Note:
            While this method filters by both IDs, it does not implicitly verify
            if the topic actually belongs to the subject. For strict hierarchy
            validation, use the internal '_exist_subject_and_topic' helper beforehand.
        """
        try:
            stmt = (select(Question)
                    .where(Question.subject_id == subject_id)
                    .where(Question.topic_id == topic_id))
            all_questions = self._db.execute(stmt).scalars().all()

            return True, list(all_questions)
        except SQLAlchemyError as error:
            return False, f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR} {str(error)}"


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
                - If failed: (False, Error message string)

        Note:
            A 'success' (True) result with 'None' as the object indicates
            that the ID does not exist in the database.
        """
        try:
            stmt = select(Question).where(Question.id == question_id)
            question = self._db.execute(stmt).scalar()

            return True, question
        except SQLAlchemyError as error:
            return False, f"{QuestionMessages.GET_QUESTIONS_ERROR} {error}"


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
