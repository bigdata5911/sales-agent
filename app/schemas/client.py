from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class ClientBase(BaseModel):
    """Base client schema"""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {}

class ClientCreate(ClientBase):
    """Schema for creating a new client"""
    pass

class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class ClientResponse(ClientBase):
    """Schema for client response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ClientList(BaseModel):
    """Schema for client list response"""
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 