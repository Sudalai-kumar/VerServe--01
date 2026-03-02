from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from routers.auth import get_current_user
from typing import List

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/{request_id}", response_model=List[schemas.ChatMessageResponse])
def get_chat_history(request_id: int, db: Session = Depends(get_db)):
    """Fetch all public messages for a specific help request."""
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.request_id == request_id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
    
    # Manually attach full_name for easier frontend display
    result = []
    for m in messages:
        res = schemas.ChatMessageResponse.from_orm(m)
        res.full_name = m.user.full_name or m.user.email
        result.append(res)
        
    return result

@router.post("/{request_id}", response_model=schemas.ChatMessageResponse)
def post_chat_message(
    request_id: int,
    payload: schemas.ChatMessageCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Post a new message to the public chat room."""
    # Verify request exists
    hr = db.query(models.HelpRequest).filter(models.HelpRequest.id == request_id).first()
    if not hr:
        raise HTTPException(status_code=404, detail="Help request not found")
        
    new_msg = models.ChatMessage(
        request_id=request_id,
        user_id=current_user.id,
        content=payload.content
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    res = schemas.ChatMessageResponse.from_orm(new_msg)
    res.full_name = current_user.full_name or current_user.email
    return res
