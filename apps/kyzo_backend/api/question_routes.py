from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import QuestionMessages
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.managers import QuestionManager
from apps.kyzo_backend.schemas import QuestionCreate, QuestionRead, QuestionStatus, QuestionUpdate

router = APIRouter(
    prefix="/api/questions",
    tags=["Questions"]
)

@router.post("/add", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
async def add_question():
    pass