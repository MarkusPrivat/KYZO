from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.kyzo_backend.config import TestMessages
from apps.kyzo_backend.core import get_db
from apps.kyzo_backend.managers import TestManager
from apps.kyzo_backend.schemas import (TestRead)


router = APIRouter(
    prefix="/api/test/",
    tags=["Test"]
)

