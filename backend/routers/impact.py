import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
from schemas import ImpactResponse, ImpactLogRequest, Badge, ImpactActivityResponse
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
    # ── Karma Badges ──────────────────────────────────────────────────────────
    {
        "name": "Good Samaritan",
        "icon": "🤝",
        "description": "Earned 50 Karma points by helping neighbors",
        "min_karma": 50,
    },
    {
        "name": "Neighborhood Hero",
        "icon": "⭐",
        "description": "Earned 200 Karma points — a pillar of the community",
        "min_karma": 200,
    },
    {
        "name": "Karma Legend",
        "icon": "🔥",
        "description": "Earned 500 Karma points — legendary status!",
        "min_karma": 500,
    },
]

# Karma points awarded per action
KARMA_RULES = {
    "task_posted": 5,       # Posting a help request
    "task_completed": 20,   # Owner marks task done
    "helped": 30,           # Confirmed helper on a completed task
    "verified": 10,         # Verifying a post in VerifyCenter
    "activity": 15,         # Manual activity log
}


def compute_rank(hours: float, activities: int, karma: int = 0) -> tuple[str, str]:
    if karma >= 500 or hours >= 100 or activities >= 20:
        return "Karma Legend 🔥", "Legend status — you're an inspiration!"
    elif karma >= 200 or hours >= 50 or activities >= 10:
        return "Chennai Guardian 🦁", f"{max(0, 500-karma)} karma to reach Karma Legend"
    elif karma >= 50 or hours >= 20 or activities >= 5:
        return "Community Champion 🏆", f"{max(0, 200-karma)} karma to reach Chennai Guardian"
    elif hours >= 5 or activities >= 2:
        return "Community Seed 🌱", f"{max(0, 50-karma)} karma to earn Good Samaritan badge"
    else:
        return "First Responder 🚑", "Help someone in your neighborhood to earn your first karma!"


def _build_response(record: models.UserImpact, db: Session) -> ImpactResponse:
    user = db.query(models.User).filter_by(id=record.user_id).first()
    hours = record.hours_volunteered
    activities = record.activities_count
    verifications = record.verifications_count
    karma = record.karma or 0
    rank, next_milestone = compute_rank(hours, activities, karma)
    category_stats = record.category_stats or "{}"

    badges = []
    for cfg in BADGES_CONFIG:
        earned = (
            activities >= cfg.get("min_activities", 9999)
            or hours >= cfg.get("min_hours", 9999)
            or verifications >= cfg.get("min_verifications", 9999)
            or karma >= cfg.get("min_karma", 9999)
        )
        badges.append(Badge(
            name=cfg["name"],
            icon=cfg["icon"],
            description=cfg["description"],
            earned=earned,
        ))

    return ImpactResponse(
        user_id=record.user_id,
        full_name=user.full_name if user else "Neighbor",
        hours_volunteered=hours,
        activities_count=activities,
        verifications_count=verifications,
        karma=karma,
        badges=badges,
        rank=rank,
        next_milestone=next_milestone,
        category_stats=category_stats,
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


def award_karma(user_id: int, action: str, db: Session, category: str = None, hours: float = 0.0):
    """
    Award karma points AND update aggregate impact stats/history automatically.
    This ensures P2P actions (helped) reflected on the Impact Page.
    """
    pts = KARMA_RULES.get(action, 0)
    if pts == 0 and action != "helped": # 'helped' might have 0 pts in some rules but still counts as activity
        return
        
    record = _get_or_create(user_id, db)
    
    # 1. Update Karma Points
    record.karma = (record.karma or 0) + pts
    
    # 2. Update Aggregate Stats for specific actions
    if action == "helped":
        record.activities_count += 1
        record.hours_volunteered = round(record.hours_volunteered + max(0.0, hours), 1)
    elif action == "verified":
        record.verifications_count += 1

    # 3. Track specialized expertise
    if category:
        try:
            stats = json.loads(record.category_stats or "{}")
            stats[category] = stats.get(category, 0) + 1
            record.category_stats = json.dumps(stats)
        except Exception as e:
            print(f"[Impact] Error updating category stats: {e}")
            
    # 4. Create Activity History Record
    if action in ["helped", "verified", "activity"]:
        new_act = models.ImpactActivity(
            user_id=user_id,
            type="activity" if action in ["helped", "activity"] else "verification",
            category=category or "General",
            hours=hours if action in ["helped", "activity"] else 0.0,
            image_url=None # Images usually come from manual logs, not auto-P2P for now
        )
        db.add(new_act)

    db.commit()


@router.get("/me", response_model=ImpactResponse)
def get_my_impact(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = _get_or_create(current_user.id, db)
    return _build_response(record, db)


@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    """Return top 20 users sorted by karma."""
    records = (
        db.query(models.UserImpact, models.User)
        .join(models.User, models.UserImpact.user_id == models.User.id)
        .order_by(models.UserImpact.karma.desc())
        .limit(20)
        .all()
    )
    result = []
    for i, (impact, user) in enumerate(records):
        result.append({
            "rank": i + 1,
            "user_id": user.id,
            "full_name": user.full_name or "Neighbor",
            "karma": impact.karma or 0,
            "activities_count": impact.activities_count,
            "hours_volunteered": impact.hours_volunteered,
            "rank_title": compute_rank(impact.hours_volunteered, impact.activities_count, impact.karma or 0)[0],
        })
    return result


@router.get("/history", response_model=list[ImpactActivityResponse])
def get_my_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch the authenticated user's impact history."""
    return (
        db.query(models.ImpactActivity)
        .filter_by(user_id=current_user.id)
        .order_by(models.ImpactActivity.created_at.desc())
        .all()
    )


@router.get("/history/{user_id}", response_model=list[ImpactActivityResponse])
def get_user_history(user_id: int, db: Session = Depends(get_db)):
    """Fetch history for any user (public)."""
    return (
        db.query(models.ImpactActivity)
        .filter_by(user_id=user_id)
        .order_by(models.ImpactActivity.created_at.desc())
        .all()
    )


@router.get("/{user_id}", response_model=ImpactResponse)
def get_impact(user_id: int, db: Session = Depends(get_db)):
    record = _get_or_create(user_id, db)
    return _build_response(record, db)


@router.post("/log", response_model=ImpactResponse)
def log_my_impact(
    payload: ImpactLogRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return log_impact(current_user.id, payload, db)


def log_impact(user_id: int, payload: ImpactLogRequest, db: Session):
    """
    Increment aggregate stats AND create a detailed ImpactActivity record.
    """
    record = _get_or_create(user_id, db)

    # 1. Update Aggregate Record
    if payload.type == "activity":
        record.activities_count += 1
        record.hours_volunteered = round(record.hours_volunteered + max(0.0, payload.hours), 1)
        award_karma(user_id, "activity", db, payload.category)
    elif payload.type == "verification":
        record.verifications_count += 1
        award_karma(user_id, "verified", db, payload.category)

    # 2. Create Detailed Activity Record (Proof of Impact)
    new_activity = models.ImpactActivity(
        user_id=user_id,
        type=payload.type,
        category=payload.category,
        hours=payload.hours if payload.type == "activity" else 0.0,
        image_url=payload.image_url
    )
    db.add(new_activity)

    db.commit()
    db.refresh(record)
    return _build_response(record, db)


