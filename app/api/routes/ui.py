from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

_FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@router.get("/", include_in_schema=False)
async def ui_index():
    return FileResponse(_FRONTEND_DIR / "index.html")


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(_FRONTEND_DIR / "favicon.svg", media_type="image/svg+xml")
