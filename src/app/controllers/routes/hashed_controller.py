__all__ = ["router"]
"""
@file hashed_controller.py
@author naflashDev
@brief FastAPI router for hash operations.
@details Exposes endpoints for hashing and unhashing phrases using supported algorithms.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal
from app.models.db import get_db
from app.services.hashed.hash_service import HashService
from app.services.hashed.hash_repository import HashAlgorithm
from sqlalchemy.orm import Session

class HashRequest(BaseModel):
    phrase: str = Field(..., description="Phrase to hash")
    algorithm: Literal["MD5", "SHA256", "SHA512"] = Field(..., description="Hash algorithm")

class UnhashRequest(BaseModel):
    hashed_value: str = Field(..., description="Hash to search")
    algorithm: Literal["MD5", "SHA256", "SHA512"] = Field(..., description="Hash algorithm")

class HashResponse(BaseModel):
    hashed_value: str

class UnhashResponse(BaseModel):
    original_value: str

router = APIRouter(prefix="/hashed", tags=["Hashed"])

@router.post("/hash", response_model=HashResponse)
def hash_phrase(request: HashRequest, db: Session = Depends(get_db)):
    '''
    @brief Endpoint to hash a phrase.
    '''
    service = HashService(db)
    try:
        hashed = service.hash_phrase(request.phrase, HashAlgorithm(request.algorithm))
        return {"hashed_value": hashed}
    except Exception as e:
        # Generic error message for UI, no internal details
        raise HTTPException(status_code=400, detail="Ha ocurrido un error interno. Por favor, contacte con el administrador.")

@router.post("/unhash", response_model=UnhashResponse)
def unhash_phrase(request: UnhashRequest, db: Session = Depends(get_db)):
    '''
    @brief Endpoint to retrieve original phrase from hash.
    '''
    service = HashService(db)
    original = service.unhash(request.hashed_value, HashAlgorithm(request.algorithm))
    if original is None:
        raise HTTPException(status_code=404, detail="Hash no encontrado.")
    return {"original_value": original}
