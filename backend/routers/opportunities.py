from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models
import schemas
from routers.auth import get_current_user
from routers.impact import log_impact

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("/", response_model=List[schemas.OpportunityResponse])
def get_opportunities(
    status: Optional[str] = Query(None, description="Filter by status: verified, needs_review, flagged"),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.Opportunity)
    # Public feed only shows non-flagged items
    if status:
        query = query.filter(models.Opportunity.status == status)
    else:
        query = query.filter(models.Opportunity.status != "flagged")
    if category:
        query = query.filter(models.Opportunity.category == category)
    return query.order_by(models.Opportunity.created_at.desc()).all()


@router.get("/review-queue", response_model=List[schemas.OpportunityResponse])
def get_review_queue(db: Session = Depends(get_db)):
    """Returns all needs_review opportunities for the Verify Center."""
    return (
        db.query(models.Opportunity)
        .filter(models.Opportunity.status == "needs_review")
        .order_by(models.Opportunity.created_at.desc())
        .all()
    )


@router.get("/map-pins", response_model=List[schemas.OpportunityResponse])
def get_map_pins(db: Session = Depends(get_db)):
    """Returns all non-flagged opportunities with lat/lng for the Map View."""
    return (
        db.query(models.Opportunity)
        .filter(models.Opportunity.status != "flagged")
        .all()
    )


@router.get("/{opportunity_id}", response_model=schemas.OpportunityResponse)
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    op = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return op


@router.post("/", response_model=schemas.OpportunityResponse, status_code=201)
def create_opportunity(
    payload: schemas.OpportunityCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_ngo_admin:
        raise HTTPException(status_code=403, detail="Only NGO administrators can create opportunities.")
    from scraper.scam_detector import detect_scam
    score, status, _, reasoning = detect_scam(
        payload.title, payload.description, payload.ngo_name,
        payload.source or "manual", payload.source_url or "",
    )
    op = models.Opportunity(**payload.model_dump(), trust_score=score, status=status, trust_reasoning=reasoning)
    db.add(op)
    db.commit()
    db.refresh(op)
    return op


@router.patch("/{opportunity_id}/verify", response_model=schemas.OpportunityResponse)
def verify_opportunity(
    opportunity_id: int,
    action: schemas.VerifyAction,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    op = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if action.action == "confirm":
        op.trust_score = min(100, op.trust_score + 15)
        op.status = "verified" if op.trust_score >= 90 else "needs_review"
        op.trust_reasoning = f"(Community) {op.trust_score}%: Confirmed by manual review."
    elif action.action == "flag":
        op.trust_score = max(0, op.trust_score - 20)
        op.status = "flagged" if op.trust_score < 50 else "needs_review"
        op.trust_reasoning = f"(Community) {op.trust_score}%: Flagged by manual review."
    else:
        raise HTTPException(status_code=400, detail="Action must be 'confirm' or 'flag'")
    
    # Automatically log impact for the user
    log_impact(current_user.id, schemas.ImpactLogRequest(type="verification"), db)
    
    db.commit()
    db.refresh(op)
    return op
