from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.models.memory_entry import MemoryEntry
from app.schemas.rag import MemoryEntryResponse, MemorySearchRequest
from app.schemas.response import APIResponse
from app.services.memory_service import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("", response_model=APIResponse[List[MemoryEntryResponse]])
def list_memory_keys(
    memory_type: str = Query("long_term", description="session, long_term"),
    db: Session = Depends(get_db),
):
    """
    Lists memory entries filtered by type.
    """
    entries = db.query(MemoryEntry).filter(MemoryEntry.memory_type == memory_type).all()
    res = [MemoryEntryResponse.model_validate(e) for e in entries]
    return APIResponse(success=True, data=res)


@router.delete("", response_model=APIResponse[Dict[str, Any]])
def clear_memory_by_type(
    memory_type: str = Query("long_term", description="session, long_term")
):
    """
    Purges all memory records of the specified type.
    """
    store = memory_service.get_store()
    store.clear(memory_type)
    return APIResponse(
        success=True,
        data={"memory_type": memory_type},
        message=f"Memory category '{memory_type}' cleared successfully.",
    )


@router.post("/search", response_model=APIResponse[Optional[MemoryEntryResponse]])
def search_memory_key(payload: MemorySearchRequest, db: Session = Depends(get_db)):
    """
    Searches for a specific memory entry by key.
    """
    entry = (
        db.query(MemoryEntry)
        .filter(
            MemoryEntry.key == payload.key,
            MemoryEntry.memory_type == payload.memory_type,
        )
        .first()
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Memory key not found.")

    return APIResponse(success=True, data=MemoryEntryResponse.model_validate(entry))
