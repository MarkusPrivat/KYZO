from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.managers import KnowledgeManager
from apps.kyzo_backend.schemas import (SubjectCreate, SubjectRead, SubjectStatus, SubjectUpdate,
                                       TopicRead, TopicCreate, TopicStatus, TopicUpdate)

router = APIRouter(
    prefix="/api/knowledge",
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
        subject_data: SubjectCreate,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)):
    """
    Registers a new learning subject in the system.

    This endpoint serves as the root for the knowledge hierarchy. It delegates
    validation and persistence to the KnowledgeManager, ensuring that subject
    names remain unique and the database integrity is maintained.

    Args:
        subject_data (SubjectCreate): The validated data for the new subject.
        knowledge_manager (KnowledgeManager): Injected manager for knowledge-base logic.

    Returns:
        SubjectRead: The newly created subject record.

    Raises:
        HTTPException:
            - 404 (Not Found): Optional, if a parent resource is missing (if applicable).
            - 409 (Conflict): If a subject with the same name already exists.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return knowledge_manager.add_subject(subject_data)


@router.post("/subjects/{subject_id}/topics/add",
             response_model=TopicRead,
             status_code=status.HTTP_201_CREATED)
async def add_topic_to_subject(
        subject_id: int,
        topic_data: TopicCreate,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)):
    """
    Creates and attaches a new learning topic to a specific subject.

    This endpoint maintains the structural integrity of the knowledge base by
    linking the new topic to a validated parent subject. It ensures that
    topic names are unique within the scope of the parent subject to prevent
    redundancy.

    Args:
        subject_id (int): The unique identifier of the parent subject.
        topic_data (TopicCreate): The metadata for the new topic.
        knowledge_manager (KnowledgeManager): Injected manager for knowledge-base logic.

    Returns:
        TopicRead: The newly created and persisted topic record.

    Raises:
        HTTPException:
            - 404 (Not Found): If the parent subject_id does not exist.
            - 409 (Conflict): If a topic with this name already exists within the subject.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    topic_data.subject_id = subject_id
    return knowledge_manager.add_topic_to_subject(topic_data)


@router.get("/subjects/list-all", response_model=list[SubjectRead])
async def get_all_subjects(
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)):
    """
    Retrieves a comprehensive list of all subjects in the system.

    This endpoint provides a full collection of subjects, including their
    metadata and status. It is typically used for populating top-level
    navigation, dropdowns, or dashboard overviews.

    Args:
        knowledge_manager (KnowledgeManager): Injected manager for knowledge-base logic.

    Returns:
        list[SubjectRead]: A list of all available subject records.

    Raises:
        HTTPException:
            - 404 (Not Found): If no subjects exist in the database.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return knowledge_manager.get_all_subjects()


@router.get("/subjects/{subject_id}/topics/list-all", response_model=list[TopicRead])
async def get_all_topics_from_subject(
        subject_id: int,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)):
    """
    Retrieves all learning topics associated with a specific subject.

    This endpoint facilitates the exploration of a subject's sub-structure.
    It enforces a hierarchical lookup, ensuring that the parent subject
    exists before attempting to retrieve its topics.

    Args:
        subject_id (int): The unique identifier of the parent subject.
        knowledge_manager (KnowledgeManager): Injected manager for knowledge-base logic.

    Returns:
        list[TopicRead]: A list of topic records belonging to the specified subject.

    Raises:
        HTTPException:
            - 404 (Not Found): If the subject ID does not exist OR if the
              subject exists but contains no topics.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return knowledge_manager.get_all_topic_from_subject(subject_id)


@router.get("/subjects/{subject_id}", response_model=SubjectRead)
async def get_subject(
        subject_id: int,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)):
    """
    Retrieves detailed information for a specific subject by its unique ID.

    This endpoint delegates the lookup logic to the KnowledgeManager. It
    ensures that the requested subject exists before returning its metadata.
    Validation and error handling are encapsulated within the manager.

    Args:
        subject_id (int): The unique database identifier of the subject.
        knowledge_manager (KnowledgeManager): Injected manager for knowledge-base logic.

    Returns:
        SubjectRead: The full subject record.

    Raises:
        HTTPException:
            - 404 (Not Found): If no subject exists with the given ID.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return knowledge_manager.get_subject_by_id(subject_id)


@router.get("/subjects/{subject_id}/topics/{topic_id}", response_model=TopicRead)
async def get_topic_from_subject(
        subject_id: int,
        topic_id: int,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)):
    """
    Retrieves a specific topic associated with a particular subject.

    This endpoint enforces a strict hierarchical lookup. Beyond mere existence,
    it verifies the ownership of the topic by the parent subject to maintain
    data integrity and prevent cross-subject access.

    Args:
        subject_id (int): The unique identifier of the parent subject.
        topic_id (int): The unique identifier of the topic to retrieve.
        knowledge_manager (KnowledgeManager): Injected manager for knowledge-base logic.

    Returns:
        TopicRead: The requested topic record if the hierarchy is valid.

    Raises:
        HTTPException:
            - 404 (Not Found): If the subject does not exist, or if the topic
              does not exist/does not belong to the specified subject.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return knowledge_manager.get_topic_from_subject(subject_id, topic_id)


