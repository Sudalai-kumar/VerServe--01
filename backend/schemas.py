from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Opportunity Schemas ──────────────────────────────────────────────────────

class OpportunityBase(BaseModel):
    title: str
    description: str
    ngo_name: str
    location: Optional[str] = "Chennai"
    lat: Optional[float] = 13.0827
    lng: Optional[float] = 80.2707
    category: Optional[str] = "General"
    contact: Optional[str] = None
    source: Optional[str] = "manual"
    source_url: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityResponse(OpportunityBase):
    id: int
    trust_score: int
    status: str
    trust_reasoning: Optional[str] = None
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── NGO Schemas ──────────────────────────────────────────────────────────────

class NGOBase(BaseModel):
    name: str
    description: str
    category: Optional[str] = "General"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    logo_emoji: Optional[str] = "🏢"
    founded_year: Optional[int] = None
    volunteers_count: Optional[int] = 0


class NGOResponse(NGOBase):
    id: int
    verified: bool

    class Config:
        from_attributes = True


# ── User & Auth Schemas ──────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    is_ngo_admin: Optional[bool] = False


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# ── Impact Schemas ───────────────────────────────────────────────────────────

class Badge(BaseModel):
    name: str
    icon: str
    description: str
    earned: bool


class ImpactResponse(BaseModel):
    user_id: int
    hours_volunteered: float
    activities_count: int
    verifications_count: int
    badges: List[Badge]
    rank: str
    next_milestone: str


# ── Verify Action ────────────────────────────────────────────────────────────

class VerifyAction(BaseModel):
    action: str  # "confirm" or "flag"


# ── Impact Log ────────────────────────────────────────────────────────────────

class ImpactLogRequest(BaseModel):
    type: str          # "activity" or "verification"
    hours: float = 0.0 # only used for type="activity"
