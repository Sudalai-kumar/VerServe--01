from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── User & Auth Schemas ──────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


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
    full_name: Optional[str] = None
    hours_volunteered: float
    activities_count: int
    verifications_count: int
    karma: int
    badges: List[Badge]
    rank: str
    next_milestone: str
    category_stats: str = "{}"


# ── Verify Action ────────────────────────────────────────────────────────────

class VerifyAction(BaseModel):
    action: str  # "confirm" or "flag"


# ── Impact Log ────────────────────────────────────────────────────────────────

class ImpactLogRequest(BaseModel):
    type: str          # "activity" or "verification"
    hours: float = 0.0 # only used for type="activity"
    category: Optional[str] = "General"
    image_url: Optional[str] = None


# ── Chat Schemas ─────────────────────────────────────────────────────────────

class ChatMessageResponse(BaseModel):
    id: int
    request_id: int
    user_id: int
    content: str
    created_at: datetime
    full_name: Optional[str] = None # For displaying sender name

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    content: str


# ── HelpRequest Schemas ──────────────────────────────────────────────────────

class HelpRequestBase(BaseModel):
    title: str
    description: str
    image_url: Optional[str] = None
    location_name: Optional[str] = "Chennai"
    lat: float
    lng: float
    people_needed: int = 1
    category: Optional[str] = "General"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class HelpRequestCreate(HelpRequestBase):
    pass


class HelperUserResponse(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: str # Or just a truncated email/name for privacy until accepted

class ApplicationResponse(BaseModel):
    user: HelperUserResponse
    status: str

    class Config:
        from_attributes = True

class HelpRequestResponse(HelpRequestBase):
    id: int
    user_id: int
    owner_name: Optional[str] = "Neighbor"
    owner_karma: int = 0
    status: str
    created_at: datetime
    helper_count: int = 0
    is_joined: bool = False
    join_status: Optional[str] = None # requested | confirmed
    trust_score: int = 50
    trust_reasoning: Optional[str] = None
    applications: List[ApplicationResponse] = [] # Only returned if current_user is owner
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True


class ImpactActivityResponse(BaseModel):
    id: int
    type: str
    category: str
    hours: float
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
