from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import KnowledgeMessages
from apps.kyzo_backend.data import Subject, Topic
from apps.kyzo_backend.schemas import (SubjectCreate, SubjectStatus, SubjectUpdate,
                                       TopicCreate, TopicStatus, TopicUpdate)


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

    def add_subject(self, subject_data: SubjectCreate) -> Subject:
        """
        Persists a new academic subject in the database after validation.

        This method ensures the subject name is unique (case-insensitive) before
        creating a new record.

        Args:
            subject_data (SubjectCreate): Pydantic schema with subject attributes.

        Returns:
            Subject: The newly created and persisted Subject instance.

        Raises:
            HTTPException:
                - 409 (Conflict): If a subject with the same name already exists.
                - 500 (Internal Server Error): If a database transaction fails.
        """
        if self._is_subject_name_taken(subject_data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=KnowledgeMessages.SUBJECT_ALREADY_EXISTS
            )
        try:
            subject_dict = subject_data.model_dump()
            new_subject = Subject(**subject_dict)

            self._db.add(new_subject)
            self._db.commit()
            self._db.refresh(new_subject)
            return new_subject

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.CREATE_SUBJECT_ERROR} {str(error)}"
            ) from error

    def add_topic_to_subject(self, topic_data: TopicCreate) -> Topic:
        """
        Persists a new learning topic within a specific subject after validation.

        This method ensures the integrity of the knowledge hierarchy by verifying
        the parent subject's existence and ensuring the topic name is unique
        within that subject's scope.

        Args:
            topic_data (TopicCreate): Validated Pydantic schema for the new topic.

        Returns:
            Topic: The newly created and persisted Topic instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If the parent subject_id does not exist.
                - 409 (Conflict): If a topic with the same name already exists in this subject.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        self.get_subject_by_id(topic_data.subject_id)

        if self._is_topic_name_taken_in_subject(topic_data.name, topic_data.subject_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=KnowledgeMessages.TOPIC_ALREADY_EXISTS
            )

        try:
            topic_dict = topic_data.model_dump()
            new_topic = Topic(**topic_dict)

            self._db.add(new_topic)
            self._db.commit()
            self._db.refresh(new_topic)
            return new_topic

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.CREATE_TOPIC_ERROR} {str(error)}"
            ) from error

    def get_all_subjects(self) -> list[Subject]:
        """
        Retrieves a comprehensive list of all subjects in the database.

        This method provides a full collection of subject records. It is used
        for populating navigation elements, dashboards, and administrative
        overviews.

        Returns:
            list[Subject]: A list containing all retrieved Subject instances.

        Raises:
            HTTPException:
                - 404 (Not Found): If no subjects are found in the database.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        try:
            stmt = select(Subject)
            all_subjects = self._db.execute(stmt).scalars().all()

            if not all_subjects:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=KnowledgeMessages.NO_SUBJECTS
                )

            return list(all_subjects)

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.GET_ALL_SUBJECTS_ERROR} {str(error)}"
            ) from error

    def get_all_topic_from_subject(self, subject_id: int) -> list[Topic]:
        """
        Retrieves all learning topics associated with a specific subject.

        This method performs a two-step validation: first, it ensures the parent
        subject exists. Then, it fetches all linked topics. This allows for
        clear distinction between a missing subject and a subject that simply
        has no topics assigned yet.

        Args:
            subject_id (int): The unique identifier of the parent subject.

        Returns:
            list[Topic]: A list of Topic instances belonging to the subject.

        Raises:
            HTTPException:
                - 404 (Not Found): If the parent subject does not exist (via get_subject_by_id)
                  OR if the subject exists but contains no topics.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        self.get_subject_by_id(subject_id)

        try:
            stmt = select(Topic).where(Topic.subject_id == subject_id)
            all_topics = self._db.execute(stmt).scalars().all()

            if not all_topics:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=KnowledgeMessages.NO_TOPICS_FOR_SUBJECTS
                )

            return list(all_topics)

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.GET_ALL_TOPICS_FROM_SUBJECT_ERROR} {str(error)}"
            ) from error

    def get_subject_by_id(self, subject_id: int) -> Subject:
        """
        Retrieves a single subject by its unique database identifier.

        This method serves as a primary lookup and validation utility. It is
        frequently used as a guard clause in hierarchical operations to ensure
        the existence of a parent subject before proceeding with dependent tasks.

        Args:
            subject_id (int): The primary key of the subject to retrieve.

        Returns:
            Subject: The retrieved Subject instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If no subject exists with the given ID.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        try:
            stmt = select(Subject).where(Subject.id == subject_id)
            subject = self._db.execute(stmt).scalar_one_or_none()

            if not subject:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=KnowledgeMessages.SUBJECT_NOT_FOUND
                )

            return subject

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.GET_SUBJECT_ERROR} {str(error)}"
            ) from error

    def get_topic_from_subject(self, subject_id: int, topic_id: int) -> Topic:
        """
        Retrieves a specific topic while strictly enforcing its subject association.

        This method acts as a security and integrity guard. It ensures that the
        requested topic is not only existent but specifically belongs to the
        provided parent subject, preventing unauthorized cross-subject access.

        Args:
            subject_id (int): The unique identifier of the parent subject.
            topic_id (int): The unique identifier of the topic to retrieve.

        Returns:
            Topic: The validated Topic instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If the subject does not exist OR the topic
                  does not exist within that specific subject's scope.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        self.get_subject_by_id(subject_id)

        topic = self._get_topic_by_id(subject_id, topic_id)

        return topic

    def set_subject_status(
            self,
            subject_id: int,
            active: SubjectStatus
    ) -> Subject:
        """
        Updates the operational status (active/inactive) of a specific subject.

        This method acts as a global toggle for a subject's visibility. It
        leverages the centralized 'get_subject_by_id' guard to ensure existence
        before applying the new status and persisting the change.

        Args:
            subject_id (int): The unique identifier of the subject to modify.
            active (SubjectStatus): Schema containing the target boolean status.

        Returns:
            Subject: The updated Subject instance with the new status applied.

        Raises:
            HTTPException:
                - 404 (Not Found): If no subject exists with the given ID.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        try:
            subject = self.get_subject_by_id(subject_id)

            subject.is_active = active.is_active

            self._db.commit()
            self._db.refresh(subject)

            return subject

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.STATUS_UPDATE_ERROR} {str(error)}"
            ) from error

    def set_topic_status_from_subject(
            self,
            subject_id: int,
            topic_id: int,
            active: TopicStatus
    ) -> Topic:
        """
        Toggles the activation status of a specific topic within a subject's scope.

        This method implements a visibility toggle (soft-delete). It leverages
        'get_topic_from_subject' to strictly enforce the knowledge hierarchy
        before applying the status change and persisting the transaction.

        Args:
            subject_id (int): The unique identifier of the parent subject.
            topic_id (int): The unique identifier of the topic to modify.
            active (TopicStatus): Schema containing the target activation state.

        Returns:
            Topic: The updated Topic instance with the new status applied.

        Raises:
            HTTPException:
                - 404 (Not Found): If the subject does not exist OR the topic
                  does not exist within that subject.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        try:
            topic = self.get_topic_from_subject(subject_id, topic_id)

            topic.is_active = active.is_active

            self._db.commit()
            self._db.refresh(topic)

            return topic

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.STATUS_UPDATE_ERROR} {str(error)}"
            ) from error

    def update_subject(self, subject_id: int, subject_update: SubjectUpdate) -> Subject:
        """
        Updates the metadata of an existing subject.

        This method performs a partial update (PATCH-style). Only the fields
        explicitly provided in the SubjectUpdate schema are modified. It ensures
        uniqueness and integrity through the centralized 'get_subject_by_id' guard.

        Args:
            subject_id (int): The unique ID of the subject to update.
            subject_update (SubjectUpdate): Schema containing the fields to be changed.

        Returns:
            Subject: The updated and persisted subject instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If no subject exists with the given ID.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        subject = self.get_subject_by_id(subject_id)

        try:
            update_data = subject_update.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(subject, key, value)

            self._db.commit()
            self._db.refresh(subject)

            return subject

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.UPDATE_SUBJECT_ERROR} {str(error)}"
            ) from error

    def update_topic_from_subject(
            self,
            subject_id: int,
            topic_id: int,
            topic_update: TopicUpdate
    ) -> Topic:
        """
        Updates the metadata of an existing topic within a specific subject context.

        This method performs a partial update (PATCH-style). It ensures that only
        fields explicitly provided in the request are modified, while strictly
        enforcing the parent-child relationship between the subject and the topic.

        Args:
            subject_id (int): Unique ID of the parent subject.
            topic_id (int): Unique ID of the topic to be updated.
            topic_update (TopicUpdate): Schema containing the optional fields to change.

        Returns:
            Topic: The updated and persisted Topic instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If the subject doesn't exist or the topic
                  is not associated with it.
                - 500 (Internal Server Error): If a database transaction failure occurs.

        Note:
            Fields not explicitly set in the request are ignored during the
            update process (via 'exclude_unset=True').
        """
        topic = self.get_topic_from_subject(subject_id, topic_id)

        try:
            update_dict = topic_update.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(topic, key, value)

            self._db.commit()
            self._db.refresh(topic)

            return topic

        except SQLAlchemyError as error:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.UPDATE_TOPIC_ERROR} {str(error)}"
            ) from error

    def _get_subject_by_name(self, subject_name: str) -> Subject:
        """
        Internal helper to retrieve a subject by its name using a case-insensitive search.

        This method ensures the uniqueness of subjects within the knowledge hierarchy
        by performing normalized string comparisons (case-insensitive). It is
        primarily used for validation during creation or name-change operations.

        Args:
            subject_name (str): The plain-text name of the subject to find.

        Returns:
            Subject: The retrieved SQLAlchemy Subject instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If no subject with the given name exists.
                - 500 (Internal Server Error): If a database transaction failure occurs.

        Note:
            This is a low-level query method. It does not perform status checks
            (e.g., 'is_active').
        """
        try:
            stmt = (
                select(Subject)
                .where(func.lower(Subject.name) == func.lower(subject_name))
            )
            subject = self._db.execute(stmt).scalar_one_or_none()

            if not subject:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=KnowledgeMessages.SUBJECT_NOT_FOUND
                )
            return subject
        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.GET_SUBJECT_ERROR} {str(error)}"
            ) from error

    def _get_topic_by_id(self, subject_id: int, topic_id: int) -> Topic:
        """
        Internal helper to fetch a specific topic while verifying its parent subject.

        This method acts as a security and integrity layer. It enforces the
        hierarchical link by ensuring the topic not only exists but is also
        correctly mapped to the provided subject_id. This prevents cross-subject
        data leakage.

        Args:
            subject_id (int): The unique ID of the subject the topic must belong to.
            topic_id (int): The unique ID of the topic to retrieve.

        Returns:
            Topic: The validated Topic instance.

        Raises:
            HTTPException:
                - 404 (Not Found): If no topic matches the ID/subject_id combination.
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        try:
            stmt = select(Topic).where(
                Topic.id == topic_id,
                Topic.subject_id == subject_id
            )
            topic = self._db.execute(stmt).scalar_one_or_none()

            if not topic:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=KnowledgeMessages.TOPIC_NOT_FOUND
                )

            return topic

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.GET_TOPIC_ERROR} {str(error)}"
            ) from error

    def _is_subject_name_taken(self, subject_name: str) -> bool:
        """
        Checks if a subject name already exists in the database (case-insensitive).

        This is an internal validation helper used to prevent duplicate subject entries
        during creation or renaming processes.

        Args:
            subject_name (str): The name to check against existing records.

        Returns:
            bool: True if a subject with this name exists, False otherwise.

        Raises:
            HTTPException:
                - 500 (Internal Server Error): If a database transaction or
                  connection failure occurs during the query.
        """
        try:
            stmt = (select(Subject)
                    .where(func.lower(Subject.name) == func.lower(subject_name))
                    )
            result = self._db.execute(stmt).scalar_one_or_none()

            return result is not None

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.GET_SUBJECT_ERROR} {str(error)}"
            ) from error

    def _is_topic_name_taken_in_subject(self, topic_name: str, subject_id: int) -> bool:
        """
        Checks if a topic name already exists within a specific subject (case-insensitive).

        This internal helper ensures that there are no duplicate topic names under
        the same parent subject, maintaining a clear structure for the user.

        Args:
            topic_name (str): The name of the topic to check.
            subject_id (int): The ID of the parent subject to search within.

        Returns:
            bool: True if the name is already taken in this subject, False otherwise.

        Raises:
            HTTPException:
                - 500 (Internal Server Error): If a database transaction failure occurs.
        """
        try:
            stmt = (
                select(Topic)
                .where(
                    func.lower(Topic.name) == func.lower(topic_name),
                    Topic.subject_id == subject_id
                )
            )
            result = self._db.execute(stmt).scalar_one_or_none()

            return result is not None

        except SQLAlchemyError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{KnowledgeMessages.GET_TOPIC_ERROR} {str(error)}"
            ) from error
