from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import KnowledgeMessages
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.managers import KnowledgeManager
from apps.kyzo_backend.schemas import SubjectCreate, SubjectRead, SubjectStatus, SubjectUpdate

router = APIRouter(
    prefix="/api/knowledge",
    tags=["Knowledge"]
)


@router.post("/subjects/add", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
async def add_subject(subject_data: SubjectCreate, db: Session = Depends(get_db)):
    """
    add new subject
    """
    knowledge_manger = KnowledgeManager(db)

    success, result = knowledge_manger.add_subject(subject_data)
    if not success:
        if result == KnowledgeMessages.SUBJECT_ALREADY_EXISTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )

    return result


@router.get("/subjects/list-all", response_model=list[SubjectRead])
async def get_all_subjects(db: Session = Depends(get_db)):
    """
    Get all subjects
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


@router.get("/subjects/{subject_id}", response_model=SubjectRead)
async def get_subject(subject_id: int, db: Session = Depends(get_db)):
    """
    Get Subject by id
    """
    knowledge_manager = KnowledgeManager(db)

    success, result = knowledge_manager.get_subject_by_id(subject_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=KnowledgeMessages.SUBJECT_NOT_FOUND
        )

    return result


@router.put("/subjects/{subject_id}/status", response_model=SubjectRead)
async def set_subject_status(subject_id: int, active: SubjectStatus, db: Session = Depends(get_db)):
    """
    change subject status
    """
    knowledge_manager = KnowledgeManager(db)

    success, result = knowledge_manager.set_subject_status(subject_id, active)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=KnowledgeMessages.SUBJECT_NOT_FOUND
        )

    return result


@router.put("/subjects/{subject_id}/edit", response_model=SubjectRead)
async def update_subject(
        subject_id: int,
        subject_data: SubjectUpdate,
        db: Session = Depends(get_db)):
    """
    update subject
    """
    knowledge_manager = KnowledgeManager(db)

    success, result = knowledge_manager.update_subject(subject_id, subject_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=KnowledgeMessages.SUBJECT_NOT_FOUND
        )

    return result