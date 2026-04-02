from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import KnowledgeMessages
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.managers import KnowledgeManager
from apps.kyzo_backend.schemas import (SubjectCreate, SubjectRead, SubjectStatus, SubjectUpdate,
                                       TopicRead, TopicCreate, TopicStatus, TopicUpdate)

router = APIRouter(
    prefix="/api/knowledge",
    tags=["Knowledge"]
)


@router.post("/subjects/add", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
async def add_subject(subject_data: SubjectCreate, db: Session = Depends(get_db)):
    """
    Registers a new learning subject in the system.

    This endpoint serves as the entry point for the knowledge hierarchy.
    It ensures that each subject has a unique name (case-insensitive) to
    maintain a clean structure for subsequent topics and questions.

    Steps:
    1. Receives and validates the subject metadata.
    2. Checks for naming conflicts against existing subjects.
    3. Persists the subject and returns the full database record.

    Args:
        subject_data (SubjectCreate): The data required to create a subject
                                     (e.g., name, description).
        db (Session): Database session dependency.

    Returns:
        SubjectRead: The newly created subject including its generated ID.

    Raises:
        HTTPException (409): If a subject with the same name already exists.
        HTTPException (500): If an unexpected database error occurs during
                            persistence.
    """
    knowledge_manager = KnowledgeManager(db)

    success, result = knowledge_manager.add_subject(subject_data)
    if not success:
        if result == KnowledgeMessages.SUBJECT_ALREADY_EXISTS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )

    return result


@router.post("/subjects/{subject_id}/topics/add",
             response_model=TopicRead,
             status_code=status.HTTP_201_CREATED)
async def add_topic_to_subject(
        subject_id: int,
        topic_data: TopicCreate,
        db: Session = Depends(get_db)):
    """
    Creates and attaches a new learning topic to a specific subject.

    This endpoint ensures the structural integrity of the knowledge base by
    linking the new topic to the subject ID provided in the URL. It prevents
    naming collisions within the scope of the parent subject.

    Steps:
    1. Overrides any 'subject_id' in the request body with the ID from the URL.
    2. Verifies that the parent subject exists.
    3. Validates that the topic name is unique within this specific subject.
    4. Persists the topic and returns the enriched database record.

    Args:
        subject_id (int): The unique ID of the parent subject (from URL).
        topic_data (TopicCreate): The metadata for the new topic (from Body).
        db (Session): Database session dependency.

    Returns:
        TopicRead: The newly created topic object.

    Raises:
        HTTPException (404): If the parent subject does not exist.
        HTTPException (409): If a topic with this name already exists in this subject.
        HTTPException (500): If a database or persistence error occurs.
    """
    knowledge_manager = KnowledgeManager(db)

    topic_data.subject_id = subject_id
    success, result = knowledge_manager.add_topic_to_subject(topic_data)

    if not success:
        if result == KnowledgeMessages.SUBJECT_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result
            )
        if result == KnowledgeMessages.TOPIC_ALREADY_EXISTS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result)
        )

    return result


@router.get("/subjects/list-all", response_model=list[SubjectRead])
async def get_all_subjects(db: Session = Depends(get_db)):
    """
    Retrieves a comprehensive list of all subjects in the system.

    This endpoint is used to populate top-level navigation or dashboard
    views. It provides a full collection of subjects, including their
    current status and descriptions.

    Steps:
    1. Queries the database for all available subject records.
    2. Validates the integrity of the returned list.
    3. Triggers a 404 response if the system contains no subjects at all.

    Args:
        db (Session): Database session dependency.

    Returns:
        list[SubjectRead]: An array of all subject objects.

    Raises:
        HTTPException (404): If the database is empty (no subjects found).
        HTTPException (500): If a technical error occurs during data retrieval.
    """
    knowledge_manager = KnowledgeManager(db)

    success, result = knowledge_manager.get_all_subjects()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=KnowledgeMessages.NO_SUBJECTS
        )

    return result


