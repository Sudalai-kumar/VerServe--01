from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas
import routers.auth as auth
from datetime import datetime
# Removed .impact import to avoid circularity

router = APIRouter(
    prefix="/requests",
    tags=["P2P Help Requests"]
)

@router.post("/", response_model=schemas.HelpRequestResponse)
def create_request(
    request: schemas.HelpRequestCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Integrate Scam Detection for P2P requests
    from services.trust.scam_detector import detect_scam
    
    # Get user's karma for trust calculation
    user_karma = current_user.impact.karma if current_user.impact else 0
    
    # Neighbor context for trust calculation
    score, status, _, reasoning = detect_scam(
        request.title, request.description, "Neighbor",
        "p2p", request.image_url, user_karma
    )
    
    new_request = models.HelpRequest(
        **request.dict(),
        user_id=current_user.id,
        trust_score=score,
        trust_reasoning=reasoning
    )
    db.add(new_request)
    
    # Award karma for posting - REMOVED for P2P (Reputation should be earned by helping others)
    # from .impact import award_karma
    # award_karma(current_user.id, "task_posted", db)
    
    db.commit()
    db.refresh(new_request)
    
    # Return consistent data structure
    data = {
        "id": new_request.id,
        "user_id": current_user.id,
        "owner_name": current_user.full_name or current_user.email.split('@')[0],
        "owner_karma": user_karma,
        "title": new_request.title,
        "description": new_request.description,
        "image_url": new_request.image_url,
        "location_name": new_request.location_name,
        "lat": new_request.lat,
        "lng": new_request.lng,
        "people_needed": new_request.people_needed,
        "category": new_request.category,
        "start_time": new_request.start_time,
        "end_time": new_request.end_time,
        "status": new_request.status,
        "created_at": new_request.created_at,
        "trust_score": new_request.trust_score,
        "trust_reasoning": new_request.trust_reasoning,
        "helper_count": 0,
        "is_joined": False,
        "join_status": None,
        "applications": [],
        "messages": []
    }
    return schemas.HelpRequestResponse(**data)

@router.get("/", response_model=List[schemas.HelpRequestResponse])
def get_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    print(f"[Requests] GET - user: {current_user.email}")
    # Get all non-completed requests
    requests = db.query(models.HelpRequest).filter(models.HelpRequest.status != "completed").all()
    
    result = []
    for r in requests:
        # Convert to dict first to avoid issues with extra fields during from_orm
        data = {
            "id": r.id,
            "user_id": r.user_id,
            "owner_name": r.owner.full_name or r.owner.email.split('@')[0],
            "owner_karma": r.owner.impact.karma if r.owner.impact else 0,
            "title": r.title,
            "description": r.description,
            "image_url": r.image_url,
            "location_name": r.location_name,
            "lat": r.lat,
            "lng": r.lng,
            "people_needed": r.people_needed,
            "category": r.category,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "status": r.status,
            "created_at": r.created_at,
            "trust_score": r.trust_score or 50,
            "trust_reasoning": r.trust_reasoning,
        }
        
        # Count only confirmed helpers
        confirmed = [a for a in r.applications if a.status == "confirmed"]
        data["helper_count"] = len(confirmed)
        
        # Check if current user has an application
        my_app = next((a for a in r.applications if a.user_id == current_user.id), None)
        data["is_joined"] = my_app is not None
        data["join_status"] = my_app.status if my_app else None
        
        # Only show all applications to the OWNER
        if r.user_id == current_user.id:
            data["applications"] = [
                {
                    "user": {
                        "id": a.user.id,
                        "full_name": a.user.full_name,
                        "email": a.user.email
                    },
                    "status": a.status
                } for a in r.applications
            ]
        else:
            data["applications"] = []
            
        result.append(schemas.HelpRequestResponse(**data))
    return result

@router.post("/{id}/join")
def join_request(
    id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(models.HelpRequest).filter_by(id=id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if req.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot join your own request")

    # Check for existing application
    existing = db.query(models.Helper).filter_by(request_id=id, user_id=current_user.id).first()
    if existing:
        return {"msg": "Already applied", "status": existing.status}
        
    new_app = models.Helper(user_id=current_user.id, request_id=id, status="requested")
    db.add(new_app)
    db.commit()
    return {"msg": "Help requested! Wait for owner to accept.", "status": "requested"}

@router.post("/{id}/accept/{user_id}")
def accept_helper(
    id: int,
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Verify ownership
    req = db.query(models.HelpRequest).filter_by(id=id, user_id=current_user.id).first()
    if not req:
        raise HTTPException(status_code=403, detail="Not the owner of this request")
    
    # Find application
    app = db.query(models.Helper).filter_by(request_id=id, user_id=user_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Helper application not found")
    
    app.status = "confirmed"
    
    # Check if we hit the limit
    confirmed_count = db.query(models.Helper).filter_by(request_id=id, status="confirmed").count()
    if confirmed_count >= req.people_needed:
        req.status = "help_found"
        
    db.commit()
    return {"msg": "Helper accepted!"}

@router.post("/{id}/reject/{user_id}")
def reject_helper(
    id: int,
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(models.HelpRequest).filter_by(id=id, user_id=current_user.id).first()
    if not req:
        raise HTTPException(status_code=403, detail="Not the owner")
    
    db.query(models.Helper).filter_by(request_id=id, user_id=user_id).delete()
    
    # If falling below limit, set back to seeking
    confirmed_count = db.query(models.Helper).filter_by(request_id=id, status="confirmed").count()
    if confirmed_count < req.people_needed:
        req.status = "seeking"
        
    db.commit()
    return {"msg": "Helper removed"}

@router.post("/{id}/leave")
def leave_request(
    id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db.query(models.Helper).filter_by(request_id=id, user_id=current_user.id).delete()
    
    req = db.query(models.HelpRequest).filter_by(id=id).first()
    if req:
        confirmed_count = db.query(models.Helper).filter_by(request_id=id, status="confirmed").count()
        if confirmed_count < req.people_needed:
            req.status = "seeking"
        db.commit()
        
    return {"msg": "Left request"}

@router.post("/{id}/complete")
def complete_request(
    id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(models.HelpRequest).filter_by(id=id, user_id=current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found or not owned by you")
    
    # Loophole Fix: Cannot complete if no one actually helped through the platform
    confirmed_helpers = db.query(models.Helper).filter_by(request_id=id, status="confirmed").all()
    if not confirmed_helpers:
        raise HTTPException(
            status_code=400, 
            detail="Cannot complete a request with no confirmed helpers. If you no longer need help, please Cancel the request instead."
        )

    if req.status == "completed":
        return {"msg": "Already completed"}
        
    req.status = "completed"
    
    # Calculate impact duration
    duration = 1.0
    if req.start_time and req.end_time:
        diff = req.end_time - req.start_time
        duration = max(1.0, round(diff.total_seconds() / 3600.0, 1))
    
    # Award karma ONLY to confirmed helpers (Pure Helper Economy)
    from .impact import award_karma
    confirmed_helpers = db.query(models.Helper).filter_by(request_id=id, status="confirmed").all()
    for helper in confirmed_helpers:
        # Pass duration to automate impact stats & history
        award_karma(helper.user_id, "helped", db, req.category, hours=duration)
        
    db.commit()
    return {"msg": "Task completed! Karma awarded to everyone involved. ✨"}

@router.delete("/{id}")
def cancel_request(
    id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(models.HelpRequest).filter_by(id=id, user_id=current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found or not owned by you")
    
    if req.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed request")
    
    # Delete helpers first
    db.query(models.Helper).filter_by(request_id=id).delete()
    # Delete chat messages
    db.query(models.ChatMessage).filter_by(request_id=id).delete()
    # Delete request
    db.delete(req)
    db.commit()
    
    return {"msg": "Request cancelled successfully."}