@router.put("/subjects/{subject_id}/status", response_model=SubjectRead)
async def set_subject_status(
        subject_id: int,
        active: SubjectStatus,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)):
    """
    Updates the operational status (active/inactive) of a specific subject.

    This endpoint serves as a visibility toggle. Inactivating a subject
    typically hides it and its associated topics from the user interface
    while preserving the underlying data hierarchy for administrative purposes.

    Args:
        subject_id (int): The unique identifier of the subject to update.
        active (SubjectStatus): Schema containing the target status.
        knowledge_manager (KnowledgeManager): Injected manager for knowledge-base logic.

    Returns:
        SubjectRead: The subject record with the updated status applied.

    Raises:
        HTTPException:
            - 404 (Not Found): If no subject exists with the given ID.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return knowledge_manager.set_subject_status(subject_id, active)


@router.put("/subjects/{subject_id}/topics/{topic_id}", response_model=TopicRead)
async def set_topic_status_from_subject(
        subject_id: int,
        topic_id: int,
        active: TopicStatus,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)):
    """
    Toggles the activation status of a specific topic within its parent subject.

    This endpoint provides administrative control over a topic's visibility.
    It enforces the knowledge hierarchy by verifying that the topic is
    correctly linked to the provided subject before applying the status change,
    preventing unauthorized cross-subject modifications.

    Args:
        subject_id (int): The unique identifier of the parent subject.
        topic_id (int): The unique identifier of the topic to be updated.
        active (TopicStatus): Schema containing the target activation state.
        knowledge_manager (KnowledgeManager): Injected manager for knowledge-base logic.

    Returns:
        TopicRead: The topic record with its updated status.

    Raises:
        HTTPException:
            - 404 (Not Found): If the subject does not exist, or if the topic
              does not exist/belong to that subject.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return knowledge_manager.set_topic_status_from_subject(
        subject_id,
        topic_id,
        active
    )


@router.put("/subjects/{subject_id}/edit", response_model=SubjectRead)
async def update_subject(
        subject_id: int,
        subject_data: SubjectUpdate,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)):
    """
    Modifies the core metadata of an existing subject.

    This endpoint performs a partial update of a subject's information. It
    ensures that any changes to the subject name remain unique across the
    system and that all metadata complies with internal naming conventions.

    Args:
        subject_id (int): The unique ID of the subject to be modified.
        subject_data (SubjectUpdate): Container for the fields to be updated.
        knowledge_manager (KnowledgeManager): Injected manager for knowledge-base logic.

    Returns:
        SubjectRead: The updated and persisted subject record.

    Raises:
        HTTPException:
            - 404 (Not Found): If no subject exists with the given ID.
            - 409 (Conflict): If the requested new name is already taken by
              another subject.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return knowledge_manager.update_subject(subject_id, subject_data)


@router.put("/subjects/{subject_id}/topics/{topic_id}/edit", response_model=TopicRead)
async def update_topic_from_subject(
        subject_id: int,
        topic_id: int,
        topic_data: TopicUpdate,
        knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)):
    """
    Modifies the metadata of a specific topic within a parent subject.

    This endpoint performs a partial update of a topic's information while
    strictly enforcing the knowledge hierarchy. It ensures ownership by the
    parent subject and prevents naming collisions within that subject's scope.

    Args:
        subject_id (int): The unique identifier of the parent subject.
        topic_id (int): The unique identifier of the topic to be modified.
        topic_data (TopicUpdate): Container for the fields to be updated.
        knowledge_manager (KnowledgeManager): Injected manager for knowledge-base logic.

    Returns:
        TopicRead: The updated and persisted topic record.

    Raises:
        HTTPException:
            - 404 (Not Found): If the subject does not exist, or if the topic
              does not exist/belong to that subject.
            - 409 (Conflict): If the new topic name already exists within this subject.
            - 500 (Internal Server Error): If a database transaction failure occurs.
    """
    return knowledge_manager.update_topic_from_subject(
        subject_id,
        topic_id,
        topic_data
    )
