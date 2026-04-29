import json
from typing import Any, Optional

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import QuestionMessages
from apps.kyzo_backend.data import Question, QuestionInput, QuestionOrigin, Topic
from apps.kyzo_backend.managers import KnowledgeManager
from apps.kyzo_backend.schemas import (QuestionCreate,
                                       QuestionStatus,
                                       QuestionUpdate,
                                       QuestionInputCreate,
                                       QuestionInputUpdate,
                                       QuestionInputRawInput)
from apps.kyzo_backend.services import ImageProcessingService, LLMService, QuestionGenerator


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
        self.image_service = ImageProcessingService()
        self.llm_service = LLMService()
        self.question_generator = QuestionGenerator()

    def add_question(self, question_data: QuestionCreate) -> Question:
        """
        Creates and persists a new question in the database after hierarchy validation.

        This method ensures that the question is correctly placed within the
        educational structure. It verifies that the specified subject and topic
        exist and are properly linked before persisting the question.

        Args:
            question_data (QuestionCreate): Validated Pydantic schema containing
                                            all question attributes.

        Returns:
            Question: The newly created and persisted Question instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If the subject or topic hierarchy is invalid.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        self._validate_hierarchy(
            question_data.subject_id,
            question_data.topic_id
        )

        try:
            question_dict = question_data.model_dump()
            new_question = Question(**question_dict)

            self._db.add(new_question)
            self._db.commit()
            self._db.refresh(new_question)

            return new_question

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.CREATE_QUESTION_ERROR} {str(error)}"
            ) from error

    async def add_question_input_with_file(
            self,
            num_of_questions: int,
            question_input_data: QuestionInputCreate,
            files: Optional[list[UploadFile]] = None
    ) -> str:
        """
        Orchestrates the full pipeline for generating questions from
        text or multi-format file inputs.

        This high-level workflow coordinates several specialized services:
        1. Validates the integrity of the input metadata and category hierarchy.
        2. Processes file uploads (Images/PDFs) by converting them into optimized
           text via Vision-OCR if 'files' are provided.
        3. Triggers the LLM-based question generation engine using the aggregated content.
        4. Persists the raw input, metadata, and generated questions in a single
           atomic database transaction.

        Args:
            num_of_questions (int): The target number of questions to be generated.
            question_input_data (QuestionInputCreate): Pydantic model containing user preferences,
                                                       grade level, and hierarchy IDs.
            files (Optional[list[UploadFile]]): A list of uploaded files (JPG, PNG, PDF).
                                                Defaults to None for purely text-based inputs.

        Returns:
            str: A localized success message indicating the number of successfully
                 generated and stored questions.

        Raises:
            HTTPException:
                - 400 (Bad Request) if validation fails or files are corrupt.
                - 500 (Internal Server Error) if the LLM fails, Poppler is misconfigured,
                  or a database SQLAlchemyError occurs.
        """
        self._validate_input_data_content_or_file(question_input_data, files)

        subject_name, topic_name = self._validate_hierarchy_and_get_names(
            question_input_data.subject_id,
            question_input_data.topic_id
        )

        if files:
            (question_input_data.raw_input.content,
             question_input_data.raw_input.source_ref) = await self._get_raw_input_from_files(files)

        extracted_questions = self.question_generator.generate_extracted_questions_from_raw_input(
            subject_name=subject_name,
            topic_name=topic_name,
            grade=question_input_data.grade,
            raw_input=question_input_data.raw_input,
            num_of_questions=num_of_questions
        )

        try:
            question_input_dict = question_input_data.model_dump()

            full_data = extracted_questions.model_dump()
            question_input_dict["extracted_questions"] = full_data["extracted_questions"]

            new_question_input = QuestionInput(**question_input_dict)
            self._db.add(new_question_input)
            self._db.commit()
            self._db.refresh(new_question_input)

            return QuestionMessages.QUESTION_INPUT_PROCESSED.format(
                num_of_questions=len(new_question_input.extracted_questions)
            )

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.CREATE_QUESTION_INPUT_ERROR} {str(error)}"
            ) from error

    def count_questions(self, subject_id: int, topic_id: Optional[int] = None) -> int:
        """
        Retrieves the total number of questions for a subject or a specific topic.

        This high-performance count operation is typically used to validate question
        availability before initializing learning sessions or to display statistics.

        Args:
            subject_id (int): The unique identifier of the parent subject.
            topic_id (Optional[int]): Optional identifier to narrow the count
                                      to a specific topic.

        Returns:
            int: The total count of questions found.

        Raises:
            HTTPException:
                - 500 (Internal Server Error): If a database execution failure occurs.
        """
        try:
            # pylint: disable=not-callable
            stmt = (
                select(func.count())
                .select_from(Question)
                .where(Question.subject_id == subject_id)
            )

            if topic_id is not None:
                stmt = stmt.where(Question.topic_id == topic_id)

            count = self._db.execute(stmt).scalar() or 0
            return count

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR} {str(error)}"
            ) from error

    def create_questions_from_question_input(
            self,
            question_input_id: int
    ) -> str:
        """
        Promotes AI-generated drafts from a buffer to the permanent question pool.

        This method handles the transition from 'draft' to 'live' content. It maps
        buffered JSON data to the Question model, establishes audit traceability
        via QuestionOrigin, and ensures idempotency by checking the processing state.

        Args:
            question_input_id (int): ID of the input record containing the drafts.

        Returns:
            str: Success message indicating the number of promoted questions.

        Raises:
            HTTPException:
                - 400 (Bad Request): If the input is already processed or empty.
                - 404 (Not Found): If the QuestionInput ID does not exist.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        question_input = self.get_question_input_by_id(question_input_id)

        if question_input.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=QuestionMessages.QUESTION_INPUT_ALREADY_PROCESSED
            )

        if not question_input.extracted_questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=QuestionMessages.NO_QUESTION_TO_PROCESS
            )

        try:
            extracted_question_dict = self._get_questions_from_json(
                question_input.extracted_questions
            )
            new_questions_count = 0

            for question in extracted_question_dict:
                new_question = Question(
                    subject_id=question_input.subject_id,
                    topic_id=question_input.topic_id,
                    grade=question_input.grade,
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
                    question_input_id=question_input.id
                )
                self._db.add(origin_link)

                new_questions_count += 1

            question_input.is_processed = True

            self._db.commit()

            return QuestionMessages.QUESTION_INPUT_TO_QUESTION.format(
                new_questions_count=new_questions_count
            )

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.CREATE_QUESTION_ERROR} {str(error)}"
            ) from error

    def extract_questions_from_raw_input(
            self,
            question_input_id: int,
            num_of_questions: int
    ) -> str:
        """
        Extracts educational questions from an existing raw input record using AI.

        This method acts as a recovery or re-processing mechanism. It fetches an
        existing QuestionInput, triggers a new AI generation cycle, and updates
         the record with the newly extracted drafts.

        Args:
            question_input_id (int): The unique identifier of the raw input record.
            num_of_questions (int): The desired number of questions to be generated.

        Returns:
            str: A status message confirming the number of questions processed.

        Raises:
            HTTPException:
                - 400 (Bad Request): If the record has already been promoted to questions.
                - 404 (Not Found): If the QuestionInput ID does not exist.
                - 502 (Bad Gateway): If the AI service fails.
                - 500 (Internal Server Error): If a database transaction error occurs.
        """
        question_input = self.get_question_input_by_id(question_input_id)

        subject_name, topic_name = self._validate_hierarchy_and_get_names(
            question_input.subject_id,
            question_input.topic_id
        )

        if question_input.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=QuestionMessages.QUESTION_INPUT_ALREADY_PROCESSED
            )

        try:
            raw_input_data = QuestionInputRawInput(**question_input.raw_input)

            ai_result = self.question_generator.generate_extracted_questions_from_raw_input(
                subject_name=subject_name,
                topic_name=topic_name,
                grade=question_input.grade,
                raw_input=raw_input_data,
                num_of_questions=num_of_questions
            )

            full_data = ai_result.model_dump()
            extracted_list = full_data["extracted_questions"]

            question_input.extracted_questions = extracted_list
            question_input.is_processed = True

            self._db.commit()
            self._db.refresh(question_input)

            return QuestionMessages.QUESTION_INPUT_PROCESSED.format(
                num_of_questions=len(extracted_list)
            )

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.CREATE_QUESTION_INPUT_ERROR} {str(error)}"
            ) from error

    def get_all_questions(self) -> list[Question]:
        """
        Retrieves all questions from the database without any filters.

        This method provides a global overview of the entire question pool,
        intended for administrative dashboards or content audits.

        Returns:
            list[Question]: A comprehensive list of all Question instances.

        Raises:
            HTTPException:
                - 404 (Not Found): If the question pool is entirely empty.
                - 500 (Internal Server Error): If a database execution failure occurs.

        Note:
            **Performance Warning**: This operation performs a full table scan.
            In production environments with large datasets, consider using
            paginated or scoped retrieval methods.
        """
        try:
            stmt = select(Question)
            all_questions = self._db.execute(stmt).scalars().all()

            if not all_questions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=QuestionMessages.QUESTION_NOT_FOUND
                )

            return list(all_questions)

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR} {str(error)}"
            ) from error

    def get_questions_for_subject_topic(
            self,
            subject_id: int,
            topic_id: Optional[int] = None
    ) -> list[Question]:
        """
        Retrieves questions filtered by subject and optionally by topic.

        This unified method serves as the central point for content retrieval,
        supporting both broad subject-wide overviews and granular topic-specific drills.

        Args:
            subject_id (int): The unique database identifier of the subject.
            topic_id (Optional[int]): The unique identifier of the topic.
                                      If None, retrieves all questions for the subject.

        Returns:
            list[Question]: A list of retrieved Question instances.

        Raises:
            HTTPException:
                - 404 (Not Found): If no questions match the given criteria.
                - 500 (Internal Server Error): If a database execution failure occurs.
        """
        try:
            stmt = select(Question).where(Question.subject_id == subject_id)

            if topic_id is not None:
                stmt = stmt.where(Question.topic_id == topic_id)

            all_questions = self._db.execute(stmt).scalars().all()

            if not all_questions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=QuestionMessages.QUESTION_NOT_FOUND
                )

            return list(all_questions)

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.GET_ALL_QUESTIONS_ERROR} {str(error)}"
            ) from error

    def get_question_by_id(self, question_id: int) -> Question:
        """
        Retrieves a single question by its unique database identifier.

        This method serves as the primary utility for targeted operations like
        editing, status toggling, or detailed single-item views. It ensures that
        the requested question exists before returning the model instance.

        Args:
            question_id (int): The unique primary key of the question.

        Returns:
            Question: The retrieved Question instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If no question exists with the given ID.
                - 500 (Internal Server Error): If a database execution failure occurs.
        """
        try:
            stmt = select(Question).where(Question.id == question_id)
            question = self._db.execute(stmt).scalar_one_or_none()

            if not question:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=QuestionMessages.QUESTION_NOT_FOUND
                )

            return question

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.GET_QUESTION_ERROR} {str(error)}"
            ) from error

    def get_question_input_by_id(
            self,
            question_input_id: int
    ) -> QuestionInput:
        """
        Retrieves a specific QuestionInput record by its unique identifier.

        This method acts as a guard and retrieval utility for the question review
        process. It fetches the generation job state, including raw source text
        and the JSON buffer of AI-extracted drafts.

        Args:
            question_input_id (int): The primary key of the QuestionInput record.

        Returns:
            QuestionInput: The retrieved QuestionInput instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If no record exists with the given ID.
                - 500 (Internal Server Error): If a database execution failure occurs.
        """
        try:
            stmt = select(QuestionInput).where(QuestionInput.id == question_input_id)
            question_input = self._db.execute(stmt).scalar_one_or_none()

            if not question_input:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=QuestionMessages.QUESTION_INPUT_NOT_FOUND
                )

            return question_input

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.GET_QUESTION_INPUT_ERROR} {str(error)}"
            ) from error

    def set_question_status(
            self,
            question_id: int,
            active: QuestionStatus
    ) -> Question:
        """
        Updates the operational visibility (active/inactive) of a specific question.

        This method implements a soft-delete toggle. It allows for hiding questions
        from the active learning engine while preserving historical data and
        audit trails.

        Args:
            question_id (int): The unique identifier of the target question.
            active (QuestionStatus): Schema containing the target 'is_active' state.

        Returns:
            Question: The updated Question instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If the question does not exist (via get_question_by_id).
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        question = self.get_question_by_id(question_id)

        try:
            question.is_active = active.is_active

            self._db.commit()
            self._db.refresh(question)

            return question

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.STATUS_UPDATE_ERROR} {str(error)}"
            ) from error

    def update_question(
            self,
            question_id: int,
            question_update: QuestionUpdate
    ) -> Question:
        """
        Performs a partial update of an existing question's attributes.

        This method implements PATCH-style logic, ensuring only fields explicitly
        provided in the request are modified. It maintains data integrity by
        verifying the question's existence before applying changes.

        Args:
            question_id (int): The unique database identifier of the question.
            question_update (QuestionUpdate): Schema containing the fields to update.

        Returns:
            Question: The updated and persisted Question instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If no question exists with the given ID.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        question = self.get_question_by_id(question_id)

        try:
            update_dict = question_update.model_dump(exclude_unset=True)

            for key, value in update_dict.items():
                setattr(question, key, value)

            self._db.commit()
            self._db.refresh(question)

            return question

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.UPDATE_QUESTION_ERROR} {str(error)}"
            ) from error

    def update_question_input(
            self,
            question_input_id: int,
            question_input_update: QuestionInputUpdate
    ) -> QuestionInput:
        """
        Performs a partial update on an existing QuestionInput record.

        This method follows the PATCH principle, allowing for granular adjustments
        to metadata or raw source text. It is typically used to correct input
        parameters before final AI processing or promotion.

        Args:
            question_input_id (int): The unique identifier of the target record.
            question_input_update (QuestionInputUpdate): Schema containing only
                                                         the fields to be modified.

        Returns:
            QuestionInput: The updated and persisted QuestionInput model instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If the record does not exist (via get_question_input_by_id).
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        question_input = self.get_question_input_by_id(question_input_id)

        try:
            update_dict = question_input_update.model_dump(exclude_unset=True)

            for key, value in update_dict.items():
                setattr(question_input, key, value)

            self._db.commit()
            self._db.refresh(question_input)

            return question_input

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{QuestionMessages.UPDATE_QUESTION_INPUT_ERROR}: {str(error)}"
            ) from error

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

    async def _get_raw_input_from_files(self, files: list[UploadFile]) -> tuple[str, str]:
        """
        Processes a list of uploaded files, performs OCR, and aggregates the results.

        Each file is optimized and stored. If a file contains multiple pages (like a PDF),
        each page is processed individually. The extracted text from all sources
        is concatenated into a single string.

        Args:
            files (list[UploadFile]): The uploaded image or PDF files.

        Returns:
            tuple[str, str]: A tuple containing (full_content, source_references).
        """
        source_refs = []
        content_parts = []

        for file in files:
            processed_elements = await self.image_service.process_upload(file)

            for element in processed_elements:
                ocr_result = self.llm_service.generate_raw_input_from_scan(
                    base64_image=element["base64"],
                    mime_type=element["mime_type"]
                )

                header = f"--- Source: {element['file_id']} ({file.filename}) ---"
                content_parts.append(f"{header}\n{ocr_result.extracted_text}")
                source_refs.append(element['file_id'])

        full_content = "\n\n".join(content_parts)
        combined_source_ref = f"Scans: {', '.join(source_refs)}"

        return full_content, combined_source_ref

    def _validate_hierarchy(self, subject_id: int, topic_id: int) -> Topic:
        """
        Internal helper to verify the hierarchical integrity of a subject and topic.

        This method delegates the validation logic to the 'KnowledgeManager' while
        reusing the current database session. It ensures that the requested topic
        is actually a child of the specified subject.

        Args:
            subject_id (int): The unique identifier of the parent subject.
            topic_id (int): The unique identifier of the topic to be verified.

        Returns:
            Topic: The retrieved and validated Topic object.

        Raises:
            HTTPException:
                - 404 (Not Found): If the subject/topic link is invalid (via KnowledgeManager).
                - 500 (Internal Server Error): If a database error occurs.
        """
        knowledge_manager = KnowledgeManager(self._db)

        return knowledge_manager.get_topic_from_subject(subject_id, topic_id)

    def _validate_hierarchy_and_get_names(self, subject_id: int, topic_id: int) -> tuple[str, str]:
        """
        Verifies the hierarchical integrity and retrieves the names for subject and topic.

        This method ensures that the requested topic is a child of the specified subject
        and returns their human-readable names to be used in AI prompts.

        Args:
            subject_id (int): The unique identifier of the parent subject.
            topic_id (int): The unique identifier of the topic.

        Returns:
            tuple[str, str]: A tuple containing (subject_name, topic_name).

        Raises:
            HTTPException:
                - 404 (Not Found): If the subject or topic does not exist or the
                  link is invalid.
                - 500 (Internal Server Error): If a database error occurs.
        """
        knowledge_manager = KnowledgeManager(self._db)

        subject = knowledge_manager.get_subject_by_id(subject_id)
        topic = knowledge_manager.get_topic_from_subject(subject_id, topic_id)

        return subject.name, topic.name

    @staticmethod
    def _validate_input_data_content_or_file(
            question_input_data: QuestionInputCreate,
            files: Optional[list[UploadFile]] = None
    ):
        """
        Enforces the exclusive input rule: either raw text content or a file must be provided.

        Refined to handle the case where raw_input.content might be an empty string
        due to the 'scan' type initialization.

        Args:
            question_input_data (QuestionInputCreate): The validated metadata containing
                                                       potential text content.
            files (Optional[UploadFile]): The uploaded file, if any.

        Raises:
            HTTPException (400): If both text content and a file are provided,
                                 or if both are missing.
        """
        has_content = (
                question_input_data.raw_input is not None and
                bool(question_input_data.raw_input.content.strip())
        )

        has_file = bool(files and len(files) > 0)

        if has_content == has_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=QuestionMessages.QUESTION_INPUT_CONTENT_OR_FILE
            )
