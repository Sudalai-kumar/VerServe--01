from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    ngo_name = Column(String(255), nullable=False)
    location = Column(String(255), default="Chennai")
    lat = Column(Float, default=13.0827)
    lng = Column(Float, default=80.2707)
    trust_score = Column(Integer, default=50)
    status = Column(String(50), default="needs_review")  # verified | needs_review | flagged
    trust_reasoning = Column(Text, nullable=True)  # Detailed reason from AI or rules
    category = Column(String(100), default="General")
    contact = Column(String(255), nullable=True)
    source = Column(String(50), default="manual")  # rss | social | manual
    source_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NGO(Base):
    __tablename__ = "ngos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), default="General")
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    address = Column(String(500), nullable=True)
    verified = Column(Boolean, default=True)
    logo_emoji = Column(String(10), default="🏢")
    founded_year = Column(Integer, nullable=True)
    volunteers_count = Column(Integer, default=0)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_ngo_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    impact = relationship("UserImpact", back_populates="user", uselist=False)


class UserImpact(Base):
    __tablename__ = "user_impact"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    hours_volunteered = Column(Float, default=0.0)
    activities_count = Column(Integer, default=0)
    verifications_count = Column(Integer, default=0)
    badges = Column(Text, default="[]")  # JSON array of badge names

    user = relationship("User", back_populates="impact")
