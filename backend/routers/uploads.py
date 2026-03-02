from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from .auth import get_current_user
from services.uploads import save_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated endpoint to upload an image.
    Returns the public URL.
    """
    url = save_upload(file)
    return {"url": url}
