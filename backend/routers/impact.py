import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
from schemas import ImpactResponse, ImpactLogRequest, Badge
from routers.auth import get_current_user

router = APIRouter(prefix="/impact", tags=["impact"])

BADGES_CONFIG = [
    {
        "name": "First Responder",
        "icon": "🚑",
        "description": "Responded to your first emergency volunteering call",
        "min_activities": 1,
    },
    {
        "name": "Community Seed",
        "icon": "🌱",
        "description": "Completed 5 volunteering activities",
        "min_activities": 5,
    },
    {
        "name": "Trust Guardian",
        "icon": "🛡️",
        "description": "Verified 10 community posts in the Verify Center",
        "min_verifications": 10,
    },
    {
        "name": "Green Hero",
        "icon": "🌿",
        "description": "Participated in 3 environmental volunteering events",
        "min_activities": 3,
    },
    {
        "name": "Community Champion",
        "icon": "🏆",
        "description": "Amassed 50+ hours of volunteer service",
        "min_hours": 50,
    },
    {
        "name": "Chennai Guardian",
        "icon": "🦁",
        "description": "Completed 20 volunteering activities — a true protector of Chennai!",
        "min_activities": 20,
    },
]


def compute_rank(hours: float, activities: int) -> tuple[str, str]:
    if hours >= 100 or activities >= 20:
        return "Chennai Guardian 🦁", "Legend status — you're an inspiration!"
    elif hours >= 50 or activities >= 10:
        return "Community Champion 🏆", f"{max(0, 100-int(hours))} more hours to reach Chennai Guardian"
    elif hours >= 20 or activities >= 5:
        return "Green Hero 🌿", f"{max(0, 50-int(hours))} more hours to reach Community Champion"
    elif hours >= 5 or activities >= 2:
        return "Community Seed 🌱", f"{max(0, 20-int(hours))} more hours to reach Green Hero"
    else:
        return "First Responder 🚑", f"{max(0, 5-int(hours))} more hours to reach Community Seed"


def _build_response(record: models.UserImpact) -> ImpactResponse:
    hours = record.hours_volunteered
    activities = record.activities_count
    verifications = record.verifications_count
    rank, next_milestone = compute_rank(hours, activities)

    badges = []
    for cfg in BADGES_CONFIG:
        earned = (
            activities >= cfg.get("min_activities", 9999)
            or hours >= cfg.get("min_hours", 9999)
            or verifications >= cfg.get("min_verifications", 9999)
        )
        badges.append(Badge(
            name=cfg["name"],
            icon=cfg["icon"],
            description=cfg["description"],
            earned=earned,
        ))

    return ImpactResponse(
        user_id=record.user_id,
        hours_volunteered=hours,
        activities_count=activities,
        verifications_count=verifications,
        badges=badges,
        rank=rank,
        next_milestone=next_milestone,
    )


def _get_or_create(user_id: int, db: Session) -> models.UserImpact:
    """Return the UserImpact row, creating it with zeroed stats if it doesn't exist."""
    record = db.query(models.UserImpact).filter_by(user_id=user_id).first()
    if not record:
        record = models.UserImpact(user_id=user_id)
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


@router.get("/me", response_model=ImpactResponse)
def get_my_impact(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = _get_or_create(current_user.id, db)
    return _build_response(record)


@router.get("/{user_id}", response_model=ImpactResponse)
def get_impact(user_id: int, db: Session = Depends(get_db)):
    record = _get_or_create(user_id, db)
    return _build_response(record)


@router.post("/log", response_model=ImpactResponse)
def log_my_impact(
    payload: ImpactLogRequest, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return log_impact(current_user.id, payload, db)


def log_impact(user_id: int, payload: ImpactLogRequest, db: Session):
    """
    Increment the user's impact stats.
    - type="activity"     → activities_count += 1, hours_volunteered += hours
    - type="verification" → verifications_count += 1
    """
    record = _get_or_create(user_id, db)

    if payload.type == "activity":
        record.activities_count += 1
        record.hours_volunteered = round(record.hours_volunteered + max(0.0, payload.hours), 1)
    elif payload.type == "verification":
        record.verifications_count += 1

    db.commit()
    db.refresh(record)
    return _build_response(record)
