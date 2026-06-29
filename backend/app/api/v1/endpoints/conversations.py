from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.rag import ConversationCreate, ConversationResponse, MessageResponse
from app.schemas.response import APIResponse
from app.services.conversation_service import conversation_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=APIResponse[ConversationResponse])
def create_new_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    """
    Creates a new conversation session.
    """
    conv = conversation_service.create_conversation(
        db=db,
        session_id=payload.session_id,
        title=payload.title,
        user_id=payload.user_id,
    )
    return APIResponse(success=True, data=ConversationResponse.model_validate(conv))


@router.get("", response_model=APIResponse[List[ConversationResponse]])
def list_conversations(
    user_id: Optional[int] = Query(None, description="Filter by owner user ID"),
    db: Session = Depends(get_db),
):
    """
    Lists metadata for active conversation threads.
    """
    query = db.query(Conversation)
    if user_id is not None:
        query = query.filter(Conversation.user_id == user_id)

    convs = query.all()
    res = [ConversationResponse.model_validate(c) for c in convs]
    return APIResponse(success=True, data=res)


@router.get("/{id}", response_model=APIResponse[ConversationResponse])
def get_conversation_details(id: int, db: Session = Depends(get_db)):
    """
    Retrieves metadata of a specific conversation thread.
    """
    conv = db.query(Conversation).filter(Conversation.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return APIResponse(success=True, data=ConversationResponse.model_validate(conv))


@router.delete("/{id}", response_model=APIResponse[Dict[str, Any]])
def delete_conversation_thread(id: int, db: Session = Depends(get_db)):
    """
    Purges conversation thread, cascading deletion of associated messages.
    """
    success = conversation_service.delete_conversation(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return APIResponse(
        success=True, data={"id": id}, message="Conversation thread deleted."
    )


@router.get("/{id}/messages", response_model=APIResponse[List[MessageResponse]])
def get_conversation_messages_log(id: int, db: Session = Depends(get_db)):
    """
    Returns dialogue turn logs for a conversation thread.
    """
    conv = db.query(Conversation).filter(Conversation.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    res = [MessageResponse.model_validate(m) for m in messages]
    return APIResponse(success=True, data=res)
