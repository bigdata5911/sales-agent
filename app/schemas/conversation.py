from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ConversationBase(BaseModel):
    """Base conversation schema"""
    content: str
    direction: str  # inbound, outbound
    metadata: Optional[Dict[str, Any]] = {}

class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation"""
    pass

class ConversationResponse(ConversationBase):
    """Schema for conversation response"""
    id: int
    lead_id: int
    message_id: Optional[str] = None
    sent_at: datetime
    
    class Config:
        from_attributes = True

class ConversationList(BaseModel):
    """Schema for conversation list response"""
    id: int
    lead_id: int
    direction: str
    content: str
    sent_at: datetime
    
    class Config:
        from_attributes = True 