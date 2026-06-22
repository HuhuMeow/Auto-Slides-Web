from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.llm.router import list_model_options
from backend.schemas import ModelOption, UserOut
from backend.security import get_current_user

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=list[ModelOption])
def get_models(_user: UserOut = Depends(get_current_user)):
    return list_model_options()