@router.get("/subjects/{subject_id}/topics/list-all", response_model=list[TopicRead])
async def get_all_topics_from_subject(subject_id: int, db: Session = Depends(get_db)):
    """
    Retrieves all learning topics associated with a specific subject.

    This endpoint allows users to explore the sub-structure of a subject.
    It enforces strict hierarchical lookup to ensure the parent subject
    is valid before returning its topics.

    Steps:
    1. Validates the existence of the subject by its ID.
    2. Fetches all topics linked to this subject.
    3. Returns a 404 if either the subject is missing or it contains no topics.

    Args:
        subject_id (int): The unique ID of the subject to query.
        db (Session): Database session dependency.

    Returns:
        list[TopicRead]: A list of topic objects belonging to the subject.

    Raises:
        HTTPException (404):
            - If the subject ID does not exist.
            - If the subject exists but has no associated topics.
        HTTPException (500): If a database error occurs during retrieval.
    """
    knowledge_manager = KnowledgeManager(db)

    success, result_topics = knowledge_manager.get_all_topic_from_subject(subject_id)
    if not success:
        if result_topics == KnowledgeMessages.SUBJECT_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result_topics
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result_topics
        )

    if not result_topics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=KnowledgeMessages.NO_TOPICS_FOR_SUBJECTS
        )

    return result_topics


@router.get("/subjects/{subject_id}", response_model=SubjectRead)
async def get_subject(subject_id: int, db: Session = Depends(get_db)):
    """
    Retrieves detailed information for a specific subject by its unique ID.

    Workflow:
    1. Fetch the subject record from the KnowledgeManager.
    2. If success is False:
        a. Return 404 Not Found if the error matches SUBJECT_NOT_FOUND.
        b. Return 500 Internal Server Error for technical database failures.
    3. Return the subject record if found.

    Args:
        subject_id (int): The unique database identifier of the subject.
        db (Session): Database session dependency.

    Returns:
        SubjectRead: The full subject record.

    Raises:
        HTTPException: 404 if the subject does not exist.
        HTTPException: 500 if a database error occurs.
    """
    knowledge_manager = KnowledgeManager(db)

    success, result = knowledge_manager.get_subject_by_id(subject_id)

    if not success:
        if result == KnowledgeMessages.SUBJECT_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(result)
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result)
        )

    return result


