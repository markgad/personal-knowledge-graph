from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.ingest import ingest_folder

router = APIRouter(prefix="/api", tags=["ingest"])


class IngestRequest(BaseModel):
    folder_path: str | None = None  # defaults to settings.notes_dir if omitted


@router.post("/ingest")
def run_ingest(req: IngestRequest):
    try:
        stats = ingest_folder(req.folder_path or settings.notes_dir)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return stats
