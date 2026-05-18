"""
API router for knowledge-base management, defining structure and validation for subjects and topics.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.api.depends.role_depends import (
    require_teacher_or_admin,
    require_student_teacher_or_admin
)
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.data import User
from apps.kyzo_backend.managers import KnowledgeManager
from apps.kyzo_backend.schemas import (
    SubjectCreate,
    SubjectRead,
    SubjectStatus,
    SubjectUpdate,
    TopicRead,
    TopicCreate,
    TopicStatus,
    TopicUpdate
)

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge"]
)


def get_knowledge_manager(db: Session = Depends(get_db)) -> KnowledgeManager:
    """
    Dependency provider for the KnowledgeManager.

    This function facilitates the injection of a KnowledgeManager instance into
    API routes. It handles the lifecycle of the manager by providing it with
    the necessary SQLAlchemy database session.

    Args:
        db (Session): The SQLAlchemy database session injected via get_db.

    Returns:
        KnowledgeManager: An initialized instance for handling knowledge-base logic.
    """
    return KnowledgeManager(db)


@router.post("/subjects/add", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
async def add_subject(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        subject_data: SubjectCreate,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """
    Registers a new learning subject in the system.

    This endpoint serves as the root for the knowledge hierarchy. It delegates
    validation and persistence to the KnowledgeManager, ensuring that subject
    names remain unique and the database integrity is maintained.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        subject_data (SubjectCreate): Pydantic container for the validated
            data of the new subject.
        knowledge_manager (KnowledgeManager): Injected manager instance for
            knowledge-base operations.

    Returns:
        SubjectRead: The newly created subject record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 409 (Conflict): If a subject with the same name already exists.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return knowledge_manager.add_subject(subject_data)


@router.post("/subjects/{subject_id}/topics/add",
             response_model=TopicRead,
             status_code=status.HTTP_201_CREATED)
