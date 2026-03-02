import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = "static/uploads"

# Create directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_upload(file: UploadFile) -> str:
    """
    Save an uploaded file locally and return the public URL path.
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported.")

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    # Return the relative URL (assuming static mounting in main.py)
    return f"/static/uploads/{filename}"
