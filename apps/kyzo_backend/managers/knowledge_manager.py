from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import KnowledgeMessages
from apps.kyzo_backend.data import Subject
from apps.kyzo_backend.schemas import SubjectCreate, SubjectStatus, SubjectUpdate


class KnowledgeManager:
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


    def add_subject(self, subject_data: SubjectCreate) -> tuple[bool, Subject | str]:
        """
        Adds a new academic subject to the database.

        This method validates that the subject name is unique (case-insensitive)
        before persistence. It converts the incoming Pydantic schema into a
        SQLAlchemy model and handles database commitment and refresh.

        Args:
            subject_data (SubjectCreate): The validated data for the new subject.

        Returns:
            tuple[bool, Subject | str]:
                - If successful: (True, Subject-instance)
                - If name exists: (False, KnowledgeMessages.SUBJECT_ALREADY_EXISTS)
                - If DB error: (False, Error-Message)
        """
        try:
            stmt = (
                select(Subject)
                .where(func.lower(Subject.name) == func.lower(subject_data.name))
            )
            existing = self._db.execute(stmt).scalar_one_or_none()

            if existing:
                return False, KnowledgeMessages.SUBJECT_ALREADY_EXISTS

            subject_dict = subject_data.model_dump()
            new_subject = Subject(**subject_dict)

            self._db.add(new_subject)
            self._db.commit()
            self._db.refresh(new_subject)
            return True, new_subject

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{KnowledgeMessages.CREATE_ERROR}: {str(error)}"


    def get_all_subjects(self) -> tuple[bool, list[Subject] | str]:
        """
        Retrieves all subjects currently stored in the database.

        This method fetches every subject entry without filtering by
        activation status. It is primarily used for administrative
        overviews or populating selection lists.

        Returns:
            tuple[bool, list[Subject] | str]:
                - If successful: (True, [Subject, ...]) - A list of Subject instances.
                - If DB error: (False, KnowledgeMessages.GET_ALL_SUBJECTS_ERROR + detail)
        """
        try:
            stmt = select(Subject)
            all_subjects = self._db.execute(stmt).scalars().all()

            return True, list(all_subjects)
        except SQLAlchemyError as error:
            return False, f"{KnowledgeMessages.GET_ALL_SUBJECTS_ERROR} {str(error)}"


    def get_subject_by_id(self, subject_id: int) -> tuple[bool, Subject | None | str]:
        """
        Fetches a single subject by its unique database ID.

        Args:
            subject_id (int): The primary key of the subject to retrieve.

        Returns:
            tuple[bool, Subject | None | str]:
                - If found: (True, Subject-instance)
                - If not found: (True, None)
                - If DB error: (False, Error-Message)
        """
        try:
            stmt = select(Subject).where(Subject.id == subject_id)
            subject = self._db.execute(stmt).scalar_one_or_none()

            return True, subject

        except SQLAlchemyError as error:
            return False, f"{KnowledgeMessages.GET_SUBJECT_ERROR} {str(error)}"


    def set_subject_status(self, subject_id: int, active: SubjectStatus) \
            -> tuple[bool, Subject | None | str]:
        """
        Updates the activation status of a specific subject.

        This method acts as a 'soft-delete' mechanism. Deactivating a subject
        (is_active=False) makes it unavailable for new content generation
        and student access while preserving all existing associations
        (topics, questions) in the database.

        Args:
            subject_id (int): The unique ID of the subject to modify.
            active (SubjectStatus): A validated schema containing the
                                   new boolean status.

        Returns:
            tuple[bool, Subject | None | str]:
                - If updated: (True, Subject-instance)
                - If not found: (True, None)
                - If DB error: (False, Error-Message)
        """
        try:
            success, result = self.get_subject_by_id(subject_id)

            if not success:
                return False, result
            if result is None:
                return True, None

            result.is_active = active.is_active
            self._db.commit()
            self._db.refresh(result)
            return True, result
        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{KnowledgeMessages.STATUS_UPDATE_ERROR} {str(error)}"


    def update_subject(self, subject_id: int, subject_update: SubjectUpdate) \
            -> tuple[bool, Subject | None | str]:
        """
        Updates the metadata of an existing subject.

        This method performs a partial update (PATCH-style). Only the fields
        provided in the SubjectUpdate schema are modified in the database.
        It uses dynamic attribute setting to ensure scalability as more
        subject attributes are added.

        Args:
            subject_id (int): The unique ID of the subject to update.
            subject_update (SubjectUpdate): A schema containing the fields
                                           to be changed (e.g., 'name').

        Returns:
            tuple[bool, Subject | None | str]:
                - If updated: (True, Subject-instance)
                - If not found: (True, None)
                - If DB error: (False, Error-Message)
        """
        try:
            success, result = self.get_subject_by_id(subject_id)

            if not success:
                return False, result
            if result is None:
                return True, None

            update_dict = subject_update.model_dump(exclude_unset=True)

            for key, value in update_dict.items():
                setattr(result, key, value)

            self._db.commit()
            self._db.refresh(result)
            return True, result
        except SQLAlchemyError as error:
            self._db.rollback()
            return  False, f"{KnowledgeMessages.UPDATE_SUBJECT_ERROR} {str(error)}"
