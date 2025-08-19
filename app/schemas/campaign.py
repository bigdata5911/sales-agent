from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class CampaignBase(BaseModel):
    """Base campaign schema"""
    name: str
    description: Optional[str] = None
    client_id: int
    message_templates: Optional[Dict[str, Any]] = {}
    is_active: bool = True

class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign"""
    pass

class CampaignUpdate(BaseModel):
    """Schema for updating a campaign"""
    name: Optional[str] = None
    description: Optional[str] = None
    message_templates: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class CampaignResponse(CampaignBase):
    """Schema for campaign response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CampaignList(BaseModel):
    """Schema for campaign list response"""
    id: int
    name: str
    description: Optional[str] = None
    client_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True 