@router.get("/subjects/{subject_id}/topics/{topic_id}", response_model=TopicRead)
async def get_topic_from_subject(subject_id: int, topic_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a specific topic associated with a particular subject.

    This endpoint performs a strict hierarchical lookup. It does not only
    check if the topic exists, but specifically verifies that it belongs
    to the indicated subject, preventing cross-subject data leakage.

    Process:
    1. Validates that the subject ID exists in the database.
    2. Verifies that the topic ID exists and is linked to the given subject.
    3. Returns the detailed topic record if both conditions are met.

    Args:
        subject_id (int): The ID of the parent subject.
        topic_id (int): The ID of the topic to retrieve.
        db (Session): Database session dependency.

    Returns:
        TopicRead: The requested topic object.

    Raises:
        HTTPException (404):
            - If the subject does not exist.
            - If the topic does not exist OR does not belong to the subject.
        HTTPException (500): If a database error occurs during the operation.
    """
    knowledge_manager = KnowledgeManager(db)

    success, result_topic = knowledge_manager.get_topic_from_subject(subject_id, topic_id)
    if not success:
        if result_topic in (
                KnowledgeMessages.SUBJECT_NOT_FOUND,
                KnowledgeMessages.TOPIC_NOT_FOUND):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result_topic
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result_topic
        )

    return result_topic


@router.put("/subjects/{subject_id}/status", response_model=SubjectRead)
async def set_subject_status(subject_id: int, active: SubjectStatus, db: Session = Depends(get_db)):
    """
    Updates the operational status (active/inactive) of a specific subject.

    This endpoint acts as a global switch for the subject. Inactivating a
    subject typically hides it from the end-user interface while
    preserving its data and hierarchy in the database.

    Process:
    1. Identifies the subject by its unique ID.
    2. Applies the new status provided in the request body.
    3. Persists the change and returns the updated subject record.

    Args:
        subject_id (int): The unique identifier of the subject to update.
        active (SubjectStatus): Schema containing the new boolean status.
        db (Session): Database session dependency.

    Returns:
        SubjectRead: The subject record with its newly applied status.

    Raises:
        HTTPException (404): If the subject ID does not exist.
        HTTPException (500): If a database error occurs during the update.
    """
    knowledge_manager = KnowledgeManager(db)

    success, result = knowledge_manager.set_subject_status(subject_id, active)

    if not success:
        if result == KnowledgeMessages.SUBJECT_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(result)
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result)
        )

    return result


@router.put("/subjects/{subject_id}/topics/{topic_id}", response_model=TopicRead)
async def set_topic_status_from_subject(
        subject_id: int,
        topic_id: int,
        active: TopicStatus,
        db: Session = Depends(get_db)):
    """
    Toggles the activation status of a specific topic within its parent subject.

    This endpoint allows administrative control over the visibility of a topic.
    It enforces the knowledge hierarchy by verifying that the topic is
    correctly linked to the provided subject before applying changes.

    Process:
    1. Validates the existence of the parent subject.
    2. Locates the specific topic and confirms its association with the subject.
    3. Updates the 'is_active' flag based on the provided payload.
    4. Returns the updated topic record.

    Args:
        subject_id (int): The ID of the subject owning the topic.
        topic_id (int): The ID of the topic to be toggled.
        active (TopicStatus): Schema containing the desired active state.
        db (Session): Database session dependency.

    Returns:
        TopicRead: The topic record with its updated status.

    Raises:
        HTTPException (404): If the subject or the topic (within that subject)
                            is not found.
        HTTPException (500): If an unexpected database error occurs.
    """
    knowledge_manager = KnowledgeManager(db)

    success, result_topic = knowledge_manager.set_topic_status_from_subject(
        subject_id,
        topic_id,
        active)
    if not success:
        if result_topic in (
                KnowledgeMessages.SUBJECT_NOT_FOUND,
                KnowledgeMessages.TOPIC_NOT_FOUND):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result_topic
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result_topic
        )

    return result_topic



@router.put("/subjects/{subject_id}/edit", response_model=SubjectRead)
async def update_subject(
        subject_id: int,
        subject_data: SubjectUpdate,
        db: Session = Depends(get_db)):
    """
    Modifies the core metadata of an existing subject.

    This endpoint is used for administrative corrections or updates to a
    subject's name and description. It ensures that the updated data
    complies with the system's naming conventions and uniqueness rules.

    Process:
    1. Locates the subject by its unique database identifier.
    2. Validates the incoming 'SubjectUpdate' payload against business rules.
    3. Performs a partial or full update of the allowed fields.
    4. Commits changes to the database and returns the refreshed record.

    Args:
        subject_id (int): The unique ID of the subject to be modified.
        subject_data (SubjectUpdate): The data to be updated (e.g., name, description).
        db (Session): Database session dependency.

    Returns:
        SubjectRead: The updated subject record.

    Raises:
        HTTPException (400): If the update data is invalid or violates constraints
                            (e.g., renaming to an already existing subject name).
        HTTPException (404): If the subject ID does not exist in the system.
    """
    knowledge_manager = KnowledgeManager(db)

    success, result = knowledge_manager.update_subject(subject_id, subject_data)
    if not success:
        if result == KnowledgeMessages.SUBJECT_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

    return result


@router.put("/subjects/{subject_id}/topics/{topic_id}/edit", response_model=TopicRead)
async def update_topic_from_subject(
        subject_id: int,
        topic_id: int,
        topic_data: TopicUpdate,
        db: Session = Depends(get_db)):
    """
    Modifies the metadata of a specific topic within a parent subject.

    This endpoint handles updates to topic names or descriptions while
    strictly enforcing the knowledge hierarchy. It ensures that the
    requested topic actually belongs to the specified subject before
    applying any changes.

    Process:
    1. Verifies the existence of the parent subject.
    2. Confirms that the topic ID is valid and linked to the subject.
    3. Validates the 'TopicUpdate' payload for naming conflicts or constraints.
    4. Applies changes and returns the fully updated topic record.

    Args:
        subject_id (int): The unique ID of the parent subject.
        topic_id (int): The unique ID of the topic to be modified.
        topic_data (TopicUpdate): The new metadata for the topic.
        db (Session): Database session dependency.

    Returns:
        TopicRead: The updated topic record.

    Raises:
        HTTPException (404): If either the subject or the topic (within
                            that subject's scope) is not found.
        HTTPException (500): If a database or internal server error occurs
                            during the update process.
    """
    knowledge_manager = KnowledgeManager(db)
    success, result_topic = knowledge_manager.update_topic_from_subject(
        subject_id,
        topic_id,
        topic_data
    )
    if not success:
        if result_topic in (
                KnowledgeMessages.SUBJECT_NOT_FOUND,
                KnowledgeMessages.TOPIC_NOT_FOUND):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result_topic
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result_topic
        )

    return result_topic
