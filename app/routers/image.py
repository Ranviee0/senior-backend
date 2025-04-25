from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from typing import List
from sqlmodel import select
from app.db import get_session  # Your session dependency
from app.models import Land, LandImage  # Ensure this is correctly imported
from datetime import datetime, timezone

router = APIRouter()

@router.post("/upload-image/{land_id}")
async def upload_image(land_id: int, file: UploadFile = File(...)):
    with get_session() as session:
        # 1. Validate land_id
        land = session.get(Land, land_id)
        if not land:
            raise HTTPException(status_code=404, detail=f"Land with ID {land_id} not found.")

        # 2. Ensure directory exists
        upload_dir = Path("uploads/images")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 3. Save file to disk
        save_path = upload_dir / file.filename
        with open(save_path, "wb") as f:
            f.write(await file.read())

        # 4. Save image metadata to DB
        image_record = LandImage(
            land_id=land_id,
            filename=file.filename,
            filepath=str(save_path),
            uploaded_at=datetime.now(timezone.utc)
        )
        session.add(image_record)
        session.commit()
        session.refresh(image_record)

        return {
            "status": "success",
            "land_id": land_id,
            "image_id": image_record.id,
            "filename": image_record.filename,
            "filepath": image_record.filepath,
            "uploaded_at": image_record.uploaded_at.isoformat()
        }

@router.get("/get-images/{land_id}/")
def get_land_images(land_id: int):
    with get_session() as session:
        images = session.exec(select(LandImage).where(LandImage.land_id == land_id)).all()
        if not images:
            raise HTTPException(status_code=404, detail="No images found for this land ID")
        return images
    

@router.delete("/delete-images/{land_id}/")
def delete_all_land_images(land_id: int):
    with get_session() as session:
        images = session.exec(select(LandImage).where(LandImage.land_id == land_id)).all()

        if not images:
            raise HTTPException(status_code=404, detail=f"No images found for Land ID {land_id}")

        failed_deletions = []

        for image in images:
            file_path = Path(image.filepath)
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as e:
                    failed_deletions.append(str(file_path))

            session.delete(image)

        session.commit()

        return {
            "status": "success",
            "land_id": land_id,
            "deleted_count": len(images) - len(failed_deletions),
            "failed_files": failed_deletions if failed_deletions else None
        }