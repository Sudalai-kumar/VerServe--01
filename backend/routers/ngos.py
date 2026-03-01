from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas

router = APIRouter(prefix="/ngos", tags=["ngos"])


@router.get("/", response_model=List[schemas.NGOResponse])
def get_ngos(db: Session = Depends(get_db)):
    return db.query(models.NGO).filter(models.NGO.verified == True).all()
