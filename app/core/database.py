from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import json

from app.core.config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

class Client(Base):
    """Client/Company model"""
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50))
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="client")
    
    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}')>"

class Campaign(Base):
    """Campaign model"""
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    message_templates = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="campaigns")
    leads = relationship("Lead", back_populates="campaign")
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', client_id={self.client_id})>"

class Lead(Base):
    """Lead model"""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255))
    lead_data = Column(JSON, default={})  # Original form data
    status = Column(String(50), default="new")  # new, contacted, responded, converted, lost
    lead_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="leads")
    conversations = relationship("Conversation", back_populates="lead")
    analytics = relationship("Analytics", back_populates="lead")
    
    def __repr__(self):
        return f"<Lead(id={self.id}, name='{self.name}', phone='{self.phone}')>"

class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    message_id = Column(String(255), unique=True)  # Twilio message ID
    direction = Column(String(20), nullable=False)  # inbound, outbound
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default={})  # Additional message data
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, direction='{self.direction}', lead_id={self.lead_id})>"

class Analytics(Base):
    """Analytics model"""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    event_type = Column(String(100), nullable=False)  # message_sent, message_received, conversion, etc.
    event_data = Column(JSON, default={})
    event_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="analytics")
    
    def __repr__(self):
        return f"<Analytics(id={self.id}, event_type='{self.event_type}', lead_id={self.lead_id})>"

# Database dependency
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 