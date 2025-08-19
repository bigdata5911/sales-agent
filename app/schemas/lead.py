from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class LeadBase(BaseModel):
    """Base lead schema"""
    name: str
    phone: str
    email: Optional[EmailStr] = None
    campaign_id: int
    lead_data: Optional[Dict[str, Any]] = {}

class LeadCreate(LeadBase):
    """Schema for creating a new lead"""
    pass

class LeadUpdate(BaseModel):
    """Schema for updating a lead"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[str] = None
    lead_score: Optional[int] = None
    lead_data: Optional[Dict[str, Any]] = None

class LeadResponse(LeadBase):
    """Schema for lead response"""
    id: int
    status: str
    lead_score: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LeadList(BaseModel):
    """Schema for lead list response"""
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    status: str
    lead_score: int
    campaign_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True 