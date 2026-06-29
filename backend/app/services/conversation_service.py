from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.memory_service import memory_service
from app.core.logging.logger import logger

class ConversationService:
    """
    Service responsible for creating conversation threads, logging messages,
    reconstructing history (injecting summaries), and triggering compression.
    """
    
    def create_conversation(
        self, 
        db: Session, 
        session_id: str, 
        title: str = "New Conversation", 
        user_id: Optional[int] = None
    ) -> Conversation:
        """
        Creates a new conversation thread record, or returns an existing one if session_id matches.
        """
        existing = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if existing:
            return existing

        conv = Conversation(
            session_id=session_id,
            user_id=user_id,
            title=title
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        logger.info(f"Created conversation thread: {title} (ID: {conv.id}, Session: {session_id})")
        return conv

    def add_message(
        self, 
        db: Session, 
        session_id: str, 
        role: str, 
        content: str
    ) -> Message:
        """
        Logs a dialogue message turn in the conversation session, calculating tokens
        and triggering compression constraints.
        """
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if not conv:
            conv = self.create_conversation(db, session_id)

        # Simple token estimation
        token_count = len(content.split()) if content else 0

        msg = Message(
            conversation_id=conv.id,
            role=role,
            content=content,
            token_count=token_count
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        # Trigger memory compression check after logging the message
        memory_service.compress_conversation_if_needed(db, conv.id)

        return msg

    def get_history(self, db: Session, session_id: str) -> List[Dict[str, str]]:
        """
        Reconstructs the conversation context. Prepends the conversation summary
        (if available) followed by remaining message history logs.
        """
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if not conv:
            return []

        history = []
        
        # 1. Prepend conversation summary context if present
        if conv.summary:
            history.append({
                "role": "system",
                "content": f"The following is a summary of the older conversation history: {conv.summary}"
            })

        # 2. Append remaining active message logs
        messages = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.timestamp.asc()).all()
        for m in messages:
            history.append({
                "role": m.role,
                "content": m.content
            })

        return history

    def delete_conversation(self, db: Session, conversation_id: int) -> bool:
        """
        Deletes a conversation node, purging messages via DB cascades.
        """
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return False
        db.delete(conv)
        db.commit()
        return True

# Global ConversationService instance
conversation_service = ConversationService()
