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


    def add_subject(self, subject_data: SubjectCreate) -> tuple[bool, Subject | str]:
        """
            Persists a new academic subject in the database after validation.

            This method performs a two-step process:
            1. It checks if a subject with the same name already exists (case-insensitive)
                to prevent duplicates.
            2. If unique, it creates a new Subject record and commits it to the database.

            Args:
                subject_data (SubjectCreate): A validated Pydantic schema containing
                                             the new subject's attributes (e.g., name).

            Returns:
                tuple[bool, Subject | str]:
                    - If successful: (True, Subject-instance) - The newly created object.
                    - If name exists: (False, KnowledgeMessages.SUBJECT_ALREADY_EXISTS)
                    - If DB error: (False, Error message string)

            Raises:
                Note: Internal SQLAlchemyErrors are caught and returned as a boolean/string tuple
                      to allow the API layer to handle the response gracefully.
            """
        try:
            success, result_subject = self._get_subject_by_name(subject_data.name)
            if not success:
                return False, result_subject

            if result_subject is not None:
                return False, KnowledgeMessages.SUBJECT_ALREADY_EXISTS

            subject_dict = subject_data.model_dump()
            new_subject = Subject(**subject_dict)

            self._db.add(new_subject)
            self._db.commit()
            self._db.refresh(new_subject)
            return True, new_subject

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{KnowledgeMessages.CREATE_SUBJECT_ERROR} {str(error)}"


    def add_topic_to_subject(self, topic_data: TopicCreate) -> tuple[bool, Topic | str]:
        """
        Creates and attaches a new learning topic to an existing subject.

        Workflow:
        1. Validate Subject: Ensures the parent subject exists via get_subject_by_id.
        2. Duplicate Check: Ensures the topic name is unique within this subject.
        3. Persistence: Maps the schema to a Topic model and commits to DB.

        Args:
            topic_data (TopicCreate): Validated data for the new topic.

        Returns:
            tuple[bool, Topic | str]:
                - (True, Topic): The newly created topic instance.
                - (False, str): Error if subject missing, topic exists, or DB failure.
        """
        try:
            success_subject, result_subject = self.get_subject_by_id(topic_data.subject_id)
            if not success_subject:
                return False, result_subject

            success_topic, result_topic = self._get_topic_by_name(
                topic_data.subject_id,
                topic_data.name
            )

            if success_topic:
                return False, KnowledgeMessages.TOPIC_ALREADY_EXISTS

            if not success_topic and result_topic != KnowledgeMessages.TOPIC_NOT_FOUND:
                return False, result_topic

            topic_dict = topic_data.model_dump()
            new_topic = Topic(**topic_dict)

            self._db.add(new_topic)
            self._db.commit()
            self._db.refresh(new_topic)
            return True, new_topic

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{KnowledgeMessages.CREATE_TOPIC_ERROR}: {str(error)}"


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


    def get_all_topic_from_subject(self, subject_id: int) -> tuple[bool, list[Topic] | str]:
        """
        Fetches all topics associated with a specific subject ID.

        This method acts as a filtered getter. It first ensures the parent subject
        exists to provide accurate feedback (distinguishing between 'subject not
        found' and 'subject has no topics').

        Steps:
        1. Verifies the existence of the subject by its ID.
        2. Executes a filtered select statement on the Topic table using a
           foreign key constraint (subject_id).
        3. Returns the result as a list of Topic model instances.

        Args:
            subject_id (int): The unique identifier of the parent subject.

        Returns:
            tuple[bool, list[Topic] | str]:
                - If successful: (True, [Topic, ...]) - Note: Can be an empty list
                  if the subject exists but has no topics assigned yet.
                - If subject missing: (False, KnowledgeMessages.SUBJECT_NOT_FOUND)
                - If DB error: (False, Error message string)
        """
        try:
            success, result_subject = self.get_subject_by_id(subject_id)
            if not success:
                return False, result_subject

            stmt = select(Topic).where(Topic.subject_id == subject_id)
            all_topics = self._db.execute(stmt).scalars().all()

            return True, list(all_topics)
        except SQLAlchemyError as error:
            return False, f"{KnowledgeMessages.GET_ALL_TOPICS_FROM_SUBJECT_ERROR}: {str(error)}"


    def get_subject_by_id(self, subject_id: int) -> tuple[bool, Subject | str]:
        """
        Fetches a single subject by its unique database ID.

        Workflow:
        1. Execute a SELECT statement with a filter on the primary key.
        2. Use scalar_one_or_none to ensure a unique result or a safe None.
        3. Return False if the subject is missing to trigger error handling in managers.

        Args:
            subject_id (int): The primary key of the subject to retrieve.

        Returns:
            tuple[bool, Subject | str]:
                - (True, Subject): If the subject was found successfully.
                - (False, str): If the subject is missing (SUBJECT_NOT_FOUND)
                                or a database error occurred.
        """
        try:
            stmt = select(Subject).where(Subject.id == subject_id)
            subject = self._db.execute(stmt).scalar_one_or_none()

            if not subject:
                return False, KnowledgeMessages.SUBJECT_NOT_FOUND

            return True, subject

        except SQLAlchemyError as error:
            return False, f"{KnowledgeMessages.GET_SUBJECT_ERROR}: {str(error)}"


    def get_topic_from_subject(self, subject_id: int, topic_id: int) \
            -> tuple[bool, Topic | None | str]:
        """
        Verifies the existence of a specific topic within the context of a subject.

        This is a core validation method used to ensure logical hierarchy and
        data integrity. It prevents "orphan" access by checking the parent
        subject first, followed by the specific topic associated with that subject.

        Validation Chain:
        1. Subject Existence: Confirms the 'subject_id' exists in the database.
        2. Topic-Subject Bond: Confirms the 'topic_id' exists and is correctly
           mapped to the provided 'subject_id' (handled by _get_topic_by_id).

        Args:
            subject_id (int): The unique ID of the parent subject.
            topic_id (int): The unique ID of the topic to retrieve.

        Returns:
            tuple[bool, Topic | None | str]:
                - If found: (True, Topic-instance)
                - If subject missing: (False, KnowledgeMessages.SUBJECT_NOT_FOUND)
                - If topic missing/mismatched: (False, KnowledgeMessages.TOPIC_NOT_FOUND)
                - If DB error: (False, Error message string)
        """
        success, result_subject = self.get_subject_by_id(subject_id)

        if not success:
            return False, result_subject

        success, result_topic = self._get_topic_by_id(subject_id, topic_id)

        if not success:
            return False, result_topic

        return True, result_topic

    def set_subject_status(
            self,
            subject_id: int,
            active: SubjectStatus
    ) -> tuple[bool, Subject | str]:
        """
        Updates the activation status of a specific subject.

        Workflow:
        1. Fetch Subject: Uses get_subject_by_id (returns False if missing).
        2. Guard: If success is False, return the error immediately.
        3. Update: Apply the 'is_active' flag from the SubjectStatus schema.
        4. Persistence: Commit the change and refresh the instance.

        Args:
            subject_id (int): The unique ID of the subject to modify.
            active (SubjectStatus): A schema containing the new boolean status.

        Returns:
            tuple[bool, Subject | str]:
                - (True, Subject): If the status was successfully updated.
                - (False, str): If the subject doesn't exist or a DB error occurred.
        """
        try:
            success, result = self.get_subject_by_id(subject_id)

            if not success:
                return False, result

            result.is_active = active.is_active

            self._db.commit()
            self._db.refresh(result)

            return True, result

        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{KnowledgeMessages.STATUS_UPDATE_ERROR}: {str(error)}"


    def set_topic_status_from_subject(self, subject_id: int, topic_id: int, active: TopicStatus) \
            -> tuple[bool, Topic | str]:
        """
        Toggles the activation status of a specific topic within a subject.

        This method implements a soft-delete mechanism. Deactivating a topic
        makes it (and potentially its associated questions) unavailable for
        active learning sessions while preserving the data for historical
        records and analytics.

        Steps:
        1. Hierarchy Check: Uses 'get_topic_from_subject' to ensure the topic
           exists and belongs to the specified subject.
        2. State Mutation: Updates the 'is_active' flag based on the input schema.
        3. Persistence: Commits the change and refreshes the object to ensure
           consistency with the database state.

        Args:
            subject_id (int): The unique ID of the parent subject.
            topic_id (int): The unique ID of the topic to modify.
            active (TopicStatus): A validated Pydantic schema containing the
                                 new 'is_active' boolean value.

        Returns:
            tuple[bool, Topic | str]:
                - If updated: (True, Topic-instance)
                - If hierarchy fails: (False, KnowledgeMessages.SUBJECT_NOT_FOUND
                  or TOPIC_NOT_FOUND)
                - If DB error: (False, Error message string)
        """
        try:
            success, result_topic = self.get_topic_from_subject(subject_id, topic_id)

            if not success:
                return False, result_topic

            result_topic.is_active = active.is_active
            self._db.commit()
            self._db.refresh(result_topic)
            return True, result_topic
        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{KnowledgeMessages.STATUS_UPDATE_ERROR} {error}"


    def update_subject(self, subject_id: int, subject_update: SubjectUpdate) \
            -> tuple[bool, Subject | None | str]:
        """
        Updates the metadata of an existing subject.

        This method performs a partial update (PATCH-style). Only the fields
        provided in the SubjectUpdate schema are modified in the database.
        It uses dynamic attribute setting to ensure scalability as more
        subject attributes are added.

        Workflow:
        1. Fetch Subject: Uses get_subject_by_id (returns False if missing).
        2. Guard: If success is False, return the error immediately (Not Found or DB error).
        3. Partial Update: Iterates over fields provided in the update schema.
        4. Persistence: Commits changes and refreshes the instance.

        Args:
            subject_id (int): The unique ID of the subject to update.
            subject_update (SubjectUpdate): A schema with optional fields to be changed.

        Returns:
            tuple[bool, Subject | str]:
                - (True, Subject): The updated subject instance.
                - (False, str): Error message if subject missing or DB failure occurs.
        """
        try:
            success_subject, result_subject = self.get_subject_by_id(subject_id)

            if not success_subject:
                return False, result_subject

            update_dict = subject_update.model_dump(exclude_unset=True)

            for key, value in update_dict.items():
                setattr(result_subject, key, value)

            self._db.commit()
            self._db.refresh(result_subject)

            return True, result_subject

        except SQLAlchemyError as error:
            self._db.rollback()
            return  False, f"{KnowledgeMessages.UPDATE_SUBJECT_ERROR} {str(error)}"


    def update_topic_from_subject(self, subject_id: int, topic_id: int, topic_update: TopicUpdate) \
            -> tuple[bool, Topic | str]:
        """
        Updates the metadata of an existing topic within a specific subject context.

        This method performs a partial update (PATCH-style). Only the fields
        explicitly provided in the TopicUpdate schema will be modified,
        preserving all other existing attributes.

        Steps:
        1. Authorization & Hierarchy: Calls 'get_topic_from_subject' to verify
           the topic belongs to the parent subject.
        2. Dynamic Mapping: Iterates through the provided update fields and
           applies them to the database model instance.
        3. State Persistence: Commits changes to the database and refreshes
           the instance to reflect the updated state.

        Args:
            subject_id (int): ID of the subject the topic belongs to.
            topic_id (int): ID of the topic to be updated.
            topic_update (TopicUpdate): A schema containing the fields to change
                                       (e.g., name, description).

        Returns:
            tuple[bool, Topic | str]:
                - If updated: (True, Updated Topic-instance)
                - If validation fails: (False, KnowledgeMessages.SUBJECT_NOT_FOUND
                  or TOPIC_NOT_FOUND)
                - If DB error: (False, Error message string)

        Note:
            Fields that are 'None' in the schema but not explicitly 'set' in the
            request are ignored thanks to 'exclude_unset=True'.
        """
        try:
            success, result_topic = self.get_topic_from_subject(subject_id, topic_id)

            if not success:
                return False, result_topic

            update_dict = topic_update.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(result_topic, key, value)

            self._db.commit()
            self._db.refresh(result_topic)
            return True, result_topic
        except SQLAlchemyError as error:
            self._db.rollback()
            return False, f"{KnowledgeMessages.UPDATE_TOPIC_ERROR} {error}"

    def _get_subject_by_name(self, subject_name: str) -> tuple[bool, Subject | None | str]:
        """
        Internal helper to retrieve a subject by its name using a case-insensitive search.

        This method is a critical component for ensuring the uniqueness of subjects
        at the top level of the knowledge hierarchy. It prevents the creation of
        redundant subject entries (e.g., 'Mathematics' vs 'mathematics').

        Logic:
            - Utilizes 'func.lower' to normalize both the database field and the
              input string for a reliable comparison.
            - Returns a single record or None if no match is found.

        Args:
            subject_name (str): The plain-text name of the subject to find.

        Returns:
            tuple[bool, Subject | None | str]:
                - If found: (True, Subject-instance)
                - If not found: (True, None)
                - If DB error: (False, Error message string)

        Note:
            This is a low-level query method. It does not perform any business
            validation or status checks (is_active).
        """
        try:
            stmt = (
                select(Subject)
                .where(func.lower(Subject.name) == func.lower(subject_name))
            )
            subject = self._db.execute(stmt).scalar_one_or_none()

            return True, subject
        except SQLAlchemyError as error:
            return False, f"{KnowledgeMessages.GET_SUBJECT_ERROR} {str(error)}"


    def _get_topic_by_id(self, subject_id: int, topic_id: int) -> tuple[bool, Topic | str]:
        """
        Internal helper to fetch a specific topic while verifying its parent subject.

        This method acts as a security and integrity layer. Instead of just
        looking up a topic by its primary key, it enforces the hierarchical
        link to the subject. This prevents "cross-subject" access where a
        valid topic ID is combined with a mismatched subject ID.

        Query Logic:
            SELECT * FROM topics
            WHERE id = :topic_id AND subject_id = :subject_id;

        Args:
            subject_id (int): The unique ID of the subject the topic must belong to.
            topic_id (int): The unique ID of the topic to retrieve.

        Returns:
            tuple[bool, Topic | str]:
                - (True, Topic): If the topic exists and belongs to the subject.
                - (False, str): If no match is found (TOPIC_NOT_FOUND) or a
                                database error occurs.
        """
        try:
            stmt = select(Topic).where(
                Topic.id == topic_id,
                Topic.subject_id == subject_id
            )
            topic = self._db.execute(stmt).scalar_one_or_none()

            if not topic:
                return False, KnowledgeMessages.TOPIC_NOT_FOUND

            return True, topic
        except SQLAlchemyError as error:
            return False, f"{KnowledgeMessages.GET_TOPIC_FROM_SUBJECT_ERROR} {error}"


    def _get_topic_by_name(self, subject_id: int, topic_name: str) \
            -> tuple[bool, Topic | None | str]:
        """
        Internal helper to locate a topic by its name within a specific subject context.

        This method is primarily used for duplicate prevention. It performs a
        case-insensitive search to ensure that topic names remain unique
        within each subject, while allowing the same topic name to exist
        across different subjects.

        Logic:
            - Filters by 'subject_id' to isolate the search scope.
            - Uses 'func.lower' for a case-insensitive name comparison.

        Args:
            subject_id (int): The ID of the subject to search within.
            topic_name (str): The name of the topic to look for.

        Returns:
            tuple[bool, Topic | None | str]:
                - If found: (True, Topic-instance)
                - If not found: (True, None)
                - If DB error: (False, Error message string)

        Note:
            This method does not check if the subject itself exists; it only
            queries the Topic table based on the provided IDs.
        """
        try:
            stmt = (
                select(Topic)
                .where(Topic.subject_id == subject_id)
                .where(func.lower(Topic.name) == func.lower(topic_name))
            )
            topic = self._db.execute(stmt).scalar_one_or_none()
            return True, topic
        except SQLAlchemyError as error:
            return False, f"{KnowledgeMessages.GET_TOPIC_ERROR} {str(error)}"
