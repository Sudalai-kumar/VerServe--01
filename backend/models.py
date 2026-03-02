from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Helper(Base):
    __tablename__ = "helpers"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    request_id = Column(Integer, ForeignKey("help_requests.id"), primary_key=True)
    status = Column(String(50), default="requested") # confirmed | requested
    
    # Relationships for easier access
    user = relationship("User", back_populates="help_applications")
    request = relationship("HelpRequest", back_populates="applications")

class HelpRequest(Base):
    __tablename__ = "help_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    location_name = Column(String(255), default="Chennai")
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    people_needed = Column(Integer, default=1)
    category = Column(String(100), default="General")
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="seeking")  # seeking | help_found | completed | expired
    trust_score = Column(Integer, default=50)
    trust_reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="my_requests", foreign_keys=[user_id])
    applications = relationship("Helper", back_populates="request", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="request", cascade="all, delete-orphan")



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    impact = relationship("UserImpact", back_populates="user", uselist=False)
    activities = relationship("ImpactActivity", back_populates="user")
    my_requests = relationship("HelpRequest", back_populates="owner", foreign_keys=[HelpRequest.user_id])
    help_applications = relationship("Helper", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user")


class UserImpact(Base):
    __tablename__ = "user_impact"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    hours_volunteered = Column(Float, default=0.0)
    activities_count = Column(Integer, default=0)
    verifications_count = Column(Integer, default=0)
    karma = Column(Integer, default=0)
    badges = Column(Text, default="[]")  # JSON array of badge names
    category_stats = Column(Text, default="{}")  # JSON mapping: {"Category": count}

    user = relationship("User", back_populates="impact")


class ImpactActivity(Base):
    __tablename__ = "impact_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50))  # activity | verification
    category = Column(String(100), default="General")
    hours = Column(Float, default=0.0)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activities")
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("help_requests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    request = relationship("HelpRequest", back_populates="messages")
    user = relationship("User", back_populates="chat_messages")