async def add_topic_to_subject(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        subject_id: int,
        topic_data: TopicCreate,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """
    Creates and attaches a new learning topic to a specific subject.

    This endpoint maintains the structural integrity of the knowledge base by
    linking the new topic to a validated parent subject. It ensures that
    topic names are unique within the scope of the parent subject to prevent
    redundancy.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        subject_id (int): The unique database identifier of the parent subject.
        topic_data (TopicCreate): Pydantic container for the metadata of the
            new topic.
        knowledge_manager (KnowledgeManager): Injected manager instance for
            knowledge-base operations.

    Returns:
        TopicRead: The newly created and persisted topic record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If the parent subject_id does not exist.
            - 409 (Conflict): If a topic with this name already exists within the subject.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    topic_data.subject_id = subject_id
    return knowledge_manager.add_topic_to_subject(topic_data)


@router.get("/subjects/list-all", response_model=list[SubjectRead])
async def get_all_subjects(
        _current_user: Annotated[User, Depends(require_student_teacher_or_admin)],
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """
    Retrieves a comprehensive list of all subjects in the system.

    This endpoint provides a full collection of subjects, including their
    metadata and status. It is typically used for populating top-level
    navigation, dropdowns, or dashboard overviews.

    Args:
        _current_user (User): The authenticated user record, used strictly to
            verify that the requester holds a valid application role.
        knowledge_manager (KnowledgeManager): Injected manager instance for
            knowledge-base operations.

    Returns:
        list[SubjectRead]: A list of all available subject records.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but does not match
              any recognized system roles.
            - 404 (Not Found): If no subjects exist in the database.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Authorized roles: STUDENT, TEACHER, ADMIN
    """
    return knowledge_manager.get_all_subjects()


@router.get("/subjects/{subject_id}/topics/list-all", response_model=list[TopicRead])
async def get_all_topics_from_subject(
        _current_user: Annotated[User, Depends(require_student_teacher_or_admin)],
        subject_id: int,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """
    Retrieves all learning topics associated with a specific subject.

    This endpoint facilitates the exploration of a subject's sub-structure.
    It enforces a hierarchical lookup, ensuring that the parent subject
    exists before attempting to retrieve its topics.

    Args:
        _current_user (User): The authenticated user record, used strictly to
            verify that the requester holds a valid application role.
        subject_id (int): The unique database identifier of the parent subject.
        knowledge_manager (KnowledgeManager): Injected manager instance for
            knowledge-base operations.

    Returns:
        list[TopicRead]: A list of topic records belonging to the specified subject.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but does not match
              any recognized system roles.
            - 404 (Not Found): If the subject ID does not exist OR if the
              subject exists but contains no topics.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Authorized roles: STUDENT, TEACHER, ADMIN
    """
    return knowledge_manager.get_all_topic_from_subject(subject_id)


@router.get("/subjects/{subject_id}", response_model=SubjectRead)
async def get_subject(
        _current_user: Annotated[User, Depends(require_student_teacher_or_admin)],
        subject_id: int,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """
    Retrieves detailed information for a specific subject by its unique ID.

    This endpoint delegates the lookup logic to the KnowledgeManager. It
    ensures that the requested subject exists before returning its metadata.
    Validation and error handling are encapsulated within the manager.

    Args:
        _current_user (User): The authenticated user record, used strictly to
            verify that the requester holds a valid application role.
        subject_id (int): The unique database identifier of the subject.
        knowledge_manager (KnowledgeManager): Injected manager instance for
            knowledge-base operations.

    Returns:
        SubjectRead: The full subject record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but does not match
              any recognized system roles.
            - 404 (Not Found): If no subject exists with the given ID.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Authorized roles: STUDENT, TEACHER, ADMIN
    """
    return knowledge_manager.get_subject_by_id(subject_id)


@router.get("/subjects/{subject_id}/topics/{topic_id}", response_model=TopicRead)
async def get_topic_from_subject(
        _current_user: Annotated[User, Depends(require_student_teacher_or_admin)],
        subject_id: int,
        topic_id: int,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """
    Retrieves a specific topic associated with a particular subject.

    This endpoint enforces a strict hierarchical lookup. Beyond mere existence,
    it verifies the ownership of the topic by the parent subject to maintain
    data integrity and prevent cross-subject access.

    Args:
        _current_user (User): The authenticated user record, used strictly to
            verify that the requester holds a valid application role.
        subject_id (int): The unique database identifier of the parent subject.
        topic_id (int): The unique database identifier of the target topic.
        knowledge_manager (KnowledgeManager): Injected manager instance for
            knowledge-base operations.

    Returns:
        TopicRead: The requested topic record if the hierarchy is valid.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but does not match
              any recognized system roles.
            - 404 (Not Found): If the subject does not exist, or if the topic
              does not exist or does not belong to the specified subject.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Authorized roles: STUDENT, TEACHER, ADMIN
    """
    return knowledge_manager.get_topic_from_subject(subject_id, topic_id)


@router.put("/subjects/{subject_id}/status", response_model=SubjectRead)
async def set_subject_status(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        subject_id: int,
        active: SubjectStatus,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """
    Updates the operational status (active/inactive) of a specific subject.

    This endpoint serves as a visibility toggle. Inactivating a subject
    typically hides it and its associated topics from the user interface
    while preserving the underlying data hierarchy for administrative purposes.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        subject_id (int): The unique database identifier of the subject to update.
        active (SubjectStatus): Pydantic enum or container containing the target status.
        knowledge_manager (KnowledgeManager): Injected manager instance for
            knowledge-base operations.

    Returns:
        SubjectRead: The subject record with the updated status applied.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If no subject exists with the given ID.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return knowledge_manager.set_subject_status(subject_id, active)


@router.put("/subjects/{subject_id}/topics/{topic_id}", response_model=TopicRead)
async def set_topic_status_from_subject(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        subject_id: int,
        topic_id: int,
        active: TopicStatus,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """
    Toggles the activation status of a specific topic within its parent subject.

    This endpoint provides administrative control over a topic's visibility.
    It enforces the knowledge hierarchy by verifying that the topic is
    correctly linked to the provided subject before applying the status change,
    preventing unauthorized cross-subject modifications.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        subject_id (int): The unique database identifier of the parent subject.
        topic_id (int): The unique database identifier of the target topic.
        active (TopicStatus): Pydantic enum or container containing the target
            activation state.
        knowledge_manager (KnowledgeManager): Injected manager instance for
            knowledge-base operations.

    Returns:
        TopicRead: The topic record reflecting its updated status.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If the subject does not exist, or if the topic
              does not exist or does not belong to that subject.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return knowledge_manager.set_topic_status_from_subject(
        subject_id,
        topic_id,
        active
    )


@router.put("/subjects/{subject_id}/edit", response_model=SubjectRead)
async def update_subject(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        subject_id: int,
        subject_data: SubjectUpdate,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """
    Modifies the core metadata of an existing subject.

    This endpoint performs a partial update of a subject's information. It
    ensures that any changes to the subject name remain unique across the
    system and that all metadata complies with internal naming conventions.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        subject_id (int): The unique database identifier of the subject to be modified.
        subject_data (SubjectUpdate): Pydantic container for the fields to be updated.
        knowledge_manager (KnowledgeManager): Injected manager instance for
            knowledge-base operations.

    Returns:
        SubjectRead: The updated and persisted subject record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If no subject exists with the given ID.
            - 409 (Conflict): If the requested new name is already taken by
              another subject.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return knowledge_manager.update_subject(subject_id, subject_data)


@router.put("/subjects/{subject_id}/topics/{topic_id}/edit", response_model=TopicRead)
async def update_topic_from_subject(
        _current_user: Annotated[User, Depends(require_teacher_or_admin)],
        subject_id: int,
        topic_id: int,
        topic_data: TopicUpdate,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """
    Modifies the metadata of a specific topic within a parent subject.

    This endpoint performs a partial update of a topic's information while
    strictly enforcing the knowledge hierarchy. It ensures ownership by the
    parent subject and prevents naming collisions within that subject's scope.

    Args:
        _current_user (User): The authenticated teacher's or administrator's user
            record, used strictly to enforce role-based access control.
        subject_id (int): The unique database identifier of the parent subject.
        topic_id (int): The unique database identifier of the topic to be modified.
        topic_data (TopicUpdate): Pydantic container for the fields to be updated.
        knowledge_manager (KnowledgeManager): Injected manager instance for
            knowledge-base operations.

    Returns:
        TopicRead: The updated and persisted topic record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
            - 404 (Not Found): If the subject does not exist, or if the topic
              does not exist or does not belong to that subject.
            - 409 (Conflict): If the new topic name already exists within this subject.
            - 500 (Internal Server Error): If a database transaction failure occurs.

    Security:
        - Bearer Auth (JWT)
        - Restricted to: TEACHER or ADMIN roles
    """
    return knowledge_manager.update_topic_from_subject(
        subject_id,
        topic_id,
        topic_data
    )
