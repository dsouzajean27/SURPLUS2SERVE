import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth.dependencies import require_role
from app.models.user import User

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# backend/uploads/  (served publicly at /uploads/<file> - see main.py)
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def _detect_ext(data: bytes):
    """Identify the real image type from its first bytes (don't trust the filename)."""
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


@router.post("/food-image")
async def upload_food_image(file: UploadFile = File(...),
                            current_user: User = Depends(require_role("donor", "admin"))):
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 5 MB)")
    ext = _detect_ext(data)
    if not ext:
        raise HTTPException(status_code=400, detail="Only JPG, PNG or WEBP images are allowed")
    name = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / name).write_bytes(data)
    return {"image_url": f"/uploads/{name}"}
